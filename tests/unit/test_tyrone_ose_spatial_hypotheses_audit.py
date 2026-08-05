from __future__ import annotations

import numpy as np
from pyproj import Transformer

from scripts.audit_tyrone_ose_spatial_hypotheses import (
    _fit_similarity,
    audit_report,
)


def _report(with_outliers: bool) -> dict:
    points = [
        {"id": f"P{i}", "x": float(i % 3) * 100.0, "y": float(i // 3) * 100.0}
        for i in range(7)
    ]
    src = np.array([[p["x"], -p["y"]] for p in points], dtype=float)
    matrix = np.array([[2.0, 0.0], [0.0, 2.0]])
    offset = np.array([300000.0, 3600000.0])
    utm = src @ matrix + offset
    if with_outliers:
        utm[5] += np.array([35.0, 20.0])
        utm[6] += np.array([-30.0, 25.0])
    to_wgs84 = Transformer.from_crs(32612, 4326, always_xy=True)
    lon, lat = to_wgs84.transform(utm[:, 0], utm[:, 1])
    matches = [
        {
            "map_point_id": point["id"],
            "matched": True,
            "candidate_longitude": float(lon[i]),
            "candidate_latitude": float(lat[i]),
        }
        for i, point in enumerate(points)
    ]
    return {
        "map_config": {"points": points},
        "hypotheses": [{"matches": matches}],
    }


def test_fit_similarity_recovers_simple_transform() -> None:
    source = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    target = np.array([[10.0, 20.0], [12.0, 20.0], [10.0, 22.0]])
    matrix, offset, _ = _fit_similarity(source, target)
    predicted = source @ matrix + offset
    assert np.max(np.abs(predicted - target)) < 1e-9


def test_audit_accepts_consistent_pattern() -> None:
    result = audit_report(_report(with_outliers=False))
    assert result["status"] == "credible_discovery_pattern_found"
    assert result["credible_hypothesis_count"] == 1
    assert result["coordinate_geometry_unblocked"] is False
    assert result["numerical_depth_unlocked"] is False


def test_audit_rejects_pattern_with_two_large_outliers() -> None:
    result = audit_report(_report(with_outliers=True))
    assert result["status"] == "all_discovery_patterns_failed_independent_accuracy"
    assert result["credible_hypothesis_count"] == 0


def test_audit_keeps_final_geometry_gate_closed() -> None:
    result = audit_report(_report(with_outliers=False))
    assert "final geometry gate" in result["warning"]
    assert result["thresholds"]["check_rmse_m_max"] == 5.0
    assert result["thresholds"]["check_max_residual_m_max"] == 7.5
