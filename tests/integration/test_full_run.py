from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.main import create_app
from app.pipeline.orchestrator import Orchestrator
from app.pipeline.stages.alignment_qa import AlignmentQaStage
from app.pipeline.stages.classifier import ClassifierStage
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.feature_stacks import FeatureStacksStage
from app.pipeline.stages.field_ops_exports import FieldOpsExportsStage
from app.pipeline.stages.focus_mask import FocusMaskStage
from app.pipeline.stages.gps_compare import GpsComparisonStage
from app.pipeline.stages.grid import GridStage, build_run_grid
from app.pipeline.stages.hypercube import HypercubeStage
from app.pipeline.stages.location_exports import LocationExportsStage
from app.pipeline.stages.object_extract import ObjectExtractStage
from app.pipeline.stages.pca_anomaly import PcaAnomalyStage
from app.pipeline.stages.report_640 import Report640Stage
from app.pipeline.stages.run_quality import RunQualityStage
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.secret_layers import SecretLayersStage
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher
from app.pipeline.stages.zero_shift import ZeroShiftStage
from app.services.storage import ensure_data_dirs


def test_full_core_run_completes_and_app_serves_safe_outputs(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = Settings(
            data_dir=Path(temp_dir) / "data",
            database_path=Path(temp_dir) / "data" / "gee_screening.db",
        )
        asyncio.run(_create_database(settings))
        monkeypatch.setattr("app.api.health.initialize_ee_session", lambda _settings: None)
        monkeypatch.setattr("app.api.runs.enqueue_core_pipeline_run", _deterministic_background_runner(settings))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            post_run = client.post("/runs", json={"lat": 35.59499, "lon": 36.12694, "name": "integration"})
            run_id = post_run.json()["id"]
            runs = client.get("/runs")
            run_detail = client.get(f"/runs/{run_id}")
            root = client.get("/")
            health = client.get("/healthz")
            ready = client.get("/readyz")
            objects_index = client.get(f"/runs/{run_id}/artifacts/objects_index")

        assert post_run.status_code == 201
        assert "lat" not in post_run.text.casefold()
        assert runs.status_code == 200
        assert len(runs.json()) == 1
        assert run_detail.status_code == 200
        assert run_detail.json()["status"] == "done"
        assert {artifact["name"] for artifact in run_detail.json()["artifacts"]} >= {
            "objects_index",
            "alignment_qa",
            "classifier_classifications",
            "classifier_summary",
            "classifier_neutral_labels",
            "experimental_classifications",
            "experimental_summary",
            "experimental_neutral_labels",
            "run_quality_summary",
        }
        assert root.status_code == 200
        assert "GEE Screening Dashboard Design" in root.text
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}
        assert ready.status_code == 200
        assert ready.json() == {"status": "ready"}
        assert objects_index.status_code == 200
        assert "row_min" in objects_index.text
        assert "col_min" in objects_index.text
        assert "latitude" not in objects_index.text.casefold()
        assert "longitude" not in objects_index.text.casefold()


async def _create_database(settings: Settings) -> None:
    ensure_data_dirs(settings)
    _upgrade_database(settings)


def _upgrade_database(settings: Settings) -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("+aiosqlite", ""))
    command.upgrade(cfg, "head")


def _deterministic_background_runner(settings: Settings):
    def run(run_id: str, _settings: Settings) -> None:
        assert _settings.data_dir == settings.data_dir
        asyncio.run(_run_full_core_pipeline(settings, run_id=run_id))

    return run


async def _run_full_core_pipeline(settings: Settings, *, run_id: str) -> None:
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        run = await session.scalar(select(Run).where(Run.id == run_id))
        assert run is not None
        latitude = float(run.latitude)
        longitude = float(run.longitude)

    grid_spec = build_run_grid(latitude, longitude)
    orchestrator = Orchestrator(
        settings=settings,
        session_factory=session_factory,
        stages=[
            GridStage(latitude=latitude, longitude=longitude),
            DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile),
            ZeroShiftStage(grid_spec=grid_spec),
            SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher),
            S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher),
            DemDerivativesStage(grid_spec=grid_spec),
            ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher),
            SecretLayersStage(grid_spec=grid_spec),
            Report640Stage(grid_spec=grid_spec),
            FeatureStacksStage(grid_spec=grid_spec),
            FocusMaskStage(grid_spec=grid_spec),
            LocationExportsStage(grid_spec=grid_spec),
            FieldOpsExportsStage(grid_spec=grid_spec),
            GpsComparisonStage(input_lat=latitude, input_lon=longitude, grid_spec=grid_spec),
            HypercubeStage(grid_spec=grid_spec),
            PcaAnomalyStage(grid_spec=grid_spec),
            ObjectExtractStage(grid_spec=grid_spec),
            ClassifierStage(),
            AlignmentQaStage(grid_spec=grid_spec),
            RunQualityStage(),
        ],
    )
    records = await orchestrator.run_run(run_id)

    assert len(records) == 20

    async with session_factory() as session:
        run = await session.scalar(select(Run).where(Run.id == run_id))
        artifact_count = await session.scalar(select(func.count(Artifact.id)).where(Artifact.run_id == run_id))
        objects_artifact = await session.scalar(select(Artifact).where(Artifact.run_id == run_id, Artifact.name == "objects_index"))
        alignment_artifact = await session.scalar(select(Artifact).where(Artifact.run_id == run_id, Artifact.name == "alignment_qa"))
        classifier_artifact = await session.scalar(
            select(Artifact).where(Artifact.run_id == run_id, Artifact.name == "classifier_summary")
        )
        run_quality_artifact = await session.scalar(
            select(Artifact).where(Artifact.run_id == run_id, Artifact.name == "run_quality_summary")
        )

    assert run is not None
    assert run.status == RunStatus.DONE
    assert artifact_count is not None and artifact_count > 20
    assert objects_artifact is not None and objects_artifact.artifact_class == ArtifactClass.REDACTED_PUBLIC
    assert alignment_artifact is not None and alignment_artifact.artifact_class == ArtifactClass.REDACTED_PUBLIC
    assert classifier_artifact is not None and classifier_artifact.artifact_class == ArtifactClass.REDACTED_PUBLIC
    assert run_quality_artifact is not None and run_quality_artifact.artifact_class == ArtifactClass.REDACTED_PUBLIC

    await engine.dispose()
