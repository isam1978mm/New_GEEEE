from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import geometry_mask

TARGET_OSM_WAY_ID = 714462943
TARGET_SURVEY_ID = "RS-33-039"
TARGET_SURVEY_URL = "https://maps-and-records.tucsonaz.gov/records-survey/details/4551"

PRE_PROJECT = "USGS_LPC_AZ_Eastern_PimaCO_2015_LAS_2017"
POST_PROJECT = "AZ_PimaCo_2_2021"
EPT_ROOT = "https://s3-us-west-2.amazonaws.com/usgs-lidar-public"
PRE_EPT_URL = f"{EPT_ROOT}/{PRE_PROJECT}/ept.json"
POST_EPT_URL = f"{EPT_ROOT}/{POST_PROJECT}/ept.json"

OUTPUT_CRS = "EPSG:32612"
EPT_QUERY_CRS = "EPSG:3857"
NODATA = -9999.0
NOMINAL_COVER_M = 0.9144

FROZEN_GATES = {
    "stable_rmse_m_max": 0.15,
    "stable_abs_median_m_max": 0.05,
    "stable_p95_abs_m_max": 0.30,
    "plane_drift_m_max": 0.10,
}


def _bounds_string(bounds: tuple[float, float, float, float]) -> str:
    xmin, ymin, xmax, ymax = bounds
    return f"([{xmin:.3f}, {xmax:.3f}], [{ymin:.3f}, {ymax:.3f}])"


def _snap_bounds(
    bounds: tuple[float, float, float, float], resolution: float
) -> tuple[float, float, float, float]:
    xmin, ymin, xmax, ymax = bounds
    return (
        math.floor(xmin / resolution) * resolution,
        math.floor(ymin / resolution) * resolution,
        math.ceil(xmax / resolution) * resolution,
        math.ceil(ymax / resolution) * resolution,
    )


def _transform_bounds(
    bounds: tuple[float, float, float, float], src: str, dst: str
) -> tuple[float, float, float, float]:
    xmin, ymin, xmax, ymax = bounds
    transformer = Transformer.from_crs(src, dst, always_xy=True)
    points = [
        transformer.transform(xmin, ymin),
        transformer.transform(xmin, ymax),
        transformer.transform(xmax, ymin),
        transformer.transform(xmax, ymax),
    ]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def _iter_polygon_positions(geometry: dict[str, Any]):
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if geom_type == "Polygon":
        polygons = [coords]
    elif geom_type == "MultiPolygon":
        polygons = coords
    else:
        raise ValueError("target geometry must be Polygon or MultiPolygon")
    if not isinstance(polygons, list):
        raise ValueError("target geometry has invalid coordinates")
    for polygon in polygons:
        if not isinstance(polygon, list):
            continue
        for ring in polygon:
            if not isinstance(ring, list):
                continue
            for position in ring:
                if (
                    isinstance(position, list)
                    and len(position) >= 2
                    and isinstance(position[0], (int, float))
                    and isinstance(position[1], (int, float))
                ):
                    yield float(position[0]), float(position[1])


def geometry_bounds_wgs84(geometry: dict[str, Any]) -> tuple[float, float, float, float]:
    positions = list(_iter_polygon_positions(geometry))
    if len(positions) < 4:
        raise ValueError("target geometry does not contain enough vertices")
    xs = [position[0] for position in positions]
    ys = [position[1] for position in positions]
    return min(xs), min(ys), max(xs), max(ys)


def buffered_analysis_bounds(
    geometry: dict[str, Any], *, buffer_m: float, resolution_m: float
) -> tuple[float, float, float, float]:
    source_bounds = geometry_bounds_wgs84(geometry)
    xmin, ymin, xmax, ymax = _transform_bounds(source_bounds, "EPSG:4326", OUTPUT_CRS)
    return _snap_bounds(
        (xmin - buffer_m, ymin - buffer_m, xmax + buffer_m, ymax + buffer_m),
        resolution_m,
    )


def build_dtm_pipeline(
    *,
    ept_url: str,
    output_tif: Path,
    analysis_bounds_utm: tuple[float, float, float, float],
    resolution_m: float,
) -> dict[str, Any]:
    reader_bounds = _transform_bounds(analysis_bounds_utm, OUTPUT_CRS, EPT_QUERY_CRS)
    return {
        "pipeline": [
            {
                "type": "readers.ept",
                "filename": ept_url,
                "bounds": _bounds_string(reader_bounds),
            },
            {"type": "filters.range", "limits": "Classification[2:2]"},
            {"type": "filters.reprojection", "out_srs": OUTPUT_CRS},
            {
                "type": "writers.gdal",
                "filename": str(output_tif),
                "resolution": resolution_m,
                "output_type": "idw",
                "window_size": 6,
                "nodata": NODATA,
                "data_type": "float",
                "bounds": _bounds_string(analysis_bounds_utm),
                "gdalopts": "tiled=yes,compress=deflate",
            },
        ]
    }


def _fetch_osm_way_geometry(way_id: int) -> dict[str, Any]:
    url = f"https://www.openstreetmap.org/api/0.6/way/{way_id}/full"
    with urllib.request.urlopen(url, timeout=30) as response:
        xml_payload = response.read()
    root = ET.fromstring(xml_payload)
    nodes: dict[int, tuple[float, float]] = {}
    for node in root.findall("node"):
        nodes[int(node.attrib["id"])] = (
            float(node.attrib["lon"]),
            float(node.attrib["lat"]),
        )
    way = next(
        (
            item
            for item in root.findall("way")
            if int(item.attrib.get("id", "-1")) == way_id
        ),
        None,
    )
    if way is None:
        raise RuntimeError(f"OSM way {way_id} was not returned")
    ring = [nodes[int(nd.attrib["ref"])] for nd in way.findall("nd")]
    if len(ring) < 4:
        raise RuntimeError("OSM landfill polygon has too few vertices")
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    return {"type": "Polygon", "coordinates": [[list(position) for position in ring]]}


def load_target_geometry(path: Path | None) -> tuple[dict[str, Any], str]:
    if path is not None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("type") == "FeatureCollection":
            features = payload.get("features") or []
            if len(features) != 1:
                raise ValueError("target GeoJSON FeatureCollection must contain exactly one feature")
            geometry = features[0].get("geometry")
        elif payload.get("type") == "Feature":
            geometry = payload.get("geometry")
        else:
            geometry = payload
        if not isinstance(geometry, dict):
            raise ValueError("target GeoJSON is missing geometry")
        geometry_bounds_wgs84(geometry)
        return geometry, f"user_supplied:{path.name}"
    geometry = _fetch_osm_way_geometry(TARGET_OSM_WAY_ID)
    return geometry, f"osm_way_{TARGET_OSM_WAY_ID}_provisional"


def _write_feature(path: Path, geometry: dict[str, Any], source: str) -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "site": "Tangerine Landfill",
                    "source": source,
                    "survey_authority": TARGET_SURVEY_ID,
                    "survey_reference_url": TARGET_SURVEY_URL,
                    "geometry_status": (
                        "provisional_execution_mask"
                        if source.startswith("osm_way_")
                        else "operator_supplied_review_required"
                    ),
                },
                "geometry": geometry,
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def prepare(
    *,
    output_dir: Path,
    target_geojson: Path | None,
    buffer_m: float,
    resolution_m: float,
    execute: bool,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    geometry, geometry_source = load_target_geometry(target_geojson)
    target_path = output_dir / "tangerine_target.geojson"
    _write_feature(target_path, geometry, geometry_source)
    bounds = buffered_analysis_bounds(
        geometry, buffer_m=buffer_m, resolution_m=resolution_m
    )
    pre_tif = output_dir / "tangerine_2015_ground_dtm.tif"
    post_tif = output_dir / "tangerine_2021_ground_dtm.tif"
    pre_pipeline = build_dtm_pipeline(
        ept_url=PRE_EPT_URL,
        output_tif=pre_tif,
        analysis_bounds_utm=bounds,
        resolution_m=resolution_m,
    )
    post_pipeline = build_dtm_pipeline(
        ept_url=POST_EPT_URL,
        output_tif=post_tif,
        analysis_bounds_utm=bounds,
        resolution_m=resolution_m,
    )
    pre_pipeline_path = output_dir / "pdal_2015_ground_dtm.json"
    post_pipeline_path = output_dir / "pdal_2021_ground_dtm.json"
    pre_pipeline_path.write_text(json.dumps(pre_pipeline, indent=2), encoding="utf-8")
    post_pipeline_path.write_text(json.dumps(post_pipeline, indent=2), encoding="utf-8")
    result = {
        "status": "prepared",
        "geometry_source": geometry_source,
        "geometry_final_for_claim": not geometry_source.startswith("osm_way_"),
        "analysis_bounds_utm12n": list(bounds),
        "resolution_m": resolution_m,
        "pre_project": PRE_PROJECT,
        "post_project": POST_PROJECT,
        "pre_ept_url": PRE_EPT_URL,
        "post_ept_url": POST_EPT_URL,
        "target_geojson": str(target_path),
        "pre_pipeline": str(pre_pipeline_path),
        "post_pipeline": str(post_pipeline_path),
        "pre_dtm": str(pre_tif),
        "post_dtm": str(post_tif),
    }
    if execute:
        pdal = shutil.which("pdal")
        if not pdal:
            raise RuntimeError(
                "PDAL executable is required for --execute. "
                "Install PDAL in a separate conda-forge analysis environment."
            )
        for pipeline_path in (pre_pipeline_path, post_pipeline_path):
            subprocess.run([pdal, "pipeline", str(pipeline_path)], check=True)
        result["status"] = "executed"
    (output_dir / "prepare_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    return result


def _binary_window_sum(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask.astype(np.int32)
    padded = np.pad(mask.astype(np.int32), radius, mode="constant")
    integral = np.pad(padded, ((1, 0), (1, 0)), mode="constant")
    integral = integral.cumsum(axis=0).cumsum(axis=1)
    size = 2 * radius + 1
    return (
        integral[size:, size:]
        - integral[:-size, size:]
        - integral[size:, :-size]
        + integral[:-size, :-size]
    )


def binary_dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask.copy()
    return _binary_window_sum(mask, radius) > 0


def binary_erode(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask.copy()
    size = 2 * radius + 1
    return _binary_window_sum(mask, radius) == size * size


def _bilinear_shift(array: np.ndarray, dx_px: float, dy_px: float) -> np.ndarray:
    rows, cols = array.shape
    y, x = np.indices((rows, cols), dtype=np.float64)
    src_x = x - dx_px
    src_y = y - dy_px
    x0 = np.floor(src_x).astype(np.int64)
    y0 = np.floor(src_y).astype(np.int64)
    x1 = x0 + 1
    y1 = y0 + 1
    valid = (x0 >= 0) & (y0 >= 0) & (x1 < cols) & (y1 < rows)
    output = np.full(array.shape, np.nan, dtype=np.float64)
    if not np.any(valid):
        return output
    fx = src_x - x0
    fy = src_y - y0
    indices = np.where(valid)
    q00 = array[y0[indices], x0[indices]]
    q10 = array[y0[indices], x1[indices]]
    q01 = array[y1[indices], x0[indices]]
    q11 = array[y1[indices], x1[indices]]
    finite = np.isfinite(q00) & np.isfinite(q10) & np.isfinite(q01) & np.isfinite(q11)
    vals = (
        q00 * (1 - fx[indices]) * (1 - fy[indices])
        + q10 * fx[indices] * (1 - fy[indices])
        + q01 * (1 - fx[indices]) * fy[indices]
        + q11 * fx[indices] * fy[indices]
    )
    output[indices[0][finite], indices[1][finite]] = vals[finite]
    return output


def _robust_plane(
    residual: np.ndarray,
    mask: np.ndarray,
    *,
    max_points: int = 200_000,
    iterations: int = 4,
) -> tuple[np.ndarray, dict[str, float]]:
    rows, cols = np.where(mask & np.isfinite(residual))
    if len(rows) < 1000:
        raise RuntimeError("too few stable pixels for robust plane fit")
    step = max(1, math.ceil(len(rows) / max_points))
    rows = rows[::step]
    cols = cols[::step]
    z = residual[rows, cols]
    x_scale = max(float(residual.shape[1] - 1), 1.0)
    y_scale = max(float(residual.shape[0] - 1), 1.0)
    x = cols.astype(np.float64) / x_scale
    y = rows.astype(np.float64) / y_scale
    keep = np.isfinite(z)
    coef = np.zeros(3, dtype=np.float64)
    for _ in range(iterations):
        matrix = np.column_stack([np.ones(np.sum(keep)), x[keep], y[keep]])
        coef, *_ = np.linalg.lstsq(matrix, z[keep], rcond=None)
        fitted = coef[0] + coef[1] * x + coef[2] * y
        errors = z - fitted
        median = float(np.median(errors[keep]))
        mad = float(np.median(np.abs(errors[keep] - median)))
        sigma = 1.4826 * mad
        if sigma <= 1e-8:
            break
        keep = keep & (np.abs(errors - median) <= 3.5 * sigma)
        if np.sum(keep) < 1000:
            raise RuntimeError("robust plane clipping left too few stable pixels")
    grid_y, grid_x = np.indices(residual.shape, dtype=np.float64)
    plane = coef[0] + coef[1] * (grid_x / x_scale) + coef[2] * (grid_y / y_scale)
    return plane, {
        "offset_m": float(coef[0]),
        "x_edge_delta_m": float(coef[1]),
        "y_edge_delta_m": float(coef[2]),
        "fit_points": int(np.sum(keep)),
    }


def _sample_shifted_points(
    array: np.ndarray,
    rows: np.ndarray,
    cols: np.ndarray,
    dx_px: float,
    dy_px: float,
) -> np.ndarray:
    src_x = cols.astype(np.float64) - dx_px
    src_y = rows.astype(np.float64) - dy_px
    x0 = np.floor(src_x).astype(np.int64)
    y0 = np.floor(src_y).astype(np.int64)
    x1 = x0 + 1
    y1 = y0 + 1
    valid = (
        (x0 >= 0)
        & (y0 >= 0)
        & (x1 < array.shape[1])
        & (y1 < array.shape[0])
    )
    result = np.full(rows.shape, np.nan, dtype=np.float64)
    if not np.any(valid):
        return result
    q00 = array[y0[valid], x0[valid]]
    q10 = array[y0[valid], x1[valid]]
    q01 = array[y1[valid], x0[valid]]
    q11 = array[y1[valid], x1[valid]]
    finite = np.isfinite(q00) & np.isfinite(q10) & np.isfinite(q01) & np.isfinite(q11)
    valid_indices = np.where(valid)[0][finite]
    fx = src_x[valid_indices] - x0[valid_indices]
    fy = src_y[valid_indices] - y0[valid_indices]
    result[valid_indices] = (
        q00[finite] * (1 - fx) * (1 - fy)
        + q10[finite] * fx * (1 - fy)
        + q01[finite] * (1 - fx) * fy
        + q11[finite] * fx * fy
    )
    return result


def _robust_plane_points(
    rows: np.ndarray,
    cols: np.ndarray,
    z: np.ndarray,
    shape: tuple[int, int],
    *,
    iterations: int = 3,
) -> tuple[np.ndarray, np.ndarray]:
    x_scale = max(float(shape[1] - 1), 1.0)
    y_scale = max(float(shape[0] - 1), 1.0)
    x = cols.astype(np.float64) / x_scale
    y = rows.astype(np.float64) / y_scale
    keep = np.isfinite(z)
    if np.sum(keep) < 1000:
        raise RuntimeError("too few finite stable samples for shift scoring")
    coef = np.zeros(3, dtype=np.float64)
    for _ in range(iterations):
        matrix = np.column_stack([np.ones(np.sum(keep)), x[keep], y[keep]])
        coef, *_ = np.linalg.lstsq(matrix, z[keep], rcond=None)
        fitted = coef[0] + coef[1] * x + coef[2] * y
        errors = z - fitted
        median = float(np.median(errors[keep]))
        mad = float(np.median(np.abs(errors[keep] - median)))
        sigma = 1.4826 * mad
        if sigma <= 1e-8:
            break
        keep = keep & (np.abs(errors - median) <= 3.5 * sigma)
        if np.sum(keep) < 1000:
            raise RuntimeError("shift-score clipping left too few samples")
    fitted = coef[0] + coef[1] * x + coef[2] * y
    return fitted, keep


def _shift_score_samples(
    pre: np.ndarray,
    post: np.ndarray,
    rows: np.ndarray,
    cols: np.ndarray,
    dx: float,
    dy: float,
) -> float:
    post_values = _sample_shifted_points(post, rows, cols, dx, dy)
    residual = post_values - pre[rows, cols]
    try:
        fitted, keep = _robust_plane_points(rows, cols, residual, pre.shape)
    except RuntimeError:
        return float("inf")
    corrected = residual - fitted
    values = corrected[keep & np.isfinite(corrected)]
    if values.size < 1000:
        return float("inf")
    return float(np.median(np.abs(values - np.median(values))))


def _best_shift(
    pre: np.ndarray, post: np.ndarray, stable_mask: np.ndarray
) -> tuple[float, float]:
    rows, cols = np.where(stable_mask & np.isfinite(pre) & np.isfinite(post))
    if rows.size < 5000:
        raise RuntimeError("too few stable pixels for horizontal co-registration")
    step = max(1, math.ceil(rows.size / 30_000))
    rows = rows[::step]
    cols = cols[::step]
    best = (float("inf"), 0.0, 0.0)
    for dy in np.arange(-3.0, 3.01, 1.0):
        for dx in np.arange(-3.0, 3.01, 1.0):
            score = _shift_score_samples(pre, post, rows, cols, float(dx), float(dy))
            if score < best[0]:
                best = (score, float(dx), float(dy))
    _, best_dx, best_dy = best
    fine_best = best
    for dy in np.arange(best_dy - 0.75, best_dy + 0.751, 0.25):
        for dx in np.arange(best_dx - 0.75, best_dx + 0.751, 0.25):
            score = _shift_score_samples(pre, post, rows, cols, float(dx), float(dy))
            if score < fine_best[0]:
                fine_best = (score, float(dx), float(dy))
    return fine_best[1], fine_best[2]


def _reproject_geometry(
    geometry: dict[str, Any], src: str, dst: str
) -> dict[str, Any]:
    transformer = Transformer.from_crs(src, dst, always_xy=True)

    def transform_position(position):
        x, y = transformer.transform(float(position[0]), float(position[1]))
        return [x, y]

    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if geom_type == "Polygon":
        new_coords = [
            [transform_position(position) for position in ring] for ring in coords
        ]
    elif geom_type == "MultiPolygon":
        new_coords = [
            [
                [transform_position(position) for position in ring]
                for ring in polygon
            ]
            for polygon in coords
        ]
    else:
        raise ValueError("target geometry must be Polygon or MultiPolygon")
    return {"type": geom_type, "coordinates": new_coords}


def analyze(
    *,
    pre_dtm: Path,
    post_dtm: Path,
    target_geojson: Path,
    output_json: Path,
    target_erode_m: float,
    stable_exclusion_m: float,
) -> dict[str, Any]:
    with rasterio.open(pre_dtm) as pre_src, rasterio.open(post_dtm) as post_src:
        if pre_src.crs != post_src.crs:
            raise RuntimeError("pre/post DTM CRS mismatch")
        if pre_src.transform != post_src.transform:
            raise RuntimeError("pre/post DTM grid transform mismatch")
        if pre_src.width != post_src.width or pre_src.height != post_src.height:
            raise RuntimeError("pre/post DTM raster size mismatch")
        pre = pre_src.read(1).astype(np.float64)
        post = post_src.read(1).astype(np.float64)
        pre[(~np.isfinite(pre)) | (pre == pre_src.nodata)] = np.nan
        post[(~np.isfinite(post)) | (post == post_src.nodata)] = np.nan
        resolution_m = abs(float(pre_src.transform.a))
        transform = pre_src.transform
        crs = pre_src.crs

    target_payload = json.loads(target_geojson.read_text(encoding="utf-8"))
    feature = target_payload["features"][0]
    target_geometry = _reproject_geometry(feature["geometry"], "EPSG:4326", str(crs))
    target_mask = geometry_mask(
        [target_geometry], out_shape=pre.shape, transform=transform, invert=True
    )
    erode_px = max(0, int(round(target_erode_m / resolution_m)))
    exclude_px = max(0, int(round(stable_exclusion_m / resolution_m)))
    target_inner = binary_erode(target_mask, erode_px)
    target_excluded = binary_dilate(target_mask, exclude_px)
    common_valid = np.isfinite(pre) & np.isfinite(post)
    stable_mask = common_valid & (~target_excluded)
    if np.sum(target_inner & common_valid) < 500:
        raise RuntimeError("too few valid target-interior pixels")
    if np.sum(stable_mask) < 5000:
        raise RuntimeError("too few stable-ground pixels")

    dx_px, dy_px = _best_shift(pre, post, stable_mask)
    shifted_post = _bilinear_shift(post, dx_px, dy_px)
    raw_diff = shifted_post - pre
    fit_mask = stable_mask & np.isfinite(raw_diff)
    plane, plane_meta = _robust_plane(raw_diff, fit_mask)
    corrected = raw_diff - plane
    stable_values = corrected[fit_mask]
    target_valid = target_inner & np.isfinite(corrected)
    target_values = corrected[target_valid]

    stable_rmse = float(np.sqrt(np.mean(stable_values**2)))
    stable_abs_median = abs(float(np.median(stable_values)))
    stable_p95_abs = float(np.percentile(np.abs(stable_values), 95))
    target_plane = plane[target_inner]
    plane_drift = float(np.nanmax(target_plane) - np.nanmin(target_plane))
    gates = {
        "stable_rmse_m": {
            "value": stable_rmse,
            "threshold_max": FROZEN_GATES["stable_rmse_m_max"],
            "pass": stable_rmse <= FROZEN_GATES["stable_rmse_m_max"],
        },
        "stable_abs_median_m": {
            "value": stable_abs_median,
            "threshold_max": FROZEN_GATES["stable_abs_median_m_max"],
            "pass": stable_abs_median <= FROZEN_GATES["stable_abs_median_m_max"],
        },
        "stable_p95_abs_m": {
            "value": stable_p95_abs,
            "threshold_max": FROZEN_GATES["stable_p95_abs_m_max"],
            "pass": stable_p95_abs <= FROZEN_GATES["stable_p95_abs_m_max"],
        },
        "plane_drift_m": {
            "value": plane_drift,
            "threshold_max": FROZEN_GATES["plane_drift_m_max"],
            "pass": plane_drift <= FROZEN_GATES["plane_drift_m_max"],
        },
    }
    residual_gate_pass = all(item["pass"] for item in gates.values())
    result = {
        "schema": "tangerine_lidar_execution_v1",
        "site": "Tangerine Landfill",
        "pre_project": PRE_PROJECT,
        "post_project": POST_PROJECT,
        "output_crs": str(crs),
        "resolution_m": resolution_m,
        "target_geometry_source": feature.get("properties", {}).get("source", "unknown"),
        "target_geometry_final_for_claim": (
            feature.get("properties", {}).get("geometry_status")
            != "provisional_execution_mask"
        ),
        "nominal_cover_m": NOMINAL_COVER_M,
        "coregistration": {
            "post_shift_x_pixels": dx_px,
            "post_shift_y_pixels": dy_px,
            "post_shift_x_m": dx_px * resolution_m,
            "post_shift_y_m": -dy_px * resolution_m,
            "vertical_plane": plane_meta,
        },
        "stable_ground": {
            "pixel_count": int(stable_values.size),
            "gates": gates,
            "all_frozen_residual_gates_pass": residual_gate_pass,
        },
        "target": {
            "pixel_count": int(target_values.size),
            "mean_change_m": float(np.mean(target_values)),
            "median_change_m": float(np.median(target_values)),
            "p05_change_m": float(np.percentile(target_values, 5)),
            "p10_change_m": float(np.percentile(target_values, 10)),
            "p90_change_m": float(np.percentile(target_values, 90)),
            "p95_change_m": float(np.percentile(target_values, 95)),
            "median_minus_nominal_m": float(np.median(target_values) - NOMINAL_COVER_M),
        },
        "interpretation": (
            "execution_residual_gates_pass_target_change_descriptive_only"
            if residual_gate_pass
            else "execution_residual_gates_fail_do_not_interpret_target_depth"
        ),
        "warnings": [
            "nominal_3ft_cover_is_design_regulatory_not_independent_measured_mean",
            "post_epoch_is_2021_about_five_years_after_2016_closure_settlement_may_reduce_apparent_change",
            "stable_ground_coregistration_removes_local_offset_and_planar_drift_before_target_differencing",
        ],
    }
    if not result["target_geometry_final_for_claim"]:
        result["warnings"].append(
            "target_geometry_is_osm_provisional_verify_against_official_RS-33-039_before_final_claim"
        )
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute the bounded Tangerine 2015->2021 public-lidar bracket test."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser(
        "prepare", help="Prepare same-grid 2015 and 2021 ground-DTM PDAL pipelines."
    )
    prepare_parser.add_argument("--output-dir", type=Path, required=True)
    prepare_parser.add_argument("--target-geojson", type=Path)
    prepare_parser.add_argument("--buffer-m", type=float, default=1200.0)
    prepare_parser.add_argument("--resolution-m", type=float, default=1.0)
    prepare_parser.add_argument("--execute", action="store_true")

    analyze_parser = subparsers.add_parser(
        "analyze", help="Co-register completed DTMs and apply the frozen residual gates."
    )
    analyze_parser.add_argument("--pre-dtm", type=Path, required=True)
    analyze_parser.add_argument("--post-dtm", type=Path, required=True)
    analyze_parser.add_argument("--target-geojson", type=Path, required=True)
    analyze_parser.add_argument("--output-json", type=Path, required=True)
    analyze_parser.add_argument("--target-erode-m", type=float, default=20.0)
    analyze_parser.add_argument("--stable-exclusion-m", type=float, default=100.0)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.command == "prepare":
        result = prepare(
            output_dir=args.output_dir,
            target_geojson=args.target_geojson,
            buffer_m=args.buffer_m,
            resolution_m=args.resolution_m,
            execute=args.execute,
        )
    else:
        result = analyze(
            pre_dtm=args.pre_dtm,
            post_dtm=args.post_dtm,
            target_geojson=args.target_geojson,
            output_json=args.output_json,
            target_erode_m=args.target_erode_m,
            stable_exclusion_m=args.stable_exclusion_m,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
