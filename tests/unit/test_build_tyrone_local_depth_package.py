from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from app.pipeline.depth.package import load_local_depth_package
from app.pipeline.stages.depth_estimation import write_depth_outputs
from scripts.build_tyrone_local_depth_package import (
    TYRONE_REVIEWED_ZONES,
    build_tyrone_local_depth_package,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def test_builder_creates_loadable_six_zone_route_a_package(tmp_path: Path) -> None:
    package_dir = tmp_path / "private" / "tyrone-depth"
    result = build_tyrone_local_depth_package(package_dir)
    package = load_local_depth_package(package_dir)

    assert result["zone_count"] == 6
    assert package.method_version == "tyrone-local-six-zone-v1"
    assert package.validation_status == "provisional"
    assert set(package.zones) == {
        "tyrone_tp1", "tyrone_tp2", "tyrone_tp3", "tyrone_tp5", "tyrone_tp6", "tyrone_tp7"
    }
    assert package.zone("tyrone_tp1").depth_range.best_m == pytest.approx(0.70612)
    assert package.zone("tyrone_tp2").depth_range.best_m == pytest.approx(0.94996)
    assert package.zone("tyrone_tp3").depth_range.best_m == pytest.approx(1.28016)
    assert package.zone("tyrone_tp5").depth_range.best_m == pytest.approx(0.68072)
    assert package.zone("tyrone_tp6").depth_range.minimum_m == pytest.approx(0.85090)
    assert package.zone("tyrone_tp6").depth_range.best_m == pytest.approx(0.94996)
    assert package.zone("tyrone_tp6").depth_range.maximum_m == pytest.approx(1.04902)
    assert package.zone("tyrone_tp7").depth_range.best_m == pytest.approx(1.30556)
    assert "not_transferable" in package.warnings
    assert "not_physical_confirmation" in package.warnings

    manifest_text = (package_dir / "depth_method_manifest.json").read_text(encoding="utf-8")
    assert "coordinate" not in manifest_text.casefold()
    assert "polygon" not in manifest_text.casefold()
    assert "private source" not in manifest_text.casefold()


def test_six_zone_ranges_use_only_frozen_ci_or_measured_envelope() -> None:
    by_zone = {zone["zone_id"]: zone for zone in TYRONE_REVIEWED_ZONES}
    assert "official_95pct_confidence_interval" in by_zone["tyrone_tp5"]["warnings"]
    assert "official_95pct_confidence_interval" in by_zone["tyrone_tp6"]["warnings"]
    for zone_id in ("tyrone_tp1", "tyrone_tp2", "tyrone_tp3", "tyrone_tp7"):
        assert "measured_sample_envelope" in by_zone[zone_id]["warnings"]


def test_route_a_writes_calibrated_range_and_abstains_outside_zone(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    build_tyrone_local_depth_package(package_dir)
    run_dir = tmp_path / "run"
    _write_json(
        run_dir / "QA" / "run_quality" / "run_quality_summary.json",
        {"schema": "run_quality_summary_v1", "stage": "run_quality", "status": "PASS", "is_usable": True},
    )
    _write_json(
        run_dir / "depth_inputs" / "candidates.json",
        {
            "schema_version": "local_depth_candidates_v1",
            "candidates": [
                {"candidate_id": "inside-tp6", "zone_id": "tyrone_tp6"},
                {"candidate_id": "outside", "zone_id": "outside_reviewed_tyrone_zones"},
            ],
        },
    )

    paths, summary = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    with paths.estimates_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert summary["status"] == "calibrated_range"
    assert summary["estimated_count"] == 1
    assert summary["not_available_count"] == 1
    assert rows[0]["depth_status"] == "calibrated_range"
    assert rows[0]["estimated_depth_min_m"] == "0.850900"
    assert rows[0]["estimated_depth_best_m"] == "0.949960"
    assert rows[0]["estimated_depth_max_m"] == "1.049020"
    assert rows[0]["depth_quality"] == "provisional_local"
    assert rows[1]["depth_status"] == "not_available"
    assert rows[1]["estimated_depth_best_m"] == ""


def test_builder_refuses_nonempty_directory_without_force(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "unrelated.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError, match="not empty"):
        build_tyrone_local_depth_package(package_dir)
    result = build_tyrone_local_depth_package(package_dir, force=True)
    assert result["status"] == "created"
    assert (package_dir / "unrelated.txt").read_text(encoding="utf-8") == "keep"
