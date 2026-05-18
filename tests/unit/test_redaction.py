from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.errors import RedactionViolationError
from app.main import create_app
from app.services.redaction import redact_for_log, verify_redacted


def test_verify_redacted_rejects_forbidden_key() -> None:
    with pytest.raises(RedactionViolationError):
        verify_redacted({"lat": 1.23})


def test_verify_redacted_rejects_absolute_path_value() -> None:
    with pytest.raises(RedactionViolationError):
        verify_redacted({"message": "C:\\secret\\file.json"})


def test_redact_for_log_masks_coordinates_hash_and_path() -> None:
    text = "point 12.34, 56.78 hash deadbeefdeadbeefdeadbeefdeadbeef at C:\\tmp\\x"
    redacted = redact_for_log(text)
    assert "[REDACTED_COORDS]" in redacted
    assert "[REDACTED_HASH]" in redacted
    assert "[REDACTED_PATH]" in redacted


def test_json_guard_blocks_forbidden_response_payload() -> None:
    app = create_app()

    @app.get("/leak")
    async def leak() -> dict[str, float]:
        return {"lat": 1.23}

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/leak")
    assert response.status_code == 500
    assert response.json() == {
        "error": "redaction_violation",
        "message": "Request could not be processed.",
    }

