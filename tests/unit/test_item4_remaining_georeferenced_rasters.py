from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import rasterio
from rasterio.transform import Affine

from app.pipeline.stages.feature_stacks import _save_stack_geotiff
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.s2_indices import (
    compute_s2_dem_matched_masks,
    compute_s2_indices,
    deterministic_s2_cube_fetcher,
    write_s2_mask_outputs,
    write_s2_outputs,
)


def _assert_georeferenced(path: Path, *, grid_spec, count: int, nodata: float | None = None) -> None:
    with rasterio.open(path) as dataset:
        assert dataset.crs.to_string() == grid_spec.crs
        assert dataset.transform == Affine(*grid_spec.transform)
        expected_nodata = grid_spec.nodata if nodata is None else nodata
        assert dataset.nodata == expected_nodata
        assert dataset.width == grid_spec.size
        assert dataset.height == grid_spec.size
        assert dataset.count == count


def test_s2_index_and_mask_tiffs_are_georeferenced() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        cube = deterministic_s2_cube_fetcher(grid_spec=grid_spec)
        outputs = compute_s2_indices(cube, nodata=grid_spec.nodata)
        paths = write_s2_outputs(run_dir, grid_spec, outputs)
        masks = compute_s2_dem_matched_masks(cube, outputs, nodata=grid_spec.nodata)
        mask_outputs = write_s2_mask_outputs(
            run_dir,
            grid_spec,
            masks,
            start_date="2022-01-01",
            end_date="2026-02-28",
            cloud_max=3,
        )

        _assert_georeferenced(paths[0], grid_spec=grid_spec, count=1)
        _assert_georeferenced(mask_outputs["raw_valid_mask_tif"], grid_spec=grid_spec, count=1, nodata=0.0)
        _assert_georeferenced(mask_outputs["index_valid_mask_tif"], grid_spec=grid_spec, count=1, nodata=0.0)


def test_feature_stack_support_tiff_is_multiband_georeferenced() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        rows, cols = np.indices((grid_spec.size, grid_spec.size), dtype=np.float32)
        cube = np.stack(
            [
                rows,
                cols,
                rows + cols,
            ],
            axis=-1,
        ).astype(np.float32)
        path = run_dir / "stack.tif"

        _save_stack_geotiff(path, cube, grid_spec)

        _assert_georeferenced(path, grid_spec=grid_spec, count=3)
