from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend_mcp.auth.dependencies import (
    get_current_user,
    rate_limit_tools,
    validate_internal_api_key,
)
from backend_mcp.schemas.tools import ToolInvokeRequest, ToolInvokeResponse
from backend_mcp.services import tooling_service

router = APIRouter(prefix="/v1/tools", tags=["tools"], dependencies=[Depends(rate_limit_tools)])


async def _resolve_user_id(user: dict[str, Any] | None, payload: ToolInvokeRequest) -> str:
    if user is not None:
        return str(user["_id"])
    user_id = payload.arguments.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing user_id")
    return user_id


async def _invoke_tool_with_user_context(
    tool_name: str,
    payload: ToolInvokeRequest,
    user: dict[str, Any] | None,
) -> ToolInvokeResponse:
    args = payload.arguments
    user_id = await _resolve_user_id(user, payload)
    result: Any

    match tool_name:
        case "pdf_ingestion":
            result = await tooling_service.pdf_ingestion(
                user_id=user_id,
                file_path=str(args.get("file_path", "")),
                source=str(args.get("source", "pdf")),
            )
        case "rag_query":
            result = await tooling_service.rag_query(
                user_id=user_id,
                query=str(args.get("query", "")),
                limit=int(args.get("limit", 5)),
            )
        case "wiki_search":
            result = await tooling_service.wiki_search(
                query=str(args.get("query", "")),
                limit=int(args.get("limit", 3)),
            )
        case "long_term_user_memory_search":
            result = await tooling_service.long_term_memory_search(
                user_id=user_id,
                query=str(args.get("query", "")),
                limit=int(args.get("limit", 5)),
            )
        case "refine_vague_prompt":
            result = await tooling_service.refine_prompt_if_vague(
                prompt=str(args.get("prompt", "")),
                user_custom_prompt=str(args.get("user_custom_prompt", "")),
            )
        case "web_search":
            result = await tooling_service.web_search(
                query=str(args.get("query", "")),
                limit=int(args.get("limit", 5)),
            )
        case "summarize_text":
            result = await tooling_service.summarize_text(
                text=str(args.get("text", "")),
                max_words=int(args.get("max_words", 120)),
            )
        case "store_user_memory":
            result = await tooling_service.store_user_memory(
                user_id=user_id,
                text=str(args.get("text", "")),
                tags=[str(item) for item in args.get("tags", [])],
            )
        case "fetch_user_context":
            result = await tooling_service.fetch_user_context(user_id=user_id)
        case "classify_intent":
            result = await tooling_service.classify_intent(prompt=str(args.get("prompt", "")))
        case _:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown tool")

    return ToolInvokeResponse(tool=tool_name, result=result)


@router.post("/{tool_name}", response_model=ToolInvokeResponse)
async def invoke_tool(
    tool_name: str,
    payload: ToolInvokeRequest,
    user: dict[str, Any] = Depends(get_current_user),
) -> ToolInvokeResponse:
    return await _invoke_tool_with_user_context(tool_name=tool_name, payload=payload, user=user)


@router.post("/{tool_name}/internal", response_model=ToolInvokeResponse)
async def invoke_tool_internal(
    tool_name: str,
    payload: ToolInvokeRequest,
    _: None = Depends(validate_internal_api_key),
) -> ToolInvokeResponse:
    return await _invoke_tool_with_user_context(tool_name=tool_name, payload=payload, user=None)
