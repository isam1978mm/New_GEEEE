from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


AI_READY_METAL_HARDNESS_RECOVERY_SCHEMA_VERSION = (
    "ai_ready_metal_hardness_recovery_v1"
)
AI_READY_METAL_HARDNESS_RECOVERY_REPORT_RELATIVE_PATH = (
    "manifests/ai_ready_metal_hardness_recovery_report.json"
)

ALLOWED_SOURCE_STATUSES = {
    "exact_source_found",
    "partial_source_found",
    "no_source_found",
    "existing_app_equivalent_found",
    "unknown_needs_reference",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "ready_for_implementation_after_reference",
    "requires_reference_output",
    "requires_source_reconstruction",
    "blocked_no_source_formula",
    "blocked_missing_metadata_contract",
    "deferred",
}


@dataclass(frozen=True)
class AIReadyMetalHardnessRecoveryItem:
    id: str
    notebook_output: str
    family: str
    current_app_status: str
    source_status: str
    authoritative_source_available: bool
    source_reference: str
    expected_input_outputs: tuple[str, ...]
    expected_formula_summary: str
    expected_dtype: str
    expected_units: str
    expected_nodata_policy: str
    required_reference_outputs: tuple[str, ...]
    required_metadata: tuple[str, ...]
    target_mode: str
    classification: str
    http_servable: bool
    runtime_output_verified: bool
    notebook_value_parity_verified: bool
    implementation_status: str
    blocker: str
    recommended_next_action: str
    notes: str

    def __post_init__(self) -> None:
        if self.source_status not in ALLOWED_SOURCE_STATUSES:
            raise ValueError(f"unsupported source_status: {self.source_status}")
        if self.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"unsupported implementation_status: {self.implementation_status}"
            )
        if self.target_mode == "public_shared":
            raise ValueError("Phase 4H3 recovery items must not target public_shared")
        if self.http_servable:
            raise ValueError("Phase 4H3 recovery items must not default http_servable true")
        if self.runtime_output_verified:
            raise ValueError("Phase 4H3 recovery does not verify runtime output presence")
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 4H3 recovery does not verify notebook value parity")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_COMMON_REQUIRED_METADATA = (
    "dtype",
    "nodata or NaN policy",
    "CRS",
    "transform",
    "width",
    "height",
    "band count",
    "value tolerance",
)

_CHECKLIST: tuple[AIReadyMetalHardnessRecoveryItem, ...] = (
    AIReadyMetalHardnessRecoveryItem(
        id="ai_ready_640_metal_hardness",
        notebook_output="AI_READY_640_Metal_Hardness.tif",
        family="AI_READY semantic rasters",
        current_app_status=(
            "missing; notebook uses the raster as a spatial reference and expected-layer "
            "presence check, but the app has no standalone writer"
        ),
        source_status="partial_source_found",
        authoritative_source_available=False,
        source_reference=(
            "notebooks/new.ipynb lines around 45081, 45168, 45221, 45303, 45455, and "
            "45528 reuse AI_READY_640_Metal_Hardness.tif as a pixel-lock reference and "
            "expected output name inside later notebook export flows. No standalone writer "
            "formula is recovered in the notebook cells or current app source reviewed for "
            "Phase 4H3."
        ),
        expected_input_outputs=(),
        expected_formula_summary=(
            "Notebook evidence keeps the filename visible as a reference anchor and expected "
            "artifact, but no standalone writer formula, source raster contract, or patch "
            "derivation path is recovered."
        ),
        expected_dtype="unknown",
        expected_units=(
            "The notebook uses the raster as a spatial ruler and anchor layer. Frozen notebook "
            "reference outputs are still required to lock final unit wording and tolerance."
        ),
        expected_nodata_policy=(
            "Nodata, NaN persistence, and exact fill behavior remain unresolved until a frozen "
            "notebook reference is captured."
        ),
        required_reference_outputs=("AI_READY_640_Metal_Hardness.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="blocked_no_source_formula",
        blocker=(
            "Notebook references exist, but no authoritative writer formula, source-raster "
            "contract, or frozen metadata set is available."
        ),
        recommended_next_action=(
            "Recover the notebook writer cell or a frozen notebook reference bundle before any "
            "implementation or alias decision."
        ),
        notes=(
            "Treat the raster as a notebook-parity private semantic artifact. Existing app "
            "outputs are not automatic equivalents."
        ),
    ),
)


def get_ai_ready_metal_hardness_recovery_checklist() -> tuple[
    AIReadyMetalHardnessRecoveryItem, ...
]:
    """Return the Phase 4H3 recovery checklist for Metal Hardness parity."""

    return _CHECKLIST


def write_ai_ready_metal_hardness_recovery_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[AIReadyMetalHardnessRecoveryItem] | None = None,
    report_relative_path: str | Path = AI_READY_METAL_HARDNESS_RECOVERY_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON recovery report without creating TIFF or NPY outputs."""

    report_items = tuple(items or _CHECKLIST)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": AI_READY_METAL_HARDNESS_RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_source_status": _counts_by("source_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status", report_items
        ),
        "phase_4h3_formula_changes": False,
        "notes": (
            "Phase 4H3 is recovery and verification-contract work only. It does not "
            "implement Metal_Hardness, change semantic formulas, or introduce public serving."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[AIReadyMetalHardnessRecoveryItem],
) -> dict[str, int]:
    if field_name == "source_status":
        counts = {status: 0 for status in sorted(ALLOWED_SOURCE_STATUSES)}
    elif field_name == "implementation_status":
        counts = {status: 0 for status in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    else:
        raise ValueError(f"unsupported count field: {field_name}")

    for item in items:
        counts[getattr(item, field_name)] += 1
    return counts
