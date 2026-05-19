from __future__ import annotations

import numpy as np

from app.pipeline._base import ParityCategory
from app.pipeline.stages.dem_derivatives import DemDerivativesStage, compute_dem_derivatives


def test_dem_derivatives_parity_matches_notebook_local_gradient_flow() -> None:
    dem = np.array(
        [
            [100.0, 101.0, 102.0, 103.0],
            [100.0, 101.0, 102.0, 103.0],
            [100.0, 101.0, 102.0, 103.0],
            [100.0, 101.0, 102.0, 103.0],
        ],
        dtype=np.float32,
    )

    outputs = compute_dem_derivatives(dem, nodata=-9999.0, scale_m=10.0)

    dz_dy, dz_dx = np.gradient(dem, 10.0, 10.0)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    expected_slope = np.degrees(slope_rad).astype(np.float32)
    expected_aspect = ((np.degrees(np.arctan2(-dz_dx, dz_dy)) + 360.0) % 360.0).astype(np.float32)
    expected_curvature = (np.gradient(dz_dx, 10.0, axis=1) + np.gradient(dz_dy, 10.0, axis=0)).astype(np.float32)

    assert DemDerivativesStage.parity_category is ParityCategory.PARITY_REPRODUCES
    assert np.allclose(outputs["slope"], expected_slope)
    assert np.allclose(outputs["aspect"], expected_aspect)
    assert np.allclose(outputs["curvature"], expected_curvature)
