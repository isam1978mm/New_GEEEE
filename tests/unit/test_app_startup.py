from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_app_starts_and_root_returns_ok() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "GEE Screening Dashboard Design" in response.text


def test_health_and_ready_routes_are_registered() -> None:
    client = TestClient(
        create_app(
            Settings(
                ee_service_account_email=None,
                ee_service_account_key_path=None,
            )
        ),
        raise_server_exceptions=False,
    )

    health_response = client.get("/healthz")
    ready_response = client.get("/readyz")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert ready_response.status_code == 503
    assert ready_response.json() == {
        "error": "ee_not_ready",
        "message": "Service is not ready.",
    }
