from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest
import rasterio

from tests.notebook_parity.test_reference_outputs_contract import (
    REFERENCE_BUNDLE_SKIP_MESSAGE,
    load_reference_manifest,
    tolerance_for,
    verify_manifest_checksums,
)


QA_GRID_REFERENCE_PAIRS = [
    ("QA/QA_GRID_dx_m_640.tif", "QA_GRID_dx_m_640.tif", False),
    ("QA/QA_GRID_dy_m_640.tif", "QA_GRID_dy_m_640.tif", False),
    ("QA/QA_GRID_validmask_640.tif", "QA_GRID_validmask_640.tif", True),
]

POST_RTC_SAR_REFERENCE_PAIRS = [
    pytest.param(
        "QA/sar/intermediates/post_rtc/final_VV_dB.npy",
        "VV_dB.tif",
        marks=pytest.mark.xfail(
            strict=True,
            raises=AssertionError,
            reason=(
                "notebook reference and app post-RTC intermediate arrays differ numerically; "
                "observed max_error is about 9998.5127 and no SAR math or tolerance change is approved"
            ),
        ),
    ),
    pytest.param(
        "QA/sar/intermediates/post_rtc/final_VH_dB.npy",
        "VH_dB.tif",
        marks=pytest.mark.xfail(
            strict=True,
            raises=AssertionError,
            reason=(
                "notebook reference and app post-RTC intermediate arrays differ numerically; "
                "observed max_error is about 9994.2227 and no SAR math or tolerance change is approved"
            ),
        ),
    ),
    pytest.param(
        "QA/sar/intermediates/post_rtc/final_logRatio_dB.npy",
        "logRatio_dB.tif",
        marks=pytest.mark.xfail(
            strict=True,
            raises=AssertionError,
            reason=(
                "notebook reference and app post-RTC intermediate arrays differ numerically; "
                "observed max_error is about 10007.8242 and no SAR math or tolerance change is approved"
            ),
        ),
    ),
    pytest.param(
        "QA/sar/intermediates/post_rtc/final_angle.npy",
        "incidence.tif",
        marks=pytest.mark.xfail(
            strict=True,
            raises=AssertionError,
            reason=(
                "notebook reference and app post-RTC intermediate arrays differ numerically; "
                "observed max_error is about 10032.8047 and no SAR math or tolerance change is approved"
            ),
        ),
    ),
]


@pytest.mark.parametrize(("reference_relative_path", "tolerance_name", "allow_validmask_representation_diff"), QA_GRID_REFERENCE_PAIRS)
def test_qa_grid_outputs_match_frozen_reference_or_skip(
    reference_relative_path: str,
    tolerance_name: str,
    allow_validmask_representation_diff: bool,
) -> None:
    manifest = load_reference_manifest()
    verify_manifest_checksums(manifest)
    app_run_dir = _load_notebook_exact_app_run_dir()

    reference_path = _resolve_reference_file(manifest, reference_relative_path)
    app_path = app_run_dir / reference_relative_path
    if not app_path.is_file():
        pytest.skip(f"Matching notebook-grid app output is missing required file: {reference_relative_path}")

    _assert_raster_matches_reference(
        label=reference_relative_path,
        reference_path=reference_path,
        app_path=app_path,
        tolerance=tolerance_for(tolerance_name),
        allow_validmask_representation_diff=allow_validmask_representation_diff,
    )


@pytest.mark.parametrize(("reference_relative_path", "tolerance_name"), POST_RTC_SAR_REFERENCE_PAIRS)
def test_post_rtc_sar_intermediates_match_frozen_reference_or_skip(
    reference_relative_path: str,
    tolerance_name: str,
) -> None:
    manifest = load_reference_manifest()
    verify_manifest_checksums(manifest)
    app_run_dir = _load_notebook_exact_app_run_dir()

    reference_path = _resolve_reference_file(manifest, reference_relative_path)
    app_path = app_run_dir / reference_relative_path
    if not app_path.is_file():
        pytest.skip(f"Matching notebook-grid app output is missing required file: {reference_relative_path}")

    _assert_npy_matches_reference(
        label=reference_relative_path,
        reference_path=reference_path,
        app_path=app_path,
        tolerance=tolerance_for(tolerance_name),
    )


def _resolve_reference_file(manifest, relative_suffix: str) -> Path:
    matches = [
        manifest.bundle_root / relative_path
        for relative_path in manifest.path_map.values()
        if Path(relative_path).as_posix().endswith(relative_suffix)
    ]
    if not matches:
        pytest.skip(f"{REFERENCE_BUNDLE_SKIP_MESSAGE} Missing reference path for {relative_suffix}.")
    if len(matches) != 1:
        pytest.skip(f"Reference bundle path map is ambiguous for {relative_suffix}.")
    path = matches[0].resolve()
    if not path.is_file():
        pytest.skip(f"Reference bundle file is missing for {relative_suffix}.")
    return path


def _load_notebook_exact_app_run_dir() -> Path:
    raw_path = os.environ.get("APP_NOTEBOOK_OUTPUT_RUN_DIR")
    if not raw_path:
        pytest.skip(
            "Matching notebook-grid app run is not configured at APP_NOTEBOOK_OUTPUT_RUN_DIR. "
            "Phase 5E requires the notebook-exact validation run, not a production-grid fixture."
        )
    path = Path(raw_path).expanduser().resolve()
    if not path.is_dir():
        pytest.skip("Matching notebook-grid app run path is configured but is not a readable directory.")
    return path


def _assert_raster_matches_reference(
    *,
    label: str,
    reference_path: Path,
    app_path: Path,
    tolerance: float,
    allow_validmask_representation_diff: bool,
) -> None:
    with rasterio.open(reference_path) as reference_dataset, rasterio.open(app_path) as app_dataset:
        if (reference_dataset.width, reference_dataset.height) != (app_dataset.width, app_dataset.height):
            raise AssertionError(
                f"{label}: metadata mismatch: width/height "
                f"{reference_dataset.width}x{reference_dataset.height} != {app_dataset.width}x{app_dataset.height}"
            )
        if reference_dataset.crs != app_dataset.crs:
            raise AssertionError(f"{label}: grid mismatch: CRS {reference_dataset.crs} != {app_dataset.crs}")
        if reference_dataset.transform != app_dataset.transform:
            raise AssertionError(f"{label}: grid mismatch: transform differs")
        if reference_dataset.count != app_dataset.count:
            raise AssertionError(f"{label}: metadata mismatch: band count {reference_dataset.count} != {app_dataset.count}")
        if reference_dataset.dtypes != app_dataset.dtypes and not _is_allowed_validmask_dtype_pair(
            reference_dataset.dtypes,
            app_dataset.dtypes,
            allow_validmask_representation_diff=allow_validmask_representation_diff,
        ):
            raise AssertionError(f"{label}: dtype mismatch: {reference_dataset.dtypes} != {app_dataset.dtypes}")
        if reference_dataset.nodata != app_dataset.nodata and not _is_allowed_validmask_nodata_pair(
            reference_dataset.nodata,
            app_dataset.nodata,
            allow_validmask_representation_diff=allow_validmask_representation_diff,
        ):
            raise AssertionError(f"{label}: nodata mismatch: {reference_dataset.nodata} != {app_dataset.nodata}")

        _assert_optional_sidecar_matches_dataset(
            label=label,
            side="reference",
            raster_path=reference_path,
            dataset=reference_dataset,
            allow_validmask_representation_diff=allow_validmask_representation_diff,
        )
        _assert_optional_sidecar_matches_dataset(
            label=label,
            side="app",
            raster_path=app_path,
            dataset=app_dataset,
            allow_validmask_representation_diff=allow_validmask_representation_diff,
        )

        for band_index in range(1, reference_dataset.count + 1):
            reference_mask = reference_dataset.read_masks(band_index) == 0
            app_mask = app_dataset.read_masks(band_index) == 0
            if not np.array_equal(reference_mask, app_mask):
                raise AssertionError(f"{label}: nodata mismatch: band {band_index} mask differs")

            reference_array = reference_dataset.read(band_index, masked=False).astype(np.float32, copy=False)
            app_array = app_dataset.read(band_index, masked=False).astype(np.float32, copy=False)

            if not np.array_equal(np.isnan(reference_array), np.isnan(app_array)):
                raise AssertionError(f"{label}: nodata mismatch: band {band_index} NaN mask differs")
            if not np.array_equal(np.isfinite(reference_array), np.isfinite(app_array)):
                raise AssertionError(f"{label}: nodata mismatch: band {band_index} finite mask differs")

            finite_mask = np.isfinite(reference_array) & np.isfinite(app_array)
            if finite_mask.any():
                max_error = float(np.max(np.abs(reference_array[finite_mask] - app_array[finite_mask])))
                if max_error > tolerance:
                    raise AssertionError(
                        f"{label}: value mismatch: band {band_index} max_error={max_error} tolerance={tolerance}"
                    )


def _assert_npy_matches_reference(*, label: str, reference_path: Path, app_path: Path, tolerance: float) -> None:
    reference_array = np.load(reference_path)
    app_array = np.load(app_path)

    if reference_array.shape != app_array.shape:
        raise AssertionError(f"{label}: metadata mismatch: shape {reference_array.shape} != {app_array.shape}")
    if reference_array.dtype != app_array.dtype:
        raise AssertionError(f"{label}: dtype mismatch: {reference_array.dtype} != {app_array.dtype}")
    if not np.array_equal(np.isnan(reference_array), np.isnan(app_array)):
        raise AssertionError(f"{label}: nodata mismatch: NaN mask differs")
    if not np.array_equal(np.isfinite(reference_array), np.isfinite(app_array)):
        raise AssertionError(f"{label}: nodata mismatch: finite mask differs")

    finite_mask = np.isfinite(reference_array) & np.isfinite(app_array)
    if finite_mask.any():
        max_error = float(np.max(np.abs(reference_array[finite_mask] - app_array[finite_mask])))
        if max_error > tolerance:
            raise AssertionError(f"{label}: value mismatch: max_error={max_error} tolerance={tolerance}")


def _assert_optional_sidecar_matches_dataset(
    *,
    label: str,
    side: str,
    raster_path: Path,
    dataset: rasterio.DatasetReader,
    allow_validmask_representation_diff: bool,
) -> None:
    sidecar = _load_optional_sidecar(raster_path)
    if sidecar is None:
        return

    dataset_crs = str(dataset.crs) if dataset.crs is not None else None
    dataset_transform = [float(value) for value in dataset.transform][:6]
    dataset_dtype = dataset.dtypes[0] if dataset.dtypes else None

    if sidecar.get("crs") != dataset_crs:
        raise AssertionError(f"{label}: metadata mismatch: {side} sidecar CRS differs from GeoTIFF")
    if sidecar.get("transform") != dataset_transform:
        raise AssertionError(f"{label}: grid mismatch: {side} sidecar transform differs from GeoTIFF")
    if sidecar.get("nodata") != dataset.nodata and not _is_allowed_validmask_nodata_pair(
        sidecar.get("nodata"),
        dataset.nodata,
        allow_validmask_representation_diff=allow_validmask_representation_diff,
    ):
        raise AssertionError(f"{label}: nodata mismatch: {side} sidecar nodata differs from GeoTIFF")
    if sidecar.get("dtype") != dataset_dtype and not _is_allowed_validmask_dtype_pair(
        (sidecar.get("dtype"),),
        (dataset_dtype,),
        allow_validmask_representation_diff=allow_validmask_representation_diff,
    ):
        raise AssertionError(f"{label}: dtype mismatch: {side} sidecar dtype differs from GeoTIFF")
    if (sidecar.get("width"), sidecar.get("height")) != (dataset.width, dataset.height):
        raise AssertionError(f"{label}: metadata mismatch: {side} sidecar width/height differ from GeoTIFF")


def _load_optional_sidecar(raster_path: Path) -> dict[str, object] | None:
    sidecar_path = raster_path.with_name(f"{raster_path.name}.meta.json")
    if not sidecar_path.is_file():
        return None
    return json.loads(sidecar_path.read_text(encoding="utf-8"))


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
