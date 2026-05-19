from __future__ import annotations

import numpy as np

from app.pipeline._base import ParityCategory
from app.pipeline.stages.object_extract import ObjectExtractStage, build_object_products


def test_objects_parity_matches_notebook_style_component_extract_cluster_and_patch_contract() -> None:
    anomaly = np.zeros((16, 16), dtype=np.float32)
    anomaly[2:6, 2:6] = 0.97
    anomaly[9:13, 10:14] = 0.99
    hypercube = np.dstack([anomaly, anomaly * 2.0, anomaly * 0.5]).astype(np.float32)

    products = build_object_products(anomaly, hypercube)

    objects = products["objects"]
    clusters = products["clusters"]
    mask = products["mask"]
    assert ObjectExtractStage.parity_category is ParityCategory.PARITY_REPRODUCES
    assert len(objects) == 2
    assert len(clusters) == 2
    assert int(mask.sum()) == 32
    assert objects[0]["row_min"] == 2
    assert objects[0]["col_min"] == 2
    assert "cluster_id" in objects[0]
