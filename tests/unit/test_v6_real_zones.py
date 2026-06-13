from __future__ import annotations

import json

import pytest

from app.services.v6_real_gee_runtime import V6GridConfig, build_v6_grid, validate_v6_aoi_bounds
from app.services.v6_real_scoring import V6ScoredCandidate
from app.services.v6_real_zones import (
    V6RequestZoneConfig,
    generate_v6_request_zones,
    request_zones_to_csv_rows,
    request_zones_to_geojson,
    safe_request_zone_summary,
)


def _candidate(cell_id: str, rank: int, *, score: float = 0.75, warnings: int = 0) -> V6ScoredCandidate:
    return V6ScoredCandidate(
        cell_id=cell_id,
        candidate_score=score,
        remote_sensing_contrast=0.6,
        s2_confidence=1.0,
        builtup_warning=0,
        cropland_heavy_warning=0,
        water_edge_warning=0,
        modern_linear_edge_warning=0,
        v6_building_warning=0,
        v6_road_like_warning=0,
        false_positive_warning_count=warnings,
        v6_false_positive_warning_count=warnings,
        v6_false_positive_penalty=warnings * 0.07,
        v6_quality_adjusted_score=score,
        v6_no_warning_bonus=1.0 if warnings == 0 else 0.5,
        v6_review_priority_score=score,
        final_priority_rank_v6=rank,
    )


def _grid():
    aoi = validate_v6_aoi_bounds(west=0, south=10, east=2, north=12)
    return build_v6_grid(aoi=aoi, config=V6GridConfig(rows=2, cols=2))


def test_generate_v6_request_zones_sorts_by_candidate_rank() -> None:
    zones = generate_v6_request_zones(
        [
            _candidate("V6_CELL_R001_C002", 2, score=0.70),
            _candidate("V6_CELL_R001_C001", 1, score=0.90),
        ],
        _grid(),
    )

    assert [zone.request_zone_id for zone in zones] == ["V6_RZ_001", "V6_RZ_002"]
    assert [zone.source_cell_id for zone in zones] == ["V6_CELL_R001_C001", "V6_CELL_R001_C002"]
    assert zones[0].quote_id == "V6_QUOTE_001"
    assert zones[0].final_priority_rank_v6 == 1


def test_generate_v6_request_zones_respects_max_zones() -> None:
    zones = generate_v6_request_zones(
        [
            _candidate("V6_CELL_R001_C001", 1),
            _candidate("V6_CELL_R001_C002", 2),
        ],
        _grid(),
        config=V6RequestZoneConfig(max_zones=1),
    )

    assert len(zones) == 1
    assert zones[0].source_cell_id == "V6_CELL_R001_C001"


def test_request_zones_to_csv_rows_excludes_bounds_values() -> None:
    zones = generate_v6_request_zones([_candidate("V6_CELL_R001_C001", 1)], _grid())

    rows = request_zones_to_csv_rows(zones)

    assert rows == (
        {
            "request_zone_id": "V6_RZ_001",
            "source_cell_id": "V6_CELL_R001_C001",
            "quote_id": "V6_QUOTE_001",
            "final_priority_rank_v6": 1,
            "v6_review_priority_score": 0.75,
            "v6_false_positive_warning_count": 0,
        },
    )
    serialized = json.dumps(rows, sort_keys=True)
    assert "west" not in serialized
    assert "south" not in serialized
    assert "east" not in serialized
    assert "north" not in serialized


def test_request_zones_to_geojson_builds_private_geometry_payload() -> None:
    zones = generate_v6_request_zones([_candidate("V6_CELL_R001_C001", 1)], _grid())

    geojson = request_zones_to_geojson(zones)

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1
    feature = geojson["features"][0]
    assert feature["properties"]["request_zone_id"] == "V6_RZ_001"
    assert feature["geometry"]["type"] == "Polygon"
    ring = feature["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1]
    assert len(ring) == 5


def test_safe_request_zone_summary_redacts_geometry_payload() -> None:
    zones = generate_v6_request_zones([_candidate("V6_CELL_R001_C001", 1)], _grid())

    summary = safe_request_zone_summary(zones)
    serialized = json.dumps(summary, sort_keys=True)

    assert summary["zone_count"] == 1
    assert summary["first_request_zone_id"] == "V6_RZ_001"
    assert summary["contains_geometry"] is False
    assert summary["bounds_values_redacted"] is True
    assert "coordinates" not in serialized
    assert "west" not in serialized


def test_generate_v6_request_zones_raises_for_missing_grid_cell() -> None:
    with pytest.raises(ValueError, match="missing_grid_cell_for_candidate:MISSING"):
        generate_v6_request_zones([_candidate("MISSING", 1)], _grid())


def test_request_zone_config_validates_positive_max_zones() -> None:
    assert V6RequestZoneConfig(max_zones=2).max_zones == 2

    with pytest.raises(ValueError, match="positive integer"):
        V6RequestZoneConfig(max_zones=0)
