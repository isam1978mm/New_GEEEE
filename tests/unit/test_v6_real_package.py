from __future__ import annotations

import json
import zipfile

import pytest

from app.services.v6_real_gee_runtime import V6GridConfig, build_v6_grid, validate_v6_aoi_bounds
from app.services.v6_real_package import (
    V6RealPackageInputs,
    build_v6_payloads_from_real_outputs,
    generate_v6_package_from_real_outputs,
)
from app.services.v6_real_scoring import V6ScoredCandidate
from app.services.v6_real_zones import generate_v6_request_zones


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


def _package_inputs() -> V6RealPackageInputs:
    aoi = validate_v6_aoi_bounds(west=0, south=10, east=2, north=12)
    grid = build_v6_grid(aoi=aoi, config=V6GridConfig(rows=2, cols=2))
    candidates = (
        _candidate("V6_CELL_R001_C001", 1, score=0.91),
        _candidate("V6_CELL_R001_C002", 2, score=0.72, warnings=1),
    )
    zones = generate_v6_request_zones(candidates, grid)
    return V6RealPackageInputs(
        run_id="REAL_RUN_FIXTURE_001",
        timestamp="20260103T010203Z",
        scored_candidates=candidates,
        request_zones=zones,
    )


def test_build_v6_payloads_from_real_outputs_contains_real_rows_and_zone_payloads() -> None:
    payloads = build_v6_payloads_from_real_outputs(package_inputs=_package_inputs())

    assert "lawful_gee_candidate_scout_top_25_20260103T010203Z.csv" in payloads
    assert "lawful_gee_candidate_scout_top_25_20260103T010203Z.geojson" in payloads
    assert "top25_enhanced_v6.csv" in payloads
    assert "request_zones_v6.csv" in payloads
    assert "request_zones_v6.geojson" in payloads

    top_csv = payloads["lawful_gee_candidate_scout_top_25_20260103T010203Z.csv"].decode("utf-8")
    assert "V6_CELL_R001_C001" in top_csv
    assert "v6_review_priority_score" in top_csv

    zones_csv = payloads["request_zones_v6.csv"].decode("utf-8")
    assert "primary_cell_id" in zones_csv
    assert "V6_RZ_001" in zones_csv
    assert "V6_QUOTE_001" in zones_csv

    zone_geojson = json.loads(payloads["request_zones_v6.geojson"].decode("utf-8"))
    assert zone_geojson["type"] == "FeatureCollection"
    assert len(zone_geojson["features"]) == 2


def test_generate_v6_package_from_real_outputs_writes_zip_inventory_and_report(tmp_path) -> None:
    result = generate_v6_package_from_real_outputs(
        output_dir=tmp_path,
        package_inputs=_package_inputs(),
    )

    assert result.is_verified is True
    assert result.payload_count == 12
    assert result.zip_entry_count == 13
    assert result.issues == ()
    assert result.category_counts["candidate_tables"] == 5
    assert result.category_counts["request_zones"] == 2
    assert result.category_counts["quote_templates"] == 2

    with zipfile.ZipFile(result.zip_path) as archive:
        names = set(archive.namelist())
        assert "request_zones_v6.geojson" in names
        assert "V6_REAL_GENERATED_inventory_20260103T010203Z.json" in names
        request_zones = json.loads(archive.read("request_zones_v6.geojson").decode("utf-8"))
        assert request_zones["type"] == "FeatureCollection"
        assert len(request_zones["features"]) == 2

    validation_report = json.loads((tmp_path / "V6_REAL_GENERATED_validation_20260103T010203Z.json").read_text())
    assert validation_report["real_output_feed"] is True
    assert validation_report["input_run_id"] == "REAL_RUN_FIXTURE_001"


def test_real_package_cli_summary_is_safe_metadata_only(tmp_path) -> None:
    result = generate_v6_package_from_real_outputs(
        output_dir=tmp_path,
        package_inputs=_package_inputs(),
    )

    summary = result.cli_summary()
    serialized = json.dumps(summary, sort_keys=True)

    assert summary["payload_count"] == 12
    assert "V6_CELL_R001_C001" not in serialized
    assert "coordinates" not in serialized
    assert "features" not in serialized


def test_v6_real_package_inputs_validates_required_values() -> None:
    inputs = _package_inputs()

    with pytest.raises(ValueError, match="run_id is required"):
        V6RealPackageInputs(
            run_id="",
            timestamp=inputs.timestamp,
            scored_candidates=inputs.scored_candidates,
            request_zones=inputs.request_zones,
        )

    with pytest.raises(ValueError, match="timestamp"):
        V6RealPackageInputs(
            run_id=inputs.run_id,
            timestamp="bad",
            scored_candidates=inputs.scored_candidates,
            request_zones=inputs.request_zones,
        )

    with pytest.raises(ValueError, match="scored_candidates"):
        V6RealPackageInputs(
            run_id=inputs.run_id,
            timestamp=inputs.timestamp,
            scored_candidates=(),
            request_zones=inputs.request_zones,
        )
