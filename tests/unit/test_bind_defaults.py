from __future__ import annotations

from app.config import Settings


def test_bind_defaults_to_loopback_and_network_bind_is_disabled() -> None:
    settings = Settings()

    assert settings.allow_network_bind is False
    assert settings.bind_host == "127.0.0.1"


def test_bind_host_switches_when_network_bind_is_enabled() -> None:
    settings = Settings(allow_network_bind=True)

    assert settings.bind_host == "0.0.0.0"
