"""Check aggregate Sentinel-1 coverage for one private candidate-site polygon.

The default action is a no-network dry run. Use --execute to query Earth Engine.
The command never prints coordinates, the private geometry, private paths, or image IDs.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
S1_COLLECTION_ID = "COPERNICUS/S1_GRD"
ALLOWED_GEOMETRY_TYPES = {"Polygon", "MultiPolygon"}
DEFAULT_RESOLUTION_METERS = 10


class DepthS1CoverageError(ValueError):
    """Raised when a private coverage check cannot proceed safely."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise DepthS1CoverageError(f"{label} must remain outside the repository")


def _parse_iso_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise DepthS1CoverageError(f"{label} must use YYYY-MM-DD") from exc


def validate_date_window(start_date: str, end_date: str, event_date: str | None = None) -> tuple[date, date, date | None]:
    start = _parse_iso_date(start_date, "start date")
    end = _parse_iso_date(end_date, "end date")
    if end <= start:
        raise DepthS1CoverageError("end date must be later than start date")
    event = _parse_iso_date(event_date, "event date") if event_date else None
    if event is not None and not (start <= event < end):
        raise DepthS1CoverageError("event date must fall inside the requested date window")
    return start, end, event


def load_private_geometry(path: Path) -> dict[str, Any]:
    path = Path(path)
    _require_outside_repo(path, "site geometry")
    if not path.is_file():
        raise DepthS1CoverageError("private site geometry file is missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DepthS1CoverageError("private site geometry file is unreadable or invalid JSON") from exc
    return _sanitize_geometry_payload(payload)


def _sanitize_geometry_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise DepthS1CoverageError("site geometry must be a GeoJSON object")

    payload_type = str(payload.get("type", ""))
    if payload_type == "FeatureCollection":
        features = payload.get("features")
        if not isinstance(features, list) or not features:
            raise DepthS1CoverageError("GeoJSON FeatureCollection must contain at least one polygon feature")
        sanitized_features = []
        for feature in features:
            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                raise DepthS1CoverageError("GeoJSON FeatureCollection contains an invalid feature")
            geometry = _sanitize_direct_geometry(feature.get("geometry"))
            sanitized_features.append({"type": "Feature", "properties": {}, "geometry": geometry})
        return {"type": "FeatureCollection", "features": sanitized_features}

    if payload_type == "Feature":
        geometry = _sanitize_direct_geometry(payload.get("geometry"))
        return {"type": "Feature", "properties": {}, "geometry": geometry}

    return _sanitize_direct_geometry(payload)


def _sanitize_direct_geometry(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DepthS1CoverageError("GeoJSON feature is missing a polygon geometry")
    geometry_type = str(value.get("type", ""))
    if geometry_type not in ALLOWED_GEOMETRY_TYPES:
        raise DepthS1CoverageError("site geometry must be Polygon or MultiPolygon")
    coordinates = value.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise DepthS1CoverageError("site geometry coordinates are missing")
    return {"type": geometry_type, "coordinates": coordinates}


def build_query_plan(
    *,
    start_date: str,
    end_date: str,
    event_date: str | None,
    resolution_meters: int,
) -> dict[str, Any]:
    validate_date_window(start_date, end_date, event_date)
    if resolution_meters <= 0:
        raise DepthS1CoverageError("resolution meters must be positive")
    return {
        "collection_id": S1_COLLECTION_ID,
        "start_date": start_date,
        "end_date_exclusive": end_date,
        "event_date": event_date,
        "instrument_mode": "IW",
        "required_polarisations": ["VV", "VH"],
        "resolution_meters": resolution_meters,
    }


def summarize_acquisitions(items: list[dict[str, Any]], event_date: str | None = None) -> dict[str, Any]:
    event = _parse_iso_date(event_date, "event date") if event_date else None
    normalized: list[dict[str, Any]] = []
    for item in items:
        try:
            timestamp_ms = int(item["time_start_ms"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DepthS1CoverageError("coverage metadata contains an invalid acquisition timestamp") from exc
        acquired = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=UTC)
        normalized.append(
            {
                "acquired": acquired,
                "orbit_pass": str(item.get("orbit_pass") or "UNKNOWN").upper(),
                "relative_orbit": str(item.get("relative_orbit") if item.get("relative_orbit") is not None else "UNKNOWN"),
                "platform": str(item.get("platform") or "UNKNOWN").upper(),
            }
        )

    normalized.sort(key=lambda item: item["acquired"])
    pass_counts = Counter(item["orbit_pass"] for item in normalized)
    relative_orbit_counts = Counter(item["relative_orbit"] for item in normalized)
    platform_counts = Counter(item["platform"] for item in normalized)

    pre_event_count = 0
    on_event_date_count = 0
    post_event_count = 0
    if event is not None:
        for item in normalized:
            acquired_date = item["acquired"].date()
            if acquired_date < event:
                pre_event_count += 1
            elif acquired_date == event:
                on_event_date_count += 1
            else:
                post_event_count += 1

    return {
        "acquisition_count": len(normalized),
        "first_acquisition_date": normalized[0]["acquired"].date().isoformat() if normalized else None,
        "last_acquisition_date": normalized[-1]["acquired"].date().isoformat() if normalized else None,
        "orbit_pass_counts": dict(sorted(pass_counts.items())),
        "relative_orbit_counts": dict(sorted(relative_orbit_counts.items(), key=lambda pair: pair[0])),
        "platform_counts": dict(sorted(platform_counts.items())),
        "pre_event_count": pre_event_count if event is not None else None,
        "on_event_date_count": on_event_date_count if event is not None else None,
        "post_event_count": post_event_count if event is not None else None,
    }


def run_coverage_check(
    *,
    site_geojson: Path,
    start_date: str,
    end_date: str,
    event_date: str | None = None,
    resolution_meters: int = DEFAULT_RESOLUTION_METERS,
    execute: bool = False,
    output_path: Path | None = None,
    query_fn: Callable[..., list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    geometry = load_private_geometry(site_geojson)
    plan = build_query_plan(
        start_date=start_date,
        end_date=end_date,
        event_date=event_date,
        resolution_meters=resolution_meters,
    )

    result: dict[str, Any] = {
        "status": "coverage_query_dry_run_ready",
        "query_executed": False,
        **plan,
        "coordinates_printed": False,
        "image_ids_printed": False,
        "private_paths_printed": False,
        "scientific_validation_run": False,
        "training_started": False,
        "app_depth_enabled": False,
    }

    if execute:
        active_query = query_fn or query_s1_metadata
        items = active_query(
            geometry_payload=geometry,
            start_date=start_date,
            end_date=end_date,
            resolution_meters=resolution_meters,
        )
        result.update(summarize_acquisitions(items, event_date=event_date))
        result["status"] = "coverage_query_completed"
        result["query_executed"] = True

    if output_path is not None:
        _require_outside_repo(output_path, "coverage output")
        _atomic_write_json(Path(output_path), result)
        result["output_written"] = True
    else:
        result["output_written"] = False

    return result


def query_s1_metadata(
    *,
    geometry_payload: dict[str, Any],
    start_date: str,
    end_date: str,
    resolution_meters: int,
) -> list[dict[str, Any]]:
    try:
        import ee

        from app.config import get_settings
        from app.services.ee_session import initialize_ee_session

        initialize_ee_session(get_settings())
        if geometry_payload.get("type") == "FeatureCollection":
            geometry = ee.FeatureCollection(geometry_payload).geometry()
        elif geometry_payload.get("type") == "Feature":
            geometry = ee.Geometry(geometry_payload["geometry"])
        else:
            geometry = ee.Geometry(geometry_payload)

        collection = (
            ee.ImageCollection(S1_COLLECTION_ID)
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
            .filter(ee.Filter.eq("resolution_meters", resolution_meters))
            .sort("system:time_start")
        )
        timestamps = collection.aggregate_array("system:time_start").getInfo() or []
        passes = collection.aggregate_array("orbitProperties_pass").getInfo() or []
        relative_orbits = collection.aggregate_array("relativeOrbitNumber_start").getInfo() or []
        platforms = collection.aggregate_array("platform_number").getInfo() or []
    except Exception as exc:
        raise DepthS1CoverageError("Earth Engine Sentinel-1 coverage query failed") from exc

    lengths = {len(timestamps), len(passes), len(relative_orbits), len(platforms)}
    if len(lengths) != 1:
        raise DepthS1CoverageError("Earth Engine returned inconsistent coverage metadata")
    return [
        {
            "time_start_ms": timestamp,
            "orbit_pass": orbit_pass,
            "relative_orbit": relative_orbit,
            "platform": platform,
        }
        for timestamp, orbit_pass, relative_orbit, platform in zip(
            timestamps,
            passes,
            relative_orbits,
            platforms,
            strict=True,
        )
    ]


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        raise DepthS1CoverageError("coverage summary could not be written") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run or execute a private aggregate Sentinel-1 site coverage check.")
    parser.add_argument("--site-geojson", type=Path, required=True)
    parser.add_argument("--start-date", required=True, help="Inclusive YYYY-MM-DD start date.")
    parser.add_argument("--end-date", required=True, help="Exclusive YYYY-MM-DD end date.")
    parser.add_argument("--event-date", help="Optional installation or event date in YYYY-MM-DD form.")
    parser.add_argument("--resolution-meters", type=int, default=DEFAULT_RESOLUTION_METERS)
    parser.add_argument("--execute", action="store_true", help="Query Earth Engine. Without this flag, validate only.")
    parser.add_argument("--output", type=Path, help="Optional aggregate JSON output path outside Git.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_coverage_check(
            site_geojson=args.site_geojson,
            start_date=args.start_date,
            end_date=args.end_date,
            event_date=args.event_date,
            resolution_meters=args.resolution_meters,
            execute=args.execute,
            output_path=args.output,
        )
    except DepthS1CoverageError as exc:
        print(
            json.dumps(
                {
                    "status": "coverage_query_failed",
                    "error": str(exc),
                    "coordinates_printed": False,
                    "image_ids_printed": False,
                    "private_paths_printed": False,
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
