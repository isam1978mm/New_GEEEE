#!/usr/bin/env python3
"""Probe whether CI has usable Earth Engine credentials without exposing secrets.

This script does not run the RMA scientific comparison. It writes only a bounded
status report indicating whether a supported credential path can initialize
Earth Engine and read one public collection count.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

OUT_DIR = Path("artifacts/rma_option2_auth_probe")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "earth_engine_auth_probe.json"


def write_result(payload: dict[str, Any]) -> None:
    OUT_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


def first_nonempty(names: list[str]) -> tuple[str | None, str | None]:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return name, value
    return None, None


def main() -> int:
    result: dict[str, Any] = {
        "status": "AUTH_REQUIRED",
        "earth_engine_initialized": False,
        "collection_read_test": False,
        "credential_source": None,
        "project_source": None,
        "secret_values_printed": False,
        "scientific_query_executed": False,
        "app_modified": False,
        "training_started": False,
    }

    try:
        import ee  # type: ignore
    except Exception as exc:  # pragma: no cover - CI diagnostic
        result["status"] = "DEPENDENCY_ERROR"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:500]
        write_result(result)
        return 0

    project_name, project_value = first_nonempty(
        ["EE_PROJECT", "GEE_PROJECT", "GOOGLE_CLOUD_PROJECT"]
    )
    if project_name:
        result["project_source"] = project_name

    service_name, service_json = first_nonempty(
        [
            "EE_SERVICE_ACCOUNT_JSON",
            "GEE_SERVICE_ACCOUNT_JSON",
            "GOOGLE_SERVICE_ACCOUNT_JSON",
        ]
    )
    token_name, token_json = first_nonempty(
        ["EARTHENGINE_TOKEN", "EE_CREDENTIALS_JSON", "GEE_CREDENTIALS_JSON"]
    )

    try:
        if service_json:
            parsed = json.loads(service_json)
            client_email = parsed.get("client_email")
            private_key = parsed.get("private_key")
            if not client_email or not private_key:
                raise ValueError("service-account JSON is missing client_email or private_key")
            key_path = OUT_DIR / "service-account.json"
            key_path.write_text(json.dumps(parsed), encoding="utf-8")
            os.chmod(key_path, 0o600)
            credentials = ee.ServiceAccountCredentials(client_email, str(key_path))
            project = project_value or parsed.get("project_id")
            ee.Initialize(credentials=credentials, project=project)
            result["credential_source"] = service_name
        elif token_json:
            parsed = json.loads(token_json)
            config_dir = Path.home() / ".config" / "earthengine"
            config_dir.mkdir(parents=True, exist_ok=True)
            credentials_path = config_dir / "credentials"
            credentials_path.write_text(json.dumps(parsed), encoding="utf-8")
            os.chmod(credentials_path, 0o600)
            ee.Initialize(project=project_value)
            result["credential_source"] = token_name
        else:
            # This succeeds only when the runner already has application-default
            # or Earth Engine user credentials. No interactive authentication is attempted.
            ee.Initialize(project=project_value)
            result["credential_source"] = "runner_default_credentials"

        result["earth_engine_initialized"] = True
        count = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterDate("2024-01-01", "2024-01-03")
            .limit(1)
            .size()
            .getInfo()
        )
        result["collection_read_test"] = isinstance(count, (int, float))
        result["status"] = "AUTH_READY"
    except Exception as exc:  # pragma: no cover - CI diagnostic
        result["status"] = "AUTH_REQUIRED"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:500]
    finally:
        for private_file in [OUT_DIR / "service-account.json"]:
            if private_file.exists():
                private_file.unlink()
        credential_file = Path.home() / ".config" / "earthengine" / "credentials"
        if credential_file.exists() and token_json:
            credential_file.unlink()

    write_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
