from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
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
from app.services.run_history import append_run_event
from app.services.storage import get_run_dir, initialize_run_storage, summarize_run_directory


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
        self.stages = self._with_optional_surface_change_stage(list(stages))
        self._validate_stage_registry()

    def _with_optional_surface_change_stage(self, stages: list[Stage]) -> list[Stage]:
        enabled = bool(getattr(self.settings, "option5_surface_change_enabled", True))
        real_execution = bool(getattr(self.settings, "ee_real_execution_enabled", False))
        if not enabled or not real_execution:
            return stages
        if any(stage.name == "surface_change" for stage in stages):
            return stages

        sar_index = next(
            (index for index, stage in enumerate(stages) if stage.name == "sar_rtc"),
            None,
        )
        if sar_index is None:
            return stages

        from app.pipeline.stages.surface_change import SurfaceChangeStage

        insertion_index = sar_index + 1
        return [
            *stages[:insertion_index],
            SurfaceChangeStage(),
            *stages[insertion_index:],
        ]

    async def run_run(self, run_id: str) -> list[StageExecutionRecord]:
        run = await self._get_run(run_id)
        run_dir = initialize_run_storage(self.settings, run_id)
        await self._set_run_status(run_id, RunStatus.RUNNING)
        append_run_event(self.settings, run_id, "run_started")

        records: list[StageExecutionRecord] = []
        for stage in self.stages:
            try:
                append_run_event(self.settings, run_id, "stage_started", stage_name=stage.name)
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
                append_run_event(self.settings, run_id, "stage_done", stage_name=stage.name)
            except Exception:
                await self._persist_stage_status(
                    run_id,
                    stage.name,
                    "failed",
                    stage,
                    artifact_count=0,
                    metadata={"failure": "stage_failed"},
                )
                append_run_event(self.settings, run_id, "stage_failed", stage_name=stage.name)
                await self._set_run_status(run_id, RunStatus.FAILED)
                await self._persist_run_disk_summary(run_id)
                append_run_event(self.settings, run_id, "run_failed")
                raise

        await self._set_run_status(run_id, RunStatus.DONE)
        await self._persist_run_disk_summary(run_id)
        append_run_event(self.settings, run_id, "run_done")
        return records

    async def run_stage_for_existing_run(
        self,
        run_id: str,
        stage: Stage,
        *,
        force: bool = False,
    ) -> StageExecutionRecord:
        """Execute one stage for an existing terminal run without changing run status."""

        self._validate_stage(stage)
        run = await self._get_run(run_id)
        if run.status in {RunStatus.QUEUED, RunStatus.RUNNING}:
            raise StageError("Cannot run an existing-run stage while the run is active.")

        run_dir = get_run_dir(self.settings, run_id)
        if not run_dir.is_dir():
            raise StageError("Run storage is unavailable.")

        stage_manifest_path = run_dir / f"stage_{stage.name}.manifest.json"
        if stage_manifest_path.exists() and not force:
            raise StageError(f"Stage {stage.name!r} already has a manifest; use force to rerun it.")

        try:
            append_run_event(self.settings, run_id, "stage_started", stage_name=stage.name)
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
            await self._persist_run_disk_summary(run_id)
            append_run_event(self.settings, run_id, "stage_done", stage_name=stage.name)
            return StageExecutionRecord(
                stage_name=stage.name,
                artifact_count=len(result.artifacts),
                status="done",
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
            await self._persist_run_disk_summary(run_id)
            append_run_event(self.settings, run_id, "stage_failed", stage_name=stage.name)
            raise

    def _validate_stage_registry(self) -> None:
        for stage in self.stages:
            self._validate_stage(stage)

    def _validate_stage(self, stage: Stage) -> None:
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
            for stage_artifact in result.artifacts:
                artifact = await session.scalar(
                    select(Artifact).where(
                        Artifact.run_id == run_id,
                        Artifact.name == stage_artifact.name,
                    )
                )
                if artifact is None:
                    artifact = Artifact(
                        run_id=run_id,
                        name=stage_artifact.name,
                        relative_path=stage_artifact.relative_path,
                        size_bytes=stage_artifact.size_bytes,
                        sha256=stage_artifact.sha256,
                        artifact_class=stage_artifact.artifact_class,
                        http_servable=stage_artifact.http_servable,
                    )
                    session.add(artifact)
                    continue

                artifact.relative_path = stage_artifact.relative_path
                artifact.size_bytes = stage_artifact.size_bytes
                artifact.sha256 = stage_artifact.sha256
                artifact.artifact_class = stage_artifact.artifact_class
                artifact.http_servable = stage_artifact.http_servable
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

    async def _persist_run_disk_summary(self, run_id: str) -> None:
        summary = summarize_run_directory(self.settings, run_id)
        async with self.session_factory() as session:
            result = await session.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one_or_none()
            if run is None:
                raise StageError(f"Run {run_id!r} does not exist.")
            run.disk_usage_bytes = summary.freed_bytes
            run.output_file_count = summary.deleted_files_count
            run.last_disk_scan_at = datetime.now(timezone.utc)
            await session.commit()
