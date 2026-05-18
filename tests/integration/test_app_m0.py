from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_healthz_returns_ok() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_fails_safely_without_service_account() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json() == {
        "error": "ee_not_ready",
        "message": "Service is not ready.",
    }


def test_openapi_and_docs_are_disabled() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)
    for path in ("/openapi.json", "/docs", "/redoc"):
        response = client.get(path)
        assert response.status_code == 404
