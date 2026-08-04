"""Audit land-cover context for one finalized ICESat-2 candidate.

This read-only research tool uses Earth Engine to inspect annual USDA NASS
Cropland Data Layer classes and Dynamic World class probabilities around the
candidate's supporting ATL08 footprint.  It is a context gate only: it does not
create a depth anchor, start permit/as-built records research, invoke the radar
engine, or modify app artifacts.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEFAULT_DOSSIER = Path(
    "./data/research/icesat2_broad_track_scan/"
    "southwest_us_earthwork_pilot_v3_imperial_valley/"
    "candidate_009_dossier.json"
)
SCHEMA = "icesat2_candidate_gee_context_audit_v1"
CDL_COLLECTION = "USDA/NASS/CDL"
DYNAMIC_WORLD_COLLECTION = "GOOGLE/DYNAMICWORLD/V1"
DYNAMIC_WORLD_BANDS = (
    "water",
    "trees",
    "grass",
    "flooded_vegetation",
    "crops",
    "shrub_and_scrub",
    "built",
    "bare",
    "snow_and_ice",
)


def _load_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read candidate dossier: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("candidate dossier must be a JSON object")
    return payload


def _number(value: object) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _candidate_summary(dossier: dict[str, Any]) -> dict[str, Any]:
    value = dossier.get("candidate_summary")
    return dict(value) if isinstance(value, dict) else {}


def _candidate_coordinates(dossier: dict[str, Any]) -> list[tuple[float, float]]:
    values = dossier.get("segments")
    coordinates: list[tuple[float, float]] = []
    if isinstance(values, list):
        for raw in values:
            if not isinstance(raw, dict):
                continue
            longitude = _number(raw.get("longitude"))
            latitude = _number(raw.get("latitude"))
            if longitude is None or latitude is None:
                continue
            coordinates.append((longitude, latitude))
    if coordinates:
        coordinates.sort(key=lambda item: (item[1], item[0]))
        return coordinates

    summary = _candidate_summary(dossier)
    longitude = _number(summary.get("longitude"))
    latitude = _number(summary.get("latitude"))
    if longitude is None or latitude is None:
        raise ValueError("candidate dossier has no usable coordinates")
    return [(longitude, latitude)]


def _class_name_map(values: object, names: object) -> dict[int, str]:
    if not isinstance(values, list) or not isinstance(names, list):
        return {}
    result: dict[int, str] = {}
    for raw_value, raw_name in zip(values, names, strict=False):
        try:
            key = int(raw_value)
        except (TypeError, ValueError):
            continue
        if isinstance(raw_name, str):
            result[key] = raw_name
    return result


def _named_histogram(
    histogram: object,
    names: dict[int, str],
    *,
    limit: int = 8,
) -> list[dict[str, object]]:
    if not isinstance(histogram, dict):
        return []
    rows: list[dict[str, object]] = []
    total = 0.0
    for raw_count in histogram.values():
        count = _number(raw_count)
        if count is not None and count > 0:
            total += count
    for raw_value, raw_count in histogram.items():
        count = _number(raw_count)
        if count is None or count <= 0:
            continue
        try:
            value = int(float(str(raw_value)))
        except ValueError:
            continue
        rows.append(
            {
                "value": value,
                "name": names.get(value, f"class_{value}"),
                "pixel_count": count,
                "fraction": count / total if total > 0 else None,
            }
        )
    rows.sort(key=lambda item: float(item["pixel_count"]), reverse=True)
    return rows[:limit]


def _cultivated_fraction(rows: Iterable[dict[str, object]]) -> float | None:
    values = list(rows)
    fractions = [
        float(item["fraction"])
        for item in values
        if isinstance(item.get("fraction"), (int, float))
        and "cultivated" in str(item.get("name", "")).lower()
        and "non-cultivated" not in str(item.get("name", "")).lower()
    ]
    if not values:
        return None
    return sum(fractions)


def _probability(window: dict[str, Any], band: str) -> float | None:
    values = window.get("mean_probabilities")
    if not isinstance(values, dict):
        return None
    return _number(values.get(band))


def build_context_decision(
    dossier: dict[str, Any],
    *,
    cdl_years: list[dict[str, Any]],
    dynamic_world_windows: list[dict[str, Any]],
    cultivated_fraction_threshold: float = 0.50,
    dynamic_world_probability_threshold: float = 0.35,
) -> dict[str, Any]:
    if not 0.0 <= cultivated_fraction_threshold <= 1.0:
        raise ValueError("cultivated_fraction_threshold must be between 0 and 1")
    if not 0.0 <= dynamic_world_probability_threshold <= 1.0:
        raise ValueError(
            "dynamic_world_probability_threshold must be between 0 and 1"
        )

    cultivated_years: list[int] = []
    point_crop_names: list[str] = []
    for row in cdl_years:
        year = row.get("year")
        point_cultivated = str(row.get("point_cultivated_name") or "")
        buffer_fraction = _number(row.get("buffer_cultivated_fraction"))
        point_crop = row.get("point_cropland_name")
        if isinstance(point_crop, str) and point_crop:
            point_crop_names.append(point_crop)
        is_cultivated = (
            "cultivated" in point_cultivated.lower()
            and "non-cultivated" not in point_cultivated.lower()
        ) or (
            buffer_fraction is not None
            and buffer_fraction >= cultivated_fraction_threshold
        )
        if is_cultivated and isinstance(year, int):
            cultivated_years.append(year)

    crop_probabilities = [
        value
        for value in (
            _probability(window, "crops") for window in dynamic_world_windows
        )
        if value is not None
    ]
    built_probabilities = [
        value
        for value in (
            _probability(window, "built") for window in dynamic_world_windows
        )
        if value is not None
    ]
    bare_probabilities = [
        value
        for value in (
            _probability(window, "bare") for window in dynamic_world_windows
        )
        if value is not None
    ]

    max_crop_probability = max(crop_probabilities, default=None)
    max_built_probability = max(built_probabilities, default=None)
    max_bare_probability = max(bare_probabilities, default=None)

    agricultural_context = bool(cultivated_years) or (
        max_crop_probability is not None
        and max_crop_probability >= dynamic_world_probability_threshold
    )
    built_context = (
        max_built_probability is not None
        and max_built_probability >= dynamic_world_probability_threshold
    )
    bare_context = (
        max_bare_probability is not None
        and max_bare_probability >= dynamic_world_probability_threshold
    )

    if agricultural_context and built_context:
        status = "mixed_agricultural_built_context"
    elif agricultural_context:
        status = "agricultural_context_detected"
    elif built_context:
        status = "engineered_or_built_context_possible"
    elif bare_context:
        status = "bare_ground_context_detected"
    else:
        status = "context_inconclusive"

    summary = _candidate_summary(dossier)
    return {
        "schema": SCHEMA,
        "status": status,
        "candidate_id": dossier.get("candidate_id"),
        "campaign_id": dossier.get("campaign_id", summary.get("campaign_id")),
        "campaign_rank": dossier.get("campaign_rank", summary.get("campaign_rank")),
        "longitude": summary.get("longitude"),
        "latitude": summary.get("latitude"),
        "median_step_m": summary.get("median_step_m"),
        "segment_count": dossier.get("segment_count", summary.get("segment_count")),
        "event_start": summary.get("event_start"),
        "event_end": summary.get("event_end"),
        "cdl_years": cdl_years,
        "dynamic_world_windows": dynamic_world_windows,
        "context_indicators": {
            "agricultural_context_detected": agricultural_context,
            "built_context_detected": built_context,
            "bare_ground_context_detected": bare_context,
            "cultivated_years": sorted(set(cultivated_years)),
            "point_cropland_names": sorted(set(point_crop_names)),
            "maximum_dynamic_world_crop_probability": max_crop_probability,
            "maximum_dynamic_world_built_probability": max_built_probability,
            "maximum_dynamic_world_bare_probability": max_bare_probability,
        },
        "audit_parameters": {
            "cultivated_fraction_threshold": cultivated_fraction_threshold,
            "dynamic_world_probability_threshold": (
                dynamic_world_probability_threshold
            ),
        },
        "decision": {
            "manual_imagery_and_parcel_review_recommended": True,
            "records_research_recommended": False,
            "candidate_is_depth_anchor": False,
            "candidate_is_placed_thickness_measurement": False,
        },
        "interpretation": {
            "agricultural_context_means": (
                "annual crop/cultivated mapping or Dynamic World crop "
                "probability overlaps the ATL08 footprint"
            ),
            "built_context_means": (
                "Dynamic World built probability is high enough to justify "
                "manual project-footprint review"
            ),
            "context_gate_only": True,
            "cause_confirmed": False,
            "placed_thickness_confirmed": False,
        },
        "does_not_prove": [
            "the apparent rise was caused by farming",
            "the apparent rise was caused by construction",
            "an official placed-material thickness",
            "depth to a buried object",
            "radar transferability",
        ],
    }


def _initialize_earth_engine(project: str | None):
    try:
        import ee
    except ImportError as exc:
        raise RuntimeError(
            'missing dependency "earthengine-api"; install the project dependencies'
        ) from exc

    from app.config import get_settings

    settings = get_settings()
    credentials = None
    if settings.ee_service_account_email and settings.ee_service_account_key_path:
        credentials = ee.ServiceAccountCredentials(
            settings.ee_service_account_email,
            str(settings.ee_service_account_key_path),
        )
    kwargs: dict[str, object] = {}
    if project:
        kwargs["project"] = project
    if credentials is not None:
        ee.Initialize(credentials, **kwargs)
    else:
        ee.Initialize(**kwargs)
    return ee


def _query_cdl_year(ee, *, geometry, point, year: int) -> dict[str, Any]:
    collection = ee.ImageCollection(CDL_COLLECTION).filterDate(
        f"{year}-01-01", f"{year + 1}-01-01"
    )
    count = int(collection.size().getInfo() or 0)
    if count <= 0:
        return {"year": year, "status": "cdl_year_unavailable"}
    image = ee.Image(collection.first())
    properties = image.toDictionary(
        [
            "cropland_class_values",
            "cropland_class_names",
            "cultivated_class_values",
            "cultivated_class_names",
        ]
    ).getInfo()
    properties = properties if isinstance(properties, dict) else {}
    cropland_names = _class_name_map(
        properties.get("cropland_class_values"),
        properties.get("cropland_class_names"),
    )
    cultivated_names = _class_name_map(
        properties.get("cultivated_class_values"),
        properties.get("cultivated_class_names"),
    )

    point_values = image.select(["cropland", "cultivated"]).reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=point,
        scale=30,
        bestEffort=True,
        maxPixels=1_000_000,
    ).getInfo()
    point_values = point_values if isinstance(point_values, dict) else {}
    point_crop_value = point_values.get("cropland")
    point_cultivated_value = point_values.get("cultivated")
    point_crop_key = (
        int(point_crop_value)
        if isinstance(point_crop_value, (int, float))
        else None
    )
    point_cultivated_key = (
        int(point_cultivated_value)
        if isinstance(point_cultivated_value, (int, float))
        else None
    )

    histograms = image.select(["cropland", "cultivated"]).reduceRegion(
        reducer=ee.Reducer.frequencyHistogram(),
        geometry=geometry,
        scale=30,
        bestEffort=True,
        maxPixels=2_000_000,
    ).getInfo()
    histograms = histograms if isinstance(histograms, dict) else {}
    crop_rows = _named_histogram(histograms.get("cropland"), cropland_names)
    cultivated_rows = _named_histogram(
        histograms.get("cultivated"), cultivated_names
    )
    return {
        "year": year,
        "status": "cdl_context_available",
        "source_collection": CDL_COLLECTION,
        "point_cropland_value": point_crop_key,
        "point_cropland_name": (
            cropland_names.get(point_crop_key) if point_crop_key is not None else None
        ),
        "point_cultivated_value": point_cultivated_key,
        "point_cultivated_name": (
            cultivated_names.get(point_cultivated_key)
            if point_cultivated_key is not None
            else None
        ),
        "buffer_top_cropland_classes": crop_rows,
        "buffer_cultivated_classes": cultivated_rows,
        "buffer_cultivated_fraction": _cultivated_fraction(cultivated_rows),
    }


def _dynamic_world_windows(dossier: dict[str, Any]) -> list[dict[str, str]]:
    summary = _candidate_summary(dossier)
    event_start = _parse_time(summary.get("event_start"))
    event_end = _parse_time(summary.get("event_end"))
    if event_start is None or event_end is None or event_end <= event_start:
        raise ValueError("candidate dossier has an invalid event window")
    return [
        {
            "window_id": "pre_event_year",
            "start": (event_start - timedelta(days=365)).date().isoformat(),
            "end": event_start.date().isoformat(),
        },
        {
            "window_id": "event_window",
            "start": event_start.date().isoformat(),
            "end": event_end.date().isoformat(),
        },
        {
            "window_id": "post_event_year",
            "start": event_end.date().isoformat(),
            "end": (event_end + timedelta(days=365)).date().isoformat(),
        },
    ]


def _query_dynamic_world_window(
    ee,
    *,
    geometry,
    window_id: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    collection = (
        ee.ImageCollection(DYNAMIC_WORLD_COLLECTION)
        .filterBounds(geometry)
        .filterDate(start, end)
    )
    count = int(collection.size().getInfo() or 0)
    if count <= 0:
        return {
            "window_id": window_id,
            "start": start,
            "end": end,
            "status": "dynamic_world_window_unavailable",
            "image_count": 0,
        }
    image = collection.select(list(DYNAMIC_WORLD_BANDS)).median()
    values = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=10,
        bestEffort=True,
        maxPixels=2_000_000,
    ).getInfo()
    values = values if isinstance(values, dict) else {}
    probabilities = {
        band: _number(values.get(band)) for band in DYNAMIC_WORLD_BANDS
    }
    finite = {
        name: value for name, value in probabilities.items() if value is not None
    }
    top_class = max(finite, key=finite.get) if finite else None
    return {
        "window_id": window_id,
        "start": start,
        "end": end,
        "status": "dynamic_world_context_available",
        "source_collection": DYNAMIC_WORLD_COLLECTION,
        "image_count": count,
        "mean_probabilities": probabilities,
        "top_probability_class": top_class,
        "top_probability": finite.get(top_class) if top_class else None,
    }


def _geojson(dossier: dict[str, Any], *, buffer_m: float) -> dict[str, Any]:
    coordinates = _candidate_coordinates(dossier)
    geometry_type = "LineString" if len(coordinates) > 1 else "Point"
    geometry_coordinates: object = coordinates if len(coordinates) > 1 else coordinates[0]
    summary = _candidate_summary(dossier)
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": geometry_type,
                    "coordinates": geometry_coordinates,
                },
                "properties": {
                    "candidate_id": dossier.get("candidate_id"),
                    "campaign_rank": dossier.get(
                        "campaign_rank", summary.get("campaign_rank")
                    ),
                    "median_step_m": summary.get("median_step_m"),
                    "segment_count": dossier.get(
                        "segment_count", summary.get("segment_count")
                    ),
                    "context_buffer_m": buffer_m,
                    "candidate_is_depth_anchor": False,
                },
            }
        ],
    }


def run_audit(
    dossier: dict[str, Any],
    *,
    project: str | None,
    buffer_m: float,
) -> dict[str, Any]:
    if buffer_m <= 0:
        raise ValueError("buffer_m must be positive")
    ee = _initialize_earth_engine(project)
    coordinates = _candidate_coordinates(dossier)
    point = ee.Geometry.Point(list(coordinates[len(coordinates) // 2]))
    if len(coordinates) > 1:
        geometry = ee.Geometry.LineString([list(item) for item in coordinates]).buffer(
            buffer_m
        )
    else:
        geometry = point.buffer(buffer_m)

    summary = _candidate_summary(dossier)
    event_start = _parse_time(summary.get("event_start"))
    event_end = _parse_time(summary.get("event_end"))
    if event_start is None or event_end is None:
        raise ValueError("candidate dossier has no valid event dates")
    years = sorted({event_start.year, event_end.year})
    cdl_years = [
        _query_cdl_year(ee, geometry=geometry, point=point, year=year)
        for year in years
    ]
    dynamic_world = [
        _query_dynamic_world_window(ee, geometry=geometry, **window)
        for window in _dynamic_world_windows(dossier)
    ]
    result = build_context_decision(
        dossier,
        cdl_years=cdl_years,
        dynamic_world_windows=dynamic_world,
    )
    result["context_geometry"] = {
        "type": "buffered_atl08_support_line",
        "buffer_m": buffer_m,
        "coordinate_count": len(coordinates),
    }
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Earth Engine land-cover context for one candidate."
    )
    parser.add_argument("--dossier", type=Path, default=DEFAULT_DOSSIER)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-geojson", type=Path, default=None)
    parser.add_argument("--buffer-m", type=float, default=60.0)
    parser.add_argument("--ee-project", type=str, default=None)
    return parser


def main() -> int:
    args = _parser().parse_args()
    output_json = args.output_json or args.dossier.with_name(
        args.dossier.stem.replace("_dossier", "_gee_context_audit") + ".json"
    )
    output_geojson = args.output_geojson or args.dossier.with_name(
        args.dossier.stem.replace("_dossier", "_gee_context_audit") + ".geojson"
    )
    try:
        dossier = _load_object(args.dossier)
        result = run_audit(
            dossier,
            project=args.ee_project,
            buffer_m=args.buffer_m,
        )
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        output_geojson.write_text(
            json.dumps(_geojson(dossier, buffer_m=args.buffer_m), indent=2)
            + "\n",
            encoding="utf-8",
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "gee_context_audit_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
