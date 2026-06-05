from __future__ import annotations

import asyncio
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import Settings
from app.db.models import Run
from app.main import create_app


FORBIDDEN_ARTIFACT_SUFFIXES = {
    ".tif",
    ".tiff",
    ".npy",
    ".geojson",
    ".kmz",
    ".kml",
    ".html",
    ".png",
    ".jpg",
    ".jpeg",
    ".csv",
}


def test_earth_engine_plan_route_returns_safe_dry_run_metadata(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        monkeypatch.setattr("app.api.runs.enqueue_core_pipeline_run", _raise_if_run_starts)

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post(
                "/earth-engine/plan",
                json={
                    "lat": 35.59499,
                    "lon": 36.12694,
                    "acquisition_start": "2026-01-01",
                    "acquisition_end": "2026-01-31",
                    "cloud_percent_max": 20,
                    "sar_orbit": "any",
                    "sar_polarization": "VV",
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["dry_run"] is True
        assert payload["execution_status"] == "auth_not_configured"
        assert payload["auth_readiness"]["status"] == "auth_not_configured"
        assert payload["grid_preview"]["width_cells"] == 640
        assert payload["planned_provider_families"]
        assert asyncio.run(_run_count(settings)) == 0
        _assert_no_forbidden_public_fields(response.text)


def test_invalid_latitude_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post(
                "/earth-engine/plan",
                json={
                    "lat": 91.0,
                    "lon": 36.0,
                    "acquisition_start": "2026-01-01",
                    "acquisition_end": "2026-01-31",
                },
            )

        assert response.status_code == 422
        assert response.json() == {"error": "validation_error", "message": "Request could not be processed."}
        _assert_no_forbidden_public_fields(response.text)


def test_invalid_longitude_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post(
                "/earth-engine/plan",
                json={
                    "lat": 35.0,
                    "lon": 181.0,
                    "acquisition_start": "2026-01-01",
                    "acquisition_end": "2026-01-31",
                },
            )

        assert response.status_code == 422
        assert response.json() == {"error": "validation_error", "message": "Request could not be processed."}
        _assert_no_forbidden_public_fields(response.text)


def test_invalid_date_range_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post(
                "/earth-engine/plan",
                json={
                    "lat": 35.0,
                    "lon": 36.0,
                    "acquisition_start": "2026-02-01",
                    "acquisition_end": "2026-01-01",
                },
            )

        assert response.status_code == 422
        assert response.json() == {"error": "validation_error", "message": "Request could not be processed."}
        _assert_no_forbidden_public_fields(response.text)


def test_plan_route_does_not_create_artifacts_or_run_directory() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post(
                "/earth-engine/plan",
                json={
                    "lat": 35.0,
                    "lon": 36.0,
                    "acquisition_start": "2026-01-01",
                    "acquisition_end": "2026-01-31",
                },
            )

        assert response.status_code == 200
        runs_dir = settings.data_dir / "runs"
        created_artifacts = [
            path
            for path in settings.data_dir.rglob("*")
            if path.suffix.casefold() in FORBIDDEN_ARTIFACT_SUFFIXES
        ]
        assert created_artifacts == []
        assert not runs_dir.exists() or list(runs_dir.iterdir()) == []


def test_plan_route_does_not_import_earth_engine_in_default_dry_run(monkeypatch) -> None:
    imported = False

    def fake_import():
        nonlocal imported
        imported = True
        raise AssertionError("default planning must not import Earth Engine")

    monkeypatch.setattr("app.services.earth_engine_control.import_earth_engine", fake_import)
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.post(
                "/earth-engine/plan",
                json={
                    "lat": 35.0,
                    "lon": 36.0,
                    "acquisition_start": "2026-01-01",
                    "acquisition_end": "2026-01-31",
                },
            )

    assert response.status_code == 200
    assert imported is False


def _raise_if_run_starts(*args, **kwargs) -> None:
    raise AssertionError("Earth Engine planning must not start a backend run.")


def _settings(root: Path) -> Settings:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        data_dir=data_dir,
        database_path=data_dir / "gee_screening.db",
        ee_service_account_email=None,
        ee_service_account_key_path=None,
        ee_real_execution_enabled=False,
    )


def _upgrade_database(settings: Settings) -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("+aiosqlite", ""))
    command.upgrade(cfg, "head")


async def _run_count(settings: Settings) -> int:
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        result = await connection.execute(select(Run))
        rows = result.fetchall()
    await engine.dispose()
    return len(rows)


def _assert_no_forbidden_public_fields(text: str) -> None:
    lowered = text.casefold()
    for forbidden in (
        "latitude",
        "longitude",
        "bounds",
        "bbox",
        "crs",
        "transform",
        "pixel_size",
        "relative_path",
        "download",
        "artifact",
        "filesystem",
        "sha256",
        "hash",
        "secret",
        "credential",
        "service_account",
    ):
        assert forbidden not in lowered
