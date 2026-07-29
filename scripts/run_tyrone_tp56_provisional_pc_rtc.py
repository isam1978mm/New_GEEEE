#!/usr/bin/env python3
"""Run the preregistered provisional Tyrone TP5/TP6 Sentinel-1 RTC ordering test.

Uses only public Microsoft Planetary Computer Sentinel-1 RTC VV/VH assets.
It does not train a model, create a calibration row, or enable app depth.
"""
from __future__ import annotations

import csv
import json
import math
import time
from collections import Counter, defaultdict
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

OUT = Path("artifacts/tyrone_tp56_provisional_pc_rtc")
OUT.mkdir(parents=True, exist_ok=True)
RESULT = OUT / "result.json"
MONTHLY = OUT / "monthly_features.csv"
SOURCES = OUT / "selected_source_items.csv"
GEOMETRY = OUT / "preregistered_geometry.geojson"

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "sentinel-1-rtc"
START = "2018-01-01"
END = "2024-01-01"
TARGET_CRS = "EPSG:32612"
PIXEL_SIZE_M = 10.0
NODATA = -32768.0
MIN_VALID_PIXELS = 15
MIN_USABLE_MONTHS = 24
DOMINANT_FRACTION = 0.70
SEASON_FRACTION = 0.60
MIN_MONTHS_PER_SEASON = 4

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
DEPTHS = {
    "tp5": {"best_m": 0.68072, "minimum_m": 0.65532, "maximum_m": 0.70612},
    "tp6": {"best_m": 0.94996, "minimum_m": 0.85090, "maximum_m": 1.04902},
}
SEASONS = {
    12: "DJF", 1: "DJF", 2: "DJF",
    3: "MAM", 4: "MAM", 5: "MAM",
    6: "JJA", 7: "JJA", 8: "JJA",
    9: "SON", 10: "SON", 11: "SON",
}
FEATURES = ("vv_db", "vh_db", "log_ratio_db")


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


def select_orbit(items: list[Any]) -> tuple[dict[str, Any], list[Any]]:
    groups: dict[tuple[str, int], list[Any]] = defaultdict(list)
    for item in items:
        props = item.properties
        pols = {str(v).upper() for v in props.get("sar:polarizations", [])}
        state = str(props.get("sat:orbit_state") or "").lower()
        orbit = props.get("sat:relative_orbit")
        if (
            props.get("sar:instrument_mode") == "IW"
            and {"VV", "VH"}.issubset(pols)
            and "vv" in item.assets
            and "vh" in item.assets
            and state
            and orbit is not None
        ):
            groups[(state, int(orbit))].append(item)
    if not groups:
        raise RuntimeError("no usable Sentinel-1 RTC orbit groups")
    ranking = []
    for (state, orbit), rows in groups.items():
        months = {item_time(item).strftime("%Y-%m") for item in rows}
        ranking.append({
            "orbit_state": state,
            "relative_orbit": orbit,
            "distinct_months": len(months),
            "acquisition_count": len(rows),
        })
    ranking.sort(key=lambda r: (-r["distinct_months"], -r["acquisition_count"], r["orbit_state"], r["relative_orbit"]))
    best = ranking[0]
    selected = sorted(groups[(best["orbit_state"], best["relative_orbit"])], key=item_time)
    return {**best, "ranking": ranking}, selected


def geometry_and_grid() -> tuple[dict[str, Polygon], dict[str, np.ndarray], dict[str, Any]]:
    to_target = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    polygons = {
        name: geom_transform(to_target.transform, Polygon(coords))
        for name, coords in CORE_COORDS.items()
    }
    if not all(p.is_valid and not p.is_empty for p in polygons.values()):
        raise RuntimeError("preregistered geometry is invalid")
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
    masks = {}
    counts = {}
    for name, polygon in polygons.items():
        mask = geometry_mask([mapping(polygon)], out_shape=(height, width), transform=transform, invert=True, all_touched=False)
        count = int(mask.sum())
        if count < MIN_VALID_PIXELS:
            raise RuntimeError(f"{name} has only {count} fixed-grid pixels")
        masks[name] = mask
        counts[name] = count
    grid = {
        "crs": TARGET_CRS,
        "transform": transform,
        "width": width,
        "height": height,
        "bounds": (left, bottom, right, top),
        "mask_pixel_counts": counts,
    }
    return polygons, masks, grid


def signed(item: Any) -> Any:
    clone = item.clone()
    planetary_computer.sign_inplace(clone)
    return clone


def read_cog(href: str, grid: dict[str, Any]) -> np.ndarray:
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
            array = np.asarray(vrt.read(1, masked=True).filled(np.nan), dtype=np.float64)
    out = np.full(array.shape, np.nan, dtype=np.float64)
    valid = np.isfinite(array) & (array > 0) & (array != NODATA)
    out[valid] = 10.0 * np.log10(array[valid])
    return out


def read_item(item: Any, grid: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    last: Exception | None = None
    for attempt in range(3):
        try:
            obj = signed(item)
            return read_cog(obj.assets["vv"].href, grid), read_cog(obj.assets["vh"].href, grid)
        except Exception as exc:
            last = exc
            if attempt < 2:
                time.sleep(2.0 * (attempt + 1))
    assert last is not None
    raise last


def masked_mean(array: np.ndarray, mask: np.ndarray) -> tuple[float | None, int]:
    values = array[mask]
    values = values[np.isfinite(values)]
    if values.size < MIN_VALID_PIXELS:
        return None, int(values.size)
    return float(values.mean()), int(values.size)


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float | None, float | None]:
    if total <= 0:
        return None, None
    p = successes / total
    den = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / den
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def evaluate(rows: list[dict[str, Any]], feature: str) -> dict[str, Any]:
    diffs = [float(r[f"difference_{feature}_tp6_minus_tp5"]) for r in rows if r.get(f"difference_{feature}_tp6_minus_tp5") is not None]
    signs = ["positive" if d > 0 else "negative" if d < 0 else "zero" for d in diffs]
    counts = Counter(signs)
    nonzero = counts["positive"] + counts["negative"]
    dominant = None
    dominant_count = 0
    if nonzero:
        dominant = "positive" if counts["positive"] >= counts["negative"] else "negative"
        dominant_count = counts[dominant]
    frac = dominant_count / nonzero if nonzero else None
    low, high = wilson_interval(dominant_count, nonzero)
    season_support = {}
    season_pass = True
    for season in ("DJF", "MAM", "JJA", "SON"):
        vals = [float(r[f"difference_{feature}_tp6_minus_tp5"]) for r in rows if r.get("season") == season and r.get(f"difference_{feature}_tp6_minus_tp5") is not None]
        season_signs = ["positive" if d > 0 else "negative" if d < 0 else "zero" for d in vals]
        sc = Counter(season_signs)
        valid = sc["positive"] + sc["negative"]
        match = sc[dominant] if dominant else 0
        sfrac = match / valid if valid else None
        passed = bool(dominant and valid >= MIN_MONTHS_PER_SEASON and sfrac is not None and sfrac >= SEASON_FRACTION)
        season_support[season] = {"usable_months": len(vals), "nonzero_months": valid, "matching_months": match, "matching_fraction": sfrac, "passed": passed}
        season_pass = season_pass and passed
    passed = bool(len(diffs) >= MIN_USABLE_MONTHS and frac is not None and frac >= DOMINANT_FRACTION and season_pass)
    return {
        "usable_months": len(diffs),
        "positive_months": counts["positive"],
        "negative_months": counts["negative"],
        "zero_months": counts["zero"],
        "dominant_sign": dominant,
        "dominant_fraction": frac,
        "dominant_fraction_wilson_95": [low, high],
        "season_support": season_support,
        "passed_ordering_screen": passed,
        "median_difference": float(np.median(diffs)) if diffs else None,
        "mean_difference": float(np.mean(diffs)) if diffs else None,
    }


def write_geometry() -> None:
    features = []
    for name, coords in CORE_COORDS.items():
        features.append({
            "type": "Feature",
            "properties": {
                "zone_id": name,
                "geometry_kind": "core_40m",
                "status": "provisional_derived_geometry",
                "depth": DEPTHS[name],
                "registration_buffer_m": 40,
            },
            "geometry": {"type": "Polygon", "coordinates": [[list(v) for v in coords]]},
        })
    GEOMETRY.write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    result: dict[str, Any] = {
        "status": "started",
        "protocol": "tyrone_tp56_provisional_pc_rtc_v1",
        "period_start": START,
        "period_end_exclusive": END,
        "source": {"stac_url": STAC_URL, "collection": COLLECTION},
        "geometry_status": "provisional_derived_geometry_40m_core",
        "geometry_registration_uncertainty_m": 40,
        "classifier_output_used": False,
        "pca_anomaly_used": False,
        "earth_engine_query_executed": False,
        "scientific_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    }
    write_geometry()
    polygons, masks, grid = geometry_and_grid()
    result["grid"] = {**grid, "transform": list(grid["transform"])[:6]}
    bbox_poly = Polygon([
        (min(p.bounds[0] for p in polygons.values()), min(p.bounds[1] for p in polygons.values())),
        (max(p.bounds[2] for p in polygons.values()), min(p.bounds[1] for p in polygons.values())),
        (max(p.bounds[2] for p in polygons.values()), max(p.bounds[3] for p in polygons.values())),
        (min(p.bounds[0] for p in polygons.values()), max(p.bounds[3] for p in polygons.values())),
    ])
    to_wgs = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)
    bbox_wgs = geom_transform(to_wgs.transform, bbox_poly).bounds

    catalog = pystac_client.Client.open(STAC_URL)
    items = list(catalog.search(collections=[COLLECTION], bbox=list(bbox_wgs), datetime=f"{START}/{END}").items())
    selection, selected = select_orbit(items)
    result["orbit_selection"] = selection
    result["candidate_item_count"] = len(items)
    result["selected_item_count"] = len(selected)
    result["scientific_query_executed"] = True

    by_month: dict[str, list[tuple[Any, np.ndarray, np.ndarray]]] = defaultdict(list)
    source_rows = []
    for item in selected:
        dt = item_time(item)
        source = {"item_id": item.id, "datetime": dt.isoformat(), "month": dt.strftime("%Y-%m"), "read_status": "failed", "error": ""}
        try:
            vv, vh = read_item(item, grid)
            by_month[dt.strftime("%Y-%m")].append((item, vv, vh))
            source["read_status"] = "ok"
        except Exception as exc:
            source["error"] = f"{type(exc).__name__}: {exc}"[:1000]
        source_rows.append(source)

    monthly_rows = []
    for month in sorted(by_month):
        records = by_month[month]
        if not records:
            continue
        vv_stack = np.stack([r[1] for r in records])
        vh_stack = np.stack([r[2] for r in records])
        vv = np.nanmedian(vv_stack, axis=0)
        vh = np.nanmedian(vh_stack, axis=0)
        ratio = vv - vh
        dt = item_time(records[0][0])
        row: dict[str, Any] = {"month": month, "season": SEASONS[dt.month], "acquisition_count": len(records)}
        for zone in ("tp5", "tp6"):
            vv_mean, vv_n = masked_mean(vv, masks[zone])
            vh_mean, vh_n = masked_mean(vh, masks[zone])
            ratio_mean, ratio_n = masked_mean(ratio, masks[zone])
            row[f"{zone}_vv_db"] = vv_mean
            row[f"{zone}_vh_db"] = vh_mean
            row[f"{zone}_log_ratio_db"] = ratio_mean
            row[f"{zone}_valid_pixels"] = min(vv_n, vh_n, ratio_n)
        for feature in FEATURES:
            a = row.get(f"tp5_{feature}")
            b = row.get(f"tp6_{feature}")
            row[f"difference_{feature}_tp6_minus_tp5"] = None if a is None or b is None else float(b) - float(a)
        monthly_rows.append(row)

    result["read_success_count"] = sum(r["read_status"] == "ok" for r in source_rows)
    result["read_failure_count"] = sum(r["read_status"] != "ok" for r in source_rows)
    result["usable_month_count"] = len(monthly_rows)
    result["feature_evaluations"] = {feature: evaluate(monthly_rows, feature) for feature in FEATURES}
    result["status"] = "ordering_supported" if any(v["passed_ordering_screen"] for v in result["feature_evaluations"].values()) else "ordering_not_supported"

    monthly_fields = [
        "month", "season", "acquisition_count",
        "tp5_vv_db", "tp6_vv_db", "difference_vv_db_tp6_minus_tp5",
        "tp5_vh_db", "tp6_vh_db", "difference_vh_db_tp6_minus_tp5",
        "tp5_log_ratio_db", "tp6_log_ratio_db", "difference_log_ratio_db_tp6_minus_tp5",
        "tp5_valid_pixels", "tp6_valid_pixels",
    ]
    with MONTHLY.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=monthly_fields)
        writer.writeheader()
        for row in monthly_rows:
            writer.writerow({k: row.get(k) for k in monthly_fields})
    with SOURCES.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["item_id", "datetime", "month", "read_status", "error"])
        writer.writeheader()
        writer.writerows(source_rows)
    RESULT.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "usable_month_count": result["usable_month_count"], "feature_evaluations": result["feature_evaluations"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
