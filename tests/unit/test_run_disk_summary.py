"""A6 verification: run disk summary is persisted on terminal state.

Proves that ``Orchestrator.run_run`` persists ``disk_usage_bytes``,
``output_file_count`` and ``last_disk_scan_at`` when a run completes (DONE) and
when a run fails (FAILED), that the persisted values match
``summarize_run_directory``, and that scanning never deletes or moves run files.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models.artifact import Artifact
from app.db.models.enums import ArtifactClass, RunStatus
from app.db.models.run import Run
from app.pipeline._base import (
    ParityCategory,
    Stage,
    StageContext,
    StageResult,
    build_stage_artifact,
)
from app.pipeline.orchestrator import Orchestrator
from app.services.storage import ensure_data_dirs, summarize_run_directory


class WritingStage(Stage):
    name = "writing"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Replaces notebook orchestration side effects with app-managed execution."

    async def run(self, context: StageContext) -> StageResult:
        marker = context.run_dir / "marker.txt"
        marker.write_text("disk summary marker payload", encoding="utf-8")
        nested = context.run_dir / "nested"
        nested.mkdir(parents=True, exist_ok=True)
        (nested / "extra.bin").write_bytes(b"0123456789")
        return StageResult(
            artifacts=[
                build_stage_artifact(
                    name="marker",
                    relative_path="marker.txt",
                    artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                    size_bytes=marker.stat().st_size,
                )
            ],
            metadata={"note": "ok"},
        )


class WriteThenFailStage(Stage):
    name = "write_then_fail"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Replaces notebook orchestration side effects with app-managed execution."

    async def run(self, context: StageContext) -> StageResult:
        (context.run_dir / "partial.txt").write_text("partial output before failure", encoding="utf-8")
        raise RuntimeError("synthetic stage failure for disk-summary coverage")


def test_successful_run_persists_disk_summary() -> None:
    asyncio.run(_run_success_case())


async def _run_success_case() -> None:
    with TemporaryDirectory() as temp_dir:
        settings, session_factory, engine = await _bootstrap(Path(temp_dir), "run-done")
        try:
            orchestrator = Orchestrator(
                settings=settings, session_factory=session_factory, stages=[WritingStage()]
            )
            await orchestrator.run_run("run-done")

            marker = settings.data_dir / "runs" / "run-done" / "marker.txt"
            assert marker.exists()

            summary = summarize_run_directory(settings, "run-done")
            async with session_factory() as session:
                run = await session.scalar(select(Run).where(Run.id == "run-done"))
                artifacts = (
                    await session.scalars(select(Artifact).where(Artifact.run_id == "run-done"))
                ).all()

            assert run.status == RunStatus.DONE
            assert run.disk_usage_bytes is not None and run.disk_usage_bytes > 0
            assert run.output_file_count is not None and run.output_file_count > 0
            assert run.last_disk_scan_at is not None
            # File count matches exactly: the persisted scan and this rescan see the
            # same set of files. The persisted byte total is captured just before the
            # terminal ``run_done`` event rewrites the single history file, so the
            # post-run rescan total is >= the persisted total.
            assert run.output_file_count == summary.deleted_files_count
            assert 0 < run.disk_usage_bytes <= summary.freed_bytes
            assert len(artifacts) == 1
        finally:
            await engine.dispose()


def test_failed_run_persists_disk_summary() -> None:
    asyncio.run(_run_failure_case())


async def _run_failure_case() -> None:
    with TemporaryDirectory() as temp_dir:
        settings, session_factory, engine = await _bootstrap(Path(temp_dir), "run-fail")
        try:
            orchestrator = Orchestrator(
                settings=settings, session_factory=session_factory, stages=[WriteThenFailStage()]
            )
            with pytest.raises(RuntimeError):
                await orchestrator.run_run("run-fail")

            partial = settings.data_dir / "runs" / "run-fail" / "partial.txt"
            assert partial.exists()
            failed_manifest = settings.data_dir / "runs" / "run-fail" / "stage_write_then_fail.manifest.json"
            assert failed_manifest.exists()

            summary = summarize_run_directory(settings, "run-fail")
            async with session_factory() as session:
                run = await session.scalar(select(Run).where(Run.id == "run-fail"))

            assert run.status == RunStatus.FAILED
            assert run.disk_usage_bytes is not None and run.disk_usage_bytes > 0
            assert run.output_file_count is not None and run.output_file_count > 0
            assert run.last_disk_scan_at is not None
            # File count matches exactly; the persisted byte total is captured just
            # before the terminal ``run_failed`` event rewrites the history file.
            assert run.output_file_count == summary.deleted_files_count
            assert 0 < run.disk_usage_bytes <= summary.freed_bytes
        finally:
            await engine.dispose()


def test_disk_summary_scan_does_not_delete_or_move_run_files() -> None:
    asyncio.run(_run_no_mutation_case())


async def _run_no_mutation_case() -> None:
    with TemporaryDirectory() as temp_dir:
        settings, session_factory, engine = await _bootstrap(Path(temp_dir), "run-keep")
        try:
            orchestrator = Orchestrator(
                settings=settings, session_factory=session_factory, stages=[WritingStage()]
            )
            await orchestrator.run_run("run-keep")

            run_dir = settings.data_dir / "runs" / "run-keep"
            files_after_first = sorted(p.relative_to(run_dir).as_posix() for p in run_dir.rglob("*") if p.is_file())

            # Scanning again must be read-only: the same files remain in place.
            summarize_run_directory(settings, "run-keep")
            files_after_second = sorted(p.relative_to(run_dir).as_posix() for p in run_dir.rglob("*") if p.is_file())

            assert files_after_first == files_after_second
            assert "marker.txt" in files_after_second
            assert "nested/extra.bin" in files_after_second
        finally:
            await engine.dispose()


def test_disk_summary_does_not_mark_active_run_terminal() -> None:
    """summarize_run_directory is a read-only scan; it must not change run status."""
    asyncio.run(_run_active_status_case())


async def _run_active_status_case() -> None:
    with TemporaryDirectory() as temp_dir:
        settings, session_factory, engine = await _bootstrap(
            Path(temp_dir), "run-active", status=RunStatus.RUNNING
        )
        try:
            run_dir = settings.data_dir / "runs" / "run-active"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "in_progress.txt").write_text("still running", encoding="utf-8")

            summarize_run_directory(settings, "run-active")

            async with session_factory() as session:
                status = await session.scalar(select(Run.status).where(Run.id == "run-active"))
            assert status == RunStatus.RUNNING
        finally:
            await engine.dispose()


async def _bootstrap(tmp_path: Path, run_id: str, *, status: RunStatus = RunStatus.QUEUED):
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    ensure_data_dirs(settings)
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(Run(id=run_id, name="demo", status=status, latitude=1.0, longitude=2.0))
        await session.commit()
    return settings, session_factory, engine
