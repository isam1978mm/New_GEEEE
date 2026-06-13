from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from app.cli import v6_package_verify
from app.services.v6_package_validator import (
    INTEGRATION_STATUS_INVALID,
    INTEGRATION_STATUS_VERIFIED,
    STATUS_INVALID,
    STATUS_VERIFIED,
    validate_v6_package,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_reference_doc(path: Path, package_sha: str) -> None:
    path.write_text(
        f"# Synthetic V6 Reference\n\nZIP SHA256:\n\n```text\n{package_sha}\n```\n",
        encoding="utf-8",
    )


def _synthetic_payloads() -> dict[str, bytes]:
    return {
        "lawful_gee_candidate_scout_top_25_20260101T120000Z.csv": b"id,score\n1,0.1\n",
        "top25_enhanced_v6.geojson": b'{"type":"FeatureCollection","features":[]}\n',
        "request_zones_v6.csv": b"zone_id\nz1\n",
        "quality_diagnostics_all_cells_v6.csv": b"cell_id\nc1\n",
        "paid_imagery_quote_template_v6.csv": b"zone_id\nz1\n",
        "paid_archive_request_summary.txt": b"summary only\n",
        "visual_inspection_map.html": b"<!doctype html><title>map</title>\n",
    }


def _write_package(tmp_path: Path, payloads: dict[str, bytes] | None = None) -> tuple[Path, Path, Path]:
    payloads = payloads or _synthetic_payloads()
    inventory_path = tmp_path / "inventory.json"
    zip_path = tmp_path / "package.zip"

    records = [
        {"file": name, "size_bytes": len(data), "sha256": _sha256(data)}
        for name, data in sorted(payloads.items())
    ]
    inventory_payload = {
        "created_utc": "2026-01-01T00:00:00Z",
        "folder": "synthetic",
        "file_count": len(records),
        "records": records,
    }
    inventory_bytes = json.dumps(inventory_payload, sort_keys=True).encode("utf-8")
    inventory_path.write_bytes(inventory_bytes)

    with zipfile.ZipFile(zip_path, "w") as archive:
        for name, data in sorted(payloads.items()):
            archive.writestr(name, data)
        archive.writestr(inventory_path.name, inventory_bytes)

    reference_doc = tmp_path / "V6_FROZEN_REFERENCE.md"
    _write_reference_doc(reference_doc, _sha256(zip_path.read_bytes()))
    return zip_path, inventory_path, reference_doc


def test_validate_v6_package_verifies_hash_inventory_and_category_counts(tmp_path: Path) -> None:
    zip_path, inventory_path, reference_doc = _write_package(tmp_path)

    result = validate_v6_package(
        zip_path=zip_path,
        inventory_path=inventory_path,
        reference_doc_path=reference_doc,
    )

    assert result.integration_status == INTEGRATION_STATUS_VERIFIED
    assert result.hash_status == STATUS_VERIFIED
    assert result.inventory_status == STATUS_VERIFIED
    assert result.payload_count == 7
    assert result.zip_entry_count_including_inventory == 8
    assert result.category_counts == {
        "candidate_tables": 2,
        "request_zones": 1,
        "diagnostics": 1,
        "quote_templates": 1,
        "summary_text": 1,
        "visual_map": 1,
        "unknown": 0,
    }
    assert result.issue_counts == {}


def test_safe_summary_omits_payload_filenames_and_hashes(tmp_path: Path) -> None:
    zip_path, inventory_path, reference_doc = _write_package(tmp_path)

    summary = validate_v6_package(
        zip_path=zip_path,
        inventory_path=inventory_path,
        reference_doc_path=reference_doc,
    ).safe_summary()
    serialized = json.dumps(summary, sort_keys=True)

    assert "records" not in summary
    assert "sha256" not in serialized.lower()
    assert "lawful_gee_candidate_scout" not in serialized
    assert "FeatureCollection" not in serialized


def test_mismatched_inventory_member_hash_is_invalid(tmp_path: Path) -> None:
    zip_path, inventory_path, reference_doc = _write_package(tmp_path)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory["records"][0]["sha256"] = _sha256(b"different")
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

    result = validate_v6_package(
        zip_path=zip_path,
        inventory_path=inventory_path,
        reference_doc_path=reference_doc,
    )

    assert result.integration_status == INTEGRATION_STATUS_INVALID
    assert result.inventory_status == STATUS_INVALID
    assert result.issue_counts["zip_member_sha256_mismatch"] == 1


def test_mismatched_documented_zip_hash_is_invalid(tmp_path: Path) -> None:
    zip_path, inventory_path, reference_doc = _write_package(tmp_path)
    _write_reference_doc(reference_doc, _sha256(b"different package"))

    result = validate_v6_package(
        zip_path=zip_path,
        inventory_path=inventory_path,
        reference_doc_path=reference_doc,
    )

    assert result.integration_status == INTEGRATION_STATUS_INVALID
    assert result.hash_status == STATUS_INVALID
    assert result.issue_counts["zip_sha256_mismatch"] == 1


def test_nested_zip_member_is_rejected_without_extraction(tmp_path: Path) -> None:
    zip_path, inventory_path, reference_doc = _write_package(tmp_path)
    with zipfile.ZipFile(zip_path, "a") as archive:
        archive.writestr("nested/unsafe.csv", b"data")
    _write_reference_doc(reference_doc, _sha256(zip_path.read_bytes()))

    result = validate_v6_package(
        zip_path=zip_path,
        inventory_path=inventory_path,
        reference_doc_path=reference_doc,
    )

    assert result.integration_status == INTEGRATION_STATUS_INVALID
    assert result.issue_counts["zip_member_name_invalid"] == 1


def test_cli_prints_safe_json_summary_for_synthetic_fixture(tmp_path: Path, capsys) -> None:
    zip_path, inventory_path, reference_doc = _write_package(tmp_path)

    exit_code = v6_package_verify.main(
        [
            "--zip",
            str(zip_path),
            "--inventory",
            str(inventory_path),
            "--reference-doc",
            str(reference_doc),
        ]
    )
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert exit_code == 0
    assert payload["integration_status"] == INTEGRATION_STATUS_VERIFIED
    assert payload["payload_count"] == 7
    assert "category_counts" in payload
    assert "lawful_gee_candidate_scout" not in out
