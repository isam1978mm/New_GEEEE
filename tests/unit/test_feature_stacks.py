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
    NOTEBOOK_RAD_MASTER_CUBE_NPY,
    NOTEBOOK_GPHYS_MASTER_STACK_NPY,
    NOTEBOOK_MASTER_RTC_REFINED_STACK_NPY,
    NOTEBOOK_ARCH_TARGETS_STACK_NPY,
    NOTEBOOK_ULTIMATE_GPHYS_SCAN_NPY,
    NOTEBOOK_AUX_BONUS_FEATURES_STACK_NPY,
    NOTEBOOK_SIM_GEOPHYSICAL_STACK_NPY,
    NOTEBOOK_RADAR_STACK_NPY,
    NOTEBOOK_SCIENCE_CORE_STACK_NPY,
    NOTEBOOK_STACK_ALIAS_MANIFEST_JSON,
    NOTEBOOK_STACK_OUTPUT_DIR,
    NOTEBOOK_TREASURE_GEOPHYSICS_STACK_NPY,
    NANO_GEOPHYSICS_BANDS,
    RAD_S0_MASTER_BANDS,
    RAD_MASTER_CUBE_BANDS,
    GPHYS_MASTER_BANDS,
    MASTER_RTC_REFINED_BANDS,
    ARCH_TARGETS_BANDS,
    ULTIMATE_GPHYS_SCAN_BANDS,
    AUX_BONUS_FEATURES_BANDS,
    SIM_GEOPHYSICAL_BANDS,
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
            "notebook_RAD_MASTER_CUBE_640_npy",
            "notebook_GPHYS_MASTER_STACK_640_npy",
            "notebook_MASTER_RTC_REFINED_STACK_640_npy",
            "notebook_ARCH_TARGETS_STACK_640_npy",
            "notebook_ULTIMATE_GPHYS_SCAN_640_npy",
            "notebook_AUX_BONUS_FEATURES_STACK_640_npy",
            "notebook_SIM_GEOPHYSICAL_STACK_640_npy",
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
        log_ratio_db = np.load(run_dir / "npy_radar_bands" / "logRatio_dB.npy")
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

        rad_master_cube = np.load(notebook_dir / NOTEBOOK_RAD_MASTER_CUBE_NPY)
        assert rad_master_cube.shape == (grid_spec.size, grid_spec.size, len(RAD_MASTER_CUBE_BANDS))

        vv_lin_grid = np.power(10.0, vv_db / 10.0).astype(np.float32)
        vh_lin_grid = np.power(10.0, vh_db / 10.0).astype(np.float32)
        vv_lin_windows = np.lib.stride_tricks.sliding_window_view(np.pad(vv_lin_grid, 1, mode="edge"), (3, 3))
        vv_lin_med = np.median(vv_lin_windows, axis=(-2, -1)).astype(np.float32)
        vv_lin_mean = np.mean(vv_lin_windows, axis=(-2, -1)).astype(np.float32)
        vv_med_db_expected = (np.log10(np.maximum(vv_lin_med, np.float32(1e-10))) * np.float32(10.0)).astype(np.float32)
        vv_mean_db_expected = (np.log10(np.maximum(vv_lin_mean, np.float32(1e-10))) * np.float32(10.0)).astype(np.float32)

        np.testing.assert_allclose(rad_master_cube[:, :, 0][valid], vv_db[valid], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(rad_master_cube[:, :, 1][valid], vh_db[valid], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(rad_master_cube[:, :, 2][valid], vv_med_db_expected[valid], rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(rad_master_cube[:, :, 3][valid], vv_mean_db_expected[valid], rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(
            rad_master_cube[:, :, 4][valid],
            vh_lin_grid[valid] / (vv_lin_grid[valid] + np.float32(1e-10)),
            rtol=1e-5,
            atol=1e-5,
        )

        gphys_master = np.load(notebook_dir / NOTEBOOK_GPHYS_MASTER_STACK_NPY)
        assert gphys_master.shape == (grid_spec.size, grid_spec.size, len(GPHYS_MASTER_BANDS))

        vh_lin_windows = np.lib.stride_tricks.sliding_window_view(np.pad(vh_lin_grid, 1, mode="edge"), (3, 3))
        vh_lin_med = np.median(vh_lin_windows, axis=(-2, -1)).astype(np.float32)

        vv_std = np.std(vv_lin_windows, axis=(-2, -1)).astype(np.float32)
        vh_std = np.std(vh_lin_windows, axis=(-2, -1)).astype(np.float32)

        def mean3_valid(array):
            padded = np.pad(array, 1, mode="edge")
            windows = np.lib.stride_tricks.sliding_window_view(padded, (3, 3))
            finite = np.isfinite(windows)
            counts = finite.sum(axis=(-2, -1))
            sums = np.where(finite, windows, 0.0).sum(axis=(-2, -1))
            return (sums / np.maximum(counts, 1)).astype(np.float32)

        vv_sigma_mean_lin = mean3_valid(np.where(vv_std > 0.0, vv_lin_grid, np.nan).astype(np.float32))
        vh_sigma_mean_lin = mean3_valid(np.where(vh_std > 0.0, vh_lin_grid, np.nan).astype(np.float32))
        vh_med_db_expected = (np.log10(np.maximum(vh_lin_med, np.float32(1e-10))) * np.float32(10.0)).astype(np.float32)
        vv_sigma_mean_db_expected = (np.log10(np.maximum(vv_sigma_mean_lin, np.float32(1e-10))) * np.float32(10.0)).astype(np.float32)
        vh_sigma_mean_db_expected = (np.log10(np.maximum(vh_sigma_mean_lin, np.float32(1e-10))) * np.float32(10.0)).astype(np.float32)

        np.testing.assert_allclose(gphys_master[:, :, 0][valid], vv_db[valid], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(gphys_master[:, :, 1][valid], vh_db[valid], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(gphys_master[:, :, 2][valid], vv_med_db_expected[valid], rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(gphys_master[:, :, 3][valid], vh_med_db_expected[valid], rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(gphys_master[:, :, 4][valid], vv_sigma_mean_db_expected[valid], rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(gphys_master[:, :, 5][valid], vh_sigma_mean_db_expected[valid], rtol=1e-5, atol=1e-5)

        master_rtc = np.load(notebook_dir / NOTEBOOK_MASTER_RTC_REFINED_STACK_NPY)
        assert master_rtc.shape == (grid_spec.size, grid_spec.size, len(MASTER_RTC_REFINED_BANDS))

        np.testing.assert_allclose(master_rtc[:, :, 0][valid], vv_db[valid], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(master_rtc[:, :, 1][valid], vh_db[valid], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(master_rtc[:, :, 2][s0_valid], incidence[s0_valid], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(master_rtc[:, :, 3][valid], vv_db[valid], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(master_rtc[:, :, 4][valid], vh_db[valid], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(
            master_rtc[:, :, 5][valid],
            vh_lin_grid[valid] / (vv_lin_grid[valid] + np.float32(1e-6)),
            rtol=1e-5,
            atol=1e-5,
        )

        arch_targets = np.load(notebook_dir / NOTEBOOK_ARCH_TARGETS_STACK_NPY)
        assert arch_targets.shape == (grid_spec.size, grid_spec.size, len(ARCH_TARGETS_BANDS))

        vv_ref_for_arch = vv_med
        expected_high = (valid & (vv_db > -3.5) & (vh_db < -18.0)).astype(np.float32)
        expected_bright = (valid & (vv_db > -3.5) & (vh_db > -18.0)).astype(np.float32)
        expected_compact = (valid & (np.abs(vv_db - vv_ref_for_arch) > 4.5)).astype(np.float32)
        expected_double = (valid & (vv_db > 0.0)).astype(np.float32)
        expected_mid = (valid & (vv_db > -17.0) & (vv_db < -13.0)).astype(np.float32)

        expected_class = np.zeros(vv_db.shape, dtype=np.float32)
        expected_class[expected_mid.astype(bool)] = 1.0
        expected_class[expected_compact.astype(bool)] = 2.0
        expected_class[expected_high.astype(bool)] = 3.0
        expected_class[expected_bright.astype(bool)] = 4.0
        expected_class[expected_double.astype(bool)] = 5.0
        expected_class[~valid] = grid_spec.nodata

        np.testing.assert_allclose(arch_targets[:, :, 0], expected_class, rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(arch_targets[:, :, 1], expected_high, rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(arch_targets[:, :, 2], expected_bright, rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(arch_targets[:, :, 3], expected_compact, rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(arch_targets[:, :, 4], expected_double, rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(arch_targets[:, :, 5], expected_mid, rtol=1e-6, atol=1e-6)

        ultimate_gphys = np.load(notebook_dir / NOTEBOOK_ULTIMATE_GPHYS_SCAN_NPY)
        assert ultimate_gphys.shape == (grid_spec.size, grid_spec.size, len(ULTIMATE_GPHYS_SCAN_BANDS))

        ugs_vv = np.where(valid, vv_db * np.float32(1.45), grid_spec.nodata).astype(np.float32)
        ugs_vh = np.where(valid, vh_db * np.float32(1.45), grid_spec.nodata).astype(np.float32)

        def std_circle2(array):
            filled = np.where(array != grid_spec.nodata, array, np.nan).astype(np.float32)
            padded = np.pad(filled, 2, mode="edge")
            windows = np.lib.stride_tricks.sliding_window_view(padded, (5, 5))
            yy, xx = np.ogrid[-2:3, -2:3]
            circle = (xx * xx + yy * yy) <= 4
            samples = windows[:, :, circle]
            return np.nanstd(samples, axis=-1).astype(np.float32)

        ugs_std_vv = std_circle2(ugs_vv)
        expected_rvi = np.full(vv_db.shape, grid_spec.nodata, dtype=np.float32)
        expected_rvi[valid] = (ugs_vh[valid] * np.float32(4.0)) / (ugs_vv[valid] + ugs_vh[valid] + np.float32(1e-6))

        expected_box_vertical = (valid & (ugs_vv > 0.0)).astype(np.float32)
        expected_box_horizontal = (valid & (ugs_vv > -4.0) & (ugs_std_vv < 2.0)).astype(np.float32)
        expected_under_cover = (valid & (ugs_vh < -22.0) & (ugs_vv > -5.0)).astype(np.float32)
        expected_exposed_metal = (valid & (ugs_vh > -15.0) & (ugs_vv > -3.0)).astype(np.float32)
        expected_depot_proxy = (expected_box_horizontal.astype(bool) & expected_under_cover.astype(bool)).astype(np.float32)
        expected_box_mine = (valid & (ugs_std_vv > 5.0) & (ugs_vv > -5.0)).astype(np.float32)
        expected_jar_dense = (valid & (ugs_vv > -2.5)).astype(np.float32)
        expected_pottery = (valid & (ugs_vv > -18.0) & (ugs_vv < -12.0)).astype(np.float32)
        expected_gear_tent = (valid & (ugs_vh > -18.0) & (ugs_vh < -14.0) & (ugs_vv > -6.0)).astype(np.float32)
        expected_chamber_mid = (valid & (ugs_std_vv > 4.2) & (ugs_vv > -8.0)).astype(np.float32)
        expected_base_deep = (valid & (ugs_vv > -12.0) & (ugs_vv < -7.0)).astype(np.float32)

        expected_box_count = np.full(vv_db.shape, grid_spec.nodata, dtype=np.float32)
        expected_jar_count = np.full(vv_db.shape, grid_spec.nodata, dtype=np.float32)
        expected_box_count[valid] = np.floor(ugs_vv[valid] + np.float32(10.0))
        expected_jar_count[valid] = np.floor(((ugs_vv[valid] - ugs_vh[valid]) - np.float32(10.0)) / np.float32(2.0))

        expected_ugs = [
            ugs_vv,
            ugs_vh,
            expected_rvi,
            expected_box_vertical,
            expected_box_horizontal,
            expected_under_cover,
            expected_exposed_metal,
            expected_depot_proxy,
            expected_box_mine,
            expected_jar_dense,
            expected_pottery,
            expected_gear_tent,
            expected_chamber_mid,
            expected_base_deep,
            expected_box_count,
            expected_jar_count,
        ]
        for band_index, expected in enumerate(expected_ugs):
            np.testing.assert_allclose(ultimate_gphys[:, :, band_index], expected, rtol=1e-5, atol=1e-5)

        aux_bonus = np.load(notebook_dir / NOTEBOOK_AUX_BONUS_FEATURES_STACK_NPY)
        sim_geophysical = np.load(notebook_dir / NOTEBOOK_SIM_GEOPHYSICAL_STACK_NPY)
        assert aux_bonus.shape == (grid_spec.size, grid_spec.size, len(AUX_BONUS_FEATURES_BANDS))
        assert sim_geophysical.shape == (grid_spec.size, grid_spec.size, len(SIM_GEOPHYSICAL_BANDS))

        def nanfill_median(array):
            out = array.copy().astype(np.float32)
            finite = np.isfinite(out)
            fill = np.float32(np.nanmedian(out)) if finite.any() else np.float32(0.0)
            out[~finite] = fill
            return out

        def entropy3(array, valid_mask):
            filled = nanfill_median(array)
            padded = np.pad(filled, 1, mode="edge")
            windows = np.lib.stride_tricks.sliding_window_view(padded, (3, 3))
            flat = windows.reshape(windows.shape[0], windows.shape[1], 9)
            lo = flat.min(axis=-1)
            hi = flat.max(axis=-1)
            span = hi - lo
            usable = span > np.float32(1e-12)
            entropy = np.zeros(array.shape, dtype=np.float32)
            for bin_index in range(16):
                lower = lo + span * np.float32(bin_index / 16.0)
                upper = lo + span * np.float32((bin_index + 1) / 16.0)
                if bin_index == 15:
                    hits = usable[:, :, None] & (flat >= lower[:, :, None]) & (flat <= upper[:, :, None])
                else:
                    hits = usable[:, :, None] & (flat >= lower[:, :, None]) & (flat < upper[:, :, None])
                counts = hits.sum(axis=-1).astype(np.float32)
                probs = counts / np.float32(9.0)
                entropy = np.where(probs > 0.0, entropy - probs * np.log2(probs), entropy).astype(np.float32)
            return np.where(valid_mask, entropy, grid_spec.nodata).astype(np.float32)

        def laplacian_abs(array, valid_mask):
            filled = nanfill_median(array)
            padded = np.pad(filled, 1, mode="edge")
            windows = np.lib.stride_tricks.sliding_window_view(padded, (3, 3))
            kernel = np.array([[1.0, 1.0, 1.0], [1.0, -8.0, 1.0], [1.0, 1.0, 1.0]], dtype=np.float32)
            out = np.abs((windows * kernel).sum(axis=(-2, -1))).astype(np.float32)
            return np.where(valid_mask, out, grid_spec.nodata).astype(np.float32)

        vv_lin_full = np.full(vv_db.shape, np.nan, dtype=np.float32)
        vh_lin_full = np.full(vh_db.shape, np.nan, dtype=np.float32)
        vv_lin_full[valid] = np.power(10.0, vv_db[valid] / 10.0).astype(np.float32)
        vh_lin_full[valid] = np.power(10.0, vh_db[valid] / 10.0).astype(np.float32)

        expected_entropy = entropy3(vv_lin_full, valid)
        expected_moisture = np.full(vv_db.shape, grid_spec.nodata, dtype=np.float32)
        expected_moisture[valid] = vh_lin_full[valid] / np.maximum(vv_lin_full[valid], np.float32(1e-6))
        valid_logratio = np.isfinite(log_ratio_db) & (log_ratio_db != grid_spec.nodata)
        expected_logratio = np.where(valid_logratio, log_ratio_db, grid_spec.nodata).astype(np.float32)

        np.testing.assert_allclose(aux_bonus[:, :, 0], expected_entropy, rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(aux_bonus[:, :, 1], expected_logratio, rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(aux_bonus[:, :, 2], expected_moisture, rtol=1e-5, atol=1e-5)

        expected_gpr = np.full(vv_db.shape, grid_spec.nodata, dtype=np.float32)
        expected_gpr[valid] = np.log10(np.abs(vv_lin_full[valid] - vh_lin_full[valid]) + np.float32(1e-6)).astype(np.float32)
        expected_magnetic = laplacian_abs(vv_lin_full, valid)
        expected_emi = expected_moisture
        expected_microgravity = np.full(vv_db.shape, grid_spec.nodata, dtype=np.float32)
        expected_microgravity[valid] = (
            np.float32(1.0) / np.maximum((vv_lin_full[valid] + vh_lin_full[valid]) / np.float32(2.0), np.float32(1e-6))
        ).astype(np.float32)

        np.testing.assert_allclose(sim_geophysical[:, :, 0], expected_gpr, rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(sim_geophysical[:, :, 1], expected_magnetic, rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(sim_geophysical[:, :, 2], expected_emi, rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(sim_geophysical[:, :, 3], expected_microgravity, rtol=1e-5, atol=1e-5)

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

        for band_name in (*RAD_S0_MASTER_BANDS, *RAD_MASTER_CUBE_BANDS, *GPHYS_MASTER_BANDS, *MASTER_RTC_REFINED_BANDS, *ARCH_TARGETS_BANDS, *ULTIMATE_GPHYS_SCAN_BANDS, *AUX_BONUS_FEATURES_BANDS, *SIM_GEOPHYSICAL_BANDS, *NANO_GEOPHYSICS_BANDS, *TREASURE_GEOPHYSICS_BANDS):
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
        assert alias_by_file[NOTEBOOK_RAD_MASTER_CUBE_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_RAD_MASTER_CUBE_NPY]["source_cell"] == "cell_053"
        assert alias_by_file[NOTEBOOK_GPHYS_MASTER_STACK_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_GPHYS_MASTER_STACK_NPY]["source_cell"] == "cell_051"
        assert alias_by_file[NOTEBOOK_MASTER_RTC_REFINED_STACK_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_MASTER_RTC_REFINED_STACK_NPY]["source_cell"] == "cell_047"
        assert alias_by_file[NOTEBOOK_ARCH_TARGETS_STACK_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_ARCH_TARGETS_STACK_NPY]["source_cell"] == "cell_052"
        assert alias_by_file[NOTEBOOK_ULTIMATE_GPHYS_SCAN_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_ULTIMATE_GPHYS_SCAN_NPY]["source_cell"] == "cell_054"
        assert alias_by_file[NOTEBOOK_AUX_BONUS_FEATURES_STACK_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_AUX_BONUS_FEATURES_STACK_NPY]["source_cell"] == "cell_072"
        assert alias_by_file[NOTEBOOK_SIM_GEOPHYSICAL_STACK_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_SIM_GEOPHYSICAL_STACK_NPY]["source_cell"] == "cell_073"
        assert alias_by_file[NOTEBOOK_NANO_GEOPHYSICS_STACK_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_NANO_GEOPHYSICS_STACK_NPY]["source_cell"] == "cell_037"
        assert alias_by_file[NOTEBOOK_TREASURE_GEOPHYSICS_STACK_NPY]["status"] == "implemented"
        assert alias_by_file[NOTEBOOK_TREASURE_GEOPHYSICS_STACK_NPY]["source_cell"] == "cell_039"
        assert set(alias_manifest["deferred_families"]) == set()

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
            "rad_master_cube_stack",
            "gphys_master_stack",
            "master_rtc_refined_stack",
            "arch_targets_stack",
            "ultimate_gphys_scan_stack",
            "aux_bonus_features_stack",
            "sim_geophysical_stack",
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
        assert family_statuses["RAD_MASTER_CUBE_640"]["status"] == "implemented"
        assert family_statuses["RAD_MASTER_CUBE_640"]["artifact_name"] == "rad_master_cube_stack"
        assert family_statuses["GPHYS_MASTER_640"]["status"] == "implemented"
        assert family_statuses["GPHYS_MASTER_640"]["artifact_name"] == "gphys_master_stack"
        assert family_statuses["MASTER_RTC_REFINED_STACK_640"]["status"] == "implemented"
        assert family_statuses["MASTER_RTC_REFINED_STACK_640"]["artifact_name"] == "master_rtc_refined_stack"
        assert family_statuses["ARCH_TARGETS_STACK_640"]["status"] == "implemented"
        assert family_statuses["ARCH_TARGETS_STACK_640"]["artifact_name"] == "arch_targets_stack"
        assert family_statuses["ULTIMATE_GPHYS_SCAN_640"]["status"] == "implemented"
        assert family_statuses["ULTIMATE_GPHYS_SCAN_640"]["artifact_name"] == "ultimate_gphys_scan_stack"
        assert family_statuses["AUX_BONUS_FEATURES_STACK_640"]["status"] == "implemented"
        assert family_statuses["AUX_BONUS_FEATURES_STACK_640"]["artifact_name"] == "aux_bonus_features_stack"
        assert family_statuses["SIM_GEOPHYSICAL_STACK_640"]["status"] == "implemented"
        assert family_statuses["SIM_GEOPHYSICAL_STACK_640"]["artifact_name"] == "sim_geophysical_stack"
        assert family_statuses["NANO_STACK"]["status"] == "implemented"
        assert family_statuses["NANO_STACK"]["artifact_name"] == "nano_geophysics_stack"
        assert family_statuses["TREASURE_GEOPHYSICS_STACK_640"]["status"] == "implemented"
        assert family_statuses["TREASURE_GEOPHYSICS_STACK_640"]["artifact_name"] == "treasure_geophysics_stack"

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
