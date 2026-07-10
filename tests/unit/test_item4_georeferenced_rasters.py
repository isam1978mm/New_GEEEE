from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.pca_anomaly import write_pca_outputs
from app.pipeline.stages.thermal import write_lst_output


def test_thermal_lst_output_is_georeferenced_geotiff(tmp_path: Path) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    rows, cols = np.indices((grid_spec.size, grid_spec.size), dtype=np.float32)
    lst = (np.float32(295.0) + rows * np.float32(0.01) + cols * np.float32(0.02)).astype(np.float32)

    path = write_lst_output(tmp_path, grid_spec, lst)

    _assert_georeferenced_single_band(path, grid_spec)


def test_pca_anomaly_output_is_georeferenced_geotiff(tmp_path: Path) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    rows, cols = np.indices((grid_spec.size, grid_spec.size), dtype=np.float32)
    anomaly = ((rows + cols) / np.float32(2 * max(grid_spec.size - 1, 1))).astype(np.float32)
    raw_score = (rows + cols).astype(np.float32)
    report = {
        "seed": 0,
        "sample_size": 10,
        "components_count": 1,
        "input_feature_channel_count": 1,
        "feature_channel_count": 1,
        "excluded_feature_channel_count": 0,
        "included_feature_channel_names": ["signal"],
        "excluded_feature_channel_names": [],
        "feature_channel_name_source": "test",
        "used_valid_mask_channel": False,
        "valid_mask_policy": "finite_selected_feature_channels_after_degenerate_exclusion",
        "pca_feature_policy": "exclude_valid_mask_all_nodata_and_near_constant_channels",
        "raw_score_method": "pca_whitened_projected_component_distance",
        "display_stretch_method": "percentile_1_99_on_valid_raw_score",
        "legacy_pca_compatibility_mode": "not_enabled_corrected_default",
        "parity_category": "PARITY_CORRECTS",
        "parity_reason": "test",
        "raw_score_range": {"min": 0.0, "max": 1.0, "mean": 0.5},
        "pixel_count": int(grid_spec.size * grid_spec.size),
        "valid_pixel_count": int(grid_spec.size * grid_spec.size),
        "valid_pixel_fraction": 1.0,
        "min_valid_pixel_fraction": 0.05,
        "eigenvalues": [1.0],
        "explained_variance": [1.0],
        "explained_variance_ratio": [1.0],
    }

    outputs = write_pca_outputs(tmp_path, grid_spec, anomaly, raw_score, report)

    _assert_georeferenced_single_band(outputs["pca_anomaly_tif"], grid_spec)


def _assert_georeferenced_single_band(path: Path, grid_spec) -> None:
    with rasterio.open(path) as dataset:
        assert dataset.crs.to_string() == grid_spec.crs
        assert dataset.transform == Affine(*grid_spec.transform)
        assert dataset.nodata == grid_spec.nodata
        assert dataset.width == grid_spec.size
        assert dataset.height == grid_spec.size
        assert dataset.count == 1
        assert dataset.dtypes == ("float32",)
