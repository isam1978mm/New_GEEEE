#!/usr/bin/env python3
"""Preregistered Tyrone 3X six-plot raw Sentinel-1 RTC signal screen.

Public Microsoft Planetary Computer data only. No Earth Engine, classifier,
NB_DEPTH, calibration row, model fitting, or app-depth enablement.
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
from shapely.geometry import Polygon, mapping, shape
from shapely.ops import transform as geom_transform

OUT = Path("artifacts/tyrone_six_plot_raw_pc_rtc")
OUT.mkdir(parents=True, exist_ok=True)
RESULT = OUT / "result.json"
MONTHLY = OUT / "monthly_plot_features.csv"
GROUP_SCREEN = OUT / "monthly_group_screen.csv"
SOURCES = OUT / "selected_source_items.csv"
GEOMETRY = OUT / "geometry_used.geojson"

GEOMETRY_SOURCE = Path("data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson")
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "sentinel-1-rtc"
START = "2018-01-01"
END = "2024-01-01"
ORBIT_STATE = "descending"
RELATIVE_ORBIT = 56
TARGET_CRS = "EPSG:32612"
PIXEL_SIZE_M = 10.0
INWARD_BUFFER_M = 10.0
NODATA = -32768.0
MIN_VALID_PIXELS = 15
MIN_USABLE_MONTHS = 24
DOMINANT_FRACTION = 0.70
SEASON_FRACTION = 0.60
MIN_MONTHS_PER_SEASON = 4

PLOT_ORDER = {
    "outslope": ["TP1", "TP2", "TP3"],
    "top_surface": ["TP5", "TP6", "TP7"],
}
MEASURED_DEPTH_M = {
    "TP1": 0.70612,
    "TP2": 0.94996,
    "TP3": 1.28016,
    "TP5": 0.68072,
    "TP6": 0.94996,
    "TP7": 1.30556,
}
SAME_DEPTH_PAIRS = [("TP1", "TP5"), ("TP2", "TP6"), ("TP3", "TP7")]
FEATURES = ("vv_db", "vh_db", "log_ratio_db")
STATS = ("mean", "median", "std", "q25", "q75")
SEASONS = {
    12: "DJF", 1: "DJF", 2: "DJF",
    3: "MAM", 4: "MAM", 5: "MAM",
    6: "JJA", 7: "JJA", 8: "JJA",
    9: "SON", 10: "SON", 11: "SON",
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


def load_geometry() -> tuple[dict[str, Polygon], dict[str, dict[str, Any]]]:
    obj = json.loads(GEOMETRY_SOURCE.read_text(encoding="utf-8"))
    to_target = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    polygons: dict[str, Polygon] = {}
    props: dict[str, dict[str, Any]] = {}
    for feature in obj.get("features", []):
        p = feature.get("properties", {})
        pid = str(p.get("plot_id", ""))
        if pid not in MEASURED_DEPTH_M:
            continue
        geom = geom_transform(to_target.transform, shape(feature["geometry"]))
        eroded = geom.buffer(-INWARD_BUFFER_M)
        if eroded.is_empty or not eroded.is_valid or eroded.geom_type != "Polygon":
            raise RuntimeError(f"{pid}: 10 m inward buffer produced invalid/empty non-Polygon geometry")
        polygons[pid] = eroded
        props[pid] = dict(p)
    missing = sorted(set(MEASURED_DEPTH_M) - set(polygons))
    if missing:
        raise RuntimeError(f"missing plots: {missing}")
    return polygons, props


def geometry_and_grid(polygons: dict[str, Polygon]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
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
    masks: dict[str, np.ndarray] = {}
    counts: dict[str, int] = {}
    for pid, polygon in polygons.items():
        mask = geometry_mask(
            [mapping(polygon)], out_shape=(height, width), transform=transform,
            invert=True, all_touched=False,
        )
        count = int(mask.sum())
        if count < MIN_VALID_PIXELS:
            raise RuntimeError(f"{pid} has only {count} fixed-grid pixels after 10 m erosion")
        masks[pid] = mask
        counts[pid] = count
    return masks, {
        "crs": TARGET_CRS,
        "transform": transform,
        "width": width,
        "height": height,
        "bounds": (left, bottom, right, top),
        "mask_pixel_counts": counts,
    }


def write_geometry(polygons: dict[str, Polygon], props: dict[str, dict[str, Any]]) -> None:
    to_wgs = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)
    features = []
    for pid in sorted(polygons):
        wgs = geom_transform(to_wgs.transform, polygons[pid])
        features.append({
            "type": "Feature",
            "properties": {
                "plot_id": pid,
                "surface_type": props[pid].get("surface_type"),
                "measured_depth_mean_m": MEASURED_DEPTH_M[pid],
                "source_geometry": str(GEOMETRY_SOURCE),
                "inward_buffer_m": INWARD_BUFFER_M,
                "status": "fixed_preregistered_10m_interior",
            },
            "geometry": mapping(wgs),
        })
    GEOMETRY.write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=2) + "\n", encoding="utf-8")


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


def plot_stats(array: np.ndarray, mask: np.ndarray) -> dict[str, float | int | None]:
    values = array[mask]
    values = values[np.isfinite(values)]
    n = int(values.size)
    if n < MIN_VALID_PIXELS:
        return {"valid_pixel_count": n, **{k: None for k in STATS}}
    return {
        "valid_pixel_count": n,
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "std": float(np.std(values, ddof=0)),
        "q25": float(np.quantile(values, 0.25)),
        "q75": float(np.quantile(values, 0.75)),
    }


def classify_monotonic(values: list[float]) -> str:
    if values[0] < values[1] < values[2]:
        return "increasing"
    if values[0] > values[1] > values[2]:
        return "decreasing"
    return "nonmonotonic"


def evaluate_group(screen_rows: list[dict[str, Any]], feature: str, group: str) -> dict[str, Any]:
    rows = [r for r in screen_rows if r["feature"] == feature and r["surface_group"] == group]
    counts = Counter(r["classification"] for r in rows)
    usable = len(rows)
    inc = counts["increasing"]
    dec = counts["decreasing"]
    dominant = "increasing" if inc >= dec else "decreasing"
    dominant_count = max(inc, dec)
    dominant_fraction = dominant_count / usable if usable else None
    season_support: dict[str, Any] = {}
    seasons_pass = True
    for season in ("DJF", "MAM", "JJA", "SON"):
        srows = [r for r in rows if r["season"] == season]
        match = sum(r["classification"] == dominant for r in srows)
        frac = match / len(srows) if srows else None
        passed = bool(len(srows) >= MIN_MONTHS_PER_SEASON and frac is not None and frac >= SEASON_FRACTION)
        season_support[season] = {
            "usable_months": len(srows),
            "matching_months": match,
            "matching_fraction": frac,
            "passed": passed,
        }
        seasons_pass = seasons_pass and passed
    passed = bool(
        usable >= MIN_USABLE_MONTHS
        and dominant_fraction is not None
        and dominant_fraction >= DOMINANT_FRACTION
        and seasons_pass
    )
    return {
        "usable_months": usable,
        "increasing_months": inc,
        "decreasing_months": dec,
        "nonmonotonic_months": counts["nonmonotonic"],
        "dominant_direction": dominant,
        "dominant_fraction_all_usable_months": dominant_fraction,
        "season_support": season_support,
        "passed_group_screen": passed,
    }


def main() -> int:
    result: dict[str, Any] = {
        "status": "started",
        "protocol": "tyrone_six_plot_raw_rtc_screen_v1",
        "period_start": START,
        "period_end_exclusive": END,
        "orbit_state": ORBIT_STATE,
        "relative_orbit": RELATIVE_ORBIT,
        "source": {"stac_url": STAC_URL, "collection": COLLECTION},
        "geometry_source": str(GEOMETRY_SOURCE),
        "geometry_inward_buffer_m": INWARD_BUFFER_M,
        "classifier_output_used": False,
        "pca_anomaly_used": False,
        "nb_depth_used": False,
        "earth_engine_query_executed": False,
        "scientific_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    }

    polygons, props = load_geometry()
    masks, grid = geometry_and_grid(polygons)
    write_geometry(polygons, props)
    result["grid"] = {**grid, "transform": list(grid["transform"])[:6]}

    minx = min(p.bounds[0] for p in polygons.values())
    miny = min(p.bounds[1] for p in polygons.values())
    maxx = max(p.bounds[2] for p in polygons.values())
    maxy = max(p.bounds[3] for p in polygons.values())
    bbox_poly = Polygon([(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)])
    to_wgs = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)
    bbox_wgs = geom_transform(to_wgs.transform, bbox_poly).bounds

    catalog = pystac_client.Client.open(STAC_URL)
    items = list(catalog.search(
        collections=[COLLECTION], bbox=list(bbox_wgs), datetime=f"{START}/{END}"
    ).items())
    selected = []
    for item in items:
        p = item.properties
        pols = {str(v).upper() for v in p.get("sar:polarizations", [])}
        state = str(p.get("sat:orbit_state") or "").lower()
        orbit = p.get("sat:relative_orbit")
        if (
            p.get("sar:instrument_mode") == "IW"
            and {"VV", "VH"}.issubset(pols)
            and "vv" in item.assets and "vh" in item.assets
            and state == ORBIT_STATE
            and orbit is not None and int(orbit) == RELATIVE_ORBIT
        ):
            selected.append(item)
    selected.sort(key=item_time)
    result["candidate_item_count"] = len(items)
    result["selected_item_count"] = len(selected)
    result["scientific_query_executed"] = True

    by_month: dict[str, list[tuple[Any, np.ndarray, np.ndarray]]] = defaultdict(list)
    source_rows: list[dict[str, Any]] = []
    for item in selected:
        dt = item_time(item)
        source = {
            "item_id": item.id,
            "datetime": dt.isoformat(),
            "month": dt.strftime("%Y-%m"),
            "orbit_state": str(item.properties.get("sat:orbit_state") or ""),
            "relative_orbit": item.properties.get("sat:relative_orbit"),
            "read_status": "failed",
            "error": "",
        }
        try:
            vv, vh = read_item(item, grid)
            by_month[dt.strftime("%Y-%m")].append((item, vv, vh))
            source["read_status"] = "ok"
        except Exception as exc:
            source["error"] = f"{type(exc).__name__}: {exc}"[:1000]
        source_rows.append(source)

    monthly_rows: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    for month in sorted(by_month):
        records = by_month[month]
        if not records:
            continue
        vv = np.nanmedian(np.stack([r[1] for r in records]), axis=0)
        vh = np.nanmedian(np.stack([r[2] for r in records]), axis=0)
        arrays = {"vv_db": vv, "vh_db": vh, "log_ratio_db": vv - vh}
        dt = item_time(records[0][0])
        season = SEASONS[dt.month]
        month_plot_stats: dict[tuple[str, str], dict[str, Any]] = {}
        for pid in sorted(polygons):
            for feature, array in arrays.items():
                stats = plot_stats(array, masks[pid])
                month_plot_stats[(pid, feature)] = stats
                monthly_rows.append({
                    "month": month,
                    "season": season,
                    "acquisition_count": len(records),
                    "plot_id": pid,
                    "surface_type": props[pid].get("surface_type"),
                    "measured_depth_mean_m": MEASURED_DEPTH_M[pid],
                    "feature": feature,
                    **stats,
                })
        for feature in FEATURES:
            for group, order in PLOT_ORDER.items():
                medians = [month_plot_stats[(pid, feature)]["median"] for pid in order]
                if all(v is not None for v in medians):
                    group_rows.append({
                        "month": month,
                        "season": season,
                        "feature": feature,
                        "surface_group": group,
                        "plot_order": ">".join(order),
                        "classification": classify_monotonic([float(v) for v in medians]),
                        "first_median": medians[0],
                        "second_median": medians[1],
                        "third_median": medians[2],
                    })

    evaluations: dict[str, Any] = {}
    for feature in FEATURES:
        groups = {group: evaluate_group(group_rows, feature, group) for group in PLOT_ORDER}
        candidate = bool(
            all(g["passed_group_screen"] for g in groups.values())
            and groups["outslope"]["dominant_direction"] == groups["top_surface"]["dominant_direction"]
        )
        evaluations[feature] = {
            "groups": groups,
            "same_dominant_direction": groups["outslope"]["dominant_direction"] == groups["top_surface"]["dominant_direction"],
            "candidate_depth_responsive_signal": candidate,
        }

    same_depth: dict[str, Any] = {}
    by_key = {(r["month"], r["plot_id"], r["feature"]): r for r in monthly_rows}
    months = sorted({r["month"] for r in monthly_rows})
    for feature in FEATURES:
        fobj: dict[str, Any] = {}
        for a, b in SAME_DEPTH_PAIRS:
            diffs = []
            for month in months:
                ra = by_key.get((month, a, feature))
                rb = by_key.get((month, b, feature))
                if ra and rb and ra["median"] is not None and rb["median"] is not None:
                    diffs.append(float(rb["median"]) - float(ra["median"]))
            fobj[f"{b}_minus_{a}"] = {
                "usable_months": len(diffs),
                "median_difference": float(np.median(diffs)) if diffs else None,
                "mean_difference": float(np.mean(diffs)) if diffs else None,
                "q25_difference": float(np.quantile(diffs, 0.25)) if diffs else None,
                "q75_difference": float(np.quantile(diffs, 0.75)) if diffs else None,
            }
        same_depth[feature] = fobj

    result["read_success_count"] = sum(r["read_status"] == "ok" for r in source_rows)
    result["read_failure_count"] = sum(r["read_status"] != "ok" for r in source_rows)
    result["usable_month_count"] = len(months)
    result["feature_evaluations"] = evaluations
    result["same_depth_surface_differences"] = same_depth
    passing = [f for f, e in evaluations.items() if e["candidate_depth_responsive_signal"]]
    result["passing_features"] = passing
    result["status"] = "candidate_signal_found" if passing else "no_candidate_signal_found"

    monthly_fields = [
        "month", "season", "acquisition_count", "plot_id", "surface_type",
        "measured_depth_mean_m", "feature", "mean", "median", "std", "q25", "q75", "valid_pixel_count",
    ]
    with MONTHLY.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=monthly_fields)
        writer.writeheader()
        writer.writerows({k: r.get(k) for k in monthly_fields} for r in monthly_rows)

    group_fields = [
        "month", "season", "feature", "surface_group", "plot_order", "classification",
        "first_median", "second_median", "third_median",
    ]
    with GROUP_SCREEN.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=group_fields)
        writer.writeheader()
        writer.writerows({k: r.get(k) for k in group_fields} for r in group_rows)

    source_fields = ["item_id", "datetime", "month", "orbit_state", "relative_orbit", "read_status", "error"]
    with SOURCES.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=source_fields)
        writer.writeheader()
        writer.writerows({k: r.get(k) for k in source_fields} for r in source_rows)

    RESULT.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "selected_item_count": result["selected_item_count"],
        "read_success_count": result["read_success_count"],
        "usable_month_count": result["usable_month_count"],
        "passing_features": passing,
        "feature_evaluations": evaluations,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
