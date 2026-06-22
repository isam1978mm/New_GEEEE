from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from app.pipeline.stages.dem import write_georeferenced_raster
from app.pipeline.stages.grid import build_run_grid
from app.services.reference_tif_compare import compare_reference_tif


def test_reference_tif_compare_reports_matching_rasters_safely() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        array = np.ones((grid_spec.size, grid_spec.size), dtype=np.float32)
        reference_path = root / "reference.tif"
        app_path = root / "app.tif"
        write_georeferenced_raster(reference_path, array, grid_spec)
        write_georeferenced_raster(app_path, array.copy(), grid_spec)

        result = compare_reference_tif(
            label="safe_compare",
            reference_path=reference_path,
            app_path=app_path,
            tolerance=0.0,
        )
        payload = result.to_safe_dict()

        assert result.pass_ is True
        assert payload == {
            "label": "safe_compare",
            "pass": True,
            "metadata_match": True,
            "values_match": True,
            "masks_match": True,
            "shape_match": True,
            "reference_system_match": True,
            "grid_match": True,
            "dtype_match": True,
            "nodata_match": True,
            "max_abs_error": 0.0,
            "mean_abs_error": 0.0,
            "finite_pixel_count": grid_spec.size * grid_spec.size,
        }
        serialized = str(payload).casefold()
        for forbidden in ("epsg", "transform", "bounds", str(root).casefold()):
            assert forbidden not in serialized


def test_reference_tif_compare_reports_value_mismatch_without_raw_arrays() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        reference = np.zeros((grid_spec.size, grid_spec.size), dtype=np.float32)
        app = reference.copy()
        app[0, 0] = 0.5
        reference_path = root / "reference.tif"
        app_path = root / "app.tif"
        write_georeferenced_raster(reference_path, reference, grid_spec)
        write_georeferenced_raster(app_path, app, grid_spec)

        result = compare_reference_tif(
            label="safe_compare",
            reference_path=reference_path,
            app_path=app_path,
            tolerance=0.1,
        )

        assert result.pass_ is False
        assert result.metadata_match is True
        assert result.values_match is False
        assert result.masks_match is True
        assert result.max_abs_error == 0.5
        assert result.mean_abs_error is not None
