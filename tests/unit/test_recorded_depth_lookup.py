from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from app.pipeline.depth.loader import load_depth_package
from app.pipeline.depth.recorded import (
    RECORDED_METHOD_KIND,
    RecordedDepthPackage,
    RecordedDepthPackageError,
    load_recorded_depth_package,
)
from app.pipeline.stages.depth_estimation import write_depth_outputs
from scripts.build_tyrone_recorded_depth_package import (
    build_tyrone_recorded_depth_package,
)
from scripts.run_recorded_depth_lookup_for_existing_run import (
    run_recorded_depth_lookup_for_existing_run,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_candidates(path: Path, candidates: list[dict[str, str]]) -> None:
    _write_json(
        path,
        {
            "schema_version": "local_depth_candidates_v1",
            "candidates": candidates,
        },
    )


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_tyrone_builder_creates_reviewed_recorded_measurements(tmp_path: Path) -> None:
    package_dir = tmp_path / "recorded"
    result = build_tyrone_recorded_depth_package(package_dir)
    package = load_depth_package(package_dir)

    assert isinstance(package, RecordedDepthPackage)
    assert result["method_kind"] == RECORDED_METHOD_KIND
    assert result["zone_count"] == 2
    assert package.review_status == "reviewed"

    tp5 = package.zone("tyrone_tp5")
    assert tp5 is not None
    assert tp5.measurement.mean_m == pytest.approx(0.68072)
    assert tp5.measurement.ci95_low_m == pytest.approx(0.65532)
    assert tp5.measurement.ci95_high_m == pytest.approx(0.70612)
    assert tp5.measurement.sample_min_m == pytest.approx(0.6604)
    assert tp5.measurement.sample_max_m == pytest.approx(0.7112)
    assert tp5.measurement.sample_count == 5
    assert tp5.measurement.reported_design_depth_m == pytest.approx(0.6096)
    assert tp5.measurement.measurement_method == "five confirmation pits"
    assert tp5.measurement.measurement_timing == "after cover placement and before seeding"
    assert tp5.measurement.measurement_date == ""

    tp6 = package.zone("tyrone_tp6")
    assert tp6 is not None
    assert tp6.measurement.mean_m == pytest.approx(0.94996)
    assert tp6.measurement.sample_min_m == pytest.approx(0.8636)
    assert tp6.measurement.sample_max_m == pytest.approx(1.0668)
    assert tp6.measurement.reported_design_depth_m == pytest.approx(0.9144)


def test_exact_recorded_zone_writes_record_fields_not_estimate_fields(tmp_path: Path) -> None:
    package_dir = tmp_path / "recorded"
    build_tyrone_recorded_depth_package(package_dir)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_candidates(
        run_dir / "depth_inputs" / "candidates.json",
        [{"candidate_id": "tp5-reviewed", "zone_id": "tyrone_tp5"}],
    )
    _write_json(
        run_dir / "QA" / "run_quality" / "run_quality_summary.json",
        {
            "schema": "run_quality_summary_v1",
            "stage": "run_quality",
            "status": "BLOCKED",
            "is_usable": False,
        },
    )

    paths, summary = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    row = _read_rows(paths.estimates_csv)[0]

    assert summary["status"] == "recorded_measurement"
    assert summary["recorded_measurement_count"] == 1
    assert summary["estimated_count"] == 0
    assert summary["method_kind"] == RECORDED_METHOD_KIND
    assert summary["record_dataset_version"] == "tyrone-3x-confirmation-pits-2026-07-29"
    assert "run_quality_not_supported" not in summary["warnings"]

    assert row["depth_status"] == "recorded_measurement"
    assert row["estimated_depth_min_m"] == ""
    assert row["estimated_depth_best_m"] == ""
    assert row["estimated_depth_max_m"] == ""
    assert row["recorded_depth_mean_m"] == "0.680720"
    assert row["recorded_depth_ci95_low_m"] == "0.655320"
    assert row["recorded_depth_ci95_high_m"] == "0.706120"
    assert row["recorded_sample_min_m"] == "0.660400"
    assert row["recorded_sample_max_m"] == "0.711200"
    assert row["recorded_sample_count"] == "5"
    assert row["reported_design_depth_m"] == "0.609600"
    assert row["measurement_source"] == "official 2006 3X as-built report"
    assert row["measurement_date"] == ""
    assert row["measurement_method"] == "five confirmation pits"
    assert row["measurement_timing"] == "after cover placement and before seeding"
    assert row["depth_quality"] == "recorded_reviewed"
    assert "no_predictive_extrapolation" in row["warnings"]


def test_unknown_zone_abstains_without_any_metre_values(tmp_path: Path) -> None:
    package_dir = tmp_path / "recorded"
    build_tyrone_recorded_depth_package(package_dir)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_candidates(
        run_dir / "depth_inputs" / "candidates.json",
        [{"candidate_id": "unknown", "zone_id": "not-reviewed"}],
    )

    paths, summary = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    row = _read_rows(paths.estimates_csv)[0]

    assert summary["status"] == "not_available"
    assert summary["recorded_measurement_count"] == 0
    assert summary["estimated_count"] == 0
    assert row["depth_status"] == "not_available"
    assert row["estimated_depth_best_m"] == ""
    assert row["recorded_depth_mean_m"] == ""
    assert row["reported_design_depth_m"] == ""
    assert "no_recorded_measurement_for_zone" in row["warnings"]
    assert "no_predictive_extrapolation" in row["warnings"]


def test_recorded_lookup_runner_is_end_to_end(tmp_path: Path) -> None:
    package_dir = tmp_path / "recorded"
    build_tyrone_recorded_depth_package(package_dir)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    candidates_path = tmp_path / "candidates.json"
    _write_candidates(
        candidates_path,
        [{"candidate_id": "tp6-reviewed", "zone_id": "tyrone_tp6"}],
    )

    result = run_recorded_depth_lookup_for_existing_run(
        run_dir=run_dir,
        package_dir=package_dir,
        candidate_input=candidates_path,
    )

    assert result["status"] == "recorded_measurement"
    assert result["recorded_measurement_count"] == 1
    assert result["estimated_count"] == 0
    assert result["method_kind"] == RECORDED_METHOD_KIND
    rows = _read_rows(run_dir / "depth" / "depth_estimates.csv")
    assert rows[0]["recorded_depth_mean_m"] == "0.949960"
    assert rows[0]["estimated_depth_best_m"] == ""


def test_recorded_package_checksum_is_enforced(tmp_path: Path) -> None:
    package_dir = tmp_path / "recorded"
    build_tyrone_recorded_depth_package(package_dir)
    manifest_path = package_dir / "depth_method_manifest.json"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    with pytest.raises(RecordedDepthPackageError, match="checksum mismatch"):
        load_recorded_depth_package(package_dir)
