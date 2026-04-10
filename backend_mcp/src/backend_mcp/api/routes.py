from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from backend_mcp.core.config import get_settings
from backend_mcp.schemas.health import HealthResponse
from backend_mcp.telemetry.metrics import metrics_response

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        environment=settings.environment,
    )


@router.get("/metrics", response_class=PlainTextResponse)
def metrics() -> PlainTextResponse:
    return metrics_response()
