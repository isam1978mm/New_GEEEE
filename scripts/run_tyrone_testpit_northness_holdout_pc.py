#!/usr/bin/env python3
"""Preregistered independent Tyrone test-pit northness holdout.

Uses only the already frozen AS-BUILT exact-depth points and the same public
Microsoft Planetary Computer 3DEP northness definition as the six-plot terrain
development screen. No NB_DEPTH, classifier/PCA depth evidence, Earth Engine,
model fitting, or app-depth enablement.
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
from rasterio.transform import Affine
from rasterio.vrt import WarpedVRT
from scipy.stats import rankdata

OUT = Path("artifacts/tyrone_testpit_northness_holdout_pc")
OUT.mkdir(parents=True, exist_ok=True)
RESULT = OUT / "result.json"
POINT_RESULTS = OUT / "point_results.csv"
SOURCES = OUT / "source_items.csv"

POINTS_SOURCE = Path("data/depth_reference/tyrone_3x_testpit_northness_holdout_points_v1.csv")
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "3dep-seamless"
ASSET = "data"
GSD_M = 10
TARGET_CRS = "EPSG:32612"
PIXEL_SIZE_M = 10.0
MARGIN_M = 80.0
RADII_M = (10.0, 20.0)
MIN_POINTS = 20
PERMUTATIONS = 100_000
SEED = 314101
MIN_RHO = 0.30
MAX_P = 0.05
NODATA = -999999.0


def load_points() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with POINTS_SOURCE.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if str(row.get("primary_holdout", "")).strip().lower() != "true":
                continue
            rows.append({
                "id": row["id"],
                "depth_in": float(row["depth_in"]),
                "utm_e_m": float(row["utm_e_m"]),
                "utm_n_m": float(row["utm_n_m"]),
                "longitude": float(row["longitude"]),
                "latitude": float(row["latitude"]),
            })
    if len(rows) < MIN_POINTS:
        raise RuntimeError(f"INSUFFICIENT_INDEPENDENT_POINTS: {len(rows)} < {MIN_POINTS}")
    return rows


def build_grid(points: list[dict[str, Any]]) -> dict[str, Any]:
    xs = [p["utm_e_m"] for p in points]
    ys = [p["utm_n_m"] for p in points]
    left = math.floor((min(xs) - MARGIN_M) / PIXEL_SIZE_M) * PIXEL_SIZE_M
    bottom = math.floor((min(ys) - MARGIN_M) / PIXEL_SIZE_M) * PIXEL_SIZE_M
    right = math.ceil((max(xs) + MARGIN_M) / PIXEL_SIZE_M) * PIXEL_SIZE_M
    top = math.ceil((max(ys) + MARGIN_M) / PIXEL_SIZE_M) * PIXEL_SIZE_M
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


def bbox_wgs84(grid: dict[str, Any]) -> list[float]:
    left, bottom, right, top = grid["bounds"]
    to_wgs = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)
    corners = [
        to_wgs.transform(left, bottom),
        to_wgs.transform(right, bottom),
        to_wgs.transform(right, top),
        to_wgs.transform(left, top),
    ]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    return [min(xs), min(ys), max(xs), max(ys)]


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


def derive_northness(dem: np.ndarray) -> np.ndarray:
    valid = np.isfinite(dem)
    if int(valid.sum()) < 100:
        raise RuntimeError("insufficient DEM coverage")
    dzdy, dzdx = np.gradient(dem, PIXEL_SIZE_M, PIXEL_SIZE_M)
    mag = np.hypot(dzdx, dzdy)
    northness = np.zeros_like(dem, dtype=float)
    nonflat = np.isfinite(mag) & (mag > 0)
    northness[nonflat] = -dzdy[nonflat] / mag[nonflat]
    northness[~valid] = np.nan
    return northness


def pixel_centers(grid: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    t = grid["transform"]
    xs = t.c + (np.arange(grid["width"]) + 0.5) * t.a
    ys = t.f + (np.arange(grid["height"]) + 0.5) * t.e
    return np.meshgrid(xs, ys)


def point_median(
    northness: np.ndarray,
    xx: np.ndarray,
    yy: np.ndarray,
    e: float,
    n: float,
    radius_m: float,
) -> tuple[float | None, int]:
    mask = ((xx - e) ** 2 + (yy - n) ** 2) <= radius_m ** 2
    values = northness[mask]
    values = values[np.isfinite(values)]
    if values.size == 0:
        return None, 0
    return float(np.median(values)), int(values.size)


def spearman_and_permutation(
    depths: np.ndarray,
    values: np.ndarray,
    permutations: int,
    seed: int,
) -> dict[str, float | int]:
    if depths.size != values.size or depths.size < MIN_POINTS:
        raise RuntimeError("invalid primary vectors")
    depth_rank = rankdata(depths, method="average").astype(np.float64)
    value_rank = rankdata(values, method="average").astype(np.float64)
    dr = depth_rank - depth_rank.mean()
    vr = value_rank - value_rank.mean()
    denom = math.sqrt(float(np.dot(dr, dr) * np.dot(vr, vr)))
    if denom == 0:
        raise RuntimeError("degenerate Spearman ranks")
    rho = float(np.dot(dr, vr) / denom)

    rng = np.random.default_rng(seed)
    ge = 0
    batch = 5000
    done = 0
    while done < permutations:
        k = min(batch, permutations - done)
        keys = rng.random((k, depths.size))
        order = np.argsort(keys, axis=1)
        perm_dr = dr[order]
        perm_rho = (perm_dr @ vr) / denom
        ge += int(np.count_nonzero(perm_rho >= rho))
        done += k
    p = float((ge + 1) / (permutations + 1))
    return {
        "n": int(depths.size),
        "rho": rho,
        "permutations": permutations,
        "permutation_ge_count": ge,
        "one_sided_p": p,
    }


def main() -> int:
    result: dict[str, Any] = {
        "status": "started",
        "protocol": "tyrone_testpit_northness_holdout_v1",
        "points_source": str(POINTS_SOURCE),
        "source": {
            "provider": "Microsoft Planetary Computer",
            "collection": COLLECTION,
            "gsd_m": GSD_M,
            "asset": ASSET,
        },
        "analysis_crs": TARGET_CRS,
        "pixel_size_m": PIXEL_SIZE_M,
        "neighborhood_radii_m": list(RADII_M),
        "minimum_primary_holdout_points": MIN_POINTS,
        "expected_direction": "positive",
        "minimum_rho": MIN_RHO,
        "maximum_p_value": MAX_P,
        "permutations": PERMUTATIONS,
        "random_seed": SEED,
        "classifier_output_used": False,
        "pca_anomaly_used": False,
        "nb_depth_used": False,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "training_started": False,
        "app_depth_enabled": False,
    }

    points = load_points()
    result["primary_point_count"] = len(points)
    grid = build_grid(points)
    result["grid"] = {
        "crs": grid["crs"],
        "width": grid["width"],
        "height": grid["height"],
        "transform": list(grid["transform"])[:6],
        "bounds": list(grid["bounds"]),
    }

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
    northness = derive_northness(dem)
    xx, yy = pixel_centers(grid)

    point_rows: list[dict[str, Any]] = []
    for p in points:
        row = dict(p)
        for radius in RADII_M:
            med, npx = point_median(
                northness, xx, yy, p["utm_e_m"], p["utm_n_m"], radius
            )
            row[f"northness_{int(radius)}m"] = med
            row[f"valid_pixels_{int(radius)}m"] = npx
        point_rows.append(row)

    tests: dict[str, Any] = {}
    for radius in RADII_M:
        key = f"{int(radius)}m"
        usable = [
            r for r in point_rows
            if r[f"northness_{int(radius)}m"] is not None
        ]
        if len(usable) < MIN_POINTS:
            tests[key] = {
                "n": len(usable),
                "passed": False,
                "decision": "INSUFFICIENT_INDEPENDENT_POINTS",
            }
            continue
        depths = np.asarray([r["depth_in"] for r in usable], dtype=float)
        vals = np.asarray([r[f"northness_{int(radius)}m"] for r in usable], dtype=float)
        stat = spearman_and_permutation(depths, vals, PERMUTATIONS, SEED)
        stat["passed"] = bool(stat["rho"] >= MIN_RHO and stat["one_sided_p"] <= MAX_P)
        tests[key] = stat

    overall_pass = all(
        tests.get(f"{int(r)}m", {}).get("passed") is True for r in RADII_M
    )
    result.update({
        "candidate_item_count": len(items),
        "read_success_count": len(arrays),
        "read_failure_count": len(items) - len(arrays),
        "tests": tests,
        "passed": overall_pass,
        "decision": (
            "NORTHNESS_HOLDOUT_PASSED_SITE_SPECIFIC_CANDIDATE_ONLY"
            if overall_pass
            else "NORTHNESS_HOLDOUT_FAILED_CLOSE_WITHOUT_RESCUE"
        ),
        "next_route": (
            "REQUIRE_FURTHER_INDEPENDENT_SITE_VALIDATION_NO_TYRONE_ONLY_DEPTH_FORMULA"
            if overall_pass
            else "PREREGISTER_THERMAL_FEATURE_FAMILY"
        ),
        "status": "ok",
    })

    with SOURCES.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item_id", "datetime", "gsd", "read_status", "error"])
        writer.writeheader()
        writer.writerows(source_rows)

    fields = [
        "id", "depth_in", "utm_e_m", "utm_n_m", "longitude", "latitude",
        "northness_10m", "valid_pixels_10m", "northness_20m", "valid_pixels_20m",
    ]
    with POINT_RESULTS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{k: r.get(k) for k in fields} for r in point_rows])

    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
