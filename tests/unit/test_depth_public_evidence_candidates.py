from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_depth_public_evidence_candidates as candidate_validator


CANDIDATE_PATH = (
    ROOT / "docs" / "depth_public_evidence" / "controlled_site_depths_v1.json"
)


def _payload() -> dict:
    return json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))


def _write_payload(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "candidates.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_committed_public_candidate_file_is_structurally_valid_but_not_import_approved() -> None:
    result = candidate_validator.validate_candidate_file(CANDIDATE_PATH)

    assert result["status"] == "validation_passed"
    assert result["readiness_decision"] == "candidate_evidence_structurally_valid_not_import_approved"
    assert result["source_count"] == 2
    assert result["physical_site_group_count"] == 2
    assert result["candidate_record_count"] == 16
    assert result["reference_uncertainty_record_count"] == 0
    assert result["private_pack_import_approved_count"] == 0
    assert result["issue_counts"] == {}
    assert result["app_depth_enabled"] is False


def test_derived_depth_field_is_rejected(tmp_path: Path) -> None:
    payload = _payload()
    payload["sources"][0]["records"][0]["gpr_estimated_depth_m"] = 2.1

    result = candidate_validator.validate_candidate_file(_write_payload(tmp_path, payload))

    assert result["status"] == "validation_failed"
    assert result["issue_counts"] == {
        "record_contains_derived_depth_or_prohibited_input": 1
    }


def test_negative_true_depth_is_rejected(tmp_path: Path) -> None:
    payload = _payload()
    payload["sources"][0]["records"][0]["known_depth_top_m"] = -0.1

    result = candidate_validator.validate_candidate_file(_write_payload(tmp_path, payload))

    assert result["status"] == "validation_failed"
    assert result["issue_counts"] == {"known_depth_top_invalid": 1}


def test_duplicate_public_target_label_is_rejected(tmp_path: Path) -> None:
    payload = _payload()
    records = payload["sources"][0]["records"]
    records[1]["public_target_label"] = records[0]["public_target_label"]

    result = candidate_validator.validate_candidate_file(_write_payload(tmp_path, payload))

    assert result["status"] == "validation_failed"
    assert result["issue_counts"] == {"duplicate_public_target_label": 1}


def test_stale_aggregate_is_rejected(tmp_path: Path) -> None:
    payload = _payload()
    payload["aggregate"]["candidate_record_count"] = 15

    result = candidate_validator.validate_candidate_file(_write_payload(tmp_path, payload))

    assert result["status"] == "validation_failed"
    assert result["issue_counts"] == {"aggregate_candidate_record_count_mismatch": 1}


def test_premature_private_import_approval_is_rejected(tmp_path: Path) -> None:
    payload = _payload()
    source = payload["sources"][0]
    source["private_pack_import_approved"] = True
    payload["aggregate"]["private_pack_import_approved_count"] = len(source["records"])

    result = candidate_validator.validate_candidate_file(_write_payload(tmp_path, payload))

    assert result["status"] == "validation_failed"
    assert result["issue_counts"] == {
        "import_approved_without_satellite_support": 1,
        "import_approved_without_uncertainty": 1,
        "private_pack_import_must_remain_unapproved": 1,
    }


def test_output_is_aggregate_only(tmp_path: Path) -> None:
    payload = copy.deepcopy(_payload())
    path = _write_payload(tmp_path, payload)

    result = candidate_validator.validate_candidate_file(path)
    rendered = json.dumps(result, sort_keys=True)

    assert "iag_usp" not in rendered
    assert "ahmadu_bello" not in rendered
    assert '"A"' not in rendered
    assert "1.97" not in rendered
    assert str(path) not in rendered
    assert result["private_values_printed"] is False
