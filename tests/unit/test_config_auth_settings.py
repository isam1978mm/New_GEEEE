from __future__ import annotations

import pytest

from app.config import Settings


def test_operator_auth_trusted_proxy_enabled_defaults_false() -> None:
    settings = Settings()

    assert settings.operator_auth_trusted_proxy_enabled is False


def test_operator_auth_trusted_proxy_enabled_accepts_explicit_true() -> None:
    settings = Settings(operator_auth_trusted_proxy_enabled=True)

    assert settings.operator_auth_trusted_proxy_enabled is True


def test_operator_run_authorizations_defaults_empty() -> None:
    settings = Settings()

    assert settings.operator_run_authorizations == {}


def test_operator_run_authorizations_accepts_explicit_mapping() -> None:
    settings = Settings(
        operator_run_authorizations={
            "operator_1": ["run_authorized", "run_review"],
            "operator_2": ["run_other"],
        }
    )

    assert settings.operator_run_authorizations == {
        "operator_1": ["run_authorized", "run_review"],
        "operator_2": ["run_other"],
    }


def test_operator_run_authorizations_parses_env_json(monkeypatch: pytest.MonkeyPatch) -> None:
    import json
    payload = {"operator_1": ["run_a", "run_b"], "operator_2": ["run_c"]}
    monkeypatch.setenv("OPERATOR_RUN_AUTHORIZATIONS", json.dumps(payload))

    settings = Settings()

    assert settings.operator_run_authorizations == payload
