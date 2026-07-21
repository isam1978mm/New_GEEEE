from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.services.v6_real_gee_features import REQUIRED_V6_FEATURE_BANDS
from app.services.v6_real_reduce import (
    MEAN_REDUCED_FEATURE_BANDS,
    MODE_REDUCED_FEATURE_BANDS,
    V6FeatureReductionConfig,
    V6FeatureStackReducer,
    merge_reduced_feature_records,
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


class _FakeReducerFactory:
    @staticmethod
    def mean() -> str:
        return "mean"

    @staticmethod
    def mode() -> str:
        return "mode"


class _FakeGeometry:
    @staticmethod
    def Rectangle(bounds, proj=None, geodesic=False):
        return {
            "bounds": tuple(bounds),
            "proj": proj,
            "geodesic": geodesic,
        }


class _FakeEE:
    Reducer = _FakeReducerFactory
    Geometry = _FakeGeometry

    @staticmethod
    def Feature(geometry, properties):
        return {
            "type": "Feature",
            "geometry": geometry,
            "properties": dict(properties),
        }

    @staticmethod
    def FeatureCollection(features):
        return tuple(features)


class _FakeRuntime:
    def initialize(self):
        return _FakeEE()


class _FakeReductionResponse:
    def __init__(self, records):
        self._records = records

    def getInfo(self):
        return {"features": self._records}


class _FakeSelectedStack:
    def __init__(self, parent, bands):
        self.parent = parent
        self.bands = tuple(bands)

    def reduceRegions(self, *, collection, reducer, scale, tileScale):
        self.parent.reduce_calls.append(
            {
                "bands": self.bands,
                "reducer": reducer,
                "scale": scale,
                "tile_scale": tileScale,
            }
        )
        records = []
        for feature in collection:
            properties = dict(feature["properties"])
            if reducer == "mean":
                properties.update({band: 0.5 for band in self.bands})
            elif reducer == "mode":
                properties.update({band: 50 for band in self.bands})
            else:
                raise AssertionError(f"unexpected reducer:{reducer}")
            records.append(
                {
                    "type": "Feature",
                    "geometry": feature["geometry"],
                    "properties": properties,
                }
            )
        return _FakeReductionResponse(records)


class _FakeFeatureStack:
    def __init__(self):
        self.select_calls = []
        self.reduce_calls = []

    def select(self, bands):
        self.select_calls.append(tuple(bands))
        return _FakeSelectedStack(self, bands)


def _grid_cell(cell_id: str = "CELL_A"):
    return SimpleNamespace(
        cell_id=cell_id,
        row=1,
        col=2,
        bounds=SimpleNamespace(west=0.0, south=0.0, east=1.0, north=1.0),
    )


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


def test_feature_stack_reducer_uses_mean_for_continuous_and_mode_for_worldcover() -> None:
    feature_stack = _FakeFeatureStack()
    reducer = V6FeatureStackReducer(_FakeRuntime())

    rows = reducer.reduce_to_rows(feature_stack=feature_stack, grid_cells=(_grid_cell(),))

    assert feature_stack.select_calls == [
        MEAN_REDUCED_FEATURE_BANDS,
        MODE_REDUCED_FEATURE_BANDS,
    ]
    assert feature_stack.reduce_calls == [
        {
            "bands": MEAN_REDUCED_FEATURE_BANDS,
            "reducer": "mean",
            "scale": 10,
            "tile_scale": 4,
        },
        {
            "bands": MODE_REDUCED_FEATURE_BANDS,
            "reducer": "mode",
            "scale": 10,
            "tile_scale": 4,
        },
    ]
    assert rows[0].cell_id == "CELL_A"
    assert rows[0].grid_row == 1
    assert rows[0].grid_col == 2
    assert rows[0].features["worldcover_class"] == 50.0


def test_merge_reduced_feature_records_uses_mode_value_not_fractional_mean() -> None:
    mean_properties = _properties("CELL_A", worldcover_class=45.0)
    mean_properties.pop("worldcover_class")
    mode_properties = {
        "cell_id": "CELL_A",
        "grid_row": 1,
        "grid_col": 1,
        "worldcover_class": 50,
    }

    merged = merge_reduced_feature_records(
        [{"properties": mean_properties}],
        [{"properties": mode_properties}],
    )

    assert merged[0]["properties"]["worldcover_class"] == 50


def test_merge_reduced_feature_records_rejects_missing_categorical_cell() -> None:
    mean_properties = _properties("CELL_A")
    mean_properties.pop("worldcover_class")

    with pytest.raises(ValueError, match="categorical mode reduction is missing cell_id:CELL_A"):
        merge_reduced_feature_records(
            [{"properties": mean_properties}],
            [{"properties": {"cell_id": "CELL_B", "worldcover_class": 40}}],
        )


def test_merge_reduced_feature_records_rejects_duplicate_categorical_cell() -> None:
    mode_record = {"properties": {"cell_id": "CELL_A", "worldcover_class": 50}}

    with pytest.raises(ValueError, match="duplicate cell_id:CELL_A"):
        merge_reduced_feature_records([], [mode_record, mode_record])


def test_merge_reduced_feature_records_rejects_grid_identity_mismatch() -> None:
    mean_properties = _properties("CELL_A")
    mean_properties.pop("worldcover_class")

    with pytest.raises(ValueError, match="reduction grid identity mismatch:CELL_A:grid_row"):
        merge_reduced_feature_records(
            [{"properties": mean_properties}],
            [
                {
                    "properties": {
                        "cell_id": "CELL_A",
                        "grid_row": 9,
                        "grid_col": 1,
                        "worldcover_class": 50,
                    }
                }
            ],
        )
