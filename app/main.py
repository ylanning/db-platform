"""FastAPI application factory and configuration for DB Platform Control Plane."""

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.services.errors import UpstreamError
from app.utils.logging import configure_logging

logger = structlog.get_logger()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance with routes and exception handlers.
    """
    configure_logging()
    app = FastAPI(title="DB Platform Control Plane", version="0.1.0")
    app.include_router(router)

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
