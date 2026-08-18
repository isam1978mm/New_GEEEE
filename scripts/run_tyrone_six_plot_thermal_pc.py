#!/usr/bin/env python3
"""Run the frozen Tyrone 3X six-plot Landsat thermal screen.

Temporary scientific experiment only. The protocol is frozen in PR #89.
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

OUT = Path("artifacts/tyrone_six_plot_thermal_pc")
OUT.mkdir(parents=True, exist_ok=True)
RESULT = OUT / "result.json"
ACQUISITIONS = OUT / "acquisitions.csv"
GEOMETRY = OUT / "geometry_used.geojson"

GEOMETRY_SOURCE = Path("data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson")
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "landsat-c2-l2"
ST_ASSET = "lwir11"
QA_ASSET = "qa_pixel"
START = "2018-01-01"
END_EXCLUSIVE = "2024-01-01"
TARGET_CRS = "EPSG:32612"
INWARD_BUFFER_M = 10.0
MIN_USABLE_ACQUISITIONS = 24
MIN_SEASON_ACQUISITIONS = 4
GLOBAL_DIRECTION_FRACTION_MIN = 0.70
SEASON_DIRECTION_FRACTION_MIN = 0.60
FALLBACK_SCALE = 0.00341802
FALLBACK_OFFSET = 149.0

PLOTS = ("TP1", "TP2", "TP3", "TP5", "TP6", "TP7")
OUTSLOPE = ("TP1", "TP2", "TP3")
TOP = ("TP5", "TP6", "TP7")
MATCHED = (("TP1", "TP5"), ("TP2", "TP6"), ("TP3", "TP7"))
SEASONS = {
    12: "DJF", 1: "DJF", 2: "DJF",
    3: "MAM", 4: "MAM", 5: "MAM",
    6: "JJA", 7: "JJA", 8: "JJA",
    9: "SON", 10: "SON", 11: "SON",
}


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
                "status": "fixed_preregistered_thermal_interior",
            },
            "geometry": mapping(wgs),
        })
    GEOMETRY.write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=2) + "\n", encoding="utf-8")


def query_bbox(polygons: dict[str, Any]) -> list[float]:
    union = unary_union(list(polygons.values()))
    to_wgs = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)
    return list(geom_transform(to_wgs.transform, union).bounds)


def qa_valid(qa: np.ndarray) -> np.ndarray:
    # Landsat Collection 2 QA_PIXEL bits masked by frozen protocol:
    # 0 fill, 1 dilated cloud, 2 cirrus, 3 cloud, 4 cloud shadow, 5 snow.
    bad = np.zeros(qa.shape, dtype=bool)
    for bit in (0, 1, 2, 3, 4, 5):
        bad |= (qa.astype(np.uint32) & (1 << bit)) != 0
    return ~bad


def scale_offset(asset: Any) -> tuple[float, float, str]:
    bands = asset.extra_fields.get("raster:bands") or []
    if bands and isinstance(bands[0], dict):
        scale = bands[0].get("scale")
        offset = bands[0].get("offset")
        if scale is not None and offset is not None:
            return float(scale), float(offset), "stac_raster_band_metadata"
    return FALLBACK_SCALE, FALLBACK_OFFSET, "frozen_landsat_c2_l2_fallback"


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


def evaluate_item(item: Any, polygons_utm: dict[str, Any]) -> dict[str, Any]:
    clone = item.clone()
    planetary_computer.sign_inplace(clone)
    if ST_ASSET not in clone.assets or QA_ASSET not in clone.assets:
        raise RuntimeError("required surface-temperature or QA asset missing")

    st_asset = clone.assets[ST_ASSET]
    qa_asset = clone.assets[QA_ASSET]
    scale, offset, scale_source = scale_offset(st_asset)

    with rasterio.open(st_asset.href, sharing=False) as st_src:
        if st_src.crs is None:
            raise RuntimeError("surface-temperature raster has no CRS")
        if str(st_src.crs) == TARGET_CRS:
            polygons_src = polygons_utm
        else:
            tx = Transformer.from_crs(TARGET_CRS, st_src.crs, always_xy=True)
            polygons_src = {pid: geom_transform(tx.transform, poly) for pid, poly in polygons_utm.items()}
        site_union = unary_union(list(polygons_src.values()))
        win = clip_window(st_src, site_union.bounds)
        transform = st_src.window_transform(win)
        raw = st_src.read(1, window=win, masked=True)
        # Preserve the integer source data and carry the mask separately. Calling
        # raw.filled(np.nan) on a uint16 MaskedArray fails before any value is read.
        raw_data = np.asarray(raw.data, dtype=np.float64)
        raw_valid = ~np.ma.getmaskarray(raw) & np.isfinite(raw_data) & (raw_data > 0)

        with rasterio.open(qa_asset.href, sharing=False) as qa_src:
            same_grid = (
                qa_src.crs == st_src.crs
                and qa_src.width == st_src.width
                and qa_src.height == st_src.height
                and qa_src.transform.almost_equals(st_src.transform)
            )
            if same_grid:
                qa = np.asarray(qa_src.read(1, window=win), dtype=np.uint32)
            else:
                with WarpedVRT(
                    qa_src,
                    crs=st_src.crs,
                    transform=st_src.transform,
                    width=st_src.width,
                    height=st_src.height,
                    resampling=Resampling.nearest,
                ) as vrt:
                    qa = np.asarray(vrt.read(1, window=win), dtype=np.uint32)

        valid = raw_valid & qa_valid(qa)
        temp_k = raw_data * scale + offset
        valid &= np.isfinite(temp_k) & (temp_k > 200.0) & (temp_k < 360.0)

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
            vals = temp_k[use]
            vals = vals[np.isfinite(vals)]
            counts[pid] = int(vals.size)
            values[pid] = float(np.median(vals)) if vals.size else None

    usable = all(values[pid] is not None for pid in PLOTS)
    dt = item.datetime
    if dt is None:
        dt_text = str(item.properties.get("datetime", ""))
        month = int(dt_text[5:7]) if len(dt_text) >= 7 else 0
    else:
        dt_text = dt.isoformat()
        month = int(dt.month)
    season = SEASONS.get(month, "UNKNOWN")

    return {
        "item_id": item.id,
        "datetime": dt_text,
        "platform": item.properties.get("platform"),
        "path": item.properties.get("landsat:wrs_path"),
        "row": item.properties.get("landsat:wrs_row"),
        "eo_cloud_cover": item.properties.get("eo:cloud_cover"),
        "season": season,
        "scale": scale,
        "offset": offset,
        "scale_source": scale_source,
        "usable": usable,
        "values": values,
        "counts": counts,
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
        key = f"{top}_minus_{outslope}_k"
        if values.get(outslope) is None or values.get(top) is None:
            out[key] = None
        else:
            out[key] = float(values[top]) - float(values[outslope])
    return out


def main() -> int:
    polygons = load_eroded_polygons()
    write_geometry(polygons)

    catalog = pystac_client.Client.open(STAC_URL)
    items = list(catalog.search(
        collections=[COLLECTION],
        bbox=query_bbox(polygons),
        datetime=f"{START}/{END_EXCLUSIVE}",
    ).items())
    # Freeze deterministic processing order. Items without ST are skipped as
    # required by the preregistration; no filtering uses thermal values.
    items = sorted(items, key=lambda x: (x.datetime.isoformat() if x.datetime else "", x.id))

    rows: list[dict[str, Any]] = []
    read_failures: list[dict[str, str]] = []
    for item in items:
        if ST_ASSET not in item.assets or QA_ASSET not in item.assets:
            continue
        try:
            obj = evaluate_item(item, polygons)
            d = direction(obj["values"])
            offsets = surface_offsets(obj["values"])
            row: dict[str, Any] = {
                "item_id": obj["item_id"],
                "datetime": obj["datetime"],
                "platform": obj["platform"],
                "path": obj["path"],
                "row": obj["row"],
                "eo_cloud_cover": obj["eo_cloud_cover"],
                "season": obj["season"],
                "usable": obj["usable"],
                "direction": d,
                "scale": obj["scale"],
                "offset": obj["offset"],
                "scale_source": obj["scale_source"],
            }
            for pid in PLOTS:
                row[f"{pid}_median_k"] = obj["values"][pid]
                row[f"{pid}_valid_product_pixels"] = obj["counts"][pid]
            row.update(offsets)
            rows.append(row)
        except Exception as exc:
            read_failures.append({"item_id": item.id, "error": f"{type(exc).__name__}: {exc}"[:1000]})

    usable = [row for row in rows if row["usable"] and row["season"] in {"DJF", "MAM", "JJA", "SON"}]
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

    by_season: dict[str, Any] = {}
    season_support_ok = True
    for season in ("DJF", "MAM", "JJA", "SON"):
        srows = [row for row in usable if row["season"] == season]
        same = sum(1 for row in srows if selected_direction is not None and row["direction"] == selected_direction)
        frac = same / len(srows) if srows else 0.0
        enough = len(srows) >= MIN_SEASON_ACQUISITIONS
        passed = bool(enough and selected_direction is not None and frac >= SEASON_DIRECTION_FRACTION_MIN)
        if not passed:
            season_support_ok = False
        by_season[season] = {
            "usable_acquisitions": len(srows),
            "selected_direction_support_count": same,
            "selected_direction_fraction": frac,
            "minimum_acquisitions_met": enough,
            "direction_gate_passed": passed,
            "direction_counts": dict(Counter(row["direction"] for row in srows)),
        }

    total_support_ok = len(usable) >= MIN_USABLE_ACQUISITIONS
    global_gate_ok = bool(selected_direction is not None and global_fraction >= GLOBAL_DIRECTION_FRACTION_MIN)
    if not total_support_ok or any(by_season[s]["usable_acquisitions"] < MIN_SEASON_ACQUISITIONS for s in by_season):
        decision = "THERMAL_INSUFFICIENT_SUPPORT"
    elif global_gate_ok and season_support_ok:
        decision = "THERMAL_DIRECT_CANDIDATE"
    else:
        decision = "THERMAL_DIRECT_FAILED_CLOSE"

    pair_summary: dict[str, Any] = {}
    for outslope, top in MATCHED:
        key = f"{top}_minus_{outslope}_k"
        vals = [float(row[key]) for row in usable if row.get(key) is not None]
        pair_summary[key] = {
            "n": len(vals),
            "median_k": float(np.median(vals)) if vals else None,
            "positive_fraction": (sum(v > 0 for v in vals) / len(vals)) if vals else None,
            "negative_fraction": (sum(v < 0 for v in vals) / len(vals)) if vals else None,
        }

    fieldnames = [
        "item_id", "datetime", "platform", "path", "row", "eo_cloud_cover", "season",
        "usable", "direction", "scale", "offset", "scale_source",
    ]
    for pid in PLOTS:
        fieldnames.extend([f"{pid}_median_k", f"{pid}_valid_product_pixels"])
    fieldnames.extend([f"{top}_minus_{out}_k" for out, top in MATCHED])
    with ACQUISITIONS.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in fieldnames} for row in rows)

    result = {
        "date": "2026-08-18",
        "protocol": "tyrone_six_plot_thermal_screen_v1",
        "decision": decision,
        "source": {
            "stac_url": STAC_URL,
            "collection": COLLECTION,
            "surface_temperature_asset": ST_ASSET,
            "qa_asset": QA_ASSET,
            "start": START,
            "end_exclusive": END_EXCLUSIVE,
            "native_thermal_gsd_m_approx": 100,
            "candidate_items_with_required_assets": len(rows) + len(read_failures),
            "successful_item_reads": len(rows),
            "read_failure_count": len(read_failures),
            "read_failures": read_failures,
        },
        "geometry_source": str(GEOMETRY_SOURCE),
        "inward_buffer_m": INWARD_BUFFER_M,
        "usable_acquisitions": len(usable),
        "direction_counts": dict(counts),
        "selected_direction": selected_direction,
        "selected_direction_fraction": global_fraction,
        "global_direction_fraction_min": GLOBAL_DIRECTION_FRACTION_MIN,
        "minimum_usable_acquisitions": MIN_USABLE_ACQUISITIONS,
        "season_minimum_acquisitions": MIN_SEASON_ACQUISITIONS,
        "season_direction_fraction_min": SEASON_DIRECTION_FRACTION_MIN,
        "season_results": by_season,
        "surface_top_minus_outslope": pair_summary,
        "gates": {
            "total_support_ok": total_support_ok,
            "global_direction_gate_ok": global_gate_ok,
            "all_season_gates_ok": season_support_ok,
        },
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
