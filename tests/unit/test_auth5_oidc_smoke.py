"""Unit tests for scripts/auth5_oidc_smoke.py. No network calls."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import auth5_oidc_smoke as smoke

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_DENIED_BODY: dict = {"outcome": "denied"}
_DENIED_RESPONSE = (403, _DENIED_BODY)
_ALLOWED_BODY: dict = {
    "outcome": "allowed",
    "frontend_visible": "operator_only",
    "downloadable_via_api": False,
}
_ALLOWED_RESPONSE = (200, _ALLOWED_BODY)


def _args(**overrides: object) -> argparse.Namespace:
    defaults: dict[str, object] = dict(
        base_url="http://127.0.0.1:8015",
        run_id="test-run-id",
        artifact_family="phase_d1_private_geojson",
        access_mode="operator_only_preview",
        token_env="AUTH5_SMOKE_BEARER_TOKEN",
        expected_valid_status=200,
        expected_valid_outcome="allowed",
        timeout_seconds=10,
        mode="all",
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# self-check mode
# ---------------------------------------------------------------------------

def test_self_check_mode_exits_zero() -> None:
    exit_code = smoke.main(["--mode", "self-check"])
    assert exit_code == 0


# ---------------------------------------------------------------------------
# no-token mode
# ---------------------------------------------------------------------------

def test_no_token_mode_sends_no_authorization_header() -> None:
    with patch.object(smoke, "_fetch", return_value=_DENIED_RESPONSE) as mock_fetch:
        result = smoke.run_no_token(_args())
    assert result is True
    assert mock_fetch.call_args.kwargs["token"] is None


def test_no_token_mode_fails_on_non_403_status(capsys: pytest.CaptureFixture) -> None:
    with patch.object(smoke, "_fetch", return_value=(200, {"outcome": "allowed"})):
        result = smoke.run_no_token(_args())
    assert result is False
    assert "FAIL" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# invalid-token mode
# ---------------------------------------------------------------------------

def test_invalid_token_mode_sends_header_but_output_does_not_contain_token(
    capsys: pytest.CaptureFixture,
) -> None:
    with patch.object(smoke, "_fetch", return_value=_DENIED_RESPONSE) as mock_fetch:
        result = smoke.run_invalid_token(_args())
    captured = capsys.readouterr()
    assert result is True
    assert mock_fetch.call_args.kwargs["token"] == smoke._INVALID_TOKEN
    assert smoke._INVALID_TOKEN not in captured.out


# ---------------------------------------------------------------------------
# valid-token mode
# ---------------------------------------------------------------------------

def test_valid_token_mode_uses_env_var_but_output_does_not_contain_token(
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH5_SMOKE_BEARER_TOKEN", "my.secret.bearer.token")
    with patch.object(smoke, "_fetch", return_value=_ALLOWED_RESPONSE):
        result = smoke.run_valid_token(_args(), skip_if_missing=False)
    captured = capsys.readouterr()
    assert result is True
    assert "my.secret.bearer.token" not in captured.out


def test_valid_token_mode_fails_when_env_var_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AUTH5_SMOKE_BEARER_TOKEN", raising=False)
    result = smoke.run_valid_token(_args(), skip_if_missing=False)
    assert result is False


def test_valid_token_mode_returns_none_when_skippable_and_env_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AUTH5_SMOKE_BEARER_TOKEN", raising=False)
    result = smoke.run_valid_token(_args(), skip_if_missing=True)
    assert result is None


# ---------------------------------------------------------------------------
# denied response checks — leak detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "leak_key,leak_body",
    [
        ("preview_payload", {"outcome": "denied", "preview_payload": {"secret": "data"}}),
        ("run_id", {"outcome": "denied", "run_id": "some-run-id"}),
        ("artifact_family", {"outcome": "denied", "artifact_family": "phase_d1_private_geojson"}),
    ],
)
def test_denied_response_check_fails_if_key_leaks(
    leak_key: str, leak_body: dict
) -> None:
    leaks = smoke._check_denied_body(leak_body)
    assert leak_key in leaks


def test_denied_response_clean_body_has_no_leaks() -> None:
    leaks = smoke._check_denied_body({"outcome": "denied"})
    assert leaks == []


# ---------------------------------------------------------------------------
# allowed response checks
# ---------------------------------------------------------------------------

def test_allowed_response_checks_pass_for_correct_response() -> None:
    violations = smoke._check_allowed_body(_ALLOWED_BODY, "allowed")
    assert violations == []


def test_allowed_response_check_fails_on_wrong_outcome() -> None:
    body = {**_ALLOWED_BODY, "outcome": "denied"}
    violations = smoke._check_allowed_body(body, "allowed")
    assert any("outcome" in v for v in violations)


def test_allowed_response_check_fails_on_public_frontend_visible() -> None:
    body = {**_ALLOWED_BODY, "frontend_visible": "public"}
    violations = smoke._check_allowed_body(body, "allowed")
    assert any("frontend_visible" in v for v in violations)


def test_allowed_response_check_fails_when_downloadable_via_api_true() -> None:
    body = {**_ALLOWED_BODY, "downloadable_via_api": True}
    violations = smoke._check_allowed_body(body, "allowed")
    assert any("downloadable_via_api" in v for v in violations)


# ---------------------------------------------------------------------------
# all mode — skips valid-token when token env absent
# ---------------------------------------------------------------------------

def test_all_mode_skips_valid_token_when_env_missing_still_passes_others(
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AUTH5_SMOKE_BEARER_TOKEN", raising=False)
    with patch.object(smoke, "_fetch", return_value=_DENIED_RESPONSE):
        exit_code = smoke.main(["--run-id", "test-run", "--mode", "all"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "SKIP" in captured.out
    assert "FAIL" not in captured.out
    assert captured.out.count("PASS") >= 2


# ---------------------------------------------------------------------------
# URL construction
# ---------------------------------------------------------------------------

def test_url_path_and_query_are_formed_correctly() -> None:
    url = smoke._build_url(
        "http://localhost:8015",
        "my-run-123",
        "phase_d1_private_geojson",
        "operator_only_preview",
    )
    assert "/runs/my-run-123/operator/private-overlays" in url
    assert "artifact_family=phase_d1_private_geojson" in url
    assert "access_mode=operator_only_preview" in url


def test_url_run_id_is_percent_encoded() -> None:
    url = smoke._build_url("http://localhost:8015", "run/with spaces", "phase_d1_private_geojson", "operator_only_preview")
    assert "/run%2Fwith%20spaces/" in url or "run%2Fwith" in url
