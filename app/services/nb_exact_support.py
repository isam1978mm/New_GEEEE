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
    """Reproduce the notebook Stage 2C/2D 2nd/98th-percentile normalization.

    Invalid pixels are zero-filled after normalization, matching the notebook's
    normalized matrix behavior. At least ten valid pixels are required so an
    optional support producer cannot manufacture a layer from insufficient data.
    """
    values = np.asarray(array, dtype=np.float32)
    valid = _valid_mask(values, nodata=nodata)
    finite_values = values[valid]
    if finite_values.size < MIN_ROBUST_NORM_VALID_PIXELS:
        raise ExactNotebookSupportUnavailable("insufficient_valid_pixels")

    low, high = np.percentile(finite_values.astype(np.float64), [2.0, 98.0])
    output = np.zeros(values.shape, dtype=np.float32)
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        return output

    output[valid] = np.clip(
        (values[valid].astype(np.float64) - low) / (high - low),
        0.0,
        1.0,
    ).astype(np.float32)
    return output


def compute_asc_desc_consistency(
    *,
    asc_vv: np.ndarray,
    asc_vh: np.ndarray,
    desc_vv: np.ndarray,
    desc_vh: np.ndarray,
    nodata: float | None,
) -> np.ndarray:
    """Reproduce new.ipynb Stage 2D FS_ASC_DESC_CONSISTENCY_640."""
    arrays = [np.asarray(value, dtype=np.float32) for value in (asc_vv, asc_vh, desc_vv, desc_vh)]
    shape = arrays[0].shape
    if any(array.shape != shape for array in arrays[1:]):
        raise ExactNotebookSupportUnavailable("asc_desc_shape_mismatch")

    prepared: list[np.ndarray] = []
    for array in arrays:
        valid = _valid_mask(array, nodata=nodata)
        copy = array.astype(np.float32, copy=True)
        copy[~valid] = np.nan
        prepared.append(copy)

    asc_energy_raw = np.float32(0.5) * prepared[0] + np.float32(0.5) * prepared[1]
    desc_energy_raw = np.float32(0.5) * prepared[2] + np.float32(0.5) * prepared[3]
    asc_energy = notebook_robust_norm01(asc_energy_raw, nodata=None)
    desc_energy = notebook_robust_norm01(desc_energy_raw, nodata=None)
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
