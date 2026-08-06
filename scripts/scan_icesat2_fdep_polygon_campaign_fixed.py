"""Compatibility entry point for Campaign 007 tile-polygon coordinates.

The shared QueryTile type stores ``polygon_wgs84`` vertices as dictionaries
with ``lon`` and ``lat`` keys. The initial Campaign 007 scanner expected
sequence-style ``[longitude, latitude]`` vertices and failed before any ATL08
query. This entry point installs a strict bbox parser that accepts the real
dictionary representation and also supports sequence-style points for backward
compatibility, then delegates to the unchanged Campaign 007 scanner.

No scientific threshold, polygon constraint, candidate gate, or app behavior is
changed.
"""

from __future__ import annotations

import math
import sys
from collections.abc import Mapping, Sequence
from typing import Any

import scan_icesat2_fdep_polygon_campaign as campaign


def _coordinate_pair(point: object) -> tuple[float, float]:
    longitude: object
    latitude: object
    if isinstance(point, Mapping):
        longitude = point.get("lon")
        latitude = point.get("lat")
    elif isinstance(point, Sequence) and not isinstance(point, (str, bytes)):
        if len(point) < 2:
            raise ValueError("tile polygon point must contain longitude and latitude")
        longitude = point[0]
        latitude = point[1]
    else:
        raise ValueError("tile polygon point has an unsupported representation")

    if not isinstance(longitude, (int, float)) or not isinstance(
        latitude, (int, float)
    ):
        raise ValueError("tile polygon longitude and latitude must be numeric")
    longitude_value = float(longitude)
    latitude_value = float(latitude)
    if not math.isfinite(longitude_value) or not math.isfinite(latitude_value):
        raise ValueError("tile polygon longitude and latitude must be finite")
    return longitude_value, latitude_value


def tile_bbox_wgs84(tile: Any) -> tuple[float, float, float, float]:
    coordinates = [_coordinate_pair(point) for point in tile.polygon_wgs84]
    if not coordinates:
        raise ValueError("tile polygon contains no WGS84 points")
    longitudes = [point[0] for point in coordinates]
    latitudes = [point[1] for point in coordinates]
    return min(longitudes), min(latitudes), max(longitudes), max(latitudes)


def install_fix() -> None:
    """Install the coordinate parser on every live canonical campaign module.

    Some focused tests load the Campaign 007 module more than once and replace
    its canonical ``sys.modules`` entry. Patch both the module captured by this
    compatibility entry point and the module currently registered under the
    canonical name so behavior is independent of import and test order.
    """

    campaign._tile_bbox_wgs84 = tile_bbox_wgs84
    current = sys.modules.get("scan_icesat2_fdep_polygon_campaign")
    if current is not None:
        setattr(current, "_tile_bbox_wgs84", tile_bbox_wgs84)


def main() -> int:
    install_fix()
    return campaign.main()


if __name__ == "__main__":
    raise SystemExit(main())
