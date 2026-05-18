from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.errors import EEInitializationError


def initialize_ee_session(settings: Settings) -> dict[str, str]:
    if not settings.ee_service_account_email or not settings.ee_service_account_key_path:
        raise EEInitializationError()

    key_path = Path(settings.ee_service_account_key_path)
    if not key_path.is_file():
        raise EEInitializationError()

    return {
        "mode": "service_account",
        "email": settings.ee_service_account_email,
        "key_path": str(key_path),
    }

