#!/usr/bin/env python3
"""Preregistered Tyrone 3X six-plot terrain signal/confounder screen.

Public Microsoft Planetary Computer 3DEP data only. No Earth Engine,
NB_DEPTH, classifier/PCA depth evidence, calibration row, model fitting,
or app-depth enablement.
"""
from __future__ import annotations

import csv
import json
import math
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
from scipy.ndimage import maximum_filter, minimum_filter, uniform_filter
from shapely.geometry import Polygon, mapping, shape
from shapely.ops import transform as geom_transform

OUT = Path("artifacts/tyrone_six_plot_terrain_pc")
OUT.mkdir(parents=True, exist_ok=True)
RESULT = OUT / "result.json"
PLOT_FEATURES = OUT / "plot_features.csv"
SOURCES = OUT / "source_items.csv"
GEOMETRY = OUT / "geometry_used.geojson"

GEOMETRY_SOURCE = Path("data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson")
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "3dep-seamless"
ASSET = "data"
GSD_M = 10
TARGET_CRS = "EPSG:32612"
PIXEL_SIZE_M = 10.0
MARGIN_M = 60.0
BUFFERS_M = (10.0, 20.0)
MIN_VALID_PIXELS = 15
NODATA = -999999.0

PLOTS = ("TP1", "TP2", "TP3", "TP5", "TP6", "TP7")
DEPTH_LEVELS = {
    "shallow": ("TP1", "TP5"),
    "medium": ("TP2", "TP6"),
    "deep": ("TP3", "TP7"),
}
MATCHED_SURFACE_PAIRS = (("TP1", "TP5"), ("TP2", "TP6"), ("TP3", "TP7"))
FEATURES = (
    "elevation_m",
    "slope_deg",
    "northness",
    "eastness",
    "roughness_3x3_m",
    "tpi_50m_m",
    "curvature_laplacian_per_m",
)
STATS = ("mean", "median", "std", "q25", "q75")


def load_polygons() -> dict[str, Polygon]:
    obj = json.loads(GEOMETRY_SOURCE.read_text(encoding="utf-8"))
    to_target = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    out: dict[str, Polygon] = {}
    for feature in obj.get("features", []):
        pid = str(feature.get("properties", {}).get("plot_id", ""))
        if pid not in PLOTS:
            continue
        geom = geom_transform(to_target.transform, shape(feature["geometry"]))
        if geom.is_empty or not geom.is_valid or geom.geom_type != "Polygon":
            raise RuntimeError(f"invalid source geometry for {pid}")
        out[pid] = geom
    missing = sorted(set(PLOTS) - set(out))
    if missing:
        raise RuntimeError(f"missing plots: {missing}")
    return out


def build_grid(polygons: dict[str, Polygon]) -> dict[str, Any]:
    minx = min(p.bounds[0] for p in polygons.values()) - MARGIN_M
    miny = min(p.bounds[1] for p in polygons.values()) - MARGIN_M
    maxx = max(p.bounds[2] for p in polygons.values()) + MARGIN_M
    maxy = max(p.bounds[3] for p in polygons.values()) + MARGIN_M
    left = math.floor(minx / PIXEL_SIZE_M) * PIXEL_SIZE_M
    bottom = math.floor(miny / PIXEL_SIZE_M) * PIXEL_SIZE_M
    right = math.ceil(maxx / PIXEL_SIZE_M) * PIXEL_SIZE_M
    top = math.ceil(maxy / PIXEL_SIZE_M) * PIXEL_SIZE_M
    width = int(round((right - left) / PIXEL_SIZE_M))
    height = int(round((top - bottom) / PIXEL_SIZE_M))
    transform = Affine(PIXEL_SIZE_M, 0.0, left, 0.0, -PIXEL_SIZE_M, top)
    return {
        "crs": TARGET_CRS,
        "transform": transform,
        "width": width,
        "height": height,
        "bounds": (left, bottom, right, top),
    }


def build_masks(polygons: dict[str, Polygon], grid: dict[str, Any]) -> tuple[dict[float, dict[str, np.ndarray]], dict[str, int]]:
    masks: dict[float, dict[str, np.ndarray]] = {}
    counts: dict[str, int] = {}
    for buffer_m in BUFFERS_M:
        masks[buffer_m] = {}
        for pid, polygon in polygons.items():
            inner = polygon.buffer(-buffer_m)
            if inner.is_empty or not inner.is_valid or inner.geom_type != "Polygon":
                raise RuntimeError(f"{pid}: {buffer_m:g} m inward buffer invalid/empty")
            mask = geometry_mask(
                [mapping(inner)],
                out_shape=(grid["height"], grid["width"]),
                transform=grid["transform"],
                invert=True,
                all_touched=False,
            )
            n = int(mask.sum())
            if n < MIN_VALID_PIXELS:
                raise RuntimeError(f"{pid}: only {n} fixed-grid pixels at {buffer_m:g} m buffer")
            masks[buffer_m][pid] = mask
            counts[f"{pid}_{int(buffer_m)}m"] = n
    return masks, counts


def bbox_wgs84(grid: dict[str, Any]) -> list[float]:
    left, bottom, right, top = grid["bounds"]
    poly = Polygon([(left, bottom), (right, bottom), (right, top), (left, top)])
    to_wgs = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)
    return list(geom_transform(to_wgs.transform, poly).bounds)


def read_item(item: Any, grid: dict[str, Any]) -> np.ndarray:
    clone = item.clone()
    planetary_computer.sign_inplace(clone)
    if ASSET not in clone.assets:
        raise RuntimeError(f"{item.id}: missing {ASSET!r} asset")
    with rasterio.open(clone.assets[ASSET].href, sharing=False) as src:
        src_nodata = src.nodata if src.nodata is not None else NODATA
        with WarpedVRT(
            src,
            crs=grid["crs"],
            transform=grid["transform"],
            width=grid["width"],
            height=grid["height"],
            resampling=Resampling.bilinear,
            src_nodata=src_nodata,
            nodata=NODATA,
        ) as vrt:
            arr = np.asarray(vrt.read(1, masked=True).filled(np.nan), dtype=np.float64)
    arr[~np.isfinite(arr)] = np.nan
    arr[arr == NODATA] = np.nan
    return arr


def derive_features(dem: np.ndarray) -> dict[str, np.ndarray]:
    valid = np.isfinite(dem)
    if int(valid.sum()) < 100:
        raise RuntimeError("insufficient DEM coverage")

    # Gradients / slope / aspect. The 60 m grid margin protects plot interiors
    # from array-edge effects for the frozen neighborhoods below.
    dzdy, dzdx = np.gradient(dem, PIXEL_SIZE_M, PIXEL_SIZE_M)
    slope_rad = np.arctan(np.hypot(dzdx, dzdy))
    slope_deg = np.degrees(slope_rad)

    # Downslope direction vector. Flat pixels are left at zero components.
    mag = np.hypot(dzdx, dzdy)
    eastness = np.zeros_like(dem, dtype=float)
    northness = np.zeros_like(dem, dtype=float)
    nonflat = np.isfinite(mag) & (mag > 0)
    eastness[nonflat] = -dzdx[nonflat] / mag[nonflat]
    northness[nonflat] = -dzdy[nonflat] / mag[nonflat]
    eastness[~valid] = np.nan
    northness[~valid] = np.nan

    # Frozen full-support local filters.
    max3 = maximum_filter(np.where(valid, dem, -np.inf), size=3, mode="nearest")
    min3 = minimum_filter(np.where(valid, dem, np.inf), size=3, mode="nearest")
    count3 = uniform_filter(valid.astype(float), size=3, mode="nearest") * 9.0
    rough = max3 - min3
    rough[count3 < 8.999] = np.nan

    sum11 = uniform_filter(np.where(valid, dem, 0.0), size=11, mode="nearest") * 121.0
    count11 = uniform_filter(valid.astype(float), size=11, mode="nearest") * 121.0
    local_mean = np.full_like(dem, np.nan, dtype=float)
    full11 = count11 >= 120.999
    local_mean[full11] = sum11[full11] / count11[full11]
    tpi = dem - local_mean

    d2zdx2 = np.gradient(dzdx, PIXEL_SIZE_M, axis=1)
    d2zdy2 = np.gradient(dzdy, PIXEL_SIZE_M, axis=0)
    curvature = d2zdx2 + d2zdy2

    arrays = {
        "elevation_m": dem.copy(),
        "slope_deg": slope_deg,
        "northness": northness,
        "eastness": eastness,
        "roughness_3x3_m": rough,
        "tpi_50m_m": tpi,
        "curvature_laplacian_per_m": curvature,
    }
    for arr in arrays.values():
        arr[~np.isfinite(arr)] = np.nan
    return arrays


def stats(array: np.ndarray, mask: np.ndarray) -> dict[str, float | int | None]:
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


def depth_direction(medians: dict[str, float | None]) -> str | None:
    if any(medians.get(pid) is None for pid in PLOTS):
        return None
    shallow = [float(medians[p]) for p in DEPTH_LEVELS["shallow"]]
    medium = [float(medians[p]) for p in DEPTH_LEVELS["medium"]]
    deep = [float(medians[p]) for p in DEPTH_LEVELS["deep"]]
    if max(shallow) < min(medium) and max(medium) < min(deep):
        return "increasing"
    if min(shallow) > max(medium) and min(medium) > max(deep):
        return "decreasing"
    return "not_fully_separated"


def surface_sign(medians: dict[str, float | None]) -> tuple[str | None, dict[str, float | None]]:
    diffs: dict[str, float | None] = {}
    vals: list[float] = []
    for out_pid, top_pid in MATCHED_SURFACE_PAIRS:
        a = medians.get(out_pid)
        b = medians.get(top_pid)
        key = f"{top_pid}_minus_{out_pid}"
        if a is None or b is None:
            diffs[key] = None
        else:
            d = float(b) - float(a)
            diffs[key] = d
            vals.append(d)
    if len(vals) != 3:
        return None, diffs
    if all(v > 0 for v in vals):
        return "positive", diffs
    if all(v < 0 for v in vals):
        return "negative", diffs
    return "mixed", diffs


def write_geometry(polygons: dict[str, Polygon]) -> None:
    to_wgs = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)
    features = []
    for buffer_m in BUFFERS_M:
        for pid in PLOTS:
            inner = polygons[pid].buffer(-buffer_m)
            wgs = geom_transform(to_wgs.transform, inner)
            features.append({
                "type": "Feature",
                "properties": {
                    "plot_id": pid,
                    "inward_buffer_m": buffer_m,
                    "status": "fixed_preregistered_terrain_interior",
                },
                "geometry": mapping(wgs),
            })
    GEOMETRY.write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    result: dict[str, Any] = {
        "status": "started",
        "protocol": "tyrone_six_plot_terrain_screen_v1",
        "geometry_source": str(GEOMETRY_SOURCE),
        "source": {"stac_url": STAC_URL, "collection": COLLECTION, "gsd_m": GSD_M, "asset": ASSET},
        "analysis_crs": TARGET_CRS,
        "pixel_size_m": PIXEL_SIZE_M,
        "buffers_m": list(BUFFERS_M),
        "classifier_output_used": False,
        "pca_anomaly_used": False,
        "nb_depth_used": False,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    }

    polygons = load_polygons()
    grid = build_grid(polygons)
    masks, mask_counts = build_masks(polygons, grid)
    write_geometry(polygons)
    result["grid"] = {**grid, "transform": list(grid["transform"])[:6], "mask_pixel_counts": mask_counts}

    catalog = pystac_client.Client.open(STAC_URL)
    items = list(catalog.search(
        collections=[COLLECTION],
        bbox=bbox_wgs84(grid),
        query={"gsd": {"eq": GSD_M}},
    ).items())
    if not items:
        raise RuntimeError("no overlapping 10 m 3DEP seamless items")

    source_rows: list[dict[str, Any]] = []
    arrays: list[np.ndarray] = []
    for item in items:
        row = {
            "item_id": item.id,
            "datetime": item.datetime.isoformat() if item.datetime else item.properties.get("datetime"),
            "start_datetime": item.properties.get("start_datetime"),
            "end_datetime": item.properties.get("end_datetime"),
            "gsd": item.properties.get("gsd"),
            "read_status": "failed",
            "error": "",
        }
        try:
            arrays.append(read_item(item, grid))
            row["read_status"] = "ok"
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"[:1000]
        source_rows.append(row)
    if not arrays:
        raise RuntimeError("all DEM reads failed")

    dem = np.nanmedian(np.stack(arrays), axis=0)
    feature_arrays = derive_features(dem)
    result["candidate_item_count"] = len(items)
    result["read_success_count"] = len(arrays)
    result["read_failure_count"] = len(items) - len(arrays)

    plot_rows: list[dict[str, Any]] = []
    medians_by_buffer_feature: dict[tuple[float, str], dict[str, float | None]] = {}
    for buffer_m in BUFFERS_M:
        for feature_name in FEATURES:
            medians: dict[str, float | None] = {}
            for pid in PLOTS:
                s = stats(feature_arrays[feature_name], masks[buffer_m][pid])
                medians[pid] = s["median"]
                plot_rows.append({
                    "buffer_m": buffer_m,
                    "plot_id": pid,
                    "feature": feature_name,
                    **s,
                })
            medians_by_buffer_feature[(buffer_m, feature_name)] = medians

    evaluations: dict[str, Any] = {}
    for feature_name in FEATURES:
        per_buffer: dict[str, Any] = {}
        depth_dirs: list[str | None] = []
        surface_signs: list[str | None] = []
        for buffer_m in BUFFERS_M:
            medians = medians_by_buffer_feature[(buffer_m, feature_name)]
            ddir = depth_direction(medians)
            ssign, diffs = surface_sign(medians)
            depth_dirs.append(ddir)
            surface_signs.append(ssign)
            per_buffer[f"{int(buffer_m)}m"] = {
                "plot_medians": medians,
                "direct_depth_direction": ddir,
                "surface_top_minus_outslope_sign": ssign,
                "matched_depth_surface_differences": diffs,
            }
        direct_candidate = bool(
            depth_dirs[0] in ("increasing", "decreasing")
            and depth_dirs[0] == depth_dirs[1]
        )
        confounder = bool(
            surface_signs[0] in ("positive", "negative")
            and surface_signs[0] == surface_signs[1]
        )
        evaluations[feature_name] = {
            "buffers": per_buffer,
            "direct_depth_candidate": direct_candidate,
            "consistent_surface_confounder": confounder,
        }

    direct = [name for name, obj in evaluations.items() if obj["direct_depth_candidate"]]
    confounders = [name for name, obj in evaluations.items() if obj["consistent_surface_confounder"]]
    result["feature_evaluations"] = evaluations
    result["direct_depth_candidates"] = direct
    result["consistent_surface_confounders"] = confounders
    result["status"] = "direct_candidate_found" if direct else "no_direct_candidate_found"

    fields = ["buffer_m", "plot_id", "feature", "mean", "median", "std", "q25", "q75", "valid_pixel_count"]
    with PLOT_FEATURES.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: row.get(k) for k in fields} for row in plot_rows)

    source_fields = ["item_id", "datetime", "start_datetime", "end_datetime", "gsd", "read_status", "error"]
    with SOURCES.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=source_fields)
        writer.writeheader()
        writer.writerows({k: row.get(k) for k in source_fields} for row in source_rows)

    RESULT.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "candidate_item_count": result["candidate_item_count"],
        "read_success_count": result["read_success_count"],
        "direct_depth_candidates": direct,
        "consistent_surface_confounders": confounders,
        "feature_evaluations": evaluations,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
