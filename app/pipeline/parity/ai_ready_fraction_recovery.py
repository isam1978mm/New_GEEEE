from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


AI_READY_FRACTION_RECOVERY_SCHEMA_VERSION = "ai_ready_fraction_recovery_v1"
AI_READY_FRACTION_RECOVERY_REPORT_RELATIVE_PATH = (
    "manifests/ai_ready_fraction_recovery_report.json"
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

_COMMON_SOURCE_REFERENCE = (
    "notebooks/new.ipynb lines around 45229-45267 keep the exact fraction builder and "
    "export loop: Sentinel-2 bands B1, B2, B4, B8, B8A, B11, B12 are median-composited, "
    "extract_unmixed_targets(image) builds four fraction rasters, purity_mask = B8 > B4 "
    "is inverted for masking, and each selected band is exported after reprojecting to "
    "drive_crs and drive_transform sourced from AI_READY_640_Metal_Hardness.tif. "
    "Later monitor cells around 45303-45310 and 45455-45462 keep the expected output "
    "filenames visible."
)

_COMMON_CURRENT_STATUS = (
    "missing; notebook source and export flow are visible, but the app has no standalone "
    "writer for the Fraction_* semantic rasters"
)

_COMMON_EXPECTED_INPUT_OUTPUTS = (
    "S2:B1",
    "S2:B2",
    "S2:B4",
    "S2:B8",
    "S2:B8A",
    "S2:B11",
    "S2:B12",
    "AI_READY_640_Metal_Hardness.tif",
)

_COMMON_UNITS = (
    "Notebook formulas produce ratio or normalized-difference semantic rasters from "
    "Sentinel-2 reflectance bands, then apply the inverted purity mask. Frozen notebook "
    "references are still required to lock final unit wording and tolerance."
)

_COMMON_NODATA = (
    "Masking behavior is visible through nano_tensors = unmixed.updateMask(purity_mask.Not()), "
    "but the exact exported nodata or NaN persistence remains unresolved until frozen "
    "notebook references are captured."
)


@dataclass(frozen=True)
class AIReadyFractionRecoveryItem:
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
            raise ValueError("Phase 4H4 recovery items must not target public_shared")
        if self.http_servable:
            raise ValueError("Phase 4H4 recovery items must not default http_servable true")
        if self.runtime_output_verified:
            raise ValueError("Phase 4H4 recovery does not verify runtime output presence")
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 4H4 recovery does not verify notebook value parity")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_CHECKLIST: tuple[AIReadyFractionRecoveryItem, ...] = (
    AIReadyFractionRecoveryItem(
        id="ai_ready_640_fraction_gold",
        notebook_output="AI_READY_640_Fraction_Gold.tif",
        family="AI_READY semantic rasters",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=_COMMON_SOURCE_REFERENCE,
        expected_input_outputs=_COMMON_EXPECTED_INPUT_OUTPUTS,
        expected_formula_summary=(
            "Fraction_Gold = (B12 - B11) / (B12 + B11), then masked by purity_mask.Not() "
            "before export on the Metal_Hardness-aligned grid."
        ),
        expected_dtype="unknown",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=("AI_READY_640_Fraction_Gold.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "The source cell and export flow are visible, but frozen notebook references are "
            "still required to lock the final metadata and numeric tolerance."
        ),
        recommended_next_action=(
            "Capture frozen notebook Fraction_Gold output and run the Phase 4H4 verifier "
            "before any implementation slice."
        ),
        notes=(
            "Existing app outputs are not automatic equivalents. The Metal_Hardness "
            "reference is a grid anchor, not a replacement output."
        ),
    ),
    AIReadyFractionRecoveryItem(
        id="ai_ready_640_fraction_pottery",
        notebook_output="AI_READY_640_Fraction_Pottery.tif",
        family="AI_READY semantic rasters",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=_COMMON_SOURCE_REFERENCE,
        expected_input_outputs=_COMMON_EXPECTED_INPUT_OUTPUTS,
        expected_formula_summary=(
            "Fraction_Pottery = B11 / (B8A + 0.0001), then masked by purity_mask.Not() "
            "before export on the Metal_Hardness-aligned grid."
        ),
        expected_dtype="unknown",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=("AI_READY_640_Fraction_Pottery.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "The source cell and export flow are visible, but frozen notebook references are "
            "still required to lock the final metadata and numeric tolerance."
        ),
        recommended_next_action=(
            "Capture frozen notebook Fraction_Pottery output and run the Phase 4H4 verifier "
            "before any implementation slice."
        ),
        notes=(
            "Existing app outputs are not automatic equivalents. The Metal_Hardness "
            "reference is a grid anchor, not a replacement output."
        ),
    ),
    AIReadyFractionRecoveryItem(
        id="ai_ready_640_fraction_carbon_age",
        notebook_output="AI_READY_640_Fraction_Carbon_Age.tif",
        family="AI_READY semantic rasters",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=_COMMON_SOURCE_REFERENCE,
        expected_input_outputs=_COMMON_EXPECTED_INPUT_OUTPUTS,
        expected_formula_summary=(
            "Fraction_Carbon_Age = normalizedDifference(B11, B12), then masked by "
            "purity_mask.Not() before export on the Metal_Hardness-aligned grid."
        ),
        expected_dtype="unknown",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=("AI_READY_640_Fraction_Carbon_Age.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "The source cell and export flow are visible, but frozen notebook references are "
            "still required to lock the final metadata and numeric tolerance."
        ),
        recommended_next_action=(
            "Capture frozen notebook Fraction_Carbon_Age output and run the Phase 4H4 verifier "
            "before any implementation slice."
        ),
        notes=(
            "Existing app outputs are not automatic equivalents. The Metal_Hardness "
            "reference is a grid anchor, not a replacement output."
        ),
    ),
    AIReadyFractionRecoveryItem(
        id="ai_ready_640_fraction_silver_lead",
        notebook_output="AI_READY_640_Fraction_Silver_Lead.tif",
        family="AI_READY semantic rasters",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=_COMMON_SOURCE_REFERENCE,
        expected_input_outputs=_COMMON_EXPECTED_INPUT_OUTPUTS,
        expected_formula_summary=(
            "Fraction_Silver_Lead = B2 / (B4 + 0.0001), then masked by purity_mask.Not() "
            "before export on the Metal_Hardness-aligned grid."
        ),
        expected_dtype="unknown",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=("AI_READY_640_Fraction_Silver_Lead.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "The source cell and export flow are visible, but frozen notebook references are "
            "still required to lock the final metadata and numeric tolerance."
        ),
        recommended_next_action=(
            "Capture frozen notebook Fraction_Silver_Lead output and run the Phase 4H4 verifier "
            "before any implementation slice."
        ),
        notes=(
            "Existing app outputs are not automatic equivalents. The Metal_Hardness "
            "reference is a grid anchor, not a replacement output."
        ),
    ),
)


def get_ai_ready_fraction_recovery_checklist() -> tuple[
    AIReadyFractionRecoveryItem, ...
]:
    """Return the Phase 4H4 recovery checklist for the Fraction_* outputs."""

    return _CHECKLIST


def write_ai_ready_fraction_recovery_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[AIReadyFractionRecoveryItem] | None = None,
    report_relative_path: str | Path = AI_READY_FRACTION_RECOVERY_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON recovery report without creating TIFF or NPY outputs."""

    report_items = tuple(items or _CHECKLIST)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": AI_READY_FRACTION_RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_source_status": _counts_by("source_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status", report_items
        ),
        "phase_4h4_formula_changes": False,
        "notes": (
            "Phase 4H4 is recovery and verification-contract work only. It does not "
            "implement Fraction_* rasters, change semantic formulas, or introduce public serving."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[AIReadyFractionRecoveryItem],
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
