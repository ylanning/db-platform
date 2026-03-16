from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.errors import UpstreamError


def test_health_check():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def _test_client_with_error() -> TestClient:
    app = create_app()
    router = APIRouter()

    @router.get("/upstream-error")
    async def upstream_error() -> None:
        raise UpstreamError("upstream_error")

    @router.get("/runtime-error")
    async def runtime_error() -> None:
        raise RuntimeError("Runtime error")

    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def test_upstream_error_handling() -> None:
    client = _test_client_with_error()
    response = client.get("/upstream-error")
    assert response.status_code == 502
    assert response.json() == {"detail": "upstream_error"}


def test_generic_error_handling() -> None:
    client = _test_client_with_error()
    response = client.get("/runtime-error")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
