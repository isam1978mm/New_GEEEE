from __future__ import annotations

import sys
from unittest.mock import MagicMock

import numpy as np

# Mock rasterio and ee before importing dem_derivatives
sys.modules["rasterio"] = MagicMock()
sys.modules["rasterio.transform"] = MagicMock()
sys.modules["ee"] = MagicMock()

from app.pipeline.stages.dem_derivatives import (
    NOTEBOOK_CURVATURE_NAMES,
    OUTPUT_NAMES,
    compute_dem_derivatives,
    compute_hillshade,
)


def test_curvature_variants_match_notebook_formulas() -> None:
    """Verify curvature variant outputs against the recovered notebook formulas."""
    dem = np.array(
        [
            [100.0, 100.0, 100.0],
            [100.0, 110.0, 100.0],
            [100.0, 100.0, 100.0],
        ],
        dtype=np.float32,
    )
    scale_m = 10.0
    outputs = compute_dem_derivatives(dem, nodata=-9999.0, scale_m=scale_m)

    # Laplacian = d2z_dxx + d2z_dyy
    assert np.isclose(outputs["curv_laplacian"][1, 1], outputs["curvature"][1, 1])

    # Recompute derivatives to verify plan/profile formulas
    dz_dy, dz_dx = np.gradient(dem.astype(np.float32), scale_m, scale_m)
    d2z_dxx = np.gradient(dz_dx, scale_m, axis=1)
    d2z_dyy = np.gradient(dz_dy, scale_m, axis=0)
    d2z_dxy = np.gradient(dz_dx, scale_m, axis=0)
    p, q = dz_dx, dz_dy
    r, s, t = d2z_dxx, d2z_dxy, d2z_dyy
    den = p * p + q * q + 1.0
    den_sqrt = np.sqrt(den)
    den_3_2 = den * den_sqrt
    expected_profile = -(r * p * p + 2.0 * s * p * q + t * q * q) / (den_3_2 + 1e-12)
    expected_plan = (r * q * q - 2.0 * s * p * q + t * p * p) / ((p * p + q * q + 1e-12) * (den_sqrt + 1e-12))

    assert np.isclose(outputs["curv_profile"][1, 1], expected_profile[1, 1], atol=1e-6)
    assert np.isclose(outputs["curv_plan"][1, 1], expected_plan[1, 1], atol=1e-6)


def test_curvature_variants_shape_dtype_and_nodata() -> None:
    dem = np.full((7, 7), 50.0, dtype=np.float32)
    dem[3, 3] = -9999.0

    outputs = compute_dem_derivatives(dem, nodata=-9999.0, scale_m=5.0)

    for name in NOTEBOOK_CURVATURE_NAMES:
        arr = outputs[name]
        assert arr.shape == (7, 7)
        assert arr.dtype == np.float32
        assert arr[3, 3] == -9999.0


def test_curvature_variants_flat_dem_produces_finite_zero() -> None:
    """Flat DEM should produce zero or near-zero curvature values."""
    dem = np.full((5, 5), 100.0, dtype=np.float32)
    outputs = compute_dem_derivatives(dem, nodata=-9999.0, scale_m=10.0)

    for name in NOTEBOOK_CURVATURE_NAMES:
        arr = outputs[name]
        valid = arr != -9999.0
        assert np.all(np.isfinite(arr[valid])), f"{name} contains non-finite values"
        assert np.allclose(arr[valid], 0.0, atol=1e-6), f"{name} should be near-zero for flat DEM"


def test_curvature_variants_sloped_plane_produces_stable_finite() -> None:
    """Sloped plane should produce stable finite curvature values."""
    dem = np.array(
        [
            [100.0, 110.0, 120.0],
            [100.0, 110.0, 120.0],
            [100.0, 110.0, 120.0],
        ],
        dtype=np.float32,
    )
    outputs = compute_dem_derivatives(dem, nodata=-9999.0, scale_m=10.0)

    for name in NOTEBOOK_CURVATURE_NAMES:
        arr = outputs[name]
        valid = arr != -9999.0
        assert np.all(np.isfinite(arr[valid])), f"{name} contains non-finite values on sloped plane"


def test_curvature_variants_no_non_finite_outside_nodata() -> None:
    """No non-finite values should remain outside nodata pixels."""
    dem = np.random.default_rng(42).random((10, 10)).astype(np.float32) * 100.0
    outputs = compute_dem_derivatives(dem, nodata=-9999.0, scale_m=10.0)

    for name in NOTEBOOK_CURVATURE_NAMES:
        arr = outputs[name]
        valid = arr != -9999.0
        assert np.all(np.isfinite(arr[valid])), f"{name} contains NaN/Inf outside nodata"


def test_compute_dem_derivatives_matches_notebook_slope_and_aspect() -> None:
    dem = np.array(
        [
            [100.0, 110.0, 120.0],
            [100.0, 110.0, 120.0],
            [100.0, 110.0, 120.0],
        ],
        dtype=np.float32,
    )

    outputs = compute_dem_derivatives(dem, nodata=-9999.0, scale_m=10.0)

    expected_slope = np.degrees(np.arctan(1.0))
    assert outputs["slope"][1, 1] == expected_slope
    assert outputs["aspect"][1, 1] == 270.0
    assert outputs["curvature"][1, 1] == 0.0


def test_compute_dem_derivatives_propagates_nodata() -> None:
    dem = np.full((5, 5), 100.0, dtype=np.float32)
    dem[2, 2] = -9999.0

    outputs = compute_dem_derivatives(dem, nodata=-9999.0, scale_m=10.0)

    for name in OUTPUT_NAMES:
        assert outputs[name][2, 2] == -9999.0

    for name in NOTEBOOK_CURVATURE_NAMES:
        assert outputs[name][2, 2] == -9999.0


def test_compute_hillshade_matches_notebook_azimuth_convention() -> None:
    dem = np.array(
        [
            [100.0, 110.0, 120.0],
            [100.0, 110.0, 120.0],
            [100.0, 110.0, 120.0],
        ],
        dtype=np.float32,
    )

    hillshade = compute_hillshade(dem, nodata=-9999.0, scale_m=10.0)

    expected_center = (
        np.sin(np.deg2rad(45.0)) * np.cos(np.arctan(1.0))
        + np.cos(np.deg2rad(45.0)) * np.sin(np.arctan(1.0)) * np.cos(np.deg2rad(45.0) - np.deg2rad(270.0))
    )
    assert np.isclose(hillshade[1, 1], expected_center, atol=1e-6)
