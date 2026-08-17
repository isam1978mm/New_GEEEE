from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

from app.services.nb_exact_support import (
    ASC_DESC_CONSISTENCY_FILENAME,
    NB_EXACT_SUPPORT_DIR,
    THERMAL_DELTA_FILENAME,
)
from app.services.nb_math import build_proxy_layers, compute_point, norm01
from app.services.nb_spatial_validity import assess_nb_spatial_validity

NB_SCHEMA = "nb_results_v1"
NB_METHOD = "notebook_new_ipynb_proxy_addons_v1"
AIX_MASK_STACK_NAME = "AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640.npy"
STAGE2D_MATRIX_RELATIVE_PATH = Path("NPY_STACKS") / "AI_MASTER_MATRIX_640_STAGE2D_FALSE_SIGNATURE.tif"
STAGE2D_ASC_DESC_BAND = "FS_ASC_DESC_CONSISTENCY_640"
STAGE2D_THERMAL_DELTA_BAND = "THERMAL_DELTA_DAY_NIGHT_PROXY"


def _not_available(reason: str) -> dict[str, Any]:
    return {
        "schema": NB_SCHEMA,
        "status": "not_available",
        "method": NB_METHOD,
        "object_count": 0,
        "reason": reason,
        "unavailable_support": [],
        "limitations": {
            "physical_confirmation": False,
            "metal_confirmation": False,
            "calibrated_numerical_depth": False,
            "fake_three_meter_fallback_used": False,
        },
        "spatial_validity": {
            "mode": "shadow",
            "candidate_suppression": False,
            "interpretation_suppression": False,
            "depth_suppression": False,
            "classifier_modified": False,
        },
        "objects": [],
    }


def _load_tif(path: Path, *, expected_shape: tuple[int, int] | None = None) -> np.ndarray | None:
    if not path.is_file():
        return None
    try:
        with rasterio.open(path) as dataset:
            array = dataset.read(1).astype(np.float32)
            nodata = dataset.nodata
    except (OSError, rasterio.errors.RasterioError):
        return None
    if expected_shape is not None and array.shape != expected_shape:
        return None
    if nodata is not None and np.isfinite(nodata):
        array[array == np.float32(nodata)] = np.nan
    array[~np.isfinite(array)] = np.nan
    return array


def _load_stage2d_exact_support(
    run_dir: Path,
    *,
    shape: tuple[int, int],
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """Load the exact Stage 2D bands consumed by new.ipynb Stage 5.

    The notebook writes both bands into AI_MASTER_MATRIX_640_STAGE2D_FALSE_SIGNATURE.tif
    and Stage 5 selects them by the ``asc_desc`` and ``thermal_delta`` names. Stage 2D
    declares nodata=0.0 even though zero is also a valid normalized value, so this loader
    intentionally preserves finite zeros instead of treating the dataset nodata metadata
    as a missing-data mask.
    """
    path = run_dir / STAGE2D_MATRIX_RELATIVE_PATH
    if not path.is_file():
        return None, None
    try:
        with rasterio.open(path) as dataset:
            if dataset.shape != shape:
                return None, None
            band_indexes = {
                str(description).strip(): index
                for index, description in enumerate(dataset.descriptions, start=1)
                if description not in (None, "", " ")
            }
            asc_index = band_indexes.get(STAGE2D_ASC_DESC_BAND)
            delta_index = band_indexes.get(STAGE2D_THERMAL_DELTA_BAND)
            ascdesc = dataset.read(asc_index).astype(np.float32) if asc_index is not None else None
            thermal_delta = dataset.read(delta_index).astype(np.float32) if delta_index is not None else None
    except (OSError, rasterio.errors.RasterioError):
        return None, None

    for array in (ascdesc, thermal_delta):
        if array is not None:
            array[~np.isfinite(array)] = np.nan
    return ascdesc, thermal_delta


def _load_produced_exact_support(
    run_dir: Path,
    *,
    shape: tuple[int, int],
) -> tuple[np.ndarray | None, np.ndarray | None]:
    support_dir = run_dir / NB_EXACT_SUPPORT_DIR
    ascdesc = _load_tif(support_dir / ASC_DESC_CONSISTENCY_FILENAME, expected_shape=shape)
    thermal_delta = _load_tif(support_dir / THERMAL_DELTA_FILENAME, expected_shape=shape)
    return ascdesc, thermal_delta


def _load_aix_support(run_dir: Path, *, shape: tuple[int, int]) -> tuple[np.ndarray | None, np.ndarray | None]:
    path = run_dir / "NPY_STACKS" / AIX_MASK_STACK_NAME
    if not path.is_file():
        return None, None
    try:
        stack = np.load(path).astype(np.float32)
    except (OSError, ValueError):
        return None, None
    if stack.ndim != 3:
        return None, None
    if stack.shape[:2] == shape and stack.shape[-1] >= 5:
        return stack[:, :, 0], stack[:, :, 4]
    if stack.shape[1:] == shape and stack.shape[0] >= 5:
        return stack[0], stack[4]
    return None, None


def _read_objects(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError:
        return []


def _object_point(row: dict[str, str], shape: tuple[int, int]) -> tuple[int, int] | None:
    try:
        if row.get("row_center") and row.get("col_center"):
            rr = int(round(float(row["row_center"])))
            cc = int(round(float(row["col_center"])))
        else:
            rr = int(round((float(row["row_min"]) + float(row["row_max"])) / 2.0))
            cc = int(round((float(row["col_min"]) + float(row["col_max"])) / 2.0))
    except (KeyError, TypeError, ValueError):
        return None
    return max(0, min(shape[0] - 1, rr)), max(0, min(shape[1] - 1, cc))


def _sample(array: np.ndarray, row: int, col: int) -> float | None:
    value = float(array[row, col])
    return value if np.isfinite(value) else None


def build_nb_results(run_dir: Path) -> dict[str, Any]:
    """Read existing run outputs and build additive NB results. No run file is modified."""
    object_rows = _read_objects(run_dir / "objects_index.csv")
    if not object_rows:
        return _not_available("object_results_unavailable")

    vv_raw = _load_tif(run_dir / "VV_dB.tif")
    vh_raw = _load_tif(run_dir / "VH_dB.tif")
    if vv_raw is None or vh_raw is None or vv_raw.shape != vh_raw.shape:
        return _not_available("radar_support_unavailable")
    shape = vv_raw.shape
    unavailable_support: set[str] = set()

    def support(name: str, relative_path: str) -> tuple[np.ndarray, bool]:
        array = _load_tif(run_dir / relative_path, expected_shape=shape)
        if array is None:
            unavailable_support.add(name)
            return np.zeros(shape, dtype=np.float32), False
        return array, True

    ratio_raw, ratio_ok = support("radar_logratio", "logRatio_dB.tif")
    gold_raw, gold_ok = support("gold_signal", "AI_READY_640/AI_READY_640_Secret_Gold_Halo.tif")
    silver_raw, silver_ok = support("silver_signal", "AI_READY_640/AI_READY_640_Secret_Silver_Oxide.tif")
    tunnel_raw, tunnel_ok = support("tunnel_signal", "AI_READY_640/AI_READY_640_Secret_Tunnel_Ceiling.tif")
    thermal_raw, thermal_ok = support("thermal_inertia", "AI_READY_640/AI_READY_640_Secret_Thermal_Inertia.tif")
    door_raw, door_ok = support("hidden_door_signal", "AI_READY_640/AI_READY_640_Secret_Hidden_Doors.tif")
    mass_raw, mass_ok = support("mass_signal", "REPORT_640_Mass_Report.tif")
    pottery_raw, pottery_ok = support("pottery_signal", "REPORT_640_Pottery_Report.tif")
    tpi_raw, tpi_ok = support("tpi", "TPI.tif")
    rough_raw, rough_ok = support("roughness", "roughness.tif")
    curv_raw, curv_ok = support("curvature", "curvature.tif")
    thermal_day_raw, thermal_day_ok = support("thermal_day", "lst.tif")
    incidence_raw = _load_tif(run_dir / "incidence.tif", expected_shape=shape)

    vegroot_raw, clay_raw = _load_aix_support(run_dir, shape=shape)
    aix_ok = vegroot_raw is not None and clay_raw is not None
    if not aix_ok:
        unavailable_support.add("aix_dem_matched_masks")
        vegroot_raw = np.zeros(shape, dtype=np.float32)
        clay_raw = np.zeros(shape, dtype=np.float32)

    ascdesc_exact, thermal_delta_exact = _load_stage2d_exact_support(run_dir, shape=shape)
    produced_ascdesc, produced_thermal_delta = _load_produced_exact_support(run_dir, shape=shape)
    if ascdesc_exact is None:
        ascdesc_exact = produced_ascdesc
    if thermal_delta_exact is None:
        thermal_delta_exact = produced_thermal_delta

    ascdesc_ok = ascdesc_exact is not None
    thermal_delta_ok = thermal_delta_exact is not None
    if ascdesc_ok:
        ascdesc = ascdesc_exact
    else:
        unavailable_support.add("asc_desc_consistency")
        ascdesc = np.zeros(shape, dtype=np.float32)
    if thermal_delta_ok:
        thermal_delta = thermal_delta_exact
    else:
        unavailable_support.add("thermal_delta")
        thermal_delta = np.zeros(shape, dtype=np.float32)

    normalized = {
        "gold": norm01(gold_raw),
        "silver": norm01(silver_raw),
        "tunnel": norm01(tunnel_raw),
        "thermal": norm01(thermal_raw),
        "door": norm01(door_raw),
        "mass": norm01(mass_raw),
        "pottery": norm01(pottery_raw),
        "tpi": norm01(tpi_raw),
        "rough": norm01(rough_raw),
        "curv": norm01(curv_raw),
    }
    proxies = build_proxy_layers(
        vv=vv_raw,
        vh=vh_raw,
        ratio=ratio_raw,
        gold=gold_raw,
        silver=silver_raw,
        thermal_day=thermal_day_raw,
        thermal_inertia=thermal_raw,
        rough=rough_raw,
        curv=curv_raw,
        tpi=tpi_raw,
        vegroot=vegroot_raw,
        clay_thermal=clay_raw,
        thermal_delta=thermal_delta,
    )

    proxy_ok = {
        "quartz": gold_ok and thermal_day_ok and aix_ok and rough_ok,
        "lime": aix_ok and rough_ok and curv_ok and tpi_ok and thermal_day_ok,
        "moist": aix_ok and thermal_day_ok and ratio_ok,
        "oxid": silver_ok and aix_ok and gold_ok,
        "sar_comp": ratio_ok,
    }
    thermal_risk_ok = thermal_day_ok and thermal_delta_ok and thermal_ok
    proxy_ok["risk"] = all(proxy_ok[name] for name in ("quartz", "lime", "moist", "oxid")) and thermal_risk_ok

    array_ok = {
        "gold": gold_ok,
        "silver": silver_ok,
        "tunnel": tunnel_ok,
        "thermal": thermal_ok,
        "door": door_ok,
        "mass": mass_ok,
        "pottery": pottery_ok,
        "tpi": tpi_ok,
        "rough": rough_ok,
        "curv": curv_ok,
        **proxy_ok,
        "ascdesc": ascdesc_ok,
        "delta": thermal_delta_ok,
    }

    vv_lin = np.power(10.0, vv_raw / 10.0).astype(np.float32)
    vh_lin = np.power(10.0, vh_raw / 10.0).astype(np.float32)
    nano_depth = np.full(shape, np.nan, dtype=np.float32)
    valid = np.isfinite(vv_lin) & np.isfinite(vh_lin)
    nano_depth[valid] = (vv_lin[valid] / (vh_lin[valid] + np.float32(1e-6))).astype(np.float32)

    arrays = {
        **normalized,
        **proxies,
        "ascdesc": ascdesc,
        "delta": thermal_delta,
        "nano_depth_penetration": nano_depth,
    }
    spatial_layers: dict[str, np.ndarray | None] = {
        "vv": vv_raw,
        "vh": vh_raw,
        "logratio": ratio_raw if ratio_ok else None,
        "incidence": incidence_raw,
        "ascdesc": ascdesc if ascdesc_ok else None,
        "thermal_day": thermal_day_raw if thermal_day_ok else None,
        "thermal_inertia": thermal_raw if thermal_ok else None,
        "thermal_delta": thermal_delta if thermal_delta_ok else None,
        "rough": rough_raw if rough_ok else None,
        "tpi": tpi_raw if tpi_ok else None,
        "curv": curv_raw if curv_ok else None,
        "mass": mass_raw if mass_ok else None,
        "pottery": pottery_raw if pottery_ok else None,
    }

    objects: list[dict[str, Any]] = []
    for row in object_rows:
        point = _object_point(row, shape)
        if point is None:
            continue
        try:
            object_id = int(float(row["object_id"]))
        except (KeyError, TypeError, ValueError):
            continue
        rr, cc = point
        values: dict[str, float | None] = {}
        for name, array in arrays.items():
            if name == "nano_depth_penetration" or array_ok.get(name, False):
                values[name] = _sample(array, rr, cc)
        nb_result = compute_point(values)
        spatial_validity = assess_nb_spatial_validity(
            object_row=row,
            shape=shape,
            row=rr,
            col=cc,
            layers=spatial_layers,
        )
        objects.append(
            {
                "object_id": object_id,
                **nb_result,
                "nb_spatial_validity": spatial_validity,
            }
        )

    if not objects:
        return _not_available("object_locations_unavailable")

    return {
        "schema": NB_SCHEMA,
        "status": "partial" if unavailable_support else "available",
        "method": NB_METHOD,
        "object_count": len(objects),
        "reason": None,
        "unavailable_support": sorted(unavailable_support),
        "limitations": {
            "physical_confirmation": False,
            "metal_confirmation": False,
            "calibrated_numerical_depth": False,
            "fake_three_meter_fallback_used": False,
        },
        "spatial_validity": {
            "mode": "shadow",
            "candidate_suppression": False,
            "interpretation_suppression": False,
            "depth_suppression": False,
            "classifier_modified": False,
        },
        "objects": sorted(objects, key=lambda item: int(item["object_id"])),
    }
