#!/usr/bin/env python3
"""Run the frozen Tyrone 3X six-plot Sentinel-2 optical screen.

Temporary scientific experiment only. The protocol is frozen in PR #92.
No Earth Engine, NB_DEPTH, classifier/PCA depth evidence, model fitting,
calibration row, UI change, or app-depth enablement.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import planetary_computer
import pystac_client
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window, from_bounds
from shapely.geometry import mapping, shape
from shapely.ops import transform as geom_transform, unary_union

OUT = Path("artifacts/tyrone_six_plot_optical_pc")
OUT.mkdir(parents=True, exist_ok=True)
RESULT = OUT / "result.json"
SCENES = OUT / "scene_plot_indices.csv"
MONTHLY = OUT / "monthly_composites.csv"
GEOMETRY = OUT / "geometry_used.geojson"

GEOMETRY_SOURCE = Path("data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson")
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "sentinel-2-l2a"
START = "2018-01-01"
END_EXCLUSIVE = "2024-01-01"
TARGET_CRS = "EPSG:32612"
INWARD_BUFFER_M = 10.0
GROWING_MONTHS = (4, 5, 6, 7, 8, 9, 10)
SCL_EXCLUDED = {0, 1, 3, 8, 9, 10, 11}
MIN_USABLE_MONTHS = 30
MIN_DISTINCT_YEARS_PER_CALENDAR_MONTH = 4
GLOBAL_DIRECTION_FRACTION_MIN = 0.70
CALENDAR_MONTH_DIRECTION_FRACTION_MIN = 0.60

PLOTS = ("TP1", "TP2", "TP3", "TP5", "TP6", "TP7")
OUTSLOPE = ("TP1", "TP2", "TP3")
TOP = ("TP5", "TP6", "TP7")
MATCHED = (("TP1", "TP5"), ("TP2", "TP6"), ("TP3", "TP7"))

FEATURES = {
    "NDVI": {
        "a": "B08",
        "b": "B04",
        "formula": "(B08-B04)/(B08+B04)",
        "native_support_m": 10,
        "minimum_valid_pixels": 20,
    },
    "NDMI": {
        "a": "B8A",
        "b": "B11",
        "formula": "(B8A-B11)/(B8A+B11)",
        "native_support_m": 20,
        "minimum_valid_pixels": 5,
    },
}
REQUIRED_ASSETS = {"B08", "B04", "B8A", "B11", "SCL"}


def load_eroded_polygons() -> dict[str, Any]:
    obj = json.loads(GEOMETRY_SOURCE.read_text(encoding="utf-8"))
    to_utm = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    out: dict[str, Any] = {}
    for feature in obj.get("features", []):
        pid = str(feature.get("properties", {}).get("plot_id", ""))
        if pid not in PLOTS:
            continue
        poly = geom_transform(to_utm.transform, shape(feature["geometry"]))
        inner = poly.buffer(-INWARD_BUFFER_M)
        if inner.is_empty or not inner.is_valid or inner.geom_type != "Polygon":
            raise RuntimeError(f"{pid}: invalid/empty fixed 10 m inward polygon")
        out[pid] = inner
    missing = sorted(set(PLOTS) - set(out))
    if missing:
        raise RuntimeError(f"missing six-plot geometry: {missing}")
    return out


def write_geometry(polygons: dict[str, Any]) -> None:
    to_wgs = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)
    features = []
    for pid in PLOTS:
        wgs = geom_transform(to_wgs.transform, polygons[pid])
        features.append({
            "type": "Feature",
            "properties": {
                "plot_id": pid,
                "inward_buffer_m": INWARD_BUFFER_M,
                "status": "fixed_preregistered_optical_interior",
            },
            "geometry": mapping(wgs),
        })
    GEOMETRY.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, indent=2) + "\n",
        encoding="utf-8",
    )


def query_bbox(polygons: dict[str, Any]) -> list[float]:
    union = unary_union(list(polygons.values()))
    to_wgs = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)
    return list(geom_transform(to_wgs.transform, union).bounds)


def clip_window(src: rasterio.io.DatasetReader, bounds: tuple[float, float, float, float]) -> Window:
    win = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
    full = Window(0, 0, src.width, src.height)
    try:
        win = win.intersection(full)
    except Exception as exc:
        raise RuntimeError(f"site outside source raster: {exc}") from exc
    if win.width < 1 or win.height < 1:
        raise RuntimeError("empty source window")
    return win


def band_scale_offset(asset: Any) -> tuple[float, float, str]:
    bands = asset.extra_fields.get("raster:bands") or []
    if bands and isinstance(bands[0], dict):
        scale = bands[0].get("scale")
        offset = bands[0].get("offset")
        if scale is not None:
            return float(scale), float(offset or 0.0), "stac_raster_band_metadata"
    # Sentinel-2 L2A reflectance is conventionally quantized by 10000. This
    # fallback is fixed before result inspection and applies equally to both
    # bands in a normalized-difference feature.
    return 0.0001, 0.0, "frozen_sentinel2_l2a_fallback"


def read_on_reference_grid(
    asset: Any,
    *,
    reference: rasterio.io.DatasetReader,
    window: Window,
    resampling: Resampling,
    masked: bool = False,
) -> np.ndarray | np.ma.MaskedArray:
    with rasterio.open(asset.href, sharing=False) as src:
        same_grid = (
            src.crs == reference.crs
            and src.width == reference.width
            and src.height == reference.height
            and src.transform.almost_equals(reference.transform)
        )
        if same_grid:
            return src.read(1, window=window, masked=masked)
        with WarpedVRT(
            src,
            crs=reference.crs,
            transform=reference.transform,
            width=reference.width,
            height=reference.height,
            resampling=resampling,
            src_nodata=src.nodata,
            nodata=src.nodata,
        ) as vrt:
            return vrt.read(1, window=window, masked=masked)


def evaluate_feature(
    clone: Any,
    polygons_utm: dict[str, Any],
    feature_name: str,
) -> dict[str, Any]:
    spec = FEATURES[feature_name]
    a_asset = clone.assets[spec["a"]]
    b_asset = clone.assets[spec["b"]]
    scl_asset = clone.assets["SCL"]
    a_scale, a_offset, a_scale_source = band_scale_offset(a_asset)
    b_scale, b_offset, b_scale_source = band_scale_offset(b_asset)

    with rasterio.open(a_asset.href, sharing=False) as ref:
        if ref.crs is None:
            raise RuntimeError(f"{feature_name}: reference band has no CRS")
        if str(ref.crs) == TARGET_CRS:
            polygons_src = polygons_utm
        else:
            tx = Transformer.from_crs(TARGET_CRS, ref.crs, always_xy=True)
            polygons_src = {pid: geom_transform(tx.transform, poly) for pid, poly in polygons_utm.items()}
        site_union = unary_union(list(polygons_src.values()))
        win = clip_window(ref, site_union.bounds)
        transform = ref.window_transform(win)

        a_raw = ref.read(1, window=win, masked=True)
        b_raw = read_on_reference_grid(
            b_asset,
            reference=ref,
            window=win,
            resampling=Resampling.bilinear,
            masked=True,
        )
        scl_raw = read_on_reference_grid(
            scl_asset,
            reference=ref,
            window=win,
            resampling=Resampling.nearest,
            masked=False,
        )

        a_data = np.asarray(a_raw.data, dtype=np.float64) * a_scale + a_offset
        b_data = np.asarray(b_raw.data, dtype=np.float64) * b_scale + b_offset
        a_valid = ~np.ma.getmaskarray(a_raw) & np.isfinite(a_data)
        b_valid = ~np.ma.getmaskarray(b_raw) & np.isfinite(b_data)
        scl = np.asarray(scl_raw, dtype=np.int16)
        quality = ~np.isin(scl, list(SCL_EXCLUDED))
        denominator = a_data + b_data
        valid = a_valid & b_valid & quality & np.isfinite(denominator) & (np.abs(denominator) > 1e-12)
        index = np.full(a_data.shape, np.nan, dtype=np.float64)
        index[valid] = (a_data[valid] - b_data[valid]) / denominator[valid]
        # Physical normalized differences should fall inside [-1, 1] apart from
        # tiny numerical excursions. Outside values are invalid rather than clipped.
        valid &= np.isfinite(index) & (index >= -1.000001) & (index <= 1.000001)

        values: dict[str, float | None] = {}
        counts: dict[str, int] = {}
        for pid in PLOTS:
            mask = geometry_mask(
                [mapping(polygons_src[pid])],
                out_shape=(int(win.height), int(win.width)),
                transform=transform,
                invert=True,
                all_touched=False,
            )
            use = mask & valid
            vals = index[use]
            vals = vals[np.isfinite(vals)]
            counts[pid] = int(vals.size)
            if vals.size >= int(spec["minimum_valid_pixels"]):
                values[pid] = float(np.median(vals))
            else:
                values[pid] = None

    # Frozen conservative implementation: an acquisition enters a monthly
    # composite only when all six plots meet the feature-specific pixel minimum.
    qualifies_all_six = all(values[pid] is not None for pid in PLOTS)
    return {
        "feature": feature_name,
        "values": values,
        "counts": counts,
        "qualifies_all_six": qualifies_all_six,
        "a_scale": a_scale,
        "a_offset": a_offset,
        "a_scale_source": a_scale_source,
        "b_scale": b_scale,
        "b_offset": b_offset,
        "b_scale_source": b_scale_source,
    }


def direction(values: dict[str, float | None]) -> str:
    if any(values.get(pid) is None for pid in PLOTS):
        return "not_usable"
    a = [float(values[p]) for p in OUTSLOPE]
    b = [float(values[p]) for p in TOP]
    if a[0] < a[1] < a[2] and b[0] < b[1] < b[2]:
        return "increasing"
    if a[0] > a[1] > a[2] and b[0] > b[1] > b[2]:
        return "decreasing"
    return "no_support"


def surface_offsets(values: dict[str, float | None]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for outslope, top in MATCHED:
        key = f"{top}_minus_{outslope}"
        if values.get(outslope) is None or values.get(top) is None:
            out[key] = None
        else:
            out[key] = float(values[top]) - float(values[outslope])
    return out


def feature_decision(month_rows: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [row for row in month_rows if row["usable"]]
    counts = Counter(row["direction"] for row in usable)
    inc = int(counts.get("increasing", 0))
    dec = int(counts.get("decreasing", 0))
    if inc > dec:
        selected_direction = "increasing"
        selected_count = inc
    elif dec > inc:
        selected_direction = "decreasing"
        selected_count = dec
    else:
        selected_direction = None
        selected_count = inc
    global_fraction = (selected_count / len(usable)) if usable and selected_direction else 0.0

    calendar_months: dict[str, Any] = {}
    support_gate_ok = len(usable) >= MIN_USABLE_MONTHS
    month_direction_gate_ok = True
    for month in GROWING_MONTHS:
        rows = [row for row in usable if int(row["month"]) == month]
        years = sorted({int(row["year"]) for row in rows})
        same = sum(1 for row in rows if selected_direction is not None and row["direction"] == selected_direction)
        frac = same / len(rows) if rows else 0.0
        enough_years = len(years) >= MIN_DISTINCT_YEARS_PER_CALENDAR_MONTH
        direction_ok = bool(enough_years and selected_direction is not None and frac >= CALENDAR_MONTH_DIRECTION_FRACTION_MIN)
        if not enough_years:
            support_gate_ok = False
        if not direction_ok:
            month_direction_gate_ok = False
        calendar_months[str(month)] = {
            "usable_composites": len(rows),
            "distinct_years": years,
            "distinct_year_count": len(years),
            "minimum_distinct_years_met": enough_years,
            "selected_direction_support_count": same,
            "selected_direction_fraction": frac,
            "direction_gate_passed": direction_ok,
            "direction_counts": dict(Counter(row["direction"] for row in rows)),
        }

    global_gate_ok = bool(selected_direction is not None and global_fraction >= GLOBAL_DIRECTION_FRACTION_MIN)
    if not support_gate_ok:
        decision = "OPTICAL_INSUFFICIENT_SUPPORT"
    elif global_gate_ok and month_direction_gate_ok:
        decision = "OPTICAL_DIRECT_CANDIDATE"
    else:
        decision = "OPTICAL_DIRECT_FAILED_CLOSE"

    pair_summary: dict[str, Any] = {}
    for outslope, top in MATCHED:
        key = f"{top}_minus_{outslope}"
        vals = [float(row[key]) for row in usable if row.get(key) is not None]
        pair_summary[key] = {
            "n": len(vals),
            "median": float(np.median(vals)) if vals else None,
            "positive_fraction": (sum(v > 0 for v in vals) / len(vals)) if vals else None,
            "negative_fraction": (sum(v < 0 for v in vals) / len(vals)) if vals else None,
        }

    return {
        "decision": decision,
        "usable_year_month_composites": len(usable),
        "direction_counts": dict(counts),
        "selected_direction": selected_direction,
        "selected_direction_fraction": global_fraction,
        "global_direction_gate_passed": global_gate_ok,
        "support_gate_passed": support_gate_ok,
        "calendar_month_direction_gate_passed": month_direction_gate_ok,
        "calendar_month_results": calendar_months,
        "surface_top_minus_outslope": pair_summary,
    }


def main() -> int:
    polygons = load_eroded_polygons()
    write_geometry(polygons)

    catalog = pystac_client.Client.open(STAC_URL)
    items = list(catalog.search(
        collections=[COLLECTION],
        bbox=query_bbox(polygons),
        datetime=f"{START}/{END_EXCLUSIVE}",
    ).items())
    items = sorted(items, key=lambda x: (x.datetime.isoformat() if x.datetime else "", x.id))

    scene_rows: list[dict[str, Any]] = []
    technical_failures: list[dict[str, str]] = []
    candidate_count = 0
    for item in items:
        dt = item.datetime
        if dt is None or int(dt.month) not in GROWING_MONTHS:
            continue
        if not REQUIRED_ASSETS.issubset(set(item.assets)):
            continue
        candidate_count += 1
        clone = item.clone()
        planetary_computer.sign_inplace(clone)
        for feature_name in FEATURES:
            try:
                obj = evaluate_feature(clone, polygons, feature_name)
                row: dict[str, Any] = {
                    "item_id": item.id,
                    "datetime": dt.isoformat(),
                    "year": int(dt.year),
                    "month": int(dt.month),
                    "feature": feature_name,
                    "platform": item.properties.get("platform"),
                    "tile": item.properties.get("s2:mgrs_tile"),
                    "eo_cloud_cover": item.properties.get("eo:cloud_cover"),
                    "qualifies_all_six": bool(obj["qualifies_all_six"]),
                    "a_scale": obj["a_scale"],
                    "a_offset": obj["a_offset"],
                    "a_scale_source": obj["a_scale_source"],
                    "b_scale": obj["b_scale"],
                    "b_offset": obj["b_offset"],
                    "b_scale_source": obj["b_scale_source"],
                }
                for pid in PLOTS:
                    row[f"{pid}_median"] = obj["values"][pid]
                    row[f"{pid}_valid_pixels"] = obj["counts"][pid]
                scene_rows.append(row)
            except Exception as exc:
                technical_failures.append({
                    "item_id": item.id,
                    "feature": feature_name,
                    "error": f"{type(exc).__name__}: {exc}"[:1000],
                })

    monthly_rows: list[dict[str, Any]] = []
    for feature_name in FEATURES:
        qualifying = [
            row for row in scene_rows
            if row["feature"] == feature_name and bool(row["qualifies_all_six"])
        ]
        groups: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
        for row in qualifying:
            groups[(int(row["year"]), int(row["month"]))].append(row)
        for (year, month), rows in sorted(groups.items()):
            values: dict[str, float | None] = {}
            for pid in PLOTS:
                vals = [float(row[f"{pid}_median"]) for row in rows if row.get(f"{pid}_median") is not None]
                values[pid] = float(np.median(vals)) if vals else None
            usable = all(values[pid] is not None for pid in PLOTS)
            d = direction(values)
            offsets = surface_offsets(values)
            out: dict[str, Any] = {
                "feature": feature_name,
                "year": year,
                "month": month,
                "scene_count": len(rows),
                "usable": usable,
                "direction": d,
            }
            for pid in PLOTS:
                out[f"{pid}_median"] = values[pid]
            out.update(offsets)
            monthly_rows.append(out)

    decisions = {
        feature_name: feature_decision([row for row in monthly_rows if row["feature"] == feature_name])
        for feature_name in FEATURES
    }

    scene_fields = [
        "item_id", "datetime", "year", "month", "feature", "platform", "tile", "eo_cloud_cover",
        "qualifies_all_six", "a_scale", "a_offset", "a_scale_source", "b_scale", "b_offset", "b_scale_source",
    ]
    for pid in PLOTS:
        scene_fields.extend([f"{pid}_median", f"{pid}_valid_pixels"])
    with SCENES.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=scene_fields)
        writer.writeheader()
        writer.writerows({k: row.get(k) for k in scene_fields} for row in scene_rows)

    monthly_fields = ["feature", "year", "month", "scene_count", "usable", "direction"]
    monthly_fields.extend([f"{pid}_median" for pid in PLOTS])
    monthly_fields.extend([f"{top}_minus_{out}" for out, top in MATCHED])
    with MONTHLY.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=monthly_fields)
        writer.writeheader()
        writer.writerows({k: row.get(k) for k in monthly_fields} for row in monthly_rows)

    result = {
        "date": "2026-08-18",
        "protocol": "tyrone_six_plot_optical_screen_v1",
        "source": {
            "stac_url": STAC_URL,
            "collection": COLLECTION,
            "start": START,
            "end_exclusive": END_EXCLUSIVE,
            "growing_months": list(GROWING_MONTHS),
            "candidate_items_with_required_assets": candidate_count,
            "scene_feature_rows": len(scene_rows),
            "technical_failure_count": len(technical_failures),
            "technical_failures": technical_failures,
        },
        "geometry_source": str(GEOMETRY_SOURCE),
        "inward_buffer_m": INWARD_BUFFER_M,
        "scl_excluded": sorted(SCL_EXCLUDED),
        "frozen_gates": {
            "minimum_usable_year_month_composites": MIN_USABLE_MONTHS,
            "minimum_distinct_years_per_calendar_month": MIN_DISTINCT_YEARS_PER_CALENDAR_MONTH,
            "global_direction_fraction_min": GLOBAL_DIRECTION_FRACTION_MIN,
            "calendar_month_direction_fraction_min": CALENDAR_MONTH_DIRECTION_FRACTION_MIN,
        },
        "features": FEATURES,
        "feature_results": decisions,
        "safeguards": {
            "classifier_output_used": False,
            "pca_anomaly_used": False,
            "nb_depth_used": False,
            "earth_engine_query_executed": False,
            "calibration_record_created": False,
            "training_started": False,
            "app_depth_enabled": False,
            "thresholds_changed_after_result": False,
        },
    }
    RESULT.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
