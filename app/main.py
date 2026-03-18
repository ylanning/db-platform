"""FastAPI application factory and configuration for DB Platform Control Plane."""

from __future__ import annotations

from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.services.errors import UpstreamError
from app.utils.logging import configure_logging, log_request_info

logger = structlog.get_logger()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance with routes and exception handlers.
    """
    configure_logging()
    app = FastAPI(title="DB Platform Control Plane", version="0.1.0")
    app.include_router(router)

    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        """Attach request metadata to logs and propagate a request ID.

        Example:
            Incoming request without an X-Request-Id header will be assigned one.
            The response includes the same X-Request-Id, and logs include
            request_id, method, and path fields.
        """
        request_id = request.headers.get("x-request-id", str(uuid4()))
        with log_request_info(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        ):
            response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response

    @app.exception_handler(UpstreamError)
    async def upstream_handler(request: Request, exc: UpstreamError) -> JSONResponse:
        logger.warning("upstream_error", path=str(request.url), error=str(exc))
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", path=str(request.url), error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

    return app


app = create_app()
