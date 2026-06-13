from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from app.cli import v6_package_import
from app.services.v6_package_importer import (
    IMPORT_STATUS_INVALID,
    IMPORT_STATUS_VERIFIED,
    write_v6_safe_import_summary,
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
        "lawful_gee_candidate_scout_top_25_20260101T120000Z.csv": (
            b"cell_id,candidate_score\n"
        ),
        "lawful_gee_candidate_scout_top_25_20260101T120000Z.geojson": (
            b'{"type":"FeatureCollection","features":[]}\n'
        ),
        "top25_enhanced_v6.csv": (
            b"cell_id,candidate_score,v6_review_priority_score\n"
        ),
        "top25_enhanced_v6.geojson": b'{"type":"FeatureCollection","features":[]}\n',
        "quality_diagnostics_all_cells_v6.csv": (
            b"cell_id,candidate_score,v6_review_priority_score\n"
        ),
        "stable_candidate_priority_list_v6.csv": (
            b"cell_id,candidate_score,v6_review_priority_score\n"
        ),
        "request_zones_v6.csv": b"request_zone_id,primary_cell_id\n",
        "request_zones_v6.geojson": b'{"type":"FeatureCollection","features":[]}\n',
        "paid_imagery_quote_template_v6.csv": b"quote_id,request_zone_id\n",
        "paid_imagery_quote_comparison_v6.csv": b"quote_id,request_zone_id,quote_score\n",
        "paid_archive_request_summary.txt": b"synthetic summary placeholder\n",
        "visual_inspection_map.html": b"<!doctype html><title>synthetic</title>\n",
    }


def _write_package(
    tmp_path: Path,
    payloads: dict[str, bytes] | None = None,
) -> tuple[Path, Path, Path]:
    payloads = payloads or _synthetic_payloads()
    inventory_path = tmp_path / "synthetic_inventory.json"
    zip_path = tmp_path / "synthetic_v6.zip"

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


def test_write_v6_safe_import_summary_persists_only_approved_metadata(tmp_path: Path) -> None:
    zip_path, inventory_path, reference_doc = _write_package(tmp_path)
    output_path = tmp_path / "safe_summary.json"

    result = write_v6_safe_import_summary(
        zip_path=zip_path,
        inventory_path=inventory_path,
        output_path=output_path,
        reference_doc_path=reference_doc,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert result.validation_status == IMPORT_STATUS_VERIFIED
    assert payload["validation_status"] == IMPORT_STATUS_VERIFIED
    assert payload["contract_version"] == "v6_external_package_contract_v1"
    assert payload["package_filename"] == zip_path.name
    assert payload["inventory_filename"] == inventory_path.name
    assert "inventory_sha256" not in payload
    assert "inventory_size_bytes" not in payload
    assert payload["payload_count"] == 12
    assert payload["zip_entry_count"] == 13
    assert payload["category_counts"] == {
        "candidate_tables": 5,
        "diagnostics": 1,
        "quote_templates": 2,
        "request_zones": 2,
        "summary_text": 1,
        "unknown": 0,
        "visual_map": 1,
    }
    assert payload["csv_headers"]["top25_enhanced_v6.csv"] == [
        "cell_id",
        "candidate_score",
        "v6_review_priority_score",
    ]
    assert payload["geojson_roles"]["top25_enhanced_v6.geojson"] == {
        "role": "top25_enhanced_geojson",
        "top_level_type": "FeatureCollection",
    }

    serialized = json.dumps(payload, sort_keys=True)
    assert str(zip_path) not in serialized
    assert str(inventory_path) not in serialized
    assert "features\": []" not in serialized
    assert "synthetic summary placeholder" not in serialized
    assert "<!doctype html>" not in serialized


def test_write_v6_safe_import_summary_marks_bad_header_invalid(tmp_path: Path) -> None:
    payloads = _synthetic_payloads()
    payloads["top25_enhanced_v6.csv"] = b"cell_id,candidate_score\n"
    zip_path, inventory_path, reference_doc = _write_package(tmp_path, payloads)
    output_path = tmp_path / "safe_summary.json"

    result = write_v6_safe_import_summary(
        zip_path=zip_path,
        inventory_path=inventory_path,
        output_path=output_path,
        reference_doc_path=reference_doc,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert result.validation_status == IMPORT_STATUS_INVALID
    assert payload["validation_status"] == IMPORT_STATUS_INVALID
    assert payload["csv_headers"]["top25_enhanced_v6.csv"] == [
        "cell_id",
        "candidate_score",
    ]


def test_cli_prints_safe_counts_and_writes_summary(tmp_path: Path, capsys) -> None:
    zip_path, inventory_path, reference_doc = _write_package(tmp_path)
    output_path = tmp_path / "safe_summary.json"

    exit_code = v6_package_import.main(
        [
            "--zip",
            str(zip_path),
            "--inventory",
            str(inventory_path),
            "--out",
            str(output_path),
            "--reference-doc",
            str(reference_doc),
        ]
    )
    stdout = capsys.readouterr().out
    cli_payload = json.loads(stdout)

    assert exit_code == 0
    assert cli_payload["validation_status"] == IMPORT_STATUS_VERIFIED
    assert cli_payload["output_path"] == str(output_path)
    assert cli_payload["payload_count"] == 12
    assert output_path.is_file()
    assert "candidate_score" not in stdout
    assert "FeatureCollection" not in stdout
    assert "sha256" not in stdout
