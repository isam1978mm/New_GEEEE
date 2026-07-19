"""Match exact Sentinel-1 acquisitions for a private site and background polygon.

The default action is a no-network dry run. Use --execute only after the private
background polygon has been visually reviewed. Console output is aggregate-only;
exact image identities may be written only to a private manifest outside Git.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Callable

import check_depth_s1_coverage as coverage


REPO_ROOT = Path(__file__).resolve().parents[1]
S1_COLLECTION_ID = coverage.S1_COLLECTION_ID
DEFAULT_RESOLUTION_METERS = coverage.DEFAULT_RESOLUTION_METERS


class DepthS1BackgroundMatchError(ValueError):
    """Raised when a private site-background acquisition match cannot proceed."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise DepthS1BackgroundMatchError(f"{label} must remain outside the repository")


def _validate_selection(orbit_pass: str, relative_orbit: int, platform: str, resolution_meters: int) -> tuple[str, int, str]:
    normalized_pass = str(orbit_pass).strip().upper()
    normalized_platform = str(platform).strip().upper()
    if normalized_pass not in {"ASCENDING", "DESCENDING"}:
        raise DepthS1BackgroundMatchError("orbit pass must be ASCENDING or DESCENDING")
    if relative_orbit <= 0:
        raise DepthS1BackgroundMatchError("relative orbit must be positive")
    if not normalized_platform:
        raise DepthS1BackgroundMatchError("platform must not be blank")
    if resolution_meters <= 0:
        raise DepthS1BackgroundMatchError("resolution meters must be positive")
    return normalized_pass, int(relative_orbit), normalized_platform


def _geometry_signature(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _parse_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise DepthS1BackgroundMatchError(f"{label} must use YYYY-MM-DD") from exc


def _validate_windows(start_date: str, end_date: str, pre_end_exclusive: str, post_start: str) -> tuple[date, date]:
    try:
        coverage.validate_date_window(
            start_date,
            end_date,
            None,
            pre_end_exclusive,
            post_start,
        )
    except coverage.DepthS1CoverageError as exc:
        raise DepthS1BackgroundMatchError(str(exc)) from exc
    return _parse_date(pre_end_exclusive, "pre end exclusive"), _parse_date(post_start, "post start")


def _normalize_query_items(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        image_id = str(item.get("image_id") or "").strip()
        if not image_id:
            raise DepthS1BackgroundMatchError("Sentinel-1 metadata contains a missing image identity")
        if image_id in indexed:
            raise DepthS1BackgroundMatchError("Sentinel-1 metadata contains a duplicate image identity")
        try:
            timestamp_ms = int(item["time_start_ms"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DepthS1BackgroundMatchError("Sentinel-1 metadata contains an invalid acquisition timestamp") from exc
        acquired = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=UTC)
        indexed[image_id] = {
            "image_id": image_id,
            "time_start_ms": timestamp_ms,
            "timestamp": acquired.isoformat(),
            "acquired_date": acquired.date(),
        }
    return indexed


def _partition_ids(
    indexed: dict[str, dict[str, Any]],
    *,
    pre_end: date,
    post_start: date,
) -> dict[str, set[str]]:
    periods = {"pre": set(), "transition": set(), "post": set()}
    for image_id, item in indexed.items():
        acquired_date = item["acquired_date"]
        if acquired_date < pre_end:
            periods["pre"].add(image_id)
        elif acquired_date < post_start:
            periods["transition"].add(image_id)
        else:
            periods["post"].add(image_id)
    return periods


def _matched_manifest_rows(
    image_ids: set[str],
    site_items: dict[str, dict[str, Any]],
    background_items: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for image_id in sorted(image_ids, key=lambda value: (site_items[value]["time_start_ms"], value)):
        site_item = site_items[image_id]
        background_item = background_items[image_id]
        if site_item["time_start_ms"] != background_item["time_start_ms"]:
            raise DepthS1BackgroundMatchError("matched Sentinel-1 image identity has inconsistent timestamps")
        rows.append(
            {
                "image_id": image_id,
                "timestamp": site_item["timestamp"],
            }
        )
    return rows


def summarize_match(
    *,
    site_items: list[dict[str, Any]],
    background_items: list[dict[str, Any]],
    pre_end_exclusive: str,
    post_start: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    pre_end = _parse_date(pre_end_exclusive, "pre end exclusive")
    post = _parse_date(post_start, "post start")
    site_index = _normalize_query_items(site_items)
    background_index = _normalize_query_items(background_items)
    site_periods = _partition_ids(site_index, pre_end=pre_end, post_start=post)
    background_periods = _partition_ids(background_index, pre_end=pre_end, post_start=post)

    matched_pre = site_periods["pre"] & background_periods["pre"]
    matched_transition = site_periods["transition"] & background_periods["transition"]
    matched_post = site_periods["post"] & background_periods["post"]

    exact_pre_match_support = bool(matched_pre)
    exact_post_match_support = bool(matched_post)
    exact_support = exact_pre_match_support and exact_post_match_support
    decision = (
        "site_background_acquisition_match_ready"
        if exact_support
        else "site_background_acquisition_match_not_ready"
    )

    summary = {
        "site_acquisition_count": len(site_index),
        "background_acquisition_count": len(background_index),
        "site_pre_count": len(site_periods["pre"]),
        "background_pre_count": len(background_periods["pre"]),
        "matched_pre_count": len(matched_pre),
        "site_pre_unmatched_count": len(site_periods["pre"] - matched_pre),
        "background_pre_unmatched_count": len(background_periods["pre"] - matched_pre),
        "site_transition_count": len(site_periods["transition"]),
        "background_transition_count": len(background_periods["transition"]),
        "matched_transition_count": len(matched_transition),
        "site_post_count": len(site_periods["post"]),
        "background_post_count": len(background_periods["post"]),
        "matched_post_count": len(matched_post),
        "site_post_unmatched_count": len(site_periods["post"] - matched_post),
        "background_post_unmatched_count": len(background_periods["post"] - matched_post),
        "exact_pre_match_support": exact_pre_match_support,
        "exact_post_match_support": exact_post_match_support,
        "site_background_exact_match_support": exact_support,
        "match_decision": decision,
    }
    manifest = {
        "schema_version": "depth_s1_site_background_match_v1",
        "status": decision,
        "matched_pre": _matched_manifest_rows(matched_pre, site_index, background_index),
        "matched_transition_excluded": _matched_manifest_rows(
            matched_transition,
            site_index,
            background_index,
        ),
        "matched_post": _matched_manifest_rows(matched_post, site_index, background_index),
    }
    return summary, manifest


def run_site_background_match(
    *,
    site_geojson: Path,
    background_geojson: Path,
    start_date: str,
    end_date: str,
    pre_end_exclusive: str,
    post_start: str,
    orbit_pass: str,
    relative_orbit: int,
    platform: str,
    resolution_meters: int = DEFAULT_RESOLUTION_METERS,
    background_reviewed: bool = False,
    execute: bool = False,
    output_path: Path | None = None,
    private_manifest_path: Path | None = None,
    query_fn: Callable[..., list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    try:
        site_geometry = coverage.load_private_geometry(site_geojson)
        background_geometry = coverage.load_private_geometry(background_geojson)
    except coverage.DepthS1CoverageError as exc:
        raise DepthS1BackgroundMatchError(str(exc)) from exc

    if _geometry_signature(site_geometry) == _geometry_signature(background_geometry):
        raise DepthS1BackgroundMatchError("site and background geometries must not be identical")

    _validate_windows(start_date, end_date, pre_end_exclusive, post_start)
    selected_pass, selected_orbit, selected_platform = _validate_selection(
        orbit_pass,
        relative_orbit,
        platform,
        resolution_meters,
    )

    if output_path is not None:
        _require_outside_repo(output_path, "aggregate match output")
    if private_manifest_path is not None:
        _require_outside_repo(private_manifest_path, "private match manifest")
    if output_path is not None and private_manifest_path is not None:
        if Path(output_path).expanduser().resolve(strict=False) == Path(private_manifest_path).expanduser().resolve(strict=False):
            raise DepthS1BackgroundMatchError("aggregate output and private manifest must use different files")

    result: dict[str, Any] = {
        "status": "site_background_match_dry_run_ready",
        "query_executed": False,
        "collection_id": S1_COLLECTION_ID,
        "instrument_mode": "IW",
        "required_polarisations": ["VV", "VH"],
        "resolution_meters": resolution_meters,
        "start_date": start_date,
        "end_date_exclusive": end_date,
        "pre_end_exclusive": pre_end_exclusive,
        "post_start": post_start,
        "selected_orbit_pass": selected_pass,
        "selected_relative_orbit": selected_orbit,
        "selected_platform": selected_platform,
        "background_visual_review_confirmed": bool(background_reviewed),
        "aggregate_output_written": False,
        "private_manifest_written": False,
        "private_manifest_contains_image_ids": False,
        "coordinates_printed": False,
        "geometry_printed": False,
        "private_paths_printed": False,
        "image_ids_printed": False,
        "scientific_validation_run": False,
        "training_started": False,
        "app_depth_enabled": False,
    }

    if execute:
        if not background_reviewed:
            raise DepthS1BackgroundMatchError("execute requires explicit confirmation that the background was visually reviewed")
        active_query = query_fn or query_selected_s1_identity_metadata
        query_kwargs = {
            "start_date": start_date,
            "end_date": end_date,
            "resolution_meters": resolution_meters,
            "orbit_pass": selected_pass,
            "relative_orbit": selected_orbit,
            "platform": selected_platform,
        }
        site_items = active_query(geometry_payload=site_geometry, **query_kwargs)
        background_items = active_query(geometry_payload=background_geometry, **query_kwargs)
        summary, manifest = summarize_match(
            site_items=site_items,
            background_items=background_items,
            pre_end_exclusive=pre_end_exclusive,
            post_start=post_start,
        )
        result.update(summary)
        result["status"] = "site_background_match_completed"
        result["query_executed"] = True

        manifest.update(
            {
                "collection_id": S1_COLLECTION_ID,
                "instrument_mode": "IW",
                "required_polarisations": ["VV", "VH"],
                "resolution_meters": resolution_meters,
                "start_date": start_date,
                "end_date_exclusive": end_date,
                "pre_end_exclusive": pre_end_exclusive,
                "post_start": post_start,
                "selected_orbit_pass": selected_pass,
                "selected_relative_orbit": selected_orbit,
                "selected_platform": selected_platform,
                "coordinates_included": False,
                "geometry_included": False,
            }
        )

        if private_manifest_path is not None:
            result["private_manifest_written"] = True
            result["private_manifest_contains_image_ids"] = True
            _atomic_write_json(Path(private_manifest_path), manifest)

        if output_path is not None:
            result["aggregate_output_written"] = True
            _atomic_write_json(Path(output_path), result)

    return result


def query_selected_s1_identity_metadata(
    *,
    geometry_payload: dict[str, Any],
    start_date: str,
    end_date: str,
    resolution_meters: int,
    orbit_pass: str,
    relative_orbit: int,
    platform: str,
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
            .filter(ee.Filter.eq("orbitProperties_pass", orbit_pass))
            .filter(ee.Filter.eq("relativeOrbitNumber_start", relative_orbit))
            .filter(ee.Filter.eq("platform_number", platform))
            .sort("system:time_start")
        )
        image_ids = collection.aggregate_array("system:index").getInfo() or []
        timestamps = collection.aggregate_array("system:time_start").getInfo() or []
    except Exception as exc:
        raise DepthS1BackgroundMatchError("Earth Engine Sentinel-1 site-background metadata query failed") from exc

    if len(image_ids) != len(timestamps):
        raise DepthS1BackgroundMatchError("Earth Engine returned inconsistent site-background metadata")
    return [
        {"image_id": image_id, "time_start_ms": timestamp}
        for image_id, timestamp in zip(image_ids, timestamps, strict=True)
    ]


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        raise DepthS1BackgroundMatchError("site-background match output could not be written") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or execute an exact private Sentinel-1 site-background acquisition match."
    )
    parser.add_argument("--site-geojson", type=Path, required=True)
    parser.add_argument("--background-geojson", type=Path, required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--pre-end-exclusive", required=True)
    parser.add_argument("--post-start", required=True)
    parser.add_argument("--orbit-pass", default="ASCENDING")
    parser.add_argument("--relative-orbit", type=int, required=True)
    parser.add_argument("--platform", default="A")
    parser.add_argument("--resolution-meters", type=int, default=DEFAULT_RESOLUTION_METERS)
    parser.add_argument(
        "--background-reviewed",
        action="store_true",
        help="Confirm the private background polygon was visually reviewed before execution.",
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path, help="Optional aggregate JSON output outside Git.")
    parser.add_argument(
        "--private-manifest",
        type=Path,
        help="Optional private matched-image manifest outside Git. Never printed.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_site_background_match(
            site_geojson=args.site_geojson,
            background_geojson=args.background_geojson,
            start_date=args.start_date,
            end_date=args.end_date,
            pre_end_exclusive=args.pre_end_exclusive,
            post_start=args.post_start,
            orbit_pass=args.orbit_pass,
            relative_orbit=args.relative_orbit,
            platform=args.platform,
            resolution_meters=args.resolution_meters,
            background_reviewed=args.background_reviewed,
            execute=args.execute,
            output_path=args.output,
            private_manifest_path=args.private_manifest,
        )
    except (DepthS1BackgroundMatchError, coverage.DepthS1CoverageError) as exc:
        print(
            json.dumps(
                {
                    "status": "site_background_match_failed",
                    "error": str(exc),
                    "coordinates_printed": False,
                    "geometry_printed": False,
                    "private_paths_printed": False,
                    "image_ids_printed": False,
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
