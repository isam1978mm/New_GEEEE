from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


S1_FILTERED_STACK_RECOVERY_SCHEMA_VERSION = "s1_filtered_stack_recovery_v1"
S1_FILTERED_STACK_RECOVERY_REPORT_RELATIVE_PATH = (
    "manifests/s1_filtered_stack_recovery_report.json"
)
S1_FILTERED_STACK_OUTPUT_NAME = "S1_FILTERED_LAYERS_STACK_640.npy"

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
class S1FilteredStackRecoveryItem:
    id: str
    notebook_output: str
    family: str
    current_app_status: str
    source_status: str
    authoritative_source_available: bool
    source_reference: str
    expected_input_outputs: tuple[str, ...]
    expected_band_order: tuple[str, ...]
    expected_shape_convention: str
    expected_dtype: str
    expected_units: str
    expected_nodata_policy: str
    required_reference_outputs: tuple[str, ...]
    required_metadata: tuple[str, ...]
    target_mode: str
    classification: str
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
            raise ValueError("Phase 4F recovery items must not target public_shared")
        if self.runtime_output_verified:
            raise ValueError("Phase 4F recovery does not verify runtime output presence")
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 4F recovery does not verify notebook value parity")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_CHECKLIST: tuple[S1FilteredStackRecoveryItem, ...] = (
    S1FilteredStackRecoveryItem(
        id="s1_filtered_layers_stack_640_npy",
        notebook_output=S1_FILTERED_STACK_OUTPUT_NAME,
        family="SAR/radar outputs",
        current_app_status=(
            "missing; app final RTC products, radar_db_support_stack.npy, "
            "radar_linear_support_stack.npy, and RADAR_STACK_HWC_640_app.npy are "
            "not equivalent to the notebook filtered ASC/DESC support stack"
        ),
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=(
            "notebooks/new.ipynb lines 26182-26309: the notebook defines "
            "speckle_filter(image.focal_mean(...)), selects newest ASCENDING and "
            "DESCENDING Sentinel-1 VV/VH images, grid-aligns the four processed "
            "bands, allocates cube = np.full((OUT_SIZE, OUT_SIZE, "
            "len(band_names_list)), NODATA, dtype=np.float32), fills cube[:, :, bi] "
            "in band_names_list order, and writes "
            "NPY_STACKS/S1_FILTERED_LAYERS_STACK_640.npy via np.save(stack_path, "
            "cube.astype(np.float32))."
        ),
        expected_input_outputs=(
            "S1_ASC_VV_Filtered_640.npy",
            "S1_ASC_VH_Filtered_640.npy",
            "S1_DESC_VV_Filtered_640.npy",
            "S1_DESC_VH_Filtered_640.npy",
        ),
        expected_band_order=(
            "S1_ASC_VV_Filtered",
            "S1_ASC_VH_Filtered",
            "S1_DESC_VV_Filtered",
            "S1_DESC_VH_Filtered",
        ),
        expected_shape_convention="HWC",
        expected_dtype="float32",
        expected_units=(
            "Notebook source indicates filtered native Sentinel-1 VV/VH export after "
            "focal_mean and grid alignment; dB-versus-linear labeling is not restated "
            "inside the stack cell and must be confirmed from frozen reference outputs."
        ),
        expected_nodata_policy=(
            "Cube is initialized with NODATA and tile sampling uses "
            "sampleRectangle(defaultValue=NODATA); unresolved cells remain NODATA."
        ),
        required_reference_outputs=(
            "NPY_STACKS/S1_FILTERED_LAYERS_STACK_640.npy",
            "NPY_RADAR_BANDS/S1_ASC_VV_Filtered_640.npy",
            "NPY_RADAR_BANDS/S1_ASC_VH_Filtered_640.npy",
            "NPY_RADAR_BANDS/S1_DESC_VV_Filtered_640.npy",
            "NPY_RADAR_BANDS/S1_DESC_VH_Filtered_640.npy",
        ),
        required_metadata=(
            "band order",
            "shape",
            "dtype",
            "NODATA or NaN policy",
            "unit convention",
            "date window",
            "selected ASC/DESC acquisition timestamps",
            "selected ASC/DESC image ids",
        ),
        target_mode="notebook_parity",
        classification="notebook-parity",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "The notebook source for the stack is explicit, but there is no current "
            "app writer and frozen notebook reference output is still required to lock "
            "shape, units, value tolerance, and exact metadata expectations."
        ),
        recommended_next_action=(
            "Capture the frozen notebook stack and the four frozen per-band NPY "
            "references, then use the Phase 4F verifier before any later "
            "implementation slice."
        ),
        notes=(
            "The stack is evidence-backed as HWC in the per-band order "
            "ASC VV, ASC VH, DESC VV, DESC VH. It is distinct from final RTC outputs "
            "and from the app notebook alias NPY_STACKS/RADAR_STACK_HWC_640_app.npy."
        ),
    ),
)


def get_s1_filtered_stack_recovery_checklist() -> tuple[S1FilteredStackRecoveryItem, ...]:
    """Return the Phase 4F recovery checklist for the S1 filtered support stack."""

    return _CHECKLIST


def write_s1_filtered_stack_recovery_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[S1FilteredStackRecoveryItem] | None = None,
    report_relative_path: str | Path = S1_FILTERED_STACK_RECOVERY_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON recovery report without creating NPY outputs."""

    report_items = tuple(items or _CHECKLIST)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": S1_FILTERED_STACK_RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_source_status": _counts_by("source_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "phase_4f_sar_math_changes": False,
        "notes": (
            "Phase 4F locks source recovery and verification contract details for "
            "S1_FILTERED_LAYERS_STACK_640.npy only. It does not generate the stack, "
            "write NPY outputs, call Earth Engine, or integrate with the live pipeline."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[S1FilteredStackRecoveryItem],
) -> dict[str, int]:
    if field_name == "source_status":
        counts = {status: 0 for status in sorted(ALLOWED_SOURCE_STATUSES)}
    elif field_name == "implementation_status":
        counts = {status: 0 for status in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    else:
        raise ValueError(f"unsupported count field: {field_name}")

    for item in items:
        value = getattr(item, field_name)
        counts[value] += 1
    return counts
