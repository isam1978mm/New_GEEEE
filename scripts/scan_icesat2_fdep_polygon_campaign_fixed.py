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
from pathlib import Path
from types import ModuleType
from typing import Any

import scan_icesat2_fdep_polygon_campaign as campaign


_CANONICAL_MODULE = "scan_icesat2_fdep_polygon_campaign"
_CANONICAL_FILENAME = "scan_icesat2_fdep_polygon_campaign.py"


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


def _is_campaign_module(value: object) -> bool:
    if not isinstance(value, ModuleType):
        return False
    if value.__name__ == _CANONICAL_MODULE:
        return True
    module_file = getattr(value, "__file__", None)
    return bool(module_file) and Path(module_file).name == _CANONICAL_FILENAME


def _patch_campaign_module(module: object) -> None:
    if _is_campaign_module(module):
        setattr(module, "_tile_bbox_wgs84", tile_bbox_wgs84)


def install_fix() -> None:
    """Install the coordinate parser on every live canonical campaign module.

    Focused tests can load the Campaign 007 source more than once and retain an
    older module object after replacing its canonical ``sys.modules`` entry.
    Patch the captured import, the current canonical entry, every loaded copy of
    the campaign module, and campaign-module references retained by test modules.
    """

    _patch_campaign_module(campaign)
    _patch_campaign_module(sys.modules.get(_CANONICAL_MODULE))

    for loaded_module in tuple(sys.modules.values()):
        _patch_campaign_module(loaded_module)
        if isinstance(loaded_module, ModuleType):
            _patch_campaign_module(getattr(loaded_module, "campaign", None))


def main() -> int:
    install_fix()
    return campaign.main()


if __name__ == "__main__":
    raise SystemExit(main())
