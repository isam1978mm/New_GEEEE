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


def test_oidc_settings_default_to_disabled_and_none() -> None:
    settings = Settings()

    assert settings.operator_auth_oidc_enabled is False
    assert settings.operator_auth_oidc_issuer_url is None
    assert settings.operator_auth_oidc_client_id is None
    assert settings.operator_auth_oidc_jwks_uri is None


def test_oidc_settings_accept_explicit_constructor_values() -> None:
    settings = Settings(
        operator_auth_oidc_enabled=True,
        operator_auth_oidc_issuer_url="https://issuer.example.test",
        operator_auth_oidc_client_id="gee-operator-ui",
        operator_auth_oidc_jwks_uri="https://issuer.example.test/.well-known/jwks.json",
    )

    assert settings.operator_auth_oidc_enabled is True
    assert settings.operator_auth_oidc_issuer_url == "https://issuer.example.test"
    assert settings.operator_auth_oidc_client_id == "gee-operator-ui"
    assert settings.operator_auth_oidc_jwks_uri == "https://issuer.example.test/.well-known/jwks.json"


def test_oidc_settings_parse_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPERATOR_AUTH_OIDC_ENABLED", "true")
    monkeypatch.setenv("OPERATOR_AUTH_OIDC_ISSUER_URL", "https://issuer.example.test")
    monkeypatch.setenv("OPERATOR_AUTH_OIDC_CLIENT_ID", "gee-operator-ui")
    monkeypatch.setenv("OPERATOR_AUTH_OIDC_JWKS_URI", "https://issuer.example.test/.well-known/jwks.json")

    settings = Settings()

    assert settings.operator_auth_oidc_enabled is True
    assert settings.operator_auth_oidc_issuer_url == "https://issuer.example.test"
    assert settings.operator_auth_oidc_client_id == "gee-operator-ui"
    assert settings.operator_auth_oidc_jwks_uri == "https://issuer.example.test/.well-known/jwks.json"
