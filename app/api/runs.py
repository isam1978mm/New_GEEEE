from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import Artifact, ArtifactClass, Run, RunDeletionAudit, RunStatus
from app.deps import get_db_session, get_settings_from_request
from app.errors import ActiveRunConflictError, AppError
from app.pipeline.manifest import save_grid_manifest
from app.pipeline.orchestrator import Orchestrator
from app.pipeline.stages.alignment_qa import AlignmentQaStage
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.dem import DemStage
from app.pipeline.stages.field_ops_exports import FieldOpsExportsStage
from app.pipeline.stages.feature_stacks import FeatureStacksStage
from app.pipeline.stages.focus_mask import FocusMaskStage
from app.pipeline.stages.gps_compare import GpsComparisonStage
from app.pipeline.stages.grid import GridSpec, GridStage, build_run_grid
from app.pipeline.stages.hypercube import HypercubeStage
from app.pipeline.stages.location_exports import LocationExportsStage
from app.pipeline.stages.object_extract import ObjectExtractStage
from app.pipeline.stages.pca_anomaly import PcaAnomalyStage
from app.pipeline.stages.report_640 import (
    Report640Stage,
    create_ee_notebook_report_mass_fetcher,
    create_ee_notebook_report_pottery_fetcher,
)
from app.pipeline.stages.s2_indices import S2IndicesStage
from app.pipeline.stages.sar_rtc import SarRtcStage
from app.pipeline.stages.secret_layers import (
    SecretLayersStage,
    create_ee_hidden_doors_fetcher,
    create_ee_notebook_secret_s2_layer_fetcher,
)
from app.pipeline.stages.thermal import ThermalStage
from app.pipeline.stages.thermal import create_ee_notebook_thermal_inertia_fetcher
from app.pipeline.stages.zero_shift import ZeroShiftStage
from app.schemas.artifact import ArtifactPublic
from app.schemas.run import (
    RunCreate,
    RunDeletePublic,
    RunDeletionAuditPublic,
    RunDeletionAuditRecordPublic,
    RunDetailPublic,
    RunHistoryEventPublic,
    RunPublic,
    RunStageProgressPublic,
)
from app.services.run_history import append_run_event, build_run_event, read_run_history_events
from app.services.run_state import ensure_single_active_run
from app.services.storage import delete_run_directory, initialize_run_storage, read_manifest, get_run_dir, summarize_run_directory

router = APIRouter()
logger = logging.getLogger(__name__)

SAFE_STAGE_PROGRESS: tuple[tuple[str, str], ...] = (
    ("grid", "GRID setup"),
    ("dem", "DEM"),
    ("zero_shift", "Zero shift"),
    ("sar_rtc", "SAR RTC"),
    ("s2_indices", "Sentinel-2 indices"),
    ("dem_derivatives", "DEM derivatives"),
    ("thermal", "Thermal"),
    ("secret_layers", "Secret layers"),
    ("report_640", "Report 640"),
    ("feature_stacks", "Feature stacks"),
    ("focus_mask", "Focus mask"),
    ("location_exports", "Location exports"),
    ("field_ops_exports", "Field ops exports"),
    ("gps_compare", "GPS comparison"),
    ("hypercube", "Hypercube"),
    ("pca_anomaly", "PCA anomaly"),
    ("object_extract", "Object extraction"),
    ("alignment_qa", "Alignment QA"),
)
SAFE_STAGE_STATUSES = {"pending", "running", "done", "failed", "skipped"}


class RunNotFoundError(AppError):
    status_code = 404
    public_code = "run_not_found"
    public_message = "Run is unavailable."


class InvalidRunIdError(AppError):
    status_code = 400
    public_code = "invalid_run_id"
    public_message = "Run identifier is invalid."


class ActiveRunDeleteError(AppError):
    status_code = 409
    public_code = "active_run_delete_blocked"
    public_message = "Cannot delete active run."


class RunDeleteError(AppError):
    status_code = 500
    public_code = "run_delete_failed"
    public_message = "Run could not be deleted."


class InvalidRunsQueryError(AppError):
    status_code = 400
    public_code = "invalid_runs_query"
    public_message = "Run query is invalid."


@router.post("/runs", response_model=RunPublic, status_code=201)
async def create_run(
    payload: RunCreate,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings_from_request),
    session: AsyncSession = Depends(get_db_session),
) -> RunPublic:
    await ensure_single_active_run(session)

    run = Run(
        name=payload.name,
        status=RunStatus.QUEUED,
        latitude=float(payload.lat),
        longitude=float(payload.lon),
    )
    session.add(run)
    await session.flush()

    run_dir = initialize_run_storage(settings, run.id)
    del run_dir
    grid_spec = build_run_grid(float(payload.lat), float(payload.lon))
    save_grid_manifest(settings, run.id, grid_spec.manifest)
    append_run_event(settings, run.id, "run_created", timestamp=run.created_at or None)
    append_run_event(settings, run.id, "run_queued", timestamp=run.created_at or None)
    await session.commit()
    await session.refresh(run)

    background_tasks.add_task(enqueue_core_pipeline_run, run.id, settings)
    return _to_run_public(run)


@router.get("/runs", response_model=list[RunPublic])
async def list_runs(
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    limit: int = Query(default=50),
    offset: int = Query(default=0),
    settings: Settings = Depends(get_settings_from_request),
    session: AsyncSession = Depends(get_db_session),
) -> list[RunPublic]:
    sort_column = _resolve_run_sort_column(sort)
    sort_order = _resolve_run_sort_order(order)
    status_filter = _resolve_run_status_filter(status)
    safe_limit = min(max(limit, 1), 200)
    safe_offset = max(offset, 0)

    stmt = select(Run)
    if q and q.strip():
        pattern = f"%{q.strip().casefold()}%"
        stmt = stmt.where(
            or_(
                func.lower(func.coalesce(Run.name, "")).like(pattern),
                func.lower(Run.id).like(pattern),
            )
        )
    if status_filter is not None:
        stmt = stmt.where(Run.status == status_filter)

    primary_order = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    secondary_order = Run.id.asc() if sort_order == "asc" else Run.id.desc()
    result = await session.scalars(stmt.order_by(primary_order, secondary_order).offset(safe_offset).limit(safe_limit))
    runs = list(result)
    await _refresh_disk_summaries(session=session, settings=settings, runs=runs)
    return [_to_run_public(run) for run in runs]


@router.get("/runs/deletion-audit", response_model=RunDeletionAuditPublic)
async def get_deletion_audit(
    session: AsyncSession = Depends(get_db_session),
) -> RunDeletionAuditPublic:
    records = list(
        await session.scalars(
            select(RunDeletionAudit).order_by(RunDeletionAudit.deleted_at.desc(), RunDeletionAudit.id.desc()).limit(25)
        )
    )
    total_freed_bytes = await session.scalar(select(func.coalesce(func.sum(RunDeletionAudit.freed_bytes), 0)))
    return RunDeletionAuditPublic(
        total_freed_bytes=int(total_freed_bytes or 0),
        records=[
            RunDeletionAuditRecordPublic(
                run_id=record.run_id,
                run_name=record.run_name,
                deleted_at=record.deleted_at,
                deleted_files_count=record.deleted_files_count,
                deleted_dirs_count=record.deleted_dirs_count,
                freed_bytes=record.freed_bytes,
                status=record.status,
                message=record.message,
            )
            for record in records
        ],
    )


@router.get("/runs/{run_id}", response_model=RunDetailPublic)
async def get_run(
    run_id: str,
    settings: Settings = Depends(get_settings_from_request),
    session: AsyncSession = Depends(get_db_session),
) -> RunDetailPublic:
    run = await session.scalar(select(Run).where(Run.id == run_id))
    if run is None:
        raise RunNotFoundError()
    await _refresh_disk_summaries(session=session, settings=settings, runs=[run])

    artifact_rows = await session.scalars(
        select(Artifact).where(Artifact.run_id == run_id).order_by(Artifact.created_at.asc(), Artifact.id.asc())
    )
    public_artifacts = [_to_artifact_public(artifact) for artifact in artifact_rows if _is_publicly_listable_artifact(artifact)]
    progress = _build_stage_progress(settings=settings, run_id=run_id, run_status=run.status)
    history = _build_run_history(settings=settings, run=run, stages=progress)
    return RunDetailPublic(
        id=run.id,
        name=run.name,
        status=run.status,
        created_at=run.created_at,
        disk_usage_bytes=run.disk_usage_bytes,
        output_file_count=run.output_file_count,
        last_disk_scan_at=run.last_disk_scan_at,
        current_stage=_current_stage(progress),
        stages=progress,
        history=history,
        artifacts=public_artifacts,
    )


@router.delete("/runs/{run_id}", response_model=RunDeletePublic)
async def delete_run(
    run_id: str,
    settings: Settings = Depends(get_settings_from_request),
    session: AsyncSession = Depends(get_db_session),
) -> RunDeletePublic:
    _validate_delete_run_id(run_id)
    run = await session.scalar(select(Run).where(Run.id == run_id))
    if run is None:
        raise RunNotFoundError()
    if _is_active_run_status(run.status):
        raise ActiveRunDeleteError()

    try:
        delete_summary = summarize_run_directory(settings, run_id)
        _set_run_disk_summary(run, delete_summary)
        delete_summary = delete_run_directory(settings, run_id)
    except Exception as exc:
        raise RunDeleteError() from exc

    session.add(
        RunDeletionAudit(
            run_id=run_id,
            run_name=run.name,
            deleted_at=datetime.now(timezone.utc),
            deleted_files_count=delete_summary.deleted_files_count,
            deleted_dirs_count=delete_summary.deleted_dirs_count,
            freed_bytes=delete_summary.freed_bytes,
            status="deleted",
            message="Run deleted.",
        )
    )
    await session.delete(run)
    await session.commit()
    return RunDeletePublic(
        run_id=run_id,
        deleted=True,
        deleted_files_count=delete_summary.deleted_files_count,
        deleted_dirs_count=delete_summary.deleted_dirs_count,
        freed_bytes=delete_summary.freed_bytes,
        status="deleted",
        message="Run deleted.",
    )


def enqueue_core_pipeline_run(run_id: str, settings: Settings) -> None:
    try:
        asyncio.run(run_core_pipeline_for_run(run_id=run_id, settings=settings))
    except Exception:
        logger.exception("Background pipeline execution failed for run.")


async def run_core_pipeline_for_run(
    *,
    run_id: str,
    settings: Settings,
    grid_spec_override: GridSpec | None = None,
) -> None:
    from app.db.session import create_engine, create_session_factory

    engine = create_engine(settings)
    session_factory = create_session_factory(settings, engine)
    try:
        try:
            async with session_factory() as session:
                run = await session.scalar(select(Run).where(Run.id == run_id))
                if run is None:
                    raise RunNotFoundError()
                latitude = float(run.latitude)
                longitude = float(run.longitude)

            grid_spec = grid_spec_override or build_run_grid(latitude, longitude)
            orchestrator = Orchestrator(
                settings=settings,
                session_factory=session_factory,
                stages=[
                    GridStage(latitude=latitude, longitude=longitude, grid_spec_override=grid_spec_override),
                    DemStage(grid_spec=grid_spec),
                    ZeroShiftStage(grid_spec=grid_spec),
                    SarRtcStage(grid_spec=grid_spec),
                    S2IndicesStage(grid_spec=grid_spec),
                    DemDerivativesStage(grid_spec=grid_spec),
                    ThermalStage(grid_spec=grid_spec),
                    SecretLayersStage(
                        grid_spec=grid_spec,
                        hidden_doors_fetcher=create_ee_hidden_doors_fetcher(settings, grid_spec),
                        secret_s2_layer_fetcher=create_ee_notebook_secret_s2_layer_fetcher(settings, grid_spec),
                        thermal_inertia_fetcher=create_ee_notebook_thermal_inertia_fetcher(settings, grid_spec),
                    ),
                    Report640Stage(
                        grid_spec=grid_spec,
                        pottery_fetcher=create_ee_notebook_report_pottery_fetcher(settings, grid_spec),
                        mass_fetcher=create_ee_notebook_report_mass_fetcher(settings, grid_spec),
                    ),
                    FeatureStacksStage(grid_spec=grid_spec),
                    FocusMaskStage(grid_spec=grid_spec),
                    LocationExportsStage(grid_spec=grid_spec),
                    FieldOpsExportsStage(grid_spec=grid_spec),
                    GpsComparisonStage(input_lat=latitude, input_lon=longitude, grid_spec=grid_spec),
                    HypercubeStage(grid_spec=grid_spec),
                    PcaAnomalyStage(grid_spec=grid_spec),
                    ObjectExtractStage(grid_spec=grid_spec),
                    AlignmentQaStage(grid_spec=grid_spec),
                ],
            )
            await orchestrator.run_run(run_id)
        except Exception:
            await _mark_run_failed_if_present(session_factory, run_id, settings=settings)
            raise
    finally:
        await engine.dispose()


async def _mark_run_failed_if_present(session_factory, run_id: str, *, settings: Settings) -> None:
    async with session_factory() as session:
        run = await session.scalar(select(Run).where(Run.id == run_id))
        if run is None or run.status in {RunStatus.DONE, RunStatus.FAILED, RunStatus.STALE_FAILED}:
            return
        run.status = RunStatus.FAILED
        await session.commit()
    append_run_event(settings, run_id, "run_failed")


def _to_run_public(run: Run) -> RunPublic:
    return RunPublic(
        id=run.id,
        name=run.name,
        status=run.status,
        created_at=run.created_at,
        disk_usage_bytes=run.disk_usage_bytes,
        output_file_count=run.output_file_count,
        last_disk_scan_at=run.last_disk_scan_at,
    )


async def _refresh_disk_summaries(*, session: AsyncSession, settings: Settings, runs: list[Run]) -> None:
    if not runs:
        return
    changed = False
    for run in runs:
        if (
            run.disk_usage_bytes is not None
            and run.output_file_count is not None
            and run.last_disk_scan_at is not None
        ):
            continue
        _set_run_disk_summary(run, summarize_run_directory(settings, run.id))
        changed = True
    if changed:
        await session.commit()


def _set_run_disk_summary(run: Run, summary) -> None:
    run.disk_usage_bytes = summary.freed_bytes
    run.output_file_count = summary.deleted_files_count
    run.last_disk_scan_at = datetime.now(timezone.utc)


def _validate_delete_run_id(run_id: str) -> None:
    try:
        parsed = UUID(run_id)
    except (TypeError, ValueError):
        raise InvalidRunIdError()
    if str(parsed) != run_id:
        raise InvalidRunIdError()


def _is_active_run_status(status: RunStatus) -> bool:
    return status in {RunStatus.QUEUED, RunStatus.RUNNING}


def _resolve_run_sort_column(sort: str):
    mapping = {
        "created_at": Run.created_at,
        "updated_at": Run.updated_at,
        "disk_usage_bytes": Run.disk_usage_bytes,
        "output_file_count": Run.output_file_count,
        "name": func.lower(func.coalesce(Run.name, "")),
        "status": Run.status,
    }
    column = mapping.get(sort.strip().casefold())
    if column is None:
        raise InvalidRunsQueryError()
    return column


def _resolve_run_sort_order(order: str) -> str:
    order_key = order.strip().casefold()
    if order_key not in {"asc", "desc"}:
        raise InvalidRunsQueryError()
    return order_key


def _resolve_run_status_filter(status: str | None) -> RunStatus | None:
    if status is None:
        return None
    status_key = status.strip().casefold()
    if not status_key:
        return None
    try:
        return RunStatus(status_key)
    except ValueError as exc:
        raise InvalidRunsQueryError() from exc


def _to_artifact_public(artifact: Artifact) -> ArtifactPublic:
    return ArtifactPublic(
        name=artifact.name,
        artifact_class=artifact.artifact_class,
        created_at=artifact.created_at,
    )


def _build_stage_progress(*, settings: Settings, run_id: str, run_status: RunStatus) -> list[RunStageProgressPublic]:
    manifest_statuses = _read_stage_manifest_statuses(settings=settings, run_id=run_id)
    stages: list[RunStageProgressPublic] = []
    for safe_name, public_label in SAFE_STAGE_PROGRESS:
        status = manifest_statuses.get(safe_name, "pending")
        if status not in SAFE_STAGE_STATUSES:
            status = "pending"
        stages.append(RunStageProgressPublic(name=safe_name, label=public_label, status=status))

    if run_status in {RunStatus.DONE, RunStatus.FAILED, RunStatus.STALE_FAILED} and not manifest_statuses:
        return []
    return stages


def _build_run_history(*, settings: Settings, run: Run, stages: list[RunStageProgressPublic]) -> list[RunHistoryEventPublic]:
    events = read_run_history_events(settings, run.id)
    if not events:
        events = _fallback_run_history(run=run, stages=stages)
    return [
        RunHistoryEventPublic(
            timestamp=event.timestamp,
            event_type=event.event_type,
            label=event.label,
            stage_name=event.stage_name,
            message=event.message,
        )
        for event in events
    ]


def _fallback_run_history(*, run: Run, stages: list[RunStageProgressPublic]):
    events = []
    created = run.created_at
    for event_type in ("run_created", "run_queued"):
        event = build_run_event(event_type=event_type, timestamp=created)
        if event is not None:
            events.append(event)

    if any(stage.status in {"running", "done", "failed"} for stage in stages):
        event = build_run_event(event_type="run_started", timestamp=created)
        if event is not None:
            events.append(event)

    for stage in stages:
        if stage.status == "running":
            event = build_run_event(event_type="stage_started", stage_name=stage.name, timestamp=created)
        elif stage.status == "done":
            event = build_run_event(event_type="stage_done", stage_name=stage.name, timestamp=created)
        elif stage.status == "failed":
            event = build_run_event(event_type="stage_failed", stage_name=stage.name, timestamp=created)
        else:
            event = None
        if event is not None:
            events.append(event)

    terminal_event_type = {
        RunStatus.DONE: "run_done",
        RunStatus.FAILED: "run_failed",
        RunStatus.STALE_FAILED: "run_stale_failed",
    }.get(run.status)
    if terminal_event_type:
        event = build_run_event(event_type=terminal_event_type, timestamp=created)
        if event is not None:
            events.append(event)
    return events


def _read_stage_manifest_statuses(*, settings: Settings, run_id: str) -> dict[str, str]:
    run_dir = get_run_dir(settings, run_id)
    statuses: dict[str, str] = {}
    for internal_name, _public_name in SAFE_STAGE_PROGRESS:
        manifest_path = run_dir / f"stage_{internal_name}.manifest.json"
        if not manifest_path.exists():
            continue
        try:
            payload = read_manifest(manifest_path)
        except (OSError, ValueError):
            continue
        status = payload.get("status")
        if isinstance(status, str):
            statuses[internal_name] = status
    return statuses


def _current_stage(stages: list[RunStageProgressPublic]) -> str | None:
    for status in ("running", "failed"):
        for stage in stages:
            if stage.status == status:
                return stage.name
    for stage in stages:
        if stage.status == "pending":
            return stage.name
    return None


def _is_publicly_listable_artifact(artifact: Artifact) -> bool:
    if artifact.artifact_class not in {ArtifactClass.REDACTED_PUBLIC, ArtifactClass.PREVIEW_ONLY}:
        return False
    if artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY:
        return False
    if artifact.name.startswith("experimental_"):
        return False
    if artifact.relative_path.startswith("experimental/"):
        return False
    return True
