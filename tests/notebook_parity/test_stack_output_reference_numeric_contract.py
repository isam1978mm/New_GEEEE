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


STACK_REFERENCE_CASES = [
    pytest.param(
        "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif",
        "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif",
        "hypercube.tif",
        "raster",
    ),
    pytest.param(
        "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy",
        "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy",
        "hypercube.npy",
        "npy",
    ),
    pytest.param(
        "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif",
        "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif",
        "hypercube.tif",
        "raster",
    ),
    pytest.param(
        "NPY_STACKS/RADAR_STACK_HWC_640_",
        "NPY_STACKS/RADAR_STACK_HWC_640_app.npy",
        "RADAR_STACK_HWC_640_app.npy",
        "npy_prefix",
        marks=pytest.mark.xfail(
            strict=True,
            raises=AssertionError,
            reason=(
                "RADAR_STACK_HWC_640_app.npy is an exact alias of app radar_db_support_stack.npy and the "
                "frozen radar stack is an exact assembly of frozen NPY_RADAR_BANDS, but the frozen and app "
                "SAR dB band families still differ by a small residual; observed max_error is about "
                "6.67572021484375e-06 and no tolerance or SAR math change is approved"
            ),
        ),
    ),
]


@pytest.mark.parametrize(("reference_locator", "app_relative_path", "tolerance_name", "mode"), STACK_REFERENCE_CASES)
def test_stack_outputs_match_frozen_reference_or_skip(
    reference_locator: str,
    app_relative_path: str,
    tolerance_name: str,
    mode: str,
) -> None:
    manifest = load_reference_manifest()
    verify_manifest_checksums(manifest)
    app_run_dir = _load_notebook_exact_app_run_dir()

    if mode == "npy_prefix":
        reference_path = _resolve_reference_file_by_prefix(manifest, reference_locator, ".npy")
    else:
        reference_path = _resolve_reference_file(manifest, reference_locator)

    app_path = app_run_dir / app_relative_path
    _skip_if_stage_manifest_marks_not_implemented(app_run_dir=app_run_dir, app_relative_path=app_relative_path)
    if not app_path.is_file():
        pytest.skip(f"Matching notebook-grid app output is missing required file: {app_relative_path}")

    if mode == "raster":
        _assert_raster_matches_reference(
            label=app_relative_path,
            reference_path=reference_path,
            app_path=app_path,
            tolerance=tolerance_for(tolerance_name),
        )
    else:
        _assert_npy_matches_reference(
            label=app_relative_path,
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


def _resolve_reference_file_by_prefix(manifest, relative_prefix: str, extension: str) -> Path:
    matches = [
        manifest.bundle_root / relative_path
        for relative_path in manifest.path_map.values()
        if Path(relative_path).as_posix().startswith(relative_prefix) and Path(relative_path).suffix == extension
    ]
    if not matches:
        pytest.skip(f"{REFERENCE_BUNDLE_SKIP_MESSAGE} Missing reference path for {relative_prefix}*{extension}.")
    if len(matches) != 1:
        pytest.skip(f"Reference bundle path map is ambiguous for {relative_prefix}*{extension}.")
    path = matches[0].resolve()
    if not path.is_file():
        pytest.skip(f"Reference bundle file is missing for {relative_prefix}*{extension}.")
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


def _skip_if_stage_manifest_marks_not_implemented(*, app_run_dir: Path, app_relative_path: str) -> None:
    if not app_relative_path.startswith("NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE"):
        return
    if (app_run_dir / app_relative_path).is_file():
        return
    manifest_path = app_run_dir / "stage_hypercube.manifest.json"
    if not manifest_path.is_file():
        return
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        return
    statuses = metadata.get("notebook_output_statuses")
    if not isinstance(statuses, list):
        return
    target_name = Path(app_relative_path).name
    for item in statuses:
        if not isinstance(item, dict):
            continue
        if item.get("filename") == target_name and item.get("status") == "not_implemented_no_source_equivalent":
            pytest.skip(f"Notebook output family is not implemented for app parity: {target_name}")


def _assert_raster_matches_reference(*, label: str, reference_path: Path, app_path: Path, tolerance: float) -> None:
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
        if reference_dataset.dtypes != app_dataset.dtypes:
            raise AssertionError(f"{label}: dtype mismatch: {reference_dataset.dtypes} != {app_dataset.dtypes}")
        if reference_dataset.nodata != app_dataset.nodata:
            raise AssertionError(f"{label}: nodata mismatch: {reference_dataset.nodata} != {app_dataset.nodata}")

        _assert_optional_sidecar_matches_dataset(label=label, side="reference", raster_path=reference_path, dataset=reference_dataset)
        _assert_optional_sidecar_matches_dataset(label=label, side="app", raster_path=app_path, dataset=app_dataset)

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


def _assert_optional_sidecar_matches_dataset(*, label: str, side: str, raster_path: Path, dataset: rasterio.DatasetReader) -> None:
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
    if sidecar.get("nodata") != dataset.nodata:
        raise AssertionError(f"{label}: nodata mismatch: {side} sidecar nodata differs from GeoTIFF")
    if sidecar.get("dtype") != dataset_dtype:
        raise AssertionError(f"{label}: dtype mismatch: {side} sidecar dtype differs from GeoTIFF")
    if (sidecar.get("width"), sidecar.get("height")) != (dataset.width, dataset.height):
        raise AssertionError(f"{label}: metadata mismatch: {side} sidecar width/height differ from GeoTIFF")


def _load_optional_sidecar(raster_path: Path) -> dict[str, object] | None:
    sidecar_path = raster_path.with_name(f"{raster_path.name}.meta.json")
    if not sidecar_path.is_file():
        return None
    return json.loads(sidecar_path.read_text(encoding="utf-8"))
