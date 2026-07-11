from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence
import zipfile

ZIP_READINESS_CONTRACT = "v6_real_zip_readiness_v1"


def build_v6_zip_readiness_report(
    *,
    zip_path: str | Path,
    inventory_path: str | Path,
    payload_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate ZIP/inventory pairing without exposing rows or geometry.

    This checks the generated package as a filesystem artifact: the sidecar inventory
    must be present inside the ZIP byte-for-byte, every payload record must be present,
    and every ZIP payload entry must match the inventory size and sha256.
    """

    zip_file = Path(zip_path)
    inventory_file = Path(inventory_path)
    expected_records = _record_map(payload_records)
    expected_entries = set(expected_records) | {inventory_file.name}
    issues: list[str] = []
    zip_names: list[str] = []

    try:
        inventory_bytes = inventory_file.read_bytes()
        inventory_payload = json.loads(inventory_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        inventory_bytes = b""
        inventory_payload = {}
        issues.append("inventory_sidecar_unreadable")

    sidecar_records = _record_map(inventory_payload.get("records", []) if isinstance(inventory_payload, dict) else [])
    if sidecar_records != expected_records:
        issues.append("inventory_sidecar_records_mismatch")

    try:
        with zipfile.ZipFile(zip_file, "r") as archive:
            zip_names = archive.namelist()
            duplicate_names = sorted({name for name in zip_names if zip_names.count(name) > 1})
            if duplicate_names:
                issues.append("zip_duplicate_entries")
            zip_name_set = set(zip_names)
            missing_entries = sorted(expected_entries - zip_name_set)
            extra_entries = sorted(zip_name_set - expected_entries)
            if missing_entries:
                issues.append("zip_missing_expected_entries")
            if extra_entries:
                issues.append("zip_has_unexpected_entries")
            if inventory_file.name in zip_name_set:
                try:
                    zip_inventory_bytes = archive.read(inventory_file.name)
                except KeyError:
                    zip_inventory_bytes = b""
                if zip_inventory_bytes != inventory_bytes:
                    issues.append("zip_inventory_entry_mismatch")
            for name, record in sorted(expected_records.items()):
                if name not in zip_name_set:
                    continue
                content = archive.read(name)
                if len(content) != record["size_bytes"]:
                    issues.append(f"payload_size_mismatch:{name}")
                if _sha256_bytes(content) != record["sha256"]:
                    issues.append(f"payload_sha256_mismatch:{name}")
    except (OSError, zipfile.BadZipFile):
        issues.append("zip_unreadable")

    unique_issues = sorted(set(issues))
    return {
        "contract": ZIP_READINESS_CONTRACT,
        "zip_ready": not unique_issues,
        "zip_filename": zip_file.name,
        "inventory_filename": inventory_file.name,
        "expected_payload_count": len(expected_records),
        "expected_zip_entry_count": len(expected_entries),
        "zip_entry_count": len(zip_names),
        "issue_count": len(unique_issues),
        "issues": unique_issues,
    }


def _record_map(records: object) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    if not isinstance(records, list) and not isinstance(records, tuple):
        return mapped
    for item in records:
        if not isinstance(item, Mapping):
            continue
        file_name = item.get("file")
        sha256 = item.get("sha256")
        try:
            size_bytes = int(item.get("size_bytes"))
        except (TypeError, ValueError):
            continue
        if isinstance(file_name, str) and file_name and isinstance(sha256, str) and sha256:
            mapped[file_name] = {"size_bytes": size_bytes, "sha256": sha256}
    return mapped


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
