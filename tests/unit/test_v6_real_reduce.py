from __future__ import annotations

import json

import pytest

from app.services.v6_real_gee_features import REQUIRED_V6_FEATURE_BANDS
from app.services.v6_real_reduce import (
    V6FeatureReductionConfig,
    reduced_feature_rows_from_records,
    safe_reduction_summary,
    score_reduced_v6_feature_rows,
)


def _properties(cell_id: str, **overrides):
    props = {band: 0.5 for band in REQUIRED_V6_FEATURE_BANDS}
    props.update(
        {
            "cell_id": cell_id,
            "grid_row": 1,
            "grid_col": 1,
            "visibility_score": 0.7,
            "spectral_contrast": 0.6,
            "terrain_score": 0.8,
            "s2_count": 8,
            "builtup_frac": 0.0,
            "cropland_frac": 0.0,
            "water_edge_frac": 0.0,
            "v6_strong_built_frac": 0.0,
            "v6_building_near_frac": 0.0,
            "v6_road_like_edge_frac": 0.0,
            "v6_modern_corridor_frac": 0.0,
            "confidence_score_all": 0.8,
            "stability_score_norm": 0.7,
            "season_stability_norm": 0.6,
            "score_gap_from_median": 0.1,
            "top10_count": 2,
            "top25_count": 4,
            "season_top10_count": 1,
            "season_top25_count": 3,
        }
    )
    props.update(overrides)
    return props


def test_reduced_feature_rows_from_records_extracts_properties_only() -> None:
    rows = reduced_feature_rows_from_records(
        [
            {
                "type": "Feature",
                "geometry": {"type": "Polygon"},
                "properties": _properties("CELL_A"),
            }
        ]
    )

    assert len(rows) == 1
    assert rows[0].cell_id == "CELL_A"
    assert rows[0].grid_row == 1
    assert rows[0].grid_col == 1
    assert rows[0].features["ndvi"] == 0.5
    assert rows[0].scoring_metadata["top10_count"] == 2


def test_reduced_feature_row_safe_summary_has_no_feature_values_or_geometry() -> None:
    row = reduced_feature_rows_from_records([{"properties": _properties("CELL_A")}])[0]

    summary = row.safe_summary()
    serialized = json.dumps(summary, sort_keys=True)

    assert summary["cell_id"] == "CELL_A"
    assert summary["contains_feature_values"] is False
    assert summary["contains_geometry"] is False
    assert "ndvi" not in serialized
    assert "0.5" not in serialized
    assert "Polygon" not in serialized


def test_safe_reduction_summary_uses_counts_and_ids_only() -> None:
    rows = reduced_feature_rows_from_records(
        [
            {"properties": _properties("CELL_A")},
            {"properties": _properties("CELL_B", grid_row=1, grid_col=2)},
        ]
    )

    summary = safe_reduction_summary(rows)
    serialized = json.dumps(summary, sort_keys=True)

    assert summary == {
        "row_count": 2,
        "first_cell_id": "CELL_A",
        "last_cell_id": "CELL_B",
        "contains_feature_values": False,
        "contains_geometry": False,
    }
    assert "ndvi" not in serialized
    assert "Polygon" not in serialized


def test_score_reduced_v6_feature_rows_connects_reduction_to_scorer() -> None:
    rows = reduced_feature_rows_from_records(
        [
            {"properties": _properties("WARNED", v6_strong_built_frac=0.5, v6_road_like_edge_frac=0.5)},
            {"properties": _properties("CLEAN", visibility_score=0.8, spectral_contrast=0.7, terrain_score=0.9)},
        ]
    )

    scored = score_reduced_v6_feature_rows(rows)

    assert [candidate.cell_id for candidate in scored] == ["CLEAN", "WARNED"]
    assert scored[0].final_priority_rank_v6 == 1
    assert scored[1].v6_false_positive_warning_count == 2


def test_reduced_feature_rows_rejects_missing_required_band() -> None:
    props = _properties("BAD")
    props.pop("ndvi")

    with pytest.raises(ValueError, match="missing_feature:ndvi"):
        reduced_feature_rows_from_records([{"properties": props}])


def test_feature_reduction_config_validates_positive_values() -> None:
    assert V6FeatureReductionConfig(scale_m=10, tile_scale=4).scale_m == 10

    with pytest.raises(ValueError, match="positive integers"):
        V6FeatureReductionConfig(scale_m=0, tile_scale=4)
