from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.pipeline.elevation_change.icesat2_repeat import (
    Icesat2Segment,
    change_summary,
    independent_midpoint_bins,
    readiness,
    reciprocal_repeat_pairs,
    summary_by_distance,
)


def _segment(
    name: str,
    x_m: float,
    y_m: float,
    height_m: float,
    *,
    year: int,
    cycle: int,
    rgt: int = 100,
    spot: int = 1,
) -> Icesat2Segment:
    return Icesat2Segment(
        segment_id=name,
        observed_at=datetime(year, 1, 1, tzinfo=UTC),
        longitude=0.0,
        latitude=0.0,
        x_m=x_m,
        y_m=y_m,
        height_m=height_m,
        height_uncertainty_m=0.1,
        terrain_slope=0.0,
        ground_photon_count=10,
        rgt=rgt,
        cycle=cycle,
        spot=spot,
        gt="gt1l",
    )


def test_pairs_require_same_rgt_and_spot() -> None:
    early = [_segment("e", 0.0, 0.0, 10.0, year=2020, cycle=1)]
    late = [
        _segment("wrong_rgt", 1.0, 0.0, 11.0, year=2023, cycle=2, rgt=101),
        _segment("wrong_spot", 1.0, 0.0, 11.0, year=2023, cycle=2, spot=2),
    ]
    assert reciprocal_repeat_pairs(early, late, max_distance_m=5.0) == []


def test_pairs_require_different_cycles() -> None:
    early = [_segment("e", 0.0, 0.0, 10.0, year=2020, cycle=1)]
    late = [_segment("l", 1.0, 0.0, 11.0, year=2023, cycle=1)]
    assert reciprocal_repeat_pairs(early, late, max_distance_m=5.0) == []


def test_reciprocal_matching_is_unique() -> None:
    early = [
        _segment("e1", 0.0, 0.0, 10.0, year=2020, cycle=1),
        _segment("e2", 2.0, 0.0, 20.0, year=2020, cycle=1),
    ]
    late = [_segment("l1", 1.0, 0.0, 11.0, year=2023, cycle=2)]
    pairs = reciprocal_repeat_pairs(early, late, max_distance_m=5.0)
    assert len(pairs) == 1
    assert len({pair.late.segment_id for pair in pairs}) == 1


def test_change_summary_reports_late_minus_early() -> None:
    early = [_segment("e", 0.0, 0.0, 10.0, year=2020, cycle=1)]
    late = [_segment("l", 1.0, 0.0, 10.75, year=2023, cycle=2)]
    pairs = reciprocal_repeat_pairs(early, late, max_distance_m=5.0)
    summary = change_summary(pairs)
    assert summary["count"] == 1
    assert summary["median_m"] == pytest.approx(0.75)


def test_summary_by_distance_uses_nested_bands() -> None:
    early = [
        _segment("e1", 0.0, 0.0, 10.0, year=2020, cycle=1),
        _segment("e2", 100.0, 0.0, 20.0, year=2020, cycle=1),
    ]
    late = [
        _segment("l1", 4.0, 0.0, 10.5, year=2023, cycle=2),
        _segment("l2", 112.0, 0.0, 20.5, year=2023, cycle=2),
    ]
    pairs = reciprocal_repeat_pairs(early, late, max_distance_m=15.0)
    summaries = summary_by_distance(pairs)
    assert summaries["within_5m"]["count"] == 1
    assert summaries["within_10m"]["count"] == 1
    assert summaries["within_15m"]["count"] == 2


def test_readiness_requires_count_and_detection_floor() -> None:
    summaries = {
        "within_5m": {"count": 29, "detection_floor_95_m": 0.2},
        "within_10m": {"count": 30, "detection_floor_95_m": 0.8},
    }
    decision = readiness(summaries, target_m=0.7, minimum_pairs=30)
    assert decision["ready_for_point_change_prototype"] is False

    summaries["within_10m"]["detection_floor_95_m"] = 0.6
    decision = readiness(summaries, target_m=0.7, minimum_pairs=30)
    assert decision["ready_for_point_change_prototype"] is True
    assert decision["supporting_distance_band"] == "within_10m"


def test_independent_bins_measure_dispersion() -> None:
    early = [
        _segment("e1", 10.0, 10.0, 1.0, year=2020, cycle=1),
        _segment("e2", 210.0, 10.0, 1.0, year=2020, cycle=1),
    ]
    late = [
        _segment("l1", 11.0, 10.0, 1.0, year=2023, cycle=2),
        _segment("l2", 211.0, 10.0, 1.0, year=2023, cycle=2),
    ]
    pairs = reciprocal_repeat_pairs(early, late, max_distance_m=5.0)
    assert independent_midpoint_bins(pairs, bin_size_m=100.0) == 2
