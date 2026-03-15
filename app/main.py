from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

from app.api.routes import router
from app.services.errors import ConflictError, NotFoundError, UpstreamError
from app.utils.logging import configure_logging

logger = structlog.get_logger()


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="DB Platform Control Plane", version="0.1.0")
    app.include_router(router)

    @app.exception_handler(UpstreamError)
    async def upstream_handler(request: Request, exc: UpstreamError) -> JSONResponse:
        logger.warning("upstream_error", path=str(request.url), error=str(exc))
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        logger.info("conflict_error", path=str(request.url), error=str(exc))
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        logger.info("not_found_error", path=str(request.url), error=str(exc))
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    return app


if __name__ == "__main__":
    app = create_app()
