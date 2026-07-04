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
from app.services.storage import ensure_data_dirs, read_manifest


class DemoStage(Stage):
    name = "demo"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Replaces notebook orchestration side effects with app-managed execution."

    async def run(self, context: StageContext) -> StageResult:
        artifact_path = context.run_dir / "demo.txt"
        artifact_path.write_text("demo", encoding="utf-8")
        return StageResult(
            artifacts=[
                build_stage_artifact(
                    name="demo",
                    relative_path="demo.txt",
                    artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                    size_bytes=artifact_path.stat().st_size,
                )
            ],
            metadata={"note": "ok"},
        )


class FailingStage(Stage):
    name = "failing"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Replaces notebook orchestration side effects with app-managed execution."

    async def run(self, context: StageContext) -> StageResult:
        raise RuntimeError(
            "raw failure lat=12.34 path=C:/secret/run-1/demo.txt hash=abc123 request_input=boom"
        )


def test_orchestrator_persists_stage_status_and_artifacts() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_orchestrator_test(Path(temp_dir)))


def test_orchestrator_persists_safe_failed_stage_manifest() -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_orchestrator_failure_test(Path(temp_dir)))


async def _run_orchestrator_test(tmp_path: Path) -> None:
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
                name="demo",
                status=RunStatus.QUEUED,
                latitude=1.0,
                longitude=2.0,
            )
        )
        await session.commit()

    orchestrator = Orchestrator(
        settings=settings,
        session_factory=session_factory,
        stages=[DemoStage()],
    )
    records = await orchestrator.run_run("run-1")
    assert len(records) == 1
    assert records[0].stage_name == "demo"
    assert records[0].status == "done"

    async with session_factory() as session:
        run_status = await session.scalar(select(Run.status).where(Run.id == "run-1"))
        assert run_status == RunStatus.DONE

        artifact = await session.scalar(select(Artifact).where(Artifact.run_id == "run-1"))
        assert artifact is not None
        assert artifact.artifact_class == ArtifactClass.LOCAL_SENSITIVE

    manifest = read_manifest(settings.data_dir / "runs" / "run-1" / "stage_demo.manifest.json")
    assert manifest["status"] == "done"
    assert manifest["artifact_count"] == 1
    assert manifest["parity_category"] == ParityCategory.PARITY_REPLACES.value
    assert manifest["artifact_class"] == ArtifactClass.LOCAL_SENSITIVE.value

    await engine.dispose()


async def _run_orchestrator_failure_test(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    ensure_data_dirs(settings)
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Run(
                id="run-fail",
                name="demo",
                status=RunStatus.QUEUED,
                latitude=1.0,
                longitude=2.0,
            )
        )
        await session.commit()

    orchestrator = Orchestrator(
        settings=settings,
        session_factory=session_factory,
        stages=[FailingStage()],
    )

    with pytest.raises(RuntimeError):
        await orchestrator.run_run("run-fail")

    async with session_factory() as session:
        run_status = await session.scalar(select(Run.status).where(Run.id == "run-fail"))
        assert run_status == RunStatus.FAILED

    manifest = read_manifest(settings.data_dir / "runs" / "run-fail" / "stage_failing.manifest.json")
    assert manifest["status"] == "failed"
    assert manifest["artifact_count"] == 0
    assert manifest["parity_category"] == ParityCategory.PARITY_REPLACES.value
    assert manifest["parity_reason"] == FailingStage.parity_reason
    assert manifest["metadata"] == {"failure": "stage_failed"}

    manifest_text = (settings.data_dir / "runs" / "run-fail" / "stage_failing.manifest.json").read_text(
        encoding="utf-8"
    )
    assert "raw failure" not in manifest_text
    assert "12.34" not in manifest_text
    assert "C:/secret/run-1/demo.txt" not in manifest_text
    assert "abc123" not in manifest_text
    assert "request_input=boom" not in manifest_text

    await engine.dispose()
