from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from backend_langgraph.agent.runner import run_agent
from backend_langgraph.auth.dependencies import (
    get_current_session_token,
    get_current_user,
    rate_limit_invoke,
)
from backend_langgraph.core.config import get_settings
from backend_langgraph.schemas.agent import AgentInvokeRequest, AgentInvokeResponse
from backend_langgraph.schemas.health import HealthResponse
from backend_langgraph.schemas.knowledge import PdfIngestRequest, PdfIngestResponse
from backend_langgraph.services.mcp_tools_client import call_tool
from backend_langgraph.telemetry.metrics import metrics_response

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        environment=settings.environment,
    )


@router.post("/v1/agent/invoke", response_model=AgentInvokeResponse)
async def invoke(
    payload: AgentInvokeRequest,
    _: None = Depends(rate_limit_invoke),
    user: dict[str, Any] = Depends(get_current_user),
    session_token: str = Depends(get_current_session_token),
) -> AgentInvokeResponse:
    result = await run_agent(
        user_id=str(user["_id"]),
        user_prompt_template=str(user.get("prompt_template", "")),
        user_input=payload.input,
        session_token=session_token,
        refine_prompt=payload.refine_prompt,
    )
    return AgentInvokeResponse(
        refined_input=result["refined_input"],
        selected_intent=result["selected_intent"],
        tool_context=result["tool_context"],
        memory_written=bool(result["memory_written"]),
        output=result["output"],
    )


@router.post("/v1/knowledge/pdf-ingest", response_model=PdfIngestResponse)
async def ingest_pdf(
    payload: PdfIngestRequest,
    _: None = Depends(rate_limit_invoke),
    user: dict[str, Any] = Depends(get_current_user),
    session_token: str = Depends(get_current_session_token),
) -> PdfIngestResponse:
    result = await call_tool(
        "pdf_ingestion",
        {
            "file_path": payload.file_path,
            "source": payload.source,
            "user_id": str(user["_id"]),
        },
        session_token=session_token,
    )
    return PdfIngestResponse(
        status=str(result.get("status", "failed")),
        chunks=int(result.get("chunks", 0)),
        file_name=str(result.get("file_name", "")),
    )


@router.get("/metrics", response_class=PlainTextResponse)
def metrics() -> PlainTextResponse:
    return metrics_response()
