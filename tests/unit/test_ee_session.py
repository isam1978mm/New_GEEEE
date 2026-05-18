from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from app.config import Settings
from app.errors import EEInitializationError
from app.services import ee_session


def test_initialize_ee_session_requires_service_account_values(tmp_path: Path) -> None:
    settings = Settings(
        ee_service_account_email=None,
        ee_service_account_key_path=None,
    )

    with pytest.raises(EEInitializationError):
        ee_session.initialize_ee_session(settings)


def test_initialize_ee_session_requires_existing_key_file(tmp_path: Path) -> None:
    settings = Settings(
        ee_service_account_email="svc@example.com",
        ee_service_account_key_path=tmp_path / "missing.json",
    )

    with pytest.raises(EEInitializationError):
        ee_session.initialize_ee_session(settings)


def test_initialize_ee_session_uses_service_account_credentials_and_initializes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    key_path = tmp_path / "service-account.json"
    key_path.write_text("{}", encoding="utf-8")
    settings = Settings(
        ee_service_account_email="svc@example.com",
        ee_service_account_key_path=key_path,
    )
    fake_credentials = object()
    credentials_mock = Mock(return_value=fake_credentials)
    initialize_mock = Mock()

    monkeypatch.setattr(ee_session.ee, "ServiceAccountCredentials", credentials_mock)
    monkeypatch.setattr(ee_session.ee, "Initialize", initialize_mock)

    session = ee_session.initialize_ee_session(settings)
    assert session["mode"] == "service_account"
    assert session["service_account_email"] == "svc@example.com"
    assert "key_path" not in session
    credentials_mock.assert_called_once_with("svc@example.com", str(key_path))
    initialize_mock.assert_called_once_with(fake_credentials)


def test_initialize_ee_session_converts_ee_exceptions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    key_path = tmp_path / "service-account.json"
    key_path.write_text("{}", encoding="utf-8")
    settings = Settings(
        ee_service_account_email="svc@example.com",
        ee_service_account_key_path=key_path,
    )
    monkeypatch.setattr(ee_session.ee, "ServiceAccountCredentials", Mock(side_effect=RuntimeError("boom")))

    with pytest.raises(EEInitializationError):
        ee_session.initialize_ee_session(settings)


def test_initialize_ee_session_converts_initialize_exceptions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    key_path = tmp_path / "service-account.json"
    key_path.write_text("{}", encoding="utf-8")
    settings = Settings(
        ee_service_account_email="svc@example.com",
        ee_service_account_key_path=key_path,
    )
    monkeypatch.setattr(ee_session.ee, "ServiceAccountCredentials", Mock(return_value=object()))
    monkeypatch.setattr(ee_session.ee, "Initialize", Mock(side_effect=RuntimeError("init failed")))

    with pytest.raises(EEInitializationError):
        ee_session.initialize_ee_session(settings)

