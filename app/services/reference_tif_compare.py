from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import rasterio


@dataclass(frozen=True, slots=True)
class ReferenceTifComparison:
    label: str
    metadata_match: bool
    values_match: bool
    masks_match: bool
    shape_match: bool
    crs_match: bool
    transform_match: bool
    dtype_match: bool
    nodata_match: bool
    max_abs_error: float | None
    mean_abs_error: float | None
    finite_pixel_count: int

    @property
    def pass_(self) -> bool:
        return self.metadata_match and self.values_match and self.masks_match

    def to_safe_dict(self) -> dict[str, Any]:
        """Return a redaction-safe comparison summary.

        This intentionally omits raw paths, coordinates, CRS values, transforms,
        bounds, arrays, hashes, and per-pixel details. It is suitable for local
        QA logs or private reports that still need to avoid sensitive payloads.
        """

        return {
            "label": self.label,
            "pass": self.pass_,
            "metadata_match": self.metadata_match,
            "values_match": self.values_match,
            "masks_match": self.masks_match,
            "shape_match": self.shape_match,
            "crs_match": self.crs_match,
            "transform_match": self.transform_match,
            "dtype_match": self.dtype_match,
            "nodata_match": self.nodata_match,
            "max_abs_error": self.max_abs_error,
            "mean_abs_error": self.mean_abs_error,
            "finite_pixel_count": self.finite_pixel_count,
        }


def compare_reference_tif(
    *,
    label: str,
    reference_path: Path,
    app_path: Path,
    tolerance: float,
    allow_validmask_representation_diff: bool = False,
) -> ReferenceTifComparison:
    with rasterio.open(reference_path) as reference_dataset, rasterio.open(app_path) as app_dataset:
        shape_match = (reference_dataset.width, reference_dataset.height, reference_dataset.count) == (
            app_dataset.width,
            app_dataset.height,
            app_dataset.count,
        )
        crs_match = reference_dataset.crs == app_dataset.crs
        transform_match = reference_dataset.transform == app_dataset.transform
        dtype_match = reference_dataset.dtypes == app_dataset.dtypes or _is_allowed_validmask_dtype_pair(
            reference_dataset.dtypes,
            app_dataset.dtypes,
            allow_validmask_representation_diff=allow_validmask_representation_diff,
        )
        nodata_match = reference_dataset.nodata == app_dataset.nodata or _is_allowed_validmask_nodata_pair(
            reference_dataset.nodata,
            app_dataset.nodata,
            allow_validmask_representation_diff=allow_validmask_representation_diff,
        )
        metadata_match = shape_match and crs_match and transform_match and dtype_match and nodata_match

        masks_match = True
        values_match = metadata_match
        max_abs_error: float | None = None
        mean_abs_error: float | None = None
        finite_pixel_count = 0

        if shape_match:
            absolute_errors: list[np.ndarray] = []
            for band_index in range(1, reference_dataset.count + 1):
                reference_mask = reference_dataset.read_masks(band_index) == 0
                app_mask = app_dataset.read_masks(band_index) == 0
                if not np.array_equal(reference_mask, app_mask):
                    masks_match = False

                reference_array = reference_dataset.read(band_index, masked=False).astype(np.float32, copy=False)
                app_array = app_dataset.read(band_index, masked=False).astype(np.float32, copy=False)
                if not np.array_equal(np.isnan(reference_array), np.isnan(app_array)):
                    masks_match = False
                if not np.array_equal(np.isfinite(reference_array), np.isfinite(app_array)):
                    masks_match = False

                finite_mask = np.isfinite(reference_array) & np.isfinite(app_array)
                if finite_mask.any():
                    error = np.abs(reference_array[finite_mask] - app_array[finite_mask])
                    absolute_errors.append(error)
                    finite_pixel_count += int(error.size)

            if absolute_errors:
                all_errors = np.concatenate(absolute_errors)
                max_abs_error = float(np.max(all_errors))
                mean_abs_error = float(np.mean(all_errors))
                values_match = bool(max_abs_error <= float(tolerance))
            else:
                max_abs_error = 0.0
                mean_abs_error = 0.0
                values_match = True

    return ReferenceTifComparison(
        label=label,
        metadata_match=metadata_match,
        values_match=values_match,
        masks_match=masks_match,
        shape_match=shape_match,
        crs_match=crs_match,
        transform_match=transform_match,
        dtype_match=dtype_match,
        nodata_match=nodata_match,
        max_abs_error=max_abs_error,
        mean_abs_error=mean_abs_error,
        finite_pixel_count=finite_pixel_count,
    )


def _is_allowed_validmask_dtype_pair(
    left_dtypes: tuple[object, ...],
    right_dtypes: tuple[object, ...],
    *,
    allow_validmask_representation_diff: bool,
) -> bool:
    if not allow_validmask_representation_diff:
        return False
    return tuple(str(value) for value in left_dtypes) == ("uint8",) and tuple(str(value) for value in right_dtypes) == ("float32",)


def _is_allowed_validmask_nodata_pair(
    left_nodata: object,
    right_nodata: object,
    *,
    allow_validmask_representation_diff: bool,
) -> bool:
    if not allow_validmask_representation_diff:
        return False
    return left_nodata == 0.0 and right_nodata == -9999.0
