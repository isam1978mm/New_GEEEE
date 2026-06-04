from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


PAN_STACK_RECOVERY_SCHEMA_VERSION = "pan_stack_recovery_v1"
PAN_STACK_RECOVERY_REPORT_RELATIVE_PATH = "manifests/pan_stack_recovery_report.json"
PAN_STACK_OUTPUT_NAME = "PAN_LAYERS_STACK_640.npy"

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
class PanStackRecoveryItem:
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
            raise ValueError("Phase 4G recovery items must not target public_shared")
        if self.runtime_output_verified:
            raise ValueError("Phase 4G recovery does not verify runtime output presence")
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 4G recovery does not verify notebook value parity")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_CHECKLIST: tuple[PanStackRecoveryItem, ...] = (
    PanStackRecoveryItem(
        id="pan_layers_stack_640_npy",
        notebook_output=PAN_STACK_OUTPUT_NAME,
        family="panchromatic/optical outputs",
        current_app_status=(
            "missing; current app writes S2 indices, S2 raw cube, optical support mask, "
            "and science-core feature stacks, but it does not write PAN_LS_Panchromatic_640.*, "
            "PAN_S2_Panchromatic_10m_640.*, or PAN_LAYERS_STACK_640.npy"
        ),
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=(
            "notebooks/new.ipynb lines 25645-25890 provide the authoritative optical-only "
            "PAN export cell: LANDSAT/LC09/C02/T1_TOA B8 is resampled bilinearly and renamed "
            "LS_Panchromatic; COPERNICUS/S2_SR_HARMONIZED B2/B3/B4/B8 are reduced with "
            "ee.Reducer.mean() and renamed S2_Panchromatic_10m; pan_stack = ee.Image.cat(["
            "landsat_pan_layer, sentinel_high_res]); cube = np.full((OUT_SIZE, OUT_SIZE, "
            "len(bands)), NODATA, dtype=np.float32); tiles are sampled with "
            "sampleRectangle(defaultValue=NODATA); per-band files PAN_<band>_640.* are written; "
            "then np.save(stack_path, cube.astype(np.float32)) writes PAN_LAYERS_STACK_640.npy."
        ),
        expected_input_outputs=(
            "PAN_LS_Panchromatic_640.npy",
            "PAN_S2_Panchromatic_10m_640.npy",
        ),
        expected_band_order=(
            "LS_Panchromatic",
            "S2_Panchromatic_10m",
        ),
        expected_shape_convention="HWC",
        expected_dtype="float32",
        expected_units=(
            "Notebook source indicates a two-band optical stack composed of Landsat 9 TOA "
            "B8 resampled bilinearly at the locked grid and a Sentinel-2 panchromatic "
            "equivalent computed as mean(B2, B3, B4, B8) at 10 m. Frozen reference output "
            "is still required to lock final unit wording."
        ),
        expected_nodata_policy=(
            "Cube is initialized with NODATA, sampleRectangle uses defaultValue=NODATA, "
            "and the optical-only cell applies finite_or_nodata() before tile assignment."
        ),
        required_reference_outputs=(
            "NPY_STACKS/PAN_LAYERS_STACK_640.npy",
            "OPT/PAN_NPY_640/PAN_LS_Panchromatic_640.npy",
            "OPT/PAN_NPY_640/PAN_S2_Panchromatic_10m_640.npy",
            "OPT/PAN_TIFS_640/PAN_LS_Panchromatic_640.tif",
            "OPT/PAN_TIFS_640/PAN_S2_Panchromatic_10m_640.tif",
        ),
        required_metadata=(
            "band order",
            "shape",
            "dtype",
            "NODATA or NaN policy",
            "unit convention",
            "date window",
            "cloud filters",
            "selected Landsat image id",
            "selected Sentinel-2 image id",
        ),
        target_mode="notebook_parity",
        classification="notebook-parity",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "The notebook source for PAN_LAYERS_STACK_640.npy is explicit, but the app has "
            "no current writer and frozen notebook references are still required to lock "
            "metadata, exact value tolerance, and final unit wording."
        ),
        recommended_next_action=(
            "Capture the frozen PAN stack and the four related per-band notebook outputs, "
            "then run the Phase 4G verifier before any later implementation slice."
        ),
        notes=(
            "The notebook stack is evidence-backed as HWC in the ee.Image.cat order "
            "LS_Panchromatic then S2_Panchromatic_10m. Existing optical outputs such as "
            "s2_raw_cube.npy or feature_stacks science_core_stack.npy are not equivalents."
        ),
    ),
)


def get_pan_stack_recovery_checklist() -> tuple[PanStackRecoveryItem, ...]:
    """Return the Phase 4G recovery checklist for PAN_LAYERS_STACK_640.npy."""

    return _CHECKLIST


def write_pan_stack_recovery_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[PanStackRecoveryItem] | None = None,
    report_relative_path: str | Path = PAN_STACK_RECOVERY_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON recovery report without creating NPY outputs."""

    report_items = tuple(items or _CHECKLIST)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": PAN_STACK_RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_source_status": _counts_by("source_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "phase_4g_optical_math_changes": False,
        "notes": (
            "Phase 4G locks source recovery and verification contract details for "
            "PAN_LAYERS_STACK_640.npy only. It does not generate the stack, write NPY "
            "outputs, call Earth Engine, or integrate with the live pipeline."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(field_name: str, items: Iterable[PanStackRecoveryItem]) -> dict[str, int]:
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
