"""Create private non-overlapping background candidates around a site polygon.

The default action is a dry run. Use --write to create private GeoJSON files
outside Git. The command makes no network request and never prints coordinates,
geometry, or private paths.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

import create_depth_site_polygon as site_polygon


REPO_ROOT = Path(__file__).resolve().parents[1]
CARDINAL_CANDIDATE_NAMES = ("north", "east", "south", "west")
DIAGONAL_CANDIDATE_NAMES = ("northeast", "southeast", "southwest", "northwest")
CANDIDATE_NAMES = CARDINAL_CANDIDATE_NAMES


class DepthBackgroundCandidateError(ValueError):
    """Raised when private background candidates cannot be created safely."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise DepthBackgroundCandidateError(f"{label} must remain outside the repository")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DepthBackgroundCandidateError("private site geometry is unreadable or invalid JSON") from exc


def _extract_polygon(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise DepthBackgroundCandidateError("site geometry must be a GeoJSON object")

    payload_type = str(payload.get("type", ""))
    if payload_type == "Feature":
        geometry = payload.get("geometry")
    else:
        geometry = payload

    if not isinstance(geometry, dict) or geometry.get("type") != "Polygon":
        raise DepthBackgroundCandidateError("site geometry must be one rectangular Polygon")

    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) != 1:
        raise DepthBackgroundCandidateError("site Polygon must contain exactly one exterior ring")

    ring = coordinates[0]
    if not isinstance(ring, list) or len(ring) != 5:
        raise DepthBackgroundCandidateError("site rectangle must contain five closed-ring vertices")

    normalized: list[tuple[float, float]] = []
    for point in ring:
        if not isinstance(point, list) or len(point) < 2:
            raise DepthBackgroundCandidateError("site rectangle contains an invalid vertex")
        try:
            longitude = float(point[0])
            latitude = float(point[1])
        except (TypeError, ValueError) as exc:
            raise DepthBackgroundCandidateError("site rectangle contains a non-numeric vertex") from exc
        if not math.isfinite(longitude) or not math.isfinite(latitude):
            raise DepthBackgroundCandidateError("site rectangle vertices must be finite")
        if not -180.0 <= longitude <= 180.0:
            raise DepthBackgroundCandidateError("site rectangle longitude is outside the supported range")
        if abs(latitude) > site_polygon.MAX_ABS_LATITUDE:
            raise DepthBackgroundCandidateError("site rectangle latitude is outside the supported range")
        normalized.append((longitude, latitude))

    if normalized[0] != normalized[-1]:
        raise DepthBackgroundCandidateError("site rectangle ring must be closed")

    unique_vertices = set(normalized[:-1])
    if len(unique_vertices) != 4:
        raise DepthBackgroundCandidateError("site rectangle must contain four unique corners")

    longitudes = sorted({point[0] for point in unique_vertices})
    latitudes = sorted({point[1] for point in unique_vertices})
    if len(longitudes) != 2 or len(latitudes) != 2:
        raise DepthBackgroundCandidateError("site Polygon must be an axis-aligned rectangle")

    expected_corners = {
        (longitudes[0], latitudes[0]),
        (longitudes[1], latitudes[0]),
        (longitudes[1], latitudes[1]),
        (longitudes[0], latitudes[1]),
    }
    if unique_vertices != expected_corners:
        raise DepthBackgroundCandidateError("site Polygon must be an axis-aligned rectangle")

    west, east = longitudes
    south, north = latitudes
    center_latitude = (south + north) / 2.0
    center_longitude = (west + east) / 2.0
    longitude_scale = math.cos(math.radians(center_latitude))
    if abs(longitude_scale) < 1e-9:
        raise DepthBackgroundCandidateError("site rectangle is too close to a pole")

    width_meters = math.radians(east - west) * site_polygon.EARTH_RADIUS_M * longitude_scale
    height_meters = math.radians(north - south) * site_polygon.EARTH_RADIUS_M
    if width_meters <= 0.0 or height_meters <= 0.0:
        raise DepthBackgroundCandidateError("site rectangle has invalid dimensions")

    return {
        "center_latitude": center_latitude,
        "center_longitude": center_longitude,
        "width_meters": width_meters,
        "height_meters": height_meters,
        "bbox": (west, south, east, north),
    }


def load_private_site_rectangle(path: Path) -> dict[str, Any]:
    path = Path(path)
    _require_outside_repo(path, "site geometry")
    if not path.is_file():
        raise DepthBackgroundCandidateError("private site geometry file is missing")
    return _extract_polygon(_read_json(path))


def _validate_edge_gap(edge_gap_meters: float) -> float:
    try:
        gap = float(edge_gap_meters)
    except (TypeError, ValueError) as exc:
        raise DepthBackgroundCandidateError("edge gap must be a finite positive number") from exc
    if not math.isfinite(gap) or gap <= 0.0:
        raise DepthBackgroundCandidateError("edge gap must be a finite positive number")
    return gap


def _candidate_names(include_diagonals: bool) -> tuple[str, ...]:
    if include_diagonals:
        return CARDINAL_CANDIDATE_NAMES + DIAGONAL_CANDIDATE_NAMES
    return CARDINAL_CANDIDATE_NAMES


def _offset_center(
    *,
    center_latitude: float,
    center_longitude: float,
    north_meters: float = 0.0,
    east_meters: float = 0.0,
) -> tuple[float, float]:
    latitude = center_latitude + math.degrees(north_meters / site_polygon.EARTH_RADIUS_M)
    if abs(latitude) > site_polygon.MAX_ABS_LATITUDE:
        raise DepthBackgroundCandidateError("background candidate latitude is outside the supported range")

    longitude_scale = math.cos(math.radians(center_latitude))
    if abs(longitude_scale) < 1e-9:
        raise DepthBackgroundCandidateError("site rectangle is too close to a pole")
    longitude = center_longitude + math.degrees(
        east_meters / (site_polygon.EARTH_RADIUS_M * longitude_scale)
    )
    if not -180.0 <= longitude <= 180.0:
        raise DepthBackgroundCandidateError("background candidate crosses the antimeridian")
    return latitude, longitude


def _geometry_bbox(payload: dict[str, Any]) -> tuple[float, float, float, float]:
    ring = payload["geometry"]["coordinates"][0]
    longitudes = [float(point[0]) for point in ring[:-1]]
    latitudes = [float(point[1]) for point in ring[:-1]]
    return min(longitudes), min(latitudes), max(longitudes), max(latitudes)


def _bboxes_overlap(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> bool:
    left_west, left_south, left_east, left_north = left
    right_west, right_south, right_east, right_north = right
    return not (
        left_east <= right_west
        or right_east <= left_west
        or left_north <= right_south
        or right_north <= left_south
    )


def build_background_candidates(
    *,
    site_rectangle: dict[str, Any],
    edge_gap_meters: float,
    include_diagonals: bool = False,
) -> dict[str, dict[str, Any]]:
    gap = _validate_edge_gap(edge_gap_meters)
    width = float(site_rectangle["width_meters"])
    height = float(site_rectangle["height_meters"])
    center_latitude = float(site_rectangle["center_latitude"])
    center_longitude = float(site_rectangle["center_longitude"])

    north_offset = height + gap
    east_offset = width + gap
    offsets = {
        "north": {"north_meters": north_offset, "east_meters": 0.0},
        "east": {"north_meters": 0.0, "east_meters": east_offset},
        "south": {"north_meters": -north_offset, "east_meters": 0.0},
        "west": {"north_meters": 0.0, "east_meters": -east_offset},
        "northeast": {"north_meters": north_offset, "east_meters": east_offset},
        "southeast": {"north_meters": -north_offset, "east_meters": east_offset},
        "southwest": {"north_meters": -north_offset, "east_meters": -east_offset},
        "northwest": {"north_meters": north_offset, "east_meters": -east_offset},
    }

    names = _candidate_names(include_diagonals)
    candidates: dict[str, dict[str, Any]] = {}
    site_bbox = tuple(site_rectangle["bbox"])
    for name in names:
        latitude, longitude = _offset_center(
            center_latitude=center_latitude,
            center_longitude=center_longitude,
            **offsets[name],
        )
        try:
            candidate = site_polygon.build_rectangle_geojson(
                center_latitude=latitude,
                center_longitude=longitude,
                width_meters=width,
                height_meters=height,
            )
        except site_polygon.DepthSitePolygonError as exc:
            raise DepthBackgroundCandidateError(str(exc)) from exc
        if _bboxes_overlap(site_bbox, _geometry_bbox(candidate)):
            raise DepthBackgroundCandidateError("generated background candidate overlaps the site rectangle")
        candidates[name] = candidate

    return candidates


def _candidate_paths(output_directory: Path, names: tuple[str, ...]) -> dict[str, Path]:
    return {name: output_directory / f"background_{name}.geojson" for name in names}


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        raise DepthBackgroundCandidateError("private background candidate could not be written") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def create_private_background_candidates(
    *,
    site_geojson: Path,
    output_directory: Path,
    edge_gap_meters: float,
    include_diagonals: bool = False,
    write: bool = False,
) -> dict[str, Any]:
    output_directory = Path(output_directory)
    _require_outside_repo(output_directory, "background output directory")
    site_rectangle = load_private_site_rectangle(site_geojson)
    gap = _validate_edge_gap(edge_gap_meters)
    names = _candidate_names(include_diagonals)
    candidates = build_background_candidates(
        site_rectangle=site_rectangle,
        edge_gap_meters=gap,
        include_diagonals=include_diagonals,
    )
    candidate_paths = _candidate_paths(output_directory, names)

    existing = [path for path in candidate_paths.values() if path.exists()]
    if write and existing:
        raise DepthBackgroundCandidateError("private background candidate output already exists")

    result = {
        "status": (
            "private_background_candidates_written"
            if write
            else "private_background_candidates_dry_run_ready"
        ),
        "candidate_count": len(candidates),
        "candidate_directions": list(names),
        "diagonal_candidates_included": bool(include_diagonals),
        "edge_gap_meters": gap,
        "candidate_width_meters": round(float(site_rectangle["width_meters"]), 6),
        "candidate_height_meters": round(float(site_rectangle["height_meters"]), 6),
        "visual_review_required": True,
        "comparison_window_only": True,
        "confirmed_no_target_record": False,
        "coordinates_printed": False,
        "geometry_printed": False,
        "private_paths_printed": False,
        "network_request_made": False,
        "scientific_validation_run": False,
        "training_started": False,
        "app_depth_enabled": False,
        "output_written": write,
    }

    if write:
        output_directory.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        try:
            for name in names:
                path = candidate_paths[name]
                _atomic_write_json(path, candidates[name])
                written.append(path)
        except Exception:
            for path in written:
                try:
                    path.unlink()
                except OSError:
                    pass
            raise

    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or write private background-screening GeoJSON candidates."
    )
    parser.add_argument("--site-geojson", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--edge-gap-m", type=float, required=True)
    parser.add_argument(
        "--include-diagonals",
        action="store_true",
        help="Create northeast, southeast, southwest, and northwest candidates in addition to the four cardinal candidates.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the private candidates. Without this flag, validate only.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = create_private_background_candidates(
            site_geojson=args.site_geojson,
            output_directory=args.output_dir,
            edge_gap_meters=args.edge_gap_m,
            include_diagonals=args.include_diagonals,
            write=args.write,
        )
    except DepthBackgroundCandidateError as exc:
        print(
            json.dumps(
                {
                    "status": "private_background_candidates_failed",
                    "error": str(exc),
                    "coordinates_printed": False,
                    "geometry_printed": False,
                    "private_paths_printed": False,
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
