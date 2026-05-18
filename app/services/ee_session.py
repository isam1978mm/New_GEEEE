from __future__ import annotations

from pathlib import Path

import ee

from app.config import Settings
from app.errors import EEInitializationError


def initialize_ee_session(settings: Settings) -> dict[str, str]:
    email = settings.ee_service_account_email
    key_path_value = settings.ee_service_account_key_path
    if not email or not key_path_value:
        raise EEInitializationError()

    key_path = Path(key_path_value)
    if not key_path.is_file():
        raise EEInitializationError()

    try:
        credentials = ee.ServiceAccountCredentials(email, str(key_path))
        ee.Initialize(credentials)
    except Exception as exc:
        raise EEInitializationError() from exc

    return {"mode": "service_account", "service_account_email": email}

