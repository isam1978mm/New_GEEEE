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
from app.pipeline.stages.feature_stacks import (
    FeatureStacksStage,
    NOTEBOOK_AI_READY_STACK_NPY,
    NOTEBOOK_RADAR_LINEAR_STACK_NPY,
    NOTEBOOK_NANO_GEOPHYSICS_STACK_NPY,
    NOTEBOOK_RAD_S0_MASTER_STACK_NPY,
    NOTEBOOK_RADAR_STACK_NPY,
    NOTEBOOK_SCIENCE_CORE_STACK_NPY,
    NOTEBOOK_STACK_ALIAS_MANIFEST_JSON,
    NOTEBOOK_STACK_OUTPUT_DIR,
    NOTEBOOK_TREASURE_GEOPHYSICS_STACK_NPY,
    NANO_GEOPHYSICS_BANDS,
    RAD_S0_MASTER_BANDS,
    SCIENCE_CORE_BANDS,
    TREASURE_GEOPHYSICS_BANDS,
)
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
            "notebook_SCIENCE_CORE_STACK_HWC_640_npy",
            "notebook_RADAR_LINEAR_SUPPORT_STACK_640_npy",
            "notebook_AI_READY_SUPPORT_STACK_640_npy",
            "notebook_RAD_S0_MASTER_STACK_640_npy",
            "notebook_NANO_GEOPHYSICS_STACK_640_npy",
            "notebook_TREASURE_GEOPHYSICS_STACK_640_npy",
            "notebook_stack_alias_manifest",
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
        notebook_radar_stack_path = run_dir / NOTEBOOK_STACK_OUTPUT_DIR / NOTEBOOK_RADAR_STACK_NPY
        assert notebook_radar_stack_path.is_file()
        assert not (run_dir / NOTEBOOK_STACK_OUTPUT_DIR / "FINAL_TESLA_V7_2_HYPERCUBE.tif").exists()
        assert not (run_dir / NOTEBOOK_STACK_OUTPUT_DIR / "FINAL_TESLA_V7_2_HYPERCUBE.npy").exists()
        notebook_radar_stack = np.load(notebook_radar_stack_path)
        assert notebook_radar_stack.dtype == np.float32
        assert notebook_radar_stack.shape == (grid_spec.size, grid_spec.size, 4)
        radar_linear_sidecar = read_manifest(
            raster_sidecar_path(run_dir / "stacks" / "tensor_support" / "radar_linear_support_stack.tif")
        )
        assert radar_linear_sidecar["transform"] == grid_spec.manifest.crs_transform

        radar_db_stack = np.load(run_dir / "stacks" / "tensor_support" / "radar_db_support_stack.npy")
        assert radar_db_stack.shape == (grid_spec.size, grid_spec.size, 4)
        np.testing.assert_array_equal(notebook_radar_stack, radar_db_stack)
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

        notebook_dir = run_dir / NOTEBOOK_STACK_OUTPUT_DIR
        np.testing.assert_array_equal(np.load(notebook_dir / NOTEBOOK_SCIENCE_CORE_STACK_NPY), stack_cube)
        np.testing.assert_array_equal(np.load(notebook_dir / NOTEBOOK_RADAR_LINEAR_STACK_NPY), radar_linear_stack)
        np.testing.assert_array_equal(np.load(notebook_dir / NOTEBOOK_AI_READY_STACK_NPY), ai_ready_stack)

        vv_db = np.load(run_dir / "npy_radar_bands" / "VV_dB.npy")
        vh_db = np.load(run_dir / "npy_radar_bands" / "VH_dB.npy")
        incidence = np.load(run_dir / "npy_radar_bands" / "incidence.npy")
        valid = (vv_db != grid_spec.nodata) & (vh_db != grid_spec.nodata)
        vv_lin = np.power(10.0, vv_db[valid] / 10.0).astype(np.float32)
        vh_lin = np.power(10.0, vh_db[valid] / 10.0).astype(np.float32)

        rad_s0_stack = np.load(notebook_dir / NOTEBOOK_RAD_S0_MASTER_STACK_NPY)
        assert rad_s0_stack.shape == (grid_spec.size, grid_spec.size, len(RAD_S0_MASTER_BANDS))
        s0_valid = valid & (incidence != grid_spec.nodata)

        vv_windows = np.lib.stride_tricks.sliding_window_view(np.pad(vv_db, 1, mode="edge"), (3, 3))
        vh_windows = np.lib.stride_tricks.sliding_window_view(np.pad(vh_db, 1, mode="edge"), (3, 3))
        vv_med = np.median(vv_windows, axis=(-2, -1)).astype(np.float32)
        vh_med = np.median(vh_windows, axis=(-2, -1)).astype(np.float32)

        np.testing.assert_allclose(rad_s0_stack[:, :, 0][valid], vv_db[valid], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(rad_s0_stack[:, :, 1][valid], vh_db[valid], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(rad_s0_stack[:, :, 2][valid], vv_med[valid], rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(rad_s0_stack[:, :, 3][valid], vh_med[valid], rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(
            rad_s0_stack[:, :, 4][valid],
            np.power(10.0, (vh_db[valid] - vv_db[valid]) / 10.0).astype(np.float32),
            rtol=1e-5,
            atol=1e-5,
        )
        np.testing.assert_allclose(rad_s0_stack[:, :, 5][s0_valid], incidence[s0_valid], rtol=1e-6, atol=1e-6)

        nano_stack = np.load(notebook_dir / NOTEBOOK_NANO_GEOPHYSICS_STACK_NPY)
        assert nano_stack.shape == (grid_spec.size, grid_spec.size, len(NANO_GEOPHYSICS_BANDS))
        np.testing.assert_allclose(nano_stack[:, :, 0][valid], vv_lin / (vh_lin + np.float32(1e-6)), rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(nano_stack[:, :, 1][valid], vv_db[valid] - vh_db[valid], rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(nano_stack[:, :, 2][valid], np.sqrt(vv_lin * vh_lin), rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(
            nano_stack[:, :, 3][valid],
            (vh_lin * np.float32(4.0)) / (vv_lin + vh_lin + np.float32(1e-6)),
            rtol=1e-5,
            atol=1e-5,
        )

        treasure_stack = np.load(notebook_dir / NOTEBOOK_TREASURE_GEOPHYSICS_STACK_NPY)
        assert treasure_stack.shape == (grid_spec.size, grid_spec.size, len(TREASURE_GEOPHYSICS_BANDS))
        np.testing.assert_allclose(
            treasure_stack[:, :, 0][valid],
            (vh_lin * vv_lin) / (vv_lin + vh_lin + np.float32(1e-6)),
            rtol=1e-5,
            atol=1e-5,
        )
        np.testing.assert_allclose(treasure_stack[:, :, 1][valid], np.log(vv_lin) - np.log(vh_lin), rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(
            treasure_stack[:, :, 2][valid],
            vh_lin / ((vv_lin ** np.float32(2.0)) + np.float32(1e-6)),
            rtol=1e-5,
            atol=1e-5,
        )

        for band_name in (*RAD_S0_MASTER_BANDS, *NANO_GEOPHYSICS_BANDS, *TREASURE_GEOPHYSICS_BANDS):
            assert (run_dir / "NPY_RADAR_BANDS" / f"{band_name}_640.npy").is_file()
            tif_path = run_dir / "GEOTIFF_RADAR_BANDS" / f"{band_name}_640.tif"
            assert tif_path.is_file()
            assert read_manifest(raster_sidecar_path(tif_path))["transform"] == grid_spec.manifest.crs_transform

        alias_manifest = json.loads((notebook_dir / NOTEBOOK_STACK_ALIAS_MANIFEST_JSON).read_text(encoding="utf-8"))
        assert alias_manifest["schema"] == "notebook_stack_alias_manifest_v1"
        assert alias_manifest["status"] == "partial_alias_contract"
        assert alias_manifest["privacy"] == {"artifact_class": "FILESYSTEM_ONLY", "http_servable": False}
        alias_by_file = {entry["filename"]: entry for entry in alias_manifest["aliases"]}
        assert alias_by_file[NOTEBOOK_RADAR_STACK_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_RADAR_LINEAR_STACK_NPY]["status"] == "implemented_subset"
        assert alias_by_file[NOTEBOOK_AI_READY_STACK_NPY]["status"] == "implemented_subset"
        assert alias_by_file[NOTEBOOK_RAD_S0_MASTER_STACK_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_RAD_S0_MASTER_STACK_NPY]["source_cell"] == "cell_050"
        assert alias_by_file[NOTEBOOK_NANO_GEOPHYSICS_STACK_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_NANO_GEOPHYSICS_STACK_NPY]["source_cell"] == "cell_037"
        assert alias_by_file[NOTEBOOK_TREASURE_GEOPHYSICS_STACK_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_TREASURE_GEOPHYSICS_STACK_NPY]["source_cell"] == "cell_039"
        assert set(alias_manifest["deferred_families"]) == {
            "GPHYS_MASTER_640",
            "RAD_MASTER_CUBE_640",
            "ULTIMATE_GPHYS_SCAN_640",
        }

        with (run_dir / "QA" / "stacks" / "band_stats.csv").open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(SCIENCE_CORE_BANDS)
        assert rows[0]["band_name"] == SCIENCE_CORE_BANDS[0]
        assert rows[-1]["band_name"] == SCIENCE_CORE_BANDS[-1]

        presence_summary = json.loads((run_dir / "QA" / "stacks" / "stack_presence_summary.json").read_text(encoding="utf-8"))
        assert presence_summary["all_expected_bands_present"] is True
        assert presence_summary["missing_expected_bands"] == []
        assert [entry["artifact_name"] for entry in presence_summary["variant_families"]] == [
            "radar_db_support_stack",
            "radar_linear_support_stack",
            "rad_s0_master_stack",
            "nano_geophysics_stack",
            "treasure_geophysics_stack",
            "ai_ready_support_stack",
        ]
        family_statuses = {entry["family"]: entry for entry in presence_summary["notebook_family_statuses"]}
        assert family_statuses["SIGMA0_MASTER_640"]["status"] == "implemented"
        assert family_statuses["SIGMA0_MASTER_640"]["artifact_name"] == "radar_linear_support_stack"
        assert family_statuses["TESLA_V7_2_VARIANTS"]["status"] == "implemented_subset"
        assert family_statuses["TESLA_V7_2_VARIANTS"]["artifact_name"] == "ai_ready_support_stack"
        assert family_statuses["RAD_S0_MASTER_STACK_640"]["status"] == "implemented"
        assert family_statuses["RAD_S0_MASTER_STACK_640"]["artifact_name"] == "rad_s0_master_stack"
        assert family_statuses["NANO_STACK"]["status"] == "implemented"
        assert family_statuses["NANO_STACK"]["artifact_name"] == "nano_geophysics_stack"
        assert family_statuses["TREASURE_GEOPHYSICS_STACK_640"]["status"] == "implemented"
        assert family_statuses["TREASURE_GEOPHYSICS_STACK_640"]["artifact_name"] == "treasure_geophysics_stack"
        assert family_statuses["GPHYS_MASTER_640"]["status"] == "deferred"
        assert family_statuses["RAD_MASTER_CUBE_640"]["status"] == "deferred"
        assert family_statuses["ULTIMATE_GPHYS_SCAN_640"]["status"] == "deferred"

        tensor_audit = json.loads((run_dir / "QA" / "stacks" / "tensor_audit_summary.json").read_text(encoding="utf-8"))
        assert tensor_audit["shape"] == [grid_spec.size, grid_spec.size, len(SCIENCE_CORE_BANDS)]

        geometry_summary = json.loads(
            (run_dir / "QA" / "stacks" / "geometry_consistency_summary.json").read_text(encoding="utf-8")
        )
        assert geometry_summary["all_sources_grid_aligned"] is True

        s2_mask_sidecar = read_manifest(raster_sidecar_path(run_dir / "stacks" / "optical_support" / "s2_mask_support_valid.tif"))
        assert s2_mask_sidecar["transform"] == grid_spec.manifest.crs_transform


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
