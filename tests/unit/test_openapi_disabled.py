from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_openapi_surfaces_are_disabled() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    for path in ("/openapi.json", "/docs", "/redoc"):
        response = client.get(path)
        assert response.status_code == 404
