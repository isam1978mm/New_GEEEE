from __future__ import annotations

import numpy as np

from app.pipeline._base import ParityCategory
from app.pipeline.stages.hypercube import HypercubeStage, build_hypercube_products


def test_hypercube_parity_matches_notebook_stack_clean_normalize_append_mask() -> None:
    layer_a = np.array([[1.0, np.nan], [3.0, 4.0]], dtype=np.float32)
    layer_b = np.array([[10.0, 20.0], [30.0, 40.0]], dtype=np.float32)

    products = build_hypercube_products([("a", layer_a), ("b", layer_b)], nodata=-9999.0)

    cube_raw = products["cube_raw"]
    mask_any = products["mask_any"]
    mask_all = products["mask_all"]
    cube_clean = products["cube_clean"]
    cube_norm = products["cube_norm"]
    cube_norm_plus_mask = products["cube_norm_plus_mask"]
    band_names = products["band_names"]

    assert HypercubeStage.parity_category is ParityCategory.PARITY_REPRODUCES
    assert cube_raw.shape == (2, 2, 3)
    assert mask_any.tolist() == [[1, 1], [1, 1]]
    assert mask_all.tolist() == [[1, 0], [1, 1]]
    assert cube_clean[0, 1, 0] == 0.0
    assert cube_norm.shape == (2, 2, 2)
    assert cube_norm_plus_mask.shape == (2, 2, 3)
    assert np.all(cube_norm_plus_mask[:, :, -1] == mask_any.astype(np.float32))
    assert np.allclose(cube_raw, cube_norm_plus_mask)
    assert band_names == ["a", "b", "valid_mask"]
