"""Read-only validator for the external frozen V6 package.

This module streams ZIP members and inventory metadata only. It never extracts
or copies package artifacts into the repository or a run directory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping
import zipfile


STATUS_VERIFIED = "verified"
STATUS_INVALID = "invalid"
STATUS_ERROR = "error"

INTEGRATION_STATUS_VERIFIED = "verified_read_only_external_package"
INTEGRATION_STATUS_INVALID = "invalid_external_package"
INTEGRATION_STATUS_ERROR = "error_external_package"

ARTIFACT_POLICY = "external_generated_artifacts_remain_outside_git_filesystem_only"

EXPECTED_SHA_PATTERN = re.compile(r"\b[a-fA-F0-9]{64}\b")
TIMESTAMPED_TOP25_PATTERN = re.compile(
    r"^lawful_gee_candidate_scout_top_25_\d{8}T\d{6}Z\.(csv|geojson)$"
)

CATEGORY_NAMES = (
    "candidate_tables",
    "request_zones",
    "diagnostics",
    "quote_templates",
    "summary_text",
    "visual_map",
    "unknown",
)

_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class V6InventoryRecord:
    file: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class V6PackageValidationResult:
    package_path: str
    hash_status: str
    inventory_status: str
    payload_count: int
    category_counts: dict[str, int]
    artifact_policy: str
    integration_status: str
    expected_hash_present: bool
    zip_exists: bool
    inventory_exists: bool
    zip_entry_count_including_inventory: int = 0
    issue_counts: dict[str, int] = field(default_factory=dict)

    @property
    def is_verified(self) -> bool:
        return self.integration_status == INTEGRATION_STATUS_VERIFIED

    def safe_summary(self) -> dict[str, Any]:
        """Return a path-safe operational summary with no row or geometry data."""

        return {
            "package_path": self.package_path,
            "hash_status": self.hash_status,
            "inventory_status": self.inventory_status,
            "payload_count": self.payload_count,
            "category_counts": dict(self.category_counts),
            "artifact_policy": self.artifact_policy,
            "integration_status": self.integration_status,
            "expected_hash_present": self.expected_hash_present,
            "zip_exists": self.zip_exists,
            "inventory_exists": self.inventory_exists,
            "zip_entry_count_including_inventory": self.zip_entry_count_including_inventory,
            "issue_counts": dict(self.issue_counts),
        }


def validate_v6_package(
    *,
    zip_path: str | Path,
    inventory_path: str | Path,
    reference_doc_path: str | Path = "docs/V6_FROZEN_REFERENCE.md",
) -> V6PackageValidationResult:
    """Validate a frozen V6 package without extracting generated artifacts."""

    package = Path(zip_path)
    inventory = Path(inventory_path)
    reference_doc = Path(reference_doc_path)

    issue_counts: dict[str, int] = {}
    expected_sha = _read_expected_sha256(reference_doc)
    expected_sha_present = expected_sha is not None

    if not package.is_file():
        _increment(issue_counts, "missing_zip")
        return _result(
            package=package,
            hash_status=STATUS_ERROR,
            inventory_status=STATUS_ERROR if not inventory.is_file() else STATUS_VERIFIED,
            payload_count=0,
            category_counts=_empty_category_counts(),
            integration_status=INTEGRATION_STATUS_ERROR,
            expected_sha_present=expected_sha_present,
            zip_exists=False,
            inventory_exists=inventory.is_file(),
            issue_counts=issue_counts,
        )

    if not inventory.is_file():
        _increment(issue_counts, "missing_inventory")
        return _result(
            package=package,
            hash_status=_hash_status_for_package(package, expected_sha, issue_counts),
            inventory_status=STATUS_ERROR,
            payload_count=0,
            category_counts=_empty_category_counts(),
            integration_status=INTEGRATION_STATUS_ERROR,
            expected_sha_present=expected_sha_present,
            zip_exists=True,
            inventory_exists=False,
            issue_counts=issue_counts,
        )

    hash_status = _hash_status_for_package(package, expected_sha, issue_counts)
    non_inventory_issue_count = sum(issue_counts.values())
    records, inventory_status = _read_inventory_records(inventory, issue_counts)
    if records is None:
        return _result(
            package=package,
            hash_status=hash_status,
            inventory_status=inventory_status,
            payload_count=0,
            category_counts=_empty_category_counts(),
            integration_status=INTEGRATION_STATUS_ERROR,
            expected_sha_present=expected_sha_present,
            zip_exists=True,
            inventory_exists=True,
            issue_counts=issue_counts,
        )

    zip_payload = _validate_zip_payload(
        package=package,
        inventory_name=inventory.name,
        records=records,
        issue_counts=issue_counts,
    )
    zip_entry_count, payload_count, category_counts = zip_payload

    inventory_issue_count = sum(issue_counts.values()) - non_inventory_issue_count
    inventory_status = STATUS_VERIFIED if inventory_issue_count == 0 else STATUS_INVALID
    integration_status = (
        INTEGRATION_STATUS_VERIFIED
        if hash_status == STATUS_VERIFIED and inventory_status == STATUS_VERIFIED
        else INTEGRATION_STATUS_INVALID
    )

    return _result(
        package=package,
        hash_status=hash_status,
        inventory_status=inventory_status,
        payload_count=payload_count,
        category_counts=category_counts,
        integration_status=integration_status,
        expected_sha_present=expected_sha_present,
        zip_exists=True,
        inventory_exists=True,
        zip_entry_count_including_inventory=zip_entry_count,
        issue_counts=issue_counts,
    )


def _result(
    *,
    package: Path,
    hash_status: str,
    inventory_status: str,
    payload_count: int,
    category_counts: dict[str, int],
    integration_status: str,
    expected_sha_present: bool,
    zip_exists: bool,
    inventory_exists: bool,
    issue_counts: dict[str, int],
    zip_entry_count_including_inventory: int = 0,
) -> V6PackageValidationResult:
    return V6PackageValidationResult(
        package_path=str(package),
        hash_status=hash_status,
        inventory_status=inventory_status,
        payload_count=payload_count,
        category_counts=category_counts,
        artifact_policy=ARTIFACT_POLICY,
        integration_status=integration_status,
        expected_hash_present=expected_sha_present,
        zip_exists=zip_exists,
        inventory_exists=inventory_exists,
        zip_entry_count_including_inventory=zip_entry_count_including_inventory,
        issue_counts=dict(sorted(issue_counts.items())),
    )


def _read_expected_sha256(reference_doc: Path) -> str | None:
    try:
        text = reference_doc.read_text(encoding="utf-8")
    except OSError:
        return None
    matches = EXPECTED_SHA_PATTERN.findall(text)
    return matches[0].lower() if matches else None


def _hash_status_for_package(
    package: Path,
    expected_sha: str | None,
    issue_counts: dict[str, int],
) -> str:
    if expected_sha is None:
        _increment(issue_counts, "missing_documented_sha256")
        return STATUS_ERROR
    actual_sha = _sha256_path(package)
    if actual_sha.lower() != expected_sha.lower():
        _increment(issue_counts, "zip_sha256_mismatch")
        return STATUS_INVALID
    return STATUS_VERIFIED


def _read_inventory_records(
    inventory: Path,
    issue_counts: dict[str, int],
) -> tuple[dict[str, V6InventoryRecord] | None, str]:
    try:
        payload = json.loads(inventory.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        _increment(issue_counts, "inventory_parse_error")
        return None, STATUS_ERROR

    if not isinstance(payload, Mapping):
        _increment(issue_counts, "inventory_not_object")
        return None, STATUS_ERROR

    records_raw = payload.get("records")
    if not isinstance(records_raw, list):
        _increment(issue_counts, "inventory_records_missing")
        return None, STATUS_ERROR

    declared_count = payload.get("file_count")
    if declared_count != len(records_raw):
        _increment(issue_counts, "inventory_file_count_mismatch")

    records: dict[str, V6InventoryRecord] = {}
    for item in records_raw:
        if not isinstance(item, Mapping):
            _increment(issue_counts, "inventory_record_invalid")
            continue
        file_name = item.get("file")
        size_bytes = item.get("size_bytes")
        sha256 = item.get("sha256")
        if not _is_safe_member_name(file_name):
            _increment(issue_counts, "inventory_file_name_invalid")
            continue
        if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0:
            _increment(issue_counts, "inventory_size_invalid")
            continue
        if not isinstance(sha256, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", sha256):
            _increment(issue_counts, "inventory_sha256_invalid")
            continue
        if file_name in records:
            _increment(issue_counts, "inventory_duplicate_file")
            continue
        records[file_name] = V6InventoryRecord(
            file=file_name,
            size_bytes=size_bytes,
            sha256=sha256.lower(),
        )

    return records, STATUS_VERIFIED


def _validate_zip_payload(
    *,
    package: Path,
    inventory_name: str,
    records: dict[str, V6InventoryRecord],
    issue_counts: dict[str, int],
) -> tuple[int, int, dict[str, int]]:
    category_counts = _empty_category_counts()
    payload_names: set[str] = set()

    try:
        with zipfile.ZipFile(package) as archive:
            infos = [info for info in archive.infolist() if not info.is_dir()]
            for info in infos:
                if not _is_safe_member_name(info.filename):
                    _increment(issue_counts, "zip_member_name_invalid")
                    continue
                if info.filename == inventory_name:
                    continue

                payload_names.add(info.filename)
                category_counts[_category_for_file(info.filename)] += 1
                record = records.get(info.filename)
                if record is None:
                    _increment(issue_counts, "zip_member_missing_inventory_record")
                    continue
                if info.file_size != record.size_bytes:
                    _increment(issue_counts, "zip_member_size_mismatch")
                actual_sha = _sha256_zip_member(archive, info)
                if actual_sha.lower() != record.sha256.lower():
                    _increment(issue_counts, "zip_member_sha256_mismatch")
    except zipfile.BadZipFile:
        _increment(issue_counts, "zip_parse_error")
        return 0, 0, category_counts

    missing_from_zip = set(records) - payload_names
    for _name in missing_from_zip:
        _increment(issue_counts, "inventory_record_missing_zip_member")

    return len(infos), len(payload_names), category_counts


def _is_safe_member_name(value: object) -> bool:
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


def _category_for_file(name: str) -> str:
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


def _empty_category_counts() -> dict[str, int]:
    return {name: 0 for name in CATEGORY_NAMES}


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


def _increment(counts: dict[str, int], key: str) -> None:
    counts[key] = counts.get(key, 0) + 1
