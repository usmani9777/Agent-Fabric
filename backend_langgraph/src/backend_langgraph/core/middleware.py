from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.responses import Response

from backend_langgraph.core.logging import get_logger


def register_middlewares(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid4().hex
        start = perf_counter()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration_ms = int((perf_counter() - start) * 1000)
            logger = get_logger(__name__)
            logger.info(
                "http.request",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
            )

        response.headers["X-Request-ID"] = request_id
        return response
