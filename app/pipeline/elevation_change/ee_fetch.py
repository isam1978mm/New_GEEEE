"""Earth Engine tile fetching for elevation epochs.

Kept in its own module so every other part of this package stays importable and
unit-testable without an Earth Engine session. Only this file imports ``ee``.

The tiling mirrors ``app.pipeline.stages.dem`` exactly, including the request
rectangle construction and the ``sampleRectangle`` call, so both elevation
epochs land on the same locked grid as the run's other rasters.
"""

from __future__ import annotations

from typing import Any

import ee
import numpy as np

from app.errors import StageError
from app.pipeline.elevation_change.sources import ElevationEpoch, build_ee_elevation_image
from app.pipeline.stages.dem import build_grid_region
from app.pipeline.stages.grid import GridSpec
from app.services.ee_session import initialize_ee_session


def create_ee_elevation_tile_fetcher(
    settings: Any,
    grid_spec: GridSpec,
    epoch: ElevationEpoch,
):
    """Build a tile fetcher for one elevation epoch on the run grid."""

    initialize_ee_session(settings)
    image = build_ee_elevation_image(
        epoch,
        build_grid_region(grid_spec),
        ee_module=ee,
    ).reproject(
        crs=grid_spec.crs,
        crsTransform=list(grid_spec.transform),
    ).unmask(grid_spec.nodata)

    band = epoch.source.band

    def fetch_tile(
        *,
        grid_spec: GridSpec,
        tile_row: int,
        tile_col: int,
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        size: int,
    ) -> np.ndarray:
        del tile_row, tile_col
        tile_geo = ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], grid_spec.crs, False)
        rectangle = image.sampleRectangle(
            region=tile_geo, defaultValue=grid_spec.nodata
        ).getInfo()
        try:
            values = rectangle["properties"][band]
        except (KeyError, TypeError) as exc:
            raise StageError(
                f"Earth Engine returned no {band} band for elevation epoch "
                f"{epoch.label}; the asset may have been renamed or is unavailable "
                "at this location."
            ) from exc
        tile = np.array(values, dtype=np.float32)[:size, :size]
        if tile.shape != (size, size):
            raise StageError(
                f"Elevation tile for {epoch.label} returned shape {tile.shape}, "
                f"expected {(size, size)}."
            )
        return tile

    return fetch_tile
