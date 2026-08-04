from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "audit_icesat2_candidate_context_priority.py"
)
SPEC = importlib.util.spec_from_file_location(
    "audit_icesat2_candidate_context_priority", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _dossier(
    *,
    step_m: float = 0.8,
    segment_count: int = 5,
    event_start: str = "2021-05-23T00:00:00+00:00",
    event_end: str = "2022-05-21T00:00:00+00:00",
) -> dict[str, object]:
    return {
        "candidate_id": "candidate",
        "candidate_summary": {
            "median_step_m": step_m,
            "segment_count": segment_count,
            "event_start": event_start,
            "event_end": event_end,
        },
        "segments": [],
    }


def test_plausible_candidate_is_prioritized_for_context_review():
    audit = MODULE.build_audit(_dossier())

    assert audit["status"] == "context_review_priority"
    assert audit["decision"]["context_review_recommended"] is True
    assert audit["decision"]["records_research_recommended"] is False


def test_large_magnitude_is_deferred():
    audit = MODULE.build_audit(_dossier(step_m=12.0))

    assert audit["status"] == "deferred_direct_thickness_magnitude"
    assert audit["decision"]["context_review_recommended"] is False


def test_too_few_segments_are_deferred():
    audit = MODULE.build_audit(_dossier(segment_count=3))

    assert audit["status"] == "deferred_insufficient_spatial_support"


def test_broad_event_window_is_deferred():
    audit = MODULE.build_audit(
        _dossier(
            event_start="2021-01-01T00:00:00+00:00",
            event_end="2025-01-01T00:00:00+00:00",
        )
    )

    assert audit["status"] == "deferred_event_window_too_broad"
