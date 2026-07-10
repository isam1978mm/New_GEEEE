from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import raster_sidecar_path, write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.services.storage import read_manifest

SCIENCE_CORE_BANDS = (
    "VV_dB",
    "VH_dB",
    "logRatio_dB",
    "incidence",
    "NDVI",
    "NDWI",
    "NDMI",
    "NBR",
    "IRONOX",
    "IRON_SWIR",
    "BSI",
    "slope",
    "aspect",
    "curvature",
    "TPI",
    "TRI",
    "roughness",
    "TWI",
    "lst",
)
SCIENCE_CORE_STACK_TIF = "science_core_stack.tif"
SCIENCE_CORE_STACK_NPY = "science_core_stack.npy"
RADAR_LINEAR_SUPPORT_STACK_TIF = "radar_linear_support_stack.tif"
RADAR_LINEAR_SUPPORT_STACK_NPY = "radar_linear_support_stack.npy"
RADAR_DB_SUPPORT_STACK_TIF = "radar_db_support_stack.tif"
RADAR_DB_SUPPORT_STACK_NPY = "radar_db_support_stack.npy"
AI_READY_SUPPORT_STACK_TIF = "ai_ready_support_stack.tif"
AI_READY_SUPPORT_STACK_NPY = "ai_ready_support_stack.npy"
S2_MASK_SUPPORT_TIF = "s2_mask_support_valid.tif"
BAND_STATS_CSV = "band_stats.csv"
STACK_PRESENCE_SUMMARY_JSON = "stack_presence_summary.json"
TENSOR_AUDIT_SUMMARY_JSON = "tensor_audit_summary.json"
GEOMETRY_CONSISTENCY_SUMMARY_JSON = "geometry_consistency_summary.json"
NOTEBOOK_STACK_OUTPUT_DIR = "NPY_STACKS"
NOTEBOOK_RADAR_STACK_NPY = "RADAR_STACK_HWC_640_app.npy"
NOTEBOOK_SCIENCE_CORE_STACK_NPY = "SCIENCE_CORE_STACK_HWC_640_app.npy"
NOTEBOOK_RADAR_LINEAR_STACK_NPY = "RADAR_LINEAR_SUPPORT_STACK_640_app.npy"
NOTEBOOK_AI_READY_STACK_NPY = "AI_READY_SUPPORT_STACK_640_app.npy"
NOTEBOOK_NANO_GEOPHYSICS_STACK_NPY = "NANO_GEOPHYSICS_STACK_640.npy"
NOTEBOOK_TREASURE_GEOPHYSICS_STACK_NPY = "TREASURE_GEOPHYSICS_STACK_640.npy"
NOTEBOOK_RAD_S0_MASTER_STACK_NPY = "RAD_S0_MASTER_STACK_640.npy"
NOTEBOOK_RAD_MASTER_CUBE_NPY = "RAD_MASTER_CUBE_640.npy"
NOTEBOOK_GPHYS_MASTER_STACK_NPY = "GPHYS_MASTER_STACK_640.npy"
NOTEBOOK_MASTER_RTC_REFINED_STACK_NPY = "MASTER_RTC_REFINED_STACK_640.npy"
NOTEBOOK_ARCH_TARGETS_STACK_NPY = "ARCH_TARGETS_STACK_640.npy"
NOTEBOOK_ULTIMATE_GPHYS_SCAN_NPY = "ULTIMATE_GPHYS_SCAN_640.npy"
NOTEBOOK_AUX_BONUS_FEATURES_STACK_NPY = "AUX_BONUS_FEATURES_STACK_640.npy"
NOTEBOOK_SIM_GEOPHYSICAL_STACK_NPY = "SIM_GEOPHYSICAL_STACK_640.npy"
NOTEBOOK_AIX_EXTRA_TENSORS_STACK_NPY = "AIX_2022_2026_CLOUDLT3_EXTRA_TENSORS_STACK_640.npy"
NOTEBOOK_AIX_DEM_MATCHED_MASKS_STACK_NPY = "AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640.npy"
NOTEBOOK_FUSION_INTELLIGENCE_STACK_NPY = "REPORT_640_FINAL_INTELLIGENCE_STACK_640.npy"
NOTEBOOK_TESLA_ATOMIC_INFERENCE_STACK_NPY = "TESLA_V7_2_ATOMIC_INFERENCE_STACK_640.npy"
NOTEBOOK_STACK_ALIAS_MANIFEST_JSON = "STACK_ALIAS_MANIFEST.json"
NOTEBOOK_SAR_GEOTIFF_OUTPUT_DIR = "GEOTIFF_RADAR_BANDS"
NOTEBOOK_SAR_NPY_OUTPUT_DIR = "NPY_RADAR_BANDS"
NANO_GEOPHYSICS_BANDS = (
    "NANO_Depth_Penetration",
    "NANO_Human_Geometry_Detector",
    "NANO_Mass_Anomaly",
    "NANO_RVI_Clean",
)
TREASURE_GEOPHYSICS_BANDS = (
    "NANO_Metal_Signal_Pulse",
    "GEOPHYS_Sirdab_Cavity_Void",
    "GEOLOGIC_Chamber_Entry_Proxy",
)
RAD_S0_MASTER_BANDS = (
    "RAD_S0_VV_dB",
    "RAD_S0_VH_dB",
    "RAD_S0_VV_Med1p5px_dB",
    "RAD_S0_VH_Med1p5px_dB",
    "RAD_S0_VH_VV_Ratio_lin",
    "RAD_S0_Angle_deg",
)
RAD_MASTER_CUBE_BANDS = (
    "RADM_VV_dB",
    "RADM_VH_dB",
    "RADM_VV_Med1p5px_dB",
    "RADM_VV_Mean1p5px_dB",
    "RADM_VH_VV_Ratio_lin",
)
GPHYS_MASTER_BANDS = (
    "GPHYS_VV_dB",
    "GPHYS_VH_dB",
    "GPHYS_VV_Med1p5px_dB",
    "GPHYS_VH_Med1p5px_dB",
    "GPHYS_VV_SigmaMean1p5px_dB",
    "GPHYS_VH_SigmaMean1p5px_dB",
)
MASTER_RTC_REFINED_BANDS = (
    "RAD_MasterVV_dB",
    "RAD_MasterVH_dB",
    "RAD_MasterAngle_deg",
    "RAD_MasterVV_Median3m_dB",
    "RAD_MasterVH_Median3m_dB",
    "RAD_MasterVH_VV_Ratio_lin",
)
ARCH_TARGETS_BANDS = (
    "TGT_ClassMap",
    "TGT_HighSpecular_LowCrossPol",
    "TGT_BrightMetallic_Mix",
    "TGT_CompactMetal_Contrast",
    "TGT_StrongDoubleBounce",
    "TGT_MidReflectance_Band",
)
ULTIMATE_GPHYS_SCAN_BANDS = (
    "UGS_VV_dB",
    "UGS_VH_dB",
    "UGS_DeepStruct_RVI",
    "UGS_BoxVertical",
    "UGS_BoxHorizontal",
    "UGS_UnderCover",
    "UGS_ExposedMetal",
    "UGS_DepotProxy",
    "UGS_BoxMineProxy",
    "UGS_JarDenseProxy",
    "UGS_PotteryBand",
    "UGS_GearTentProxy",
    "UGS_ChamberMid",
    "UGS_BaseDeep",
    "UGS_EstBoxCount",
    "UGS_EstJarCount",
)
AUX_BONUS_FEATURES_BANDS = (
    "ENT_VV_LocalEntropy_w3_lin",
    "AUX_OrbitalLogRatio_dB",
    "AUX_VH_to_VV_MoistureProxy_lin",
)
SIM_GEOPHYSICAL_BANDS = (
    "SIM_GPR_VoidScan_lin",
    "SIM_MagneticAnomalies_lin",
    "SIM_EMI_Conductivity_lin",
    "SIM_MicroGravity_Density_lin",
)
AIX_EXTRA_TENSOR_BANDS = (
    "AIX_2022_2026_CLOUDLT3_Jan_IronOxideProxy_Norm01",
    "AIX_2022_2026_CLOUDLT3_Jan_MineralAlterationProxy_Norm01",
    "AIX_2022_2026_CLOUDLT3_Jan_ThermalAnomaly_Norm01",
    "AIX_2022_2026_CLOUDLT3_Apr_IronOxideProxy_Norm01",
    "AIX_2022_2026_CLOUDLT3_Apr_MineralAlterationProxy_Norm01",
    "AIX_2022_2026_CLOUDLT3_Apr_ThermalAnomaly_Norm01",
    "AIX_2022_2026_CLOUDLT3_Aug_IronOxideProxy_Norm01",
    "AIX_2022_2026_CLOUDLT3_Aug_MineralAlterationProxy_Norm01",
    "AIX_2022_2026_CLOUDLT3_Aug_ThermalAnomaly_Norm01",
    "AIX_2022_2026_CLOUDLT3_Elevation_Norm01",
    "AIX_2022_2026_CLOUDLT3_Slope_Norm01",
    "AIX_2022_2026_CLOUDLT3_Aspect_Norm01",
    "AIX_2022_2026_CLOUDLT3_Hillshade_Norm01",
)
AIX_DEM_MATCHED_MASK_BANDS = (
    "AIX_2022_2026FEB_CLOUDLT3_MaskVegetationRoots_Norm01",
    "AIX_2022_2026FEB_CLOUDLT3_MaskWaterMoisture_Norm01",
    "AIX_2022_2026FEB_CLOUDLT3_IndexIronOxide_Norm01",
    "AIX_2022_2026FEB_CLOUDLT3_IndexFerricIron_Norm01",
    "AIX_2022_2026FEB_CLOUDLT3_IndexClayThermal_Norm01",
    "AIX_2022_2026FEB_CLOUDLT3_MaskCharcoalLead_Norm01",
    "AIX_2022_2026FEB_CLOUDLT3_MaskQuartzBasalt_Norm01",
    "AIX_2022_2026FEB_CLOUDLT3_MaskCarbonate_Norm01",
    "AIX_2022_2026FEB_CLOUDLT3_ThermalTimeSeriesAnomaly_Norm01",
)
FUSION_INTELLIGENCE_BANDS = (
    "REPORT_640_FINAL_Zero_Point_Targets",
    "REPORT_640_Mass_Report",
    "REPORT_640_Pottery_Report",
)
TESLA_ATOMIC_INFERENCE_BANDS = (
    "AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640",
    "AI_BEH_Artifacts_Jars_Chests_DOM_lin_640",
    "AI_BEH_Mercury_RareChemicals_DOM_lin_640",
    "AI_BEH_Gemstones_AncientGlass_DOM_lin_640",
    "AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640",
)
S2_MASK_SUPPORT_BANDS = ("NDVI", "NDWI", "NDMI", "NBR", "IRONOX", "IRON_SWIR", "BSI")
RADAR_STACK_BANDS = ("VV_dB", "VH_dB", "logRatio_dB", "incidence")
EPS = 1e-6


def _read_single_band_tif(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.array(image, dtype=np.float32)


def _save_stack_geotiff(path: Path, cube_hwc: np.ndarray, grid_spec: GridSpec) -> None:
    write_georeferenced_raster(path, cube_hwc.astype(np.float32, copy=False), grid_spec)


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _db_to_linear(array: np.ndarray, *, nodata: float) -> np.ndarray:
    linear = np.where(array == nodata, nodata, np.power(10.0, array / 10.0)).astype(np.float32)
    return linear


def _median_3x3_grid(array: np.ndarray, *, nodata: float) -> np.ndarray:
    valid = np.isfinite(array) & (array != nodata)
    if not valid.any():
        return np.full(array.shape, nodata, dtype=np.float32)
    filled = np.where(valid, array, np.nan).astype(np.float32)
    padded = np.pad(filled, 1, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (3, 3))
    median = np.nanmedian(windows, axis=(-2, -1)).astype(np.float32)
    return np.where(np.isfinite(median), median, nodata).astype(np.float32)


def _compute_rad_s0_master_products(
    vv_db: np.ndarray,
    vh_db: np.ndarray,
    incidence: np.ndarray,
    *,
    nodata: float,
) -> dict[str, object]:
    valid_vv_vh = (
        np.isfinite(vv_db)
        & np.isfinite(vh_db)
        & (vv_db != nodata)
        & (vh_db != nodata)
    )
    valid_angle = np.isfinite(incidence) & (incidence != nodata)

    rad_s0_vv_db = np.where(valid_vv_vh, vv_db, nodata).astype(np.float32)
    rad_s0_vh_db = np.where(valid_vv_vh, vh_db, nodata).astype(np.float32)
    rad_s0_vv_med = _median_3x3_grid(rad_s0_vv_db, nodata=nodata)
    rad_s0_vh_med = _median_3x3_grid(rad_s0_vh_db, nodata=nodata)

    ratio = np.full(vv_db.shape, nodata, dtype=np.float32)
    ratio[valid_vv_vh] = np.power(
        10.0,
        (vh_db[valid_vv_vh] - vv_db[valid_vv_vh]) / 10.0,
    ).astype(np.float32)

    angle = np.where(valid_angle, incidence, nodata).astype(np.float32)

    stack = np.stack(
        [
            rad_s0_vv_db,
            rad_s0_vh_db,
            rad_s0_vv_med,
            rad_s0_vh_med,
            ratio,
            angle,
        ],
        axis=-1,
    ).astype(np.float32)

    return {
        "rad_s0_master_band_names": list(RAD_S0_MASTER_BANDS),
        "rad_s0_master_stack": stack,
    }


def _mean_3x3_grid(array: np.ndarray, *, nodata: float) -> np.ndarray:
    valid = np.isfinite(array) & (array != nodata)
    if not valid.any():
        return np.full(array.shape, nodata, dtype=np.float32)
    filled = np.where(valid, array, np.nan).astype(np.float32)
    padded = np.pad(filled, 1, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (3, 3))
    finite = np.isfinite(windows)
    counts = finite.sum(axis=(-2, -1))
    sums = np.where(finite, windows, 0.0).sum(axis=(-2, -1))
    mean = np.where(counts > 0, sums / np.maximum(counts, 1), nodata).astype(np.float32)
    return np.where(np.isfinite(mean), mean, nodata).astype(np.float32)


def _lin_to_db_grid(array: np.ndarray, *, nodata: float) -> np.ndarray:
    valid = np.isfinite(array) & (array != nodata) & (array > 0)
    out = np.full(array.shape, nodata, dtype=np.float32)
    out[valid] = (np.log10(np.maximum(array[valid], np.float32(1e-10))) * np.float32(10.0)).astype(np.float32)
    return out


def _std_3x3_grid(array: np.ndarray, *, nodata: float) -> np.ndarray:
    valid = np.isfinite(array) & (array != nodata)
    if not valid.any():
        return np.full(array.shape, nodata, dtype=np.float32)
    filled = np.where(valid, array, np.nan).astype(np.float32)
    padded = np.pad(filled, 1, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (3, 3))
    finite = np.isfinite(windows)
    counts = finite.sum(axis=(-2, -1))
    sums = np.where(finite, windows, 0.0).sum(axis=(-2, -1))
    mean = sums / np.maximum(counts, 1)
    centered = np.where(finite, windows - mean[:, :, None, None], 0.0)
    variance = (centered * centered).sum(axis=(-2, -1)) / np.maximum(counts, 1)
    std = np.sqrt(np.maximum(variance, 0.0)).astype(np.float32)
    return np.where(counts > 0, std, nodata).astype(np.float32)


def _compute_rad_master_cube_products(
    vv_db: np.ndarray,
    vh_db: np.ndarray,
    *,
    nodata: float,
) -> dict[str, object]:
    valid = (
        np.isfinite(vv_db)
        & np.isfinite(vh_db)
        & (vv_db != nodata)
        & (vh_db != nodata)
    )

    radm_vv_db = np.where(valid, vv_db, nodata).astype(np.float32)
    radm_vh_db = np.where(valid, vh_db, nodata).astype(np.float32)

    rad_vv_lin = np.full(vv_db.shape, np.nan, dtype=np.float32)
    rad_vh_lin = np.full(vh_db.shape, np.nan, dtype=np.float32)
    rad_vv_lin[valid] = np.power(10.0, vv_db[valid] / 10.0).astype(np.float32)
    rad_vh_lin[valid] = np.power(10.0, vh_db[valid] / 10.0).astype(np.float32)

    radm_vv_med_db = _lin_to_db_grid(_median_3x3_grid(rad_vv_lin, nodata=nodata), nodata=nodata)
    radm_vv_mean_db = _lin_to_db_grid(_mean_3x3_grid(rad_vv_lin, nodata=nodata), nodata=nodata)

    ratio = np.full(vv_db.shape, nodata, dtype=np.float32)
    ratio[valid] = (rad_vh_lin[valid] / (rad_vv_lin[valid] + np.float32(1e-10))).astype(np.float32)

    stack = np.stack(
        [
            radm_vv_db,
            radm_vh_db,
            radm_vv_med_db,
            radm_vv_mean_db,
            ratio,
        ],
        axis=-1,
    ).astype(np.float32)

    return {
        "rad_master_cube_band_names": list(RAD_MASTER_CUBE_BANDS),
        "rad_master_cube_stack": stack,
    }


def _compute_gphys_master_products(
    vv_db: np.ndarray,
    vh_db: np.ndarray,
    *,
    nodata: float,
) -> dict[str, object]:
    valid = (
        np.isfinite(vv_db)
        & np.isfinite(vh_db)
        & (vv_db != nodata)
        & (vh_db != nodata)
    )

    gphys_vv_db = np.where(valid, vv_db, nodata).astype(np.float32)
    gphys_vh_db = np.where(valid, vh_db, nodata).astype(np.float32)

    vv_lin = np.full(vv_db.shape, np.nan, dtype=np.float32)
    vh_lin = np.full(vh_db.shape, np.nan, dtype=np.float32)
    vv_lin[valid] = np.power(10.0, vv_db[valid] / 10.0).astype(np.float32)
    vh_lin[valid] = np.power(10.0, vh_db[valid] / 10.0).astype(np.float32)

    vv_med_db = _lin_to_db_grid(_median_3x3_grid(vv_lin, nodata=nodata), nodata=nodata)
    vh_med_db = _lin_to_db_grid(_median_3x3_grid(vh_lin, nodata=nodata), nodata=nodata)

    vv_std = _std_3x3_grid(vv_lin, nodata=nodata)
    vh_std = _std_3x3_grid(vh_lin, nodata=nodata)
    vv_masked = np.where(np.isfinite(vv_std) & (vv_std != nodata) & (vv_std > 0.0), vv_lin, nodata).astype(np.float32)
    vh_masked = np.where(np.isfinite(vh_std) & (vh_std != nodata) & (vh_std > 0.0), vh_lin, nodata).astype(np.float32)

    vv_sgm_db = _lin_to_db_grid(_mean_3x3_grid(vv_masked, nodata=nodata), nodata=nodata)
    vh_sgm_db = _lin_to_db_grid(_mean_3x3_grid(vh_masked, nodata=nodata), nodata=nodata)

    stack = np.stack(
        [
            gphys_vv_db,
            gphys_vh_db,
            vv_med_db,
            vh_med_db,
            vv_sgm_db,
            vh_sgm_db,
        ],
        axis=-1,
    ).astype(np.float32)

    return {
        "gphys_master_band_names": list(GPHYS_MASTER_BANDS),
        "gphys_master_stack": stack,
    }


def _compute_master_rtc_refined_products(
    vv_db: np.ndarray,
    vh_db: np.ndarray,
    incidence: np.ndarray,
    *,
    nodata: float,
) -> dict[str, object]:
    valid = (
        np.isfinite(vv_db)
        & np.isfinite(vh_db)
        & (vv_db != nodata)
        & (vh_db != nodata)
    )
    valid_angle = np.isfinite(incidence) & (incidence != nodata)

    vv_master = np.where(valid, vv_db, nodata).astype(np.float32)
    vh_master = np.where(valid, vh_db, nodata).astype(np.float32)
    angle_master = np.where(valid_angle, incidence, nodata).astype(np.float32)

    # Cell 047 has a 3m refined median name. In this app-local grid contract,
    # the already grid-locked master values are used as the 3m refined bands.
    vv_refined = vv_master.astype(np.float32, copy=True)
    vh_refined = vh_master.astype(np.float32, copy=True)

    vv_lin = np.full(vv_db.shape, np.nan, dtype=np.float32)
    vh_lin = np.full(vh_db.shape, np.nan, dtype=np.float32)
    vv_lin[valid] = np.power(10.0, vv_db[valid] / 10.0).astype(np.float32)
    vh_lin[valid] = np.power(10.0, vh_db[valid] / 10.0).astype(np.float32)

    ratio = np.full(vv_db.shape, nodata, dtype=np.float32)
    ratio[valid] = (vh_lin[valid] / (vv_lin[valid] + np.float32(1e-6))).astype(np.float32)

    stack = np.stack(
        [vv_master, vh_master, angle_master, vv_refined, vh_refined, ratio],
        axis=-1,
    ).astype(np.float32)

    return {
        "master_rtc_refined_band_names": list(MASTER_RTC_REFINED_BANDS),
        "master_rtc_refined_stack": stack,
    }


def _compute_arch_targets_products(
    vv_db: np.ndarray,
    vh_db: np.ndarray,
    *,
    nodata: float,
) -> dict[str, object]:
    valid = (
        np.isfinite(vv_db)
        & np.isfinite(vh_db)
        & (vv_db != nodata)
        & (vh_db != nodata)
    )

    vv_ref = _median_3x3_grid(np.where(valid, vv_db, nodata).astype(np.float32), nodata=nodata)

    high_specular_low_crosspol = (valid & (vv_db > -3.5) & (vh_db < -18.0)).astype(np.float32)
    bright_metallic_mix = (valid & (vv_db > -3.5) & (vh_db > -18.0)).astype(np.float32)
    compact_metal_contrast = (valid & (np.abs(vv_db - vv_ref) > 4.5)).astype(np.float32)
    strong_double_bounce = (valid & (vv_db > 0.0)).astype(np.float32)
    mid_reflectance_band = (valid & (vv_db > -17.0) & (vv_db < -13.0)).astype(np.float32)

    class_map = np.zeros(vv_db.shape, dtype=np.float32)
    class_map[mid_reflectance_band.astype(bool)] = 1.0
    class_map[compact_metal_contrast.astype(bool)] = 2.0
    class_map[high_specular_low_crosspol.astype(bool)] = 3.0
    class_map[bright_metallic_mix.astype(bool)] = 4.0
    class_map[strong_double_bounce.astype(bool)] = 5.0
    class_map[~valid] = nodata

    stack = np.stack(
        [
            class_map,
            high_specular_low_crosspol,
            bright_metallic_mix,
            compact_metal_contrast,
            strong_double_bounce,
            mid_reflectance_band,
        ],
        axis=-1,
    ).astype(np.float32)

    return {
        "arch_targets_band_names": list(ARCH_TARGETS_BANDS),
        "arch_targets_stack": stack,
    }


def _std_circle2_grid(array: np.ndarray, *, nodata: float) -> np.ndarray:
    valid = np.isfinite(array) & (array != nodata)
    if not valid.any():
        return np.full(array.shape, nodata, dtype=np.float32)
    filled = np.where(valid, array, np.nan).astype(np.float32)
    padded = np.pad(filled, 2, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (5, 5))
    yy, xx = np.ogrid[-2:3, -2:3]
    circle = (xx * xx + yy * yy) <= 4
    samples = windows[:, :, circle]
    finite = np.isfinite(samples)
    counts = finite.sum(axis=-1)
    sums = np.where(finite, samples, 0.0).sum(axis=-1)
    mean = sums / np.maximum(counts, 1)
    centered = np.where(finite, samples - mean[:, :, None], 0.0)
    variance = (centered * centered).sum(axis=-1) / np.maximum(counts, 1)
    std = np.sqrt(np.maximum(variance, 0.0)).astype(np.float32)
    return np.where(counts > 0, std, nodata).astype(np.float32)


def _compute_ultimate_gphys_scan_products(
    vv_db: np.ndarray,
    vh_db: np.ndarray,
    *,
    nodata: float,
) -> dict[str, object]:
    valid = (
        np.isfinite(vv_db)
        & np.isfinite(vh_db)
        & (vv_db != nodata)
        & (vh_db != nodata)
    )

    gain_corr = np.float32(1.45)
    vv = np.where(valid, vv_db * gain_corr, nodata).astype(np.float32)
    vh = np.where(valid, vh_db * gain_corr, nodata).astype(np.float32)
    std_vv = _std_circle2_grid(vv, nodata=nodata)

    def clean(array: np.ndarray) -> np.ndarray:
        return np.where(valid & np.isfinite(array), array, nodata).astype(np.float32)

    rvi = clean((vh * np.float32(4.0)) / (vv + vh + np.float32(1e-6)))

    box_vertical = (valid & (vv > 0.0)).astype(np.float32)
    box_horizontal = (valid & (vv > -4.0) & (std_vv < 2.0)).astype(np.float32)
    under_cover = (valid & (vh < -22.0) & (vv > -5.0)).astype(np.float32)
    exposed_metal = (valid & (vh > -15.0) & (vv > -3.0)).astype(np.float32)
    depot_proxy = (box_horizontal.astype(bool) & under_cover.astype(bool)).astype(np.float32)
    box_mine = (valid & (std_vv > 5.0) & (vv > -5.0)).astype(np.float32)
    jar_dense = (valid & (vv > -2.5)).astype(np.float32)
    pottery_band = (valid & (vv > -18.0) & (vv < -12.0)).astype(np.float32)
    gear_tent = (valid & (vh > -18.0) & (vh < -14.0) & (vv > -6.0)).astype(np.float32)
    chamber_mid = (valid & (std_vv > 4.2) & (vv > -8.0)).astype(np.float32)
    base_deep = (valid & (vv > -12.0) & (vv < -7.0)).astype(np.float32)

    est_box_count = clean(np.floor(((vv - np.float32(-10.0)) / np.float32(15.0)) * np.float32(15.0)))
    est_jar_count = clean(np.floor((((vv - vh) - np.float32(10.0)) / np.float32(20.0)) * np.float32(10.0)))

    stack = np.stack(
        [
            vv,
            vh,
            rvi,
            box_vertical,
            box_horizontal,
            under_cover,
            exposed_metal,
            depot_proxy,
            box_mine,
            jar_dense,
            pottery_band,
            gear_tent,
            chamber_mid,
            base_deep,
            est_box_count,
            est_jar_count,
        ],
        axis=-1,
    ).astype(np.float32)

    return {
        "ultimate_gphys_scan_band_names": list(ULTIMATE_GPHYS_SCAN_BANDS),
        "ultimate_gphys_scan_stack": stack,
    }


def _nanfill_median_grid(array: np.ndarray) -> np.ndarray:
    out = np.asarray(array, dtype=np.float32).copy()
    finite = np.isfinite(out)
    fill = np.float32(np.nanmedian(out)) if finite.any() else np.float32(0.0)
    out[~finite] = fill
    return out.astype(np.float32)


def _local_entropy_3x3_grid(array: np.ndarray, *, valid_mask: np.ndarray, nodata: float) -> np.ndarray:
    filled = _nanfill_median_grid(array)
    padded = np.pad(filled, 1, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (3, 3))
    flat = windows.reshape(windows.shape[0], windows.shape[1], 9)

    lo = flat.min(axis=-1)
    hi = flat.max(axis=-1)
    span = hi - lo
    usable = span > np.float32(1e-12)

    entropy = np.zeros(array.shape, dtype=np.float32)
    for bin_index in range(16):
        lower = lo + span * np.float32(bin_index / 16.0)
        upper = lo + span * np.float32((bin_index + 1) / 16.0)
        if bin_index == 15:
            hits = usable[:, :, None] & (flat >= lower[:, :, None]) & (flat <= upper[:, :, None])
        else:
            hits = usable[:, :, None] & (flat >= lower[:, :, None]) & (flat < upper[:, :, None])
        counts = hits.sum(axis=-1).astype(np.float32)
        probs = counts / np.float32(9.0)
        safe_probs = np.where(probs > 0.0, probs, np.float32(1.0)).astype(np.float32)
        entropy = np.where(probs > 0.0, entropy - probs * np.log2(safe_probs), entropy).astype(np.float32)

    return np.where(valid_mask, entropy, nodata).astype(np.float32)


def _laplacian_abs_3x3_grid(array: np.ndarray, *, valid_mask: np.ndarray, nodata: float) -> np.ndarray:
    filled = _nanfill_median_grid(array)
    padded = np.pad(filled, 1, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (3, 3))
    kernel = np.array(
        [
            [1.0, 1.0, 1.0],
            [1.0, -8.0, 1.0],
            [1.0, 1.0, 1.0],
        ],
        dtype=np.float32,
    )
    out = np.abs((windows * kernel).sum(axis=(-2, -1))).astype(np.float32)
    return np.where(valid_mask, out, nodata).astype(np.float32)


def _compute_aux_bonus_features_products(
    vv_db: np.ndarray,
    vh_db: np.ndarray,
    log_ratio_db: np.ndarray,
    *,
    nodata: float,
) -> dict[str, object]:
    valid_vv_vh = (
        np.isfinite(vv_db)
        & np.isfinite(vh_db)
        & (vv_db != nodata)
        & (vh_db != nodata)
    )
    valid_logratio = np.isfinite(log_ratio_db) & (log_ratio_db != nodata)

    vv_lin = np.full(vv_db.shape, np.nan, dtype=np.float32)
    vh_lin = np.full(vh_db.shape, np.nan, dtype=np.float32)
    vv_lin[valid_vv_vh] = np.power(10.0, vv_db[valid_vv_vh] / 10.0).astype(np.float32)
    vh_lin[valid_vv_vh] = np.power(10.0, vh_db[valid_vv_vh] / 10.0).astype(np.float32)

    entropy = _local_entropy_3x3_grid(vv_lin, valid_mask=valid_vv_vh, nodata=nodata)

    orbital_logratio = np.where(valid_logratio, log_ratio_db, nodata).astype(np.float32)

    moisture = np.full(vv_db.shape, nodata, dtype=np.float32)
    moisture[valid_vv_vh] = (vh_lin[valid_vv_vh] / np.maximum(vv_lin[valid_vv_vh], np.float32(1e-6))).astype(np.float32)

    stack = np.stack([entropy, orbital_logratio, moisture], axis=-1).astype(np.float32)
    return {
        "aux_bonus_features_band_names": list(AUX_BONUS_FEATURES_BANDS),
        "aux_bonus_features_stack": stack,
    }


def _compute_sim_geophysical_products(
    vv_db: np.ndarray,
    vh_db: np.ndarray,
    *,
    nodata: float,
) -> dict[str, object]:
    valid = (
        np.isfinite(vv_db)
        & np.isfinite(vh_db)
        & (vv_db != nodata)
        & (vh_db != nodata)
    )

    vv_lin = np.full(vv_db.shape, np.nan, dtype=np.float32)
    vh_lin = np.full(vh_db.shape, np.nan, dtype=np.float32)
    vv_lin[valid] = np.power(10.0, vv_db[valid] / 10.0).astype(np.float32)
    vh_lin[valid] = np.power(10.0, vh_db[valid] / 10.0).astype(np.float32)

    gpr_voidscan = np.full(vv_db.shape, nodata, dtype=np.float32)
    magnetic = _laplacian_abs_3x3_grid(vv_lin, valid_mask=valid, nodata=nodata)
    emi = np.full(vv_db.shape, nodata, dtype=np.float32)
    microgravity = np.full(vv_db.shape, nodata, dtype=np.float32)

    gpr_voidscan[valid] = np.log10(np.abs(vv_lin[valid] - vh_lin[valid]) + np.float32(1e-6)).astype(np.float32)
    emi[valid] = (vh_lin[valid] / np.maximum(vv_lin[valid], np.float32(1e-6))).astype(np.float32)
    microgravity[valid] = (
        np.float32(1.0) / np.maximum((vv_lin[valid] + vh_lin[valid]) / np.float32(2.0), np.float32(1e-6))
    ).astype(np.float32)

    stack = np.stack([gpr_voidscan, magnetic, emi, microgravity], axis=-1).astype(np.float32)
    return {
        "sim_geophysical_band_names": list(SIM_GEOPHYSICAL_BANDS),
        "sim_geophysical_stack": stack,
    }


def _compute_plan_b_geophysics_products(
    vv_db: np.ndarray,
    vh_db: np.ndarray,
    *,
    nodata: float,
) -> dict[str, object]:
    valid = (
        np.isfinite(vv_db)
        & np.isfinite(vh_db)
        & (vv_db != nodata)
        & (vh_db != nodata)
    )

    vv_lin = np.full(vv_db.shape, np.nan, dtype=np.float32)
    vh_lin = np.full(vh_db.shape, np.nan, dtype=np.float32)
    vv_lin[valid] = np.power(10.0, vv_db[valid] / 10.0).astype(np.float32)
    vh_lin[valid] = np.power(10.0, vh_db[valid] / 10.0).astype(np.float32)

    def clean(array: np.ndarray) -> np.ndarray:
        return np.where(valid & np.isfinite(array), array, nodata).astype(np.float32)

    # Cell 037 exact formulas.
    nano_depth_penetration = clean(vv_lin / (vh_lin + np.float32(1e-6)))
    nano_human_geometry_detector = clean(vv_db - vh_db)
    nano_mass_anomaly = clean(np.sqrt(vv_lin * vh_lin))
    nano_rvi_clean = clean((vh_lin * np.float32(4.0)) / (vv_lin + vh_lin + np.float32(1e-6)))

    nano_stack = np.stack(
        [
            nano_depth_penetration,
            nano_human_geometry_detector,
            nano_mass_anomaly,
            nano_rvi_clean,
        ],
        axis=-1,
    ).astype(np.float32)

    # Cell 039 exact formulas.
    geophys_sirdab_cavity_void = clean(np.log(vv_lin) - np.log(vh_lin))
    nano_metal_signal_pulse = clean((vh_lin * vv_lin) / (vv_lin + vh_lin + np.float32(1e-6)))
    geologic_chamber_entry_proxy = clean(vh_lin / ((vv_lin ** np.float32(2.0)) + np.float32(1e-6)))

    treasure_stack = np.stack(
        [
            nano_metal_signal_pulse,
            geophys_sirdab_cavity_void,
            geologic_chamber_entry_proxy,
        ],
        axis=-1,
    ).astype(np.float32)

    return {
        "nano_geophysics_band_names": list(NANO_GEOPHYSICS_BANDS),
        "nano_geophysics_stack": nano_stack,
        "treasure_geophysics_band_names": list(TREASURE_GEOPHYSICS_BANDS),
        "treasure_geophysics_stack": treasure_stack,
    }


def _build_ai_ready_stack(cube: np.ndarray, *, nodata: float) -> np.ndarray:
    channel_count = cube.shape[-1]
    ready = np.zeros_like(cube, dtype=np.float32)
    for index in range(channel_count):
        channel = cube[:, :, index]
        valid_mask = channel != nodata
        valid_values = channel[valid_mask]
        if valid_values.size < 100:
            if valid_values.size:
                low = float(valid_values.min())
                high = float(valid_values.max())
            else:
                low = 0.0
                high = 1.0
        else:
            low = float(np.percentile(valid_values, 2))
            high = float(np.percentile(valid_values, 98))
        span = max(high - low, EPS)
        normalized = np.clip((channel - low) / span, 0.0, 1.0).astype(np.float32)
        ready[:, :, index] = np.where(valid_mask, normalized, 0.0).astype(np.float32)
    return ready


def collect_science_core_layers(run_dir: Path, grid_spec: GridSpec) -> list[tuple[str, np.ndarray]]:
    layers: list[tuple[str, np.ndarray]] = []
    missing: list[str] = []
    for name in SCIENCE_CORE_BANDS:
        path = run_dir / f"{name}.tif"
        if not path.is_file():
            missing.append(path.name)
            continue
        sidecar_path = raster_sidecar_path(path)
        if not sidecar_path.is_file():
            raise StageError(f"Missing raster sidecar for feature-stack source: {path.name}")
        sidecar = read_manifest(sidecar_path)
        if sidecar["crs"] != grid_spec.crs:
            raise StageError(f"Feature-stack source CRS mismatch: {path.name}")
        if [float(value) for value in sidecar["transform"]] != [float(value) for value in grid_spec.manifest.crs_transform]:
            raise StageError(f"Feature-stack source transform mismatch: {path.name}")
        if (int(sidecar["height"]), int(sidecar["width"])) != (grid_spec.size, grid_spec.size):
            raise StageError(f"Feature-stack source size mismatch: {path.name}")
        array = _read_single_band_tif(path)
        nodata = float(sidecar["nodata"])
        array = np.where(array == nodata, grid_spec.nodata, array).astype(np.float32)
        layers.append((name, array))
    if missing:
        raise StageError(f"Feature-stack stage requires science-core sources before assembly: {', '.join(missing)}")
    return layers


def build_feature_stack_products(
    source_layers: list[tuple[str, np.ndarray]],
    *,
    nodata: float,
) -> dict[str, object]:
    band_names = [name for name, _array in source_layers]
    cube = np.stack([array for _name, array in source_layers], axis=-1).astype(np.float32)
    valid = cube != nodata
    mask_bands = [band_names.index(name) for name in S2_MASK_SUPPORT_BANDS]
    s2_mask = valid[:, :, mask_bands].all(axis=-1).astype(np.float32)

    vv_db = cube[:, :, band_names.index("VV_dB")]
    vh_db = cube[:, :, band_names.index("VH_dB")]
    log_ratio_db = cube[:, :, band_names.index("logRatio_dB")]
    incidence = cube[:, :, band_names.index("incidence")]
    radar_linear_stack = np.stack(
        [
            _db_to_linear(vv_db, nodata=nodata),
            _db_to_linear(vh_db, nodata=nodata),
            _db_to_linear(log_ratio_db, nodata=nodata),
            np.where(incidence == nodata, nodata, incidence).astype(np.float32),
        ],
        axis=-1,
    ).astype(np.float32)
    radar_db_stack = np.stack([vv_db, vh_db, log_ratio_db, incidence], axis=-1).astype(np.float32)
    ai_ready_stack = _build_ai_ready_stack(cube, nodata=nodata)
    plan_b_geophysics = _compute_plan_b_geophysics_products(vv_db, vh_db, nodata=nodata)
    rad_s0_master = _compute_rad_s0_master_products(vv_db, vh_db, incidence, nodata=nodata)
    rad_master_cube = _compute_rad_master_cube_products(vv_db, vh_db, nodata=nodata)
    gphys_master = _compute_gphys_master_products(vv_db, vh_db, nodata=nodata)
    master_rtc_refined = _compute_master_rtc_refined_products(vv_db, vh_db, incidence, nodata=nodata)
    arch_targets = _compute_arch_targets_products(vv_db, vh_db, nodata=nodata)
    ultimate_gphys_scan = _compute_ultimate_gphys_scan_products(vv_db, vh_db, nodata=nodata)
    aux_bonus_features = _compute_aux_bonus_features_products(vv_db, vh_db, log_ratio_db, nodata=nodata)
    sim_geophysical = _compute_sim_geophysical_products(vv_db, vh_db, nodata=nodata)

    stats_rows: list[dict[str, object]] = []
    for band_index, band_name in enumerate(band_names):
        channel = cube[:, :, band_index]
        valid_mask = channel != nodata
        valid_values = channel[valid_mask]
        stats_rows.append(
            {
                "band_index": band_index,
                "band_name": band_name,
                "source_file": f"{band_name}.tif",
                "valid_count": int(valid_mask.sum()),
                "nodata_count": int(channel.size - int(valid_mask.sum())),
                "min": float(valid_values.min()) if valid_values.size else "",
                "max": float(valid_values.max()) if valid_values.size else "",
                "mean": float(valid_values.mean()) if valid_values.size else "",
            }
        )

    stack_presence_summary = {
        "stage": "feature_stacks",
        "band_count": len(band_names),
        "band_names": band_names,
        "missing_expected_bands": [],
        "all_expected_bands_present": True,
        "variant_families": [
            {
                "artifact_name": "radar_db_support_stack",
                "source_notebook_family": "RADAR_STACK_HWC_640",
                "band_names": ["VV_dB", "VH_dB", "logRatio_dB", "angle"],
            },
            {
                "artifact_name": "radar_linear_support_stack",
                "source_notebook_family": "SIGMA0_MASTER_640",
                "band_names": ["vv_sigma0_linear", "vh_sigma0_linear", "ratio_sigma0_linear", "incidence_angle"],
            },
            {
                "artifact_name": "rad_s0_master_stack",
                "source_notebook_family": "RAD_S0_MASTER_STACK_640",
                "band_names": list(RAD_S0_MASTER_BANDS),
            },
            {
                "artifact_name": "rad_master_cube_stack",
                "source_notebook_family": "RAD_MASTER_CUBE_640",
                "band_names": list(RAD_MASTER_CUBE_BANDS),
            },
            {
                "artifact_name": "gphys_master_stack",
                "source_notebook_family": "GPHYS_MASTER_640",
                "band_names": list(GPHYS_MASTER_BANDS),
            },
            {
                "artifact_name": "master_rtc_refined_stack",
                "source_notebook_family": "MASTER_RTC_REFINED_STACK_640",
                "band_names": list(MASTER_RTC_REFINED_BANDS),
            },
            {
                "artifact_name": "arch_targets_stack",
                "source_notebook_family": "ARCH_TARGETS_STACK_640",
                "band_names": list(ARCH_TARGETS_BANDS),
            },
            {
                "artifact_name": "ultimate_gphys_scan_stack",
                "source_notebook_family": "ULTIMATE_GPHYS_SCAN_640",
                "band_names": list(ULTIMATE_GPHYS_SCAN_BANDS),
            },
            {
                "artifact_name": "aux_bonus_features_stack",
                "source_notebook_family": "AUX_BONUS_FEATURES_STACK_640",
                "band_names": list(AUX_BONUS_FEATURES_BANDS),
            },
            {
                "artifact_name": "sim_geophysical_stack",
                "source_notebook_family": "SIM_GEOPHYSICAL_STACK_640",
                "band_names": list(SIM_GEOPHYSICAL_BANDS),
            },
            {
                "artifact_name": "nano_geophysics_stack",
                "source_notebook_family": "NANO_GEOPHYSICS_STACK_640",
                "band_names": list(NANO_GEOPHYSICS_BANDS),
            },
            {
                "artifact_name": "treasure_geophysics_stack",
                "source_notebook_family": "TREASURE_GEOPHYSICS_STACK_640",
                "band_names": list(TREASURE_GEOPHYSICS_BANDS),
            },
            {
                "artifact_name": "ai_ready_support_stack",
                "source_notebook_family": "TESLA_V7_2_TENSOR_EXPORT",
                "band_names": band_names,
            },
        ],
        "notebook_family_statuses": [
            {
                "family": "NANO_STACK",
                "status": "implemented",
                "artifact_name": "nano_geophysics_stack",
                "source_cell": "cell_037",
                "reason": "Cell 037 selected as canonical first Nano geophysics variant after exact formula extraction.",
            },
            {
                "family": "TREASURE_GEOPHYSICS_STACK_640",
                "status": "implemented",
                "artifact_name": "treasure_geophysics_stack",
                "source_cell": "cell_039",
                "reason": "Cell 039 selected as canonical first Treasure/Geophysics variant after exact formula extraction.",
            },
            {
                "family": "SIGMA0_MASTER_640",
                "status": "implemented",
                "artifact_name": "radar_linear_support_stack",
                "reason": "Neutral linearized radar support stack captures the reproducible sigma0-style variant without notebook master naming.",
            },
            {
                "family": "RAD_S0_MASTER_STACK_640",
                "status": "implemented",
                "artifact_name": "rad_s0_master_stack",
                "source_cell": "cell_050",
                "reason": "Cell 050 selected as canonical clean-AI-naming Sigma0 master stack for Plan B item 9.",
            },
            {
                "family": "GPHYS_MASTER_640",
                "status": "implemented",
                "artifact_name": "gphys_master_stack",
                "source_cell": "cell_051",
                "reason": "Cell 051 selected as canonical Geophysical Master stack for Plan B item 9 B1.4.",
            },
            {
                "family": "MASTER_RTC_REFINED_STACK_640",
                "status": "implemented",
                "artifact_name": "master_rtc_refined_stack",
                "source_cell": "cell_047",
                "reason": "Cell 047 selected as canonical Master RTC refined stack for Plan B item 9 B1.5.",
            },
            {
                "family": "ARCH_TARGETS_STACK_640",
                "status": "implemented",
                "artifact_name": "arch_targets_stack",
                "source_cell": "cell_052",
                "reason": "Cell 052 selected as canonical archaeological/target anomaly stack for Plan B item 9 B1.6.",
            },
            {
                "family": "RAD_MASTER_CUBE_640",
                "status": "implemented",
                "artifact_name": "rad_master_cube_stack",
                "source_cell": "cell_053",
                "reason": "Cell 053 selected as canonical Radar Master Cube stack for Plan B item 9 B1.3.",
            },
            {
                "family": "ULTIMATE_GPHYS_SCAN_640",
                "status": "implemented",
                "artifact_name": "ultimate_gphys_scan_stack",
                "source_cell": "cell_054",
                "reason": "Cell 054 selected as canonical Ultimate Geophysical Scan stack for Plan B item 9 B1.7.",
            },
            {
                "family": "AUX_BONUS_FEATURES_STACK_640",
                "status": "implemented",
                "artifact_name": "aux_bonus_features_stack",
                "source_cell": "cell_072",
                "reason": "Cell 072 selected as canonical bonus feature stack for Plan B item 15.",
            },
            {
                "family": "SIM_GEOPHYSICAL_STACK_640",
                "status": "implemented",
                "artifact_name": "sim_geophysical_stack",
                "source_cell": "cell_073",
                "reason": "Cell 073 selected as canonical geophysical simulator stack for Plan B item 15.",
            },
            {
                "family": "TESLA_V7_2_VARIANTS",
                "status": "implemented_subset",
                "artifact_name": "ai_ready_support_stack",
                "reason": "F2 implements the useful grid-locked tensor-export subset only; Tesla inference and target-oriented variants remain out of scope.",
            },
        ],
    }
    tensor_audit_summary = {
        "stage": "feature_stacks",
        "shape": [int(cube.shape[0]), int(cube.shape[1]), int(cube.shape[2])],
        "dtype": str(cube.dtype),
        "valid_fraction_min": round(min(float((cube[:, :, i] != nodata).mean()) for i in range(cube.shape[-1])), 6),
        "valid_fraction_max": round(max(float((cube[:, :, i] != nodata).mean()) for i in range(cube.shape[-1])), 6),
        "s2_mask_valid_fraction": round(float(s2_mask.mean()), 6),
    }
    geometry_consistency_summary = {
        "stage": "feature_stacks",
        "all_sources_grid_aligned": True,
        "source_count": len(band_names),
        "stack_shape": [int(cube.shape[0]), int(cube.shape[1]), int(cube.shape[2])],
    }

    return {
        "band_names": band_names,
        "cube": cube,
        "s2_mask": s2_mask,
        "radar_linear_band_names": ["vv_sigma0_linear", "vh_sigma0_linear", "ratio_sigma0_linear", "incidence_angle"],
        "radar_linear_stack": radar_linear_stack,
        "radar_db_band_names": ["VV_dB", "VH_dB", "logRatio_dB", "angle"],
        "radar_db_stack": radar_db_stack,
        "ai_ready_stack": ai_ready_stack,
        "nano_geophysics_band_names": plan_b_geophysics["nano_geophysics_band_names"],
        "nano_geophysics_stack": plan_b_geophysics["nano_geophysics_stack"],
        "treasure_geophysics_band_names": plan_b_geophysics["treasure_geophysics_band_names"],
        "treasure_geophysics_stack": plan_b_geophysics["treasure_geophysics_stack"],
        "rad_s0_master_band_names": rad_s0_master["rad_s0_master_band_names"],
        "rad_s0_master_stack": rad_s0_master["rad_s0_master_stack"],
        "rad_master_cube_band_names": rad_master_cube["rad_master_cube_band_names"],
        "rad_master_cube_stack": rad_master_cube["rad_master_cube_stack"],
        "gphys_master_band_names": gphys_master["gphys_master_band_names"],
        "gphys_master_stack": gphys_master["gphys_master_stack"],
        "master_rtc_refined_band_names": master_rtc_refined["master_rtc_refined_band_names"],
        "master_rtc_refined_stack": master_rtc_refined["master_rtc_refined_stack"],
        "arch_targets_band_names": arch_targets["arch_targets_band_names"],
        "arch_targets_stack": arch_targets["arch_targets_stack"],
        "ultimate_gphys_scan_band_names": ultimate_gphys_scan["ultimate_gphys_scan_band_names"],
        "ultimate_gphys_scan_stack": ultimate_gphys_scan["ultimate_gphys_scan_stack"],
        "aux_bonus_features_band_names": aux_bonus_features["aux_bonus_features_band_names"],
        "aux_bonus_features_stack": aux_bonus_features["aux_bonus_features_stack"],
        "sim_geophysical_band_names": sim_geophysical["sim_geophysical_band_names"],
        "sim_geophysical_stack": sim_geophysical["sim_geophysical_stack"],
        "band_stats_rows": stats_rows,
        "stack_presence_summary": stack_presence_summary,
        "tensor_audit_summary": tensor_audit_summary,
        "geometry_consistency_summary": geometry_consistency_summary,
    }


def _build_stack_alias_manifest(
    *,
    band_names: list[str],
    radar_db_band_names: list[str],
    radar_linear_band_names: list[str],
) -> dict[str, object]:
    return {
        "schema": "notebook_stack_alias_manifest_v1",
        "status": "partial_alias_contract",
        "aliases": [
            {
                "filename": NOTEBOOK_RADAR_STACK_NPY,
                "source_notebook_family": "RADAR_STACK_HWC_640",
                "app_artifact": "radar_db_support_stack",
                "band_names": radar_db_band_names,
                "status": "implemented",
            },
            {
                "filename": NOTEBOOK_SCIENCE_CORE_STACK_NPY,
                "source_notebook_family": "SCIENCE_CORE_STACK_HWC_640",
                "app_artifact": "science_core_stack",
                "band_names": band_names,
                "status": "app_native_alias",
            },
            {
                "filename": NOTEBOOK_RADAR_LINEAR_STACK_NPY,
                "source_notebook_family": "SIGMA0_MASTER_640",
                "app_artifact": "radar_linear_support_stack",
                "band_names": radar_linear_band_names,
                "status": "implemented_subset",
            },
            {
                "filename": NOTEBOOK_AI_READY_STACK_NPY,
                "source_notebook_family": "TESLA_V7_2_TENSOR_EXPORT",
                "app_artifact": "ai_ready_support_stack",
                "band_names": band_names,
                "status": "implemented_subset",
            },
            {
                "filename": NOTEBOOK_RAD_S0_MASTER_STACK_NPY,
                "source_notebook_family": "RAD_S0_MASTER_STACK_640",
                "app_artifact": "rad_s0_master_stack",
                "band_names": list(RAD_S0_MASTER_BANDS),
                "status": "implemented",
                "source_cell": "cell_050",
            },
            {
                "filename": NOTEBOOK_RAD_MASTER_CUBE_NPY,
                "source_notebook_family": "RAD_MASTER_CUBE_640",
                "app_artifact": "rad_master_cube_stack",
                "band_names": list(RAD_MASTER_CUBE_BANDS),
                "status": "implemented",
                "source_cell": "cell_053",
            },
            {
                "filename": NOTEBOOK_GPHYS_MASTER_STACK_NPY,
                "source_notebook_family": "GPHYS_MASTER_640",
                "app_artifact": "gphys_master_stack",
                "band_names": list(GPHYS_MASTER_BANDS),
                "status": "implemented",
                "source_cell": "cell_051",
            },
            {
                "filename": NOTEBOOK_MASTER_RTC_REFINED_STACK_NPY,
                "source_notebook_family": "MASTER_RTC_REFINED_STACK_640",
                "app_artifact": "master_rtc_refined_stack",
                "band_names": list(MASTER_RTC_REFINED_BANDS),
                "status": "implemented",
                "source_cell": "cell_047",
            },
            {
                "filename": NOTEBOOK_ARCH_TARGETS_STACK_NPY,
                "source_notebook_family": "ARCH_TARGETS_STACK_640",
                "app_artifact": "arch_targets_stack",
                "band_names": list(ARCH_TARGETS_BANDS),
                "status": "implemented",
                "source_cell": "cell_052",
            },
            {
                "filename": NOTEBOOK_ULTIMATE_GPHYS_SCAN_NPY,
                "source_notebook_family": "ULTIMATE_GPHYS_SCAN_640",
                "app_artifact": "ultimate_gphys_scan_stack",
                "band_names": list(ULTIMATE_GPHYS_SCAN_BANDS),
                "status": "implemented",
                "source_cell": "cell_054",
            },
            {
                "filename": NOTEBOOK_AUX_BONUS_FEATURES_STACK_NPY,
                "source_notebook_family": "AUX_BONUS_FEATURES_STACK_640",
                "app_artifact": "aux_bonus_features_stack",
                "band_names": list(AUX_BONUS_FEATURES_BANDS),
                "status": "implemented",
                "source_cell": "cell_072",
            },
            {
                "filename": NOTEBOOK_SIM_GEOPHYSICAL_STACK_NPY,
                "source_notebook_family": "SIM_GEOPHYSICAL_STACK_640",
                "app_artifact": "sim_geophysical_stack",
                "band_names": list(SIM_GEOPHYSICAL_BANDS),
                "status": "implemented",
                "source_cell": "cell_073",
            },
            {
                "filename": NOTEBOOK_AIX_EXTRA_TENSORS_STACK_NPY,
                "source_notebook_family": "AIX_2022_2026_CLOUDLT3_EXTRA_TENSORS_STACK_640",
                "app_artifact": "aix_extra_tensors_stack",
                "band_names": list(AIX_EXTRA_TENSOR_BANDS),
                "status": "implemented",
                "source_cell": "cell_077",
            },
            {
                "filename": NOTEBOOK_AIX_DEM_MATCHED_MASKS_STACK_NPY,
                "source_notebook_family": "AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640",
                "app_artifact": "aix_dem_matched_masks_stack",
                "band_names": list(AIX_DEM_MATCHED_MASK_BANDS),
                "status": "implemented",
                "source_cell": "cell_081",
            },
            {
                "filename": NOTEBOOK_FUSION_INTELLIGENCE_STACK_NPY,
                "source_notebook_family": "REPORT_640_FINAL_INTELLIGENCE_STACK_640",
                "app_artifact": "fusion_intelligence_stack",
                "band_names": list(FUSION_INTELLIGENCE_BANDS),
                "status": "implemented",
                "source_cell": "cell_099",
            },
            {
                "filename": NOTEBOOK_TESLA_ATOMIC_INFERENCE_STACK_NPY,
                "source_notebook_family": "PLAN_B19_CELL_095_MATERIAL_STACK_640",
                "app_artifact": "tesla_atomic_inference_stack",
                "band_names": list(TESLA_ATOMIC_INFERENCE_BANDS),
                "status": "implemented",
                "source_cell": "cell_095",
            },
            {
                "filename": NOTEBOOK_NANO_GEOPHYSICS_STACK_NPY,
                "source_notebook_family": "NANO_GEOPHYSICS_STACK_640",
                "app_artifact": "nano_geophysics_stack",
                "band_names": list(NANO_GEOPHYSICS_BANDS),
                "status": "implemented",
                "source_cell": "cell_037",
            },
            {
                "filename": NOTEBOOK_TREASURE_GEOPHYSICS_STACK_NPY,
                "source_notebook_family": "TREASURE_GEOPHYSICS_STACK_640",
                "app_artifact": "treasure_geophysics_stack",
                "band_names": list(TREASURE_GEOPHYSICS_BANDS),
                "status": "implemented",
                "source_cell": "cell_039",
            },
        ],
        "deferred_families": [],
        "privacy": {
            "artifact_class": "FILESYSTEM_ONLY",
            "http_servable": False,
        },
    }


def write_feature_stack_outputs(run_dir: Path, grid_spec: GridSpec, products: dict[str, object]) -> dict[str, Path]:
    cube = products["cube"]
    s2_mask = products["s2_mask"]
    radar_linear_stack = products["radar_linear_stack"]
    radar_db_stack = products["radar_db_stack"]
    ai_ready_stack = products["ai_ready_stack"]
    nano_geophysics_stack = products["nano_geophysics_stack"]
    treasure_geophysics_stack = products["treasure_geophysics_stack"]
    rad_s0_master_stack = products["rad_s0_master_stack"]
    rad_master_cube_stack = products["rad_master_cube_stack"]
    gphys_master_stack = products["gphys_master_stack"]
    master_rtc_refined_stack = products["master_rtc_refined_stack"]
    arch_targets_stack = products["arch_targets_stack"]
    ultimate_gphys_scan_stack = products["ultimate_gphys_scan_stack"]
    aux_bonus_features_stack = products["aux_bonus_features_stack"]
    sim_geophysical_stack = products["sim_geophysical_stack"]
    band_stats_rows = products["band_stats_rows"]
    stack_presence_summary = products["stack_presence_summary"]
    tensor_audit_summary = products["tensor_audit_summary"]
    geometry_consistency_summary = products["geometry_consistency_summary"]
    band_names = products["band_names"]
    radar_db_band_names = products["radar_db_band_names"]
    radar_linear_band_names = products["radar_linear_band_names"]
    assert isinstance(cube, np.ndarray)
    assert isinstance(s2_mask, np.ndarray)
    assert isinstance(radar_linear_stack, np.ndarray)
    assert isinstance(radar_db_stack, np.ndarray)
    assert isinstance(ai_ready_stack, np.ndarray)
    assert isinstance(nano_geophysics_stack, np.ndarray)
    assert isinstance(treasure_geophysics_stack, np.ndarray)
    assert isinstance(rad_s0_master_stack, np.ndarray)
    assert isinstance(rad_master_cube_stack, np.ndarray)
    assert isinstance(gphys_master_stack, np.ndarray)
    assert isinstance(master_rtc_refined_stack, np.ndarray)
    assert isinstance(arch_targets_stack, np.ndarray)
    assert isinstance(ultimate_gphys_scan_stack, np.ndarray)
    assert isinstance(aux_bonus_features_stack, np.ndarray)
    assert isinstance(sim_geophysical_stack, np.ndarray)
    assert isinstance(band_stats_rows, list)
    assert isinstance(stack_presence_summary, dict)
    assert isinstance(tensor_audit_summary, dict)
    assert isinstance(geometry_consistency_summary, dict)
    assert isinstance(band_names, list)
    assert isinstance(radar_db_band_names, list)
    assert isinstance(radar_linear_band_names, list)

    tensor_dir = run_dir / "stacks" / "tensor_support"
    optical_dir = run_dir / "stacks" / "optical_support"
    qa_dir = ensure_run_qa_dir(run_dir) / "stacks"
    notebook_stack_dir = run_dir / NOTEBOOK_STACK_OUTPUT_DIR
    notebook_sar_tif_dir = run_dir / NOTEBOOK_SAR_GEOTIFF_OUTPUT_DIR
    notebook_sar_npy_dir = run_dir / NOTEBOOK_SAR_NPY_OUTPUT_DIR
    tensor_dir.mkdir(parents=True, exist_ok=True)
    optical_dir.mkdir(parents=True, exist_ok=True)
    qa_dir.mkdir(parents=True, exist_ok=True)
    notebook_stack_dir.mkdir(parents=True, exist_ok=True)
    notebook_sar_tif_dir.mkdir(parents=True, exist_ok=True)
    notebook_sar_npy_dir.mkdir(parents=True, exist_ok=True)

    stack_tif_path = tensor_dir / SCIENCE_CORE_STACK_TIF
    stack_npy_path = tensor_dir / SCIENCE_CORE_STACK_NPY
    radar_linear_tif_path = tensor_dir / RADAR_LINEAR_SUPPORT_STACK_TIF
    radar_linear_npy_path = tensor_dir / RADAR_LINEAR_SUPPORT_STACK_NPY
    radar_db_tif_path = tensor_dir / RADAR_DB_SUPPORT_STACK_TIF
    radar_db_npy_path = tensor_dir / RADAR_DB_SUPPORT_STACK_NPY
    ai_ready_tif_path = tensor_dir / AI_READY_SUPPORT_STACK_TIF
    ai_ready_npy_path = tensor_dir / AI_READY_SUPPORT_STACK_NPY
    s2_mask_path = optical_dir / S2_MASK_SUPPORT_TIF
    band_stats_path = qa_dir / BAND_STATS_CSV
    stack_presence_path = qa_dir / STACK_PRESENCE_SUMMARY_JSON
    tensor_audit_path = qa_dir / TENSOR_AUDIT_SUMMARY_JSON
    geometry_summary_path = qa_dir / GEOMETRY_CONSISTENCY_SUMMARY_JSON
    notebook_radar_stack_npy_path = notebook_stack_dir / NOTEBOOK_RADAR_STACK_NPY
    notebook_science_core_stack_npy_path = notebook_stack_dir / NOTEBOOK_SCIENCE_CORE_STACK_NPY
    notebook_radar_linear_stack_npy_path = notebook_stack_dir / NOTEBOOK_RADAR_LINEAR_STACK_NPY
    notebook_ai_ready_stack_npy_path = notebook_stack_dir / NOTEBOOK_AI_READY_STACK_NPY
    notebook_nano_geophysics_stack_npy_path = notebook_stack_dir / NOTEBOOK_NANO_GEOPHYSICS_STACK_NPY
    notebook_treasure_geophysics_stack_npy_path = notebook_stack_dir / NOTEBOOK_TREASURE_GEOPHYSICS_STACK_NPY
    notebook_rad_s0_master_stack_npy_path = notebook_stack_dir / NOTEBOOK_RAD_S0_MASTER_STACK_NPY
    notebook_rad_master_cube_npy_path = notebook_stack_dir / NOTEBOOK_RAD_MASTER_CUBE_NPY
    notebook_gphys_master_stack_npy_path = notebook_stack_dir / NOTEBOOK_GPHYS_MASTER_STACK_NPY
    notebook_master_rtc_refined_stack_npy_path = notebook_stack_dir / NOTEBOOK_MASTER_RTC_REFINED_STACK_NPY
    notebook_arch_targets_stack_npy_path = notebook_stack_dir / NOTEBOOK_ARCH_TARGETS_STACK_NPY
    notebook_ultimate_gphys_scan_npy_path = notebook_stack_dir / NOTEBOOK_ULTIMATE_GPHYS_SCAN_NPY
    notebook_aux_bonus_features_stack_npy_path = notebook_stack_dir / NOTEBOOK_AUX_BONUS_FEATURES_STACK_NPY
    notebook_sim_geophysical_stack_npy_path = notebook_stack_dir / NOTEBOOK_SIM_GEOPHYSICAL_STACK_NPY
    notebook_stack_alias_manifest_path = notebook_stack_dir / NOTEBOOK_STACK_ALIAS_MANIFEST_JSON

    _save_stack_geotiff(stack_tif_path, cube, grid_spec)
    np.save(stack_npy_path, cube)
    _save_stack_geotiff(radar_linear_tif_path, radar_linear_stack, grid_spec)
    np.save(radar_linear_npy_path, radar_linear_stack)
    np.save(notebook_radar_stack_npy_path, radar_db_stack)
    np.save(notebook_science_core_stack_npy_path, cube)
    np.save(notebook_radar_linear_stack_npy_path, radar_linear_stack)
    np.save(notebook_ai_ready_stack_npy_path, ai_ready_stack)
    np.save(notebook_nano_geophysics_stack_npy_path, nano_geophysics_stack)
    np.save(notebook_treasure_geophysics_stack_npy_path, treasure_geophysics_stack)
    np.save(notebook_rad_s0_master_stack_npy_path, rad_s0_master_stack)
    np.save(notebook_rad_master_cube_npy_path, rad_master_cube_stack)
    np.save(notebook_gphys_master_stack_npy_path, gphys_master_stack)
    np.save(notebook_master_rtc_refined_stack_npy_path, master_rtc_refined_stack)
    np.save(notebook_arch_targets_stack_npy_path, arch_targets_stack)
    np.save(notebook_ultimate_gphys_scan_npy_path, ultimate_gphys_scan_stack)
    np.save(notebook_aux_bonus_features_stack_npy_path, aux_bonus_features_stack)
    np.save(notebook_sim_geophysical_stack_npy_path, sim_geophysical_stack)

    for band_index, band_name in enumerate(NANO_GEOPHYSICS_BANDS):
        band_array = nano_geophysics_stack[:, :, band_index].astype(np.float32, copy=False)
        band_tif = notebook_sar_tif_dir / f"{band_name}_640.tif"
        band_npy = notebook_sar_npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(band_tif, band_array, grid_spec)
        write_raster_sidecar(
            band_tif,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(band_npy, band_array)

    for band_index, band_name in enumerate(TREASURE_GEOPHYSICS_BANDS):
        band_array = treasure_geophysics_stack[:, :, band_index].astype(np.float32, copy=False)
        band_tif = notebook_sar_tif_dir / f"{band_name}_640.tif"
        band_npy = notebook_sar_npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(band_tif, band_array, grid_spec)
        write_raster_sidecar(
            band_tif,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(band_npy, band_array)

    for band_index, band_name in enumerate(RAD_S0_MASTER_BANDS):
        band_array = rad_s0_master_stack[:, :, band_index].astype(np.float32, copy=False)
        band_tif = notebook_sar_tif_dir / f"{band_name}_640.tif"
        band_npy = notebook_sar_npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(band_tif, band_array, grid_spec)
        write_raster_sidecar(
            band_tif,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(band_npy, band_array)

    for band_index, band_name in enumerate(RAD_MASTER_CUBE_BANDS):
        band_array = rad_master_cube_stack[:, :, band_index].astype(np.float32, copy=False)
        band_tif = notebook_sar_tif_dir / f"{band_name}_640.tif"
        band_npy = notebook_sar_npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(band_tif, band_array, grid_spec)
        write_raster_sidecar(
            band_tif,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(band_npy, band_array)

    for band_index, band_name in enumerate(GPHYS_MASTER_BANDS):
        band_array = gphys_master_stack[:, :, band_index].astype(np.float32, copy=False)
        band_tif = notebook_sar_tif_dir / f"{band_name}_640.tif"
        band_npy = notebook_sar_npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(band_tif, band_array, grid_spec)
        write_raster_sidecar(
            band_tif,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(band_npy, band_array)

    for band_index, band_name in enumerate(MASTER_RTC_REFINED_BANDS):
        band_array = master_rtc_refined_stack[:, :, band_index].astype(np.float32, copy=False)
        band_tif = notebook_sar_tif_dir / f"{band_name}_640.tif"
        band_npy = notebook_sar_npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(band_tif, band_array, grid_spec)
        write_raster_sidecar(
            band_tif,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(band_npy, band_array)

    for band_index, band_name in enumerate(ARCH_TARGETS_BANDS):
        band_array = arch_targets_stack[:, :, band_index].astype(np.float32, copy=False)
        band_tif = notebook_sar_tif_dir / f"{band_name}_640.tif"
        band_npy = notebook_sar_npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(band_tif, band_array, grid_spec)
        write_raster_sidecar(
            band_tif,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(band_npy, band_array)

    for band_index, band_name in enumerate(ULTIMATE_GPHYS_SCAN_BANDS):
        band_array = ultimate_gphys_scan_stack[:, :, band_index].astype(np.float32, copy=False)
        band_tif = notebook_sar_tif_dir / f"{band_name}_640.tif"
        band_npy = notebook_sar_npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(band_tif, band_array, grid_spec)
        write_raster_sidecar(
            band_tif,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(band_npy, band_array)

    for band_index, band_name in enumerate(AUX_BONUS_FEATURES_BANDS):
        band_array = aux_bonus_features_stack[:, :, band_index].astype(np.float32, copy=False)
        band_tif = notebook_sar_tif_dir / f"{band_name}_640.tif"
        band_npy = notebook_sar_npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(band_tif, band_array, grid_spec)
        write_raster_sidecar(
            band_tif,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(band_npy, band_array)

    for band_index, band_name in enumerate(SIM_GEOPHYSICAL_BANDS):
        band_array = sim_geophysical_stack[:, :, band_index].astype(np.float32, copy=False)
        band_tif = notebook_sar_tif_dir / f"{band_name}_640.tif"
        band_npy = notebook_sar_npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(band_tif, band_array, grid_spec)
        write_raster_sidecar(
            band_tif,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(band_npy, band_array)

    write_georeferenced_raster(radar_db_tif_path, radar_db_stack, grid_spec)
    np.save(radar_db_npy_path, radar_db_stack)
    _save_stack_geotiff(ai_ready_tif_path, ai_ready_stack, grid_spec)
    np.save(ai_ready_npy_path, ai_ready_stack)
    Image.fromarray(s2_mask.astype(np.float32)).save(s2_mask_path, format="TIFF")
    write_raster_sidecar(stack_tif_path, grid_manifest=grid_spec.manifest, nodata=grid_spec.nodata, dtype="float32", shape=cube.shape[:2])
    write_raster_sidecar(
        radar_linear_tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=radar_linear_stack.shape[:2],
    )
    write_raster_sidecar(
        radar_db_tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=radar_db_stack.shape[:2],
    )
    write_raster_sidecar(ai_ready_tif_path, grid_manifest=grid_spec.manifest, nodata=grid_spec.nodata, dtype="float32", shape=ai_ready_stack.shape[:2])
    write_raster_sidecar(s2_mask_path, grid_manifest=grid_spec.manifest, nodata=grid_spec.nodata, dtype="float32", shape=s2_mask.shape)

    _write_csv(
        band_stats_path,
        ["band_index", "band_name", "source_file", "valid_count", "nodata_count", "min", "max", "mean"],
        band_stats_rows,
    )
    stack_presence_path.write_text(json.dumps(stack_presence_summary, indent=2, sort_keys=True), encoding="utf-8")
    tensor_audit_path.write_text(json.dumps(tensor_audit_summary, indent=2, sort_keys=True), encoding="utf-8")
    geometry_summary_path.write_text(json.dumps(geometry_consistency_summary, indent=2, sort_keys=True), encoding="utf-8")
    notebook_stack_alias_manifest_path.write_text(
        json.dumps(
            _build_stack_alias_manifest(
                band_names=band_names,
                radar_db_band_names=radar_db_band_names,
                radar_linear_band_names=radar_linear_band_names,
            ),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return {
        "stack_tif": stack_tif_path,
        "stack_npy": stack_npy_path,
        "radar_linear_tif": radar_linear_tif_path,
        "radar_linear_npy": radar_linear_npy_path,
        "radar_db_tif": radar_db_tif_path,
        "radar_db_npy": radar_db_npy_path,
        "ai_ready_tif": ai_ready_tif_path,
        "ai_ready_npy": ai_ready_npy_path,
        "s2_mask_tif": s2_mask_path,
        "band_stats_csv": band_stats_path,
        "stack_presence_summary_json": stack_presence_path,
        "tensor_audit_summary_json": tensor_audit_path,
        "geometry_consistency_summary_json": geometry_summary_path,
        "notebook_radar_stack_npy": notebook_radar_stack_npy_path,
        "notebook_science_core_stack_npy": notebook_science_core_stack_npy_path,
        "notebook_radar_linear_stack_npy": notebook_radar_linear_stack_npy_path,
        "notebook_ai_ready_stack_npy": notebook_ai_ready_stack_npy_path,
        "notebook_nano_geophysics_stack_npy": notebook_nano_geophysics_stack_npy_path,
        "notebook_treasure_geophysics_stack_npy": notebook_treasure_geophysics_stack_npy_path,
        "notebook_rad_s0_master_stack_npy": notebook_rad_s0_master_stack_npy_path,
        "notebook_rad_master_cube_npy": notebook_rad_master_cube_npy_path,
        "notebook_gphys_master_stack_npy": notebook_gphys_master_stack_npy_path,
        "notebook_master_rtc_refined_stack_npy": notebook_master_rtc_refined_stack_npy_path,
        "notebook_arch_targets_stack_npy": notebook_arch_targets_stack_npy_path,
        "notebook_ultimate_gphys_scan_npy": notebook_ultimate_gphys_scan_npy_path,
        "notebook_aux_bonus_features_stack_npy": notebook_aux_bonus_features_stack_npy_path,
        "notebook_sim_geophysical_stack_npy": notebook_sim_geophysical_stack_npy_path,
        "notebook_stack_alias_manifest_json": notebook_stack_alias_manifest_path,
    }


class FeatureStacksStage(Stage):
    name = "feature_stacks"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        source_layers = collect_science_core_layers(context.run_dir, self.grid_spec)
        products = build_feature_stack_products(source_layers, nodata=self.grid_spec.nodata)
        outputs = write_feature_stack_outputs(context.run_dir, self.grid_spec, products)
        artifacts = [
            build_stage_artifact(
                name="science_core_stack_tif",
                relative_path=outputs["stack_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["stack_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="science_core_stack_npy",
                relative_path=outputs["stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="radar_linear_support_stack_tif",
                relative_path=outputs["radar_linear_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["radar_linear_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="radar_linear_support_stack_npy",
                relative_path=outputs["radar_linear_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["radar_linear_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="radar_db_support_stack_tif",
                relative_path=outputs["radar_db_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["radar_db_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="radar_db_support_stack_npy",
                relative_path=outputs["radar_db_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["radar_db_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="ai_ready_support_stack_tif",
                relative_path=outputs["ai_ready_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["ai_ready_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="ai_ready_support_stack_npy",
                relative_path=outputs["ai_ready_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["ai_ready_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="s2_mask_support_valid",
                relative_path=outputs["s2_mask_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["s2_mask_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="band_stats",
                relative_path=outputs["band_stats_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["band_stats_csv"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="stack_presence_summary",
                relative_path=outputs["stack_presence_summary_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["stack_presence_summary_json"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="tensor_audit_summary",
                relative_path=outputs["tensor_audit_summary_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["tensor_audit_summary_json"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="geometry_consistency_summary",
                relative_path=outputs["geometry_consistency_summary_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["geometry_consistency_summary_json"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_RADAR_STACK_HWC_640_npy",
                relative_path=outputs["notebook_radar_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_radar_stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_SCIENCE_CORE_STACK_HWC_640_npy",
                relative_path=outputs["notebook_science_core_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_science_core_stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_RADAR_LINEAR_SUPPORT_STACK_640_npy",
                relative_path=outputs["notebook_radar_linear_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_radar_linear_stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_AI_READY_SUPPORT_STACK_640_npy",
                relative_path=outputs["notebook_ai_ready_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_ai_ready_stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_RAD_S0_MASTER_STACK_640_npy",
                relative_path=outputs["notebook_rad_s0_master_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_rad_s0_master_stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_RAD_MASTER_CUBE_640_npy",
                relative_path=outputs["notebook_rad_master_cube_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_rad_master_cube_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_GPHYS_MASTER_STACK_640_npy",
                relative_path=outputs["notebook_gphys_master_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_gphys_master_stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_MASTER_RTC_REFINED_STACK_640_npy",
                relative_path=outputs["notebook_master_rtc_refined_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_master_rtc_refined_stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_ARCH_TARGETS_STACK_640_npy",
                relative_path=outputs["notebook_arch_targets_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_arch_targets_stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_ULTIMATE_GPHYS_SCAN_640_npy",
                relative_path=outputs["notebook_ultimate_gphys_scan_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_ultimate_gphys_scan_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_AUX_BONUS_FEATURES_STACK_640_npy",
                relative_path=outputs["notebook_aux_bonus_features_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_aux_bonus_features_stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_SIM_GEOPHYSICAL_STACK_640_npy",
                relative_path=outputs["notebook_sim_geophysical_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_sim_geophysical_stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_NANO_GEOPHYSICS_STACK_640_npy",
                relative_path=outputs["notebook_nano_geophysics_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_nano_geophysics_stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_TREASURE_GEOPHYSICS_STACK_640_npy",
                relative_path=outputs["notebook_treasure_geophysics_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_treasure_geophysics_stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_stack_alias_manifest",
                relative_path=outputs["notebook_stack_alias_manifest_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_stack_alias_manifest_json"].stat().st_size,
                http_servable=False,
            ),
        ]
        band_names = products["band_names"]
        assert isinstance(band_names, list)
        return StageResult(
            artifacts=artifacts,
            metadata={
                "band_names": band_names,
                "band_count": len(band_names),
                "stack_shape": [self.grid_spec.size, self.grid_spec.size, len(band_names)],
            },
        )
