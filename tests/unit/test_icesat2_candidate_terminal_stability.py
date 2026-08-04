from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "audit_icesat2_candidate_terminal_stability.py"
)
SPEC = importlib.util.spec_from_file_location(
    "audit_icesat2_candidate_terminal_stability", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _segment(
    segment_id: str,
    *,
    immediate_height: float,
    terminal_height: float,
) -> dict[str, object]:
    return {
        "segment_id": segment_id,
        "rgt": 1,
        "spot": 1,
        "pre_cycle": 10,
        "post_cycle": 11,
        "pre_median_m": 100.0,
        "post_median_m": 101.0,
        "step_m": 1.0,
        "timeline": [
            {"cycle": 10, "height_m": 100.0, "observed_at": "2021-01-01"},
            {"cycle": 11, "height_m": 101.0, "observed_at": "2021-04-01"},
            {
                "cycle": 12,
                "height_m": immediate_height,
                "observed_at": "2021-07-01",
            },
            {
                "cycle": 20,
                "height_m": terminal_height,
                "observed_at": "2023-07-01",
            },
        ],
    }


def _dossier(*segments: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_id": "candidate",
        "segments": list(segments),
    }


def test_stable_late_epochs_remain_eligible():
    audit = MODULE.build_audit(
        _dossier(
            _segment("001", immediate_height=100.9, terminal_height=100.95),
            _segment("002", immediate_height=100.8, terminal_height=100.9),
            _segment("003", immediate_height=100.85, terminal_height=100.8),
        )
    )

    assert audit["status"] == "terminal_stability_not_disproved"
    assert audit["decision"]["direct_thickness_anchor_lookup_recommended"] is True
    assert audit["median_terminal_retention_fraction"] == 0.9


def test_immediate_reversal_is_rejected():
    audit = MODULE.build_audit(
        _dossier(
            _segment("001", immediate_height=100.2, terminal_height=100.8),
            _segment("002", immediate_height=100.1, terminal_height=100.9),
            _segment("003", immediate_height=100.3, terminal_height=100.7),
        )
    )

    assert audit["status"] == "immediate_post_step_reversal_pattern"
    assert audit["immediate_reversal_like_segment_fraction"] == 1.0
    assert audit["decision"]["direct_thickness_anchor_lookup_recommended"] is False


def test_late_epoch_reversal_is_rejected():
    audit = MODULE.build_audit(
        _dossier(
            _segment("001", immediate_height=100.9, terminal_height=100.1),
            _segment("002", immediate_height=100.8, terminal_height=99.9),
            _segment("003", immediate_height=100.85, terminal_height=100.2),
        )
    )

    assert audit["status"] == "late_epoch_reversal_pattern"
    assert audit["terminal_reversal_like_segment_fraction"] == 1.0
    assert audit["decision"]["direct_thickness_anchor_lookup_recommended"] is False


def test_missing_followup_is_not_eligible():
    segment = _segment("001", immediate_height=100.9, terminal_height=100.9)
    segment["timeline"] = [
        {"cycle": 10, "height_m": 100.0, "observed_at": "2021-01-01"},
        {"cycle": 11, "height_m": 101.0, "observed_at": "2021-04-01"},
    ]
    audit = MODULE.build_audit(_dossier(segment))

    assert audit["status"] == "insufficient_followup_for_terminal_stability"
    assert audit["decision"]["direct_thickness_anchor_lookup_recommended"] is False
