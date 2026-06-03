from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable


PARITY_SCHEMA_VERSION = "parity_manifest_v1"
PARITY_ROOT_DIRNAME = "parity"
MANIFESTS_DIRNAME = "manifests"

STANDARD_PARITY_SUBDIRS = (
    "root",
    "DEM_GEO8_TIFS",
    "GEOTIFF_RADAR_BANDS",
    "NPY_RADAR_BANDS",
    "NPY_STACKS",
    "OPT",
    "QA",
    "kmz",
    "maps",
    "navigation",
    "experimental",
)

TARGET_MODES = {
    "core_app",
    "notebook_parity",
    "experimental_private",
    "public_shared",
    "not_applicable",
}

ARTIFACT_CLASSES = {
    "LOCAL_SENSITIVE",
    "REDACTED_PUBLIC",
    "PREVIEW_ONLY",
    "FILESYSTEM_ONLY",
}

CLASSIFICATIONS = {
    "app-native",
    "notebook-parity",
    "experimental/private",
    "QA/provenance",
    "coordinate-bearing",
    "notebook-parity semantic raster stage",
    "notebook-parity report/semantic raster stage",
    "probability-classifier output",
}


class ParityPathError(ValueError):
    """Raised when a parity helper path would escape the run directory."""


class ParityManifestError(ValueError):
    """Raised when manifest metadata violates the Phase 1 parity contract."""


def _coerce_relative_path(value: str | Path, *, field_name: str) -> Path:
    raw = Path(value)
    if raw.is_absolute():
        raise ParityPathError(f"{field_name} must be relative")
    if str(value).strip() == "":
        raise ParityPathError(f"{field_name} must not be empty")
    if ".." in raw.parts:
        raise ParityPathError(f"{field_name} must not contain path traversal")
    return raw


def _ensure_inside(base_dir: Path, candidate: Path) -> Path:
    base = base_dir.resolve()
    resolved = candidate.resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise ParityPathError(f"path escapes run directory: {candidate}") from exc
    return resolved


def resolve_run_output_path(run_dir: str | Path, run_relative_path: str | Path) -> Path:
    """Resolve a run-relative path while preventing traversal outside run_dir."""

    base = Path(run_dir)
    relative = _coerce_relative_path(run_relative_path, field_name="run_relative_path")
    return _ensure_inside(base, base / relative)


def resolve_parity_output_path(run_dir: str | Path, parity_relative_path: str | Path) -> Path:
    """Resolve a parity-relative output path under <run_dir>/parity/."""

    base = Path(run_dir) / PARITY_ROOT_DIRNAME
    relative = _coerce_relative_path(
        parity_relative_path,
        field_name="parity_relative_path",
    )
    return _ensure_inside(base, base / relative)


def ensure_standard_parity_dirs(run_dir: str | Path) -> dict[str, Path]:
    """Create standard Phase 1 parity directories under a run directory."""

    run_root = Path(run_dir)
    run_root.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    parity_root = resolve_run_output_path(run_root, PARITY_ROOT_DIRNAME)
    parity_root.mkdir(parents=True, exist_ok=True)
    paths[PARITY_ROOT_DIRNAME] = parity_root

    manifests_root = resolve_run_output_path(run_root, MANIFESTS_DIRNAME)
    manifests_root.mkdir(parents=True, exist_ok=True)
    paths[MANIFESTS_DIRNAME] = manifests_root

    for subdir in STANDARD_PARITY_SUBDIRS:
        target = resolve_parity_output_path(run_root, subdir)
        target.mkdir(parents=True, exist_ok=True)
        paths[subdir] = target

    return paths


@dataclass(frozen=True)
class ParityManifestEntry:
    source_path: str
    parity_path: str
    notebook_name_or_pattern: str
    family: str
    classification: str
    artifact_class: str
    target_mode: str = "notebook_parity"
    http_servable: bool = False
    requires_coordinates: bool = False
    probability_only_required: bool = False
    runtime_output_verified: bool = False
    notebook_value_parity_verified: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if self.target_mode not in TARGET_MODES:
            raise ParityManifestError(f"unknown target_mode: {self.target_mode}")
        if self.artifact_class not in ARTIFACT_CLASSES:
            raise ParityManifestError(f"unknown artifact_class: {self.artifact_class}")
        if self.classification not in CLASSIFICATIONS:
            raise ParityManifestError(f"unknown classification: {self.classification}")
        if self.requires_coordinates and self.http_servable:
            raise ParityManifestError(
                "coordinate-bearing parity entries cannot be HTTP servable"
            )
        if (
            self.classification == "probability-classifier output"
            and not self.probability_only_required
        ):
            raise ParityManifestError(
                "probability-classifier outputs must set probability_only_required"
            )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def write_parity_manifest(
    run_dir: str | Path,
    run_id: str,
    entries: Iterable[ParityManifestEntry],
    *,
    created_at: datetime | None = None,
    manifest_name: str = "parity_manifest.json",
) -> Path:
    """Write a run-local parity manifest JSON and return its path."""

    ensure_standard_parity_dirs(run_dir)
    manifest_relative = _coerce_relative_path(
        manifest_name,
        field_name="manifest_name",
    )
    manifest_path = resolve_run_output_path(
        run_dir,
        Path(MANIFESTS_DIRNAME) / manifest_relative,
    )

    timestamp = created_at or datetime.now(UTC)
    payload = {
        "schema_version": PARITY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": timestamp.isoformat(),
        "parity_root": PARITY_ROOT_DIRNAME,
        "entries": [entry.to_dict() for entry in entries],
    }
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path
