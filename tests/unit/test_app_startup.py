from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_app_starts_and_root_returns_ok() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_and_ready_routes_are_registered() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    health_response = client.get("/healthz")
    ready_response = client.get("/readyz")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert ready_response.status_code == 503
    assert ready_response.json() == {
        "error": "ee_not_ready",
        "message": "Service is not ready.",
    }
