from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.main import create_app
from app.pipeline.orchestrator import Orchestrator
from app.pipeline.stages.alignment_qa import AlignmentQaStage
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.grid import GridStage, build_run_grid
from app.pipeline.stages.hypercube import HypercubeStage
from app.pipeline.stages.object_extract import ObjectExtractStage
from app.pipeline.stages.pca_anomaly import PcaAnomalyStage
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher
from app.pipeline.stages.zero_shift import ZeroShiftStage
from app.services.storage import ensure_data_dirs


def test_full_core_run_completes_and_app_serves_safe_outputs(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        asyncio.run(_run_full_core_pipeline(Path(temp_dir)))

        settings = Settings(
            data_dir=Path(temp_dir) / "data",
            database_path=Path(temp_dir) / "data" / "gee_screening.db",
        )
        monkeypatch.setattr("app.api.health.initialize_ee_session", lambda _settings: None)

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            root = client.get("/")
            health = client.get("/healthz")
            ready = client.get("/readyz")
            objects_index = client.get("/runs/run-1/artifacts/objects_index")

        assert root.status_code == 200
        assert "GEE Screening Workspace" in root.text
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}
        assert ready.status_code == 200
        assert ready.json() == {"status": "ready"}
        assert objects_index.status_code == 200
        assert "row_min" in objects_index.text
        assert "col_min" in objects_index.text
        assert "latitude" not in objects_index.text.casefold()
        assert "longitude" not in objects_index.text.casefold()


async def _run_full_core_pipeline(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    db_path = data_dir / "gee_screening.db"
    settings = Settings(data_dir=data_dir, database_path=db_path)
    ensure_data_dirs(settings)

    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Run(
                id="run-1",
                name="integration",
                status=RunStatus.QUEUED,
                latitude=35.59499,
                longitude=36.12694,
            )
        )
        await session.commit()

    grid_spec = build_run_grid(35.59499, 36.12694)
    orchestrator = Orchestrator(
        settings=settings,
        session_factory=session_factory,
        stages=[
            GridStage(latitude=35.59499, longitude=36.12694),
            DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile),
            ZeroShiftStage(grid_spec=grid_spec),
            SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher),
            S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher),
            DemDerivativesStage(grid_spec=grid_spec),
            ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher),
            HypercubeStage(grid_spec=grid_spec),
            PcaAnomalyStage(grid_spec=grid_spec),
            ObjectExtractStage(grid_spec=grid_spec),
            AlignmentQaStage(grid_spec=grid_spec),
        ],
    )
    records = await orchestrator.run_run("run-1")

    assert len(records) == 11

    async with session_factory() as session:
        run = await session.scalar(select(Run).where(Run.id == "run-1"))
        artifact_count = await session.scalar(select(func.count(Artifact.id)).where(Artifact.run_id == "run-1"))
        objects_artifact = await session.scalar(select(Artifact).where(Artifact.run_id == "run-1", Artifact.name == "objects_index"))
        alignment_artifact = await session.scalar(select(Artifact).where(Artifact.run_id == "run-1", Artifact.name == "alignment_qa"))

    assert run is not None
    assert run.status == RunStatus.DONE
    assert artifact_count is not None and artifact_count > 20
    assert objects_artifact is not None and objects_artifact.artifact_class == ArtifactClass.REDACTED_PUBLIC
    assert alignment_artifact is not None and alignment_artifact.artifact_class == ArtifactClass.REDACTED_PUBLIC

    await engine.dispose()
