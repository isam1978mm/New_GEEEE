from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models.enums import RunStatus
from app.db.models.run import Run
from app.main import create_app
from app.services.storage import ensure_data_dirs


def test_startup_marks_running_runs_stale_failed(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "gee_screening.db",
    )

    asyncio.run(_create_running_run(settings))

    with TestClient(create_app(settings), raise_server_exceptions=False):
        pass

    run_status = asyncio.run(_fetch_run_status(settings, "run-startup"))
    assert run_status == RunStatus.STALE_FAILED


def test_startup_allows_existing_unmigrated_sqlite_db(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "gee_screening.db",
    )

    ensure_data_dirs(settings)
    settings.database_path.touch()

    with TestClient(create_app(settings), raise_server_exceptions=False) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def _create_running_run(settings: Settings) -> None:
    ensure_data_dirs(settings)
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Run(
                id="run-startup",
                name="startup cleanup",
                status=RunStatus.RUNNING,
                latitude=10.0,
                longitude=20.0,
            )
        )
        await session.commit()

    await engine.dispose()


async def _fetch_run_status(settings: Settings, run_id: str) -> RunStatus:
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        result = await session.execute(select(Run.status).where(Run.id == run_id))
        status = result.scalar_one()

    await engine.dispose()
    return status
