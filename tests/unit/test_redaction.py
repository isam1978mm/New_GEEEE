from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.errors import RedactionViolationError
from app.main import create_app
from app.services.redaction import redact, redact_for_log, verify_redacted


def test_verify_redacted_rejects_forbidden_key() -> None:
    with pytest.raises(RedactionViolationError):
        verify_redacted({"lat": 1.23})


def test_verify_redacted_rejects_absolute_path_value() -> None:
    with pytest.raises(RedactionViolationError):
        verify_redacted({"message": "C:\\secret\\file.json"})


def test_redact_drops_forbidden_fields_and_masks_spatial_values() -> None:
    payload = {
        "name": "run-1",
        "geometry": "POINT(1 2)",
        "roi_center": "12.34, 56.78",
        "metadata": {
            "sha256": "a" * 64,
            "notes": "keep me",
        },
    }

    assert redact(payload) == {
        "name": "run-1",
        "roi_center": "[REDACTED_COORDS]",
        "metadata": {
            "notes": "keep me",
        },
    }


def test_redact_preserves_non_spatial_numeric_pairs() -> None:
    payload = {"eigenvalues": [12.34, 56.78], "summary": "12.34, 56.78"}
    assert redact(payload) == payload
    verify_redacted(payload)


def test_redact_for_log_masks_coordinates_hash_and_path() -> None:
    text = "point 12.34, 56.78 hash deadbeefdeadbeefdeadbeefdeadbeef at C:\\tmp\\x"
    redacted = redact_for_log(text, levelno=20)
    assert "[REDACTED_COORDS]" in redacted
    assert "[REDACTED_HASH]" in redacted
    assert "[REDACTED_PATH]" in redacted


def test_redact_for_log_keeps_debug_messages_unchanged() -> None:
    text = "point 12.34, 56.78 at C:\\tmp\\x"
    assert redact_for_log(text, levelno=10) == text


def test_json_guard_blocks_forbidden_response_payload() -> None:
    app = create_app()

    @app.get("/leak")
    async def leak() -> dict[str, float]:
        return {"lat": 1.23}

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/leak")
    assert response.status_code == 500
    assert response.json() == {
        "error": "internal_error",
        "message": "Request could not be processed.",
    }

