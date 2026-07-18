from __future__ import annotations

import csv
import json
import sys
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


def _populate_valid_pack(pack: Path) -> None:
    rows = [
        _valid_row(1, split="train", status="known_depth_positive"),
        _valid_row(2, split="train", status="confirmed_no_target"),
        _valid_row(3, split="validation", status="known_depth_positive"),
        _valid_row(4, split="validation", status="confirmed_no_target"),
        _valid_row(5, split="holdout", status="known_depth_positive"),
        _valid_row(6, split="holdout", status="confirmed_no_target"),
    ]
    with (pack / "calibration_records.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(validator.REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

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
            "features": [{"name": "VV_dB", "unit": "dB", "order": 1}],
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
    assert result["private_rows_printed"] is False
    assert "site_id" not in json.dumps(result)


def test_valid_synthetic_pack_passes_contract_validation(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _populate_valid_pack(pack)

    result = validator.validate_pack(pack)

    assert result["status"] == "validation_passed"
    assert result["readiness_decision"] == "ready_for_relative_depth_research"
    assert result["record_count"] == 6
    assert result["positive_count"] == 3
    assert result["negative_count"] == 3
    assert result["issue_counts"] == {}
    assert result["scientific_validation_run"] is False
    assert result["training_started"] is False


def test_group_leakage_blocks_readiness(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _populate_valid_pack(pack)
    with (pack / "calibration_records.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows[2]["group_id"] = rows[0]["group_id"]
    with (pack / "calibration_records.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(validator.REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

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
