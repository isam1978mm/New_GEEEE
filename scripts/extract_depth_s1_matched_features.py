"""Extract private matched Sentinel-1 site/background summary features.

The default action is a no-network dry run. Use --execute only after an exact
site-background match manifest has been frozen privately. Detailed feature values
and image identities are written only to a private output outside Git.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import check_depth_s1_coverage as coverage


REPO_ROOT = Path(__file__).resolve().parents[1]
S1_COLLECTION_ID = coverage.S1_COLLECTION_ID
MATCH_MANIFEST_SCHEMA = "depth_s1_site_background_match_v1"
PRIVATE_OUTPUT_SCHEMA = "depth_s1_matched_feature_extract_v1"
IMAGE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
FEATURE_NAMES = (
    "vv_db",
    "vh_db",
    "incidence_deg",
    "vv_minus_vh_db",
    "vh_to_vv_linear_ratio",
)
STATISTIC_NAMES = ("p25", "median", "p75", "count")
STATISTIC_KEYS = tuple(
    f"{feature}_{statistic}"
    for feature in FEATURE_NAMES
    for statistic in STATISTIC_NAMES
)
DELTA_KEYS = tuple(
    f"{feature}_{statistic}"
    for feature in FEATURE_NAMES
    for statistic in ("p25", "median", "p75")
)


class DepthS1MatchedFeatureError(ValueError):
    """Raised when private matched feature extraction cannot proceed safely."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise DepthS1MatchedFeatureError(f"{label} must remain outside the repository")


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DepthS1MatchedFeatureError(f"{label} is unreadable or invalid JSON") from exc


def _parse_timestamp(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise DepthS1MatchedFeatureError(f"{label} contains a missing timestamp")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DepthS1MatchedFeatureError(f"{label} contains an invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise DepthS1MatchedFeatureError(f"{label} timestamp must include a timezone")
    return parsed.astimezone(UTC).isoformat()


def _normalize_manifest_rows(rows: Any, label: str, *, require_non_empty: bool) -> list[dict[str, str]]:
    if not isinstance(rows, list):
        raise DepthS1MatchedFeatureError(f"{label} must be a list")
    if require_non_empty and not rows:
        raise DepthS1MatchedFeatureError(f"{label} must not be empty")

    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in rows:
        if not isinstance(item, dict):
            raise DepthS1MatchedFeatureError(f"{label} contains an invalid row")
        image_id = str(item.get("image_id") or "").strip()
        if not image_id or not IMAGE_ID_PATTERN.fullmatch(image_id):
            raise DepthS1MatchedFeatureError(f"{label} contains an invalid image identity")
        if image_id in seen:
            raise DepthS1MatchedFeatureError(f"{label} contains a duplicate image identity")
        seen.add(image_id)
        normalized.append(
            {
                "image_id": image_id,
                "timestamp": _parse_timestamp(item.get("timestamp"), label),
            }
        )
    return normalized


def load_private_match_manifest(path: Path) -> dict[str, Any]:
    path = Path(path)
    _require_outside_repo(path, "match manifest")
    if not path.is_file():
        raise DepthS1MatchedFeatureError("private match manifest is missing")
    payload = _read_json(path, "private match manifest")
    if not isinstance(payload, dict):
        raise DepthS1MatchedFeatureError("private match manifest must be a JSON object")
    if payload.get("schema_version") != MATCH_MANIFEST_SCHEMA:
        raise DepthS1MatchedFeatureError("private match manifest schema is unsupported")
    if payload.get("status") != "site_background_acquisition_match_ready":
        raise DepthS1MatchedFeatureError("private match manifest is not ready for feature extraction")
    if payload.get("collection_id") != S1_COLLECTION_ID:
        raise DepthS1MatchedFeatureError("private match manifest uses an unsupported collection")
    if payload.get("instrument_mode") != "IW":
        raise DepthS1MatchedFeatureError("private match manifest must use Sentinel-1 IW mode")
    required_polarisations = payload.get("required_polarisations")
    if not isinstance(required_polarisations, list) or not {"VV", "VH"}.issubset(
        {str(value) for value in required_polarisations}
    ):
        raise DepthS1MatchedFeatureError("private match manifest must require VV and VH")
    if payload.get("coordinates_included") is True or payload.get("geometry_included") is True:
        raise DepthS1MatchedFeatureError("private match manifest must not embed coordinates or geometry")

    try:
        resolution_meters = int(payload["resolution_meters"])
        relative_orbit = int(payload["selected_relative_orbit"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DepthS1MatchedFeatureError("private match manifest selection metadata is invalid") from exc
    orbit_pass = str(payload.get("selected_orbit_pass") or "").strip().upper()
    platform = str(payload.get("selected_platform") or "").strip().upper()
    if resolution_meters <= 0 or relative_orbit <= 0:
        raise DepthS1MatchedFeatureError("private match manifest selection metadata is invalid")
    if orbit_pass not in {"ASCENDING", "DESCENDING"} or not platform:
        raise DepthS1MatchedFeatureError("private match manifest selection metadata is invalid")

    matched_pre = _normalize_manifest_rows(
        payload.get("matched_pre"),
        "matched_pre",
        require_non_empty=True,
    )
    matched_transition = _normalize_manifest_rows(
        payload.get("matched_transition_excluded", []),
        "matched_transition_excluded",
        require_non_empty=False,
    )
    matched_post = _normalize_manifest_rows(
        payload.get("matched_post"),
        "matched_post",
        require_non_empty=True,
    )

    groups = {
        "matched_pre": {row["image_id"] for row in matched_pre},
        "matched_transition_excluded": {row["image_id"] for row in matched_transition},
        "matched_post": {row["image_id"] for row in matched_post},
    }
    labels = list(groups)
    for index, left_label in enumerate(labels):
        for right_label in labels[index + 1 :]:
            if groups[left_label] & groups[right_label]:
                raise DepthS1MatchedFeatureError("private match manifest periods contain overlapping image identities")

    return {
        "schema_version": MATCH_MANIFEST_SCHEMA,
        "status": payload["status"],
        "collection_id": S1_COLLECTION_ID,
        "instrument_mode": "IW",
        "required_polarisations": ["VV", "VH"],
        "resolution_meters": resolution_meters,
        "start_date": str(payload.get("start_date") or ""),
        "end_date_exclusive": str(payload.get("end_date_exclusive") or ""),
        "pre_end_exclusive": str(payload.get("pre_end_exclusive") or ""),
        "post_start": str(payload.get("post_start") or ""),
        "selected_orbit_pass": orbit_pass,
        "selected_relative_orbit": relative_orbit,
        "selected_platform": platform,
        "matched_pre": matched_pre,
        "matched_transition_excluded": matched_transition,
        "matched_post": matched_post,
    }


def _geometry_signature(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _normalize_stat_value(value: Any, key: str) -> float | int | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    if key.endswith("_count"):
        if numeric < 0:
            return None
        return int(round(numeric))
    return numeric


def _normalize_feature_stats(value: Any) -> dict[str, float | int | None]:
    source = value if isinstance(value, dict) else {}
    return {
        key: _normalize_stat_value(source.get(key), key)
        for key in STATISTIC_KEYS
    }


def _normalize_query_items(items: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        raise DepthS1MatchedFeatureError("feature query returned an invalid result")
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            raise DepthS1MatchedFeatureError("feature query returned an invalid row")
        image_id = str(item.get("image_id") or "").strip()
        if not image_id or not IMAGE_ID_PATTERN.fullmatch(image_id):
            raise DepthS1MatchedFeatureError("feature query returned an invalid image identity")
        if image_id in indexed:
            raise DepthS1MatchedFeatureError("feature query returned a duplicate image identity")
        indexed[image_id] = {
            "image_id": image_id,
            "timestamp": _parse_timestamp(item.get("timestamp"), "feature query"),
            "site": _normalize_feature_stats(item.get("site")),
            "background": _normalize_feature_stats(item.get("background")),
        }
    return indexed


def _missing_stats(stats: dict[str, float | int | None]) -> int:
    return sum(1 for key in STATISTIC_KEYS if stats.get(key) is None)


def _delta_stats(
    site: dict[str, float | int | None],
    background: dict[str, float | int | None],
) -> dict[str, float | None]:
    deltas: dict[str, float | None] = {}
    for key in DELTA_KEYS:
        site_value = site.get(key)
        background_value = background.get(key)
        if site_value is None or background_value is None:
            deltas[key] = None
        else:
            deltas[key] = float(site_value) - float(background_value)
    return deltas


def build_private_feature_rows(
    *,
    manifest: dict[str, Any],
    query_items: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    indexed = _normalize_query_items(query_items)
    expected_rows = [
        ("pre", row) for row in manifest["matched_pre"]
    ] + [
        ("post", row) for row in manifest["matched_post"]
    ]
    expected_ids = {row["image_id"] for _, row in expected_rows}
    unexpected_ids = set(indexed) - expected_ids
    if unexpected_ids:
        raise DepthS1MatchedFeatureError("feature query returned image identities outside the private manifest")

    private_rows: list[dict[str, Any]] = []
    missing_statistic_count = 0
    extracted_pre_count = 0
    extracted_post_count = 0
    missing_image_count = 0

    empty_stats = {key: None for key in STATISTIC_KEYS}
    for period, manifest_row in expected_rows:
        image_id = manifest_row["image_id"]
        query_row = indexed.get(image_id)
        if query_row is None:
            missing_image_count += 1
            site_stats = dict(empty_stats)
            background_stats = dict(empty_stats)
        else:
            if query_row["timestamp"] != manifest_row["timestamp"]:
                raise DepthS1MatchedFeatureError("feature query timestamp does not match the private manifest")
            site_stats = query_row["site"]
            background_stats = query_row["background"]
            if period == "pre":
                extracted_pre_count += 1
            else:
                extracted_post_count += 1

        missing_statistic_count += _missing_stats(site_stats)
        missing_statistic_count += _missing_stats(background_stats)
        private_rows.append(
            {
                "period": period,
                "image_id": image_id,
                "timestamp": manifest_row["timestamp"],
                "site": site_stats,
                "background": background_stats,
                "site_minus_background": _delta_stats(site_stats, background_stats),
            }
        )

    expected_statistic_count = len(expected_rows) * 2 * len(STATISTIC_KEYS)
    all_rows_complete = missing_statistic_count == 0 and missing_image_count == 0
    summary = {
        "manifest_pre_count": len(manifest["matched_pre"]),
        "manifest_post_count": len(manifest["matched_post"]),
        "transition_rows_excluded": len(manifest["matched_transition_excluded"]),
        "extracted_pre_count": extracted_pre_count,
        "extracted_post_count": extracted_post_count,
        "missing_image_count": missing_image_count,
        "expected_statistic_count": expected_statistic_count,
        "missing_statistic_count": missing_statistic_count,
        "all_rows_complete": all_rows_complete,
    }
    return private_rows, summary


def _as_ee_geometry(ee: Any, payload: dict[str, Any]) -> Any:
    if payload.get("type") == "FeatureCollection":
        return ee.FeatureCollection(payload).geometry()
    if payload.get("type") == "Feature":
        return ee.Geometry(payload["geometry"])
    return ee.Geometry(payload)


def query_exact_s1_feature_summaries(
    *,
    manifest_rows: list[dict[str, str]],
    site_geometry_payload: dict[str, Any],
    background_geometry_payload: dict[str, Any],
    resolution_meters: int,
) -> list[dict[str, Any]]:
    try:
        import ee

        from app.config import get_settings
        from app.services.ee_session import initialize_ee_session

        initialize_ee_session(get_settings())
        site_geometry = _as_ee_geometry(ee, site_geometry_payload)
        background_geometry = _as_ee_geometry(ee, background_geometry_payload)
        reducer = ee.Reducer.percentile([25, 50, 75], ["p25", "median", "p75"]).combine(
            ee.Reducer.count(),
            True,
        )

        features = []
        for row in manifest_rows:
            image = ee.Image(f"{S1_COLLECTION_ID}/{row['image_id']}").select(["VV", "VH", "angle"])
            mask = (
                image.select("VV").gt(-35)
                .And(image.select("VH").gt(-42))
                .And(image.select("angle").gt(29))
                .And(image.select("angle").lt(46))
            )
            image = image.updateMask(mask)
            vv = image.select("VV").rename("vv_db")
            vh = image.select("VH").rename("vh_db")
            angle = image.select("angle").rename("incidence_deg")
            difference = vv.subtract(vh).rename("vv_minus_vh_db")
            ratio = ee.Image(10).pow(vh.subtract(vv).divide(10.0)).rename("vh_to_vv_linear_ratio")
            feature_image = ee.Image.cat([vv, vh, angle, difference, ratio]).toFloat()
            site_stats = feature_image.reduceRegion(
                reducer=reducer,
                geometry=site_geometry,
                scale=resolution_meters,
                maxPixels=100000,
                bestEffort=False,
                tileScale=2,
            )
            background_stats = feature_image.reduceRegion(
                reducer=reducer,
                geometry=background_geometry,
                scale=resolution_meters,
                maxPixels=100000,
                bestEffort=False,
                tileScale=2,
            )
            features.append(
                ee.Feature(
                    None,
                    {
                        "image_id": row["image_id"],
                        "timestamp": row["timestamp"],
                        "site": site_stats,
                        "background": background_stats,
                    },
                )
            )

        response = ee.FeatureCollection(features).getInfo()
    except Exception as exc:
        raise DepthS1MatchedFeatureError("Earth Engine matched feature query failed") from exc

    returned = response.get("features") if isinstance(response, dict) else None
    if not isinstance(returned, list):
        raise DepthS1MatchedFeatureError("Earth Engine matched feature query returned an invalid response")
    rows: list[dict[str, Any]] = []
    for feature in returned:
        properties = feature.get("properties") if isinstance(feature, dict) else None
        if not isinstance(properties, dict):
            raise DepthS1MatchedFeatureError("Earth Engine matched feature query returned an invalid row")
        rows.append(
            {
                "image_id": properties.get("image_id"),
                "timestamp": properties.get("timestamp"),
                "site": properties.get("site"),
                "background": properties.get("background"),
            }
        )
    return rows


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        raise DepthS1MatchedFeatureError("private matched feature output could not be written") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def run_matched_feature_extraction(
    *,
    site_geojson: Path,
    background_geojson: Path,
    match_manifest: Path,
    output_path: Path | None = None,
    execute: bool = False,
    query_fn: Callable[..., list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    try:
        site_geometry = coverage.load_private_geometry(site_geojson)
        background_geometry = coverage.load_private_geometry(background_geojson)
    except coverage.DepthS1CoverageError as exc:
        raise DepthS1MatchedFeatureError(str(exc)) from exc
    if _geometry_signature(site_geometry) == _geometry_signature(background_geometry):
        raise DepthS1MatchedFeatureError("site and background geometries must not be identical")

    manifest = load_private_match_manifest(match_manifest)
    if output_path is not None:
        _require_outside_repo(output_path, "private matched feature output")
    if execute and output_path is None:
        raise DepthS1MatchedFeatureError("execute requires a private output path outside the repository")

    result: dict[str, Any] = {
        "status": "matched_s1_feature_extraction_dry_run_ready",
        "query_executed": False,
        "private_output_written": False,
        "collection_id": S1_COLLECTION_ID,
        "instrument_mode": "IW",
        "required_polarisations": ["VV", "VH"],
        "resolution_meters": manifest["resolution_meters"],
        "selected_orbit_pass": manifest["selected_orbit_pass"],
        "selected_relative_orbit": manifest["selected_relative_orbit"],
        "selected_platform": manifest["selected_platform"],
        "exact_manifest_selection": True,
        "manifest_pre_count": len(manifest["matched_pre"]),
        "manifest_post_count": len(manifest["matched_post"]),
        "transition_rows_excluded": len(manifest["matched_transition_excluded"]),
        "feature_names": list(FEATURE_NAMES),
        "statistics_per_feature": list(STATISTIC_NAMES),
        "expected_statistic_count": (
            (len(manifest["matched_pre"]) + len(manifest["matched_post"]))
            * 2
            * len(STATISTIC_KEYS)
        ),
        "missing_statistic_count": None,
        "missing_image_count": None,
        "all_rows_complete": False,
        "coordinates_printed": False,
        "geometry_printed": False,
        "private_paths_printed": False,
        "image_ids_printed": False,
        "feature_values_printed": False,
        "scientific_validation_run": False,
        "training_started": False,
        "app_depth_enabled": False,
    }

    if execute:
        active_query = query_fn or query_exact_s1_feature_summaries
        analysis_rows = manifest["matched_pre"] + manifest["matched_post"]
        query_items = active_query(
            manifest_rows=analysis_rows,
            site_geometry_payload=site_geometry,
            background_geometry_payload=background_geometry,
            resolution_meters=manifest["resolution_meters"],
        )
        private_rows, summary = build_private_feature_rows(
            manifest=manifest,
            query_items=query_items,
        )
        result.update(summary)
        result["query_executed"] = True
        result["status"] = (
            "matched_s1_feature_extraction_complete"
            if summary["all_rows_complete"]
            else "matched_s1_feature_extraction_incomplete"
        )
        result["private_output_written"] = True
        private_payload = {
            "schema_version": PRIVATE_OUTPUT_SCHEMA,
            "status": result["status"],
            "selection_contract": {
                "collection_id": S1_COLLECTION_ID,
                "instrument_mode": "IW",
                "required_polarisations": ["VV", "VH"],
                "resolution_meters": manifest["resolution_meters"],
                "selected_orbit_pass": manifest["selected_orbit_pass"],
                "selected_relative_orbit": manifest["selected_relative_orbit"],
                "selected_platform": manifest["selected_platform"],
                "start_date": manifest["start_date"],
                "end_date_exclusive": manifest["end_date_exclusive"],
                "pre_end_exclusive": manifest["pre_end_exclusive"],
                "post_start": manifest["post_start"],
            },
            "feature_names": list(FEATURE_NAMES),
            "statistics_per_feature": list(STATISTIC_NAMES),
            "transition_rows_excluded": len(manifest["matched_transition_excluded"]),
            "coordinates_included": False,
            "geometry_included": False,
            "rows": private_rows,
        }
        _atomic_write_json(Path(output_path), private_payload)

    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or execute private exact-manifest Sentinel-1 site-background feature extraction."
    )
    parser.add_argument("--site-geojson", type=Path, required=True)
    parser.add_argument("--background-geojson", type=Path, required=True)
    parser.add_argument("--match-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Required private detailed JSON output when --execute is used.")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_matched_feature_extraction(
            site_geojson=args.site_geojson,
            background_geojson=args.background_geojson,
            match_manifest=args.match_manifest,
            output_path=args.output,
            execute=args.execute,
        )
    except (DepthS1MatchedFeatureError, coverage.DepthS1CoverageError) as exc:
        print(
            json.dumps(
                {
                    "status": "matched_s1_feature_extraction_failed",
                    "error": str(exc),
                    "coordinates_printed": False,
                    "geometry_printed": False,
                    "private_paths_printed": False,
                    "image_ids_printed": False,
                    "feature_values_printed": False,
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
