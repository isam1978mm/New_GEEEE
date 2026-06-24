from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import rasterio
from rasterio.transform import Affine

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.dem import write_raster_sidecar
from app.pipeline.stages.feature_stacks import SCIENCE_CORE_BANDS
from app.pipeline.stages.grid import GridSpec

FOCUS_MASK_TIF_NAME = "focus_zone_17m.tif"
FOCUS_MASK_NPY_NAME = "focus_zone_17m.npy"
FOCUS_WINDOW_NPY_NAME = "focus_zone_ai_ready_window.npy"
FOCUS_SUMMARY_JSON_NAME = "focus_zone_summary.json"
FOCUS_BAND_SUMMARY_CSV_NAME = "focus_zone_band_summary.csv"
FOCUS_PIXEL_REPORT_CSV_NAME = "AI_FOCUS_17M_PIXEL_REPORT_V7_2.csv"
FOCUS_TARGET_REPORT_CSV_NAME = "AI_FOCUS_17M_TARGETS_V7_2.csv"
FOCUS_TARGET_GEOJSON_NAME = "AI_FOCUS_17M_TARGETS_V7_2.geojson"
HARD_TYPE_CLASSIFIER_CSV_NAME = "AI_HARD_TYPE_CLASSIFIER_CORE9.csv"
HARD_TYPE_CLASSIFIER_TXT_NAME = "AI_HARD_TYPE_CLASSIFIER_CORE9.txt"
HARD_TYPE_CLASSIFIER_JSON_NAME = "AI_HARD_TYPE_CLASSIFIER_CORE9.json"
FOCUS_DIR_PARTS = ("full_job", "focus")
FOCUS_SIZE_M = 17.0

FOCUS_ANALYSIS_BANDS = (
    "Secret_Gold_Halo",
    "Secret_Silver_Oxide",
    "Secret_Tunnel_Ceiling",
    "Secret_Thermal_Inertia",
    "Secret_Chemical_Protector",
    "Secret_Hidden_Doors",
    "REPORT_640_FINAL_Zero_Point_Targets",
    "REPORT_640_Mass_Report",
    "REPORT_640_Pottery_Report",
)

FOCUS_SECRET_LAYER_FILES = {
    "Secret_Gold_Halo": "AI_READY_640_Secret_Gold_Halo.tif",
    "Secret_Silver_Oxide": "AI_READY_640_Secret_Silver_Oxide.tif",
    "Secret_Tunnel_Ceiling": "AI_READY_640_Secret_Tunnel_Ceiling.tif",
    "Secret_Thermal_Inertia": "AI_READY_640_Secret_Thermal_Inertia.tif",
    "Secret_Chemical_Protector": "AI_READY_640_Secret_Chemical_Protector.tif",
    "Secret_Hidden_Doors": "AI_READY_640_Secret_Hidden_Doors.tif",
}

FOCUS_REPORT_BAND_FILES = {
    "REPORT_640_FINAL_Zero_Point_Targets": "REPORT_640_FINAL_Zero_Point_Targets_640.npy",
    "REPORT_640_Mass_Report": "REPORT_640_Mass_Report_640.npy",
    "REPORT_640_Pottery_Report": "REPORT_640_Pottery_Report_640.npy",
}


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(fieldnames=fieldnames, f=handle)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_ai_ready_support_stack(run_dir: Path) -> np.ndarray:
    path = run_dir / "stacks" / "tensor_support" / "ai_ready_support_stack.npy"
    if not path.is_file():
        raise StageError("Focus-mask stage requires ai_ready_support_stack.npy from feature_stacks.")
    return np.load(path).astype(np.float32)


def _load_tif(path: Path, *, grid_spec: GridSpec) -> np.ndarray:
    if not path.is_file():
        raise StageError(f"ROI focus analysis requires missing raster: {path.as_posix()}")
    with rasterio.open(path) as dataset:
        arr = dataset.read(1).astype(np.float32)
    if arr.shape != (grid_spec.size, grid_spec.size):
        raise StageError(f"ROI focus analysis raster {path.name} has shape {arr.shape}, expected {(grid_spec.size, grid_spec.size)}.")
    return arr


def _load_npy(path: Path, *, grid_spec: GridSpec) -> np.ndarray:
    if not path.is_file():
        raise StageError(f"ROI focus analysis requires missing array: {path.as_posix()}")
    arr = np.load(path).astype(np.float32)
    if arr.shape != (grid_spec.size, grid_spec.size):
        raise StageError(f"ROI focus analysis array {path.name} has shape {arr.shape}, expected {(grid_spec.size, grid_spec.size)}.")
    return arr


def load_focus_analysis_bands(run_dir: Path, *, grid_spec: GridSpec) -> dict[str, np.ndarray]:
    bands: dict[str, np.ndarray] = {}

    for notebook_name, filename in FOCUS_SECRET_LAYER_FILES.items():
        bands[notebook_name] = _load_tif(run_dir / "AI_READY_640" / filename, grid_spec=grid_spec)

    for notebook_name, filename in FOCUS_REPORT_BAND_FILES.items():
        bands[notebook_name] = _load_npy(run_dir / "NPY_RADAR_BANDS" / filename, grid_spec=grid_spec)

    return bands


def build_focus_mask_products(
    ai_ready_stack: np.ndarray,
    *,
    grid_spec: GridSpec,
    focus_size_m: float = FOCUS_SIZE_M,
) -> dict[str, object]:
    if ai_ready_stack.ndim != 3:
        raise StageError("Focus-mask stage requires a 3D ai_ready support stack.")
    if ai_ready_stack.shape[0] != grid_spec.size or ai_ready_stack.shape[1] != grid_spec.size:
        raise StageError("Focus-mask stage requires ai_ready support stack on the authoritative grid.")

    transform = grid_spec.transform
    pixel_size_m = float((abs(transform[0]) + abs(transform[4])) / 2.0)
    radius_px = float(focus_size_m) / pixel_size_m
    center_row = float(grid_spec.size) / 2.0
    center_col = float(grid_spec.size) / 2.0

    rows, cols = np.meshgrid(np.arange(grid_spec.size), np.arange(grid_spec.size), indexing="ij")
    dist_px = np.sqrt((rows.astype(np.float64) - center_row) ** 2 + (cols.astype(np.float64) - center_col) ** 2)
    mask = (dist_px <= radius_px).astype(np.float32)
    row_indices, col_indices = np.where(mask == 1.0)

    if row_indices.size == 0 or col_indices.size == 0:
        raise StageError("Focus-mask stage could not derive a non-empty focus zone from the configured grid.")

    row_min = int(row_indices.min())
    row_max = int(row_indices.max())
    col_min = int(col_indices.min())
    col_max = int(col_indices.max())
    cropped_window = ai_ready_stack[row_min : row_max + 1, col_min : col_max + 1, :].astype(np.float32)
    masked_window = cropped_window * mask[row_min : row_max + 1, col_min : col_max + 1, None]

    band_summary_rows: list[dict[str, object]] = []
    for index in range(ai_ready_stack.shape[-1]):
        channel = ai_ready_stack[:, :, index]
        values = channel[mask == 1.0]
        band_summary_rows.append(
            {
                "band_index": index,
                "band_name": SCIENCE_CORE_BANDS[index] if index < len(SCIENCE_CORE_BANDS) else f"band_{index}",
                "focus_mean": float(values.mean()) if values.size else "",
                "focus_min": float(values.min()) if values.size else "",
                "focus_max": float(values.max()) if values.size else "",
            }
        )

    summary = {
        "stage": "focus_mask",
        "focus_size_m": float(focus_size_m),
        "mask_pixel_count": int(mask.sum()),
        "window_shape": [int(masked_window.shape[0]), int(masked_window.shape[1]), int(masked_window.shape[2])],
        "analysis_source": "ai_ready_support_stack",
        "public_safe": False,
    }
    return {
        "mask": mask,
        "masked_window": masked_window,
        "summary": summary,
        "band_summary_rows": band_summary_rows,
    }


def _robust_z(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return np.zeros_like(values, dtype=np.float64)

    med = np.nanmedian(finite)
    mad = np.nanmedian(np.abs(finite - med))
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale < 1e-9:
        std = np.nanstd(finite)
        if not np.isfinite(std) or std < 1e-9:
            return np.zeros_like(values, dtype=np.float64)
        result = (values - np.nanmean(finite)) / std
    else:
        result = (values - med) / scale

    result[~np.isfinite(result)] = 0.0
    return result.astype(np.float64, copy=False)


def _mask_values(arr: np.ndarray, mask: np.ndarray, *, nodata: float) -> np.ndarray:
    values = arr[mask].astype(np.float64)
    values[~np.isfinite(values)] = np.nan
    values[values == float(nodata)] = np.nan
    return values


def _score_confidence(score: float, scores: list[float]) -> str:
    if not scores:
        return "0.0%"
    finite_scores = [s for s in scores if np.isfinite(s)]
    if not finite_scores:
        return "0.0%"
    rank_fraction = sum(s <= score for s in finite_scores) / float(len(finite_scores))
    return f"{rank_fraction * 100.0:.1f}%"


def _classify_target(row: dict[str, object], medians: dict[str, float]) -> str:
    g = float(row["Secret_Gold_Halo"])
    td = float(row["Secret_Tunnel_Ceiling"])
    th = float(row["Secret_Thermal_Inertia"])
    hd = float(row["Secret_Hidden_Doors"])
    ms = float(row["REPORT_640_Mass_Report"])
    pt = float(row["REPORT_640_Pottery_Report"])

    if g >= medians["Secret_Gold_Halo"] and ms >= medians["REPORT_640_Mass_Report"]:
        return "Priority A ? Metallic/High-density focus"
    if hd >= medians["Secret_Hidden_Doors"] and td >= medians["Secret_Tunnel_Ceiling"]:
        return "Priority B ? Structural/void-related focus"
    if pt >= medians["REPORT_640_Pottery_Report"]:
        return "Priority C ? Pottery/material concentration"
    if th >= medians["Secret_Thermal_Inertia"]:
        return "Priority D ? Thermal contrast focus"
    return "Priority E ? Comparative anomaly inside 17m"


def build_focus_roi_analysis_products(
    *,
    focus_mask: np.ndarray,
    analysis_bands: dict[str, np.ndarray],
    grid_spec: GridSpec,
) -> dict[str, object]:
    mask_bool = focus_mask.astype(bool)
    rows, cols = np.where(mask_bool)
    if rows.size == 0:
        raise StageError("ROI-constrained focus analysis requires a non-empty 17m focus mask.")

    missing = [name for name in FOCUS_ANALYSIS_BANDS if name not in analysis_bands]
    if missing:
        raise StageError(f"ROI-constrained focus analysis is missing required bands: {', '.join(missing)}")

    z_bands: dict[str, np.ndarray] = {}
    for name in FOCUS_ANALYSIS_BANDS:
        arr = analysis_bands[name].astype(np.float32, copy=False)
        vals = _mask_values(arr, mask_bool, nodata=grid_spec.nodata)
        zvals = _robust_z(vals)
        tmp = np.full(arr.shape, np.nan, dtype=np.float64)
        tmp[mask_bool] = zvals
        z_bands[name] = tmp

    score = (
        1.20 * np.nan_to_num(z_bands["Secret_Gold_Halo"], nan=0.0)
        + 1.00 * np.nan_to_num(z_bands["Secret_Silver_Oxide"], nan=0.0)
        + 0.90 * np.nan_to_num(z_bands["Secret_Hidden_Doors"], nan=0.0)
        + 0.90 * np.nan_to_num(z_bands["Secret_Tunnel_Ceiling"], nan=0.0)
        + 0.80 * np.nan_to_num(z_bands["Secret_Thermal_Inertia"], nan=0.0)
        + 0.60 * np.nan_to_num(z_bands["Secret_Chemical_Protector"], nan=0.0)
        + 0.80 * np.nan_to_num(z_bands["REPORT_640_Mass_Report"], nan=0.0)
        + 0.60 * np.nan_to_num(z_bands["REPORT_640_Pottery_Report"], nan=0.0)
        + 0.50 * np.nan_to_num(z_bands["REPORT_640_FINAL_Zero_Point_Targets"], nan=0.0)
    )
    score[~mask_bool] = np.nan

    affine = Affine(*grid_spec.transform)
    pixel_records: list[dict[str, object]] = []
    for r, c in zip(rows, cols):
        x, y = rasterio.transform.xy(affine, int(r), int(c), offset="center")
        record: dict[str, object] = {
            "row": int(r),
            "col": int(c),
            "UTM_E": round(float(x), 3),
            "UTM_N": round(float(y), 3),
        }
        for name in FOCUS_ANALYSIS_BANDS:
            record[name] = float(analysis_bands[name][r, c])
        record["ROI_Composite_Score"] = float(score[r, c])
        pixel_records.append(record)

    pixel_records.sort(key=lambda item: float(item["ROI_Composite_Score"]), reverse=True)
    target_source = pixel_records[: min(5, len(pixel_records))]
    medians = {
        name: float(np.nanmedian([float(row[name]) for row in target_source])) if target_source else 0.0
        for name in FOCUS_ANALYSIS_BANDS
    }
    scores = [float(row["ROI_Composite_Score"]) for row in target_source]

    target_records: list[dict[str, object]] = []
    for index, source in enumerate(target_source, start=1):
        target = {
            "Target_ID": index,
            "row": source["row"],
            "col": source["col"],
            "UTM_E": source["UTM_E"],
            "UTM_N": source["UTM_N"],
            "Classification": _classify_target(source, medians),
            "Confidence": _score_confidence(float(source["ROI_Composite_Score"]), scores),
            "ROI_Composite_Score": source["ROI_Composite_Score"],
        }
        for name in FOCUS_ANALYSIS_BANDS:
            target[name] = source[name]
        target_records.append(target)

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(row["UTM_E"]), float(row["UTM_N"])]},
            "properties": {
                "Target_ID": int(row["Target_ID"]),
                "Classification": row["Classification"],
                "Confidence": row["Confidence"],
                "ROI_Composite_Score": float(row["ROI_Composite_Score"]),
            },
        }
        for row in target_records
    ]

    return {
        "pixel_records": pixel_records,
        "target_records": target_records,
        "target_geojson": {"type": "FeatureCollection", "features": features},
    }



def _hard_get_vals(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    vals = arr[mask].astype(np.float64)
    vals = vals[np.isfinite(vals)]
    return vals


def _hard_robust_contrast(core_vals: np.ndarray, ref_vals: np.ndarray) -> float:
    if len(core_vals) == 0 or len(ref_vals) == 0:
        return 0.0
    ref_med = np.nanmedian(ref_vals)
    ref_mad = np.nanmedian(np.abs(ref_vals - ref_med)) * 1.4826
    if not np.isfinite(ref_mad) or ref_mad < 1e-9:
        ref_mad = np.nanstd(ref_vals)
    if not np.isfinite(ref_mad) or ref_mad < 1e-9:
        return 0.0
    return float((np.nanmean(core_vals) - ref_med) / ref_mad)


def _hard_effect_size(core_vals: np.ndarray, ref_vals: np.ndarray) -> float:
    if len(core_vals) == 0 or len(ref_vals) == 0:
        return 0.0
    m1 = np.nanmean(core_vals)
    m2 = np.nanmean(ref_vals)
    s1 = np.nanstd(core_vals)
    s2 = np.nanstd(ref_vals)
    pooled = np.sqrt((s1**2 + s2**2) / 2.0)
    if not np.isfinite(pooled) or pooled < 1e-9:
        return 0.0
    return float((m1 - m2) / pooled)


def _hard_clip01(x: float) -> float:
    return float(np.clip(x, 0.0, 1.0))


def _hard_prob(x: float, *, bias: float = 0.0, gain: float = 1.0) -> float:
    z = gain * (x - bias)
    z = float(np.clip(z, -60.0, 60.0))
    return _hard_clip01(1.0 / (1.0 + np.exp(-z)))


def _hard_safe_mean(arr: np.ndarray, mask: np.ndarray) -> float:
    vals = arr[mask]
    vals = vals[np.isfinite(vals)]
    return float(np.mean(vals)) if len(vals) else 0.0


def _hard_dilate(mask: np.ndarray, iterations: int) -> np.ndarray:
    out = mask.astype(bool).copy()
    for _ in range(iterations):
        padded = np.pad(out, 1, mode="constant", constant_values=False)
        nxt = np.zeros_like(out, dtype=bool)
        for dr in range(3):
            for dc in range(3):
                nxt |= padded[dr : dr + out.shape[0], dc : dc + out.shape[1]]
        out = nxt
    return out


def _hard_ring_masks(core_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    dil2 = _hard_dilate(core_mask, 2)
    dil4 = _hard_dilate(core_mask, 4)
    dil6 = _hard_dilate(core_mask, 6)
    ring_near = dil2 & (~core_mask)
    ring_far = dil4 & (~dil2)
    ring_wide = dil6 & (~dil4)
    scene_mask = np.ones_like(core_mask, dtype=bool)
    return ring_near, ring_far, ring_wide, scene_mask


def _hard_band_pack(
    arr: np.ndarray,
    *,
    core_mask: np.ndarray,
    ring_near: np.ndarray,
    ring_far: np.ndarray,
    ring_wide: np.ndarray,
    scene_mask: np.ndarray,
) -> dict[str, float]:
    core_vals = _hard_get_vals(arr, core_mask)
    near_vals = _hard_get_vals(arr, ring_near)
    far_vals = _hard_get_vals(arr, ring_far)
    wide_vals = _hard_get_vals(arr, ring_wide)
    scene_vals = _hard_get_vals(arr, scene_mask)
    return {
        "core_mean": float(np.nanmean(core_vals)) if len(core_vals) else 0.0,
        "near_mean": float(np.nanmean(near_vals)) if len(near_vals) else 0.0,
        "far_mean": float(np.nanmean(far_vals)) if len(far_vals) else 0.0,
        "wide_mean": float(np.nanmean(wide_vals)) if len(wide_vals) else 0.0,
        "scene_mean": float(np.nanmean(scene_vals)) if len(scene_vals) else 0.0,
        "rc_near": _hard_robust_contrast(core_vals, near_vals),
        "rc_far": _hard_robust_contrast(core_vals, far_vals),
        "rc_wide": _hard_robust_contrast(core_vals, wide_vals),
        "rc_scene": _hard_robust_contrast(core_vals, scene_vals),
        "ef_near": _hard_effect_size(core_vals, near_vals),
        "ef_scene": _hard_effect_size(core_vals, scene_vals),
    }


def _hard_rc(stats: dict[str, dict[str, float]], band: str, key: str) -> float:
    return float(stats.get(band, {}).get(key, 0.0))


def _hard_robust_norm(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr, dtype=np.float32)
    vals = arr[np.isfinite(arr)]
    if vals.size == 0:
        return np.zeros_like(arr, dtype=np.float32)
    lo = np.percentile(vals, 2)
    hi = np.percentile(vals, 98)
    if not np.isfinite(hi - lo) or abs(float(hi - lo)) < 1e-9:
        return np.zeros_like(arr, dtype=np.float32)
    return np.clip((arr - lo) / (hi - lo + 1e-9), 0, 1).astype(np.float32)


def _hard_count_local_peaks(score_map: np.ndarray, mask: np.ndarray, *, threshold_q: float) -> int:
    vals = score_map[mask]
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return 0
    threshold = float(np.percentile(vals, threshold_q))
    candidates = (score_map >= threshold) & mask
    count = 0
    rr, cc = np.where(candidates)
    for r, c in zip(rr, cc):
        r0 = max(0, int(r) - 1)
        r1 = min(score_map.shape[0], int(r) + 2)
        c0 = max(0, int(c) - 1)
        c1 = min(score_map.shape[1], int(c) + 2)
        if float(score_map[int(r), int(c)]) >= float(np.nanmax(score_map[r0:r1, c0:c1])):
            count += 1
    return int(count)


def _hard_elongation_from_mask(mask: np.ndarray) -> float:
    rr, cc = np.where(mask)
    if len(rr) < 2:
        return 1.0
    pts = np.column_stack([cc, rr]).astype(np.float64)
    pts -= pts.mean(axis=0, keepdims=True)
    cov = np.cov(pts.T)
    vals = np.linalg.eigvalsh(cov)
    vals = np.sort(np.maximum(vals, 1e-9))
    return float(np.sqrt(vals[-1] / vals[0]))


def _hard_axis_orientation(mask: np.ndarray) -> str:
    rr, cc = np.where(mask)
    if len(rr) < 2:
        return "UNRESOLVED"
    pts = np.column_stack([cc, rr]).astype(np.float64)
    pts -= pts.mean(axis=0, keepdims=True)
    cov = np.cov(pts.T)
    vals, vecs = np.linalg.eigh(cov)
    vec = vecs[:, int(np.argmax(vals))]
    angle = float(np.degrees(np.arctan2(vec[1], vec[0])))
    if -22.5 <= angle <= 22.5 or angle >= 157.5 or angle <= -157.5:
        return "E_W"
    if 67.5 <= angle <= 112.5 or -112.5 <= angle <= -67.5:
        return "N_S"
    if angle > 0:
        return "NE_SW"
    return "NW_SE"


def build_hard_type_classifier_products(
    *,
    focus_mask: np.ndarray,
    analysis_bands: dict[str, np.ndarray],
    grid_spec: GridSpec,
) -> dict[str, object]:
    core_mask = focus_mask.astype(bool)
    if int(core_mask.sum()) == 0:
        raise StageError("Hard type classifier requires a non-empty focus/core mask.")

    missing = [name for name in FOCUS_ANALYSIS_BANDS if name not in analysis_bands]
    if missing:
        raise StageError(f"Hard type classifier is missing required bands: {', '.join(missing)}")

    ring_near, ring_far, ring_wide, scene_mask = _hard_ring_masks(core_mask)
    stats = {
        name: _hard_band_pack(
            analysis_bands[name],
            core_mask=core_mask,
            ring_near=ring_near,
            ring_far=ring_far,
            ring_wide=ring_wide,
            scene_mask=scene_mask,
        )
        for name in FOCUS_ANALYSIS_BANDS
    }

    gold = analysis_bands["Secret_Gold_Halo"]
    silver = analysis_bands["Secret_Silver_Oxide"]
    tunnel = analysis_bands["Secret_Tunnel_Ceiling"]
    thermal = analysis_bands["Secret_Thermal_Inertia"]
    chemical = analysis_bands["Secret_Chemical_Protector"]
    doors = analysis_bands["Secret_Hidden_Doors"]
    zero = analysis_bands["REPORT_640_FINAL_Zero_Point_Targets"]
    mass = analysis_bands["REPORT_640_Mass_Report"]
    pottery = analysis_bands["REPORT_640_Pottery_Report"]

    focus_rows, focus_cols = np.where(core_mask)
    center_r = float(np.mean(focus_rows))
    center_c = float(np.mean(focus_cols))
    rr, cc = np.indices(core_mask.shape)
    direction_mask = core_mask | ring_near
    directional_arr = _hard_robust_norm(doors) + _hard_robust_norm(tunnel) + _hard_robust_norm(zero)
    dir_scores = {
        "north": _hard_safe_mean(directional_arr, direction_mask & (rr < center_r)),
        "south": _hard_safe_mean(directional_arr, direction_mask & (rr > center_r)),
        "west": _hard_safe_mean(directional_arr, direction_mask & (cc < center_c)),
        "east": _hard_safe_mean(directional_arr, direction_mask & (cc > center_c)),
    }
    best_dir = max(dir_scores, key=dir_scores.get)
    sorted_dir = sorted(dir_scores.values(), reverse=True)
    directionality_strength = float(sorted_dir[0] - sorted_dir[1]) if len(sorted_dir) > 1 else 0.0

    void_family_score = (
        0.34 * _hard_rc(stats, "Secret_Tunnel_Ceiling", "rc_near")
        + 0.26 * _hard_rc(stats, "Secret_Hidden_Doors", "rc_near")
        + 0.18 * _hard_rc(stats, "REPORT_640_FINAL_Zero_Point_Targets", "rc_scene")
        + 0.12 * _hard_rc(stats, "Secret_Thermal_Inertia", "rc_far")
        + 0.10 * directionality_strength
    )
    metal_family_score = (
        0.36 * _hard_rc(stats, "Secret_Gold_Halo", "rc_scene")
        + 0.28 * _hard_rc(stats, "Secret_Silver_Oxide", "rc_scene")
        + 0.22 * _hard_rc(stats, "REPORT_640_Mass_Report", "rc_near")
        + 0.14 * _hard_rc(stats, "Secret_Chemical_Protector", "rc_scene")
    )
    fill_family_score = (
        0.42 * _hard_rc(stats, "REPORT_640_Pottery_Report", "rc_scene")
        + 0.22 * _hard_rc(stats, "Secret_Thermal_Inertia", "rc_scene")
        + 0.18 * _hard_rc(stats, "Secret_Chemical_Protector", "rc_near")
        + 0.18 * _hard_rc(stats, "Secret_Tunnel_Ceiling", "rc_far")
    )
    entrance_family_score = (
        0.34 * _hard_rc(stats, "Secret_Hidden_Doors", "rc_near")
        + 0.28 * _hard_rc(stats, "Secret_Tunnel_Ceiling", "rc_near")
        + 0.18 * directionality_strength
        + 0.20 * _hard_rc(stats, "REPORT_640_FINAL_Zero_Point_Targets", "rc_near")
    )
    surface_penalty_raw = abs(_hard_rc(stats, "Secret_Thermal_Inertia", "rc_scene")) * 0.35
    surface_exclusion_score = _hard_clip01(_hard_prob(1.2 - surface_penalty_raw, bias=0.0, gain=1.0))

    p_void_raw = _hard_prob(void_family_score, bias=0.85, gain=0.90)
    p_metal_raw = _hard_prob(metal_family_score, bias=0.70, gain=0.90)
    p_fill_raw = _hard_prob(fill_family_score, bias=0.70, gain=0.85)
    p_entry_raw = _hard_prob(entrance_family_score, bias=0.90, gain=0.85)

    surface_gate = _hard_clip01(0.20 + 0.80 * surface_exclusion_score)
    entry_gate = _hard_clip01(0.55 * p_void_raw + 0.45 * directionality_strength)
    p_void = p_void_raw
    p_fill = p_fill_raw
    p_metal = _hard_clip01(p_metal_raw * (0.65 + 0.35 * surface_gate))
    p_entry = _hard_clip01(p_entry_raw * entry_gate)

    shaft_score = _hard_clip01(
        0.42 * p_void
        + 0.20 * _hard_prob(_hard_rc(stats, "Secret_Tunnel_Ceiling", "rc_scene"), bias=0.5, gain=0.7)
        + 0.14 * surface_exclusion_score
        + 0.24 * _hard_prob(_hard_rc(stats, "Secret_Thermal_Inertia", "rc_scene"), bias=0.4, gain=0.7)
    )
    entrance_score = _hard_clip01(
        0.34 * p_void
        + 0.30 * p_entry
        + 0.18 * directionality_strength
        + 0.18 * _hard_prob(_hard_rc(stats, "Secret_Hidden_Doors", "rc_near"), bias=0.5, gain=0.7)
    )
    chamber_score = _hard_clip01(
        0.45 * p_void
        + 0.18 * surface_exclusion_score
        + 0.20 * _hard_prob(_hard_rc(stats, "REPORT_640_Mass_Report", "rc_scene"), bias=0.5, gain=0.7)
        + 0.17 * _hard_prob(_hard_rc(stats, "Secret_Tunnel_Ceiling", "rc_wide"), bias=0.5, gain=0.7)
    )
    drain_void_score = _hard_clip01(
        0.32 * p_void
        + 0.32 * _hard_prob(_hard_rc(stats, "Secret_Tunnel_Ceiling", "rc_near"), bias=0.5, gain=0.7)
        + 0.20 * directionality_strength
        + 0.16 * _hard_prob(_hard_rc(stats, "Secret_Thermal_Inertia", "rc_far"), bias=0.5, gain=0.7)
    )

    gold_like_score = _hard_clip01(
        0.42 * p_metal
        + 0.34 * _hard_prob(_hard_rc(stats, "Secret_Gold_Halo", "rc_scene"), bias=0.5, gain=0.75)
        + 0.12 * _hard_prob(_hard_rc(stats, "REPORT_640_Mass_Report", "rc_scene"), bias=0.5, gain=0.75)
        + 0.12 * surface_exclusion_score
    )
    silver_like_score = _hard_clip01(
        0.42 * p_metal
        + 0.34 * _hard_prob(_hard_rc(stats, "Secret_Silver_Oxide", "rc_scene"), bias=0.5, gain=0.75)
        + 0.12 * _hard_prob(_hard_rc(stats, "REPORT_640_Mass_Report", "rc_scene"), bias=0.5, gain=0.75)
        + 0.12 * surface_exclusion_score
    )
    dense_metal_score = _hard_clip01(
        0.55 * p_metal
        + 0.25 * _hard_prob(_hard_rc(stats, "REPORT_640_Mass_Report", "rc_scene"), bias=0.5, gain=0.75)
        + 0.20 * max(gold_like_score, silver_like_score)
    )

    coins_score = _hard_clip01(0.34 * p_metal + 0.18 * gold_like_score + 0.16 * silver_like_score + 0.20 * p_fill + 0.12 * surface_exclusion_score)
    ingots_score = _hard_clip01(0.42 * p_metal + 0.26 * dense_metal_score + 0.12 * gold_like_score + 0.10 * surface_exclusion_score + 0.10 * _hard_prob(_hard_rc(stats, "REPORT_640_Mass_Report", "rc_scene"), bias=0.5, gain=0.75))
    statues_score = _hard_clip01(0.28 * p_metal + 0.22 * dense_metal_score + 0.18 * p_void + 0.16 * surface_exclusion_score + 0.16 * _hard_prob(_hard_rc(stats, "REPORT_640_Mass_Report", "rc_near"), bias=0.5, gain=0.75))
    pottery_treasures_score = _hard_clip01(0.38 * p_fill + 0.18 * p_void + 0.18 * _hard_prob(_hard_rc(stats, "REPORT_640_Pottery_Report", "rc_scene"), bias=0.5, gain=0.75) + 0.16 * surface_exclusion_score + 0.10 * _hard_prob(_hard_rc(stats, "Secret_Chemical_Protector", "rc_scene"), bias=0.5, gain=0.75))
    general_antiquities_score = _hard_clip01(0.22 * p_void + 0.22 * p_metal + 0.18 * p_fill + 0.18 * surface_exclusion_score + 0.20 * max(gold_like_score, silver_like_score, dense_metal_score))

    if p_void >= 0.60 and p_metal >= 0.58 and surface_exclusion_score >= 0.55:
        primary_class = "MIXED_VOID_METAL"
    elif p_void >= 0.60 and surface_exclusion_score >= 0.55:
        primary_class = "STRUCTURAL_VOID"
    elif p_metal >= 0.58 and surface_exclusion_score >= 0.50:
        primary_class = "METAL_DENSE"
    elif p_fill >= 0.58:
        primary_class = "FILL_OR_POTTERY"
    else:
        primary_class = "UNRESOLVED_ANOMALY"

    void_subscores = {
        "ENTRANCE": entrance_score,
        "SHAFT": shaft_score,
        "CHAMBER": chamber_score,
        "DRAIN_VOID": drain_void_score,
    }
    best_void_subtype = max(void_subscores, key=void_subscores.get)
    if primary_class in {"STRUCTURAL_VOID", "MIXED_VOID_METAL"} and p_void >= 0.60:
        void_type = best_void_subtype if void_subscores[best_void_subtype] >= 0.56 else "VOID_UNRESOLVED"
    else:
        void_type = "NO_CONFIRMED_VOID"

    metal_subscores = {
        "GOLD_LIKE": gold_like_score,
        "SILVER_LIKE": silver_like_score,
        "DENSE_METAL": dense_metal_score,
    }
    best_metal_subtype = max(metal_subscores, key=metal_subscores.get)
    if p_metal >= 0.55:
        metal_type = best_metal_subtype if metal_subscores[best_metal_subtype] >= 0.54 else "METAL_UNRESOLVED"
    else:
        metal_type = "NO_CONFIRMED_METAL"

    analysis_mask = core_mask | ring_near
    metal_combo = _hard_robust_norm(gold) + _hard_robust_norm(silver) + _hard_robust_norm(mass)
    jar_combo = _hard_robust_norm(pottery) + _hard_robust_norm(chemical) + _hard_robust_norm(thermal)

    metal_vals = metal_combo[analysis_mask]
    jar_vals = jar_combo[analysis_mask]
    metal_thr = float(np.percentile(metal_vals[np.isfinite(metal_vals)], 70)) if np.isfinite(metal_vals).sum() else 0.7
    jar_thr = float(np.percentile(jar_vals[np.isfinite(jar_vals)], 68)) if np.isfinite(jar_vals).sum() else 0.68
    metal_obj_mask = (metal_combo >= metal_thr) & analysis_mask
    jar_obj_mask = (jar_combo >= jar_thr) & analysis_mask

    elongation = _hard_elongation_from_mask(metal_obj_mask if metal_obj_mask.sum() > 0 else core_mask)
    orientation = _hard_axis_orientation(metal_obj_mask if metal_obj_mask.sum() > 0 else core_mask)
    if p_metal < 0.50:
        metal_shape = "NO_CONFIRMED_METAL_SHAPE"
    elif elongation >= 2.8:
        metal_shape = f"LINEAR_{orientation}"
    elif elongation >= 1.45:
        metal_shape = f"ELLIPSOID_{orientation}"
    else:
        metal_shape = "COMPACT_CLUSTER"

    estimated_stacked_boxes = 0
    if p_metal >= 0.58 and dense_metal_score >= 0.58:
        estimated_stacked_boxes = min(4, max(1, _hard_count_local_peaks(metal_combo, analysis_mask, threshold_q=75)))

    estimated_aligned_jars = 0
    if p_fill >= 0.56 and pottery_treasures_score >= 0.56:
        estimated_aligned_jars = min(6, max(1, _hard_count_local_peaks(jar_combo, analysis_mask, threshold_q=72)))

    content_subscores = {
        "COINS": coins_score,
        "INGOTS": ingots_score,
        "STATUES": statues_score,
        "POTTERY_TREASURES": pottery_treasures_score,
        "GENERAL_ANTIQUITIES": general_antiquities_score,
    }
    best_content_type = max(content_subscores, key=content_subscores.get)
    content_type = best_content_type if content_subscores[best_content_type] >= 0.50 else "CONTENT_UNRESOLVED"

    final_confidence = _hard_clip01(
        max(
            0.34 * p_void + 0.34 * p_metal + 0.16 * surface_exclusion_score + 0.16 * max(gold_like_score, silver_like_score, dense_metal_score),
            0.52 * p_void + 0.22 * surface_exclusion_score + 0.16 * max(entrance_score, shaft_score, chamber_score, drain_void_score),
            0.54 * p_metal + 0.20 * surface_exclusion_score + 0.26 * max(gold_like_score, silver_like_score, dense_metal_score),
            0.55 * p_fill + 0.25 * pottery_treasures_score + 0.20 * surface_exclusion_score,
        )
    )

    record = {
        "Core_Mask_Source": "focus_zone_17m",
        "Source_Cell": "cell_128",
        "Core_Pixels": int(core_mask.sum()),
        "Near_Ring_Pixels": int(ring_near.sum()),
        "Far_Ring_Pixels": int(ring_far.sum()),
        "Wide_Ring_Pixels": int(ring_wide.sum()),
        "Primary_Class": primary_class,
        "Void_Type": void_type,
        "Metal_Type": metal_type,
        "Metal_Shape": metal_shape,
        "Content_Type": content_type,
        "Estimated_Stacked_Boxes": int(estimated_stacked_boxes),
        "Estimated_Aligned_Jars": int(estimated_aligned_jars),
        "Final_Confidence": round(final_confidence, 4),
        "Void_Probability": round(p_void, 4),
        "Metal_Probability": round(p_metal, 4),
        "Fill_Probability": round(p_fill, 4),
        "Entrance_Probability": round(p_entry, 4),
        "Surface_Exclusion": round(surface_exclusion_score, 4),
        "Dominant_Direction": best_dir,
        "Directionality_Strength": round(directionality_strength, 4),
        "Entrance_Score": round(entrance_score, 4),
        "Shaft_Score": round(shaft_score, 4),
        "Chamber_Score": round(chamber_score, 4),
        "Drain_Void_Score": round(drain_void_score, 4),
        "Gold_Like_Score": round(gold_like_score, 4),
        "Silver_Like_Score": round(silver_like_score, 4),
        "Dense_Metal_Score": round(dense_metal_score, 4),
        "Coins_Score": round(coins_score, 4),
        "Ingots_Score": round(ingots_score, 4),
        "Statues_Score": round(statues_score, 4),
        "Pottery_Treasures_Score": round(pottery_treasures_score, 4),
        "General_Antiquities_Score": round(general_antiquities_score, 4),
    }

    summary_lines = [
        "AI HARD TYPE CLASSIFIER - CORE 9 ONLY",
        "=" * 82,
        f"Core mask source          : {record['Core_Mask_Source']}",
        f"Core pixels               : {record['Core_Pixels']}",
        f"Near/Far/Wide ring pixels : {record['Near_Ring_Pixels']} / {record['Far_Ring_Pixels']} / {record['Wide_Ring_Pixels']}",
        "-" * 82,
        f"Primary class             : {primary_class}",
        f"Void type                 : {void_type}",
        f"Metal type                : {metal_type}",
        f"Metal shape               : {metal_shape}",
        f"Content type              : {content_type}",
        f"Estimated stacked boxes   : {int(estimated_stacked_boxes)}",
        f"Estimated aligned jars    : {int(estimated_aligned_jars)}",
        f"Final confidence          : {final_confidence:.2%}",
        "-" * 82,
        f"Void probability          : {p_void:.2%}",
        f"Metal probability         : {p_metal:.2%}",
        f"Fill probability          : {p_fill:.2%}",
        f"Entrance probability      : {p_entry:.2%}",
        f"Surface exclusion         : {surface_exclusion_score:.2%}",
        "-" * 82,
        f"Void scores               : entrance={entrance_score:.4f} | shaft={shaft_score:.4f} | chamber={chamber_score:.4f} | drain={drain_void_score:.4f}",
        f"Metal scores              : gold={gold_like_score:.4f} | silver={silver_like_score:.4f} | dense={dense_metal_score:.4f}",
        f"Content scores            : coins={coins_score:.4f} | ingots={ingots_score:.4f} | statues={statues_score:.4f} | pottery={pottery_treasures_score:.4f} | antiquities={general_antiquities_score:.4f}",
        f"Dominant direction        : {best_dir}",
        f"Directionality strength   : {directionality_strength:.4f}",
    ]

    return {
        "hard_type_record": record,
        "hard_type_json": {
            "source_cell": "cell_128",
            "source_notebook_family": "AI_HARD_TYPE_CLASSIFIER_CORE9",
            "status": "implemented",
            "privacy": "FILESYSTEM_ONLY",
            "record": record,
            "band_stats": stats,
        },
        "hard_type_summary_lines": summary_lines,
    }

def write_focus_mask_outputs(run_dir: Path, grid_spec: GridSpec, products: dict[str, object]) -> dict[str, Path]:
    mask = products["mask"]
    masked_window = products["masked_window"]
    summary = products["summary"]
    band_summary_rows = products["band_summary_rows"]
    pixel_records = products["pixel_records"]
    target_records = products["target_records"]
    target_geojson = products["target_geojson"]
    hard_type_record = products["hard_type_record"]
    hard_type_json = products["hard_type_json"]
    hard_type_summary_lines = products["hard_type_summary_lines"]
    assert isinstance(mask, np.ndarray)
    assert isinstance(masked_window, np.ndarray)
    assert isinstance(summary, dict)
    assert isinstance(band_summary_rows, list)
    assert isinstance(pixel_records, list)
    assert isinstance(target_records, list)
    assert isinstance(target_geojson, dict)
    assert isinstance(hard_type_record, dict)
    assert isinstance(hard_type_json, dict)
    assert isinstance(hard_type_summary_lines, list)

    focus_dir = run_dir.joinpath(*FOCUS_DIR_PARTS)
    focus_dir.mkdir(parents=True, exist_ok=True)

    mask_tif_path = focus_dir / FOCUS_MASK_TIF_NAME
    mask_npy_path = focus_dir / FOCUS_MASK_NPY_NAME
    focus_window_path = focus_dir / FOCUS_WINDOW_NPY_NAME
    summary_path = focus_dir / FOCUS_SUMMARY_JSON_NAME
    band_summary_path = focus_dir / FOCUS_BAND_SUMMARY_CSV_NAME
    pixel_report_path = focus_dir / FOCUS_PIXEL_REPORT_CSV_NAME
    target_report_path = focus_dir / FOCUS_TARGET_REPORT_CSV_NAME
    target_geojson_path = focus_dir / FOCUS_TARGET_GEOJSON_NAME
    hard_type_csv_path = focus_dir / HARD_TYPE_CLASSIFIER_CSV_NAME
    hard_type_txt_path = focus_dir / HARD_TYPE_CLASSIFIER_TXT_NAME
    hard_type_json_path = focus_dir / HARD_TYPE_CLASSIFIER_JSON_NAME

    _write_focus_mask_tif(mask_tif_path, mask, grid_spec)
    np.save(mask_npy_path, mask.astype(np.float32))
    np.save(focus_window_path, masked_window.astype(np.float32))
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    _write_csv(band_summary_path, ["band_index", "band_name", "focus_mean", "focus_min", "focus_max"], band_summary_rows)

    pixel_fields = ["row", "col", "UTM_E", "UTM_N", *FOCUS_ANALYSIS_BANDS, "ROI_Composite_Score"]
    target_fields = [
        "Target_ID",
        "row",
        "col",
        "UTM_E",
        "UTM_N",
        "Classification",
        "Confidence",
        "ROI_Composite_Score",
        *FOCUS_ANALYSIS_BANDS,
    ]
    _write_csv(pixel_report_path, pixel_fields, pixel_records)
    _write_csv(target_report_path, target_fields, target_records)
    target_geojson_path.write_text(json.dumps(target_geojson, indent=2, sort_keys=True), encoding="utf-8")
    _write_csv(hard_type_csv_path, list(hard_type_record.keys()), [hard_type_record])
    hard_type_txt_path.write_text("\n".join(str(line) for line in hard_type_summary_lines), encoding="utf-8")
    hard_type_json_path.write_text(json.dumps(hard_type_json, indent=2, sort_keys=True), encoding="utf-8")

    write_raster_sidecar(
        mask_tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=0.0,
        dtype="uint8",
        shape=mask.shape,
    )

    return {
        "focus_mask_tif": mask_tif_path,
        "focus_mask_npy": mask_npy_path,
        "focus_window_npy": focus_window_path,
        "focus_summary_json": summary_path,
        "focus_band_summary_csv": band_summary_path,
        "focus_pixel_report_csv": pixel_report_path,
        "focus_target_report_csv": target_report_path,
        "focus_target_geojson": target_geojson_path,
        "hard_type_classifier_csv": hard_type_csv_path,
        "hard_type_classifier_txt": hard_type_txt_path,
        "hard_type_classifier_json": hard_type_json_path,
    }


def _write_focus_mask_tif(path: Path, mask: np.ndarray, grid_spec: GridSpec) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=int(mask.shape[0]),
        width=int(mask.shape[1]),
        count=1,
        dtype="uint8",
        crs=grid_spec.crs,
        transform=Affine(*grid_spec.transform),
        nodata=0,
        compress="deflate",
    ) as dataset:
        dataset.write(mask.astype(np.uint8, copy=False), 1)


class FocusMaskStage(Stage):
    name = "focus_mask"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Replaces notebook location-bearing 17m focus-region outputs with local-only FILESYSTEM_ONLY mask and ROI analysis products."

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        ai_ready_stack = load_ai_ready_support_stack(context.run_dir)
        products = build_focus_mask_products(ai_ready_stack, grid_spec=self.grid_spec)
        analysis_bands = load_focus_analysis_bands(context.run_dir, grid_spec=self.grid_spec)
        products.update(
            build_focus_roi_analysis_products(
                focus_mask=products["mask"],
                analysis_bands=analysis_bands,
                grid_spec=self.grid_spec,
            )
        )
        products.update(
            build_hard_type_classifier_products(
                focus_mask=products["mask"],
                analysis_bands=analysis_bands,
                grid_spec=self.grid_spec,
            )
        )
        outputs = write_focus_mask_outputs(context.run_dir, self.grid_spec, products)
        artifacts = [
            build_stage_artifact(
                name="focus_zone_17m_tif",
                relative_path=outputs["focus_mask_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_mask_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_zone_17m_npy",
                relative_path=outputs["focus_mask_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_mask_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_zone_ai_ready_window",
                relative_path=outputs["focus_window_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_window_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_zone_summary",
                relative_path=outputs["focus_summary_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_summary_json"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_band_summary",
                relative_path=outputs["focus_band_summary_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_band_summary_csv"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_17m_pixel_report_v7_2",
                relative_path=outputs["focus_pixel_report_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_pixel_report_csv"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_17m_targets_v7_2",
                relative_path=outputs["focus_target_report_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_target_report_csv"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_17m_targets_geojson_v7_2",
                relative_path=outputs["focus_target_geojson"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_target_geojson"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="hard_type_classifier_core9_csv",
                relative_path=outputs["hard_type_classifier_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["hard_type_classifier_csv"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="hard_type_classifier_core9_txt",
                relative_path=outputs["hard_type_classifier_txt"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["hard_type_classifier_txt"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="hard_type_classifier_core9_json",
                relative_path=outputs["hard_type_classifier_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["hard_type_classifier_json"].stat().st_size,
                http_servable=False,
            ),
        ]
        summary = products["summary"]
        assert isinstance(summary, dict)
        target_records = products["target_records"]
        hard_type_record = products["hard_type_record"]
        assert isinstance(target_records, list)
        assert isinstance(hard_type_record, dict)
        return StageResult(
            artifacts=artifacts,
            metadata={
                "focus_size_m": float(summary["focus_size_m"]),
                "mask_pixel_count": int(summary["mask_pixel_count"]),
                "window_shape": summary["window_shape"],
                "roi_pixel_report": FOCUS_PIXEL_REPORT_CSV_NAME,
                "roi_target_report": FOCUS_TARGET_REPORT_CSV_NAME,
                "roi_target_geojson": FOCUS_TARGET_GEOJSON_NAME,
                "target_count": len(target_records),
                "hard_type_classifier_csv": HARD_TYPE_CLASSIFIER_CSV_NAME,
                "hard_type_classifier_txt": HARD_TYPE_CLASSIFIER_TXT_NAME,
                "hard_type_classifier_json": HARD_TYPE_CLASSIFIER_JSON_NAME,
                "hard_type_primary_class": hard_type_record["Primary_Class"],
                "hard_type_source_cell": "cell_128",
            },
        )
