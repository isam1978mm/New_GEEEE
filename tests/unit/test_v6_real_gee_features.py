from __future__ import annotations

import json

import pytest

from app.services.v6_real_gee_features import (
    DEM_IMAGE_ID,
    DYNAMIC_WORLD_COLLECTION_ID,
    REQUIRED_V6_FEATURE_BANDS,
    SENTINEL2_COLLECTION_ID,
    SURFACE_WATER_IMAGE_ID,
    V6FeatureLayerConfig,
    build_v6_feature_stack_plan,
    validate_v6_feature_row,
)


def _valid_feature_row() -> dict[str, float]:
    return {band: 0.5 for band in REQUIRED_V6_FEATURE_BANDS}


def test_feature_layer_config_validates_dates_and_thresholds() -> None:
    config = V6FeatureLayerConfig(start_date="2020-01-01", end_date="2020-12-31")

    assert config.start_date == "2020-01-01"
    assert config.end_date == "2020-12-31"
    assert config.sentinel_cloud_pct_max == 40

    with pytest.raises(ValueError, match="start_date must be earlier"):
        V6FeatureLayerConfig(start_date="2020-12-31", end_date="2020-01-01")

    with pytest.raises(ValueError, match="between 0 and 100"):
        V6FeatureLayerConfig(start_date="2020-01-01", end_date="2020-12-31", sentinel_cloud_pct_max=101)

    with pytest.raises(ValueError, match="between 0 and 1"):
        V6FeatureLayerConfig(start_date="2020-01-01", end_date="2020-12-31", dynamic_world_built_threshold=1.1)


def test_feature_stack_plan_lists_sources_and_required_bands_without_values() -> None:
    plan = build_v6_feature_stack_plan()

    assert SENTINEL2_COLLECTION_ID in plan.dataset_ids
    assert DEM_IMAGE_ID in plan.dataset_ids
    assert SURFACE_WATER_IMAGE_ID in plan.dataset_ids
    assert DYNAMIC_WORLD_COLLECTION_ID in plan.dataset_ids
    assert "ndvi" in plan.required_bands
    assert "bsi" in plan.required_bands
    assert "v6_modern_corridor_frac" in plan.required_bands

    summary = plan.safe_summary()
    serialized = json.dumps(summary, sort_keys=True)
    assert summary["contains_feature_values"] is False
    assert "0.5" not in serialized


def test_validate_v6_feature_row_accepts_complete_numeric_row() -> None:
    assert validate_v6_feature_row(_valid_feature_row()) == ()


def test_validate_v6_feature_row_reports_missing_and_bad_values() -> None:
    row = _valid_feature_row()
    row.pop("ndvi")
    row["bsi"] = "not-a-number"
    row["slope_deg"] = float("nan")

    issues = validate_v6_feature_row(row)

    assert "missing_feature:ndvi" in issues
    assert "non_numeric_feature:bsi" in issues
    assert "non_finite_feature:slope_deg" in issues


def test_required_feature_band_schema_has_no_duplicate_names() -> None:
    assert len(REQUIRED_V6_FEATURE_BANDS) == len(set(REQUIRED_V6_FEATURE_BANDS))
