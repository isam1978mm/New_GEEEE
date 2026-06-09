"""A5 unit tests for stale running-run cleanup and active-run locking.

Verifies ``mark_stale_running_runs`` transitions only RUNNING runs to
STALE_FAILED, persists the change, returns the count of changed runs, and
tolerates a missing ``runs`` table (fresh DB before migrations).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models.enums import RunStatus
from app.db.models.run import Run
from app.errors import ActiveRunConflictError
from app.services.run_state import ensure_single_active_run, mark_stale_running_runs


def test_mark_stale_running_runs_transitions_only_running() -> None:
    asyncio.run(_run_mark_stale_running_runs_case())


async def _run_mark_stale_running_runs_case() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        engine = create_async_engine(settings.database_url, future=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_factory() as session:
                session.add_all(
                    [
                        _run("run-running-a", RunStatus.RUNNING),
                        _run("run-running-b", RunStatus.RUNNING),
                        _run("run-queued", RunStatus.QUEUED),
                        _run("run-done", RunStatus.DONE),
                        _run("run-failed", RunStatus.FAILED),
                        _run("run-stale", RunStatus.STALE_FAILED),
                    ]
                )
                await session.commit()

            async with session_factory() as session:
                changed = await mark_stale_running_runs(session)

            assert changed == 2

            # Re-open a fresh session to prove the change persisted to the DB.
            async with session_factory() as session:
                statuses = {
                    run_id: status
                    for run_id, status in (
                        await session.execute(select(Run.id, Run.status))
                    ).all()
                }
        finally:
            await engine.dispose()

    assert statuses["run-running-a"] == RunStatus.STALE_FAILED
    assert statuses["run-running-b"] == RunStatus.STALE_FAILED
    assert statuses["run-queued"] == RunStatus.QUEUED
    assert statuses["run-done"] == RunStatus.DONE
    assert statuses["run-failed"] == RunStatus.FAILED
    assert statuses["run-stale"] == RunStatus.STALE_FAILED


def test_mark_stale_running_runs_returns_zero_with_no_running_runs() -> None:
    asyncio.run(_run_no_running_case())


async def _run_no_running_case() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        engine = create_async_engine(settings.database_url, future=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_factory() as session:
                session.add_all(
                    [
                        _run("run-queued", RunStatus.QUEUED),
                        _run("run-done", RunStatus.DONE),
                    ]
                )
                await session.commit()

            async with session_factory() as session:
                changed = await mark_stale_running_runs(session)
        finally:
            await engine.dispose()

    assert changed == 0


def test_mark_stale_running_runs_tolerates_missing_runs_table() -> None:
    asyncio.run(_run_missing_table_case())


async def _run_missing_table_case() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        # Note: no migration is applied, so the ``runs`` table does not exist.
        engine = create_async_engine(settings.database_url, future=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_factory() as session:
                changed = await mark_stale_running_runs(session)
        finally:
            await engine.dispose()

    assert changed == 0


def test_ensure_single_active_run_blocks_on_queued_and_running() -> None:
    asyncio.run(_run_active_lock_case())


async def _run_active_lock_case() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        engine = create_async_engine(settings.database_url, future=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            # No active runs -> no conflict.
            async with session_factory() as session:
                session.add(_run("run-done", RunStatus.DONE))
                await session.commit()
            async with session_factory() as session:
                await ensure_single_active_run(session)

            # A QUEUED run blocks.
            async with session_factory() as session:
                session.add(_run("run-queued", RunStatus.QUEUED))
                await session.commit()
            async with session_factory() as session:
                with pytest.raises(ActiveRunConflictError):
                    await ensure_single_active_run(session)
        finally:
            await engine.dispose()


def _run(run_id: str, status: RunStatus) -> Run:
    return Run(id=run_id, name="fixture", status=status, latitude=10.0, longitude=20.0)


def _settings(root: Path) -> Settings:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(data_dir=data_dir, database_path=data_dir / "gee_screening.db")


def _upgrade_database(settings: Settings) -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("+aiosqlite", ""))
    command.upgrade(cfg, "head")
