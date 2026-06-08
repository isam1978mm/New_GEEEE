from __future__ import annotations

from app.config import Settings


def test_operator_auth_trusted_proxy_enabled_defaults_false() -> None:
    settings = Settings()

    assert settings.operator_auth_trusted_proxy_enabled is False


def test_operator_auth_trusted_proxy_enabled_accepts_explicit_true() -> None:
    settings = Settings(operator_auth_trusted_proxy_enabled=True)

    assert settings.operator_auth_trusted_proxy_enabled is True
