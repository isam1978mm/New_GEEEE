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
from app.pipeline.elevation_change.sources import (
    ASSET_IMAGE_COLLECTION,
    ElevationEpoch,
    build_ee_elevation_image,
)
from app.pipeline.stages.dem import build_grid_region
from app.pipeline.stages.grid import GridSpec
from app.services.ee_session import initialize_ee_session


def assert_epoch_has_data(epoch: ElevationEpoch, region: Any) -> int:
    """Fail early and clearly when an epoch has no imagery over the region.

    Lidar is flown project by project, so a collection covering most of a
    country is routinely empty over one particular site. Left unchecked, an
    empty collection mosaics into a band-less image and Earth Engine reports
    "Band pattern was applied to an Image with no bands", which says nothing
    about the actual cause. This turns that into a sentence the operator can
    act on.

    Returns the image count, or 0 for a single-image asset where the concept
    does not apply.
    """

    if epoch.source.asset_kind != ASSET_IMAGE_COLLECTION:
        return 0

    collection = ee.ImageCollection(epoch.source.asset_id).filterBounds(region)
    if epoch.source.multi_vintage:
        collection = collection.filterDate(
            f"{int(epoch.start_year)}-01-01",
            f"{int(epoch.end_year)}-12-31",
        )
    count = int(collection.size().getInfo())
    if count == 0:
        raise StageError(
            f"No {epoch.source.asset_id} imagery covers this area for epoch "
            f"{epoch.start_year}-{epoch.end_year}. This is a coverage limit of the "
            "public data at this location, not a software fault. Run "
            "scripts/inspect_elevation_sources.py to see which sources do have "
            "data here."
        )
    return count


def create_ee_elevation_tile_fetcher(
    settings: Any,
    grid_spec: GridSpec,
    epoch: ElevationEpoch,
):
    """Build a tile fetcher for one elevation epoch on the run grid."""

    initialize_ee_session(settings)
    region = build_grid_region(grid_spec)
    assert_epoch_has_data(epoch, region)
    image = build_ee_elevation_image(
        epoch,
        region,
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
