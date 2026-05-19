from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import Settings
from app.db.models.artifact import Artifact
from app.db.models.enums import RunStatus
from app.db.models.run import Run
from app.errors import ArtifactClassError, ParityMetadataError, StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult
from app.pipeline.manifest import save_stage_manifest
from app.services.storage import initialize_run_storage


@dataclass(slots=True)
class StageExecutionRecord:
    stage_name: str
    artifact_count: int
    status: str


class Orchestrator:
    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: async_sessionmaker,
        stages: Iterable[Stage],
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.stages = list(stages)
        self._validate_stage_registry()

    async def run_run(self, run_id: str) -> list[StageExecutionRecord]:
        run = await self._get_run(run_id)
        run_dir = initialize_run_storage(self.settings, run_id)
        await self._set_run_status(run_id, RunStatus.RUNNING)

        records: list[StageExecutionRecord] = []
        for stage in self.stages:
            try:
                await self._persist_stage_status(run_id, stage.name, "running", stage, artifact_count=0)
                result = await stage.run(StageContext(run_id=run.id, settings=self.settings, run_dir=run_dir))
                self._validate_stage_result(result)
                await self._record_artifacts(run.id, result)
                await self._persist_stage_status(
                    run_id,
                    stage.name,
                    "done",
                    stage,
                    artifact_count=len(result.artifacts),
                    metadata=result.metadata,
                )
                records.append(
                    StageExecutionRecord(
                        stage_name=stage.name,
                        artifact_count=len(result.artifacts),
                        status="done",
                    )
                )
            except Exception:
                await self._persist_stage_status(
                    run_id,
                    stage.name,
                    "failed",
                    stage,
                    artifact_count=0,
                    metadata={"failure": "stage_failed"},
                )
                await self._set_run_status(run_id, RunStatus.FAILED)
                raise

        await self._set_run_status(run_id, RunStatus.DONE)
        return records

    def _validate_stage_registry(self) -> None:
        for stage in self.stages:
            if not isinstance(stage, Stage):
                raise ParityMetadataError("Stage registry must contain Stage instances.")
            if not stage.name:
                raise ParityMetadataError("Stage name is required.")
            if not isinstance(stage.parity_category, ParityCategory):
                raise ParityMetadataError(f"Stage {stage.name!r} is missing parity_category.")
            if stage.parity_category in {
                ParityCategory.PARITY_CORRECTS,
                ParityCategory.PARITY_REPLACES,
            } and not stage.parity_reason:
                raise ParityMetadataError(f"Stage {stage.name!r} is missing parity_reason.")

    def _validate_stage_result(self, result: StageResult) -> None:
        for artifact in result.artifacts:
            if artifact.artifact_class is None:
                raise ArtifactClassError()

    async def _get_run(self, run_id: str) -> Run:
        async with self.session_factory() as session:
            result = await session.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one_or_none()
            if run is None:
                raise StageError(f"Run {run_id!r} does not exist.")
            return run

    async def _set_run_status(self, run_id: str, status: RunStatus) -> None:
        async with self.session_factory() as session:
            result = await session.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one_or_none()
            if run is None:
                raise StageError(f"Run {run_id!r} does not exist.")
            run.status = status
            await session.commit()

    async def _record_artifacts(self, run_id: str, result: StageResult) -> None:
        async with self.session_factory() as session:
            for artifact in result.artifacts:
                session.add(
                    Artifact(
                        run_id=run_id,
                        name=artifact.name,
                        relative_path=artifact.relative_path,
                        size_bytes=artifact.size_bytes,
                        sha256=artifact.sha256,
                        artifact_class=artifact.artifact_class,
                        http_servable=artifact.http_servable,
                    )
                )
            await session.commit()

    async def _persist_stage_status(
        self,
        run_id: str,
        stage_name: str,
        status: str,
        stage: Stage,
        *,
        artifact_count: int,
        metadata: dict | None = None,
    ) -> None:
        payload = {
            "status": status,
            "artifact_count": artifact_count,
            "parity_category": stage.parity_category.value,
        }
        if stage.parity_reason:
            payload["parity_reason"] = stage.parity_reason
        if metadata:
            payload["metadata"] = metadata
        save_stage_manifest(self.settings, run_id, stage_name, payload)
