from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest
import rasterio

from app.pipeline._base import StageContext
from app.pipeline.stages.dem import DemStage, deterministic_dem_tile
from app.pipeline.stages.dem_derivatives import DemDerivativesStage
from app.pipeline.stages.grid import build_run_grid
from tests.notebook_parity.test_reference_outputs_contract import (
    REFERENCE_BUNDLE_SKIP_MESSAGE,
    load_reference_manifest,
    load_sidecar,
    tolerance_for,
    verify_manifest_checksums,
)


def test_dem_outputs_match_frozen_reference_or_skip() -> None:
    manifest = load_reference_manifest()
    verify_manifest_checksums(manifest)

    with TemporaryDirectory() as temp_dir:
        app_run_dir = Path(temp_dir)
        _build_canonical_dem_app_fixture(app_run_dir)

        pairs = [
            ("DEM_GEO8_TIFS/DEM_640.tif", "dem.tif"),
            ("DEM_GEO8_TIFS/slope_deg_640.tif", "slope.tif"),
            ("DEM_GEO8_TIFS/aspect_deg_640.tif", "aspect.tif"),
            ("DEM_GEO8_TIFS/roughness_100m_640.tif", "roughness.tif"),
            ("DEM_GEO8_TIFS/tpi_100m_640.tif", "TPI.tif"),
            ("DEM_GEO8_TIFS/hillshade_0to1_640.tif", "hillshade_0to1_640.tif"),
        ]

        for reference_relative_path, tolerance_name in pairs:
            reference_path = _resolve_reference_file(manifest, reference_relative_path)
            app_path = app_run_dir / reference_relative_path
            assert app_path.is_file(), f"{reference_relative_path}: metadata mismatch: app output missing"
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


def _assert_raster_matches_reference(*, label: str, reference_path: Path, app_path: Path, tolerance: float) -> None:
    reference_sidecar = load_sidecar(reference_path)
    app_sidecar = load_sidecar(app_path)

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

        if reference_sidecar["crs"] != app_sidecar["crs"]:
            raise AssertionError(f"{label}: grid mismatch: sidecar CRS differs")
        if reference_sidecar["transform"] != app_sidecar["transform"]:
            raise AssertionError(f"{label}: grid mismatch: sidecar transform differs")
        if reference_sidecar["nodata"] != app_sidecar["nodata"]:
            raise AssertionError(f"{label}: nodata mismatch: sidecar nodata differs")
        if reference_sidecar["dtype"] != app_sidecar["dtype"]:
            raise AssertionError(f"{label}: dtype mismatch: sidecar dtype differs")
        if (reference_sidecar["width"], reference_sidecar["height"]) != (app_sidecar["width"], app_sidecar["height"]):
            raise AssertionError(f"{label}: metadata mismatch: sidecar width/height differ")

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


def _build_canonical_dem_app_fixture(run_dir: Path) -> None:
    settings = _settings(run_dir)
    grid_spec = build_run_grid(35.59499, 36.12694)
    context = StageContext(run_id="run-1", settings=settings, run_dir=run_dir)

    asyncio.run(DemStage(grid_spec=grid_spec, tile_fetcher=deterministic_dem_tile).run(context))
    asyncio.run(DemDerivativesStage(grid_spec=grid_spec).run(context))


def _settings(run_dir: Path):
    from app.config import Settings

    data_dir = run_dir / "data"
    return Settings(data_dir=data_dir, database_path=data_dir / "db.sqlite")
