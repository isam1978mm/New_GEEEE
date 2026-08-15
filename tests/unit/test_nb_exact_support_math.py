from __future__ import annotations

import numpy as np

from app.services.nb_exact_support import compute_asc_desc_consistency, notebook_robust_norm01


def _notebook_norm01(array: np.ndarray) -> np.ndarray:
    values = array.astype(np.float32).copy()
    values[~np.isfinite(values)] = np.nan
    valid = np.isfinite(values)
    if int(valid.sum()) < 10:
        return np.zeros_like(values, dtype=np.float32)
    p2, p98 = np.nanpercentile(values[valid], [2, 98])
    if abs(float(p98) - float(p2)) < 1e-6:
        return np.zeros_like(values, dtype=np.float32)
    output = (values - p2) / (p98 - p2)
    output = np.clip(output, 0, 1)
    output[~np.isfinite(output)] = 0
    return output.astype(np.float32)


def test_robust_norm_matches_new_ipynb_helper() -> None:
    array = np.arange(144, dtype=np.float32).reshape(12, 12)
    array[0, 0] = np.nan

    actual = notebook_robust_norm01(array, nodata=None)
    expected = _notebook_norm01(array)

    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-6)


def test_robust_norm_returns_zero_when_notebook_has_fewer_than_ten_valid_pixels() -> None:
    array = np.full((4, 4), np.nan, dtype=np.float32)
    array.flat[:9] = np.arange(9, dtype=np.float32)

    actual = notebook_robust_norm01(array, nodata=None)

    np.testing.assert_array_equal(actual, np.zeros((4, 4), dtype=np.float32))


def test_asc_desc_consistency_matches_stage2b_then_stage2d_formula() -> None:
    rows, cols = np.indices((12, 12), dtype=np.float32)
    asc_vv = -12.0 + rows * 0.11 + cols * 0.03
    asc_vh = -18.0 + rows * 0.07 + cols * 0.05
    desc_vv = -11.0 + rows * 0.04 + cols * 0.12
    desc_vh = -17.0 + rows * 0.09 + cols * 0.02

    asc_vv_n = _notebook_norm01(asc_vv)
    asc_vh_n = _notebook_norm01(asc_vh)
    desc_vv_n = _notebook_norm01(desc_vv)
    desc_vh_n = _notebook_norm01(desc_vh)
    asc_energy = _notebook_norm01(0.5 * asc_vv_n + 0.5 * asc_vh_n)
    desc_energy = _notebook_norm01(0.5 * desc_vv_n + 0.5 * desc_vh_n)
    expected = np.clip(1.0 - _notebook_norm01(np.abs(asc_energy - desc_energy)), 0, 1).astype(np.float32)

    actual = compute_asc_desc_consistency(
        asc_vv=asc_vv,
        asc_vh=asc_vh,
        desc_vv=desc_vv,
        desc_vh=desc_vh,
        nodata=-9999.0,
    )

    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-6)
