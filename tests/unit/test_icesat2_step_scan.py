from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.pipeline.elevation_change.icesat2_repeat import Icesat2Segment
from app.pipeline.elevation_change.icesat2_step_scan import (
    assess_segment_series,
    cluster_step_candidates,
    scan_segment_series,
)


def _segment(
    segment_id: str,
    *,
    cycle: int,
    month: int,
    height_m: float,
    x_m: float = 0.0,
    y_m: float = 0.0,
    spot: int = 5,
) -> Icesat2Segment:
    return Icesat2Segment(
        segment_id=segment_id,
        observed_at=datetime(2021 + (month - 1) // 12, ((month - 1) % 12) + 1, 1, tzinfo=UTC),
        longitude=x_m / 100000.0,
        latitude=y_m / 100000.0,
        x_m=x_m,
        y_m=y_m,
        height_m=height_m,
        height_uncertainty_m=2.0,
        terrain_slope=0.0,
        ground_photon_count=100,
        rgt=45,
        cycle=cycle,
        spot=spot,
        gt="gt2l",
    )


def test_flat_jump_flat_is_step_candidate() -> None:
    assessment = assess_segment_series(
        [
            _segment("100", cycle=10, month=1, height_m=10.00),
            _segment("100", cycle=11, month=4, height_m=10.03),
            _segment("100", cycle=12, month=7, height_m=10.72),
            _segment("100", cycle=13, month=10, height_m=10.75),
        ],
        minimum_step_m=0.5,
    )

    assert assessment.classification == "step_up_candidate"
    assert assessment.step_m == pytest.approx(0.72, abs=0.03)
    assert assessment.pre_cycle == 11
    assert assessment.post_cycle == 12


def test_gradual_rise_is_ramp_not_step() -> None:
    assessment = assess_segment_series(
        [
            _segment("100", cycle=10, month=1, height_m=10.0),
            _segment("100", cycle=11, month=4, height_m=10.2),
            _segment("100", cycle=12, month=7, height_m=10.4),
            _segment("100", cycle=13, month=10, height_m=10.6),
        ],
        minimum_step_m=0.3,
    )

    assert assessment.classification == "ramp_up"


def test_stable_terrain_is_not_candidate() -> None:
    assessment = assess_segment_series(
        [
            _segment("100", cycle=10, month=1, height_m=10.00),
            _segment("100", cycle=11, month=4, height_m=10.04),
            _segment("100", cycle=12, month=7, height_m=9.98),
            _segment("100", cycle=13, month=10, height_m=10.02),
        ]
    )

    assert assessment.classification == "stable"


def test_up_then_down_spike_is_rejected() -> None:
    assessment = assess_segment_series(
        [
            _segment("100", cycle=10, month=1, height_m=10.0),
            _segment("100", cycle=11, month=4, height_m=10.0),
            _segment("100", cycle=12, month=7, height_m=11.0),
            _segment("100", cycle=13, month=10, height_m=10.0),
            _segment("100", cycle=14, month=13, height_m=10.0),
        ],
        minimum_step_m=0.5,
    )

    assert assessment.classification != "step_up_candidate"


def test_neighbouring_consistent_steps_form_cluster() -> None:
    segments: list[Icesat2Segment] = []
    for index, x_m in enumerate((0.0, 100.0, 200.0), start=1):
        segment_id = str(index * 5)
        segments.extend(
            [
                _segment(segment_id, cycle=10, month=1, height_m=10.00, x_m=x_m),
                _segment(segment_id, cycle=11, month=4, height_m=10.02, x_m=x_m),
                _segment(segment_id, cycle=12, month=7, height_m=10.72, x_m=x_m),
                _segment(segment_id, cycle=13, month=10, height_m=10.74, x_m=x_m),
            ]
        )

    assessments = scan_segment_series(segments, minimum_step_m=0.5)
    clusters = cluster_step_candidates(
        assessments,
        neighbor_distance_m=150.0,
        minimum_neighbor_segments=3,
    )

    assert len(clusters) == 1
    assert len(clusters[0].assessments) == 3
    assert clusters[0].median_step_m == pytest.approx(0.72, abs=0.03)


def test_isolated_step_does_not_survive_neighbor_gate() -> None:
    segments = [
        _segment("5", cycle=10, month=1, height_m=10.0),
        _segment("5", cycle=11, month=4, height_m=10.0),
        _segment("5", cycle=12, month=7, height_m=10.8),
        _segment("5", cycle=13, month=10, height_m=10.8),
    ]

    assessments = scan_segment_series(segments, minimum_step_m=0.5)
    clusters = cluster_step_candidates(
        assessments,
        minimum_neighbor_segments=3,
    )

    assert clusters == []


def test_invalid_epoch_requirement_is_rejected() -> None:
    with pytest.raises(ValueError):
        assess_segment_series(
            [_segment("5", cycle=10, month=1, height_m=10.0)],
            minimum_epochs=3,
        )
