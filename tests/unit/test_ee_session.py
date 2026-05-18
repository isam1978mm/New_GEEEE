from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.errors import EEInitializationError
from app.services.ee_session import initialize_ee_session


def test_initialize_ee_session_requires_service_account_values(tmp_path: Path) -> None:
    settings = Settings(
        ee_service_account_email=None,
        ee_service_account_key_path=None,
    )

    with pytest.raises(EEInitializationError):
        initialize_ee_session(settings)


def test_initialize_ee_session_requires_existing_key_file(tmp_path: Path) -> None:
    settings = Settings(
        ee_service_account_email="svc@example.com",
        ee_service_account_key_path=tmp_path / "missing.json",
    )

    with pytest.raises(EEInitializationError):
        initialize_ee_session(settings)


def test_initialize_ee_session_returns_stub_when_key_exists(tmp_path: Path) -> None:
    key_path = tmp_path / "service-account.json"
    key_path.write_text("{}", encoding="utf-8")
    settings = Settings(
        ee_service_account_email="svc@example.com",
        ee_service_account_key_path=key_path,
    )

    session = initialize_ee_session(settings)
    assert session["mode"] == "service_account"
    assert session["email"] == "svc@example.com"
    assert session["key_path"] == str(key_path)

