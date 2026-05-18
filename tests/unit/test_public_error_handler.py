from __future__ import annotations

from fastapi import Query
from fastapi.testclient import TestClient

from app.api.errors import public_error_response
from app.main import create_app


def test_validation_errors_use_safe_public_handler() -> None:
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


def test_unhandled_errors_do_not_echo_forbidden_fields() -> None:
    app = create_app()

    @app.get("/boom")
    async def boom() -> dict[str, str]:
        raise RuntimeError("lat=1.0, lon=2.0 path=C:\\secret input=roi")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/boom")
    assert response.status_code == 500
    assert response.json() == {
        "error": "internal_error",
        "message": "Request could not be processed.",
    }
    assert "lat" not in response.text
    assert "secret" not in response.text
    assert "input" not in response.text


def test_public_error_response_falls_back_to_generic_payload_if_needed() -> None:
    response = public_error_response(
        status_code=500,
        code="error_code",
        message="C:\\secret\\file.json",
    )
    assert response.status_code == 500
    assert response.body == b'{"error":"internal_error","message":"Request could not be processed."}'
