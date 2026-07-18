"""Create one private rectangular GeoJSON screening footprint outside Git.

The default action is a dry run. Use --write to create the private GeoJSON file.
The command never prints coordinates or private paths and makes no network request.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
EARTH_RADIUS_M = 6_378_137.0
MAX_ABS_LATITUDE = 85.0


class DepthSitePolygonError(ValueError):
    """Raised when a private screening footprint cannot be created safely."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise DepthSitePolygonError(f"{label} must remain outside the repository")


def validate_polygon_inputs(
    *,
    center_latitude: float,
    center_longitude: float,
    width_meters: float,
    height_meters: float,
) -> None:
    values = (center_latitude, center_longitude, width_meters, height_meters)
    if not all(math.isfinite(value) for value in values):
        raise DepthSitePolygonError("polygon inputs must be finite numbers")
    if abs(center_latitude) > MAX_ABS_LATITUDE:
        raise DepthSitePolygonError("center latitude is outside the supported range")
    if not -180.0 <= center_longitude <= 180.0:
        raise DepthSitePolygonError("center longitude is outside the supported range")
    if width_meters <= 0.0 or height_meters <= 0.0:
        raise DepthSitePolygonError("polygon width and height must be positive")


def build_rectangle_geojson(
    *,
    center_latitude: float,
    center_longitude: float,
    width_meters: float,
    height_meters: float,
) -> dict[str, Any]:
    validate_polygon_inputs(
        center_latitude=center_latitude,
        center_longitude=center_longitude,
        width_meters=width_meters,
        height_meters=height_meters,
    )

    half_height = height_meters / 2.0
    half_width = width_meters / 2.0
    latitude_delta = math.degrees(half_height / EARTH_RADIUS_M)
    longitude_scale = math.cos(math.radians(center_latitude))
    if abs(longitude_scale) < 1e-9:
        raise DepthSitePolygonError("center latitude is too close to a pole")
    longitude_delta = math.degrees(half_width / (EARTH_RADIUS_M * longitude_scale))

    south = center_latitude - latitude_delta
    north = center_latitude + latitude_delta
    west = center_longitude - longitude_delta
    east = center_longitude + longitude_delta
    if west < -180.0 or east > 180.0:
        raise DepthSitePolygonError("screening footprint crosses the antimeridian")

    ring = [
        [west, south],
        [east, south],
        [east, north],
        [west, north],
        [west, south],
    ]
    return {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [ring],
        },
    }


def create_private_site_polygon(
    *,
    output_path: Path,
    center_latitude: float,
    center_longitude: float,
    width_meters: float,
    height_meters: float,
    write: bool = False,
) -> dict[str, Any]:
    output_path = Path(output_path)
    _require_outside_repo(output_path, "site polygon output")
    polygon = build_rectangle_geojson(
        center_latitude=center_latitude,
        center_longitude=center_longitude,
        width_meters=width_meters,
        height_meters=height_meters,
    )

    if write and output_path.exists():
        raise DepthSitePolygonError("private site polygon output already exists")

    result = {
        "status": "private_site_polygon_written" if write else "private_site_polygon_dry_run_ready",
        "polygon_type": "Polygon",
        "vertex_count": 5,
        "width_meters": width_meters,
        "height_meters": height_meters,
        "screening_footprint_requires_visual_review": True,
        "coordinates_printed": False,
        "private_path_printed": False,
        "network_request_made": False,
        "scientific_validation_run": False,
        "training_started": False,
        "app_depth_enabled": False,
        "output_written": write,
    }

    if write:
        _atomic_write_json(output_path, polygon)

    return result


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        raise DepthSitePolygonError("private site polygon could not be written") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or write one private rectangular site-screening GeoJSON footprint."
    )
    parser.add_argument("--center-lat", type=float, required=True)
    parser.add_argument("--center-lon", type=float, required=True)
    parser.add_argument("--width-m", type=float, required=True)
    parser.add_argument("--height-m", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the private GeoJSON. Without this flag, validate only.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = create_private_site_polygon(
            output_path=args.output,
            center_latitude=args.center_lat,
            center_longitude=args.center_lon,
            width_meters=args.width_m,
            height_meters=args.height_m,
            write=args.write,
        )
    except DepthSitePolygonError as exc:
        print(
            json.dumps(
                {
                    "status": "private_site_polygon_failed",
                    "error": str(exc),
                    "coordinates_printed": False,
                    "private_path_printed": False,
                    "network_request_made": False,
                    "app_depth_enabled": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
