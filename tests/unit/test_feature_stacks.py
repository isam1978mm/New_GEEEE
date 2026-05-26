from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile, raster_sidecar_path
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.feature_stacks import FeatureStacksStage, NOTEBOOK_STACK_OUTPUT_DIR, SCIENCE_CORE_BANDS
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.s2_indices import S2IndicesStage, deterministic_s2_cube_fetcher
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher
from app.pipeline.stages.thermal import ThermalStage, deterministic_lst_fetcher
from app.services.storage import read_manifest


def test_feature_stacks_stage_writes_filesystem_only_support_outputs() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        context = StageContext(run_id="run-1", settings=_settings(run_dir), run_dir=run_dir)

        asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
        asyncio.run(SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher).run(context))
        asyncio.run(S2IndicesStage(grid_spec=grid_spec, s2_cube_fetcher=deterministic_s2_cube_fetcher).run(context))
        asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))
        asyncio.run(ThermalStage(grid_spec=grid_spec, lst_fetcher=deterministic_lst_fetcher).run(context))

        result = asyncio.run(FeatureStacksStage(grid_spec=grid_spec).run(context))

        assert [artifact.name for artifact in result.artifacts] == [
            "science_core_stack_tif",
            "science_core_stack_npy",
            "radar_linear_support_stack_tif",
            "radar_linear_support_stack_npy",
            "radar_db_support_stack_tif",
            "radar_db_support_stack_npy",
            "ai_ready_support_stack_tif",
            "ai_ready_support_stack_npy",
            "s2_mask_support_valid",
            "band_stats",
            "stack_presence_summary",
            "tensor_audit_summary",
            "geometry_consistency_summary",
            "notebook_RADAR_STACK_HWC_640_npy",
        ]
        assert all(artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY for artifact in result.artifacts)
        assert all(artifact.http_servable is False for artifact in result.artifacts)

        stack_cube = np.load(run_dir / "stacks" / "tensor_support" / "science_core_stack.npy")
        assert stack_cube.shape == (grid_spec.size, grid_spec.size, len(SCIENCE_CORE_BANDS))
        stack_sidecar = read_manifest(raster_sidecar_path(run_dir / "stacks" / "tensor_support" / "science_core_stack.tif"))
        assert stack_sidecar["transform"] == grid_spec.manifest.crs_transform

        radar_linear_stack = np.load(run_dir / "stacks" / "tensor_support" / "radar_linear_support_stack.npy")
        assert radar_linear_stack.shape == (grid_spec.size, grid_spec.size, 4)
        assert float(radar_linear_stack[:, :, 0].min()) >= 0.0
        notebook_radar_stack_path = run_dir / NOTEBOOK_STACK_OUTPUT_DIR / "RADAR_STACK_HWC_640_app.npy"
        assert notebook_radar_stack_path.is_file()
        notebook_radar_stack = np.load(notebook_radar_stack_path)
        assert notebook_radar_stack.dtype == np.float32
        assert notebook_radar_stack.shape == (grid_spec.size, grid_spec.size, 4)
        np.testing.assert_array_equal(notebook_radar_stack, radar_linear_stack)
        radar_linear_sidecar = read_manifest(
            raster_sidecar_path(run_dir / "stacks" / "tensor_support" / "radar_linear_support_stack.tif")
        )
        assert radar_linear_sidecar["transform"] == grid_spec.manifest.crs_transform

        radar_db_stack = np.load(run_dir / "stacks" / "tensor_support" / "radar_db_support_stack.npy")
        assert radar_db_stack.shape == (grid_spec.size, grid_spec.size, 4)
        for band_index, band_name in enumerate(("VV_dB", "VH_dB", "logRatio_dB", "incidence")):
            source = np.load(run_dir / "npy_radar_bands" / f"{band_name}.npy")
            np.testing.assert_array_equal(radar_db_stack[:, :, band_index], source)
        radar_db_sidecar = read_manifest(raster_sidecar_path(run_dir / "stacks" / "tensor_support" / "radar_db_support_stack.tif"))
        assert radar_db_sidecar["transform"] == grid_spec.manifest.crs_transform

        ai_ready_stack = np.load(run_dir / "stacks" / "tensor_support" / "ai_ready_support_stack.npy")
        assert ai_ready_stack.shape == (grid_spec.size, grid_spec.size, len(SCIENCE_CORE_BANDS))
        assert float(ai_ready_stack.min()) >= 0.0
        assert float(ai_ready_stack.max()) <= 1.0
        ai_ready_sidecar = read_manifest(raster_sidecar_path(run_dir / "stacks" / "tensor_support" / "ai_ready_support_stack.tif"))
        assert ai_ready_sidecar["transform"] == grid_spec.manifest.crs_transform

        with (run_dir / "qa" / "stacks" / "band_stats.csv").open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(SCIENCE_CORE_BANDS)
        assert rows[0]["band_name"] == SCIENCE_CORE_BANDS[0]
        assert rows[-1]["band_name"] == SCIENCE_CORE_BANDS[-1]

        presence_summary = json.loads((run_dir / "qa" / "stacks" / "stack_presence_summary.json").read_text(encoding="utf-8"))
        assert presence_summary["all_expected_bands_present"] is True
        assert presence_summary["missing_expected_bands"] == []
        assert [entry["artifact_name"] for entry in presence_summary["variant_families"]] == [
            "radar_db_support_stack",
            "radar_linear_support_stack",
            "ai_ready_support_stack",
        ]
        family_statuses = {entry["family"]: entry for entry in presence_summary["notebook_family_statuses"]}
        assert family_statuses["SIGMA0_MASTER_640"]["status"] == "implemented"
        assert family_statuses["SIGMA0_MASTER_640"]["artifact_name"] == "radar_linear_support_stack"
        assert family_statuses["TESLA_V7_2_VARIANTS"]["status"] == "implemented_subset"
        assert family_statuses["TESLA_V7_2_VARIANTS"]["artifact_name"] == "ai_ready_support_stack"
        assert family_statuses["NANO_STACK"]["status"] == "deferred"
        assert family_statuses["GPHYS_MASTER_640"]["status"] == "deferred"
        assert family_statuses["RAD_MASTER_CUBE_640"]["status"] == "deferred"
        assert family_statuses["ULTIMATE_GPHYS_SCAN_640"]["status"] == "deferred"

        tensor_audit = json.loads((run_dir / "qa" / "stacks" / "tensor_audit_summary.json").read_text(encoding="utf-8"))
        assert tensor_audit["shape"] == [grid_spec.size, grid_spec.size, len(SCIENCE_CORE_BANDS)]

        geometry_summary = json.loads(
            (run_dir / "qa" / "stacks" / "geometry_consistency_summary.json").read_text(encoding="utf-8")
        )
        assert geometry_summary["all_sources_grid_aligned"] is True

        s2_mask_sidecar = read_manifest(raster_sidecar_path(run_dir / "stacks" / "optical_support" / "s2_mask_support_valid.tif"))
        assert s2_mask_sidecar["transform"] == grid_spec.manifest.crs_transform


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
