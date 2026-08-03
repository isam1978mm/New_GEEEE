from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.pipeline.elevation_change.icesat2_repeat import Icesat2Segment
from app.pipeline.elevation_change.icesat2_step_scan import SegmentStepAssessment


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "audit_icesat2_regional_near_misses.py"
)
SPEC = importlib.util.spec_from_file_location(
    "audit_icesat2_regional_near_misses", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _observation(
    *,
    segment_id: str,
    cycle: int,
    height_m: float,
    x_m: float,
) -> Icesat2Segment:
    return Icesat2Segment(
        segment_id=segment_id,
        observed_at=datetime(2021 + cycle, 1, 1, tzinfo=UTC),
        longitude=37.0,
        latitude=33.5,
        x_m=x_m,
        y_m=1000.0,
        height_m=height_m,
        height_uncertainty_m=2.0,
        terrain_slope=0.0,
        ground_photon_count=50,
        rgt=45,
        cycle=cycle,
        spot=5,
        gt="gt1l",
    )


def _candidate(
    segment_id: str,
    *,
    x_m: float,
    step_m: float = 0.8,
    pre_cycle: int = 11,
    post_cycle: int = 16,
    spot: int = 5,
) -> SegmentStepAssessment:
    before = _observation(
        segment_id=segment_id,
        cycle=pre_cycle,
        height_m=10.0,
        x_m=x_m,
    )
    after = _observation(
        segment_id=segment_id,
        cycle=post_cycle,
        height_m=10.0 + step_m,
        x_m=x_m,
    )
    return SegmentStepAssessment(
        rgt=45,
        spot=spot,
        segment_id=segment_id,
        x_m=x_m,
        y_m=1000.0,
        longitude=37.0 + x_m / 1_000_000.0,
        latitude=33.5,
        classification="step_up_candidate",
        observation_count=4,
        cycle_count=4,
        pre_cycle=pre_cycle,
        post_cycle=post_cycle,
        event_start=before.observed_at,
        event_end=after.observed_at,
        pre_median_m=10.0,
        post_median_m=10.0 + step_m,
        step_m=step_m,
        pre_nmad_m=0.02,
        post_nmad_m=0.02,
        residual_nmad_m=0.03,
        linear_residual_nmad_m=0.2,
        dominant_increment_ratio=0.9,
        positive_increment_fraction=1.0 / 3.0,
        score=10.0,
        observations=(before, after),
    )


def test_selected_geographies_only_keeps_raw_steps_without_clusters():
    summary = {
        "geography_summaries": [
            {
                "geography_id": "near",
                "raw_step_up_segment_count": 2,
                "surviving_step_cluster_count": 0,
            },
            {
                "geography_id": "none",
                "raw_step_up_segment_count": 0,
                "surviving_step_cluster_count": 0,
            },
            {
                "geography_id": "passed",
                "raw_step_up_segment_count": 3,
                "surviving_step_cluster_count": 1,
            },
        ]
    }

    assert MODULE._selected_geography_ids(summary) == ["near"]


def test_wider_radius_can_be_identified_as_binding_without_changing_gate():
    candidates = [
        _candidate("100", x_m=0.0),
        _candidate("101", x_m=300.0, step_m=0.82),
        _candidate("102", x_m=600.0, step_m=0.78),
    ]

    groups = MODULE.diagnose_event_groups(
        candidates,
        strict_radius_m=250.0,
        diagnostic_radii_m=(500.0, 1000.0),
        minimum_segments=3,
        maximum_step_nmad_m=0.25,
    )

    assert len(groups) == 1
    assert groups[0]["diagnosis"] == "strict_neighbor_radius_was_binding"
    assert groups[0]["radius_diagnostics"][0]["passing_component_count"] == 0
    assert groups[0]["radius_diagnostics"][1]["passing_component_count"] == 1


def test_three_same_event_segments_can_remain_genuinely_isolated():
    candidates = [
        _candidate("100", x_m=0.0),
        _candidate("101", x_m=1200.0),
        _candidate("102", x_m=2400.0),
    ]

    groups = MODULE.diagnose_event_groups(candidates)

    assert groups[0]["diagnosis"] == (
        "event_peers_exist_but_remain_disconnected_or_inconsistent"
    )
    assert all(
        item["passing_component_count"] == 0
        for item in groups[0]["radius_diagnostics"]
    )


def test_different_event_windows_are_not_merged():
    candidates = [
        _candidate("100", x_m=0.0, pre_cycle=11, post_cycle=16),
        _candidate("101", x_m=50.0, pre_cycle=12, post_cycle=28),
        _candidate("102", x_m=100.0, pre_cycle=11, post_cycle=28),
    ]

    groups = MODULE.diagnose_event_groups(candidates)

    assert len(groups) == 3
    assert {item["diagnosis"] for item in groups} == {"single_same_event_segment"}


def test_cross_spot_support_is_reported_but_not_accepted_as_same_spot_cluster():
    first = _candidate("100", x_m=0.0, spot=5)
    second = _candidate("200", x_m=100.0, spot=6)

    mapped = MODULE._assessment_mapping(
        first,
        [first, second],
        cross_spot_distance_m=500.0,
    )

    assert mapped["nearest_same_event_same_spot_m"] is None
    assert mapped["nearest_same_event_any_spot_m"] == 100.0
    assert mapped["cross_spot_supported_within_m"] is True
