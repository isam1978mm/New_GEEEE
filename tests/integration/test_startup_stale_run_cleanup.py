"""Startup integration tests for orphaned active-run recovery."""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

import pytest

for _heavy_module in (
    "rasterio",
    "rasterio.transform",
    "rasterio.features",
    "rasterio.warp",
    "rasterio.enums",
    "ee",
):
    sys.modules.setdefault(_heavy_module, MagicMock())

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models.enums import RunStatus
from app.db.models.run import Run
from app.main import create_app
from app.services.storage import ensure_data_dirs

ABSOLUTE_PATH_PATTERN = re.compile(r"(?i)([A-Z]:\\|/Users/|/home/|/tmp/)")


@pytest.mark.parametrize("active_status", [RunStatus.QUEUED, RunStatus.RUNNING])
def test_startup_marks_preexisting_active_run_stale_failed(
    active_status: RunStatus,
) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        asyncio.run(_seed_run(settings, "run-active", active_status))
        run_dir = settings.data_dir / "runs" / "run-active"
        run_dir.mkdir(parents=True, exist_ok=True)
        marker = run_dir / "keep.txt"
        marker.write_text("keep", encoding="utf-8")

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            status = asyncio.run(_fetch_status(settings, "run-active"))
            detail = client.get("/runs/run-active")

        assert status == RunStatus.STALE_FAILED
        assert marker.exists()
        assert detail.status_code == 200
        assert detail.json()["status"] == "stale_failed"
        _assert_no_leakage(detail.text)


def test_startup_leaves_terminal_runs_unchanged() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        asyncio.run(_seed_run(settings, "run-done", RunStatus.DONE))
        asyncio.run(_seed_run(settings, "run-failed", RunStatus.FAILED))
        asyncio.run(_seed_run(settings, "run-stale", RunStatus.STALE_FAILED))

        with TestClient(create_app(settings), raise_server_exceptions=False):
            assert asyncio.run(_fetch_status(settings, "run-done")) == RunStatus.DONE
            assert asyncio.run(_fetch_status(settings, "run-failed")) == RunStatus.FAILED
            assert asyncio.run(_fetch_status(settings, "run-stale")) == RunStatus.STALE_FAILED


@pytest.mark.parametrize("active_status", [RunStatus.QUEUED, RunStatus.RUNNING])
def test_recovered_active_run_no_longer_blocks_new_run(
    monkeypatch,
    active_status: RunStatus,
) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        asyncio.run(_seed_run(settings, "run-active", active_status))
        monkeypatch.setattr(
            "app.api.runs.enqueue_core_pipeline_run",
            _noop_background_runner,
        )

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            assert asyncio.run(_fetch_status(settings, "run-active")) == RunStatus.STALE_FAILED
            response = client.post(
                "/runs",
                json={
                    "lat": 35.59499,
                    "lon": 36.12694,
                    "name": "fresh run",
                },
            )

        assert response.status_code == 201
        assert response.json()["status"] == "queued"
        _assert_no_leakage(response.text)


def test_startup_tolerates_existing_unmigrated_sqlite_db() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        ensure_data_dirs(settings)
        settings.database_path.touch()

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get("/healthz")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def _noop_background_runner(run_id: str, settings: Settings) -> None:
    del run_id, settings


async def _seed_run(
    settings: Settings,
    run_id: str,
    status: RunStatus,
) -> None:
    ensure_data_dirs(settings)
    _upgrade_database(settings)
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Run(
                id=run_id,
                name="startup fixture",
                status=status,
                latitude=10.0,
                longitude=20.0,
            )
        )
        await session.commit()
    await engine.dispose()


async def _fetch_status(settings: Settings, run_id: str) -> RunStatus:
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        status = (
            await session.execute(
                select(Run.status).where(Run.id == run_id)
            )
        ).scalar_one()
    await engine.dispose()
    return status


def _settings(root: Path) -> Settings:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(data_dir=data_dir, database_path=data_dir / "gee_screening.db")


def _upgrade_database(settings: Settings) -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = Config("alembic.ini")
    cfg.set_main_option(
        "sqlalchemy.url",
        settings.database_url.replace("+aiosqlite", ""),
    )
    command.upgrade(cfg, "head")


def _assert_no_leakage(text: str) -> None:
    assert ABSOLUTE_PATH_PATTERN.search(text) is None
    lowered = text.casefold()
    for forbidden in (
        "latitude",
        "longitude",
        "geometry",
        "bounds",
        "transform",
        "10.0",
        "20.0",
    ):
        assert forbidden not in lowered
