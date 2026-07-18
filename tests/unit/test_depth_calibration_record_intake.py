from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import add_depth_calibration_record as intake
import init_depth_calibration_pack as initializer
import validate_depth_calibration_pack as validator


def _copy_pack(tmp_path: Path) -> Path:
    destination = tmp_path / "private_pack"
    initializer.initialize_pack(destination, template_dir=ROOT / "templates" / "depth_calibration")
    return destination


def _record(index: int = 1) -> dict[str, str]:
    return {
        "schema_version": "depth_calibration_record_v1",
        "record_id": f"record_{index}",
        "site_id": f"site_{index}",
        "feature_id": f"feature_{index}",
        "group_id": f"group_{index}",
        "reference_status": "known_depth_positive",
        "finding_family": "reference_structure",
        "known_depth_top_m": "2.0",
        "known_depth_bottom_m": "3.0",
        "depth_reference_uncertainty_m": "0.2",
        "depth_reference_method": "engineering_record",
        "evidence_source_type": "private_record",
        "evidence_source_reference": f"source_{index}",
        "evidence_source_version": "v1",
        "evidence_review_method": "independent_review",
        "label_quality": "reviewed_independent",
        "target_size_length_m": "1.0",
        "target_size_width_m": "1.0",
        "target_size_height_m": "1.0",
        "target_material_or_structure": "documented_structure",
        "soil_or_surface_type": "unknown",
        "moisture_or_season": "unknown",
        "terrain_class": "unknown",
        "observation_start": "2025-01-01",
        "observation_end": "2025-01-31",
        "sensor_sources": "S1",
        "sensor_acquisition_ids": f"acquisition_{index}",
        "pipeline_commit": "test_commit",
        "feature_manifest_version": "feature_v1",
        "split": "train",
        "split_policy_version": "split_v1",
        "include_for_relative_depth": "false",
        "include_for_numerical_depth": "false",
        "exclusion_reason": "",
        "quality_notes": "synthetic test fixture",
        "created_at": "2026-01-01",
        "reviewed_at": "2026-01-02",
        "reviewer_reference": "reviewer_1",
    }


def _source(index: int = 1) -> dict[str, str]:
    return {
        "source_reference": f"source_{index}",
        "source_type": "private_record",
        "source_version": "v1",
        "private_location": f"private_source_{index}",
        "review_status": "reviewed",
        "review_notes": "synthetic test fixture",
    }


def _write_payload(path: Path, *, record: dict[str, str] | None = None, source: dict[str, str] | None = None) -> None:
    payload = {"record": record or _record(), "source": source}
    path.write_text(json.dumps(payload), encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_source_index(pack: Path, rows: list[dict[str, str]]) -> None:
    with (pack / "source_index.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(validator.SOURCE_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def test_create_blank_payload_writes_only_blank_private_template(tmp_path: Path) -> None:
    payload_path = tmp_path / "record_intake.json"

    result = intake.create_blank_payload(payload_path)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    assert result["status"] == "blank_private_intake_payload_created"
    assert set(payload["record"]) == set(validator.REQUIRED_COLUMNS)
    assert set(payload["source"]) == set(validator.SOURCE_COLUMNS)
    assert all(value == "" for value in payload["record"].values())
    assert all(value == "" for value in payload["source"].values())


def test_dry_run_validates_without_writing_or_leaking_values(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    payload_path = pack / "record_intake.json"
    _write_payload(payload_path, record=_record(), source=_source())
    records_before = (pack / "calibration_records.csv").read_text(encoding="utf-8")
    sources_before = (pack / "source_index.csv").read_text(encoding="utf-8")

    result = intake.intake_record(pack, payload_path, write=False)
    rendered = json.dumps(result)

    assert result["status"] == "private_depth_record_dry_run_ready"
    assert result["record_written"] is False
    assert result["source_written"] is False
    assert (pack / "calibration_records.csv").read_text(encoding="utf-8") == records_before
    assert (pack / "source_index.csv").read_text(encoding="utf-8") == sources_before
    assert "record_1" not in rendered
    assert "source_1" not in rendered
    assert "2.0" not in rendered
    assert str(pack) not in rendered


def test_write_appends_record_and_source_and_invalidates_manifest(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    payload_path = pack / "record_intake.json"
    _write_payload(payload_path, record=_record(), source=_source())

    result = intake.intake_record(pack, payload_path, write=True)
    manifest = json.loads((pack / "calibration_manifest.json").read_text(encoding="utf-8"))

    assert result["status"] == "private_depth_record_written"
    assert result["record_written"] is True
    assert result["source_written"] is True
    assert len(_read_csv(pack / "calibration_records.csv")) == 1
    assert len(_read_csv(pack / "source_index.csv")) == 1
    assert manifest["status"] == intake.MANIFEST_INVALIDATED_STATUS
    assert manifest["record_count"] is None
    assert manifest["records_sha256"] is None
    assert manifest["manifest_hash"] is None


def test_existing_identical_source_is_reused_without_duplicate(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _write_source_index(pack, [_source()])
    payload_path = pack / "record_intake.json"
    _write_payload(payload_path, record=_record(), source=None)

    result = intake.intake_record(pack, payload_path, write=True)

    assert result["source_written"] is False
    assert result["source_count_before"] == 1
    assert result["source_count_after"] == 1
    assert len(_read_csv(pack / "source_index.csv")) == 1


def test_duplicate_record_identifier_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    payload_path = pack / "record_intake.json"
    _write_payload(payload_path, record=_record(), source=_source())
    intake.intake_record(pack, payload_path, write=True)

    with pytest.raises(intake.DepthRecordIntakeError, match="record identifier already exists"):
        intake.intake_record(pack, payload_path, write=False)


def test_missing_source_linkage_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    payload_path = pack / "record_intake.json"
    _write_payload(payload_path, record=_record(), source=None)

    with pytest.raises(intake.DepthRecordIntakeError, match="source index"):
        intake.intake_record(pack, payload_path, write=False)


def test_coordinate_like_identifier_is_rejected_by_existing_contract(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    payload_path = pack / "record_intake.json"
    record = _record()
    record["site_id"] = "35.1234, 44.1234"
    _write_payload(payload_path, record=record, source=_source())

    with pytest.raises(intake.DepthRecordIntakeError, match="identifier_looks_coordinate_bearing"):
        intake.intake_record(pack, payload_path, write=False)


def test_repository_payload_path_is_rejected() -> None:
    with pytest.raises(validator.PackValidationError, match="outside"):
        intake.create_blank_payload(ROOT / "record_intake.json")
