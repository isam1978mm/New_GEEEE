from __future__ import annotations

import json
import math
import random
from pathlib import Path

import pytest

from scripts.match_tyrone_ose_spatial_pattern import (
    CandidatePoint,
    MapPoint,
    filter_and_project_candidates,
    find_hypotheses,
    load_map_points,
)


def test_load_map_points_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = tmp_path / "map.json"
    path.write_text(
        json.dumps(
            {
                "points": [
                    {"id": "a", "x": 0, "y": 0},
                    {"id": "a", "x": 1, "y": 1},
                    {"id": "c", "x": 2, "y": 2},
                    {"id": "d", "x": 3, "y": 3},
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_map_points(path)


def test_filter_candidates_keeps_tyrone_owner_and_deduplicates() -> None:
    rows = [
        {
            "longitude": -108.4,
            "latitude": 32.65,
            "own_lname": "Phelps Dodge Tyrone",
            "priority_score": 1,
            "OBJECTID": 1,
        },
        {
            "longitude": -108.4,
            "latitude": 32.65,
            "own_lname": "Phelps Dodge Tyrone",
            "priority_score": 2,
            "OBJECTID": 2,
        },
        {
            "longitude": -108.41,
            "latitude": 32.66,
            "own_lname": "Unrelated owner",
            "priority_score": 10,
            "OBJECTID": 3,
        },
    ]

    candidates = filter_and_project_candidates(rows)

    assert len(candidates) == 1
    assert candidates[0].attributes["OBJECTID"] == 2


def _synthetic_constellation() -> tuple[list[MapPoint], list[CandidatePoint]]:
    map_points = [
        MapPoint("a", 0, 0),
        MapPoint("b", 100, 0),
        MapPoint("c", 0, 100),
        MapPoint("d", 100, 100),
        MapPoint("e", 50, 180),
        MapPoint("f", -50, 80),
        MapPoint("g", 180, 50),
    ]
    alpha = 3 * complex(math.cos(0.4), math.sin(0.4))
    beta = 500000 + 1j * 3600000
    candidates: list[CandidatePoint] = []
    for index, point in enumerate(map_points):
        source = point.x + 1j * (-point.y)
        target = alpha * source + beta
        candidates.append(
            CandidatePoint(
                index=index,
                longitude=-108.4,
                latitude=32.65,
                easting_m=target.real,
                northing_m=target.imag,
                attributes={
                    "OBJECTID": index,
                    "own_lname": "Phelps Dodge Tyrone",
                },
            )
        )

    random.seed(2)
    for offset in range(12):
        candidates.append(
            CandidatePoint(
                index=len(candidates),
                longitude=-108.4,
                latitude=32.65,
                easting_m=499000 + random.random() * 4000,
                northing_m=3599000 + random.random() * 4000,
                attributes={
                    "OBJECTID": 100 + offset,
                    "own_lname": "Phelps Dodge Tyrone",
                },
            )
        )
    return map_points, candidates


def test_find_hypotheses_recovers_seven_point_pattern() -> None:
    map_points, candidates = _synthetic_constellation()

    hypotheses = find_hypotheses(
        map_points,
        candidates,
        tolerance_m=5,
        minimum_matches=7,
    )

    assert hypotheses
    assert len(hypotheses[0]["matches"]) == 7
    assert hypotheses[0]["ranking"][1] < 1e-6


def test_find_hypotheses_returns_empty_when_minimum_is_impossible() -> None:
    map_points, candidates = _synthetic_constellation()

    assert find_hypotheses(
        map_points,
        candidates[:4],
        minimum_matches=6,
    ) == []


def test_real_map_config_is_discovery_only() -> None:
    config = Path("config/tyrone_route_b_map_well_pixels.json")
    payload = json.loads(config.read_text(encoding="utf-8"))

    assert len(payload["points"]) == 7
    assert payload["coordinate_type"] == "manual_marker_center_pixels"
    assert "not surveyed coordinates" in payload["warning"]
