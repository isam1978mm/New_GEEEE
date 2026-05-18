from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models.run import Run
from app.db.models.enums import RunStatus
from app.errors import ActiveRunConflictError
from app.services.storage import ensure_data_dirs
from app.services.run_state import ensure_single_active_run, mark_stale_running_runs


def test_mark_stale_running_runs_updates_running_runs() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_mark_stale_running_runs_test(Path(temp_dir)))


def test_ensure_single_active_run_rejects_active_runs() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_active_run_rejection_test(Path(temp_dir)))


def test_ensure_single_active_run_allows_inactive_runs() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_inactive_run_allowed_test(Path(temp_dir)))


def test_mark_stale_running_runs_returns_zero_when_runs_table_missing() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_missing_runs_table_test(Path(temp_dir)))


async def _run_mark_stale_running_runs_test(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    ensure_data_dirs(settings)
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Run(
                id="run-1",
                name="test",
                status=RunStatus.RUNNING,
                latitude=10.0,
                longitude=20.0,
            )
        )
        await session.commit()
        updated_count = await mark_stale_running_runs(session)
        assert updated_count == 1

        result = await session.execute(select(Run).where(Run.id == "run-1"))
        run = result.scalar_one()
        assert run.status == RunStatus.STALE_FAILED

    await engine.dispose()


async def _run_active_run_rejection_test(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    ensure_data_dirs(settings)
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Run(
                id="run-1",
                name="test",
                status=RunStatus.QUEUED,
                latitude=10.0,
                longitude=20.0,
            )
        )
        await session.commit()

        with pytest.raises(ActiveRunConflictError):
            await ensure_single_active_run(session)

    await engine.dispose()


async def _run_inactive_run_allowed_test(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    ensure_data_dirs(settings)
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Run(
                id="run-1",
                name="test",
                status=RunStatus.DONE,
                latitude=10.0,
                longitude=20.0,
            )
        )
        await session.commit()

        await ensure_single_active_run(session)

    await engine.dispose()


async def _run_missing_runs_table_test(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    ensure_data_dirs(settings)
    engine = create_async_engine(settings.database_url, future=True)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        updated_count = await mark_stale_running_runs(session)
        assert updated_count == 0

    await engine.dispose()
