"""D2 — Frozen ``notebooks/new.ipynb`` reference-bundle validator.

This service validates a frozen D1 reference bundle that lives on the local
filesystem *outside Git*. It does not generate notebook outputs and performs no
parity math. It only checks that a supplied bundle is complete, readable, and
checksum-clean.

The default machine-readable result (``safe_summary``) contains counts only and
never echoes raw, potentially coordinate-bearing relative paths. Detailed
per-file findings are kept on the result object and surfaced only when a caller
explicitly opts in (e.g. the CLI ``--show-details`` flag, which is local-only).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

REFERENCE_MANIFEST_NAME = "reference_manifest.json"

REQUIRED_MANIFEST_FIELDS = (
    "source_notebook",
    "repo_commit",
    "created_at",
    "bundle_name",
    "files",
)
REQUIRED_FILE_FIELDS = ("relative_path", "sha256", "size_bytes")

_WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
_SHA256_HEX_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")
_CHUNK_SIZE = 1024 * 1024

# Issue kinds (stable identifiers used in summaries and tests).
ISSUE_INVALID_PATH = "invalid_path"
ISSUE_MISSING = "missing"
ISSUE_SIZE_MISMATCH = "size_mismatch"
ISSUE_CHECKSUM_MISMATCH = "checksum_mismatch"
ISSUE_EMPTY = "empty"

STATUS_VALID = "valid"
STATUS_INVALID = "invalid"
STATUS_ERROR = "error"


@dataclass(frozen=True)
class ReferenceFileIssue:
    """A single per-file finding. ``relative_path`` may be path-bearing."""

    relative_path: str
    issue: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"relative_path": self.relative_path, "issue": self.issue, "detail": self.detail}


@dataclass(frozen=True)
class ReferenceBundleValidationResult:
    status: str
    file_count: int = 0
    total_bytes: int = 0
    missing_count: int = 0
    size_mismatch_count: int = 0
    checksum_mismatch_count: int = 0
    invalid_path_count: int = 0
    empty_count: int = 0
    error: str | None = None
    bundle_name: str = ""
    issues: tuple[ReferenceFileIssue, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        return self.status == STATUS_VALID

    def safe_summary(self) -> dict[str, Any]:
        """Counts-only summary. Never includes raw relative paths or bundle text."""

        return {
            "status": self.status,
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
            "missing_count": self.missing_count,
            "size_mismatch_count": self.size_mismatch_count,
            "checksum_mismatch_count": self.checksum_mismatch_count,
            "invalid_path_count": self.invalid_path_count,
            "empty_count": self.empty_count,
            "error": self.error,
        }

    def detailed_report(self) -> dict[str, Any]:
        """Local-only report including per-file findings and the bundle name."""

        report = self.safe_summary()
        report["bundle_name"] = self.bundle_name
        report["issues"] = [issue.to_dict() for issue in self.issues]
        return report


def _error(message: str) -> ReferenceBundleValidationResult:
    return ReferenceBundleValidationResult(status=STATUS_ERROR, error=message)


def _is_safe_relative_path(raw: str, bundle_root: Path) -> bool:
    if not isinstance(raw, str) or not raw:
        return False
    if raw.startswith(("/", "\\")):
        return False
    if _WINDOWS_DRIVE_PATTERN.match(raw):
        return False
    segments = re.split(r"[\\/]", raw)
    if any(segment in {"", ".", ".."} for segment in segments):
        return False
    candidate = (bundle_root / raw).resolve()
    root = bundle_root.resolve()
    return root == candidate or root in candidate.parents


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_reference_bundle(
    bundle_dir: str | Path,
    *,
    allow_empty_files: bool = False,
) -> ReferenceBundleValidationResult:
    """Validate a frozen D1 reference bundle directory.

    Returns a result whose ``status`` is one of ``valid``/``invalid``/``error``.
    ``error`` covers structural problems (missing directory/manifest, unreadable
    or malformed manifest). ``invalid`` covers per-file problems (missing files,
    size/checksum mismatches, unsafe paths, unexpected empty files).
    """

    bundle_root = Path(bundle_dir)
    if not bundle_root.is_dir():
        return _error("Reference bundle directory does not exist.")

    manifest_path = bundle_root / REFERENCE_MANIFEST_NAME
    if not manifest_path.is_file():
        return _error(f"{REFERENCE_MANIFEST_NAME} is missing from the bundle.")

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return _error(f"{REFERENCE_MANIFEST_NAME} could not be read or parsed: {exc}")

    if not isinstance(payload, Mapping):
        return _error(f"{REFERENCE_MANIFEST_NAME} must contain a JSON object.")

    missing_fields = [field_name for field_name in REQUIRED_MANIFEST_FIELDS if field_name not in payload]
    if missing_fields:
        return _error(f"Manifest is missing required fields: {', '.join(sorted(missing_fields))}.")

    files = payload.get("files")
    if not isinstance(files, list):
        return _error("Manifest 'files' must be a list.")

    bundle_name = payload.get("bundle_name")
    bundle_name = bundle_name if isinstance(bundle_name, str) else ""

    issues: list[ReferenceFileIssue] = []
    total_bytes = 0
    missing_count = 0
    size_mismatch_count = 0
    checksum_mismatch_count = 0
    invalid_path_count = 0
    empty_count = 0

    for index, entry in enumerate(files):
        if not isinstance(entry, Mapping):
            return _error(f"Manifest file entry at index {index} must be an object.")
        missing_entry_fields = [name for name in REQUIRED_FILE_FIELDS if name not in entry]
        if missing_entry_fields:
            return _error(
                f"Manifest file entry at index {index} is missing fields: "
                f"{', '.join(sorted(missing_entry_fields))}."
            )

        relative_path = entry.get("relative_path")
        declared_sha = entry.get("sha256")
        declared_size = entry.get("size_bytes")
        if not isinstance(relative_path, str):
            return _error(f"Manifest file entry at index {index} has a non-string relative_path.")
        if not isinstance(declared_sha, str) or not _SHA256_HEX_PATTERN.match(declared_sha):
            return _error(
                f"Manifest file entry at index {index} has an invalid sha256 value."
            )
        if not isinstance(declared_size, int) or isinstance(declared_size, bool) or declared_size < 0:
            return _error(
                f"Manifest file entry at index {index} has an invalid size_bytes value."
            )

        total_bytes += declared_size

        if not _is_safe_relative_path(relative_path, bundle_root):
            invalid_path_count += 1
            issues.append(
                ReferenceFileIssue(
                    relative_path=relative_path,
                    issue=ISSUE_INVALID_PATH,
                    detail="Path is absolute or escapes the bundle root.",
                )
            )
            continue

        file_path = (bundle_root / relative_path).resolve()
        if not file_path.is_file():
            missing_count += 1
            issues.append(
                ReferenceFileIssue(
                    relative_path=relative_path,
                    issue=ISSUE_MISSING,
                    detail="Listed file does not exist in the bundle.",
                )
            )
            continue

        actual_size = file_path.stat().st_size
        if actual_size == 0 and not allow_empty_files:
            empty_count += 1
            issues.append(
                ReferenceFileIssue(
                    relative_path=relative_path,
                    issue=ISSUE_EMPTY,
                    detail="File is empty and empty files are not allowed.",
                )
            )
            # An empty file is also a size/checksum concern; continue to avoid
            # double-reporting the same file under multiple issue kinds.
            continue

        if actual_size != declared_size:
            size_mismatch_count += 1
            issues.append(
                ReferenceFileIssue(
                    relative_path=relative_path,
                    issue=ISSUE_SIZE_MISMATCH,
                    detail=f"Declared {declared_size} bytes, found {actual_size} bytes.",
                )
            )
            continue

        actual_sha = _sha256_of(file_path)
        if actual_sha.lower() != declared_sha.lower():
            checksum_mismatch_count += 1
            issues.append(
                ReferenceFileIssue(
                    relative_path=relative_path,
                    issue=ISSUE_CHECKSUM_MISMATCH,
                    detail="SHA256 does not match the manifest.",
                )
            )

    status = STATUS_VALID if not issues else STATUS_INVALID
    return ReferenceBundleValidationResult(
        status=status,
        file_count=len(files),
        total_bytes=total_bytes,
        missing_count=missing_count,
        size_mismatch_count=size_mismatch_count,
        checksum_mismatch_count=checksum_mismatch_count,
        invalid_path_count=invalid_path_count,
        empty_count=empty_count,
        error=None,
        bundle_name=bundle_name,
        issues=tuple(issues),
    )
