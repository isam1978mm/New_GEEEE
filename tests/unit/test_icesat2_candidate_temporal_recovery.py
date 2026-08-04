from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "audit_icesat2_candidate_temporal_recovery.py"
)
SPEC = importlib.util.spec_from_file_location(
    "audit_icesat2_candidate_temporal_recovery", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _segment(
    segment_id: str,
    heights: list[float],
    *,
    step_m: float,
):
    cycles = [12, 14, 15, 16, 17, 24]
    return {
        "segment_id": segment_id,
        "rgt": 844,
        "spot": 3,
        "pre_cycle": 15,
        "post_cycle": 16,
        "pre_median_m": sorted(heights[:3])[1],
        "post_median_m": sorted(heights[3:])[1],
        "step_m": step_m,
        "timeline": [
            {
                "cycle": cycle,
                "height_m": height,
                "observed_at": f"202{index}-01-01T00:00:00+00:00",
            }
            for index, (cycle, height) in enumerate(zip(cycles, heights), start=1)
        ],
    }


def test_recovery_pattern_is_identified():
    dossier = {
        "candidate_id": "candidate_001",
        "segments": [
            _segment("1", [100.0, 99.5, 99.5, 100.1, 100.0, 100.0], step_m=0.5),
            _segment("2", [200.0, 199.4, 199.5, 200.0, 200.1, 200.0], step_m=0.5),
            _segment("3", [300.0, 299.5, 299.5, 300.1, 300.0, 300.0], step_m=0.5),
        ],
    }

    result = MODULE.build_audit(dossier)

    assert result["status"] == "temporary_depression_recovery_pattern"
    assert result["recovery_like_segment_count"] == 3
    assert result["decision"]["direct_thickness_anchor_lookup_recommended"] is False


def test_lasting_rise_is_not_rejected():
    dossier = {
        "candidate_id": "candidate_002",
        "segments": [
            _segment("1", [100.0, 100.0, 100.0, 100.6, 100.5, 100.6], step_m=0.55),
            _segment("2", [200.0, 200.0, 200.0, 200.5, 200.6, 200.5], step_m=0.55),
            _segment("3", [300.0, 300.0, 300.0, 300.5, 300.5, 300.6], step_m=0.55),
        ],
    }

    result = MODULE.build_audit(dossier)

    assert result["status"] == "lasting_rise_not_disproved_by_recovery_audit"
    assert result["recovery_like_segment_count"] == 0
    assert result["decision"]["direct_thickness_anchor_lookup_recommended"] is True


def test_invalid_threshold_is_rejected():
    try:
        MODULE.build_audit(
            {"segments": [_segment("1", [1, 1, 1, 2, 2, 2], step_m=1.0)]},
            maximum_net_fraction=1.1,
        )
    except ValueError as exc:
        assert "between 0 and 1" in str(exc)
    else:
        raise AssertionError("invalid threshold should fail")
