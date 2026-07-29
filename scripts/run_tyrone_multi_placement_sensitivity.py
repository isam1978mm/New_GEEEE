#!/usr/bin/env python3
"""Run the preregistered Tyrone multi-placement Sentinel-1 ordering screen.

This is an isolated local method screen. It does not train a model, create a
calibration row, modify app outputs, or use classifier/anomaly layers.
"""
from __future__ import annotations

import csv
import json
import math
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

OUT_DIR = Path("artifacts/tyrone_multi_placement_sensitivity")
OUT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_JSON = OUT_DIR / "tyrone_sensitivity_result.json"
PLACEMENT_CSV = OUT_DIR / "placement_summary.csv"
MONTHLY_CSV = OUT_DIR / "monthly_differences.csv"

START_DATE = "2018-01-01"
END_DATE = "2024-01-01"
MIN_USABLE_MONTHS = 24
MIN_VALID_PIXELS = 20
MAX_INCIDENCE_DIFFERENCE_DEG = 0.5
PLACEMENT_DOMINANT_FRACTION = 0.70
SEASON_DOMINANT_FRACTION = 0.60
MIN_MONTHS_PER_SEASON = 4
MIN_PASSING_PLACEMENTS = 29
EDGE_BUFFER_M = 20
FIXED_SCALE_RATIO = 0.20202020202020202

# Manually digitized from the official rendered 2006 drawing. Areas are
# approximately 4.04 and 4.50 acres at the official drawing scale.
TP5_SOURCE_PIXELS = [(503, 124), (619, 176), (565, 303), (379, 219)]
TP6_SOURCE_PIXELS = [(380, 219), (565, 302), (520, 416), (341, 350)]

# Best placement plus the eight boundary/midpoint samples of the tight local
# registration basin. Values are 2020 rendered-map pixels.
TRANSLATIONS = [
    (484, 504),
    (481, 477),
    (493, 477),
    (505, 477),
    (481, 492),
    (505, 492),
    (481, 507),
    (493, 507),
    (505, 507),
]

# Image-pixel to UTM 12N similarity transforms.
# E = a*x + b*y + c
# N = -a*y + b*x + d
GROUND_TRANSFORMS = {
    "fit_no3_no3x_no2": (4.33924854, 0.00252438686, 739016.720, 3626308.84),
    "fit_no3_no3x": (4.34302329, 0.290343884, 738876.050, 3626159.74),
    "fit_no3x_no2": (4.33565097, -0.479943504, 739428.483, 3626736.01),
    "fit_no3_no2": (4.33849550, -0.0209035338, 738999.437, 3626292.04),
}

SEASONS = {
    12: "DJF",
    1: "DJF",
    2: "DJF",
    3: "MAM",
    4: "MAM",
    5: "MAM",
    6: "JJA",
    7: "JJA",
    8: "JJA",
    9: "SON",
    10: "SON",
    11: "SON",
}


@dataclass(frozen=True)
class PlacementSummary:
    hypothesis_id: str
    transform_id: str
    translation_x: int
    translation_y: int
    usable_months: int
    positive_months: int
    negative_months: int
    zero_months: int
    dominant_sign: str | None
    dominant_fraction: float | None
    season_support: dict[str, dict[str, Any]]
    passed: bool
    failure_reasons: tuple[str, ...]


def write_json(payload: dict[str, Any]) -> None:
    RESULT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


def first_nonempty(names: Iterable[str]) -> tuple[str | None, str | None]:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return name, value
    return None, None


def initialize_earth_engine(ee: Any) -> tuple[str, str | None, list[Path]]:
    project_name, project_value = first_nonempty(
        ["EE_PROJECT", "GEE_PROJECT", "GOOGLE_CLOUD_PROJECT"]
    )
    service_name, service_json = first_nonempty(
        [
            "EE_SERVICE_ACCOUNT_JSON",
            "GEE_SERVICE_ACCOUNT_JSON",
            "GOOGLE_SERVICE_ACCOUNT_JSON",
        ]
    )
    token_name, token_json = first_nonempty(
        ["EARTHENGINE_TOKEN", "EE_CREDENTIALS_JSON", "GEE_CREDENTIALS_JSON"]
    )
    cleanup: list[Path] = []

    if service_json:
        parsed = json.loads(service_json)
        client_email = parsed.get("client_email")
        private_key = parsed.get("private_key")
        if not client_email or not private_key:
            raise ValueError("service-account JSON is missing client_email or private_key")
        key_path = OUT_DIR / "service-account.json"
        key_path.write_text(json.dumps(parsed), encoding="utf-8")
        os.chmod(key_path, 0o600)
        cleanup.append(key_path)
        credentials = ee.ServiceAccountCredentials(client_email, str(key_path))
        ee.Initialize(credentials=credentials, project=project_value or parsed.get("project_id"))
        return service_name or "service_account", project_name, cleanup

    if token_json:
        parsed = json.loads(token_json)
        config_dir = Path.home() / ".config" / "earthengine"
        config_dir.mkdir(parents=True, exist_ok=True)
        credentials_path = config_dir / "credentials"
        credentials_path.write_text(json.dumps(parsed), encoding="utf-8")
        os.chmod(credentials_path, 0o600)
        cleanup.append(credentials_path)
        ee.Initialize(project=project_value)
        return token_name or "earth_engine_token", project_name, cleanup

    ee.Initialize(project=project_value)
    return "runner_default_credentials", project_name, cleanup


def source_to_map_pixel(point: tuple[float, float], tx: int, ty: int) -> tuple[float, float]:
    # outer06.png is an exact crop beginning at full-page pixel (1000, 600).
    # The 2006 comparison crop begins at full-page pixel (100, 30).
    x, y = point
    return (
        FIXED_SCALE_RATIO * (x + 900.0) + tx,
        FIXED_SCALE_RATIO * (y + 570.0) + ty,
    )


def map_pixel_to_utm(
    point: tuple[float, float], transform: tuple[float, float, float, float]
) -> tuple[float, float]:
    x, y = point
    a, b, c, d = transform
    return a * x + b * y + c, -a * y + b * x + d


def build_hypotheses() -> list[dict[str, Any]]:
    from pyproj import Transformer

    to_wgs84 = Transformer.from_crs("EPSG:32612", "EPSG:4326", always_xy=True)
    rows: list[dict[str, Any]] = []
    for transform_id, transform in GROUND_TRANSFORMS.items():
        for translation_index, (tx, ty) in enumerate(TRANSLATIONS, start=1):
            hypothesis_id = f"{transform_id}__shift_{translation_index:02d}"
            polygons: dict[str, list[list[float]]] = {}
            for zone_id, source_points in {
                "tp5": TP5_SOURCE_PIXELS,
                "tp6": TP6_SOURCE_PIXELS,
            }.items():
                coordinates: list[list[float]] = []
                for point in source_points:
                    map_point = source_to_map_pixel(point, tx, ty)
                    easting, northing = map_pixel_to_utm(map_point, transform)
                    lon, lat = to_wgs84.transform(easting, northing)
                    coordinates.append([float(lon), float(lat)])
                coordinates.append(coordinates[0])
                polygons[zone_id] = coordinates
            rows.append(
                {
                    "hypothesis_id": hypothesis_id,
                    "transform_id": transform_id,
                    "translation_index": translation_index,
                    "translation_x": tx,
                    "translation_y": ty,
                    "polygons": polygons,
                }
            )
    if len(rows) != 36:
        raise RuntimeError(f"expected 36 geometry hypotheses, found {len(rows)}")
    return rows


def select_orbit_group(metadata: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in metadata:
        orbit_pass = str(row.get("orbit_pass") or "")
        relative_orbit = row.get("relative_orbit")
        timestamp = row.get("timestamp")
        if not orbit_pass or relative_orbit is None or timestamp is None:
            continue
        grouped[(orbit_pass, int(relative_orbit))].append(row)
    if not grouped:
        raise RuntimeError("no Sentinel-1 orbit/pass groups were available")

    ranked = []
    for (orbit_pass, relative_orbit), rows in grouped.items():
        months = {
            datetime.fromtimestamp(float(row["timestamp"]) / 1000.0, tz=timezone.utc).strftime("%Y-%m")
            for row in rows
        }
        ranked.append(
            {
                "orbit_pass": orbit_pass,
                "relative_orbit": relative_orbit,
                "distinct_months": len(months),
                "acquisition_count": len(rows),
            }
        )
    ranked.sort(
        key=lambda row: (
            -int(row["distinct_months"]),
            -int(row["acquisition_count"]),
            str(row["orbit_pass"]),
            int(row["relative_orbit"]),
        )
    )
    return {**ranked[0], "ranking": ranked}


def month_sequence(start: str, end: str) -> list[str]:
    start_dt = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    end_dt = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
    months: list[str] = []
    year, month = start_dt.year, start_dt.month
    while (year, month) < (end_dt.year, end_dt.month):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return months


def sign_of(value: float, epsilon: float = 1e-9) -> str:
    if value > epsilon:
        return "positive"
    if value < -epsilon:
        return "negative"
    return "zero"


def summarize_placement(hypothesis: dict[str, Any], rows: list[dict[str, Any]]) -> PlacementSummary:
    signs = [row["sign"] for row in rows]
    counts = Counter(signs)
    positive = int(counts.get("positive", 0))
    negative = int(counts.get("negative", 0))
    zero = int(counts.get("zero", 0))
    nonzero = positive + negative
    if nonzero == 0:
        dominant_sign = None
        dominant_fraction = None
    elif positive >= negative:
        dominant_sign = "positive"
        dominant_fraction = positive / nonzero
    else:
        dominant_sign = "negative"
        dominant_fraction = negative / nonzero

    season_support: dict[str, dict[str, Any]] = {}
    for season in ("DJF", "MAM", "JJA", "SON"):
        season_rows = [row for row in rows if row["season"] == season]
        season_nonzero = [row for row in season_rows if row["sign"] != "zero"]
        if dominant_sign and season_nonzero:
            supporting = sum(row["sign"] == dominant_sign for row in season_nonzero)
            fraction = supporting / len(season_nonzero)
        else:
            supporting = 0
            fraction = None
        season_support[season] = {
            "usable_months": len(season_rows),
            "nonzero_months": len(season_nonzero),
            "supporting_months": supporting,
            "dominant_sign_fraction": fraction,
        }

    failures: list[str] = []
    if len(rows) < MIN_USABLE_MONTHS:
        failures.append("usable_months_below_24")
    if dominant_sign is None or dominant_fraction is None:
        failures.append("no_nonzero_dominant_sign")
    elif dominant_fraction < PLACEMENT_DOMINANT_FRACTION:
        failures.append("dominant_sign_fraction_below_0_70")
    for season, support in season_support.items():
        if int(support["usable_months"]) < MIN_MONTHS_PER_SEASON:
            failures.append(f"{season.lower()}_usable_months_below_4")
        fraction = support["dominant_sign_fraction"]
        if fraction is None or float(fraction) < SEASON_DOMINANT_FRACTION:
            failures.append(f"{season.lower()}_sign_fraction_below_0_60")

    return PlacementSummary(
        hypothesis_id=str(hypothesis["hypothesis_id"]),
        transform_id=str(hypothesis["transform_id"]),
        translation_x=int(hypothesis["translation_x"]),
        translation_y=int(hypothesis["translation_y"]),
        usable_months=len(rows),
        positive_months=positive,
        negative_months=negative,
        zero_months=zero,
        dominant_sign=dominant_sign,
        dominant_fraction=dominant_fraction,
        season_support=season_support,
        passed=not failures,
        failure_reasons=tuple(failures),
    )


def write_csvs(monthly_rows: list[dict[str, Any]], summaries: list[PlacementSummary]) -> None:
    monthly_fields = [
        "hypothesis_id",
        "month",
        "season",
        "tp5_log_ratio_db",
        "tp6_log_ratio_db",
        "difference_tp6_minus_tp5",
        "sign",
        "tp5_vv_db",
        "tp6_vv_db",
        "tp5_vh_db",
        "tp6_vh_db",
        "tp5_angle_deg",
        "tp6_angle_deg",
        "incidence_difference_deg",
        "tp5_valid_pixels",
        "tp6_valid_pixels",
    ]
    with MONTHLY_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=monthly_fields)
        writer.writeheader()
        for row in monthly_rows:
            writer.writerow({key: row.get(key) for key in monthly_fields})

    placement_fields = [
        "hypothesis_id",
        "transform_id",
        "translation_x",
        "translation_y",
        "usable_months",
        "positive_months",
        "negative_months",
        "zero_months",
        "dominant_sign",
        "dominant_fraction",
        "passed",
        "failure_reasons",
        "season_support_json",
    ]
    with PLACEMENT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=placement_fields)
        writer.writeheader()
        for summary in summaries:
            writer.writerow(
                {
                    "hypothesis_id": summary.hypothesis_id,
                    "transform_id": summary.transform_id,
                    "translation_x": summary.translation_x,
                    "translation_y": summary.translation_y,
                    "usable_months": summary.usable_months,
                    "positive_months": summary.positive_months,
                    "negative_months": summary.negative_months,
                    "zero_months": summary.zero_months,
                    "dominant_sign": summary.dominant_sign or "",
                    "dominant_fraction": "" if summary.dominant_fraction is None else summary.dominant_fraction,
                    "passed": summary.passed,
                    "failure_reasons": "|".join(summary.failure_reasons),
                    "season_support_json": json.dumps(summary.season_support, sort_keys=True),
                }
            )


def run_query(ee: Any, hypotheses: list[dict[str, Any]]) -> dict[str, Any]:
    features = []
    for hypothesis in hypotheses:
        for zone_id in ("tp5", "tp6"):
            geometry = ee.Geometry.Polygon(hypothesis["polygons"][zone_id], proj="EPSG:4326", geodesic=False)
            buffered = geometry.buffer(-EDGE_BUFFER_M, 1)
            features.append(
                ee.Feature(
                    buffered,
                    {
                        "hypothesis_id": hypothesis["hypothesis_id"],
                        "zone_id": zone_id,
                    },
                )
            )
    placement_features = ee.FeatureCollection(features)
    bounds = placement_features.geometry().bounds(1)

    collection = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterDate(START_DATE, END_DATE)
        .filterBounds(bounds)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VV", "VH", "angle"])
    )

    metadata_fc = collection.map(
        lambda image: ee.Feature(
            None,
            {
                "image_id": image.get("system:index"),
                "timestamp": image.get("system:time_start"),
                "orbit_pass": image.get("orbitProperties_pass"),
                "relative_orbit": image.get("relativeOrbitNumber_start"),
            },
        )
    )
    metadata_info = metadata_fc.getInfo()
    metadata = [feature.get("properties", {}) for feature in metadata_info.get("features", [])]
    selected = select_orbit_group(metadata)

    selected_collection = collection.filter(
        ee.Filter.eq("orbitProperties_pass", selected["orbit_pass"])
    ).filter(ee.Filter.eq("relativeOrbitNumber_start", selected["relative_orbit"]))

    reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
    zone_rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    query_months = month_sequence(START_DATE, END_DATE)
    months_with_acquisitions = 0

    for month in query_months:
        month_start = ee.Date(f"{month}-01")
        month_end = month_start.advance(1, "month")
        monthly_collection = selected_collection.filterDate(month_start, month_end)
        acquisition_count = int(monthly_collection.size().getInfo())
        if acquisition_count <= 0:
            continue
        months_with_acquisitions += 1
        monthly = monthly_collection.median()
        image = monthly.addBands(monthly.select("VV").subtract(monthly.select("VH")).rename("log_ratio_db"))
        reduced = image.reduceRegions(
            collection=placement_features,
            reducer=reducer,
            scale=10,
            tileScale=4,
        )
        info = reduced.getInfo()
        for feature in info.get("features", []):
            props = feature.get("properties", {})
            hypothesis_id = str(props.get("hypothesis_id") or "")
            zone_id = str(props.get("zone_id") or "")
            if not hypothesis_id or zone_id not in {"tp5", "tp6"}:
                continue
            zone_rows[(hypothesis_id, month, zone_id)] = props

    usable_by_hypothesis: dict[str, list[dict[str, Any]]] = defaultdict(list)
    all_monthly_rows: list[dict[str, Any]] = []
    for hypothesis in hypotheses:
        hypothesis_id = str(hypothesis["hypothesis_id"])
        for month in query_months:
            tp5 = zone_rows.get((hypothesis_id, month, "tp5"))
            tp6 = zone_rows.get((hypothesis_id, month, "tp6"))
            if not tp5 or not tp6:
                continue
            required = [
                tp5.get("VV_mean"),
                tp5.get("VH_mean"),
                tp5.get("angle_mean"),
                tp5.get("log_ratio_db_mean"),
                tp6.get("VV_mean"),
                tp6.get("VH_mean"),
                tp6.get("angle_mean"),
                tp6.get("log_ratio_db_mean"),
            ]
            if any(value is None for value in required):
                continue
            tp5_count = min(int(tp5.get("VV_count") or 0), int(tp5.get("VH_count") or 0))
            tp6_count = min(int(tp6.get("VV_count") or 0), int(tp6.get("VH_count") or 0))
            incidence_difference = abs(float(tp6["angle_mean"]) - float(tp5["angle_mean"]))
            if tp5_count < MIN_VALID_PIXELS or tp6_count < MIN_VALID_PIXELS:
                continue
            if incidence_difference > MAX_INCIDENCE_DIFFERENCE_DEG:
                continue
            difference = float(tp6["log_ratio_db_mean"]) - float(tp5["log_ratio_db_mean"])
            month_number = int(month.split("-")[1])
            row = {
                "hypothesis_id": hypothesis_id,
                "month": month,
                "season": SEASONS[month_number],
                "tp5_log_ratio_db": float(tp5["log_ratio_db_mean"]),
                "tp6_log_ratio_db": float(tp6["log_ratio_db_mean"]),
                "difference_tp6_minus_tp5": difference,
                "sign": sign_of(difference),
                "tp5_vv_db": float(tp5["VV_mean"]),
                "tp6_vv_db": float(tp6["VV_mean"]),
                "tp5_vh_db": float(tp5["VH_mean"]),
                "tp6_vh_db": float(tp6["VH_mean"]),
                "tp5_angle_deg": float(tp5["angle_mean"]),
                "tp6_angle_deg": float(tp6["angle_mean"]),
                "incidence_difference_deg": incidence_difference,
                "tp5_valid_pixels": tp5_count,
                "tp6_valid_pixels": tp6_count,
            }
            usable_by_hypothesis[hypothesis_id].append(row)
            all_monthly_rows.append(row)

    summaries = [
        summarize_placement(hypothesis, usable_by_hypothesis[str(hypothesis["hypothesis_id"])])
        for hypothesis in hypotheses
    ]
    passing = [summary for summary in summaries if summary.passed]
    passing_signs = Counter(summary.dominant_sign for summary in passing if summary.dominant_sign)
    shared_sign = passing_signs.most_common(1)[0][0] if passing_signs else None
    same_sign_passing = [summary for summary in passing if summary.dominant_sign == shared_sign]

    if all(summary.usable_months < MIN_USABLE_MONTHS for summary in summaries):
        status = "insufficient_data"
    elif len(same_sign_passing) >= MIN_PASSING_PLACEMENTS and len(same_sign_passing) == len(passing):
        status = "ordering_supported"
    else:
        status = "ordering_inconsistent"

    write_csvs(all_monthly_rows, summaries)
    return {
        "status": status,
        "selected_orbit": {
            "orbit_pass": selected["orbit_pass"],
            "relative_orbit": selected["relative_orbit"],
            "distinct_months": selected["distinct_months"],
            "acquisition_count": selected["acquisition_count"],
        },
        "orbit_ranking": selected["ranking"],
        "months_with_selected_orbit_acquisitions": months_with_acquisitions,
        "geometry_hypothesis_count": len(hypotheses),
        "passing_placement_count": len(passing),
        "same_sign_passing_placement_count": len(same_sign_passing),
        "required_passing_placement_count": MIN_PASSING_PLACEMENTS,
        "shared_dominant_sign": shared_sign,
        "placement_summaries": [
            {
                "hypothesis_id": summary.hypothesis_id,
                "transform_id": summary.transform_id,
                "translation_x": summary.translation_x,
                "translation_y": summary.translation_y,
                "usable_months": summary.usable_months,
                "positive_months": summary.positive_months,
                "negative_months": summary.negative_months,
                "zero_months": summary.zero_months,
                "dominant_sign": summary.dominant_sign,
                "dominant_fraction": summary.dominant_fraction,
                "season_support": summary.season_support,
                "passed": summary.passed,
                "failure_reasons": list(summary.failure_reasons),
            }
            for summary in summaries
        ],
        "monthly_usable_row_count": len(all_monthly_rows),
    }


def main() -> int:
    result: dict[str, Any] = {
        "status": "auth_required",
        "protocol": "tyrone_multi_placement_sensitivity_v1",
        "query_period": {"start": START_DATE, "end_exclusive": END_DATE},
        "primary_feature": "VV_dB_minus_VH_dB",
        "edge_buffer_m": EDGE_BUFFER_M,
        "secret_values_printed": False,
        "interactive_authentication_attempted": False,
        "classifier_output_used": False,
        "pca_anomaly_used": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
        "unknown_aoi_depth_enabled": False,
    }
    cleanup: list[Path] = []
    try:
        import ee  # type: ignore

        credential_source, project_source, cleanup = initialize_earth_engine(ee)
        result["earth_engine_initialized"] = True
        result["credential_source"] = credential_source
        result["project_source"] = project_source
        hypotheses = build_hypotheses()
        query_result = run_query(ee, hypotheses)
        result.update(query_result)
        result["scientific_query_executed"] = True
    except Exception as exc:  # bounded diagnostic; workflow still uploads the artifact
        if not result.get("earth_engine_initialized"):
            result["status"] = "auth_required"
        else:
            result["status"] = "query_error"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:1000]
        result["scientific_query_executed"] = False
    finally:
        for path in cleanup:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    write_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
