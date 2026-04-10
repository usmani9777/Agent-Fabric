from typing import Any

from mcp.server.fastmcp import FastMCP

from backend_mcp.services import tooling_service

mcp = FastMCP("saynoma-mcp")


@mcp.tool()
def ping() -> str:
    """Simple tool used by clients to validate MCP connectivity."""
    return "pong"


@mcp.tool()
async def pdf_ingestion(user_id: str, file_path: str, source: str = "pdf") -> dict[str, Any]:
    return await tooling_service.pdf_ingestion(user_id=user_id, file_path=file_path, source=source)


@mcp.tool()
async def rag_query(user_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    return await tooling_service.rag_query(user_id=user_id, query=query, limit=limit)


@mcp.tool()
async def wiki_search(query: str, limit: int = 3) -> list[dict[str, str]]:
    return await tooling_service.wiki_search(query=query, limit=limit)


@mcp.tool()
async def long_term_user_memory_search(
    user_id: str,
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    return await tooling_service.long_term_memory_search(user_id=user_id, query=query, limit=limit)


@mcp.tool()
async def refine_vague_prompt(prompt: str, user_custom_prompt: str = "") -> dict[str, Any]:
    return await tooling_service.refine_prompt_if_vague(
        prompt=prompt,
        user_custom_prompt=user_custom_prompt,
    )


@mcp.tool()
async def web_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    return await tooling_service.web_search(query=query, limit=limit)


@mcp.tool()
async def summarize_text(text: str, max_words: int = 120) -> str:
    return await tooling_service.summarize_text(text=text, max_words=max_words)


@mcp.tool()
async def store_user_memory(
    user_id: str,
    text: str,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    return await tooling_service.store_user_memory(user_id=user_id, text=text, tags=tags)


@mcp.tool()
async def fetch_user_context(user_id: str) -> dict[str, Any]:
    return await tooling_service.fetch_user_context(user_id=user_id)


@mcp.tool()
async def classify_intent(prompt: str) -> dict[str, str]:
    return await tooling_service.classify_intent(prompt=prompt)


def get_mcp_http_app() -> Any | None:
    """Return a mounted ASGI app for MCP when supported by the SDK version."""
    if hasattr(mcp, "streamable_http_app"):
        return mcp.streamable_http_app()
    if hasattr(mcp, "sse_app"):
        return mcp.sse_app()
    return None
