from __future__ import annotations

import numpy as np

from app.pipeline._base import ParityCategory
from app.pipeline.stages.pca_anomaly import PcaAnomalyStage, compute_pca_anomaly


def test_pca_parity_records_intentional_correction_not_frozen_numeric_parity() -> None:
    cube = np.zeros((10, 10, 3), dtype=np.float32)
    cube[:, :, 0] = np.arange(100, dtype=np.float32).reshape(10, 10)
    cube[:, :, 1] = cube[:, :, 0] * 0.5 + 5.0
    cube[:, :, 2] = np.flipud(cube[:, :, 0])

    anomaly, report = compute_pca_anomaly(cube, nodata=-9999.0, seed=0)

    assert PcaAnomalyStage.parity_category is ParityCategory.PARITY_CORRECTS
    assert PcaAnomalyStage.parity_reason is not None
    assert report["seed"] == 0
    assert report["sample_size"] == 100
    assert len(report["explained_variance_ratio"]) == 3
    assert "eigenvalues" in report or "explained_variance" in report
    assert report["raw_score_method"] == "pca_whitened_projected_component_distance"
    assert report["legacy_pca_compatibility_mode"] == "not_enabled_corrected_default"
    assert report["parity_category"] == "PARITY_CORRECTS"
    assert "Frozen numeric notebook parity is not claimed" in report["parity_reason"]
    assert float(np.min(anomaly)) >= 0.0
    assert float(np.max(anomaly)) <= 1.0
    assert anomaly.shape == (10, 10)
