from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models import Artifact, Run
from app.main import create_app
from app.pipeline.orchestrator import Orchestrator
from app.pipeline.stages.alignment_qa import AlignmentQaStage
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.feature_stacks import FeatureStacksStage
from app.pipeline.stages.field_ops_exports import FieldOpsExportsStage
from app.pipeline.stages.focus_mask import FocusMaskStage
from app.pipeline.stages.gps_compare import GpsComparisonStage
from app.pipeline.stages.grid import GridStage, build_run_grid
from app.pipeline.stages.hypercube import HypercubeStage
from app.pipeline.stages.location_exports import LocationExportsStage
from app.pipeline.stages.object_extract import ObjectExtractStage
from app.pipeline.stages.pca_anomaly import PcaAnomalyStage
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher
from app.pipeline.stages.zero_shift import ZeroShiftStage
from app.services.storage import ensure_data_dirs


def test_full_job_outputs_are_not_publicly_listed_or_served_unless_redacted(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = Settings(
            data_dir=Path(temp_dir) / "data",
            database_path=Path(temp_dir) / "data" / "gee_screening.db",
        )
        asyncio.run(_create_database(settings))
        monkeypatch.setattr("app.api.health.initialize_ee_session", lambda _settings: None)
        monkeypatch.setattr("app.api.runs.enqueue_core_pipeline_run", _deterministic_background_runner(settings))

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            create_response = client.post("/runs", json={"lat": 35.59499, "lon": 36.12694, "name": "inventory"})
            run_id = create_response.json()["id"]
            detail_response = client.get(f"/runs/{run_id}")

            blocked_names = [
                "grid_guard_summary",
                "sar_npy_VV_dB",
                "sar_npy_VH_dB",
                "sar_npy_logRatio_dB",
                "sar_npy_incidence",
                "sar_summary",
                "science_core_stack_npy",
                "ai_ready_support_stack_npy",
                "focus_zone_17m_npy",
                "location_geojson",
                "location_kmz",
                "field_ops_navigation_kmz",
                "field_ops_report",
                "gps_point_comparison_json",
                "gps_point_comparison_csv",
                "object_mask",
                "parity_qa_summary",
                "thermal_summary",
            ]
            blocked_responses = {
                name: client.get(f"/runs/{run_id}/artifacts/{name}")
                for name in blocked_names
            }

        assert create_response.status_code == 201
        assert detail_response.status_code == 200

        body = detail_response.json()
        public_names = {artifact["name"] for artifact in body["artifacts"]}
        assert {"objects_index", "clusters_summary", "alignment_qa", "alignment_audit", "alignment_mask_selection"} <= public_names
        assert "grid_guard_summary" not in public_names
        assert "sar_npy_VV_dB" not in public_names
        assert "sar_npy_VH_dB" not in public_names
        assert "sar_npy_logRatio_dB" not in public_names
        assert "sar_npy_incidence" not in public_names
        assert "sar_summary" not in public_names
        assert "science_core_stack_npy" not in public_names
        assert "ai_ready_support_stack_npy" not in public_names
        assert "focus_zone_17m_npy" not in public_names
        assert "location_geojson" not in public_names
        assert "location_kmz" not in public_names
        assert "field_ops_navigation_kmz" not in public_names
        assert "field_ops_report" not in public_names
        assert "gps_point_comparison_json" not in public_names
        assert "gps_point_comparison_csv" not in public_names
        assert "object_mask" not in public_names
        assert "parity_qa_summary" not in public_names
        assert "thermal_summary" not in public_names
        assert "VV_dB" not in public_names
        assert "lst" not in public_names

        for response in blocked_responses.values():
            assert response.status_code == 404
            assert response.json() == {
                "error": "artifact_unavailable",
                "message": "Artifact is unavailable.",
            }

        asyncio.run(_assert_internal_artifacts_present(settings, run_id))


async def _assert_internal_artifacts_present(settings: Settings, run_id: str) -> None:
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        run = await session.scalar(select(Run).where(Run.id == run_id))
        assert run is not None
        artifacts = list((await session.scalars(select(Artifact).where(Artifact.run_id == run_id))).all())
    await engine.dispose()

    name_to_path = {artifact.name: artifact.relative_path for artifact in artifacts}
    assert name_to_path["grid_guard_summary"] == "QA/grid_dem/grid_guard_summary.json"
    assert name_to_path["sar_npy_VV_dB"] == "npy_radar_bands/VV_dB.npy"
    assert name_to_path["sar_npy_VH_dB"] == "npy_radar_bands/VH_dB.npy"
    assert name_to_path["sar_npy_logRatio_dB"] == "npy_radar_bands/logRatio_dB.npy"
    assert name_to_path["sar_npy_incidence"] == "npy_radar_bands/incidence.npy"
    assert name_to_path["sar_summary"] == "QA/sar/sar_summary.csv"
    assert name_to_path["science_core_stack_npy"] == "stacks/tensor_support/science_core_stack.npy"
    assert name_to_path["ai_ready_support_stack_npy"] == "stacks/tensor_support/ai_ready_support_stack.npy"
    assert name_to_path["focus_zone_17m_npy"] == "full_job/focus/focus_zone_17m.npy"
    assert name_to_path["location_geojson"] == "full_job/location/site_location.geojson"
    assert name_to_path["location_kmz"] == "kmz/site_location.kmz"
    assert name_to_path["field_ops_navigation_kmz"] == "kmz/field_ops_navigation.kmz"
    assert name_to_path["field_ops_report"] == "full_job/field_ops/field_ops_report.json"
    assert name_to_path["gps_point_comparison_json"] == "full_job/gps/gps_point_comparison.json"
    assert name_to_path["gps_point_comparison_csv"] == "full_job/gps/gps_point_comparison.csv"
    assert name_to_path["object_mask"] == "objects/object_mask.npy"
    assert name_to_path["parity_qa_summary"] == "QA/parity/parity_qa_summary.json"
    assert name_to_path["thermal_summary"] == "QA/stacks/thermal_summary.json"


async def _create_database(settings: Settings) -> None:
    ensure_data_dirs(settings)
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


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
    await engine.dispose()
