from __future__ import annotations

from fastapi import Query
from fastapi.testclient import TestClient

from app.main import create_app


def test_validation_errors_are_public_safe() -> None:
    app = create_app()

    @app.get("/needs-int")
    async def needs_int(limit: int = Query(...)) -> dict[str, int]:
        return {"limit": limit}

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/needs-int", params={"limit": "abc"})
    assert response.status_code == 422
    assert response.json() == {
        "error": "validation_error",
        "message": "Request could not be processed.",
    }
    assert "limit" not in response.text


def test_unhandled_errors_are_public_safe() -> None:
    app = create_app()

    @app.get("/boom")
    async def boom() -> dict[str, str]:
        raise RuntimeError("lat=1.0, lon=2.0 path=C:\\secret")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/boom")
    assert response.status_code == 500
    assert response.json() == {
        "error": "internal_error",
        "message": "Request could not be processed.",
    }
    assert "lat" not in response.text
    assert "secret" not in response.text

