from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import rasterio

from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.grid import GridStage, build_run_grid


def test_notebook_dem_aliases_match_local_sources_numerically() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _build_dem_run(run_dir)

        alias_pairs = [
            ("DEM_GEO8_TIFS/DEM_640.tif", "dem.tif"),
            ("DEM_GEO8_TIFS/slope_deg_640.tif", "slope.tif"),
            ("DEM_GEO8_TIFS/aspect_deg_640.tif", "aspect.tif"),
            ("DEM_GEO8_TIFS/roughness_100m_640.tif", "roughness.tif"),
            ("DEM_GEO8_TIFS/tpi_100m_640.tif", "TPI.tif"),
        ]

        for alias_relative_path, source_relative_path in alias_pairs:
            alias_path = run_dir / alias_relative_path
            source_path = run_dir / source_relative_path

            assert alias_path.is_file(), f"missing DEM alias raster: {alias_relative_path}"
            assert source_path.is_file(), f"missing DEM source raster: {source_relative_path}"

            with rasterio.open(alias_path) as alias_dataset, rasterio.open(source_path) as source_dataset:
                assert alias_dataset.shape == source_dataset.shape, alias_relative_path
                assert alias_dataset.crs == source_dataset.crs, alias_relative_path
                assert alias_dataset.transform == source_dataset.transform, alias_relative_path
                assert alias_dataset.nodata == source_dataset.nodata, alias_relative_path
                assert alias_dataset.count == source_dataset.count == 1, alias_relative_path
                assert alias_dataset.dtypes == source_dataset.dtypes, alias_relative_path

                alias_mask = alias_dataset.read_masks(1) == 0
                source_mask = source_dataset.read_masks(1) == 0
                np.testing.assert_array_equal(alias_mask, source_mask, err_msg=alias_relative_path)

                alias_array = alias_dataset.read(1, masked=False)
                source_array = source_dataset.read(1, masked=False)

            np.testing.assert_array_equal(np.isnan(alias_array), np.isnan(source_array), err_msg=alias_relative_path)
            np.testing.assert_allclose(alias_array, source_array, rtol=0.0, atol=0.0, err_msg=alias_relative_path)

        # hillshade_0to1_640.tif is intentionally excluded here because it is
        # generated as a notebook-compatible output, not a direct alias-vs-source copy.


def _build_dem_run(run_dir: Path) -> None:
    settings = _settings(run_dir)
    grid_spec = build_run_grid(35.59499, 36.12694)
    context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

    asyncio.run(GridStage(latitude=35.59499, longitude=36.12694).run(context))
    asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
    asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
