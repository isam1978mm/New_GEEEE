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
from app.pipeline.parity.metal_fingerprint_diagnostic import write_plan_b33_metal_fingerprint_diagnostic_outputs
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
CORE_RING_SCENE_TARGETS_CSV_NAME = "AI_CORE_RING_SCENE_TARGETS_V7_2C.csv"
CORE_RING_SCENE_DECISION_TXT_NAME = "AI_CORE_RING_SCENE_DECISION_V7_2C.txt"
CORE_RING_SCENE_DECISION_JSON_NAME = "AI_CORE_RING_SCENE_DECISION_V7_2C.json"
DETECTED_FEATURES_WGS84_GEOJSON_NAME = "AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson"
HEATMAP_CLASSIFICATION_PNG_NAME = "AI_HEATMAP_CLASSIFICATION.png"
HEATMAP_CLASSIFICATION_KMZ_NAME = "AI_HEATMAP_CLASSIFICATION.kmz"
TARGET_3D_VISUALIZATION_KMZ_NAME = "AI_3D_TARGET_VISUALIZATION.kmz"
FIELD_OPERATIONS_GEOJSON_NAME = "FINAL_ARCHEO_INTELLIGENCE_MAP.geojson"
FIELD_OPERATIONS_KMZ_NAME = "TESLA_V7_2_FIELD_OPERATIONS.kmz"
LIVE_OVERLAY_MANIFEST_NAME = "APP_NATIVE_LIVE_OVERLAY_MANIFEST_V7_2.json"
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


def _focus_softmax_dict(score_dict: dict[str, float]) -> dict[str, float]:
    keys = list(score_dict.keys())
    vals = np.array([score_dict[k] for k in keys], dtype=np.float64)

    if np.all(~np.isfinite(vals)):
        return {k: 1.0 / len(keys) for k in keys}

    vals[~np.isfinite(vals)] = -9999.0
    vals = vals - np.nanmax(vals)
    ex = np.exp(vals)
    den = ex.sum()
    if den <= 0 or not np.isfinite(den):
        return {k: 1.0 / len(keys) for k in keys}
    probs = ex / den
    return {k: float(v) for k, v in zip(keys, probs)}


def _focus_google_maps_link(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}"


def _infer_focus_ai_target(row: dict[str, object]) -> dict[str, object]:
    metal = float(row["محور_معدني"])
    void = float(row["محور_فراغ"])
    struct = float(row["محور_بنيوي"])

    gold = float(row["z_Gold"])
    silver = float(row["z_Silver"])
    tunnel = float(row["z_Tunnel"])
    thermal = float(row["z_Thermal"])
    doors = float(row["z_Doors"])
    mass = float(row["z_Mass"])
    pottery = float(row["z_Pottery"])
    zero = float(row["z_Zero"])
    chem = float(row["z_Chemical"])

    form_scores = {
        "ناووس": 1.35 * struct + 1.10 * mass + 0.25 * metal - 0.15 * void,
        "تابوت": 1.20 * struct + 0.95 * mass + 0.35 * metal,
        "ران": 1.30 * metal + 1.00 * mass + 0.30 * struct,
        "صندوق": 1.35 * metal + 0.95 * mass + 0.20 * doors,
        "صناديق متراكبة عمودية": 1.20 * metal + 1.10 * mass + 0.65 * struct,
        "صناديق متراكبة أفقية": 1.15 * metal + 1.05 * mass + 0.60 * struct,
        "جرة فخارية": 1.20 * pottery + 0.55 * metal + 0.20 * thermal,
        "جرار فخارية": 1.25 * pottery + 0.65 * mass + 0.20 * struct,
        "غرفة": 1.20 * void + 1.10 * struct + 0.55 * mass,
        "غرفة تكنيزية": 1.10 * void + 1.15 * struct + 0.95 * metal + 0.75 * mass,
        "غرفة بقايا عضوية": 1.00 * void + 0.75 * thermal + 0.55 * pottery + 0.35 * chem,
        "سرداب": 1.35 * void + 1.10 * tunnel + 0.55 * struct,
        "ممر": 1.20 * void + 1.15 * tunnel + 0.45 * doors,
        "مدخل": 1.30 * struct + 1.15 * doors + 0.55 * void,
        "باب": 1.25 * struct + 1.20 * doors + 0.35 * mass,
        "باب سري": 1.35 * doors + 1.10 * struct + 0.40 * void,
        "جب": 1.30 * void + 0.85 * thermal + 0.35 * doors,
        "بئر جانبي سفلي": 1.35 * void + 0.90 * thermal + 0.45 * tunnel,
        "درج مستقيم": 1.20 * struct + 0.95 * void + 0.40 * thermal,
        "درج لولبي": 1.30 * struct + 1.00 * void + 0.55 * thermal + 0.20 * doors,
        "قبر شمسي": 1.10 * struct + 0.95 * mass + 0.45 * thermal,
        "قبر ملكي": 1.25 * struct + 1.05 * mass + 0.75 * metal + 0.35 * void,
        "قبر روماني": 1.15 * struct + 0.95 * mass + 0.40 * pottery,
        "قبر بيزنطي": 1.10 * struct + 0.90 * mass + 0.45 * thermal + 0.30 * pottery,
        "دفين يوناني": 1.10 * metal + 0.85 * mass + 0.35 * pottery,
        "دفين عثماني": 1.20 * metal + 0.80 * silver + 0.35 * mass,
        "دفين غرفة": 1.05 * void + 1.00 * struct + 0.90 * metal + 0.70 * mass,
        "تمثال": 1.10 * mass + 0.85 * metal + 0.30 * struct,
        "سبائك": 1.35 * metal + 1.05 * gold + 0.65 * mass,
        "عملات": 1.15 * metal + 1.00 * silver + 0.35 * pottery,
        "زجاج": 0.95 * pottery + 0.35 * thermal + 0.15 * metal,
        "أحجار كريمة": 1.05 * gold + 0.65 * chem + 0.25 * metal,
        "زئبق أحمر": 1.15 * chem + 0.85 * thermal + 0.35 * metal,
        "زئبق أسود": 1.20 * chem + 0.95 * void + 0.20 * thermal,
        "أسلحة أثرية": 1.15 * metal + 0.95 * mass + 0.30 * struct,
        "سيف": 1.10 * metal + 0.85 * mass + 0.20 * struct,
        "درع": 1.05 * metal + 0.95 * mass + 0.25 * struct,
        "خوذة": 1.00 * metal + 0.85 * mass + 0.20 * thermal,
        "ترس": 1.00 * metal + 0.90 * mass + 0.20 * struct,
        "مسدس عثماني": 1.20 * metal + 0.80 * silver + 0.45 * mass,
        "فخ سلك معدني": 1.10 * metal + 0.95 * struct + 0.25 * doors,
        "بلاطة منزلقة": 1.25 * struct + 0.85 * doors + 0.35 * mass,
        "فخ غير محدد": 1.00 * struct + 0.90 * void + 0.35 * doors,
    }

    content_scores = {
        "ذهب": 1.35 * gold + 0.55 * metal,
        "فضة": 1.25 * silver + 0.45 * metal,
        "نحاس": 0.95 * metal + 0.35 * silver + 0.15 * mass,
        "معادن مختلطة": 1.00 * metal + 0.45 * silver + 0.35 * mass,
        "فخار": 1.30 * pottery + 0.20 * thermal,
        "زجاج": 1.10 * pottery + 0.30 * thermal,
        "أحجار كريمة": 1.10 * chem + 0.55 * gold,
        "زئبق أحمر": 1.25 * chem + 0.85 * thermal,
        "زئبق أسود": 1.20 * chem + 0.90 * void,
        "كتلة حجرية": 1.15 * mass + 0.75 * struct,
        "بقايا عضوية": 0.95 * thermal + 0.75 * pottery + 0.35 * chem,
        "فراغ صرف": 1.30 * void + 0.25 * tunnel,
        "محتوى غير محسوم": 0.20,
    }

    burial_scores = {
        "دفن روماني": 1.10 * struct + 0.85 * mass + 0.35 * pottery,
        "دفن بيزنطي": 1.05 * struct + 0.80 * mass + 0.35 * thermal,
        "دفن عثماني": 1.00 * metal + 0.75 * silver + 0.30 * mass,
        "دفن يوناني": 0.95 * metal + 0.70 * pottery + 0.30 * mass,
        "دفن أيّوبي": 0.95 * struct + 0.70 * mass + 0.25 * thermal,
        "دفن آشوري": 1.05 * struct + 0.85 * mass + 0.20 * metal,
        "دفن يهودي": 0.90 * struct + 0.70 * mass + 0.20 * thermal,
        "غير محسوم": 0.25,
    }

    form_probs = _focus_softmax_dict(form_scores)
    content_probs = _focus_softmax_dict(content_scores)
    burial_probs = _focus_softmax_dict(burial_scores)

    best_form = max(form_probs, key=form_probs.get)
    best_content = max(content_probs, key=content_probs.get)
    best_burial = max(burial_probs, key=burial_probs.get)

    conf_form = form_probs[best_form] * 100.0
    conf_content = content_probs[best_content] * 100.0
    conf_burial = burial_probs[best_burial] * 100.0
    final_conf = (0.55 * conf_form) + (0.25 * conf_content) + (0.20 * conf_burial)

    trap_score = max(form_scores["فخ سلك معدني"], form_scores["بلاطة منزلقة"], form_scores["فخ غير محدد"])
    trap_flag = "تحذير فخ" if trap_score > np.percentile(list(form_scores.values()), 75) else "لا يوجد تحذير فخ واضح"

    interpretation = (
        f"محور معدني={metal:.2f} | محور فراغ={void:.2f} | محور بنيوي={struct:.2f} | "
        f"الشكل المرجح={best_form} | المحتوى المرجح={best_content} | "
        f"نظام الدفن/الحقبة المرجحة={best_burial} | {trap_flag}"
    )

    return {
        "الهدف_المرجح": best_form,
        "المحتوى_المرجح": best_content,
        "نظام_الدفن_او_الحقبة_المرجحة": best_burial,
        "تحذير_الفخاخ": trap_flag,
        "ثقة_الشكل_%": round(conf_form, 1),
        "ثقة_المحتوى_%": round(conf_content, 1),
        "ثقة_الحقبة_%": round(conf_burial, 1),
        "الثقة_النهائية_%": round(final_conf, 1),
        "تفسير_الذكاء": interpretation,
    }


def build_focus_roi_analysis_products(
    *,
    focus_mask: np.ndarray,
    analysis_bands: dict[str, np.ndarray],
    grid_spec: GridSpec,
) -> dict[str, object]:
    from pyproj import Transformer

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

    to_wgs84 = Transformer.from_crs(grid_spec.crs, "EPSG:4326", always_xy=True)
    affine = Affine(*grid_spec.transform)

    pixel_records: list[dict[str, object]] = []
    for r, c in zip(rows, cols):
        x, y = rasterio.transform.xy(affine, int(r), int(c), offset="center")
        lon, lat = to_wgs84.transform(float(x), float(y))

        record: dict[str, object] = {
            "row": int(r),
            "col": int(c),
            "X_native": round(float(x), 3),
            "Y_native": round(float(y), 3),
            "UTM_E": round(float(x), 3),
            "UTM_N": round(float(y), 3),
            "Lon": round(float(lon), 8),
            "Lat": round(float(lat), 8),
            "Google_Maps_Link": _focus_google_maps_link(float(lat), float(lon)),
            "Secret_Gold_Halo": float(analysis_bands["Secret_Gold_Halo"][r, c]),
            "Secret_Silver_Oxide": float(analysis_bands["Secret_Silver_Oxide"][r, c]),
            "Secret_Tunnel_Ceiling": float(analysis_bands["Secret_Tunnel_Ceiling"][r, c]),
            "Secret_Thermal_Inertia": float(analysis_bands["Secret_Thermal_Inertia"][r, c]),
            "Secret_Chemical_Protector": float(analysis_bands["Secret_Chemical_Protector"][r, c]),
            "Secret_Hidden_Doors": float(analysis_bands["Secret_Hidden_Doors"][r, c]),
            "REPORT_640_FINAL_Zero_Point_Targets": float(analysis_bands["REPORT_640_FINAL_Zero_Point_Targets"][r, c]),
            "REPORT_640_Mass_Report": float(analysis_bands["REPORT_640_Mass_Report"][r, c]),
            "REPORT_640_Pottery_Report": float(analysis_bands["REPORT_640_Pottery_Report"][r, c]),
            "z_Gold": float(z_bands["Secret_Gold_Halo"][r, c]),
            "z_Silver": float(z_bands["Secret_Silver_Oxide"][r, c]),
            "z_Tunnel": float(z_bands["Secret_Tunnel_Ceiling"][r, c]),
            "z_Thermal": float(z_bands["Secret_Thermal_Inertia"][r, c]),
            "z_Chemical": float(z_bands["Secret_Chemical_Protector"][r, c]),
            "z_Doors": float(z_bands["Secret_Hidden_Doors"][r, c]),
            "z_Zero": float(z_bands["REPORT_640_FINAL_Zero_Point_Targets"][r, c]),
            "z_Mass": float(z_bands["REPORT_640_Mass_Report"][r, c]),
            "z_Pottery": float(z_bands["REPORT_640_Pottery_Report"][r, c]),
        }

        record["محور_معدني"] = (
            1.30 * float(record["z_Gold"])
            + 1.10 * float(record["z_Silver"])
            + 0.90 * float(record["z_Mass"])
            + 0.40 * float(record["z_Chemical"])
        )
        record["محور_فراغ"] = (
            1.20 * float(record["z_Tunnel"])
            + 1.00 * float(record["z_Thermal"])
            + 0.70 * float(record["z_Doors"])
            + 0.30 * float(record["z_Zero"])
        )
        record["محور_بنيوي"] = (
            1.25 * float(record["z_Doors"])
            + 1.00 * float(record["z_Tunnel"])
            + 0.85 * float(record["z_Mass"])
            + 0.35 * float(record["z_Thermal"])
        )
        record["درجة_مركبة"] = (
            1.00 * float(record["محور_معدني"])
            + 0.90 * float(record["محور_فراغ"])
            + 0.95 * float(record["محور_بنيوي"])
            + 0.40 * float(record["z_Pottery"])
        )

        pixel_records.append(record)

    pixel_records.sort(key=lambda item: float(item["درجة_مركبة"]), reverse=True)

    target_source = pixel_records[: min(5, len(pixel_records))]
    target_fields = [
        "Target_ID",
        "الهدف_المرجح",
        "المحتوى_المرجح",
        "نظام_الدفن_او_الحقبة_المرجحة",
        "تحذير_الفخاخ",
        "ثقة_الشكل_%",
        "ثقة_المحتوى_%",
        "ثقة_الحقبة_%",
        "الثقة_النهائية_%",
        "تفسير_الذكاء",
        "X_native",
        "Y_native",
        "UTM_E",
        "UTM_N",
        "Lon",
        "Lat",
        "Google_Maps_Link",
        "row",
        "col",
        "محور_معدني",
        "محور_فراغ",
        "محور_بنيوي",
        "درجة_مركبة",
        "Secret_Gold_Halo",
        "Secret_Silver_Oxide",
        "Secret_Tunnel_Ceiling",
        "Secret_Thermal_Inertia",
        "Secret_Chemical_Protector",
        "Secret_Hidden_Doors",
        "REPORT_640_FINAL_Zero_Point_Targets",
        "REPORT_640_Mass_Report",
        "REPORT_640_Pottery_Report",
    ]

    target_records: list[dict[str, object]] = []
    for index, source in enumerate(target_source, start=1):
        inferred = _infer_focus_ai_target(source)
        merged = dict(source)
        merged.update(inferred)
        merged["Target_ID"] = int(index)
        target_records.append({field: merged[field] for field in target_fields})

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(row["Lon"]), float(row["Lat"])]},
            "properties": {
                "Target_ID": int(row["Target_ID"]),
                "الهدف_المرجح": row["الهدف_المرجح"],
                "المحتوى_المرجح": row["المحتوى_المرجح"],
                "نظام_الدفن_او_الحقبة_المرجحة": row["نظام_الدفن_او_الحقبة_المرجحة"],
                "تحذير_الفخاخ": row["تحذير_الفخاخ"],
                "الثقة_النهائية_%": float(row["الثقة_النهائية_%"]),
                "UTM_E": float(row["UTM_E"]),
                "UTM_N": float(row["UTM_N"]),
                "Google_Maps_Link": row["Google_Maps_Link"],
                "تفسير_الذكاء": row["تفسير_الذكاء"],
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


def _hard_safe_std(arr: np.ndarray, mask: np.ndarray) -> float:
    vals = arr[mask]
    vals = vals[np.isfinite(vals)]
    return float(np.std(vals)) if len(vals) else 0.0


def _hard_count_local_peaks(score_map: np.ndarray, mask: np.ndarray, *, threshold_q: float) -> int:
    vals = score_map[mask]
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return 0
    threshold = float(np.percentile(vals, threshold_q))
    try:
        from scipy import ndimage

        local_max = ndimage.maximum_filter(score_map, size=3, mode="nearest")
        peaks = (score_map == local_max) & (score_map >= threshold) & mask
        _labels, count = ndimage.label(peaks)
        return int(count)
    except Exception:
        return int(np.count_nonzero((score_map >= threshold) & mask))


def _hard_connected_components_above(arr: np.ndarray, mask: np.ndarray, threshold_q: float = 70) -> int:
    vals = arr[mask]
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return 0
    threshold = float(np.percentile(vals, threshold_q))
    bin_mask = (arr >= threshold) & mask
    try:
        from scipy import ndimage

        _labels, count = ndimage.label(bin_mask)
        return int(count)
    except Exception:
        return int(np.count_nonzero(bin_mask))

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
            arr,
            core_mask=core_mask,
            ring_near=ring_near,
            ring_far=ring_far,
            ring_wide=ring_wide,
            scene_mask=scene_mask,
        )
        for name, arr in analysis_bands.items()
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
    rr, cc = np.indices(core_mask.shape)

    r0 = int(focus_rows.min())
    r1 = int(focus_rows.max())
    c0 = int(focus_cols.min())
    c1 = int(focus_cols.max())

    north = np.zeros_like(core_mask, dtype=bool)
    south = np.zeros_like(core_mask, dtype=bool)
    west = np.zeros_like(core_mask, dtype=bool)
    east = np.zeros_like(core_mask, dtype=bool)

    if r0 - 1 >= 0:
        north[max(r0 - 1, 0):r0, c0:c1 + 1] = True
    if r1 + 2 <= core_mask.shape[0]:
        south[r1 + 1:min(r1 + 2, core_mask.shape[0]), c0:c1 + 1] = True
    if c0 - 1 >= 0:
        west[r0:r1 + 1, max(c0 - 1, 0):c0] = True
    if c1 + 2 <= core_mask.shape[1]:
        east[r0:r1 + 1, c1 + 1:min(c1 + 2, core_mask.shape[1])] = True

    def strip_score(mask: np.ndarray) -> float:
        if int(mask.sum()) == 0:
            return 0.0
        return (
            0.95 * _hard_safe_mean(doors, mask)
            + 0.80 * _hard_safe_mean(tunnel, mask)
            + 0.45 * _hard_safe_mean(thermal, mask)
        )

    dir_scores = {
        "north": strip_score(north),
        "south": strip_score(south),
        "west": strip_score(west),
        "east": strip_score(east),
    }
    best_dir = max(dir_scores, key=dir_scores.get)
    sorted_dir = sorted(dir_scores.values(), reverse=True)
    raw_dir_gap = float(sorted_dir[0] - sorted_dir[1]) if len(sorted_dir) > 1 else 0.0
    directionality_strength = _hard_clip01(float(np.tanh(max(0.0, raw_dir_gap) / 4.5)))

    void_family_score = (
        1.55 * _hard_rc(stats, "Secret_Tunnel_Ceiling", "rc_scene")
        + 1.15 * _hard_rc(stats, "Secret_Tunnel_Ceiling", "rc_near")
        + 1.25 * _hard_rc(stats, "Secret_Thermal_Inertia", "rc_scene")
        + 0.85 * _hard_rc(stats, "Secret_Thermal_Inertia", "rc_near")
        + 1.05 * _hard_rc(stats, "Secret_Hidden_Doors", "rc_scene")
        + 0.75 * _hard_rc(stats, "Secret_Hidden_Doors", "rc_near")
        - 0.40 * _hard_rc(stats, "Secret_Chemical_Protector", "rc_scene")
        - 0.25 * _hard_rc(stats, "REPORT_640_FINAL_Zero_Point_Targets", "rc_scene")
    )
    metal_family_score = (
        1.30 * _hard_rc(stats, "REPORT_640_Mass_Report", "rc_scene")
        + 1.05 * _hard_rc(stats, "REPORT_640_Mass_Report", "rc_near")
        + 1.00 * _hard_rc(stats, "Secret_Gold_Halo", "rc_scene")
        + 0.82 * _hard_rc(stats, "Secret_Silver_Oxide", "rc_scene")
        + 0.85 * _hard_rc(stats, "AI_READY_640_Magnetic_Anomaly", "rc_scene")
        + 0.75 * _hard_rc(stats, "AI_READY_640_EM_Anomaly", "rc_scene")
    )
    fill_family_score = (
        1.20 * _hard_rc(stats, "REPORT_640_Pottery_Report", "rc_scene")
        + 0.80 * _hard_rc(stats, "REPORT_640_Pottery_Report", "rc_near")
        + 0.52 * _hard_rc(stats, "Secret_Chemical_Protector", "rc_scene")
        + 0.30 * _hard_rc(stats, "Secret_Thermal_Inertia", "rc_scene")
    )
    entrance_family_score = (
        1.05 * _hard_rc(stats, "Secret_Hidden_Doors", "rc_near")
        + 0.85 * _hard_rc(stats, "Secret_Hidden_Doors", "rc_scene")
        + 0.72 * _hard_rc(stats, "Secret_Tunnel_Ceiling", "rc_near")
        + 0.58 * _hard_rc(stats, "Secret_Thermal_Inertia", "rc_near")
        + 0.95 * directionality_strength
    )

    surface_penalty_raw = (
        0.80 * abs(_hard_rc(stats, "DEM_Slope", "rc_scene"))
        + 0.65 * abs(_hard_rc(stats, "DEM_Roughness", "rc_scene"))
        - 0.50 * abs(_hard_rc(stats, "DEM_TPI", "rc_scene"))
    )
    surface_exclusion_score = _hard_clip01(_hard_prob(1.2 - surface_penalty_raw, bias=0.0, gain=1.0))

    p_void_raw = _hard_prob(void_family_score, bias=0.85, gain=0.90)
    p_metal_raw = _hard_prob(metal_family_score, bias=0.70, gain=0.90)
    p_fill_raw = _hard_prob(fill_family_score, bias=0.70, gain=0.85)
    p_entry_raw = _hard_prob(entrance_family_score, bias=0.90, gain=0.85)

    surface_gate = _hard_clip01(0.20 + 0.80 * surface_exclusion_score)
    entry_gate = _hard_clip01(0.55 * p_void_raw + 0.45 * directionality_strength)

    p_void = p_void_raw
    p_entry = _hard_clip01(p_entry_raw * entry_gate * (0.75 + 0.25 * surface_gate))
    p_metal = _hard_clip01(p_metal_raw * (0.65 + 0.35 * surface_gate))
    p_fill = _hard_clip01(p_fill_raw * (0.60 + 0.40 * surface_gate))

    shaft_score = _hard_clip01(
        0.42 * p_void
        + 0.18 * directionality_strength
        + 0.12 * _hard_clip01(_hard_prob(_hard_rc(stats, "Secret_Tunnel_Ceiling", "rc_near"), bias=0.3, gain=1.0))
        + 0.14 * _hard_clip01(_hard_prob(_hard_rc(stats, "Secret_Hidden_Doors", "rc_near"), bias=0.2, gain=1.0))
        + 0.14 * surface_exclusion_score
    )
    entrance_score = _hard_clip01(
        0.34 * p_void
        + 0.30 * p_entry
        + 0.18 * directionality_strength
        + 0.18 * _hard_clip01(_hard_prob(_hard_rc(stats, "Secret_Hidden_Doors", "rc_near"), bias=0.25, gain=1.1))
    )
    chamber_score = _hard_clip01(
        0.45 * p_void
        + 0.18 * surface_exclusion_score
        + 0.15 * _hard_clip01(_hard_prob(_hard_rc(stats, "Secret_Tunnel_Ceiling", "rc_scene"), bias=0.45, gain=1.0))
        + 0.12 * _hard_clip01(_hard_prob(_hard_rc(stats, "Secret_Thermal_Inertia", "rc_scene"), bias=0.40, gain=1.0))
        - 0.10 * directionality_strength
    )
    drain_void_score = _hard_clip01(
        0.32 * p_void
        + 0.30 * p_fill
        + 0.18 * _hard_clip01(_hard_prob(_hard_rc(stats, "Secret_Chemical_Protector", "rc_scene"), bias=0.20, gain=1.0))
        + 0.20 * _hard_clip01(_hard_prob(_hard_rc(stats, "REPORT_640_Pottery_Report", "rc_scene"), bias=0.20, gain=1.0))
    )

    gold_like_score = _hard_clip01(
        0.42 * p_metal
        + 0.30 * _hard_clip01(_hard_prob(_hard_rc(stats, "Secret_Gold_Halo", "rc_scene"), bias=0.35, gain=1.0))
        - 0.12 * _hard_clip01(_hard_prob(_hard_rc(stats, "Secret_Silver_Oxide", "rc_scene"), bias=0.55, gain=1.0))
        + 0.16 * _hard_clip01(_hard_prob(_hard_rc(stats, "REPORT_640_Mass_Report", "rc_scene"), bias=0.35, gain=1.0))
        + 0.12 * surface_exclusion_score
    )
    silver_like_score = _hard_clip01(
        0.42 * p_metal
        + 0.30 * _hard_clip01(_hard_prob(_hard_rc(stats, "Secret_Silver_Oxide", "rc_scene"), bias=0.35, gain=1.0))
        - 0.08 * _hard_clip01(_hard_prob(_hard_rc(stats, "Secret_Gold_Halo", "rc_scene"), bias=0.65, gain=1.0))
        + 0.16 * _hard_clip01(_hard_prob(_hard_rc(stats, "REPORT_640_Mass_Report", "rc_scene"), bias=0.35, gain=1.0))
        + 0.12 * surface_exclusion_score
    )
    dense_metal_score = _hard_clip01(
        0.55 * p_metal
        + 0.22 * _hard_clip01(_hard_prob(_hard_rc(stats, "REPORT_640_Mass_Report", "rc_scene"), bias=0.45, gain=1.0))
        + 0.13 * _hard_clip01(_hard_prob(_hard_rc(stats, "AI_READY_640_Magnetic_Anomaly", "rc_scene"), bias=0.20, gain=1.0))
        + 0.10 * _hard_clip01(_hard_prob(_hard_rc(stats, "AI_READY_640_EM_Anomaly", "rc_scene"), bias=0.20, gain=1.0))
    )

    coins_score = _hard_clip01(
        0.34 * p_metal
        + 0.18 * gold_like_score
        + 0.16 * silver_like_score
        + 0.12 * _hard_clip01(_hard_prob(_hard_connected_components_above(gold, core_mask, 60), bias=1.0, gain=1.2))
        + 0.10 * _hard_clip01(_hard_prob(_hard_connected_components_above(silver, core_mask, 60), bias=1.0, gain=1.2))
        - 0.10 * _hard_clip01(_hard_prob(_hard_rc(stats, "REPORT_640_Mass_Report", "rc_scene"), bias=0.95, gain=1.0))
    )
    ingots_score = _hard_clip01(
        0.42 * p_metal
        + 0.26 * dense_metal_score
        + 0.12 * _hard_clip01(_hard_prob(_hard_rc(stats, "REPORT_640_Mass_Report", "rc_scene"), bias=0.60, gain=1.0))
        + 0.10 * _hard_clip01(_hard_prob(_hard_safe_mean(mass, core_mask), bias=float(np.nanmean(mass)), gain=1e-5))
        + 0.10 * surface_exclusion_score
    )
    statues_score = _hard_clip01(
        0.28 * p_metal
        + 0.22 * dense_metal_score
        + 0.18 * _hard_clip01(_hard_prob(_hard_safe_std(mass, core_mask), bias=max(1e-6, float(np.nanstd(mass))), gain=1e-5))
        + 0.16 * _hard_clip01(_hard_prob(_hard_safe_std(gold, core_mask) + _hard_safe_std(silver, core_mask), bias=0.15, gain=1.5))
        + 0.16 * surface_exclusion_score
    )
    pottery_treasures_score = _hard_clip01(
        0.34 * p_fill
        + 0.18 * p_void
        + 0.18 * _hard_clip01(_hard_prob(_hard_rc(stats, "REPORT_640_Pottery_Report", "rc_scene"), bias=0.35, gain=1.0))
        + 0.14 * _hard_clip01(_hard_prob(_hard_rc(stats, "Secret_Chemical_Protector", "rc_scene"), bias=0.10, gain=1.0))
        + 0.16 * surface_exclusion_score
    )
    general_antiquities_score = _hard_clip01(
        0.22 * p_void
        + 0.22 * p_metal
        + 0.18 * p_fill
        + 0.18 * surface_exclusion_score
        + 0.20 * max(gold_like_score, silver_like_score, dense_metal_score)
    )

    metal_combo = 0.0
    if "AI_READY_640_Magnetic_Anomaly" in analysis_bands:
        metal_combo = (
            0.40 * _hard_robust_norm(mass)
            + 0.30 * _hard_robust_norm(gold)
            + 0.20 * _hard_robust_norm(silver)
            + 0.10 * _hard_robust_norm(analysis_bands["AI_READY_640_Magnetic_Anomaly"])
        )
    if isinstance(metal_combo, float):
        metal_combo = (
            0.55 * _hard_robust_norm(mass)
            + 0.25 * _hard_robust_norm(gold)
            + 0.20 * _hard_robust_norm(silver)
        )

    metal_core_values = metal_combo[core_mask]
    if np.isfinite(metal_core_values).sum() > 0:
        thr_core = float(np.percentile(metal_core_values[np.isfinite(metal_core_values)], 70))
        metal_shape_mask = (metal_combo >= thr_core) & core_mask
    else:
        metal_shape_mask = core_mask.copy()

    elongation = _hard_elongation_from_mask(metal_shape_mask)
    orientation = _hard_axis_orientation(metal_shape_mask)
    if p_metal < 0.50:
        metal_shape = "NO_CONFIRMED_METAL_SHAPE"
    elif elongation >= 2.2 and orientation in {"N_S", "E_W", "NE_SW", "NW_SE"}:
        metal_shape = f"LINEAR_{orientation}"
    elif 1.4 <= elongation < 2.2:
        metal_shape = f"ELLIPSOID_{orientation}"
    else:
        metal_shape = "COMPACT_CLUSTER"

    box_peak_map = (
        0.55 * _hard_robust_norm(mass)
        + 0.25 * _hard_robust_norm(gold)
        + 0.20 * _hard_robust_norm(silver)
    )
    jar_peak_map = (
        0.55 * _hard_robust_norm(pottery)
        + 0.25 * _hard_robust_norm(thermal)
        + 0.20 * _hard_robust_norm(chemical)
    )

    analysis_mask = core_mask | ring_near
    estimated_stacked_boxes = 0
    estimated_aligned_jars = 0
    if p_metal >= 0.58 and dense_metal_score >= 0.58:
        estimated_stacked_boxes = min(4, max(1, _hard_count_local_peaks(box_peak_map, analysis_mask, threshold_q=75)))
    if p_fill >= 0.56 and pottery_treasures_score >= 0.56:
        estimated_aligned_jars = min(6, max(1, _hard_count_local_peaks(jar_peak_map, analysis_mask, threshold_q=72)))

    if p_void >= 0.60 and p_metal >= 0.58 and surface_exclusion_score >= 0.55:
        primary_class = "MIXED_VOID_METAL"
    elif p_void >= 0.60 and surface_exclusion_score >= 0.55:
        primary_class = "STRUCTURAL_VOID"
    elif p_metal >= 0.58 and surface_exclusion_score >= 0.50:
        primary_class = "METAL_DENSE"
    elif p_fill >= 0.56:
        primary_class = "FILL_OR_POTTERY_DISTURBANCE"
    else:
        primary_class = "INCONCLUSIVE"

    void_subscores = {
        "ENTRANCE": entrance_score,
        "SHAFT": shaft_score,
        "CHAMBER": chamber_score,
        "DRAIN_VOID": drain_void_score,
    }
    best_void_subtype = max(void_subscores, key=void_subscores.get)
    best_void_subscore = void_subscores[best_void_subtype]

    if primary_class in {"STRUCTURAL_VOID", "MIXED_VOID_METAL"} and p_void >= 0.60:
        if best_void_subtype == "ENTRANCE" and entrance_score >= 0.58 and p_entry >= 0.50:
            void_type = "ENTRANCE"
        elif best_void_subtype == "SHAFT" and shaft_score >= 0.58:
            void_type = "SHAFT"
        elif best_void_subtype == "CHAMBER" and chamber_score >= 0.58:
            void_type = "CHAMBER"
        elif best_void_subtype == "DRAIN_VOID" and drain_void_score >= 0.56:
            void_type = "DRAIN_VOID"
        else:
            void_type = "VOID_UNRESOLVED"
    else:
        void_type = "NO_CONFIRMED_VOID"

    metal_subscores = {
        "GOLD_LIKE": gold_like_score,
        "SILVER_LIKE": silver_like_score,
        "DENSE_METAL": dense_metal_score,
    }
    best_metal_subtype = max(metal_subscores, key=metal_subscores.get)
    best_metal_subscore = metal_subscores[best_metal_subtype]

    if primary_class in {"METAL_DENSE", "MIXED_VOID_METAL"} and p_metal >= 0.58:
        if gold_like_score >= 0.60 and gold_like_score > silver_like_score + 0.04:
            metal_type = "GOLD_LIKE"
        elif silver_like_score >= 0.60 and silver_like_score >= gold_like_score:
            metal_type = "SILVER_LIKE"
        elif dense_metal_score >= 0.58:
            metal_type = "DENSE_METAL"
        else:
            metal_type = "METAL_UNRESOLVED"
    else:
        metal_type = "NO_CONFIRMED_METAL"

    content_scores = {
        "COINS": coins_score,
        "INGOTS": ingots_score,
        "STATUES": statues_score,
        "POTTERY_TREASURES": pottery_treasures_score,
        "GENERAL_ANTIQUITIES": general_antiquities_score,
    }
    best_content = max(content_scores, key=content_scores.get)
    best_content_score = content_scores[best_content]

    if primary_class == "INCONCLUSIVE":
        content_type = "UNRESOLVED_CONTENT"
    else:
        if best_content == "COINS" and coins_score >= 0.57 and metal_type in {"GOLD_LIKE", "SILVER_LIKE", "DENSE_METAL"}:
            content_type = "COINS"
        elif best_content == "INGOTS" and ingots_score >= 0.58 and metal_type in {"GOLD_LIKE", "DENSE_METAL"}:
            content_type = "INGOTS"
        elif best_content == "STATUES" and statues_score >= 0.58 and metal_type in {"DENSE_METAL", "GOLD_LIKE", "SILVER_LIKE"}:
            content_type = "STATUES"
        elif best_content == "POTTERY_TREASURES" and pottery_treasures_score >= 0.56:
            content_type = "POTTERY_TREASURES"
        elif general_antiquities_score >= 0.54:
            content_type = "GENERAL_ANTIQUITIES"
        else:
            content_type = "UNRESOLVED_CONTENT"

    final_confidence = _hard_clip01(
        0.24 * max(p_void, p_metal, p_fill)
        + 0.14 * surface_exclusion_score
        + 0.12 * max(best_void_subscore, best_metal_subscore, best_content_score)
        + 0.10 * directionality_strength
        + 0.10 * _hard_clip01(_hard_prob(abs(_hard_rc(stats, "REPORT_640_Mass_Report", "rc_scene")), bias=0.35, gain=1.0))
        + 0.10 * _hard_clip01(_hard_prob(abs(_hard_rc(stats, "Secret_Tunnel_Ceiling", "rc_scene")), bias=0.35, gain=1.0))
        + 0.10 * _hard_clip01(_hard_prob(abs(_hard_rc(stats, "Secret_Hidden_Doors", "rc_scene")), bias=0.20, gain=1.0))
        + 0.10 * _hard_clip01(_hard_prob(abs(_hard_rc(stats, "REPORT_640_Pottery_Report", "rc_scene")), bias=0.20, gain=1.0))
    )

    active_core_name = "FOCUS_MASK_" + "17M"

    record = {
        "Core_Mask_Source": active_core_name,
        "Core_Pixels": int(core_mask.sum()),
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

    hard_type_json = {
        "core_mask_name": active_core_name,
        "core_pixels": int(core_mask.sum()),
        "near_ring_pixels": int(ring_near.sum()),
        "far_ring_pixels": int(ring_far.sum()),
        "wide_ring_pixels": int(ring_wide.sum()),
        "crs": grid_spec.crs,
        "analysis_pixel_m": 2.0,
        "native_pixel_m": 10.0,
        "is_super_resolved": True,
        "void_family_score": float(void_family_score),
        "metal_family_score": float(metal_family_score),
        "fill_family_score": float(fill_family_score),
        "entrance_family_score": float(entrance_family_score),
        "p_void": float(p_void),
        "p_metal": float(p_metal),
        "p_fill": float(p_fill),
        "p_entry": float(p_entry),
        "surface_exclusion_score": float(surface_exclusion_score),
        "shaft_score": float(shaft_score),
        "entrance_score": float(entrance_score),
        "chamber_score": float(chamber_score),
        "drain_void_score": float(drain_void_score),
        "gold_like_score": float(gold_like_score),
        "silver_like_score": float(silver_like_score),
        "dense_metal_score": float(dense_metal_score),
        "coins_score": float(coins_score),
        "ingots_score": float(ingots_score),
        "statues_score": float(statues_score),
        "pottery_treasures_score": float(pottery_treasures_score),
        "general_antiquities_score": float(general_antiquities_score),
        "dominant_direction": best_dir,
        "directionality_strength": float(directionality_strength),
        "primary_class": primary_class,
        "void_type": void_type,
        "metal_type": metal_type,
        "metal_shape": metal_shape,
        "content_type": content_type,
        "estimated_stacked_boxes": int(estimated_stacked_boxes),
        "estimated_aligned_jars": int(estimated_aligned_jars),
        "final_confidence": float(final_confidence),
    }

    summary_lines = [
        "AI HARD TYPE CLASSIFIER — CORE 9 ONLY",
        "=" * 82,
        f"Core mask source          : {active_core_name}",
        f"Core pixels               : {int(core_mask.sum())}",
        f"Near/Far/Wide ring pixels : {int(ring_near.sum())} / {int(ring_far.sum())} / {int(ring_wide.sum())}",
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
        "hard_type_json": hard_type_json,
        "hard_type_summary_lines": summary_lines,
    }


def _decision_grade(detection_confidence: float, interpretation_confidence: float) -> str:
    if detection_confidence >= 0.75 and interpretation_confidence >= 0.60:
        return "A_HIGH_CONFIDENCE_REVIEW"
    if detection_confidence >= 0.60 and interpretation_confidence >= 0.45:
        return "B_MEDIUM_CONFIDENCE_REVIEW"
    if detection_confidence >= 0.45:
        return "C_LOW_CONFIDENCE_REVIEW"
    return "D_WEAK_OR_UNRESOLVED"


def _scenario_from_hard_class(primary_class: str) -> str:
    return {
        "MIXED_VOID_METAL": "Mixed void-metal anomaly inside 17m focus",
        "STRUCTURAL_VOID": "Structural void / chamber anomaly inside 17m focus",
        "METAL_DENSE": "Dense metal anomaly inside 17m focus",
        "FILL_OR_POTTERY": "Fill or pottery anomaly inside 17m focus",
        "UNRESOLVED_ANOMALY": "Unresolved comparative anomaly inside 17m focus",
    }.get(primary_class, "Unresolved comparative anomaly inside 17m focus")


def _burial_style_from_hard_class(primary_class: str, void_type: str) -> str:
    if primary_class == "MIXED_VOID_METAL":
        return "Possible chamber or cache with mixed structural/material response"
    if primary_class == "STRUCTURAL_VOID":
        return f"Possible structural void pattern: {void_type}"
    if primary_class == "METAL_DENSE":
        return "Possible compact high-density material concentration"
    if primary_class == "FILL_OR_POTTERY":
        return "Possible fill/pottery/material concentration"
    return "No hard burial style inferred"


def build_core_ring_scene_decision_products(
    *,
    focus_mask: np.ndarray,
    analysis_bands: dict[str, np.ndarray],
    grid_spec: GridSpec,
) -> dict[str, object]:
    core_mask = focus_mask.astype(bool)
    if int(core_mask.sum()) == 0:
        raise StageError("Core-vs-ring-vs-scene decision requires a non-empty focus/core mask.")

    missing = [name for name in FOCUS_ANALYSIS_BANDS if name not in analysis_bands]
    if missing:
        raise StageError(f"Core-vs-ring-vs-scene decision is missing required bands: {', '.join(missing)}")

    pixel_size_analysis = 2.0
    pixel_size_native = 10.0
    is_super_resolved = True
    resolution_gain = max(1.0, float(pixel_size_native / pixel_size_analysis))

    # Notebook cell 121 uses an 8-connected structure with dilation iterations 2/4.
    dil2 = _hard_dilate(core_mask, 2)
    dil4 = _hard_dilate(core_mask, 4)
    ring_near = dil2 & (~core_mask)
    ring_far = dil4 & (~dil2)
    if int(ring_near.sum()) < max(8, int(core_mask.sum())):
        dil3 = _hard_dilate(core_mask, 3)
        ring_near = dil3 & (~core_mask)
    scene_mask = np.ones_like(core_mask, dtype=bool)

    def robust_stats(vals: np.ndarray) -> dict[str, float]:
        vals = np.asarray(vals, dtype=np.float64)
        vals = vals[np.isfinite(vals)]
        if len(vals) == 0:
            return {
                "mean": 0.0,
                "median": 0.0,
                "std": 0.0,
                "mad": 0.0,
                "p10": 0.0,
                "p25": 0.0,
                "p75": 0.0,
                "p90": 0.0,
                "max": 0.0,
            }
        med = np.nanmedian(vals)
        mad = np.nanmedian(np.abs(vals - med))
        return {
            "mean": float(np.nanmean(vals)),
            "median": float(med),
            "std": float(np.nanstd(vals)),
            "mad": float(mad),
            "p10": float(np.nanpercentile(vals, 10)),
            "p25": float(np.nanpercentile(vals, 25)),
            "p75": float(np.nanpercentile(vals, 75)),
            "p90": float(np.nanpercentile(vals, 90)),
            "max": float(np.nanmax(vals)),
        }

    def score_to_prob(x: float, *, bias: float = 0.0, gain: float = 1.0) -> float:
        return _hard_clip01(1.0 / (1.0 + np.exp(-(gain * (x - bias)))))

    def nanmean_mask(arr: np.ndarray, mask: np.ndarray) -> float:
        vals = arr[mask]
        vals = vals[np.isfinite(vals)]
        return float(np.mean(vals)) if len(vals) else 0.0

    band_analysis: dict[str, dict[str, object]] = {}
    for name, arr in analysis_bands.items():
        arr_for_analysis = np.asarray(arr, dtype=np.float32)
        if name == "Secret_Hidden_Doors":
            # Notebook cell 121 reads this band from the hypercube where missing scene pixels
            # are preserved as -9999-like sentinel values. The downloaded single-band export
            # materializes those pixels as NaN, so restore the sentinel for #25 parity only.
            arr_for_analysis = np.where(
                np.isfinite(arr_for_analysis),
                arr_for_analysis,
                -9999.0,
            ).astype(np.float32)

        core_vals = _hard_get_vals(arr_for_analysis, core_mask)
        near_vals = _hard_get_vals(arr_for_analysis, ring_near)
        far_vals = _hard_get_vals(arr_for_analysis, ring_far)
        scene_vals = _hard_get_vals(arr_for_analysis, scene_mask)
        band_analysis[name] = {
            "core_n": int(len(core_vals)),
            "near_n": int(len(near_vals)),
            "far_n": int(len(far_vals)),
            "scene_n": int(len(scene_vals)),
            "core_stats": robust_stats(core_vals),
            "near_stats": robust_stats(near_vals),
            "far_stats": robust_stats(far_vals),
            "scene_stats": robust_stats(scene_vals),
            "core_vs_near_es": _hard_effect_size(core_vals, near_vals),
            "core_vs_scene_es": _hard_effect_size(core_vals, scene_vals),
            "core_vs_far_es": _hard_effect_size(core_vals, far_vals),
            "core_vs_near_rc": _hard_robust_contrast(core_vals, near_vals),
            "core_vs_scene_rc": _hard_robust_contrast(core_vals, scene_vals),
            "core_vs_far_rc": _hard_robust_contrast(core_vals, far_vals),
        }

    def B(name: str, key: str) -> float:
        return float(band_analysis[name][key]) if name in band_analysis else 0.0

    gold_scene = B("Secret_Gold_Halo", "core_vs_scene_rc")
    silver_scene = B("Secret_Silver_Oxide", "core_vs_scene_rc")
    tunnel_scene = B("Secret_Tunnel_Ceiling", "core_vs_scene_rc")
    thermal_scene = B("Secret_Thermal_Inertia", "core_vs_scene_rc")
    chem_scene = B("Secret_Chemical_Protector", "core_vs_scene_rc")
    doors_scene = B("Secret_Hidden_Doors", "core_vs_scene_rc")
    zero_scene = B("REPORT_640_FINAL_Zero_Point_Targets", "core_vs_scene_rc")
    mass_scene = B("REPORT_640_Mass_Report", "core_vs_scene_rc")
    pottery_scene = B("REPORT_640_Pottery_Report", "core_vs_scene_rc")

    gold_near = B("Secret_Gold_Halo", "core_vs_near_rc")
    silver_near = B("Secret_Silver_Oxide", "core_vs_near_rc")
    tunnel_near = B("Secret_Tunnel_Ceiling", "core_vs_near_rc")
    thermal_near = B("Secret_Thermal_Inertia", "core_vs_near_rc")
    doors_near = B("Secret_Hidden_Doors", "core_vs_near_rc")
    mass_near = B("REPORT_640_Mass_Report", "core_vs_near_rc")
    pottery_near = B("REPORT_640_Pottery_Report", "core_vs_near_rc")

    mag_scene = B("AI_READY_640_Magnetic_Anomaly", "core_vs_scene_rc") if "AI_READY_640_Magnetic_Anomaly" in band_analysis else 0.0
    em_scene = B("AI_READY_640_EM_Anomaly", "core_vs_scene_rc") if "AI_READY_640_EM_Anomaly" in band_analysis else 0.0

    void_score = (
        1.30 * tunnel_scene
        + 1.10 * doors_scene
        + 0.90 * thermal_scene
        + 1.00 * tunnel_near
        + 0.80 * doors_near
        + 0.70 * thermal_near
        - 0.35 * chem_scene
        - 0.20 * zero_scene
    )
    entrance_score = 1.40 * doors_near + 1.10 * doors_scene + 0.90 * tunnel_near + 0.60 * thermal_near
    metal_score = (
        1.20 * mass_scene
        + 1.00 * mass_near
        + 1.00 * gold_scene
        + 0.90 * silver_scene
        + 0.80 * mag_scene
        + 0.70 * em_scene
        + 0.60 * gold_near
        + 0.50 * silver_near
    )
    pottery_score = 1.30 * pottery_scene + 0.90 * pottery_near + 0.50 * chem_scene + 0.40 * thermal_scene

    rr, cc = np.where(core_mask)
    r0, r1 = int(rr.min()), int(rr.max())
    c0, c1 = int(cc.min()), int(cc.max())

    arr_doors = analysis_bands["Secret_Hidden_Doors"]
    arr_tunnel = analysis_bands["Secret_Tunnel_Ceiling"]

    north = np.zeros_like(core_mask, dtype=bool)
    south = np.zeros_like(core_mask, dtype=bool)
    west = np.zeros_like(core_mask, dtype=bool)
    east = np.zeros_like(core_mask, dtype=bool)

    if r0 - 1 >= 0:
        north[max(r0 - 1, 0):r0, c0:c1 + 1] = True
    if r1 + 2 <= core_mask.shape[0]:
        south[r1 + 1:min(r1 + 2, core_mask.shape[0]), c0:c1 + 1] = True
    if c0 - 1 >= 0:
        west[r0:r1 + 1, max(c0 - 1, 0):c0] = True
    if c1 + 2 <= core_mask.shape[1]:
        east[r0:r1 + 1, c1 + 1:min(c1 + 2, core_mask.shape[1])] = True

    dir_scores = {
        "north": nanmean_mask(arr_doors + arr_tunnel, north),
        "south": nanmean_mask(arr_doors + arr_tunnel, south),
        "west": nanmean_mask(arr_doors + arr_tunnel, west),
        "east": nanmean_mask(arr_doors + arr_tunnel, east),
    }
    best_dir = max(dir_scores, key=dir_scores.get)
    dir_sorted = sorted(dir_scores.values(), reverse=True)
    directionality_strength = float((dir_sorted[0] - dir_sorted[1]) if len(dir_sorted) >= 2 else 0.0)

    p_void = score_to_prob(void_score, bias=0.8, gain=0.85)
    p_entrance = score_to_prob(entrance_score + 0.6 * directionality_strength, bias=0.7, gain=0.90)
    p_metal = score_to_prob(metal_score, bias=0.7, gain=0.85)
    p_pottery = score_to_prob(pottery_score, bias=0.7, gain=0.85)

    agreement = np.mean([
        float(p_void > 0.55),
        float(p_entrance > 0.55),
        float(p_metal > 0.55),
        float(p_pottery > 0.55),
    ])
    core_n = int(core_mask.sum())
    scene_separation = np.mean([
        abs(gold_scene),
        abs(silver_scene),
        abs(tunnel_scene),
        abs(thermal_scene),
        abs(mass_scene),
        abs(pottery_scene),
    ]) / 3.0
    scene_separation = _hard_clip01(scene_separation)
    reliability = _hard_clip01(0.45 * float(agreement) + 0.35 * scene_separation + 0.20 * min(1.0, core_n / 9.0))

    detection_confidence = _hard_clip01(0.40 * p_void + 0.25 * p_metal + 0.15 * p_pottery + 0.20 * reliability)
    interpretation_penalty = 0.82 if is_super_resolved else 1.00
    interpretation_confidence = _hard_clip01(detection_confidence * interpretation_penalty * (0.55 + 0.45 * p_entrance))
    final_confidence = _hard_clip01(0.55 * detection_confidence + 0.45 * interpretation_confidence)

    if detection_confidence >= 0.75 and interpretation_confidence >= 0.60:
        decision_grade = "قرار قوي"
    elif detection_confidence >= 0.60 and interpretation_confidence >= 0.45:
        decision_grade = "قرار متوسط داعم"
    else:
        decision_grade = "قرار أولي غير حاسم"

    if p_void >= 0.68 and p_entrance >= 0.62:
        scenario = "هدف بنيوي-فراغي مرجح مع مؤشر دخول"
    elif p_void >= 0.68 and p_metal >= 0.60:
        scenario = "فراغ مرجح مع استجابة معدنية/كثافية مرافقة"
    elif p_metal >= 0.70 and p_void < 0.55:
        scenario = "شذوذ معدني/كثافي أقوى من فرضية الفراغ"
    elif p_pottery >= 0.65:
        scenario = "مواد فخارية/ردمية مرجحة"
    elif p_void >= 0.55:
        scenario = "شذوذ فراغي متوسط"
    else:
        scenario = "لا يوجد حسم كافٍ"

    if p_entrance >= 0.68:
        if directionality_strength > 0.15:
            entrance_type = f"مدخل مرجح باتجاه {best_dir}"
        else:
            entrance_type = "فتحة/باب محتمل دون اتجاه حاسم"
    else:
        entrance_type = "لا يوجد دليل مدخل كافٍ"

    if p_metal >= 0.62:
        if gold_scene > silver_scene and gold_scene > 0.5:
            metal_type = "معدن عالي الكثافة أقرب لاستجابة ذهبية"
        elif silver_scene >= gold_scene and silver_scene > 0.5:
            metal_type = "معدن أقرب لاستجابة فضية/أكسيدية"
        elif mag_scene > 0.6:
            metal_type = "معدن/كتلة ذات سلوك مغناطيسي"
        else:
            metal_type = "كتلة معدنية غير محسومة النوع"
    else:
        metal_type = "لا يوجد دليل معدني كافٍ"

    if p_void >= 0.70 and core_n == 9:
        room_count = "يوجد نواة هدف فراغي قوية، لكن عدد الغرف غير قابل للحسم من 9 بكسلات"
    elif p_void >= 0.55:
        room_count = "فراغ محتمل، لكن عدد الغرف غير محسوم"
    else:
        room_count = "لا يوجد دليل كافٍ على الغرف"

    if p_void >= 0.60 and p_metal >= 0.60 and p_pottery >= 0.45:
        content = "محتوى محتمل مختلط: فراغ + كتلة معدنية + مواد ردم/فخار"
    elif p_void >= 0.60 and p_metal >= 0.60:
        content = "محتوى معدني محتمل داخل/قرب فراغ"
    elif p_pottery >= 0.60:
        content = "مواد فخارية/ردمية مرجحة"
    else:
        content = "المحتوى غير محسوم"

    if p_void >= 0.68 and p_entrance >= 0.62 and p_metal < 0.50:
        burial_style = "بنية فراغية/حجرية مع مدخل مرجح أكثر من كونها كتلة معدنية صلبة"
    elif p_void >= 0.68 and p_metal >= 0.60:
        burial_style = "دفن أو حيز مغلق محتمل مع محتوى كثافي"
    elif p_metal >= 0.70 and p_void < 0.55:
        burial_style = "كتلة معدنية/كثافية دون إثبات بنية دفن"
    else:
        burial_style = "نمط الهدف غير محسوم"

    resolution_note = (
        "شبكة التحليل 2م ناتجة عن Super-Resolution فوق مصدر أصلي 10م؛ لذلك ثقة الكشف أعلى من ثقة التفسير النوعي."
        if is_super_resolved
        else "شبكة التحليل مبنية على دقة أصلية مباشرة."
    )

    payload = {
        "core_pixel_count": core_n,
        "ring_near_pixel_count": int(ring_near.sum()),
        "ring_far_pixel_count": int(ring_far.sum()),
        "crs": grid_spec.crs,
        "pixel_size_analysis_m": pixel_size_analysis,
        "pixel_size_native_m": pixel_size_native,
        "is_super_resolved": is_super_resolved,
        "resolution_gain": resolution_gain,
        "void_score": float(void_score),
        "entrance_score": float(entrance_score),
        "metal_score": float(metal_score),
        "pottery_score": float(pottery_score),
        "void_probability": float(p_void),
        "entrance_probability": float(p_entrance),
        "metal_probability": float(p_metal),
        "pottery_probability": float(p_pottery),
        "reliability": float(reliability),
        "detection_confidence": float(detection_confidence),
        "interpretation_confidence": float(interpretation_confidence),
        "final_confidence": float(final_confidence),
        "decision_grade": decision_grade,
        "scenario": scenario,
        "entrance_type": entrance_type,
        "metal_type": metal_type,
        "room_count_inference": room_count,
        "content_inference": content,
        "burial_style_inference": burial_style,
        "dominant_direction": best_dir,
        "directionality_strength": float(directionality_strength),
        "resolution_note": resolution_note,
        "band_analysis": band_analysis,
    }

    record = {
        "Core_Pixels": core_n,
        "Near_Ring_Pixels": int(ring_near.sum()),
        "Far_Ring_Pixels": int(ring_far.sum()),
        "Analysis_Pixel_m": pixel_size_analysis,
        "Native_Pixel_m": pixel_size_native,
        "Is_Super_Resolved": is_super_resolved,
        "Scenario": scenario,
        "Burial_Style_Inference": burial_style,
        "Void_Probability": round(p_void, 4),
        "Entrance_Probability": round(p_entrance, 4),
        "Metal_Probability": round(p_metal, 4),
        "Pottery_Probability": round(p_pottery, 4),
        "Reliability": round(reliability, 4),
        "Detection_Confidence": round(detection_confidence, 4),
        "Interpretation_Confidence": round(interpretation_confidence, 4),
        "Final_Confidence": round(final_confidence, 4),
        "Decision_Grade": decision_grade,
        "Entrance_Type": entrance_type,
        "Metal_Type": metal_type,
        "Room_Count_Inference": room_count,
        "Content_Inference": content,
        "Dominant_Direction": best_dir,
        "Directionality_Strength": round(directionality_strength, 4),
        "Resolution_Note": resolution_note,
    }

    summary_lines = [
        "AI CORE-vs-RING-vs-SCENE DECISION",
        "=" * 78,
        f"Core target pixels         : {core_n}",
        f"Near ring pixels           : {int(ring_near.sum())}",
        f"Far ring pixels            : {int(ring_far.sum())}",
        f"Analysis pixel size        : {pixel_size_analysis} m",
        f"Native support pixel size  : {pixel_size_native} m",
        f"Super-resolved             : {is_super_resolved}",
        "-" * 78,
        f"Scenario                   : {scenario}",
        f"Burial style inference     : {burial_style}",
        f"Void probability           : {p_void:.2%}",
        f"Entrance probability       : {p_entrance:.2%}",
        f"Metal probability          : {p_metal:.2%}",
        f"Pottery probability        : {p_pottery:.2%}",
        f"Reliability                : {reliability:.2%}",
        f"Detection confidence       : {detection_confidence:.2%}",
        f"Interpretation confidence  : {interpretation_confidence:.2%}",
        f"Final confidence           : {final_confidence:.2%}",
        f"Decision grade             : {decision_grade}",
        "-" * 78,
        f"Entrance type              : {entrance_type}",
        f"Metal type                 : {metal_type}",
        f"Room count inference       : {room_count}",
        f"Content inference          : {content}",
        f"Dominant direction         : {best_dir}",
        f"Directionality strength    : {directionality_strength:.4f}",
        "-" * 78,
        f"Resolution note            : {resolution_note}",
    ]

    return {
        "core_ring_scene_record": record,
        "core_ring_scene_json": payload,
        "core_ring_scene_summary_lines": summary_lines,
    }

def build_detected_features_wgs84_geojson_products(
    *,
    target_records: list[dict[str, object]],
    hard_type_record: dict[str, object],
    core_ring_scene_record: dict[str, object],
    grid_spec: GridSpec,
) -> dict[str, object]:
    try:
        from pyproj import Transformer
    except Exception as exc:  # pragma: no cover - dependency should be present through rasterio/pyproj stack
        raise StageError("WGS84 detected-feature GeoJSON export requires pyproj.") from exc

    transformer = Transformer.from_crs(grid_spec.crs, "EPSG:4326", always_xy=True)

    features: list[dict[str, object]] = []
    for row in target_records:
        utm_e = float(row["UTM_E"])
        utm_n = float(row["UTM_N"])
        fallback_lon, fallback_lat = transformer.transform(utm_e, utm_n)
        lon = float(row.get("Lon", fallback_lon))
        lat = float(row.get("Lat", fallback_lat))
        google_maps_link = str(
            row.get("Google_Maps_Link")
            or f"https://www.google.com/maps?q={float(lat):.8f},{float(lon):.8f}"
        )

        target_label = str(row.get("الهدف_المرجح", row.get("Classification", "")))
        target_confidence = row.get("الثقة_النهائية_%", row.get("Confidence", ""))

        props = {
            "Target_ID": int(row["Target_ID"]),
            "Source_Cell": "cell_123",
            "Source_Notebook_Family": "AI_FOCUS_17M_TARGETS_WGS84_V7_2",
            "App_Output_Contract": "app_enhanced_local_v1",
            "Notebook_Semantic_Source": "cell_123_AI_FOCUS_17M_TARGETS_V7_2",
            "Production_Redaction_Required": True,
            "row": int(row["row"]),
            "col": int(row["col"]),
            "UTM_E": round(utm_e, 3),
            "UTM_N": round(utm_n, 3),
            "Lon": round(float(lon), 8),
            "Lat": round(float(lat), 8),
            "Google_Maps_Link": google_maps_link,
            "Classification": target_label,
            "Confidence": str(target_confidence),
            "ROI_Composite_Score": float(row.get("ROI_Composite_Score", row.get("درجة_مركبة", 0.0))),
            "الهدف_المرجح": str(row.get("الهدف_المرجح", "")),
            "المحتوى_المرجح": str(row.get("المحتوى_المرجح", "")),
            "نظام_الدفن_او_الحقبة_المرجحة": str(row.get("نظام_الدفن_او_الحقبة_المرجحة", "")),
            "تحذير_الفخاخ": str(row.get("تحذير_الفخاخ", "")),
            "ثقة_الشكل_%": row.get("ثقة_الشكل_%", ""),
            "ثقة_المحتوى_%": row.get("ثقة_المحتوى_%", ""),
            "ثقة_الحقبة_%": row.get("ثقة_الحقبة_%", ""),
            "الثقة_النهائية_%": row.get("الثقة_النهائية_%", ""),
            "تفسير_الذكاء": str(row.get("تفسير_الذكاء", "")),
            "Hard_Primary_Class": str(hard_type_record.get("Primary_Class", "")),
            "Hard_Void_Type": str(hard_type_record.get("Void_Type", "")),
            "Hard_Metal_Type": str(hard_type_record.get("Metal_Type", "")),
            "Hard_Content_Type": str(hard_type_record.get("Content_Type", "")),
            "Decision_Grade": str(core_ring_scene_record.get("Decision_Grade", "")),
            "Scenario": str(core_ring_scene_record.get("Scenario", "")),
            "Final_Confidence": float(core_ring_scene_record.get("Final_Confidence", 0.0)),
        }

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lon), float(lat)],
                },
                "properties": props,
            }
        )

    return {
        "detected_features_wgs84_geojson": {
            "type": "FeatureCollection",
            "name": "AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2",
            "source_cell": "cell_123",
            "source_notebook_family": "AI_FOCUS_17M_TARGETS_WGS84_V7_2",
            "app_output_contract": "app_enhanced_local_v1",
            "notebook_semantic_source": "cell_123_AI_FOCUS_17M_TARGETS_V7_2",
            "parity_status": "app_enhanced_local_contract_not_exact_file_parity",
            "production_redaction_required": True,
            "coordinate_reference_system": "EPSG:4326",
            "privacy": "FILESYSTEM_ONLY",
            "features": features,
        }
    }



def _write_rgba_png(path: Path, rgba: np.ndarray) -> None:
    import struct
    import zlib

    arr = rgba.astype(np.uint8, copy=False)
    if arr.ndim != 3 or arr.shape[2] != 4:
        raise StageError("KMZ PNG writer requires an RGBA array.")

    height, width, _channels = arr.shape

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    raw = b"".join(b"\\x00" + arr[row].tobytes() for row in range(height))
    png = (
        b"\\x89PNG\\r\\n\\x1a\\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, level=6))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def _kmz_norm(arr: np.ndarray) -> np.ndarray:
    values = np.asarray(arr, dtype=np.float32)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    mn = float(np.min(values))
    mx = float(np.max(values))
    if not np.isfinite(mn) or not np.isfinite(mx) or abs(mx - mn) < 1e-9:
        return np.zeros_like(values, dtype=np.float32)
    return np.clip((values - mn) / (mx - mn + 1e-9), 0.0, 1.0).astype(np.float32)


def _kmz_safe_float(value: object, default: float = 3.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if not np.isfinite(out):
        return default
    return out


def _kmz_xml_text(value: object) -> str:
    from html import escape
    return escape(str(value), quote=True)


def _kmz_wgs84_bounds(transform: object, crs: str, height: int, width: int) -> tuple[float, float, float, float]:
    try:
        from pyproj import Transformer
    except Exception as exc:  # pragma: no cover
        raise StageError("KMZ export requires pyproj.") from exc

    affine = transform if isinstance(transform, Affine) else Affine(*transform)

    left = float(affine.c)
    top = float(affine.f)
    right = float(affine.c + width * affine.a + height * affine.b)
    bottom = float(affine.f + width * affine.d + height * affine.e)

    transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    west_1, south_1 = transformer.transform(left, bottom)
    east_1, north_1 = transformer.transform(right, top)

    return (
        min(float(west_1), float(east_1)),
        min(float(south_1), float(north_1)),
        max(float(west_1), float(east_1)),
        max(float(south_1), float(north_1)),
    )


def _kmz_google_maps_link(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}"


def build_kmz_visualization_products(
    *,
    analysis_bands: dict[str, np.ndarray],
    target_records: list[dict[str, object]],
    core_ring_scene_record: dict[str, object],
    hard_type_record: dict[str, object],
    grid_spec: GridSpec,
) -> dict[str, object]:
    try:
        from pyproj import Transformer
    except Exception as exc:  # pragma: no cover
        raise StageError("KMZ export requires pyproj.") from exc

    required = [
        "Secret_Gold_Halo",
        "Secret_Tunnel_Ceiling",
        "REPORT_640_Mass_Report",
        "Secret_Hidden_Doors",
    ]
    missing = [name for name in required if name not in analysis_bands]
    if missing:
        raise StageError(f"Missing KMZ heatmap source bands: {missing}")

    metal = _kmz_norm(analysis_bands["Secret_Gold_Halo"])
    void = _kmz_norm(analysis_bands["Secret_Tunnel_Ceiling"])
    rock = _kmz_norm(analysis_bands["REPORT_640_Mass_Report"])
    doors = _kmz_norm(analysis_bands["Secret_Hidden_Doors"])

    if metal.shape != void.shape or metal.shape != rock.shape or metal.shape != doors.shape:
        raise StageError("KMZ heatmap source bands must share one shape.")

    height, width = metal.shape

    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    rgba[:, :, 0] = (metal * 255).astype(np.uint8)
    rgba[:, :, 3] = (metal * 255).astype(np.uint8)

    mask_black = doors > 0.5
    rgba[mask_black] = [0, 0, 0, 255]

    mask_blue = (void > 0.5) & (~mask_black)
    rgba[mask_blue] = [0, 0, 255, 255]

    mask_yellow = (rock > 0.5) & (~mask_black) & (~mask_blue)
    rgba[mask_yellow] = [255, 255, 0, 255]

    mask_green = rgba[:, :, 3] == 0
    rgba[mask_green] = [0, 255, 0, 255]

    west, south, east, north = _kmz_wgs84_bounds(grid_spec.transform, grid_spec.crs, height, width)

    heatmap_kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>AI Heatmap Classification</name>
    <description>source_cell=cell_155; privacy=FILESYSTEM_ONLY</description>
    <GroundOverlay>
      <name>AI Heatmap Classification</name>
      <Icon><href>heat.png</href></Icon>
      <LatLonBox>
        <north>{north:.10f}</north>
        <south>{south:.10f}</south>
        <east>{east:.10f}</east>
        <west>{west:.10f}</west>
      </LatLonBox>
    </GroundOverlay>
  </Document>
</kml>
'''

    transformer = Transformer.from_crs(grid_spec.crs, "EPSG:4326", always_xy=True)

    placemarks: list[str] = []
    for row in target_records:
        utm_e = _kmz_safe_float(row.get("UTM_E"), default=np.nan)
        utm_n = _kmz_safe_float(row.get("UTM_N"), default=np.nan)
        if not np.isfinite(utm_e) or not np.isfinite(utm_n):
            continue

        lon, lat = transformer.transform(utm_e, utm_n)
        lon = float(lon)
        lat = float(lat)

        target_id = int(row.get("Target_ID", len(placemarks) + 1))
        classification = str(row.get("Classification", "Target"))
        confidence = str(row.get("Confidence", ""))
        scenario = str(core_ring_scene_record.get("Scenario", ""))
        decision_grade = str(core_ring_scene_record.get("Decision_Grade", ""))
        primary_class = str(hard_type_record.get("Primary_Class", ""))
        content_type = str(hard_type_record.get("Content_Type", ""))
        depth = 3.0
        gmaps = _kmz_google_maps_link(lat, lon)

        placemarks.append(
            f'''
    <Placemark>
      <name>{target_id} - {_kmz_xml_text(classification)}</name>
      <description><![CDATA[
      <b>Target ID:</b> {target_id}<br/>
      <b>Classification:</b> {_kmz_xml_text(classification)}<br/>
      <b>Confidence:</b> {_kmz_xml_text(confidence)}<br/>
      <b>Scenario:</b> {_kmz_xml_text(scenario)}<br/>
      <b>Decision Grade:</b> {_kmz_xml_text(decision_grade)}<br/>
      <b>Primary Class:</b> {_kmz_xml_text(primary_class)}<br/>
      <b>Content:</b> {_kmz_xml_text(content_type)}<br/>
      <b>Depth:</b> {depth:.2f} m<br/>
      <b>UTM_E:</b> {utm_e:.3f}<br/>
      <b>UTM_N:</b> {utm_n:.3f}<br/>
      <b>Google Maps:</b> <a href="{gmaps}">{gmaps}</a><br/>
      <b>Source Cell:</b> cell_155<br/>
      ]]></description>
      <Point>
        <extrude>1</extrude>
        <altitudeMode>relativeToGround</altitudeMode>
        <coordinates>{lon:.8f},{lat:.8f},{-abs(depth):.2f}</coordinates>
      </Point>
    </Placemark>'''
        )

    targets_kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>AI 3D Target Visualization</name>
    <description>source_cell=cell_155; privacy=FILESYSTEM_ONLY</description>
    {''.join(placemarks)}
  </Document>
</kml>
'''

    return {
        "heatmap_classification_rgba": rgba,
        "heatmap_classification_kml": heatmap_kml,
        "target_3d_visualization_kml": targets_kml,
        "target_3d_visualization_count": len(placemarks),
        "heatmap_bounds_wgs84": {"west": west, "south": south, "east": east, "north": north},
    }

def build_field_operations_products(
    *,
    target_records: list[dict[str, object]],
    hard_type_record: dict[str, object],
    core_ring_scene_record: dict[str, object],
    grid_spec: GridSpec,
) -> dict[str, object]:
    try:
        from pyproj import Transformer
    except Exception as exc:
        raise StageError("Field-operation KMZ export requires pyproj.") from exc

    transformer = Transformer.from_crs(grid_spec.crs, "EPSG:4326", always_xy=True)

    features: list[dict[str, object]] = []
    placemarks: list[str] = []

    primary_class = str(hard_type_record.get("Primary_Class", "UNRESOLVED_ANOMALY"))
    content_type = str(hard_type_record.get("Content_Type", "CONTENT_UNRESOLVED"))
    decision_grade = str(core_ring_scene_record.get("Decision_Grade", ""))
    scenario = str(core_ring_scene_record.get("Scenario", ""))
    final_confidence = _kmz_safe_float(core_ring_scene_record.get("Final_Confidence"), default=0.0)

    for row in target_records:
        utm_e = _kmz_safe_float(row.get("UTM_E"), default=np.nan)
        utm_n = _kmz_safe_float(row.get("UTM_N"), default=np.nan)
        if not np.isfinite(utm_e) or not np.isfinite(utm_n):
            continue

        lon, lat = transformer.transform(utm_e, utm_n)
        lon = float(lon)
        lat = float(lat)

        target_id = int(row.get("Target_ID", len(features) + 1))
        target_class = str(row.get("Classification", "General Anomaly"))
        confidence = str(row.get("Confidence", "N/A"))
        field_notes = (
            f"Decision: {decision_grade} | "
            f"Scenario: {scenario} | "
            f"Primary: {primary_class} | "
            f"Content: {content_type}"
        )

        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "ID": target_id,
                "Source_Cell": "cell_200",
                "Classification": target_class,
                "Material_Content": content_type,
                "Field_Notes": field_notes,
                "Confidence": confidence,
                "Decision_Grade": decision_grade,
                "Scenario": scenario,
                "Final_Confidence": round(final_confidence, 4),
                "UTM_E": round(utm_e, 3),
                "UTM_N": round(utm_n, 3),
                "UTM": f"{utm_e:.3f}, {utm_n:.3f}",
            },
        })

        placemarks.append("\\n".join([
            "        <Placemark>",
            f"            <name>Target {target_id}: {_kmz_xml_text(target_class)}</name>",
            "            <description><![CDATA[",
            "                <div style='font-family:Arial; font-size:14px; color:#333;'>",
            "                    <h3 style='color:#D4AF37;'>Strategic Intelligence Data</h3>",
            "                    <table border='1' style='border-collapse:collapse; width:100%; text-align:left;'>",
            "                        <tr style='background-color:#f2f2f2;'><th>Parameter</th><th>Value</th></tr>",
            f"                        <tr><td><b>Object Type</b></td><td>{_kmz_xml_text(target_class)}</td></tr>",
            f"                        <tr><td><b>Subtype/Content</b></td><td>{_kmz_xml_text(content_type)}</td></tr>",
            f"                        <tr><td><b>Confidence</b></td><td>{_kmz_xml_text(confidence)}</td></tr>",
            f"                        <tr><td><b>Decision Grade</b></td><td>{_kmz_xml_text(decision_grade)}</td></tr>",
            f"                        <tr><td><b>Scenario</b></td><td>{_kmz_xml_text(scenario)}</td></tr>",
            f"                        <tr><td><b>Coordinates (UTM)</b></td><td>{utm_e:.3f},{utm_n:.3f}</td></tr>",
            "                        <tr><td><b>Source Cell</b></td><td>cell_200</td></tr>",
            "                    </table>",
            "                    <p style='margin-top:10px;'><i>Local/private field-operation export.</i></p>",
            "                </div>",
            "            ]]></description>",
            "            <Point>",
            f"                <coordinates>{lon:.8f},{lat:.8f},0</coordinates>",
            "            </Point>",
            "        </Placemark>",
        ]))

    geojson = {
        "type": "FeatureCollection",
        "name": "FINAL_ARCHEO_INTELLIGENCE_MAP",
        "source_cell": "cell_200",
        "source_notebook_family": "TESLA_V7_2_FIELD_OPERATIONS",
        "coordinate_reference_system": "EPSG:4326",
        "privacy": "FILESYSTEM_ONLY",
        "features": features,
    }

    kml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        "<Document>",
        "    <name>Tesla v7.2 Mission: Advanced Intelligence Assets</name>",
        "    <description>source_cell=cell_200; privacy=FILESYSTEM_ONLY</description>",
        *placemarks,
        "</Document>",
        "</kml>",
    ]

    return {
        "field_operations_geojson": geojson,
        "field_operations_kml": "\\n".join(kml_lines),
        "field_operations_feature_count": len(features),
    }




def build_live_overlay_manifest_products(
    *,
    target_records: list[dict[str, object]],
    field_operations_feature_count: int,
) -> dict[str, object]:
    layers = [
        {
            "id": "hybrid_basemap",
            "type": "basemap",
            "title": "HYBRID",
            "source_cell": "cell_243",
            "status": "app_native_replacement",
            "notebook_equivalent": "Map.add_basemap('HYBRID')",
        },
        {
            "id": "cnn_digital_matrix",
            "type": "raster_probability_overlay",
            "title": "CNN Digital Matrix",
            "source_cell": "cell_243",
            "status": "pending_dependency",
            "blocked_by": ["Plan B item #32 CNN final target inference", "Plan B item #39 probability map overlay"],
            "visualization": {"min": 0.1, "max": 0.9, "palette": ["black", "yellow", "red"]},
            "note": "Notebook used probabilities[1]. App probability raster is pending later ML work.",
        },
        {
            "id": "detected_target_markers",
            "type": "vector_markers",
            "title": "Detected target markers",
            "source_cell": "cell_243",
            "status": "available_private_filesystem",
            "feature_count": len(target_records),
            "private_source_artifact": DETECTED_FEATURES_WGS84_GEOJSON_NAME,
        },
        {
            "id": "detected_target_area_buffers",
            "type": "vector_buffers",
            "title": "Detected target area buffers",
            "source_cell": "cell_243",
            "status": "available_private_filesystem",
            "feature_count": len(target_records),
            "private_source_artifact": FIELD_OPERATIONS_GEOJSON_NAME,
        },
        {
            "id": "field_operations_targets",
            "type": "field_operation_points",
            "title": "Field operations targets",
            "source_cell": "cell_200",
            "status": "available_private_filesystem",
            "feature_count": field_operations_feature_count,
            "private_source_artifact": FIELD_OPERATIONS_GEOJSON_NAME,
        },
        {
            "id": "subterranean_corridor_candidates",
            "type": "vector_linestring_candidates",
            "title": "Subterranean Corridor",
            "source_cell": "cell_243",
            "status": "pending_dependency",
            "blocked_by": ["Plan B item #32 final target tags", "Plan B item #40 GPS/path tracing from targets"],
            "feature_count": 0,
        },
        {
            "id": "heatmap_ground_overlay",
            "type": "image_overlay",
            "title": "AI Heatmap Classification",
            "source_cell": "cell_155",
            "status": "available_private_filesystem",
            "private_source_artifact": HEATMAP_CLASSIFICATION_PNG_NAME,
        },
    ]

    manifest = {
        "type": "AppNativeLiveOverlayManifest",
        "source_cell": "cell_243",
        "source_notebook_family": "LIVE_GEEMAP_OVERLAY_REPLACEMENT",
        "status": "implemented_as_app_native_manifest",
        "privacy": "FILESYSTEM_ONLY",
        "http_servable": False,
        "downloadable_via_api": False,
        "basemap": "HYBRID",
        "target_count": len(target_records),
        "layer_count": len(layers),
        "exact_coordinates_in_manifest": False,
        "raw_geometry_in_manifest": False,
        "implementation_note": "Replaces geemap.Map live display with an app-native private layer manifest.",
        "layers": layers,
    }
    return {
        "live_overlay_manifest": manifest,
        "live_overlay_manifest_layer_count": len(layers),
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
    core_ring_scene_record = products["core_ring_scene_record"]
    core_ring_scene_json = products["core_ring_scene_json"]
    core_ring_scene_summary_lines = products["core_ring_scene_summary_lines"]
    detected_features_wgs84_geojson = products["detected_features_wgs84_geojson"]
    heatmap_classification_rgba = products["heatmap_classification_rgba"]
    heatmap_classification_kml = products["heatmap_classification_kml"]
    target_3d_visualization_kml = products["target_3d_visualization_kml"]
    field_operations_geojson = products["field_operations_geojson"]
    field_operations_kml = products["field_operations_kml"]
    live_overlay_manifest = products["live_overlay_manifest"]
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
    assert isinstance(core_ring_scene_record, dict)
    assert isinstance(core_ring_scene_json, dict)
    assert isinstance(core_ring_scene_summary_lines, list)
    assert isinstance(detected_features_wgs84_geojson, dict)
    assert isinstance(heatmap_classification_rgba, np.ndarray)
    assert isinstance(heatmap_classification_kml, str)
    assert isinstance(target_3d_visualization_kml, str)
    assert isinstance(field_operations_geojson, dict)
    assert isinstance(field_operations_kml, str)
    assert isinstance(live_overlay_manifest, dict)

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
    core_ring_scene_csv_path = focus_dir / CORE_RING_SCENE_TARGETS_CSV_NAME
    core_ring_scene_txt_path = focus_dir / CORE_RING_SCENE_DECISION_TXT_NAME
    core_ring_scene_json_path = focus_dir / CORE_RING_SCENE_DECISION_JSON_NAME
    detected_features_wgs84_geojson_path = focus_dir / DETECTED_FEATURES_WGS84_GEOJSON_NAME
    heatmap_classification_png_path = focus_dir / HEATMAP_CLASSIFICATION_PNG_NAME
    heatmap_classification_kmz_path = focus_dir / HEATMAP_CLASSIFICATION_KMZ_NAME
    target_3d_visualization_kmz_path = focus_dir / TARGET_3D_VISUALIZATION_KMZ_NAME
    field_operations_geojson_path = focus_dir / FIELD_OPERATIONS_GEOJSON_NAME
    field_operations_kmz_path = focus_dir / FIELD_OPERATIONS_KMZ_NAME
    live_overlay_manifest_path = focus_dir / LIVE_OVERLAY_MANIFEST_NAME

    _write_focus_mask_tif(mask_tif_path, mask, grid_spec)
    np.save(mask_npy_path, mask.astype(np.float32))
    np.save(focus_window_path, masked_window.astype(np.float32))
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    _write_csv(band_summary_path, ["band_index", "band_name", "focus_mean", "focus_min", "focus_max"], band_summary_rows)

    pixel_fields = [
        "row",
        "col",
        "X_native",
        "Y_native",
        "UTM_E",
        "UTM_N",
        "Lon",
        "Lat",
        "Google_Maps_Link",
        *FOCUS_ANALYSIS_BANDS,
        "z_Gold",
        "z_Silver",
        "z_Tunnel",
        "z_Thermal",
        "z_Chemical",
        "z_Doors",
        "z_Zero",
        "z_Mass",
        "z_Pottery",
        "محور_معدني",
        "محور_فراغ",
        "محور_بنيوي",
        "درجة_مركبة",
    ]
    target_fields = [
        "Target_ID",
        "الهدف_المرجح",
        "المحتوى_المرجح",
        "نظام_الدفن_او_الحقبة_المرجحة",
        "تحذير_الفخاخ",
        "ثقة_الشكل_%",
        "ثقة_المحتوى_%",
        "ثقة_الحقبة_%",
        "الثقة_النهائية_%",
        "تفسير_الذكاء",
        "X_native",
        "Y_native",
        "UTM_E",
        "UTM_N",
        "Lon",
        "Lat",
        "Google_Maps_Link",
        "row",
        "col",
        "محور_معدني",
        "محور_فراغ",
        "محور_بنيوي",
        "درجة_مركبة",
        *FOCUS_ANALYSIS_BANDS,
    ]
    _write_csv(pixel_report_path, pixel_fields, pixel_records)
    _write_csv(target_report_path, target_fields, target_records)
    target_geojson_path.write_text(json.dumps(target_geojson, indent=2, sort_keys=True), encoding="utf-8")
    _write_csv(hard_type_csv_path, list(hard_type_record.keys()), [hard_type_record])
    hard_type_txt_path.write_text("\n".join(str(line) for line in hard_type_summary_lines), encoding="utf-8")
    hard_type_json_path.write_text(json.dumps(hard_type_json, indent=2, sort_keys=True), encoding="utf-8")
    _write_csv(core_ring_scene_csv_path, list(core_ring_scene_record.keys()), [core_ring_scene_record])
    core_ring_scene_txt_path.write_text("\n".join(str(line) for line in core_ring_scene_summary_lines), encoding="utf-8")
    core_ring_scene_json_path.write_text(json.dumps(core_ring_scene_json, indent=2, sort_keys=True), encoding="utf-8")
    detected_features_wgs84_geojson_path.write_text(
        json.dumps(detected_features_wgs84_geojson, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )

    import zipfile

    _write_rgba_png(heatmap_classification_png_path, heatmap_classification_rgba)

    with zipfile.ZipFile(heatmap_classification_kmz_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", heatmap_classification_kml)
        zf.write(heatmap_classification_png_path, "heat.png")

    with zipfile.ZipFile(target_3d_visualization_kmz_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", target_3d_visualization_kml)

    field_operations_geojson_path.write_text(
        json.dumps(field_operations_geojson, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    with zipfile.ZipFile(field_operations_kmz_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", field_operations_kml)

    live_overlay_manifest_path.write_text(
        json.dumps(live_overlay_manifest, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )

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
        "core_ring_scene_targets_csv": core_ring_scene_csv_path,
        "core_ring_scene_decision_txt": core_ring_scene_txt_path,
        "core_ring_scene_decision_json": core_ring_scene_json_path,
        "detected_features_wgs84_geojson": detected_features_wgs84_geojson_path,
        "heatmap_classification_png": heatmap_classification_png_path,
        "heatmap_classification_kmz": heatmap_classification_kmz_path,
        "target_3d_visualization_kmz": target_3d_visualization_kmz_path,
        "field_operations_geojson": field_operations_geojson_path,
        "field_operations_kmz": field_operations_kmz_path,
        "live_overlay_manifest": live_overlay_manifest_path,
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
        products.update(
            build_core_ring_scene_decision_products(
                focus_mask=products["mask"],
                analysis_bands=analysis_bands,
                grid_spec=self.grid_spec,
            )
        )
        products.update(
            build_detected_features_wgs84_geojson_products(
                target_records=products["target_records"],
                hard_type_record=products["hard_type_record"],
                core_ring_scene_record=products["core_ring_scene_record"],
                grid_spec=self.grid_spec,
            )
        )
        products.update(
            build_kmz_visualization_products(
                analysis_bands=analysis_bands,
                target_records=products["target_records"],
                core_ring_scene_record=products["core_ring_scene_record"],
                hard_type_record=products["hard_type_record"],
                grid_spec=self.grid_spec,
            )
        )
        products.update(
            build_field_operations_products(
                target_records=products["target_records"],
                hard_type_record=products["hard_type_record"],
                core_ring_scene_record=products["core_ring_scene_record"],
                grid_spec=self.grid_spec,
            )
        )
        products.update(
            build_live_overlay_manifest_products(
                target_records=products["target_records"],
                field_operations_feature_count=products["field_operations_feature_count"],
            )
        )
        outputs = write_focus_mask_outputs(context.run_dir, self.grid_spec, products)
        metal_fingerprint_outputs = write_plan_b33_metal_fingerprint_diagnostic_outputs(context.run_dir, context.run_id)
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
            build_stage_artifact(
                name="core_ring_scene_targets_v7_2c_csv",
                relative_path=outputs["core_ring_scene_targets_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["core_ring_scene_targets_csv"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="core_ring_scene_decision_v7_2c_txt",
                relative_path=outputs["core_ring_scene_decision_txt"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["core_ring_scene_decision_txt"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="core_ring_scene_decision_v7_2c_json",
                relative_path=outputs["core_ring_scene_decision_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["core_ring_scene_decision_json"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="detected_features_wgs84_geojson_v7_2",
                relative_path=outputs["detected_features_wgs84_geojson"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["detected_features_wgs84_geojson"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="ai_heatmap_classification_png",
                relative_path=outputs["heatmap_classification_png"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["heatmap_classification_png"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="ai_heatmap_classification_kmz",
                relative_path=outputs["heatmap_classification_kmz"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["heatmap_classification_kmz"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="ai_3d_target_visualization_kmz",
                relative_path=outputs["target_3d_visualization_kmz"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["target_3d_visualization_kmz"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="final_archeo_intelligence_map_geojson",
                relative_path=outputs["field_operations_geojson"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["field_operations_geojson"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="tesla_v7_2_field_operations_kmz",
                relative_path=outputs["field_operations_kmz"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["field_operations_kmz"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="app_native_live_overlay_manifest_v7_2",
                relative_path=outputs["live_overlay_manifest"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["live_overlay_manifest"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="metal_fingerprint_diagnostic_csv",
                relative_path=metal_fingerprint_outputs["csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=metal_fingerprint_outputs["csv"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="metal_fingerprint_diagnostic_json",
                relative_path=metal_fingerprint_outputs["json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=metal_fingerprint_outputs["json"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="metal_fingerprint_diagnostic_txt",
                relative_path=metal_fingerprint_outputs["txt"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=metal_fingerprint_outputs["txt"].stat().st_size,
                http_servable=False,
            ),
        ]
        summary = products["summary"]
        assert isinstance(summary, dict)
        target_records = products["target_records"]
        hard_type_record = products["hard_type_record"]
        core_ring_scene_record = products["core_ring_scene_record"]
        target_3d_visualization_count = products["target_3d_visualization_count"]
        field_operations_feature_count = products["field_operations_feature_count"]
        live_overlay_manifest_layer_count = products["live_overlay_manifest_layer_count"]
        assert isinstance(target_records, list)
        assert isinstance(hard_type_record, dict)
        assert isinstance(core_ring_scene_record, dict)
        assert isinstance(target_3d_visualization_count, int)
        assert isinstance(field_operations_feature_count, int)
        assert isinstance(live_overlay_manifest_layer_count, int)
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
                "core_ring_scene_targets_csv": CORE_RING_SCENE_TARGETS_CSV_NAME,
                "core_ring_scene_decision_txt": CORE_RING_SCENE_DECISION_TXT_NAME,
                "core_ring_scene_decision_json": CORE_RING_SCENE_DECISION_JSON_NAME,
                "core_ring_scene_source_cell": "cell_121",
                "core_ring_scene_decision_grade": core_ring_scene_record["Decision_Grade"],
                "detected_features_wgs84_geojson": DETECTED_FEATURES_WGS84_GEOJSON_NAME,
                "detected_features_wgs84_source_cell": "cell_123",
                "detected_features_wgs84_feature_count": len(target_records),
                "heatmap_classification_png": HEATMAP_CLASSIFICATION_PNG_NAME,
                "heatmap_classification_kmz": HEATMAP_CLASSIFICATION_KMZ_NAME,
                "target_3d_visualization_kmz": TARGET_3D_VISUALIZATION_KMZ_NAME,
                "kmz_visualization_source_cell": "cell_155",
                "target_3d_visualization_count": target_3d_visualization_count,
                "field_operations_geojson": FIELD_OPERATIONS_GEOJSON_NAME,
                "field_operations_kmz": FIELD_OPERATIONS_KMZ_NAME,
                "field_operations_source_cell": "cell_200",
                "field_operations_feature_count": field_operations_feature_count,
                "live_overlay_manifest": LIVE_OVERLAY_MANIFEST_NAME,
                "live_overlay_manifest_source_cell": "cell_243",
                "live_overlay_manifest_layer_count": live_overlay_manifest_layer_count,
            },
        )
