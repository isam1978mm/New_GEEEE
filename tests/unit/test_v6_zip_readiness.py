from __future__ import annotations

import json
import zipfile

from app.services.v6_real_gee_runtime import V6GridConfig, build_v6_grid, validate_v6_aoi_bounds
from app.services.v6_real_package import V6RealPackageInputs, generate_v6_package_from_real_outputs
from app.services.v6_real_scoring import V6ScoredCandidate
from app.services.v6_real_zones import generate_v6_request_zones
from app.services.v6_zip_readiness import ZIP_READINESS_CONTRACT, build_v6_zip_readiness_report


def test_real_package_validation_report_exposes_zip_readiness_contract(tmp_path) -> None:
    result = generate_v6_package_from_real_outputs(output_dir=tmp_path, package_inputs=_package_inputs())

    report = json.loads((tmp_path / "V6_REAL_GENERATED_validation_20260103T010203Z.json").read_text())

    assert result.is_verified is True
    assert report["zip_ready"] is True
    assert report["zip_readiness"]["contract"] == ZIP_READINESS_CONTRACT
    assert report["zip_readiness"]["zip_ready"] is True
    assert report["zip_readiness"]["expected_payload_count"] == 12
    assert report["zip_readiness"]["expected_zip_entry_count"] == 13
    assert report["zip_readiness"]["zip_entry_count"] == 13
    assert report["zip_readiness"]["issues"] == []


def test_zip_readiness_blocks_inventory_entry_mismatch(tmp_path) -> None:
    result = generate_v6_package_from_real_outputs(output_dir=tmp_path, package_inputs=_package_inputs())
    inventory_path = tmp_path / "V6_REAL_GENERATED_inventory_20260103T010203Z.json"
    original_zip_path = tmp_path / "V6_REAL_GENERATED_20260103T010203Z.zip"
    tampered_zip_path = tmp_path / "tampered.zip"

    with zipfile.ZipFile(original_zip_path, "r") as original, zipfile.ZipFile(tampered_zip_path, "w") as tampered:
        for name in original.namelist():
            if name == inventory_path.name:
                tampered.writestr(name, b"{}")
            else:
                tampered.writestr(name, original.read(name))

    sidecar_inventory = json.loads(inventory_path.read_text())
    readiness = build_v6_zip_readiness_report(
        zip_path=tampered_zip_path,
        inventory_path=inventory_path,
        payload_records=sidecar_inventory["records"],
    )

    assert result.is_verified is True
    assert readiness["zip_ready"] is False
    assert "zip_inventory_entry_mismatch" in readiness["issues"]


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
