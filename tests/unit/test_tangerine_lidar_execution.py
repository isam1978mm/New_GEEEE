from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from scripts import tangerine_lidar_execution as tangerine


def test_frozen_projects_and_gates() -> None:
    assert tangerine.PRE_PROJECT == "USGS_LPC_AZ_Eastern_PimaCO_2015_LAS_2017"
    assert tangerine.POST_PROJECT == "AZ_PimaCo_2_2021"
    assert tangerine.NOMINAL_COVER_M == pytest.approx(0.9144)
    assert tangerine.FROZEN_GATES == {
        "stable_rmse_m_max": 0.15,
        "stable_abs_median_m_max": 0.05,
        "stable_p95_abs_m_max": 0.30,
        "plane_drift_m_max": 0.10,
    }


def test_pipeline_is_ground_only_and_same_grid_ready(tmp_path: Path) -> None:
    bounds = (741000.0, 3589000.0, 744000.0, 3592000.0)
    pipeline = tangerine.build_dtm_pipeline(
        ept_url=tangerine.POST_EPT_URL,
        output_tif=tmp_path / "post.tif",
        analysis_bounds_utm=bounds,
        resolution_m=1.0,
    )
    stages = pipeline["pipeline"]
    assert stages[0]["type"] == "readers.ept"
    assert stages[0]["filename"].endswith("/AZ_PimaCo_2_2021/ept.json")
    assert stages[1] == {"type": "filters.range", "limits": "Classification[2:2]"}
    assert stages[2] == {"type": "filters.reprojection", "out_srs": "EPSG:32612"}
    assert stages[3]["type"] == "writers.gdal"
    assert stages[3]["resolution"] == 1.0
    assert stages[3]["output_type"] == "idw"
    assert stages[3]["bounds"] == "([741000.000, 744000.000], [3589000.000, 3592000.000])"


def test_binary_morphology_is_conservative() -> None:
    mask = np.zeros((9, 9), dtype=bool)
    mask[4, 4] = True
    assert tangerine.binary_dilate(mask, 1).sum() == 9
    block = np.zeros((9, 9), dtype=bool)
    block[2:7, 2:7] = True
    eroded = tangerine.binary_erode(block, 1)
    assert eroded.sum() == 9


def test_shift_search_recovers_known_subpixel_shift() -> None:
    rows, cols = 160, 160
    y, x = np.indices((rows, cols), dtype=float)
    pre = 0.01 * x + 0.02 * y + 2.0 * np.sin(x / 13.0) + np.cos(y / 11.0)
    post = tangerine._bilinear_shift(pre, -1.5, 0.75) + 0.2 + 0.0005 * x
    stable = np.ones_like(pre, dtype=bool)
    stable[:5, :] = False
    stable[-5:, :] = False
    stable[:, :5] = False
    stable[:, -5:] = False
    dx, dy = tangerine._best_shift(pre, post, stable)
    assert dx == pytest.approx(1.5, abs=0.25)
    assert dy == pytest.approx(-0.75, abs=0.25)
