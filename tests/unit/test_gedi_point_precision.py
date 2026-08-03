from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.pipeline.elevation_change.gedi_points import GediPair, GediShot
from app.pipeline.elevation_change.gedi_precision import (
    GediTerrainReference,
    assess_sub_metre_readiness,
    corrected_pair_change,
    summaries_by_distance,
)


def _shot(name: str, x: float, elevation: float) -> GediShot:
    return GediShot(
        shot_number=name,
        observed_at=datetime(2020, 1, 1, tzinfo=UTC),
        longitude=0.0,
        latitude=0.0,
        x_m=x,
        y_m=0.0,
        elevation_m=elevation,
        beam=1,
        orbit_number=1,
        table_id="table",
    )


def _pair(
    index: int,
    distance: float,
    raw_change: float,
    terrain_change: float,
) -> tuple[GediPair, dict[str, GediTerrainReference]]:
    early = _shot(f"e{index}", index * 100.0, 100.0)
    late = _shot(f"l{index}", index * 100.0 + distance, 100.0 + raw_change)
    pair = GediPair(early=early, late=late, distance_m=distance)
    terrain = {
        early.shot_number: GediTerrainReference(tandemx_m=50.0, srtm_m=70.0),
        late.shot_number: GediTerrainReference(
            tandemx_m=50.0 + terrain_change,
            srtm_m=70.0 + terrain_change,
        ),
    }
    return pair, terrain


def test_slope_correction_removes_static_terrain_offset() -> None:
    pair, terrain = _pair(1, 5.0, raw_change=2.7, terrain_change=2.0)

    assert corrected_pair_change(pair, terrain, correction="raw") == pytest.approx(2.7)
    assert corrected_pair_change(pair, terrain, correction="tandemx") == pytest.approx(0.7)
    assert corrected_pair_change(pair, terrain, correction="srtm") == pytest.approx(0.7)


def test_missing_reference_is_reported_not_invented() -> None:
    pair, _ = _pair(1, 5.0, raw_change=1.0, terrain_change=0.2)
    summaries = summaries_by_distance([pair], {})

    assert summaries["raw"]["within_5m"]["usable_pair_count"] == 1
    assert summaries["tandemx"]["within_5m"]["usable_pair_count"] == 0
    assert summaries["tandemx"]["within_5m"]["missing_reference_count"] == 1


def test_distance_bands_are_nested() -> None:
    pairs = []
    terrain: dict[str, GediTerrainReference] = {}
    for index, distance in enumerate((4.0, 8.0, 14.0, 20.0), start=1):
        pair, refs = _pair(index, distance, raw_change=0.2, terrain_change=0.0)
        pairs.append(pair)
        terrain.update(refs)

    summaries = summaries_by_distance(pairs, terrain)

    assert summaries["raw"]["within_5m"]["usable_pair_count"] == 1
    assert summaries["raw"]["within_10m"]["usable_pair_count"] == 2
    assert summaries["raw"]["within_15m"]["usable_pair_count"] == 3
    assert summaries["raw"]["within_25m"]["usable_pair_count"] == 4


def test_readiness_requires_both_reference_models_and_enough_pairs() -> None:
    good = {
        "tandemx": {
            "within_5m": {"usable_pair_count": 30, "detection_floor_95_m": 0.5},
            "within_10m": {"usable_pair_count": 40, "detection_floor_95_m": 0.6},
        },
        "srtm": {
            "within_5m": {"usable_pair_count": 30, "detection_floor_95_m": 0.6},
            "within_10m": {"usable_pair_count": 40, "detection_floor_95_m": 0.6},
        },
    }
    result = assess_sub_metre_readiness(good, target_m=0.7)
    assert result["ready_for_point_change_prototype"] is True
    assert result["supporting_distance_band"] == "within_5m"

    too_few = {
        "tandemx": {
            "within_5m": {"usable_pair_count": 15, "detection_floor_95_m": 0.3}
        },
        "srtm": {
            "within_5m": {"usable_pair_count": 15, "detection_floor_95_m": 0.3}
        },
    }
    assert (
        assess_sub_metre_readiness(too_few)["ready_for_point_change_prototype"]
        is False
    )
