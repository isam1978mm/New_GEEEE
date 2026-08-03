from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.pipeline.elevation_change.gedi_points import (
    GediShot,
    datetime_from_delta_time,
    elevation_change_summary,
    independent_spatial_bin_count,
    pair_threshold_counts,
    reciprocal_nearest_pairs,
)


def _shot(
    name: str,
    x_m: float,
    y_m: float,
    elevation_m: float,
    *,
    day: int,
) -> GediShot:
    return GediShot(
        shot_number=name,
        observed_at=datetime(2020 if day == 1 else 2023, 1, day, tzinfo=UTC),
        longitude=0.0,
        latitude=0.0,
        x_m=x_m,
        y_m=y_m,
        elevation_m=elevation_m,
        beam=1,
        orbit_number=10,
        table_id="table",
        sensitivity=0.9,
    )


def test_delta_time_uses_gedi_epoch() -> None:
    assert datetime_from_delta_time(86400).isoformat() == "2018-01-02T00:00:00+00:00"


def test_reciprocal_pairs_are_unique() -> None:
    early = [
        _shot("e1", 0.0, 0.0, 10.0, day=1),
        _shot("e2", 2.0, 0.0, 20.0, day=1),
    ]
    late = [_shot("l1", 1.0, 0.0, 11.0, day=2)]

    pairs = reciprocal_nearest_pairs(early, late, max_distance_m=5.0)

    assert len(pairs) == 1
    assert pairs[0].late.shot_number == "l1"
    assert len({pair.early.shot_number for pair in pairs}) == len(pairs)
    assert len({pair.late.shot_number for pair in pairs}) == len(pairs)


def test_distance_thresholds_are_integer_counts() -> None:
    early = [
        _shot("e1", 0.0, 0.0, 10.0, day=1),
        _shot("e2", 100.0, 0.0, 20.0, day=1),
    ]
    late = [
        _shot("l1", 4.0, 0.0, 11.0, day=2),
        _shot("l2", 112.0, 0.0, 21.0, day=2),
    ]
    pairs = reciprocal_nearest_pairs(early, late, max_distance_m=25.0)

    counts = pair_threshold_counts(pairs)

    assert counts == {
        "within_5m": 1,
        "within_10m": 1,
        "within_15m": 2,
        "within_25m": 2,
    }
    assert all(isinstance(value, int) for value in counts.values())


def test_change_summary_is_late_minus_early() -> None:
    early = [_shot("e", 0.0, 0.0, 10.0, day=1)]
    late = [_shot("l", 1.0, 0.0, 10.75, day=2)]
    pairs = reciprocal_nearest_pairs(early, late, max_distance_m=5.0)

    summary = elevation_change_summary(pairs)

    assert summary["count"] == 1
    assert summary["median_m"] == pytest.approx(0.75)


def test_spatial_bins_report_dispersion_not_shot_count() -> None:
    early = [
        _shot("e1", 10.0, 10.0, 1.0, day=1),
        _shot("e2", 20.0, 20.0, 1.0, day=1),
        _shot("e3", 210.0, 10.0, 1.0, day=1),
    ]
    late = [
        _shot("l1", 11.0, 10.0, 1.0, day=2),
        _shot("l2", 21.0, 20.0, 1.0, day=2),
        _shot("l3", 211.0, 10.0, 1.0, day=2),
    ]
    pairs = reciprocal_nearest_pairs(early, late, max_distance_m=5.0)

    assert independent_spatial_bin_count(pairs, bin_size_m=100.0) == 2


def test_nonpositive_pair_distance_is_rejected() -> None:
    with pytest.raises(ValueError):
        reciprocal_nearest_pairs([], [], max_distance_m=0)
