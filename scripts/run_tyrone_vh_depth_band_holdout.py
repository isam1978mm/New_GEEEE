#!/usr/bin/env python3
"""Fresh temporal holdout for a Tyrone-only two-band VH depth output.

This workflow uses only 2024-01-01 through 2026-06-30 data, which were not used
in the 2018-2023 development analysis. It never enables app depth output.
"""
from __future__ import annotations

import csv
import json
import math
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import planetary_computer
import pystac_client
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.transform import Affine
from rasterio.vrt import WarpedVRT
from shapely.geometry import Polygon, mapping
from shapely.ops import transform as geom_transform

OUT = Path("artifacts/tyrone_vh_depth_band_holdout")
OUT.mkdir(parents=True, exist_ok=True)
RESULT = OUT / "result.json"
MONTHLY = OUT / "monthly_band_classifications.csv"
SOURCES = OUT / "selected_source_items.csv"
GEOMETRY = OUT / "preregistered_geometry.geojson"

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "sentinel-1-rtc"
START = "2024-01-01"
END = "2026-07-01"
ORBIT_STATE = "descending"
RELATIVE_ORBIT = 56
TARGET_CRS = "EPSG:32612"
PIXEL_SIZE_M = 10.0
NODATA = -32768.0
MIN_SUBSET_PIXELS = 5
MIN_ANCHOR_SEPARATION_DB = 0.25

DEPTH5_BEST = 0.68072
DEPTH6_BEST = 0.94996
DEPTH_SPAN = DEPTH6_BEST - DEPTH5_BEST
SHALLOW_RANGE = (0.65532, 0.70612)
DEEP_RANGE = (0.85090, 1.04902)

SHALLOW_POSITION_MAX = 1.0 / 3.0
DEEP_POSITION_MIN = 2.0 / 3.0

PERIOD_RULES = {
    "all": {
        "minimum_eligible_months": 12,
        "minimum_zone_coverage": 0.50,
        "minimum_zone_accuracy": 0.80,
        "minimum_paired_classified_months": 6,
        "minimum_paired_correct_fraction": 0.80,
    },
    "year_2024": {
        "minimum_eligible_months": 5,
        "minimum_zone_coverage": 0.40,
        "minimum_zone_accuracy": 0.75,
        "minimum_paired_classified_months": 2,
        "minimum_paired_correct_fraction": 0.75,
    },
    "year_2025_to_h1_2026": {
        "minimum_eligible_months": 8,
        "minimum_zone_coverage": 0.40,
        "minimum_zone_accuracy": 0.75,
        "minimum_paired_classified_months": 3,
        "minimum_paired_correct_fraction": 0.75,
    },
}
MIN_PASSING_SPLITS = 3

CORE_COORDS = {
    "tp5": [
        (-108.41686720244914, 32.72290093339319),
        (-108.41636296944517, 32.72272155362998),
        (-108.41650947152623, 32.72242292999285),
        (-108.4171542370669, 32.72271978069025),
        (-108.41686720244914, 32.72290093339319),
    ],
    "tp6": [
        (-108.41769163179988, 32.72214603107497),
        (-108.4168388637975, 32.72175341728606),
        (-108.41696147335597, 32.721505076150926),
        (-108.41781984639033, 32.721802258048086),
        (-108.41769163179988, 32.72214603107497),
    ],
}
SPLITS = {
    "west_anchor_east_holdout": ("west", "east"),
    "east_anchor_west_holdout": ("east", "west"),
    "north_anchor_south_holdout": ("north", "south"),
    "south_anchor_north_holdout": ("south", "north"),
}


def item_time(item: Any) -> datetime:
    value = item.datetime
    if value is None:
        raw = item.properties.get("datetime") or item.properties.get("start_datetime")
        if not raw:
            raise ValueError(f"item {item.id} has no datetime")
        value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def build_geometry_grid() -> tuple[dict[str, Polygon], dict[str, dict[str, np.ndarray]], dict[str, Any]]:
    to_target = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    polygons = {
        name: geom_transform(to_target.transform, Polygon(coords))
        for name, coords in CORE_COORDS.items()
    }
    minx = min(p.bounds[0] for p in polygons.values())
    miny = min(p.bounds[1] for p in polygons.values())
    maxx = max(p.bounds[2] for p in polygons.values())
    maxy = max(p.bounds[3] for p in polygons.values())
    left = math.floor(minx / PIXEL_SIZE_M) * PIXEL_SIZE_M
    bottom = math.floor(miny / PIXEL_SIZE_M) * PIXEL_SIZE_M
    right = math.ceil(maxx / PIXEL_SIZE_M) * PIXEL_SIZE_M
    top = math.ceil(maxy / PIXEL_SIZE_M) * PIXEL_SIZE_M
    width = int(round((right - left) / PIXEL_SIZE_M))
    height = int(round((top - bottom) / PIXEL_SIZE_M))
    transform = Affine(PIXEL_SIZE_M, 0.0, left, 0.0, -PIXEL_SIZE_M, top)
    rows, cols = np.indices((height, width))
    x = left + (cols + 0.5) * PIXEL_SIZE_M
    y = top - (rows + 0.5) * PIXEL_SIZE_M

    zone_parts: dict[str, dict[str, np.ndarray]] = {}
    counts: dict[str, dict[str, int]] = {}
    for zone, polygon in polygons.items():
        whole = geometry_mask(
            [mapping(polygon)],
            out_shape=(height, width),
            transform=transform,
            invert=True,
            all_touched=False,
        )
        median_x = float(np.median(x[whole]))
        median_y = float(np.median(y[whole]))
        parts = {
            "whole": whole,
            "west": whole & (x < median_x),
            "east": whole & (x >= median_x),
            "south": whole & (y < median_y),
            "north": whole & (y >= median_y),
        }
        for part_name, mask in parts.items():
            if part_name != "whole" and int(mask.sum()) < MIN_SUBSET_PIXELS:
                raise RuntimeError(
                    f"{zone} {part_name} has only {int(mask.sum())} pixels"
                )
        zone_parts[zone] = parts
        counts[zone] = {name: int(mask.sum()) for name, mask in parts.items()}

    grid = {
        "crs": TARGET_CRS,
        "transform": transform,
        "width": width,
        "height": height,
        "bounds": (left, bottom, right, top),
        "subset_pixel_counts": counts,
    }
    return polygons, zone_parts, grid


def signed(item: Any) -> Any:
    clone = item.clone()
    planetary_computer.sign_inplace(clone)
    return clone


def read_vh_db(item: Any, grid: dict[str, Any]) -> np.ndarray:
    last: Exception | None = None
    for attempt in range(3):
        try:
            obj = signed(item)
            href = obj.assets["vh"].href
            with rasterio.open(href, sharing=False) as src:
                src_nodata = src.nodata if src.nodata is not None else NODATA
                with WarpedVRT(
                    src,
                    crs=grid["crs"],
                    transform=grid["transform"],
                    width=grid["width"],
                    height=grid["height"],
                    resampling=Resampling.nearest,
                    src_nodata=src_nodata,
                    nodata=NODATA,
                ) as vrt:
                    array = np.asarray(
                        vrt.read(1, masked=True).filled(np.nan),
                        dtype=np.float64,
                    )
            out = np.full(array.shape, np.nan, dtype=np.float64)
            valid = np.isfinite(array) & (array > 0) & (array != NODATA)
            out[valid] = 10.0 * np.log10(array[valid])
            return out
        except Exception as exc:
            last = exc
            if attempt < 2:
                time.sleep(2.0 * (attempt + 1))
    assert last is not None
    raise last


def mask_mean(array: np.ndarray, mask: np.ndarray) -> tuple[float | None, int]:
    values = array[mask]
    values = values[np.isfinite(values)]
    if values.size < MIN_SUBSET_PIXELS:
        return None, int(values.size)
    return float(values.mean()), int(values.size)


def period_name(month: str) -> str:
    return "year_2024" if month < "2025-01" else "year_2025_to_h1_2026"


def classify_position(position: float) -> str:
    if not math.isfinite(position) or position < 0.0 or position > 1.0:
        return "abstain"
    if position <= SHALLOW_POSITION_MAX:
        return "shallow"
    if position >= DEEP_POSITION_MIN:
        return "deep"
    return "abstain"


def evaluate_period(rows: list[dict[str, Any]], period: str) -> dict[str, Any]:
    subset = rows if period == "all" else [row for row in rows if row["period"] == period]
    rules = PERIOD_RULES[period]
    eligible_months = len(subset)
    zone_results: dict[str, Any] = {}
    zone_passed = True
    for zone, truth in (("tp5", "shallow"), ("tp6", "deep")):
        labels = [str(row[f"{zone}_band"]) for row in subset]
        classified = [label for label in labels if label != "abstain"]
        correct = sum(label == truth for label in classified)
        wrong = len(classified) - correct
        coverage = len(classified) / eligible_months if eligible_months else None
        accuracy = correct / len(classified) if classified else None
        passed = bool(
            eligible_months >= rules["minimum_eligible_months"]
            and coverage is not None
            and coverage >= rules["minimum_zone_coverage"]
            and accuracy is not None
            and accuracy >= rules["minimum_zone_accuracy"]
        )
        zone_results[zone] = {
            "truth_band": truth,
            "eligible_months": eligible_months,
            "classified_months": len(classified),
            "abstained_months": eligible_months - len(classified),
            "correct_classifications": correct,
            "wrong_classifications": wrong,
            "coverage_fraction": coverage,
            "accuracy_fraction": accuracy,
            "passed": passed,
        }
        zone_passed = zone_passed and passed

    paired_rows = [
        row
        for row in subset
        if row["tp5_band"] != "abstain" and row["tp6_band"] != "abstain"
    ]
    paired_correct = sum(
        row["tp5_band"] == "shallow" and row["tp6_band"] == "deep"
        for row in paired_rows
    )
    paired_fraction = (
        paired_correct / len(paired_rows) if paired_rows else None
    )
    paired_passed = bool(
        len(paired_rows) >= rules["minimum_paired_classified_months"]
        and paired_fraction is not None
        and paired_fraction >= rules["minimum_paired_correct_fraction"]
    )
    return {
        "rules": rules,
        "eligible_months": eligible_months,
        "zones": zone_results,
        "paired_classified_months": len(paired_rows),
        "paired_correct_months": paired_correct,
        "paired_correct_fraction": paired_fraction,
        "paired_passed": paired_passed,
        "passed": bool(zone_passed and paired_passed),
    }


def write_geometry() -> None:
    features = []
    for zone, coords in CORE_COORDS.items():
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "zone_id": zone,
                    "status": "provisional_derived_geometry_40m_core",
                    "known_band": "shallow" if zone == "tp5" else "deep",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[list(point) for point in coords]],
                },
            }
        )
    GEOMETRY.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, indent=2)
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    write_geometry()
    polygons, parts, grid = build_geometry_grid()
    bbox = (
        min(p.bounds[0] for p in polygons.values()),
        min(p.bounds[1] for p in polygons.values()),
        max(p.bounds[2] for p in polygons.values()),
        max(p.bounds[3] for p in polygons.values()),
    )
    to_wgs = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)
    west, south = to_wgs.transform(bbox[0], bbox[1])
    east, north = to_wgs.transform(bbox[2], bbox[3])

    catalog = pystac_client.Client.open(STAC_URL)
    candidates = list(
        catalog.search(
            collections=[COLLECTION],
            bbox=[west, south, east, north],
            datetime=f"{START}/{END}",
        ).items()
    )
    selected = []
    for item in candidates:
        props = item.properties
        pols = {str(value).upper() for value in props.get("sar:polarizations", [])}
        if (
            props.get("sar:instrument_mode") == "IW"
            and str(props.get("sat:orbit_state") or "").lower() == ORBIT_STATE
            and int(props.get("sat:relative_orbit") or -1) == RELATIVE_ORBIT
            and "VH" in pols
            and "vh" in item.assets
        ):
            selected.append(item)
    selected.sort(key=item_time)
    if not selected:
        raise RuntimeError("fixed descending orbit 56 has no usable items")

    by_month: dict[str, list[np.ndarray]] = defaultdict(list)
    source_rows: list[dict[str, Any]] = []
    for item in selected:
        dt = item_time(item)
        source = {
            "item_id": item.id,
            "datetime": dt.isoformat(),
            "month": dt.strftime("%Y-%m"),
            "read_status": "failed",
            "error": "",
        }
        try:
            by_month[dt.strftime("%Y-%m")].append(read_vh_db(item, grid))
            source["read_status"] = "ok"
        except Exception as exc:
            source["error"] = f"{type(exc).__name__}: {exc}"[:1000]
        source_rows.append(source)

    monthly_rows: list[dict[str, Any]] = []
    for month in sorted(by_month):
        arrays = by_month[month]
        if not arrays:
            continue
        vh = np.nanmedian(np.stack(arrays), axis=0)
        for split_name, (anchor_part, holdout_part) in SPLITS.items():
            anchor5, n_a5 = mask_mean(vh, parts["tp5"][anchor_part])
            anchor6, n_a6 = mask_mean(vh, parts["tp6"][anchor_part])
            hold5, n_h5 = mask_mean(vh, parts["tp5"][holdout_part])
            hold6, n_h6 = mask_mean(vh, parts["tp6"][holdout_part])
            if None in (anchor5, anchor6, hold5, hold6):
                continue
            separation = float(anchor6) - float(anchor5)
            if separation < MIN_ANCHOR_SEPARATION_DB:
                continue
            position5 = (float(hold5) - float(anchor5)) / separation
            position6 = (float(hold6) - float(anchor5)) / separation
            estimate5 = DEPTH5_BEST + position5 * DEPTH_SPAN
            estimate6 = DEPTH5_BEST + position6 * DEPTH_SPAN
            band5 = classify_position(position5)
            band6 = classify_position(position6)
            monthly_rows.append(
                {
                    "month": month,
                    "period": period_name(month),
                    "split": split_name,
                    "acquisition_count": len(arrays),
                    "anchor_part": anchor_part,
                    "holdout_part": holdout_part,
                    "anchor_tp5_vh_db": anchor5,
                    "anchor_tp6_vh_db": anchor6,
                    "anchor_separation_db": separation,
                    "holdout_tp5_vh_db": hold5,
                    "holdout_tp6_vh_db": hold6,
                    "tp5_relative_position": position5,
                    "tp6_relative_position": position6,
                    "tp5_diagnostic_estimated_depth_m": estimate5,
                    "tp6_diagnostic_estimated_depth_m": estimate6,
                    "tp5_band": band5,
                    "tp6_band": band6,
                    "tp5_correct": band5 == "shallow",
                    "tp6_correct": band6 == "deep",
                    "anchor_tp5_pixels": n_a5,
                    "anchor_tp6_pixels": n_a6,
                    "holdout_tp5_pixels": n_h5,
                    "holdout_tp6_pixels": n_h6,
                }
            )

    split_results: dict[str, Any] = {}
    for split_name in SPLITS:
        rows = [row for row in monthly_rows if row["split"] == split_name]
        periods = {
            period: evaluate_period(rows, period)
            for period in ("all", "year_2024", "year_2025_to_h1_2026")
        }
        split_results[split_name] = {
            "periods": periods,
            "passed": all(result["passed"] for result in periods.values()),
        }

    passing_splits = sum(result["passed"] for result in split_results.values())
    holdout_passed = passing_splits >= MIN_PASSING_SPLITS
    result = {
        "status": (
            "fresh_temporal_depth_band_supported"
            if holdout_passed
            else "fresh_temporal_depth_band_not_supported"
        ),
        "protocol": "tyrone_vh_two_band_temporal_holdout_v1",
        "source": {
            "stac_url": STAC_URL,
            "collection": COLLECTION,
            "period_start": START,
            "period_end_exclusive": END,
            "orbit_state": ORBIT_STATE,
            "relative_orbit": RELATIVE_ORBIT,
            "selected_items": len(selected),
            "read_successes": sum(row["read_status"] == "ok" for row in source_rows),
            "read_failures": sum(row["read_status"] != "ok" for row in source_rows),
        },
        "geometry_status": "provisional_derived_geometry_40m_core",
        "grid": {**grid, "transform": list(grid["transform"])[:6]},
        "minimum_anchor_separation_db": MIN_ANCHOR_SEPARATION_DB,
        "position_rules": {
            "no_extrapolation_interval": [0.0, 1.0],
            "shallow_position_max": SHALLOW_POSITION_MAX,
            "deep_position_min": DEEP_POSITION_MIN,
            "middle_region": "abstain",
        },
        "reported_numeric_bands_m": {
            "shallow": list(SHALLOW_RANGE),
            "deep": list(DEEP_RANGE),
        },
        "diagnostic_depth_anchors_m": {
            "tp5": DEPTH5_BEST,
            "tp6": DEPTH6_BEST,
        },
        "period_rules": PERIOD_RULES,
        "minimum_passing_splits": MIN_PASSING_SPLITS,
        "passing_splits": passing_splits,
        "split_results": split_results,
        "interpretation": "fresh_temporal_binary_band_holdout_only",
        "classifier_output_used": False,
        "pca_anomaly_used": False,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "continuous_unknown_depth_ready": False,
        "depth_band_ready": holdout_passed,
        "app_depth_enabled": False,
    }

    fields = [
        "month",
        "period",
        "split",
        "acquisition_count",
        "anchor_part",
        "holdout_part",
        "anchor_tp5_vh_db",
        "anchor_tp6_vh_db",
        "anchor_separation_db",
        "holdout_tp5_vh_db",
        "holdout_tp6_vh_db",
        "tp5_relative_position",
        "tp6_relative_position",
        "tp5_diagnostic_estimated_depth_m",
        "tp6_diagnostic_estimated_depth_m",
        "tp5_band",
        "tp6_band",
        "tp5_correct",
        "tp6_correct",
        "anchor_tp5_pixels",
        "anchor_tp6_pixels",
        "holdout_tp5_pixels",
        "holdout_tp6_pixels",
    ]
    with MONTHLY.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(monthly_rows)
    with SOURCES.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["item_id", "datetime", "month", "read_status", "error"],
        )
        writer.writeheader()
        writer.writerows(source_rows)
    RESULT.write_text(
        json.dumps(result, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "passing_splits": passing_splits,
                "split_results": split_results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
