from __future__ import annotations

import asyncio
import json
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
from app.errors import StageError
from app.pipeline._base import (
    ParityCategory,
    Stage,
    StageContext,
    StageResult,
    build_stage_artifact,
)
from app.services.artifact_response import is_expected_download_filename, public_download_filename
from app.services.storage import ensure_data_dirs, read_manifest
from scripts.run_surface_change_for_existing_run import run_surface_change_for_existing_run


class DemoSurfaceChangeStage(Stage):
    name = "surface_change"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Test-only deterministic surface-change replacement."

    async def run(self, context: StageContext) -> StageResult:
        summary_path = context.run_dir / "option5_surface_change_summary.json"
        summary_path.write_text(
            json.dumps(
                {
                    "schema": "option5_surface_change_summary_v1",
                    "status": "available",
                    "warnings": [
                        "radar_backscatter_change_only",
                        "not_depth",
                        "not_settlement",
                    ],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return StageResult(
            artifacts=[
                build_stage_artifact(
                    name="option5_surface_change_summary",
                    relative_path=summary_path.name,
                    artifact_class=ArtifactClass.REDACTED_PUBLIC,
                    size_bytes=summary_path.stat().st_size,
                )
            ],
            metadata={
                "status": "available",
                "summary_artifact": "option5_surface_change_summary",
            },
        )


def test_surface_change_public_download_filename_matches_frontend_route() -> None:
    assert public_download_filename("option5_surface_change_summary") == "option5_surface_change_summary.json"
    assert is_expected_download_filename(
        artifact_name="option5_surface_change_summary",
        download_filename="option5_surface_change_summary.json",
    ) is True


def test_existing_run_surface_change_registers_artifact_and_preserves_status() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_existing_run_surface_change_test(Path(temp_dir)))


def test_existing_run_surface_change_requires_explicit_force_for_rerun() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_existing_run_force_guard_test(Path(temp_dir)))


def test_real_existing_run_surface_change_requires_real_ee_setting(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "db.sqlite",
        ee_real_execution_enabled=False,
        option5_surface_change_enabled=True,
    )

    with pytest.raises(RuntimeError, match="EE_REAL_EXECUTION_ENABLED"):
        asyncio.run(
            run_surface_change_for_existing_run(
                run_id="run-1",
                settings=settings,
            )
        )


async def _build_done_run(tmp_path: Path) -> tuple[Settings, object, async_sessionmaker]:
    settings = Settings(
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "db.sqlite",
        ee_real_execution_enabled=False,
        option5_surface_change_enabled=True,
    )
    ensure_data_dirs(settings)
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Run(
                id="run-1",
                name="completed",
                status=RunStatus.DONE,
                latitude=1.0,
                longitude=2.0,
            )
        )
        await session.commit()

    run_dir = settings.data_dir / "runs" / "run-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    return settings, engine, session_factory


async def _run_existing_run_surface_change_test(tmp_path: Path) -> None:
    settings, engine, session_factory = await _build_done_run(tmp_path)
    try:
        result = await run_surface_change_for_existing_run(
            run_id="run-1",
            settings=settings,
            stage=DemoSurfaceChangeStage(),
            session_factory=session_factory,
        )

        assert result["stage"] == "surface_change"
        assert result["stage_status"] == "done"
        assert result["surface_change_status"] == "available"
        assert result["summary_filename"] == "option5_surface_change_summary.json"
        assert result["run_status_preserved"] is True

        async with session_factory() as session:
            run_status = await session.scalar(select(Run.status).where(Run.id == "run-1"))
            artifact = await session.scalar(
                select(Artifact).where(
                    Artifact.run_id == "run-1",
                    Artifact.name == "option5_surface_change_summary",
                )
            )

        assert run_status == RunStatus.DONE
        assert artifact is not None
        assert artifact.relative_path == "option5_surface_change_summary.json"
        assert artifact.artifact_class == ArtifactClass.REDACTED_PUBLIC
        assert artifact.http_servable is True

        manifest = read_manifest(
            settings.data_dir / "runs" / "run-1" / "stage_surface_change.manifest.json"
        )
        assert manifest["status"] == "done"
        assert manifest["artifact_count"] == 1
        assert manifest["metadata"]["status"] == "available"
    finally:
        await engine.dispose()


async def _run_existing_run_force_guard_test(tmp_path: Path) -> None:
    settings, engine, session_factory = await _build_done_run(tmp_path)
    try:
        first = await run_surface_change_for_existing_run(
            run_id="run-1",
            settings=settings,
            stage=DemoSurfaceChangeStage(),
            session_factory=session_factory,
        )
        assert first["artifact_count"] == 1

        with pytest.raises(StageError, match="already has a manifest"):
            await run_surface_change_for_existing_run(
                run_id="run-1",
                settings=settings,
                stage=DemoSurfaceChangeStage(),
                session_factory=session_factory,
            )

        forced = await run_surface_change_for_existing_run(
            run_id="run-1",
            settings=settings,
            stage=DemoSurfaceChangeStage(),
            session_factory=session_factory,
            force=True,
        )
        assert forced["artifact_count"] == 1

        async with session_factory() as session:
            artifact_count = len(
                list(
                    (
                        await session.scalars(
                            select(Artifact).where(
                                Artifact.run_id == "run-1",
                                Artifact.name == "option5_surface_change_summary",
                            )
                        )
                    ).all()
                )
            )
        assert artifact_count == 1
    finally:
        await engine.dispose()
