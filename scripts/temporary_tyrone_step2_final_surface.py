#!/usr/bin/env python3
"""Temporary research helper for Tyrone Step 2 final-surface QA.

Downloads the public USGS 1 m DEM product for NM_SouthCentral_2018_D19,
crops a small area around Tailing Dam 3X, and extracts elevation-only
statistics for the six already-fixed WGS84 plot geometries.

This script does NOT calculate depth, fit/calibrate any model, read known depth
answers, or modify production application behavior.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_bounds, transform_geom
import requests

DEM_URL = (
    "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/"
    "NM_SouthCentral_2018_D19/TIFF/"
    "USGS_1M_12_x74y363_NM_SouthCentral_2018_D19.tif"
)

# Tight 3X box with surrounding terrain for later stable-ground comparison.
CLIP_BBOX_WGS84 = (-108.4270, 32.7160, -108.4120, 32.7270)
GEOMETRY_PATH = Path("data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson")
OUT = Path("artifacts/tyrone_step2_2018_dem")
OUT.mkdir(parents=True, exist_ok=True)
RAW = OUT / "source_1m_dem.tif"
CLIP = OUT / "tyrone_3x_2018_dem_clip.tif"
STATS = OUT / "plot_elevation_stats.csv"
META = OUT / "metadata.json"


def download() -> None:
    with requests.get(DEM_URL, stream=True, timeout=180) as r:
        r.raise_for_status()
        with RAW.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


def finite_values(arr: np.ma.MaskedArray) -> np.ndarray:
    values = np.asarray(arr.compressed(), dtype=np.float64)
    return values[np.isfinite(values)]


def main() -> int:
    download()

    with rasterio.open(RAW) as src:
        source_crs = src.crs
        source_bounds = tuple(src.bounds)
        source_res = tuple(src.res)
        source_shape = (src.height, src.width)
        source_nodata = src.nodata

        clip_bounds_src = transform_bounds(
            "EPSG:4326", src.crs, *CLIP_BBOX_WGS84, densify_pts=21
        )
        left = max(clip_bounds_src[0], src.bounds.left)
        bottom = max(clip_bounds_src[1], src.bounds.bottom)
        right = min(clip_bounds_src[2], src.bounds.right)
        top = min(clip_bounds_src[3], src.bounds.top)
        if not (left < right and bottom < top):
            raise RuntimeError("Requested 3X clip does not intersect source DEM")

        window = rasterio.windows.from_bounds(left, bottom, right, top, src.transform)
        window = window.round_offsets().round_lengths()
        data = src.read(1, window=window, masked=True)
        transform = src.window_transform(window)

        profile = src.profile.copy()
        profile.update(
            height=data.shape[0],
            width=data.shape[1],
            transform=transform,
            compress="deflate",
            tiled=True,
        )
        with rasterio.open(CLIP, "w", **profile) as dst:
            dst.write(data.filled(src.nodata if src.nodata is not None else np.nan), 1)

    geometry = json.loads(GEOMETRY_PATH.read_text(encoding="utf-8"))
    rows = []
    # Reopen the clipped DEM and use geometry only. Depth properties are never read.
    with rasterio.open(CLIP) as dem:
        for feature in geometry["features"]:
            plot_id = feature["properties"]["plot_id"]
            geom_src = transform_geom("EPSG:4326", dem.crs, feature["geometry"], precision=9)
            arr, _ = mask(dem, [geom_src], crop=True, filled=False)
            vals = finite_values(arr[0])
            if vals.size == 0:
                raise RuntimeError(f"No valid 2018 DEM pixels for {plot_id}")
            rows.append(
                {
                    "plot_id": plot_id,
                    "valid_pixels": int(vals.size),
                    "mean_m": float(np.mean(vals)),
                    "median_m": float(np.median(vals)),
                    "std_m": float(np.std(vals)),
                    "p05_m": float(np.quantile(vals, 0.05)),
                    "p95_m": float(np.quantile(vals, 0.95)),
                    "min_m": float(np.min(vals)),
                    "max_m": float(np.max(vals)),
                }
            )

    with STATS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with rasterio.open(CLIP) as clip:
        clip_vals = finite_values(clip.read(1, masked=True))
        clip_meta = {
            "crs": str(clip.crs),
            "bounds": list(clip.bounds),
            "resolution": list(clip.res),
            "shape": [clip.height, clip.width],
            "valid_pixels": int(clip_vals.size),
            "min_m": float(np.min(clip_vals)),
            "max_m": float(np.max(clip_vals)),
        }

    meta = {
        "status": "STEP2_2018_FINAL_SURFACE_EXTRACTED",
        "source_url": DEM_URL,
        "source_project": "NM_SouthCentral_2018_D19",
        "source_product": "USGS_1M_12_x74y363_NM_SouthCentral_2018_D19",
        "clip_bbox_wgs84": list(CLIP_BBOX_WGS84),
        "source_crs": str(source_crs),
        "source_bounds": list(source_bounds),
        "source_resolution": list(source_res),
        "source_shape": list(source_shape),
        "source_nodata": source_nodata,
        "clip": clip_meta,
        "plot_stats": rows,
        "known_depth_values_read": False,
        "depth_calculated": False,
        "model_fit_or_calibrated": False,
        "classifier_modified": False,
        "nb_formula_modified": False,
        "ui_modified": False,
    }
    META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2))

    # Avoid uploading the full ~233 MB source tile; only the clipped DEM + small tables persist.
    RAW.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
