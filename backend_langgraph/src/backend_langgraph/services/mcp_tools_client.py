from __future__ import annotations

from typing import Any

import httpx

from backend_langgraph.core.config import get_settings


async def call_tool(
    tool_name: str,
    arguments: dict[str, Any],
    session_token: str,
) -> Any:
    settings = get_settings()
    url = f"{settings.mcp_backend_base_url}/api/v1/tools/{tool_name}"
    headers = {"X-Session-Token": session_token}
    payload = {"arguments": arguments}

    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()
        return body["result"]
