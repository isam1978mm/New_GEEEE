from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import rasterio

from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.sar_rtc import SarRtcStage, deterministic_radar_cube_fetcher


def test_notebook_sar_geotiff_aliases_match_local_sources_numerically() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        _build_sar_run(run_dir)

        alias_pairs = [
            ("GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_app.tif", "VV_dB.tif"),
            ("GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_app.tif", "VH_dB.tif"),
            ("GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_app.tif", "logRatio_dB.tif"),
            ("GEOTIFF_RADAR_BANDS/RADAR_angle_640_app.tif", "incidence.tif"),
        ]

        for alias_relative_path, source_relative_path in alias_pairs:
            alias_path = run_dir / alias_relative_path
            source_path = run_dir / source_relative_path

            assert alias_path.is_file(), f"missing SAR GeoTIFF alias raster: {alias_relative_path}"
            assert source_path.is_file(), f"missing SAR GeoTIFF source raster: {source_relative_path}"

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


def _build_sar_run(run_dir: Path) -> None:
    settings = _settings(run_dir)
    grid_spec = build_run_grid(35.59499, 36.12694)
    context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

    asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
    asyncio.run(SarRtcStage(grid_spec=grid_spec, radar_cube_fetcher=deterministic_radar_cube_fetcher).run(context))


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
