from __future__ import annotations

import numpy as np
import pytest

from app.pipeline.stages.object_extract import (
    CANDIDATE_THRESHOLD_POLICY_RAW,
    build_candidate_mask,
    connected_components,
)


def test_raw_threshold_falls_back_to_p99_when_robust_gate_is_impossible() -> None:
    anomaly = np.linspace(1.0, 5.0, 400, dtype=np.float32).reshape(20, 20)
    anomaly[18:20, 18:20] = 5.0

    finite = anomaly[np.isfinite(anomaly)].astype(np.float64)
    median = float(np.median(finite))
    mad = float(np.median(np.abs(finite - median)))
    robust_threshold = median + 6.0 * 1.4826 * mad
    maximum = float(np.max(finite))
    percentile_99 = float(np.percentile(finite, 99.0))

    assert robust_threshold >= maximum

    mask, threshold = build_candidate_mask(
        anomaly,
        floor=None,
        threshold_policy=CANDIDATE_THRESHOLD_POLICY_RAW,
    )

    assert threshold == pytest.approx(percentile_99)
    assert threshold <= maximum
    assert int(mask.sum()) == 4

    components = connected_components(mask)
    assert len(components) == 1
    assert components[0]["area_px"] == 4
