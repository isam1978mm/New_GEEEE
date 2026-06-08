"""Unit tests for scripts/deploy1_oidc_env_check.py. No network calls, no file writes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import deploy1_oidc_env_check as envcheck

# A real-looking but example-only subject string used to prove it is never printed.
_SECRET_SUBJECT = "operator-subject-VERY-SECRET-123456789"
_FAKE_TOKEN = "fake.bearer.token.NEVER.PRINT.ME"


def _set_complete_env(monkeypatch: pytest.MonkeyPatch, **overrides: str) -> None:
    env: dict[str, str] = {
        "OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED": "true",
        "OPERATOR_AUTH_TRUSTED_PROXY_ENABLED": "false",
        "OPERATOR_AUTH_OIDC_ENABLED": "true",
        "OPERATOR_AUTH_OIDC_ISSUER_URL": "https://auth.example.test",
        "OPERATOR_AUTH_OIDC_CLIENT_ID": "gee-operator-ui",
        "OPERATOR_AUTH_OIDC_JWKS_URI": "https://auth.example.test/.well-known/jwks.json",
        "OPERATOR_RUN_AUTHORIZATIONS": json.dumps({_SECRET_SUBJECT: ["run_example_001"]}),
    }
    env.update(overrides)
    # Clear all relevant vars first, then set the desired ones.
    for key in list(env.keys()) + ["AUTH5_SMOKE_BEARER_TOKEN"]:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)


def _clear_all(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED",
        "OPERATOR_AUTH_TRUSTED_PROXY_ENABLED",
        "OPERATOR_AUTH_OIDC_ENABLED",
        "OPERATOR_AUTH_OIDC_ISSUER_URL",
        "OPERATOR_AUTH_OIDC_CLIENT_ID",
        "OPERATOR_AUTH_OIDC_JWKS_URI",
        "OPERATOR_RUN_AUTHORIZATIONS",
        "AUTH5_SMOKE_BEARER_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)


# ---------------------------------------------------------------------------
# strict mode pass/fail
# ---------------------------------------------------------------------------

def test_missing_env_strict_mode_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_all(monkeypatch)
    assert envcheck.main(["--strict"]) == 1


def test_complete_env_strict_mode_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_complete_env(monkeypatch)
    assert envcheck.main(["--strict"]) == 0


def test_non_strict_missing_env_exits_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_all(monkeypatch)
    # Non-strict: warnings/fails still exit 0.
    assert envcheck.main([]) == 0


# ---------------------------------------------------------------------------
# URL scheme validation
# ---------------------------------------------------------------------------

def test_issuer_must_be_https(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_complete_env(monkeypatch, OPERATOR_AUTH_OIDC_ISSUER_URL="http://auth.example.test")
    results = envcheck.run_checks()
    issuer = next(r for r in results if r["check"] == "OPERATOR_AUTH_OIDC_ISSUER_URL")
    assert issuer["status"] == "FAIL"


def test_jwks_uri_must_be_https(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_complete_env(monkeypatch, OPERATOR_AUTH_OIDC_JWKS_URI="http://auth.example.test/jwks")
    results = envcheck.run_checks()
    jwks = next(r for r in results if r["check"] == "OPERATOR_AUTH_OIDC_JWKS_URI")
    assert jwks["status"] == "FAIL"


# ---------------------------------------------------------------------------
# OPERATOR_RUN_AUTHORIZATIONS validation
# ---------------------------------------------------------------------------

def test_run_authorizations_must_parse_as_json_object(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_complete_env(monkeypatch, OPERATOR_RUN_AUTHORIZATIONS="not-json{{{")
    results = envcheck.run_checks()
    auth = next(r for r in results if r["check"] == "OPERATOR_RUN_AUTHORIZATIONS")
    assert auth["status"] == "FAIL"


def test_run_authorizations_json_array_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_complete_env(monkeypatch, OPERATOR_RUN_AUTHORIZATIONS=json.dumps(["run_a"]))
    results = envcheck.run_checks()
    auth = next(r for r in results if r["check"] == "OPERATOR_RUN_AUTHORIZATIONS")
    assert auth["status"] == "FAIL"


def test_actor_mapping_must_be_list_of_strings(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_complete_env(monkeypatch, OPERATOR_RUN_AUTHORIZATIONS=json.dumps({"actor": "run_a"}))
    results = envcheck.run_checks()
    auth = next(r for r in results if r["check"] == "OPERATOR_RUN_AUTHORIZATIONS")
    assert auth["status"] == "FAIL"


def test_empty_actor_run_list_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_complete_env(monkeypatch, OPERATOR_RUN_AUTHORIZATIONS=json.dumps({"actor": []}))
    results = envcheck.run_checks()
    auth = next(r for r in results if r["check"] == "OPERATOR_RUN_AUTHORIZATIONS")
    assert auth["status"] == "FAIL"
    # strict mode should fail
    assert envcheck.main(["--strict"]) == 1


# ---------------------------------------------------------------------------
# Secret masking
# ---------------------------------------------------------------------------

def test_output_does_not_include_full_actor_subject(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _set_complete_env(monkeypatch)
    envcheck.main([])
    out = capsys.readouterr().out
    assert _SECRET_SUBJECT not in out


def test_output_does_not_include_bearer_token(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _set_complete_env(monkeypatch)
    monkeypatch.setenv("AUTH5_SMOKE_BEARER_TOKEN", _FAKE_TOKEN)
    envcheck.main([])
    out = capsys.readouterr().out
    assert _FAKE_TOKEN not in out


def test_json_output_does_not_include_bearer_token(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _set_complete_env(monkeypatch)
    monkeypatch.setenv("AUTH5_SMOKE_BEARER_TOKEN", _FAKE_TOKEN)
    envcheck.main(["--json"])
    out = capsys.readouterr().out
    assert _FAKE_TOKEN not in out
    assert _SECRET_SUBJECT not in out


def test_client_id_is_masked_in_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    long_client = "super-secret-client-id-value-1234567890"
    _set_complete_env(monkeypatch, OPERATOR_AUTH_OIDC_CLIENT_ID=long_client)
    envcheck.main([])
    out = capsys.readouterr().out
    assert long_client not in out


# ---------------------------------------------------------------------------
# --json output validity
# ---------------------------------------------------------------------------

def test_json_output_is_valid_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _set_complete_env(monkeypatch)
    envcheck.main(["--json"])
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert "checks" in parsed
    assert parsed["ok"] is True
    assert isinstance(parsed["checks"], list)


# ---------------------------------------------------------------------------
# trusted proxy warning
# ---------------------------------------------------------------------------

def test_trusted_proxy_true_emits_warning_without_secrets(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _set_complete_env(monkeypatch, OPERATOR_AUTH_TRUSTED_PROXY_ENABLED="true")
    envcheck.main([])
    out = capsys.readouterr().out
    proxy_results = envcheck.run_checks()
    proxy = next(r for r in proxy_results if r["check"] == "OPERATOR_AUTH_TRUSTED_PROXY_ENABLED")
    assert proxy["status"] == "WARN"
    assert _SECRET_SUBJECT not in out
    # A WARN alone (no FAIL) should still allow strict exit 0.
    assert envcheck.main(["--strict"]) == 0
