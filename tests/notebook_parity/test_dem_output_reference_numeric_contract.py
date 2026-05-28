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


DEM_REFERENCE_PAIRS = [
    ("DEM_GEO8_TIFS/DEM_640.tif", "dem.tif"),
    ("DEM_GEO8_TIFS/slope_deg_640.tif", "slope.tif"),
    ("DEM_GEO8_TIFS/aspect_deg_640.tif", "aspect.tif"),
    ("DEM_GEO8_TIFS/roughness_100m_640.tif", "roughness.tif"),
    ("DEM_GEO8_TIFS/tpi_100m_640.tif", "TPI.tif"),
    pytest.param(
        "DEM_GEO8_TIFS/hillshade_0to1_640.tif",
        "hillshade_0to1_640.tif",
        marks=pytest.mark.xfail(
            strict=True,
            raises=AssertionError,
            reason=(
                "notebook reference and app hillshade now match the corrected azimuth convention, "
                "but a residual float-precision difference of about 1.8e-07 remains under zero tolerance; "
                "no tolerance change is approved"
            ),
        ),
    ),
]


@pytest.mark.parametrize(("reference_relative_path", "tolerance_name"), DEM_REFERENCE_PAIRS)
def test_dem_outputs_match_frozen_reference_or_skip(reference_relative_path: str, tolerance_name: str) -> None:
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

            finite_mask = np.isfinite(reference_array) & np.isfinite(app_array)
            if finite_mask.any():
                max_error = float(np.max(np.abs(reference_array[finite_mask] - app_array[finite_mask])))
                if max_error > tolerance:
                    raise AssertionError(
                        f"{label}: value mismatch: band {band_index} max_error={max_error} tolerance={tolerance}"
                    )


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
