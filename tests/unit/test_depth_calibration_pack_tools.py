from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import finalize_depth_calibration_manifest as finalizer
import init_depth_calibration_pack as initializer
import validate_depth_calibration_pack as validator


def _copy_pack(tmp_path: Path) -> Path:
    destination = tmp_path / "private_pack"
    initializer.initialize_pack(destination, template_dir=ROOT / "templates" / "depth_calibration")
    return destination


def _valid_row(index: int, *, split: str, status: str) -> dict[str, str]:
    positive = status == "known_depth_positive"
    return {
        "schema_version": "depth_calibration_record_v1",
        "record_id": f"record_{index}",
        "site_id": f"site_{index}",
        "feature_id": f"feature_{index}",
        "group_id": f"group_{index}",
        "reference_status": status,
        "finding_family": "reference_structure" if positive else "confirmed_background",
        "known_depth_top_m": "2.0" if positive else "",
        "known_depth_bottom_m": "3.0" if positive else "",
        "depth_reference_uncertainty_m": "0.2" if positive else "",
        "depth_reference_method": "engineering_record",
        "evidence_source_type": "private_record",
        "evidence_source_reference": f"source_{index}",
        "evidence_source_version": "v1",
        "evidence_review_method": "independent_review",
        "label_quality": "reviewed_independent",
        "target_size_length_m": "1.0" if positive else "unknown",
        "target_size_width_m": "1.0" if positive else "unknown",
        "target_size_height_m": "1.0" if positive else "unknown",
        "target_material_or_structure": "documented_structure" if positive else "none",
        "soil_or_surface_type": "unknown",
        "moisture_or_season": "unknown",
        "terrain_class": "unknown",
        "observation_start": "2025-01-01",
        "observation_end": "2025-01-31",
        "sensor_sources": "S1",
        "sensor_acquisition_ids": f"acquisition_{index}",
        "pipeline_commit": "test_commit",
        "feature_manifest_version": "feature_v1",
        "split": split,
        "split_policy_version": "split_v1",
        "include_for_relative_depth": "true",
        "include_for_numerical_depth": "false",
        "exclusion_reason": "",
        "quality_notes": "synthetic test row",
        "created_at": "2026-01-01",
        "reviewed_at": "2026-01-02",
        "reviewer_reference": "reviewer_1",
    }


def _valid_rows() -> list[dict[str, str]]:
    return [
        _valid_row(1, split="train", status="known_depth_positive"),
        _valid_row(2, split="train", status="confirmed_no_target"),
        _valid_row(3, split="validation", status="known_depth_positive"),
        _valid_row(4, split="validation", status="confirmed_no_target"),
        _valid_row(5, split="holdout", status="known_depth_positive"),
        _valid_row(6, split="holdout", status="confirmed_no_target"),
    ]


def _uncertain_row(index: int, *, split: str) -> dict[str, str]:
    row = _valid_row(index, split=split, status="confirmed_no_target")
    row.update(
        {
            "reference_status": "uncertain_reference",
            "finding_family": "",
            "depth_reference_method": "",
            "evidence_source_type": "",
            "evidence_source_reference": "",
            "evidence_source_version": "",
            "evidence_review_method": "",
            "label_quality": "uncertain",
            "include_for_relative_depth": "false",
            "include_for_numerical_depth": "false",
            "reviewer_reference": "",
        }
    )
    return row


def _write_rows(pack: Path, rows: list[dict[str, str]]) -> None:
    with (pack / "calibration_records.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(validator.REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def _readiness_for_rows(rows: list[dict[str, str]]) -> tuple[str, dict[str, object]]:
    counts = validator._aggregate_counts(rows)
    decision = validator._readiness_decision(
        input_errors={},
        issues=Counter(),
        counts=counts,
        feature_manifest={"status": "frozen"},
    )
    return decision, counts


def _populate_valid_pack(pack: Path) -> None:
    rows = _valid_rows()
    _write_rows(pack, rows)

    with (pack / "source_index.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(validator.SOURCE_COLUMNS))
        writer.writeheader()
        for index in range(1, 7):
            writer.writerow(
                {
                    "source_reference": f"source_{index}",
                    "source_type": "private_record",
                    "source_version": "v1",
                    "private_location": f"private_source_{index}",
                    "review_status": "reviewed",
                    "review_notes": "synthetic test fixture",
                }
            )

    feature_manifest = json.loads((pack / "feature_manifest.json").read_text(encoding="utf-8"))
    feature_manifest.update(
        {
            "status": "frozen",
            "feature_manifest_version": "feature_v1",
            "pipeline_commit": "test_commit",
            "features": [
                {
                    "name": "VV_dB",
                    "role": "candidate_depth_signal",
                    "source": "Sentinel-1 GRD",
                    "source_fields": ["VV"],
                    "formula_or_definition": "Calibrated VV backscatter in dB",
                    "unit": "dB",
                    "spatial_resolution": "10 m app grid",
                    "nodata_behavior": "GRID nodata when source is invalid",
                    "preprocessing": "RTC and approved speckle filtering",
                    "known_confounders": ["soil moisture", "roughness", "incidence angle"],
                    "allowed_for_depth_research": True,
                    "limitation": "Sensor signal only; not a depth measurement",
                    "order": 1,
                }
            ],
        }
    )
    (pack / "feature_manifest.json").write_text(json.dumps(feature_manifest), encoding="utf-8")

    manifest = json.loads((pack / "calibration_manifest.json").read_text(encoding="utf-8"))
    manifest.update({"status": "populated_private_dataset", "dataset_id": "dataset_v1", "dataset_version": "v1"})
    (pack / "calibration_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_initializer_copies_complete_empty_pack(tmp_path: Path) -> None:
    destination = _copy_pack(tmp_path)

    assert sorted(path.name for path in destination.iterdir()) == sorted(initializer.REQUIRED_FILES)
    assert (destination / "calibration_records.csv").read_text(encoding="utf-8").count("\n") == 1


def test_initializer_rejects_nonempty_destination(tmp_path: Path) -> None:
    destination = tmp_path / "private_pack"
    destination.mkdir()
    (destination / "existing.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(initializer.PackInitError, match="not empty"):
        initializer.initialize_pack(destination, template_dir=ROOT / "templates" / "depth_calibration")


def test_initializer_rejects_repository_destination() -> None:
    with pytest.raises(initializer.PackInitError, match="outside"):
        initializer._require_outside_repo(initializer.REPO_ROOT / "private_pack", "destination")


def test_empty_pack_reports_no_records_without_leaking_rows(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)

    result = validator.validate_pack(pack)

    assert result["readiness_decision"] == "not_ready_no_records"
    assert result["record_count"] == 0
    assert result["eligible_positive_by_split"] == {"train": 0, "validation": 0, "holdout": 0}
    assert result["eligible_confirmed_negative_by_split"] == {"train": 0, "validation": 0, "holdout": 0}
    assert result["private_rows_printed"] is False
    assert "site_id" not in json.dumps(result)


def test_populated_pack_remains_blocked_until_manifest_is_finalized(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _populate_valid_pack(pack)

    result = validator.validate_pack(pack)

    assert result["status"] == "validation_failed"
    assert result["readiness_decision"] == "not_ready_contract_errors"
    assert result["record_count"] == 6
    assert result["positive_count"] == 3
    assert result["negative_count"] == 3
    assert result["eligible_positive_count"] == 3
    assert result["eligible_confirmed_negative_count"] == 3
    assert result["issue_counts"]["manifest_required_value_missing_records_sha256"] == 1
    assert result["scientific_validation_run"] is False
    assert result["training_started"] is False


def test_group_leakage_blocks_readiness(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _populate_valid_pack(pack)
    with (pack / "calibration_records.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows[2]["group_id"] = rows[0]["group_id"]
    _write_rows(pack, rows)

    result = validator.validate_pack(pack)

    assert result["readiness_decision"] == "not_ready_contract_errors"
    assert result["issue_counts"]["group_split_leakage"] == 1


def test_validator_rejects_repository_dataset_path() -> None:
    with pytest.raises(validator.PackValidationError, match="outside"):
        validator.validate_pack(validator.REPO_ROOT / "templates" / "depth_calibration")


def test_manifest_finalizer_dry_run_does_not_write(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _populate_valid_pack(pack)
    before = (pack / "calibration_manifest.json").read_text(encoding="utf-8")

    result = finalizer.finalize_manifest(
        pack,
        dataset_id="dataset_v1",
        dataset_version="v1",
        write=False,
    )

    assert result["status"] == "manifest_dry_run_ready"
    assert result["manifest_written"] is False
    assert result["eligible_positive_by_split"] == {"train": 1, "validation": 1, "holdout": 1}
    assert result["eligible_confirmed_negative_by_split"] == {"train": 1, "validation": 1, "holdout": 1}
    assert (pack / "calibration_manifest.json").read_text(encoding="utf-8") == before


def test_manifest_finalizer_writes_counts_and_hashes(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _populate_valid_pack(pack)

    result = finalizer.finalize_manifest(
        pack,
        dataset_id="dataset_v1",
        dataset_version="v1",
        write=True,
    )
    validated = validator.validate_pack(pack)
    manifest = json.loads((pack / "calibration_manifest.json").read_text(encoding="utf-8"))

    assert result["status"] == "manifest_written"
    assert result["manifest_written"] is True
    assert manifest["record_count"] == 6
    assert manifest["positive_count"] == 3
    assert manifest["negative_count"] == 3
    assert len(manifest["records_sha256"]) == 64
    assert len(manifest["content_hash"]) == 64
    assert len(manifest["manifest_hash"]) == 64
    assert validated["status"] == "validation_passed"
    assert validated["eligible_positive_by_split"] == {"train": 1, "validation": 1, "holdout": 1}
    assert validated["eligible_confirmed_negative_by_split"] == {"train": 1, "validation": 1, "holdout": 1}


def test_manifest_hash_mismatch_blocks_readiness(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _populate_valid_pack(pack)
    finalizer.finalize_manifest(pack, dataset_id="dataset_v1", dataset_version="v1", write=True)
    manifest_path = pack / "calibration_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["manifest_hash"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validator.validate_pack(pack)

    assert result["readiness_decision"] == "not_ready_contract_errors"
    assert result["issue_counts"]["manifest_manifest_hash_mismatch"] == 1


def test_incomplete_feature_manifest_entry_blocks_readiness(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _populate_valid_pack(pack)
    feature_path = pack / "feature_manifest.json"
    feature_manifest = json.loads(feature_path.read_text(encoding="utf-8"))
    feature_manifest["features"][0].pop("limitation")
    feature_path.write_text(json.dumps(feature_manifest), encoding="utf-8")

    result = validator.validate_pack(pack)

    assert result["readiness_decision"] == "not_ready_contract_errors"
    assert result["issue_counts"]["feature_manifest_entry_missing_limitation"] == 1


def test_eligible_aggregates_keep_raw_counts_and_explicit_zero_keys() -> None:
    rows = [
        _valid_row(1, split="train", status="known_depth_positive"),
        _valid_row(2, split="validation", status="confirmed_no_target"),
    ]

    counts = validator._aggregate_counts(rows)

    assert counts["positive_count"] == 1
    assert counts["negative_count"] == 1
    assert counts["eligible_positive_by_split"] == {"train": 1, "validation": 0, "holdout": 0}
    assert counts["eligible_confirmed_negative_by_split"] == {"train": 0, "validation": 1, "holdout": 0}


def test_ineligible_row_cannot_satisfy_split_requirement() -> None:
    rows = _valid_rows()[:4] + [_uncertain_row(7, split="holdout")]

    decision, counts = _readiness_for_rows(rows)

    assert counts["split_counts"]["holdout"] == 1
    assert counts["eligible_positive_by_split"]["holdout"] == 0
    assert counts["eligible_confirmed_negative_by_split"]["holdout"] == 0
    assert decision == "not_ready_missing_eligible_split_coverage"


def test_non_included_rows_cannot_reach_readiness() -> None:
    rows = _valid_rows()
    for row in rows:
        row["include_for_relative_depth"] = "false"

    decision, counts = _readiness_for_rows(rows)

    assert counts["positive_count"] == 3
    assert counts["negative_count"] == 3
    assert counts["eligible_positive_count"] == 0
    assert decision == "not_ready_no_eligible_positive_records"


def test_weak_quality_positive_cannot_satisfy_eligible_positive_gate() -> None:
    rows = _valid_rows()
    for row in rows:
        if row["reference_status"] == "known_depth_positive":
            row["label_quality"] = "weak_or_proxy"

    decision, counts = _readiness_for_rows(rows)

    assert counts["positive_count"] == 3
    assert counts["eligible_positive_count"] == 0
    assert decision == "not_ready_no_eligible_positive_records"


def test_no_eligible_confirmed_negative_records_is_distinct() -> None:
    rows = _valid_rows()
    for row in rows:
        if row["reference_status"] == "confirmed_no_target":
            row["include_for_relative_depth"] = "false"

    decision, counts = _readiness_for_rows(rows)

    assert counts["eligible_positive_count"] == 3
    assert counts["eligible_confirmed_negative_count"] == 0
    assert decision == "not_ready_no_eligible_confirmed_negative_records"


def test_single_class_split_blocks_readiness() -> None:
    rows = [row for row in _valid_rows() if row["record_id"] != "record_6"]

    decision, counts = _readiness_for_rows(rows)

    assert counts["eligible_positive_by_split"]["holdout"] == 1
    assert counts["eligible_confirmed_negative_by_split"]["holdout"] == 0
    assert decision == "not_ready_missing_eligible_split_coverage"


def test_valid_rows_satisfy_eligible_gate() -> None:
    decision, counts = _readiness_for_rows(_valid_rows())

    assert counts["eligible_positive_count"] == 3
    assert counts["eligible_confirmed_negative_count"] == 3
    assert decision == "ready_for_relative_depth_research"


def test_finalizer_refuses_missing_eligible_split_coverage_without_writing(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _populate_valid_pack(pack)
    _write_rows(pack, _valid_rows()[:4] + [_uncertain_row(7, split="holdout")])
    manifest_path = pack / "calibration_manifest.json"
    before = manifest_path.read_text(encoding="utf-8")

    with pytest.raises(
        finalizer.ManifestFinalizeError,
        match="each active split requires at least one eligible positive and one eligible confirmed-negative record",
    ):
        finalizer.finalize_manifest(pack, dataset_id="dataset_v1", dataset_version="v1", write=True)

    assert manifest_path.read_text(encoding="utf-8") == before
