from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend_langgraph.api.auth_routes import router as auth_router
from backend_langgraph.api.routes import router as api_router
from backend_langgraph.core.config import get_settings
from backend_langgraph.core.logging import configure_logging, get_logger
from backend_langgraph.core.middleware import register_middlewares
from backend_langgraph.db.clients import lifespan_clients
from backend_langgraph.db.indexes import ensure_indexes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)
    logger.info("service.starting", service=settings.service_name, environment=settings.environment)
    async with lifespan_clients():
        if settings.auto_bootstrap_indexes:
            await ensure_indexes()
        yield
    logger.info("service.stopped", service=settings.service_name)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.service_name,
        version=settings.version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )
    register_middlewares(app)
    app.include_router(api_router)
    app.include_router(auth_router, prefix="/api")
    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend_langgraph.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=1 if settings.reload else settings.workers,
    )
