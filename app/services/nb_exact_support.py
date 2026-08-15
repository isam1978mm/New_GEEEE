from __future__ import annotations

from pathlib import Path

import numpy as np

from app.pipeline.stages.dem import write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec

NB_EXACT_SUPPORT_DIR = "NB_EXACT_SUPPORT"
ASC_DESC_CONSISTENCY_FILENAME = "FS_ASC_DESC_CONSISTENCY_640.tif"
THERMAL_DELTA_FILENAME = "THERMAL_DELTA_DAY_NIGHT_PROXY_640.tif"
MIN_ROBUST_NORM_VALID_PIXELS = 10


class ExactNotebookSupportUnavailable(ValueError):
    """Raised when an exact notebook support layer cannot be computed safely."""


def _valid_mask(array: np.ndarray, *, nodata: float | None) -> np.ndarray:
    mask = np.isfinite(array)
    if nodata is not None and np.isfinite(nodata):
        mask &= array != np.float32(nodata)
    return mask


def notebook_robust_norm01(array: np.ndarray, *, nodata: float | None) -> np.ndarray:
    """Reproduce the notebook Stage 2B/2C/2D robust_norm01 helper."""
    values = np.asarray(array, dtype=np.float32).copy()
    valid = _valid_mask(values, nodata=nodata)
    values[~valid] = np.nan
    if int(valid.sum()) < MIN_ROBUST_NORM_VALID_PIXELS:
        return np.zeros_like(values, dtype=np.float32)

    low, high = np.nanpercentile(values[valid], [2.0, 98.0])
    if abs(float(high) - float(low)) < 1e-6:
        return np.zeros_like(values, dtype=np.float32)

    output = (values - np.float32(low)) / np.float32(high - low)
    output = np.clip(output, 0.0, 1.0)
    output[~np.isfinite(output)] = 0.0
    return output.astype(np.float32)


def compute_asc_desc_consistency(
    *,
    asc_vv: np.ndarray,
    asc_vh: np.ndarray,
    desc_vv: np.ndarray,
    desc_vh: np.ndarray,
    nodata: float | None,
) -> np.ndarray:
    """Reproduce Stage 2B normalization plus Stage 2D ASC/DESC consistency."""
    arrays = [np.asarray(value, dtype=np.float32) for value in (asc_vv, asc_vh, desc_vv, desc_vh)]
    shape = arrays[0].shape
    if any(array.shape != shape for array in arrays[1:]):
        raise ExactNotebookSupportUnavailable("asc_desc_shape_mismatch")

    # Stage 2B normalizes every available source layer before it is put in the
    # AI master matrix. Stage 2D then normalizes the ASC/DESC energies again.
    asc_vv_n = notebook_robust_norm01(arrays[0], nodata=nodata)
    asc_vh_n = notebook_robust_norm01(arrays[1], nodata=nodata)
    desc_vv_n = notebook_robust_norm01(arrays[2], nodata=nodata)
    desc_vh_n = notebook_robust_norm01(arrays[3], nodata=nodata)

    asc_energy = notebook_robust_norm01(
        np.float32(0.5) * asc_vv_n + np.float32(0.5) * asc_vh_n,
        nodata=None,
    )
    desc_energy = notebook_robust_norm01(
        np.float32(0.5) * desc_vv_n + np.float32(0.5) * desc_vh_n,
        nodata=None,
    )
    asc_desc_diff = notebook_robust_norm01(np.abs(asc_energy - desc_energy), nodata=None)
    return np.clip(np.float32(1.0) - asc_desc_diff, 0.0, 1.0).astype(np.float32)


def compute_thermal_delta_normalized(
    *,
    lst_day_k: np.ndarray,
    lst_night_k: np.ndarray,
    nodata: float | None,
) -> np.ndarray:
    """Reproduce the normalized Stage 2C thermal_delta consumed by Stage 5."""
    day = np.asarray(lst_day_k, dtype=np.float32)
    night = np.asarray(lst_night_k, dtype=np.float32)
    if day.shape != night.shape:
        raise ExactNotebookSupportUnavailable("thermal_shape_mismatch")

    valid = _valid_mask(day, nodata=nodata) & _valid_mask(night, nodata=nodata)
    raw_delta = np.full(day.shape, np.nan, dtype=np.float32)
    raw_delta[valid] = (day[valid] - night[valid]).astype(np.float32)
    return notebook_robust_norm01(raw_delta, nodata=None)


def write_exact_support_raster(
    run_dir: Path,
    *,
    grid_spec: GridSpec,
    filename: str,
    array: np.ndarray,
) -> Path:
    expected_shape = (grid_spec.size, grid_spec.size)
    if array.shape != expected_shape:
        raise ExactNotebookSupportUnavailable("support_shape_mismatch")
    if not np.isfinite(array).all():
        raise ExactNotebookSupportUnavailable("support_contains_nonfinite_values")

    output_dir = run_dir / NB_EXACT_SUPPORT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    write_georeferenced_raster(path, array.astype(np.float32, copy=False), grid_spec)
    write_raster_sidecar(
        path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=array.shape,
    )
    return path
