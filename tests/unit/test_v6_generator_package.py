from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from app.cli import v6_package_generate
from app.services.v6_generator_package import (
    GENERATOR_STATUS_VERIFIED,
    generate_synthetic_v6_package,
)
from app.services.v6_package_contract import validate_payload_file_names
from app.services.v6_package_validator import (
    INTEGRATION_STATUS_VERIFIED,
    validate_v6_package,
)


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_reference_doc(path: Path, package_sha: str) -> None:
    path.write_text(
        f"# Synthetic Generated V6 Reference\n\nZIP SHA256:\n\n```text\n{package_sha}\n```\n",
        encoding="utf-8",
    )


def test_generate_synthetic_v6_package_creates_all_required_roles(tmp_path: Path) -> None:
    result = generate_synthetic_v6_package(output_dir=tmp_path)

    assert result.validation_status == GENERATOR_STATUS_VERIFIED
    assert result.payload_count == 12
    assert result.zip_entry_count == 13
    assert result.category_counts == {
        "candidate_tables": 5,
        "diagnostics": 1,
        "quote_templates": 2,
        "request_zones": 2,
        "summary_text": 1,
        "unknown": 0,
        "visual_map": 1,
    }

    zip_path = Path(result.zip_path)
    inventory_path = Path(result.inventory_path)
    validation_report_path = Path(result.validation_report_path)
    assert zip_path.is_file()
    assert inventory_path.is_file()
    assert validation_report_path.is_file()

    with zipfile.ZipFile(zip_path) as archive:
        names = sorted(info.filename for info in archive.infolist() if not info.is_dir())

    contract_result = validate_payload_file_names(
        names,
        inventory_filename=inventory_path.name,
    )
    assert contract_result.valid
    assert inventory_path.name in names
    assert "top25_enhanced_v6.csv" in names
    assert "request_zones_v6.geojson" in names
    assert "paid_imagery_quote_template_v6.csv" in names
    assert "visual_inspection_map.html" in names


def test_generated_synthetic_package_inventory_matches_zip_members(tmp_path: Path) -> None:
    result = generate_synthetic_v6_package(output_dir=tmp_path)
    inventory = json.loads(Path(result.inventory_path).read_text(encoding="utf-8"))

    assert inventory["file_count"] == 12
    records = {item["file"]: item for item in inventory["records"]}
    assert set(records) == set(result.payload_file_names)

    with zipfile.ZipFile(result.zip_path) as archive:
        for name, record in records.items():
            data = archive.read(name)
            assert len(data) == record["size_bytes"]
            assert hashlib.sha256(data).hexdigest() == record["sha256"]


def test_generated_synthetic_package_passes_existing_validator(tmp_path: Path) -> None:
    result = generate_synthetic_v6_package(output_dir=tmp_path)
    reference_doc = tmp_path / "V6_FROZEN_REFERENCE.md"
    _write_reference_doc(reference_doc, _sha256_path(Path(result.zip_path)))

    validation = validate_v6_package(
        zip_path=result.zip_path,
        inventory_path=result.inventory_path,
        reference_doc_path=reference_doc,
    )

    assert validation.integration_status == INTEGRATION_STATUS_VERIFIED
    assert validation.payload_count == 12
    assert validation.zip_entry_count_including_inventory == 13
    assert validation.issue_counts == {}


def test_validation_report_is_safe_metadata_only(tmp_path: Path) -> None:
    result = generate_synthetic_v6_package(output_dir=tmp_path)
    report = json.loads(Path(result.validation_report_path).read_text(encoding="utf-8"))

    assert report["validation_status"] == GENERATOR_STATUS_VERIFIED
    assert report["payload_count"] == 12
    assert report["issues"] == []
    assert report["warnings"] == []

    serialized = json.dumps(report, sort_keys=True)
    assert "SYNTH_CELL_001,0.81" not in serialized
    assert "FeatureCollection","features" not in serialized
    assert "Synthetic placeholder map" not in serialized
    assert "Synthetic V6 paid-imagery request package summary" not in serialized


def test_cli_generates_synthetic_package_and_prints_safe_counts(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "generated"

    exit_code = v6_package_generate.main(["--out", str(output_dir)])
    stdout = capsys.readouterr().out
    payload = json.loads(stdout)

    assert exit_code == 0
    assert payload["validation_status"] == GENERATOR_STATUS_VERIFIED
    assert payload["payload_count"] == 12
    assert payload["zip_entry_count"] == 13
    assert Path(payload["zip_path"]).is_file()
    assert Path(payload["inventory_path"]).is_file()
    assert Path(payload["validation_report_path"]).is_file()
    assert "candidate_score" not in stdout
    assert "FeatureCollection" not in stdout
    assert "SYNTH_CELL_001" not in stdout
