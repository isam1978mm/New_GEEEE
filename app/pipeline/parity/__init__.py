"""Helpers for future notebook-parity output manifests.

This package is intentionally not wired into the live pipeline in Phase 1.
"""

from app.pipeline.parity.manifest import (
    PARITY_SCHEMA_VERSION,
    STANDARD_PARITY_SUBDIRS,
    ParityManifestEntry,
    ParityManifestError,
    ParityPathError,
    ensure_standard_parity_dirs,
    resolve_parity_output_path,
    resolve_run_output_path,
    write_parity_manifest,
)

__all__ = [
    "PARITY_SCHEMA_VERSION",
    "STANDARD_PARITY_SUBDIRS",
    "ParityManifestEntry",
    "ParityManifestError",
    "ParityPathError",
    "ensure_standard_parity_dirs",
    "resolve_parity_output_path",
    "resolve_run_output_path",
    "write_parity_manifest",
]
