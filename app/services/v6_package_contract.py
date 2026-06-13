"""V6 external package contract helpers.

The contract module defines V6 package roles and safe schema checks for a
future read-only import path. It does not read, copy, extract, or serve package
artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import re
from typing import Any, Mapping, Sequence


V6_PACKAGE_CONTRACT_VERSION = "v6_external_package_contract_v1"

TIMESTAMPED_TOP25_PATTERN = re.compile(
    r"^lawful_gee_candidate_scout_top_25_\d{8}T\d{6}Z\.(csv|geojson)$"
)

REQUIRED_FIXED_PAYLOAD_FILES = (
    "top25_enhanced_v6.csv",
    "top25_enhanced_v6.geojson",
    "quality_diagnostics_all_cells_v6.csv",
    "stable_candidate_priority_list_v6.csv",
    "request_zones_v6.csv",
    "request_zones_v6.geojson",
    "paid_imagery_quote_template_v6.csv",
    "paid_imagery_quote_comparison_v6.csv",
    "paid_archive_request_summary.txt",
    "visual_inspection_map.html",
)

REQUIRED_TIMESTAMPED_PAYLOAD_PATTERNS = (
    "lawful_gee_candidate_scout_top_25_<YYYYMMDDTHHMMSSZ>.csv",
    "lawful_gee_candidate_scout_top_25_<YYYYMMDDTHHMMSSZ>.geojson",
)

OPTIONAL_PAYLOAD_FILES: tuple[str, ...] = ()

CSV_PAYLOAD_FILES = (
    "lawful_gee_candidate_scout_top_25_<timestamp>.csv",
    "top25_enhanced_v6.csv",
    "quality_diagnostics_all_cells_v6.csv",
    "stable_candidate_priority_list_v6.csv",
    "request_zones_v6.csv",
    "paid_imagery_quote_template_v6.csv",
    "paid_imagery_quote_comparison_v6.csv",
)

GEOJSON_PAYLOAD_FILES = (
    "lawful_gee_candidate_scout_top_25_<timestamp>.geojson",
    "top25_enhanced_v6.geojson",
    "request_zones_v6.geojson",
)

INVENTORY_FILE_ROLE = "inventory_json_not_payload"

CATEGORY_NAMES = (
    "candidate_tables",
    "request_zones",
    "diagnostics",
    "quote_templates",
    "summary_text",
    "visual_map",
    "unknown",
)

ARTIFACT_POLICY = "FILESYSTEM_ONLY; external generated V6 artifacts remain outside Git"
SAFETY_POLICY = (
    "Read-only import only; no Earth Engine calls, no artifact generation, no HTTP serving, "
    "and no row, geometry, coordinate, path, or per-candidate logging."
)

SOURCE_LOCK_IDENTITY_FIELDS = (
    "contract_version",
    "zip_filename",
    "zip_size_bytes",
    "zip_sha256",
    "inventory_filename",
    "inventory_size_bytes",
    "inventory_sha256",
    "payload_count",
    "zip_entry_count_including_inventory",
    "payload_file_names",
    "payload_file_sizes",
    "payload_file_sha256_values",
    "csv_header_sets",
    "geojson_top_level_roles",
    "category_counts",
)


@dataclass(frozen=True)
class V6CsvHeaderContract:
    """Caller-supplied CSV header contract for a V6 package member."""

    file_name: str
    required_headers: tuple[str, ...] = ()
    exact_headers: tuple[str, ...] | None = None


@dataclass(frozen=True)
class V6ContractValidationResult:
    valid: bool
    issues: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class V6GeoJsonTopLevelSummary:
    valid: bool
    top_level_keys: tuple[str, ...]
    document_type: str | None
    features_is_list: bool
    feature_count: int | None
    issues: tuple[str, ...] = ()


def is_safe_member_name(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    member = PurePosixPath(value)
    return (
        not value.startswith(("/", "\\"))
        and "\\" not in value
        and len(member.parts) == 1
        and ".." not in member.parts
        and member.name == value
    )


def category_for_file(name: str) -> str:
    if TIMESTAMPED_TOP25_PATTERN.match(name):
        return "candidate_tables"
    if name in {
        "top25_enhanced_v6.csv",
        "top25_enhanced_v6.geojson",
        "stable_candidate_priority_list_v6.csv",
    }:
        return "candidate_tables"
    if name in {"request_zones_v6.csv", "request_zones_v6.geojson"}:
        return "request_zones"
    if name == "quality_diagnostics_all_cells_v6.csv":
        return "diagnostics"
    if name in {"paid_imagery_quote_template_v6.csv", "paid_imagery_quote_comparison_v6.csv"}:
        return "quote_templates"
    if name == "paid_archive_request_summary.txt":
        return "summary_text"
    if name == "visual_inspection_map.html":
        return "visual_map"
    return "unknown"


def validate_payload_file_names(
    names: Sequence[str],
    *,
    inventory_filename: str | None = None,
) -> V6ContractValidationResult:
    """Validate top-level V6 payload names without opening payload contents."""

    issues: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    payload_names: set[str] = set()

    for name in names:
        if not is_safe_member_name(name):
            issues.append(f"unsafe_member_name:{name}")
            continue
        if name in seen:
            issues.append(f"duplicate_member_name:{name}")
            continue
        seen.add(name)
        if inventory_filename is not None and name == inventory_filename:
            continue
        payload_names.add(name)

    for required_name in REQUIRED_FIXED_PAYLOAD_FILES:
        if required_name not in payload_names:
            issues.append(f"missing_required_payload:{required_name}")

    timestamped_csv = [
        name for name in payload_names if TIMESTAMPED_TOP25_PATTERN.match(name) and name.endswith(".csv")
    ]
    timestamped_geojson = [
        name
        for name in payload_names
        if TIMESTAMPED_TOP25_PATTERN.match(name) and name.endswith(".geojson")
    ]
    if not timestamped_csv:
        issues.append("missing_required_payload:lawful_gee_candidate_scout_top_25_<timestamp>.csv")
    if not timestamped_geojson:
        issues.append("missing_required_payload:lawful_gee_candidate_scout_top_25_<timestamp>.geojson")

    known_names = set(REQUIRED_FIXED_PAYLOAD_FILES)
    known_names.update(timestamped_csv)
    known_names.update(timestamped_geojson)
    known_names.update(OPTIONAL_PAYLOAD_FILES)
    for name in sorted(payload_names - known_names):
        warnings.append(f"unknown_payload:{name}")

    return V6ContractValidationResult(
        valid=not issues and not warnings,
        issues=tuple(issues),
        warnings=tuple(warnings),
    )


def validate_csv_headers(
    observed_headers: Sequence[str],
    contract: V6CsvHeaderContract,
) -> V6ContractValidationResult:
    """Validate headers only; never inspect CSV rows."""

    headers = _normalize_headers(observed_headers)
    issues: list[str] = []

    if not headers:
        issues.append(f"empty_csv_headers:{contract.file_name}")

    duplicates = sorted({header for header in headers if headers.count(header) > 1})
    for duplicate in duplicates:
        issues.append(f"duplicate_csv_header:{contract.file_name}:{duplicate}")

    header_set = set(headers)
    for required in contract.required_headers:
        if required not in header_set:
            issues.append(f"missing_csv_header:{contract.file_name}:{required}")

    if contract.exact_headers is not None:
        expected = _normalize_headers(contract.exact_headers)
        if headers != expected:
            issues.append(f"csv_header_set_mismatch:{contract.file_name}")

    return V6ContractValidationResult(valid=not issues, issues=tuple(issues))


def summarize_geojson_top_level(document: object) -> V6GeoJsonTopLevelSummary:
    """Return a GeoJSON top-level summary without reading feature bodies."""

    if not isinstance(document, Mapping):
        return V6GeoJsonTopLevelSummary(
            valid=False,
            top_level_keys=(),
            document_type=None,
            features_is_list=False,
            feature_count=None,
            issues=("geojson_not_object",),
        )

    top_level_keys = tuple(sorted(str(key) for key in document.keys()))
    document_type_raw = document.get("type")
    document_type = document_type_raw if isinstance(document_type_raw, str) else None
    features = document.get("features")
    features_is_list = isinstance(features, list)
    issues: list[str] = []

    if document_type != "FeatureCollection":
        issues.append("geojson_type_not_feature_collection")
    if not features_is_list:
        issues.append("geojson_features_not_list")

    return V6GeoJsonTopLevelSummary(
        valid=not issues,
        top_level_keys=top_level_keys,
        document_type=document_type,
        features_is_list=features_is_list,
        feature_count=len(features) if features_is_list else None,
        issues=tuple(issues),
    )


def _normalize_headers(headers: Sequence[str]) -> tuple[str, ...]:
    return tuple(str(header).removeprefix("\ufeff").strip() for header in headers)
