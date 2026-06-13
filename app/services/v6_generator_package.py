"""App-side V6 package generator.

This module implements the early V6 generator path. It can generate a complete
V6 package shape from synthetic fixtures or app-input fixture models, write an
inventory and ZIP, and validate generated package structure without using real
V6 rows, real coordinates, Earth Engine, notebook globals, or provider APIs.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping
import zipfile

from app.services.v6_generator_inputs import (
    V6GenerationInput,
    build_synthetic_v6_generation_input,
)
from app.services.v6_package_contract import (
    CATEGORY_NAMES,
    V6CsvHeaderContract,
    category_for_file,
    summarize_geojson_top_level,
    validate_csv_headers,
    validate_payload_file_names,
)


GENERATOR_STATUS_VERIFIED = "generated_synthetic_package_verified"
GENERATOR_STATUS_INVALID = "generated_synthetic_package_invalid"

_DEFAULT_TIMESTAMP = "20260101T120000Z"
_TIMESTAMP_PATTERN = re.compile(r"^\d{8}T\d{6}Z$")
_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class V6GeneratedPackageResult:
    output_dir: str
    zip_path: str
    inventory_path: str
    validation_report_path: str
    validation_status: str
    payload_count: int
    zip_entry_count: int
    category_counts: dict[str, int]
    payload_file_names: tuple[str, ...]
    issues: tuple[str, ...]

    @property
    def is_verified(self) -> bool:
        return self.validation_status == GENERATOR_STATUS_VERIFIED

    def cli_summary(self) -> dict[str, Any]:
        """Return a safe CLI summary with no rows, headers, geometry, or payload bodies."""

        return {
            "validation_status": self.validation_status,
            "output_dir": self.output_dir,
            "zip_path": self.zip_path,
            "inventory_path": self.inventory_path,
            "validation_report_path": self.validation_report_path,
            "payload_count": self.payload_count,
            "zip_entry_count": self.zip_entry_count,
            "category_counts": dict(self.category_counts),
            "issue_count": len(self.issues),
        }


def generate_synthetic_v6_package(
    *,
    output_dir: str | Path,
    timestamp: str = _DEFAULT_TIMESTAMP,
    package_name: str | None = None,
) -> V6GeneratedPackageResult:
    """Generate a complete synthetic V6 package shape into an operator path."""

    return generate_v6_package_from_input(
        output_dir=output_dir,
        generation_input=build_synthetic_v6_generation_input(timestamp=timestamp),
        package_name=package_name,
    )


def generate_v6_package_from_input(
    *,
    output_dir: str | Path,
    generation_input: V6GenerationInput,
    package_name: str | None = None,
) -> V6GeneratedPackageResult:
    """Generate a complete V6 package shape from a safe app-input fixture.

    The current implementation still uses safe GeoJSON shells and fixture-style
    rows. It connects the package writer to app input models while keeping Earth
    Engine, real geometry, notebook runtime state, and provider workflow out of
    this stage.
    """

    timestamp = generation_input.timestamp
    if not _TIMESTAMP_PATTERN.fullmatch(timestamp):
        raise ValueError("timestamp must use YYYYMMDDTHHMMSSZ format")

    root = Path(output_dir)
    payload_dir = root / "payloads"
    root.mkdir(parents=True, exist_ok=True)
    payload_dir.mkdir(parents=True, exist_ok=True)

    payloads = build_v6_payloads_from_input(generation_input=generation_input)
    for name, content in payloads.items():
        (payload_dir / name).write_bytes(content)

    inventory_name = f"V6_SYNTHETIC_GENERATED_inventory_{timestamp}.json"
    zip_name = package_name or f"V6_SYNTHETIC_GENERATED_{timestamp}.zip"
    inventory_path = root / inventory_name
    zip_path = root / zip_name
    validation_report_path = root / f"V6_SYNTHETIC_GENERATED_validation_{timestamp}.json"

    records = [
        {
            "file": name,
            "size_bytes": len(content),
            "sha256": _sha256_bytes(content),
        }
        for name, content in sorted(payloads.items())
    ]
    inventory_payload = {
        "created_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "generator": "app-side synthetic V6 package generator",
        "input_run_id": generation_input.run_id,
        "file_count": len(records),
        "records": records,
    }
    inventory_bytes = json.dumps(inventory_payload, indent=2, sort_keys=True).encode("utf-8")
    inventory_path.write_bytes(inventory_bytes)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(payloads.items()):
            archive.writestr(name, content)
        archive.writestr(inventory_path.name, inventory_bytes)

    validation_report = validate_generated_v6_payload_shape(
        payloads=payloads,
        inventory_filename=inventory_path.name,
    )
    validation_report.update(
        {
            "zip_filename": zip_path.name,
            "inventory_filename": inventory_path.name,
            "input_run_id": generation_input.run_id,
            "zip_entry_count": len(payloads) + 1,
            "package_sha256": _sha256_path(zip_path),
        }
    )
    validation_report_path.write_text(
        json.dumps(validation_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return V6GeneratedPackageResult(
        output_dir=str(root),
        zip_path=str(zip_path),
        inventory_path=str(inventory_path),
        validation_report_path=str(validation_report_path),
        validation_status=str(validation_report["validation_status"]),
        payload_count=len(payloads),
        zip_entry_count=len(payloads) + 1,
        category_counts=dict(validation_report["category_counts"]),
        payload_file_names=tuple(sorted(payloads)),
        issues=tuple(validation_report["issues"]),
    )


def build_synthetic_v6_payloads(*, timestamp: str = _DEFAULT_TIMESTAMP) -> dict[str, bytes]:
    """Return all required V6 payload roles as synthetic bytes."""

    return build_v6_payloads_from_input(
        generation_input=build_synthetic_v6_generation_input(timestamp=timestamp),
    )


def build_v6_payloads_from_input(*, generation_input: V6GenerationInput) -> dict[str, bytes]:
    """Return all required V6 payload roles from safe app-input fixture data."""

    timestamp = generation_input.timestamp
    top25_csv = f"lawful_gee_candidate_scout_top_25_{timestamp}.csv"
    top25_geojson = f"lawful_gee_candidate_scout_top_25_{timestamp}.geojson"

    top_candidate_rows = [
        [candidate.cell_id, _format_score(candidate.candidate_score)]
        for candidate in generation_input.candidates
    ]
    enhanced_rows = [
        [
            candidate.cell_id,
            _format_score(candidate.candidate_score),
            _format_score(candidate.v6_review_priority_score),
        ]
        for candidate in generation_input.candidates
    ]
    request_zone_rows = [
        [zone.request_zone_id, zone.primary_cell_id]
        for zone in generation_input.request_zones
    ]
    quote_template_rows = [
        [zone.quote_id, zone.request_zone_id]
        for zone in generation_input.request_zones
    ]
    quote_comparison_rows = [
        [zone.quote_id, zone.request_zone_id, _format_score(zone.quote_score)]
        for zone in generation_input.request_zones
    ]

    return {
        top25_csv: _csv_bytes(["cell_id", "candidate_score"], top_candidate_rows),
        top25_geojson: _geojson_bytes(),
        "top25_enhanced_v6.csv": _csv_bytes(
            ["cell_id", "candidate_score", "v6_review_priority_score"],
            enhanced_rows,
        ),
        "top25_enhanced_v6.geojson": _geojson_bytes(),
        "quality_diagnostics_all_cells_v6.csv": _csv_bytes(
            ["cell_id", "candidate_score", "v6_review_priority_score"],
            enhanced_rows,
        ),
        "stable_candidate_priority_list_v6.csv": _csv_bytes(
            ["cell_id", "candidate_score", "v6_review_priority_score"],
            enhanced_rows,
        ),
        "request_zones_v6.csv": _csv_bytes(
            ["request_zone_id", "primary_cell_id"],
            request_zone_rows,
        ),
        "request_zones_v6.geojson": _geojson_bytes(),
        "paid_imagery_quote_template_v6.csv": _csv_bytes(
            ["quote_id", "request_zone_id"],
            quote_template_rows,
        ),
        "paid_imagery_quote_comparison_v6.csv": _csv_bytes(
            ["quote_id", "request_zone_id", "quote_score"],
            quote_comparison_rows,
        ),
        "paid_archive_request_summary.txt": (
            "Synthetic V6 request package summary.\n"
            f"Input run: {generation_input.run_id}\n"
            "This placeholder proves package shape only and contains no real request content.\n"
        ).encode("utf-8"),
        "visual_inspection_map.html": (
            "<!doctype html>\n"
            "<html><head><meta charset=\"utf-8\"><title>Synthetic V6 Map</title></head>\n"
            "<body><p>Synthetic placeholder map only.</p></body></html>\n"
        ).encode("utf-8"),
    }


def validate_generated_v6_payload_shape(
    *,
    payloads: Mapping[str, bytes],
    inventory_filename: str,
) -> dict[str, Any]:
    """Validate generated payload shape and return safe metadata only."""

    issues: list[str] = []
    warnings: list[str] = []
    member_names = [*payloads.keys(), inventory_filename]
    name_result = validate_payload_file_names(member_names, inventory_filename=inventory_filename)
    issues.extend(name_result.issues)
    warnings.extend(name_result.warnings)

    category_counts = {name: 0 for name in CATEGORY_NAMES}
    csv_header_files: dict[str, list[str]] = {}
    geojson_top_level_files: dict[str, str | None] = {}

    for name, content in sorted(payloads.items()):
        category_counts[category_for_file(name)] = category_counts.get(category_for_file(name), 0) + 1
        lower_name = name.lower()
        if lower_name.endswith(".csv"):
            headers = _read_csv_header_from_bytes(content)
            csv_header_files[name] = list(headers)
            header_result = validate_csv_headers(headers, _csv_contract_for_file(name))
            issues.extend(header_result.issues)
        elif lower_name.endswith(".geojson"):
            try:
                document = json.loads(content.decode("utf-8-sig"))
            except ValueError:
                issues.append(f"geojson_parse_error:{name}")
                continue
            summary = summarize_geojson_top_level(document)
            if not summary.valid:
                issues.extend(f"{name}:{issue}" for issue in summary.issues)
            geojson_top_level_files[name] = summary.document_type

    validation_status = GENERATOR_STATUS_VERIFIED if not issues and not warnings else GENERATOR_STATUS_INVALID

    return {
        "validation_status": validation_status,
        "payload_count": len(payloads),
        "category_counts": dict(sorted(category_counts.items())),
        "payload_file_names": sorted(payloads),
        "csv_header_files": csv_header_files,
        "geojson_top_level_files": geojson_top_level_files,
        "issues": sorted(issues),
        "warnings": sorted(warnings),
    }


def _csv_contract_for_file(name: str) -> V6CsvHeaderContract:
    return V6CsvHeaderContract(file_name=name, required_headers=_required_csv_headers_for_file(name))


def _required_csv_headers_for_file(name: str) -> tuple[str, ...]:
    if name.startswith("lawful_gee_candidate_scout_top_25_") and name.endswith(".csv"):
        return ("cell_id", "candidate_score")
    if name == "top25_enhanced_v6.csv":
        return ("cell_id", "candidate_score", "v6_review_priority_score")
    if name == "quality_diagnostics_all_cells_v6.csv":
        return ("cell_id", "candidate_score", "v6_review_priority_score")
    if name == "stable_candidate_priority_list_v6.csv":
        return ("cell_id", "candidate_score", "v6_review_priority_score")
    if name == "request_zones_v6.csv":
        return ("request_zone_id", "primary_cell_id")
    if name == "paid_imagery_quote_template_v6.csv":
        return ("quote_id", "request_zone_id")
    if name == "paid_imagery_quote_comparison_v6.csv":
        return ("quote_id", "request_zone_id", "quote_score")
    return ()


def _csv_bytes(headers: list[str], rows: list[list[str]]) -> bytes:
    lines = [",".join(headers)]
    lines.extend(",".join(row) for row in rows)
    return ("\n".join(lines) + "\n").encode("utf-8")


def _read_csv_header_from_bytes(content: bytes) -> tuple[str, ...]:
    first_line = content.splitlines()[0].decode("utf-8-sig") if content else ""
    return tuple(next(csv.reader([first_line]), []))


def _geojson_bytes() -> bytes:
    return b'{"type":"FeatureCollection","features":[]}\n'


def _format_score(value: float) -> str:
    return f"{value:.6g}"


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()
