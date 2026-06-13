"""Private read-only V6 package import summary writer.

The importer composes the V6 package validator and source-lock contract helpers,
then writes only approved safe summary metadata to an operator-supplied JSON path.
It never extracts ZIP members, copies payload artifacts, or persists row,
geometry, coordinate, feature-property, HTML, or text-summary contents.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import csv
import hashlib
import json
from pathlib import Path
import zipfile
from typing import Any

from app.services.v6_package_contract import (
    CATEGORY_NAMES,
    TIMESTAMPED_TOP25_PATTERN,
    V6_PACKAGE_CONTRACT_VERSION,
    V6CsvHeaderContract,
    category_for_file,
    summarize_geojson_top_level,
    validate_csv_headers,
    validate_payload_file_names,
)
from app.services.v6_package_validator import (
    INTEGRATION_STATUS_VERIFIED,
    validate_v6_package,
)


IMPORT_STATUS_VERIFIED = "verified_safe_summary_written"
IMPORT_STATUS_INVALID = "invalid_safe_summary_written"

_CHUNK_SIZE = 1024 * 1024
_CSV_HEADER_READ_LIMIT = 128 * 1024
_GEOJSON_TOP_LEVEL_READ_LIMIT = 128 * 1024


@dataclass(frozen=True)
class V6PackageImportSummaryResult:
    output_path: str
    validation_status: str
    payload_count: int
    zip_entry_count: int
    category_counts: dict[str, int]
    role_counts: dict[str, int]

    @property
    def is_verified(self) -> bool:
        return self.validation_status == IMPORT_STATUS_VERIFIED

    def cli_summary(self) -> dict[str, Any]:
        return {
            "validation_status": self.validation_status,
            "output_path": self.output_path,
            "payload_count": self.payload_count,
            "zip_entry_count": self.zip_entry_count,
            "category_counts": dict(self.category_counts),
            "role_counts": dict(self.role_counts),
        }


def write_v6_safe_import_summary(
    *,
    zip_path: str | Path,
    inventory_path: str | Path,
    output_path: str | Path,
    reference_doc_path: str | Path = "docs/V6_FROZEN_REFERENCE.md",
) -> V6PackageImportSummaryResult:
    """Write a metadata-only V6 import summary from an external package."""

    package = Path(zip_path)
    inventory = Path(inventory_path)
    output = Path(output_path)

    validator_result = validate_v6_package(
        zip_path=package,
        inventory_path=inventory,
        reference_doc_path=reference_doc_path,
    )

    metadata = _build_safe_summary_metadata(
        package=package,
        inventory=inventory,
        validator_status=validator_result.integration_status,
        validator_payload_count=validator_result.payload_count,
        validator_zip_entry_count=validator_result.zip_entry_count_including_inventory,
        validator_category_counts=validator_result.category_counts,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return V6PackageImportSummaryResult(
        output_path=str(output),
        validation_status=str(metadata["validation_status"]),
        payload_count=int(metadata["payload_count"]),
        zip_entry_count=int(metadata["zip_entry_count"]),
        category_counts=dict(metadata["category_counts"]),
        role_counts=dict(metadata["role_counts"]),
    )


def _build_safe_summary_metadata(
    *,
    package: Path,
    inventory: Path,
    validator_status: str,
    validator_payload_count: int,
    validator_zip_entry_count: int,
    validator_category_counts: dict[str, int],
) -> dict[str, Any]:
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    package_sha256 = _sha256_path(package) if package.is_file() else None
    payload_files: list[dict[str, Any]] = []
    csv_headers: dict[str, list[str]] = {}
    geojson_roles: dict[str, dict[str, str | None]] = {}
    role_counts: dict[str, int] = {}
    category_counts = {name: 0 for name in CATEGORY_NAMES}
    zip_entry_count = 0
    contract_valid = False

    if package.is_file():
        try:
            with zipfile.ZipFile(package) as archive:
                infos = [info for info in archive.infolist() if not info.is_dir()]
                zip_entry_count = len(infos)
                member_names = [info.filename for info in infos]
                name_check = validate_payload_file_names(
                    member_names,
                    inventory_filename=inventory.name,
                )
                contract_valid = name_check.valid
                for info in sorted(infos, key=lambda item: item.filename):
                    if info.filename == inventory.name:
                        continue
                    if not _is_top_level_member(info.filename):
                        contract_valid = False
                        continue

                    role = _role_for_file(info.filename)
                    category = category_for_file(info.filename)
                    role_counts[role] = role_counts.get(role, 0) + 1
                    category_counts[category] = category_counts.get(category, 0) + 1
                    payload_files.append(
                        {
                            "file_name": info.filename,
                            "role": role,
                            "category": category,
                            "size_bytes": info.file_size,
                            "sha256": _sha256_zip_member(archive, info),
                        }
                    )

                    lower_name = info.filename.lower()
                    if lower_name.endswith(".csv"):
                        headers = _read_csv_header_only(archive, info)
                        csv_headers[info.filename] = list(headers)
                        if not validate_csv_headers(
                            headers,
                            _csv_contract_for_file(info.filename),
                        ).valid:
                            contract_valid = False
                    elif lower_name.endswith(".geojson"):
                        document_type = _read_geojson_top_level_type_only(archive, info)
                        summary = summarize_geojson_top_level(
                            {"type": document_type, "features": []}
                            if document_type is not None
                            else {"features": []}
                        )
                        if not summary.valid:
                            contract_valid = False
                        geojson_roles[info.filename] = {
                            "role": role,
                            "top_level_type": document_type,
                        }
        except (OSError, zipfile.BadZipFile):
            contract_valid = False

    payload_count = len(payload_files)
    validation_status = (
        IMPORT_STATUS_VERIFIED
        if validator_status == INTEGRATION_STATUS_VERIFIED
        and contract_valid
        and payload_count == validator_payload_count
        else IMPORT_STATUS_INVALID
    )

    return {
        "contract_version": V6_PACKAGE_CONTRACT_VERSION,
        "generated_at": generated_at,
        "validation_status": validation_status,
        "package_filename": package.name,
        "inventory_filename": inventory.name,
        "package_sha256": package_sha256,
        "package_size_bytes": package.stat().st_size if package.is_file() else None,
        "payload_count": payload_count,
        "zip_entry_count": zip_entry_count or validator_zip_entry_count,
        "category_counts": category_counts if payload_files else dict(validator_category_counts),
        "role_counts": dict(sorted(role_counts.items())),
        "payload_files": payload_files,
        "csv_headers": dict(sorted(csv_headers.items())),
        "geojson_roles": dict(sorted(geojson_roles.items())),
    }


def _csv_contract_for_file(name: str) -> V6CsvHeaderContract:
    return V6CsvHeaderContract(file_name=name, required_headers=_required_csv_headers_for_file(name))


def _required_csv_headers_for_file(name: str) -> tuple[str, ...]:
    if TIMESTAMPED_TOP25_PATTERN.match(name) and name.endswith(".csv"):
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


def _role_for_file(name: str) -> str:
    if TIMESTAMPED_TOP25_PATTERN.match(name) and name.endswith(".csv"):
        return "timestamped_top25_csv"
    if TIMESTAMPED_TOP25_PATTERN.match(name) and name.endswith(".geojson"):
        return "timestamped_top25_geojson"
    if name == "top25_enhanced_v6.csv":
        return "top25_enhanced_csv"
    if name == "top25_enhanced_v6.geojson":
        return "top25_enhanced_geojson"
    if name == "quality_diagnostics_all_cells_v6.csv":
        return "quality_diagnostics_csv"
    if name == "stable_candidate_priority_list_v6.csv":
        return "stable_candidate_priority_csv"
    if name == "request_zones_v6.csv":
        return "request_zones_csv"
    if name == "request_zones_v6.geojson":
        return "request_zones_geojson"
    if name == "paid_imagery_quote_template_v6.csv":
        return "quote_template_csv"
    if name == "paid_imagery_quote_comparison_v6.csv":
        return "quote_comparison_csv"
    if name == "paid_archive_request_summary.txt":
        return "summary_text"
    if name == "visual_inspection_map.html":
        return "visual_map_html"
    return "unknown"


def _read_csv_header_only(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> tuple[str, ...]:
    data = bytearray()
    with archive.open(info, "r") as handle:
        while len(data) < _CSV_HEADER_READ_LIMIT:
            chunk = handle.read(min(4096, _CSV_HEADER_READ_LIMIT - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            if b"\n" in chunk:
                break
    header_line = bytes(data).splitlines()[0] if data else b""
    text = header_line.decode("utf-8-sig")
    return tuple(next(csv.reader([text]), []))


def _read_geojson_top_level_type_only(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
) -> str | None:
    buffer = ""
    decoder = json.JSONDecoder()
    type_value: str | None = None
    bytes_read = 0

    with archive.open(info, "r") as handle:
        while bytes_read < _GEOJSON_TOP_LEVEL_READ_LIMIT:
            chunk = handle.read(1)
            if not chunk:
                break
            bytes_read += 1
            if chunk == b"\xef" and not buffer:
                handle.read(2)
                bytes_read += 2
                continue
            buffer += chunk.decode("ascii", errors="ignore")

            if type_value is None:
                type_value = _extract_top_level_string(buffer, decoder, "type")
            if _top_level_array_key_seen(buffer, "features"):
                return type_value

    return None


def _extract_top_level_string(buffer: str, decoder: json.JSONDecoder, key: str) -> str | None:
    marker = f'"{key}"'
    index = buffer.find(marker)
    if index < 0:
        return None
    colon = buffer.find(":", index + len(marker))
    if colon < 0:
        return None
    value_start = colon + 1
    while value_start < len(buffer) and buffer[value_start].isspace():
        value_start += 1
    try:
        value, _end = decoder.raw_decode(buffer[value_start:])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, str) else None


def _top_level_array_key_seen(buffer: str, key: str) -> bool:
    marker = f'"{key}"'
    index = buffer.find(marker)
    if index < 0:
        return False
    colon = buffer.find(":", index + len(marker))
    if colon < 0:
        return False
    value_start = colon + 1
    while value_start < len(buffer) and buffer[value_start].isspace():
        value_start += 1
    return value_start < len(buffer) and buffer[value_start] == "["


def _is_top_level_member(name: str) -> bool:
    return "/" not in name and "\\" not in name and name not in {"", ".", ".."}


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_zip_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    digest = hashlib.sha256()
    with archive.open(info, "r") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()
