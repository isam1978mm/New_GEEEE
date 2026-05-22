from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageArtifact, build_stage_artifact

REFERENCE_LOCATOR_REPORT_NAME = "reference_locator_inventory.json"
SECRET_DIRECTORY_NAMES = {
    ".aws",
    ".git",
    ".gnupg",
    ".kube",
    ".ssh",
    "credential",
    "credentials",
    "key_material",
    "keys",
    "private",
    "private_keys",
    "secret",
    "secrets",
    "service-account-keys",
}


@dataclass(slots=True)
class ReferenceMatch:
    requested_name: str
    filename: str
    search_root: str
    relative_path: str


@dataclass(slots=True)
class ReferenceLocatorResult:
    requested_names: list[str]
    searched_roots: list[str]
    matches: list[ReferenceMatch]
    skipped_secret_roots: list[str]
    skipped_secret_directories: list[str]
    missing_roots: list[str]


def locate_reference_files(search_roots: list[Path], requested_names: list[str]) -> ReferenceLocatorResult:
    normalized_requests = {name.casefold(): name for name in requested_names}
    matches: list[ReferenceMatch] = []
    searched_roots: list[str] = []
    skipped_secret_roots: list[str] = []
    skipped_secret_directories: list[str] = []
    missing_roots: list[str] = []

    for root in search_roots:
        resolved_root = root.resolve()
        if not resolved_root.exists():
            missing_roots.append(resolved_root.as_posix())
            continue
        if _is_secret_path(resolved_root):
            skipped_secret_roots.append(resolved_root.as_posix())
            continue

        searched_roots.append(resolved_root.as_posix())
        if resolved_root.is_file():
            _maybe_add_file_match(
                resolved_root,
                search_root=resolved_root.parent,
                normalized_requests=normalized_requests,
                matches=matches,
            )
            continue

        for current_root, dirnames, filenames in os.walk(resolved_root, topdown=True):
            current_path = Path(current_root)
            allowed_dirnames: list[str] = []
            for dirname in dirnames:
                candidate = current_path / dirname
                if _is_secret_name(dirname):
                    skipped_secret_directories.append(candidate.resolve().as_posix())
                    continue
                allowed_dirnames.append(dirname)
            dirnames[:] = allowed_dirnames

            for filename in filenames:
                _maybe_add_file_match(
                    current_path / filename,
                    search_root=resolved_root,
                    normalized_requests=normalized_requests,
                    matches=matches,
                )

    return ReferenceLocatorResult(
        requested_names=list(requested_names),
        searched_roots=searched_roots,
        matches=sorted(matches, key=lambda item: (item.requested_name, item.search_root, item.relative_path)),
        skipped_secret_roots=sorted(skipped_secret_roots),
        skipped_secret_directories=sorted(skipped_secret_directories),
        missing_roots=sorted(missing_roots),
    )


def build_reference_locator_public_summary(result: ReferenceLocatorResult) -> dict[str, Any]:
    return {
        "requested_reference_count": len(result.requested_names),
        "searched_root_count": len(result.searched_roots),
        "match_count": len(result.matches),
        "matched_filenames": sorted({match.filename for match in result.matches}),
        "skipped_secret_root_count": len(result.skipped_secret_roots),
        "skipped_secret_directory_count": len(result.skipped_secret_directories),
        "missing_root_count": len(result.missing_roots),
    }


def write_reference_locator_inventory_report(
    run_dir: Path,
    result: ReferenceLocatorResult,
) -> Path:
    reference_dir = run_dir / "full_job" / "reference"
    reference_dir.mkdir(parents=True, exist_ok=True)
    report_path = reference_dir / REFERENCE_LOCATOR_REPORT_NAME
    payload = {
        "report_type": "reference_locator_inventory",
        "requested_names": result.requested_names,
        "searched_roots": result.searched_roots,
        "matches": [asdict(match) for match in result.matches],
        "skipped_secret_roots": result.skipped_secret_roots,
        "skipped_secret_directories": result.skipped_secret_directories,
        "missing_roots": result.missing_roots,
        "public_summary": build_reference_locator_public_summary(result),
    }
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return report_path


def build_reference_locator_inventory_artifact(run_dir: Path, report_path: Path) -> StageArtifact:
    return build_stage_artifact(
        name="reference_locator_inventory",
        relative_path=report_path.relative_to(run_dir).as_posix(),
        artifact_class=ArtifactClass.FILESYSTEM_ONLY,
        size_bytes=report_path.stat().st_size,
        http_servable=False,
    )


def _maybe_add_file_match(
    path: Path,
    *,
    search_root: Path,
    normalized_requests: dict[str, str],
    matches: list[ReferenceMatch],
) -> None:
    requested_name = normalized_requests.get(path.name.casefold())
    if requested_name is None:
        return
    matches.append(
        ReferenceMatch(
            requested_name=requested_name,
            filename=path.name,
            search_root=search_root.resolve().as_posix(),
            relative_path=path.resolve().relative_to(search_root.resolve()).as_posix(),
        )
    )


def _is_secret_path(path: Path) -> bool:
    return any(_is_secret_name(part) for part in path.parts)


def _is_secret_name(name: str) -> bool:
    return name.casefold() in SECRET_DIRECTORY_NAMES
