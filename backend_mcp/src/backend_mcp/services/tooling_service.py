from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx
import wikipedia
from bson import ObjectId
from duckduckgo_search import DDGS
from pypdf import PdfReader

from backend_mcp.core.config import get_settings
from backend_mcp.db.clients import get_database, get_redis_client


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def _chunks(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    if not text:
        return []
    out: list[str] = []
    i = 0
    while i < len(text):
        out.append(text[i : i + size])
        i += max(1, size - overlap)
    return out


async def pdf_ingestion(user_id: str, file_path: str, source: str = "pdf") -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists() or path.suffix.lower() != ".pdf":
        raise ValueError("Invalid PDF path")

    reader = PdfReader(str(path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    parts = _chunks(text)

    documents = [
        {
            "user_id": user_id,
            "source": source,
            "file_name": path.name,
            "chunk_index": idx,
            "text": chunk,
            "created_at": datetime.now(UTC),
        }
        for idx, chunk in enumerate(parts)
    ]

    if documents:
        await get_database()["rag_chunks"].insert_many(documents)

    return {"status": "ok", "chunks": len(documents), "file_name": path.name}


async def rag_query(user_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    key = f"rag:{user_id}:{query}:{limit}"
    cached = await get_redis_client().get(key)
    if cached is not None:
        return cast(list[dict[str, Any]], json.loads(cached))

    docs = await get_database()["rag_chunks"].find({"user_id": user_id}).to_list(length=1000)
    query_tokens = _tokenize(query)
    scored: list[tuple[int, dict[str, Any]]] = []
    for doc in docs:
        text = str(doc.get("text", ""))
        overlap = len(query_tokens.intersection(_tokenize(text)))
        if overlap > 0:
            scored.append(
                (
                    overlap,
                    {
                        "source": str(doc.get("source", "unknown")),
                        "file_name": str(doc.get("file_name", "")),
                        "chunk_index": int(doc.get("chunk_index", 0)),
                        "text": text[:1000],
                        "score": overlap,
                    },
                )
            )

    scored.sort(key=lambda item: item[0], reverse=True)
    result = [item[1] for item in scored[:limit]]
    await get_redis_client().setex(key, 300, json.dumps(result))
    return result


async def wiki_search(query: str, limit: int = 3) -> list[dict[str, str]]:
    titles = wikipedia.search(query, results=limit)
    results: list[dict[str, str]] = []
    for title in titles:
        try:
            summary = wikipedia.summary(title, sentences=2)
        except Exception:
            summary = ""
        results.append({"title": title, "summary": summary})
    return results


async def long_term_memory_search(user_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    pattern = re.escape(query)
    rows = (
        await get_database()["user_memories"]
        .find({"user_id": user_id, "text": {"$regex": pattern, "$options": "i"}})
        .sort("created_at", -1)
        .limit(limit)
        .to_list(length=limit)
    )
    return [{"text": str(row.get("text", "")), "tags": row.get("tags", [])} for row in rows]


async def store_user_memory(
    user_id: str,
    text: str,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    payload = {
        "user_id": user_id,
        "text": text,
        "tags": tags or [],
        "created_at": datetime.now(UTC),
    }
    await get_database()["user_memories"].insert_one(payload)
    return {"status": "stored", "length": len(text)}


async def fetch_user_context(user_id: str) -> dict[str, Any]:
    user = await get_database()["users"].find_one({"_id": ObjectId(user_id)})
    memories = (
        await get_database()["user_memories"]
        .find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(5)
        .to_list(length=5)
    )
    return {
        "email": "" if user is None else str(user.get("email", "")),
        "prompt_template": "" if user is None else str(user.get("prompt_template", "")),
        "recent_memories": [str(m.get("text", "")) for m in memories],
    }


async def _groq_chat(system_prompt: str, user_prompt: str) -> str:
    settings = get_settings()
    if not settings.groq_api_key:
        return user_prompt

    url = f"{settings.groq_base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"])


async def refine_prompt_if_vague(prompt: str, user_custom_prompt: str = "") -> dict[str, Any]:
    words = len(prompt.split())
    settings = get_settings()
    if words >= settings.vague_prompt_word_threshold:
        return {"refined": prompt, "was_refined": False}

    system = "Refine vague user prompts into specific, actionable prompts."
    user = (
        f"User prompt template: {user_custom_prompt}\n"
        f"Original prompt: {prompt}\n"
        "Return only the improved prompt."
    )
    refined = await _groq_chat(system, user)
    return {"refined": refined.strip(), "was_refined": True}


async def web_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    with DDGS() as ddgs:
        for row in ddgs.text(query, max_results=limit):
            results.append(
                {
                    "title": str(row.get("title", "")),
                    "url": str(row.get("href", "")),
                    "snippet": str(row.get("body", "")),
                }
            )
    return results


async def summarize_text(text: str, max_words: int = 120) -> str:
    system = f"Summarize text to at most {max_words} words with high factual fidelity."
    return await _groq_chat(system, text)


async def classify_intent(prompt: str) -> dict[str, str]:
    system = (
        "Classify user prompt intent into one of: rag, wiki, memory, web, general. "
        "Return JSON with key intent."
    )
    output = await _groq_chat(system, prompt)
    intent = "general"
    for name in ["rag", "wiki", "memory", "web", "general"]:
        if name in output.lower():
            intent = name
            break
    return {"intent": intent}
