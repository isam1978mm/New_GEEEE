from __future__ import annotations

from datetime import UTC, datetime

from app.pipeline.elevation_change.icesat2_independence import (
    build_cycle_pair_cohorts,
    independence_decision,
    summarize_cohort,
)
from app.pipeline.elevation_change.icesat2_repeat import Icesat2Segment


def _segment(
    *,
    segment_id: str,
    cycle: int,
    year: int,
    x_m: float,
    height_m: float,
    rgt: int = 45,
    spot: int = 5,
) -> Icesat2Segment:
    return Icesat2Segment(
        segment_id=segment_id,
        observed_at=datetime(year, 6, 1, tzinfo=UTC),
        longitude=0.0,
        latitude=0.0,
        x_m=x_m,
        y_m=0.0,
        height_m=height_m,
        height_uncertainty_m=2.0,
        terrain_slope=0.0,
        ground_photon_count=100,
        rgt=rgt,
        cycle=cycle,
        spot=spot,
        gt="gt1l",
    )


def _cycle_segments(cycle: int, year: int, offset: float) -> list[Icesat2Segment]:
    return [
        _segment(
            segment_id=str(index),
            cycle=cycle,
            year=year,
            x_m=float(index * 100),
            height_m=float(index) + offset + ((index % 3) - 1) * 0.01,
        )
        for index in range(40)
    ]


def test_one_cycle_pair_does_not_count_as_multi_epoch_support() -> None:
    segments = _cycle_segments(12, 2021, 0.0) + _cycle_segments(16, 2022, 0.1)
    cohorts = build_cycle_pair_cohorts(
        segments,
        split_time=datetime(2022, 1, 1, tzinfo=UTC),
    )
    summaries = [
        summarize_cohort(cohort, target_m=0.7, minimum_pairs=30)
        for cohort in cohorts
    ]

    decision = independence_decision(summaries)

    assert len(cohorts) == 1
    assert decision["single_cycle_pair_precision_supported"] is True
    assert decision["multi_epoch_repeatability_supported"] is False


def test_two_early_and_two_late_cycles_can_support_independence() -> None:
    segments = (
        _cycle_segments(11, 2020, 0.00)
        + _cycle_segments(12, 2021, 0.02)
        + _cycle_segments(16, 2022, 0.10)
        + _cycle_segments(17, 2023, 0.12)
    )
    cohorts = build_cycle_pair_cohorts(
        segments,
        split_time=datetime(2022, 1, 1, tzinfo=UTC),
    )
    summaries = [
        summarize_cohort(cohort, target_m=0.7, minimum_pairs=30)
        for cohort in cohorts
    ]

    decision = independence_decision(summaries)

    assert len(cohorts) == 4
    assert decision["multi_epoch_repeatability_supported"] is True
    assert decision["distinct_passing_early_cycles"] == [11, 12]
    assert decision["distinct_passing_late_cycles"] == [16, 17]


def test_cohorts_do_not_cross_rgt_or_spot() -> None:
    early = _cycle_segments(12, 2021, 0.0)
    late_other_track = [
        _segment(
            segment_id=str(index),
            cycle=16,
            year=2022,
            x_m=float(index * 100),
            height_m=float(index) + 0.1,
            rgt=46,
            spot=5,
        )
        for index in range(40)
    ]

    cohorts = build_cycle_pair_cohorts(
        early + late_other_track,
        split_time=datetime(2022, 1, 1, tzinfo=UTC),
    )

    assert cohorts == []
