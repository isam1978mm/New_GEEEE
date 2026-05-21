from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.deps import get_db_session, get_settings_from_request
from app.errors import ActiveRunConflictError, AppError
from app.pipeline.manifest import save_grid_manifest
from app.pipeline.orchestrator import Orchestrator
from app.pipeline.stages.alignment_qa import AlignmentQaStage
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.dem import DemStage
from app.pipeline.stages.feature_stacks import FeatureStacksStage
from app.pipeline.stages.grid import GridStage, build_run_grid
from app.pipeline.stages.hypercube import HypercubeStage
from app.pipeline.stages.object_extract import ObjectExtractStage
from app.pipeline.stages.pca_anomaly import PcaAnomalyStage
from app.pipeline.stages.s2_indices import S2IndicesStage
from app.pipeline.stages.sar_rtc import SarRtcStage
from app.pipeline.stages.thermal import ThermalStage
from app.pipeline.stages.zero_shift import ZeroShiftStage
from app.schemas.artifact import ArtifactPublic
from app.schemas.run import RunCreate, RunDetailPublic, RunPublic
from app.services.run_state import ensure_single_active_run
from app.services.storage import initialize_run_storage

router = APIRouter()


class RunNotFoundError(AppError):
    status_code = 404
    public_code = "run_not_found"
    public_message = "Run is unavailable."


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
    await session.commit()
    await session.refresh(run)

    background_tasks.add_task(enqueue_core_pipeline_run, run.id, settings)
    return _to_run_public(run)


@router.get("/runs", response_model=list[RunPublic])
async def list_runs(
    session: AsyncSession = Depends(get_db_session),
) -> list[RunPublic]:
    result = await session.scalars(select(Run).order_by(Run.created_at.desc(), Run.id.desc()))
    return [_to_run_public(run) for run in result]


@router.get("/runs/{run_id}", response_model=RunDetailPublic)
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> RunDetailPublic:
    run = await session.scalar(select(Run).where(Run.id == run_id))
    if run is None:
        raise RunNotFoundError()

    artifact_rows = await session.scalars(
        select(Artifact).where(Artifact.run_id == run_id).order_by(Artifact.created_at.asc(), Artifact.id.asc())
    )
    public_artifacts = [_to_artifact_public(artifact) for artifact in artifact_rows if _is_publicly_listable_artifact(artifact)]
    return RunDetailPublic(
        id=run.id,
        name=run.name,
        status=run.status,
        created_at=run.created_at,
        artifacts=public_artifacts,
    )


def enqueue_core_pipeline_run(run_id: str, settings: Settings) -> None:
    asyncio.run(run_core_pipeline_for_run(run_id=run_id, settings=settings))


async def run_core_pipeline_for_run(*, run_id: str, settings: Settings) -> None:
    from app.db.session import create_engine, create_session_factory

    engine = create_engine(settings)
    session_factory = create_session_factory(settings, engine)
    try:
        async with session_factory() as session:
            run = await session.scalar(select(Run).where(Run.id == run_id))
            if run is None:
                raise RunNotFoundError()
            latitude = float(run.latitude)
            longitude = float(run.longitude)

        grid_spec = build_run_grid(latitude, longitude)
        orchestrator = Orchestrator(
            settings=settings,
            session_factory=session_factory,
            stages=[
                GridStage(latitude=latitude, longitude=longitude),
                DemStage(grid_spec=grid_spec),
                ZeroShiftStage(grid_spec=grid_spec),
                SarRtcStage(grid_spec=grid_spec),
                S2IndicesStage(grid_spec=grid_spec),
                DemDerivativesStage(grid_spec=grid_spec),
                ThermalStage(grid_spec=grid_spec),
                FeatureStacksStage(grid_spec=grid_spec),
                HypercubeStage(grid_spec=grid_spec),
                PcaAnomalyStage(grid_spec=grid_spec),
                ObjectExtractStage(grid_spec=grid_spec),
                AlignmentQaStage(grid_spec=grid_spec),
            ],
        )
        await orchestrator.run_run(run_id)
    finally:
        await engine.dispose()


def _to_run_public(run: Run) -> RunPublic:
    return RunPublic(
        id=run.id,
        name=run.name,
        status=run.status,
        created_at=run.created_at,
    )


def _to_artifact_public(artifact: Artifact) -> ArtifactPublic:
    return ArtifactPublic(
        name=artifact.name,
        artifact_class=artifact.artifact_class,
        created_at=artifact.created_at,
    )


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
