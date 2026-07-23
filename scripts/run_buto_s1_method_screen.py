"""Run a bounded Sentinel-1 spatial comparison for the published Buto case.

The default action is a no-network dry run. Use --execute to query Earth Engine.
Detailed numeric output is written only to a path outside the repository. Terminal
output is redacted and never contains coordinates, image IDs, private paths, or
feature values.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
S1_COLLECTION_ID = "COPERNICUS/S1_GRD"
DEFAULT_IMAGE_DATE = "2018-05-05"
DEFAULT_SUPPORT_DAYS = 36
DEFAULT_ANALYSIS_SCALE_METERS = 20
MIN_VALID_PIXELS = 4
ALLOWED_GEOMETRY_TYPES = {"Polygon", "MultiPolygon"}
FEATURE_NAMES = (
    "vv_db",
    "vh_db",
    "vv_minus_vh_db",
    "vh_to_vv_linear_ratio",
    "incidence_angle",
)
SIGNAL_FEATURE_NAMES = FEATURE_NAMES[:-1]


class ButoMethodScreenError(ValueError):
    """Raised when the bounded method screen cannot proceed safely."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise ButoMethodScreenError(f"{label} must remain outside the repository")


def _parse_iso_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ButoMethodScreenError(f"{label} must use YYYY-MM-DD") from exc


def _sanitize_direct_geometry(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ButoMethodScreenError("GeoJSON feature is missing a polygon geometry")
    geometry_type = str(value.get("type", ""))
    if geometry_type not in ALLOWED_GEOMETRY_TYPES:
        raise ButoMethodScreenError("geometry must be Polygon or MultiPolygon")
    coordinates = value.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise ButoMethodScreenError("geometry coordinates are missing")
    return {"type": geometry_type, "coordinates": coordinates}


def _sanitize_geometry_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ButoMethodScreenError("geometry must be a GeoJSON object")
    payload_type = str(payload.get("type", ""))
    if payload_type == "FeatureCollection":
        features = payload.get("features")
        if not isinstance(features, list) or not features:
            raise ButoMethodScreenError("FeatureCollection must contain a polygon feature")
        sanitized = []
        for feature in features:
            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                raise ButoMethodScreenError("FeatureCollection contains an invalid feature")
            sanitized.append(
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": _sanitize_direct_geometry(feature.get("geometry")),
                }
            )
        return {"type": "FeatureCollection", "features": sanitized}
    if payload_type == "Feature":
        return {
            "type": "Feature",
            "properties": {},
            "geometry": _sanitize_direct_geometry(payload.get("geometry")),
        }
    return _sanitize_direct_geometry(payload)


def load_local_geometry(path: Path, label: str) -> dict[str, Any]:
    path = Path(path)
    _require_outside_repo(path, label)
    if not path.is_file():
        raise ButoMethodScreenError(f"{label} file is missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ButoMethodScreenError(f"{label} file is unreadable or invalid JSON") from exc
    return _sanitize_geometry_payload(payload)


def build_query_plan(
    *,
    image_date: str,
    support_days: int,
    analysis_scale_meters: int,
) -> dict[str, Any]:
    exact = _parse_iso_date(image_date, "image date")
    if support_days < 0:
        raise ButoMethodScreenError("support days must be zero or greater")
    if analysis_scale_meters <= 0:
        raise ButoMethodScreenError("analysis scale must be positive")
    start = exact - timedelta(days=support_days)
    end_exclusive = exact + timedelta(days=support_days + 1)
    return {
        "collection_id": S1_COLLECTION_ID,
        "image_date": exact.isoformat(),
        "support_start": start.isoformat(),
        "support_end_exclusive": end_exclusive.isoformat(),
        "support_days": support_days,
        "analysis_scale_meters": analysis_scale_meters,
        "instrument_mode": "IW",
        "required_polarisations": ["VV", "VH"],
        "method_scope": "spatial_comparison_only",
    }


def _safe_float(value: Any, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ButoMethodScreenError(f"query result contains invalid {label}") from exc
    if not math.isfinite(numeric):
        raise ButoMethodScreenError(f"query result contains non-finite {label}")
    return numeric


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    try:
        acquired = _parse_iso_date(str(row["acquired_date"]), "acquisition date")
    except KeyError as exc:
        raise ButoMethodScreenError("query result is missing acquisition date") from exc

    normalized: dict[str, Any] = {
        "acquired_date": acquired.isoformat(),
        "orbit_pass": str(row.get("orbit_pass") or "UNKNOWN").upper(),
        "relative_orbit": str(
            row.get("relative_orbit") if row.get("relative_orbit") is not None else "UNKNOWN"
        ),
        "platform": str(row.get("platform") or "UNKNOWN").upper(),
        "target_valid_pixels": int(row.get("target_valid_pixels") or 0),
        "background_valid_pixels": int(row.get("background_valid_pixels") or 0),
        "features": {},
    }
    raw_features = row.get("features")
    if not isinstance(raw_features, dict):
        raise ButoMethodScreenError("query result is missing feature summaries")
    for feature in FEATURE_NAMES:
        raw = raw_features.get(feature)
        if not isinstance(raw, dict):
            raise ButoMethodScreenError(f"query result is missing {feature}")
        target_median = _safe_float(raw.get("target_median"), f"{feature} target median")
        background_median = _safe_float(
            raw.get("background_median"), f"{feature} background median"
        )
        normalized["features"][feature] = {
            "target_median": target_median,
            "background_median": background_median,
            "target_minus_background": target_median - background_median,
        }
    return normalized


def _direction(value: float, *, tolerance: float = 1e-9) -> str:
    if value > tolerance:
        return "positive"
    if value < -tolerance:
        return "negative"
    return "zero"


def summarize_rows(rows: list[dict[str, Any]], *, image_date: str) -> dict[str, Any]:
    exact_date = _parse_iso_date(image_date, "image date").isoformat()
    normalized = sorted(
        (_normalize_row(row) for row in rows), key=lambda item: item["acquired_date"]
    )
    exact_rows = [row for row in normalized if row["acquired_date"] == exact_date]
    if not exact_rows:
        return {
            "status": "method_screen_not_ready_no_exact_date_acquisition",
            "exact_date_acquisition_count": 0,
            "usable_exact_date_acquisition_count": 0,
            "support_acquisition_count": len(normalized),
            "feature_count": len(FEATURE_NAMES),
            "signal_feature_count": len(SIGNAL_FEATURE_NAMES),
            "spatial_agreement_decision": "method_screen_inconclusive",
        }

    usable = [
        row
        for row in exact_rows
        if row["target_valid_pixels"] >= MIN_VALID_PIXELS
        and row["background_valid_pixels"] >= MIN_VALID_PIXELS
    ]
    if not usable:
        return {
            "status": "method_screen_not_ready_insufficient_valid_pixels",
            "exact_date_acquisition_count": len(exact_rows),
            "usable_exact_date_acquisition_count": 0,
            "support_acquisition_count": len(normalized),
            "feature_count": len(FEATURE_NAMES),
            "signal_feature_count": len(SIGNAL_FEATURE_NAMES),
            "spatial_agreement_decision": "method_screen_inconclusive",
        }

    exact_feature_summary: dict[str, Any] = {}
    exact_orbits = {row["relative_orbit"] for row in usable}
    support_rows = [
        row
        for row in normalized
        if row["acquired_date"] != exact_date
        and row["relative_orbit"] in exact_orbits
        and row["target_valid_pixels"] >= MIN_VALID_PIXELS
        and row["background_valid_pixels"] >= MIN_VALID_PIXELS
    ]

    stable_feature_count = 0
    for feature in FEATURE_NAMES:
        exact_deltas = [
            row["features"][feature]["target_minus_background"] for row in usable
        ]
        exact_delta = float(median(exact_deltas))
        exact_direction = _direction(exact_delta)
        support_deltas = [
            row["features"][feature]["target_minus_background"] for row in support_rows
        ]
        support_same_direction = [
            delta
            for delta in support_deltas
            if exact_direction != "zero" and _direction(delta) == exact_direction
        ]
        same_direction_fraction = (
            len(support_same_direction) / len(support_deltas) if support_deltas else None
        )
        stable = bool(
            exact_direction != "zero"
            and support_deltas
            and same_direction_fraction is not None
            and same_direction_fraction >= 2 / 3
        )
        if stable and feature in SIGNAL_FEATURE_NAMES:
            stable_feature_count += 1
        exact_feature_summary[feature] = {
            "exact_target_minus_background_median": exact_delta,
            "exact_direction": exact_direction,
            "support_same_orbit_count": len(support_deltas),
            "support_same_direction_fraction": same_direction_fraction,
            "stable_direction": stable,
        }

    if not support_rows:
        decision = "method_screen_inconclusive"
        status = "method_screen_complete_exact_date_only_no_same_orbit_support"
    elif stable_feature_count >= 2:
        decision = "spatial_agreement_supported"
        status = "method_screen_complete_spatial_comparison_only"
    else:
        decision = "spatial_agreement_not_supported"
        status = "method_screen_complete_spatial_comparison_only"

    return {
        "status": status,
        "exact_date_acquisition_count": len(exact_rows),
        "usable_exact_date_acquisition_count": len(usable),
        "support_acquisition_count": len(normalized),
        "same_orbit_support_count": len(support_rows),
        "feature_count": len(FEATURE_NAMES),
        "signal_feature_count": len(SIGNAL_FEATURE_NAMES),
        "stable_feature_count": stable_feature_count,
        "exact_feature_summary": exact_feature_summary,
        "spatial_agreement_decision": decision,
        "depth_measured": False,
        "calibration_record_created": False,
        "app_depth_enabled": False,
    }


def _geometry_to_ee(ee: Any, payload: dict[str, Any]) -> Any:
    if payload.get("type") == "FeatureCollection":
        return ee.FeatureCollection(payload).geometry()
    if payload.get("type") == "Feature":
        return ee.Geometry(payload["geometry"])
    return ee.Geometry(payload)


def _feature_image(ee: Any, processed: Any) -> Any:
    vv = processed.select("VV_dB").rename("vv_db")
    vh = processed.select("VH_dB").rename("vh_db")
    difference = vv.subtract(vh).rename("vv_minus_vh_db")
    ratio = (
        ee.Image(10)
        .pow(vh.subtract(vv).divide(10.0))
        .rename("vh_to_vv_linear_ratio")
    )
    incidence = processed.select("angle").rename("incidence_angle")
    return ee.Image.cat([vv, vh, difference, ratio, incidence])


def _region_summary(ee: Any, image: Any, geometry: Any, scale: int) -> dict[str, Any]:
    reducer = ee.Reducer.median().combine(ee.Reducer.count(), sharedInputs=True)
    values = (
        image.reduceRegion(
            reducer=reducer,
            geometry=geometry,
            scale=scale,
            bestEffort=False,
            maxPixels=1_000_000,
            tileScale=4,
        ).getInfo()
        or {}
    )
    output: dict[str, Any] = {"features": {}, "valid_pixels": None}
    counts = []
    for feature in FEATURE_NAMES:
        median_key = f"{feature}_median"
        count_key = f"{feature}_count"
        if values.get(median_key) is None or values.get(count_key) is None:
            raise ButoMethodScreenError(
                "Earth Engine returned an incomplete regional summary"
            )
        output["features"][feature] = float(values[median_key])
        counts.append(int(values[count_key]))
    output["valid_pixels"] = min(counts) if counts else 0
    return output


def query_s1_region_summaries(
    *,
    target_geometry_payload: dict[str, Any],
    background_geometry_payload: dict[str, Any],
    image_date: str,
    support_days: int,
    analysis_scale_meters: int,
) -> list[dict[str, Any]]:
    plan = build_query_plan(
        image_date=image_date,
        support_days=support_days,
        analysis_scale_meters=analysis_scale_meters,
    )
    try:
        import ee

        from app.config import get_settings
        from app.pipeline.stages.sar_rtc import per_image_products_db
        from app.services.ee_session import initialize_ee_session

        initialize_ee_session(get_settings())
        target = _geometry_to_ee(ee, target_geometry_payload)
        background = _geometry_to_ee(ee, background_geometry_payload)
        region = target.union(background, maxError=1)
        collection = (
            ee.ImageCollection(S1_COLLECTION_ID)
            .filterBounds(region)
            .filterDate(plan["support_start"], plan["support_end_exclusive"])
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.eq("resolution_meters", 10))
            .filter(
                ee.Filter.listContains("transmitterReceiverPolarisation", "VV")
            )
            .filter(
                ee.Filter.listContains("transmitterReceiverPolarisation", "VH")
            )
            .select(["VV", "VH", "angle"])
            .sort("system:time_start")
        )
        count = int(collection.size().getInfo())
        image_list = collection.toList(count)
        rows: list[dict[str, Any]] = []
        for index in range(count):
            source = ee.Image(image_list.get(index))
            processed = per_image_products_db(source)
            features = _feature_image(ee, processed)
            target_summary = _region_summary(
                ee, features, target, analysis_scale_meters
            )
            background_summary = _region_summary(
                ee, features, background, analysis_scale_meters
            )
            timestamp_ms = int(source.get("system:time_start").getInfo())
            acquired = datetime.fromtimestamp(
                timestamp_ms / 1000.0, tz=timezone.utc
            ).date().isoformat()
            row_features = {
                feature: {
                    "target_median": target_summary["features"][feature],
                    "background_median": background_summary["features"][feature],
                }
                for feature in FEATURE_NAMES
            }
            rows.append(
                {
                    "acquired_date": acquired,
                    "orbit_pass": source.get("orbitProperties_pass").getInfo(),
                    "relative_orbit": source.get(
                        "relativeOrbitNumber_start"
                    ).getInfo(),
                    "platform": source.get("platform_number").getInfo(),
                    "target_valid_pixels": target_summary["valid_pixels"],
                    "background_valid_pixels": background_summary["valid_pixels"],
                    "features": row_features,
                }
            )
        return rows
    except ButoMethodScreenError:
        raise
    except Exception as exc:
        raise ButoMethodScreenError("Earth Engine Buto method query failed") from exc


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)
    except OSError as exc:
        raise ButoMethodScreenError("method-screen output could not be written") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def run_method_screen(
    *,
    target_geojson: Path,
    background_geojson: Path,
    image_date: str = DEFAULT_IMAGE_DATE,
    support_days: int = DEFAULT_SUPPORT_DAYS,
    analysis_scale_meters: int = DEFAULT_ANALYSIS_SCALE_METERS,
    execute: bool = False,
    output_path: Path | None = None,
    query_fn: Callable[..., list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    target = load_local_geometry(target_geojson, "target geometry")
    background = load_local_geometry(background_geojson, "background geometry")
    if target == background:
        raise ButoMethodScreenError("target and background geometries must be different")
    plan = build_query_plan(
        image_date=image_date,
        support_days=support_days,
        analysis_scale_meters=analysis_scale_meters,
    )
    result: dict[str, Any] = {
        "status": "method_screen_dry_run_ready",
        "query_executed": False,
        **plan,
        "target_geometry_loaded": True,
        "background_geometry_loaded": True,
        "comparison_area_is_confirmed_negative": False,
        "coordinates_printed": False,
        "image_ids_printed": False,
        "private_paths_printed": False,
        "depth_measured": False,
        "training_started": False,
        "calibration_record_created": False,
        "app_depth_enabled": False,
        "output_written": False,
    }
    if execute:
        active_query = query_fn or query_s1_region_summaries
        rows = active_query(
            target_geometry_payload=target,
            background_geometry_payload=background,
            image_date=image_date,
            support_days=support_days,
            analysis_scale_meters=analysis_scale_meters,
        )
        result.update(summarize_rows(rows, image_date=image_date))
        result["query_executed"] = True
    if output_path is not None:
        _require_outside_repo(output_path, "method-screen output")
        result["output_written"] = True
        _atomic_write_json(Path(output_path), result)
    return result


def redacted_console_summary(result: dict[str, Any]) -> dict[str, Any]:
    safe_keys = (
        "status",
        "query_executed",
        "image_date",
        "support_days",
        "analysis_scale_meters",
        "exact_date_acquisition_count",
        "usable_exact_date_acquisition_count",
        "support_acquisition_count",
        "same_orbit_support_count",
        "feature_count",
        "signal_feature_count",
        "stable_feature_count",
        "spatial_agreement_decision",
        "comparison_area_is_confirmed_negative",
        "coordinates_printed",
        "image_ids_printed",
        "private_paths_printed",
        "depth_measured",
        "training_started",
        "calibration_record_created",
        "app_depth_enabled",
        "output_written",
    )
    return {key: result[key] for key in safe_keys if key in result}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the bounded Buto Sentinel-1 spatial method screen."
    )
    parser.add_argument("--target-geojson", type=Path, required=True)
    parser.add_argument("--background-geojson", type=Path, required=True)
    parser.add_argument("--image-date", default=DEFAULT_IMAGE_DATE)
    parser.add_argument("--support-days", type=int, default=DEFAULT_SUPPORT_DAYS)
    parser.add_argument(
        "--analysis-scale-meters", type=int, default=DEFAULT_ANALYSIS_SCALE_METERS
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Query Earth Engine. Without this flag, validate only.",
    )
    parser.add_argument("--output", type=Path, help="Detailed JSON output path outside Git.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_method_screen(
            target_geojson=args.target_geojson,
            background_geojson=args.background_geojson,
            image_date=args.image_date,
            support_days=args.support_days,
            analysis_scale_meters=args.analysis_scale_meters,
            execute=args.execute,
            output_path=args.output,
        )
    except ButoMethodScreenError as exc:
        print(
            json.dumps(
                {
                    "status": "method_screen_failed",
                    "error": str(exc),
                    "coordinates_printed": False,
                    "image_ids_printed": False,
                    "private_paths_printed": False,
                    "depth_measured": False,
                    "app_depth_enabled": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(redacted_console_summary(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
