from __future__ import annotations

import httpx

from backend_langgraph.core.config import get_settings


async def groq_chat(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
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
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"])
