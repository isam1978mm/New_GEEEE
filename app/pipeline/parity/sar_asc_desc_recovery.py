from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


SAR_ASC_DESC_RECOVERY_SCHEMA_VERSION = "sar_asc_desc_recovery_v1"
SAR_ASC_DESC_RECOVERY_REPORT_RELATIVE_PATH = (
    "manifests/sar_asc_desc_recovery_report.json"
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
    "blocked_dependency_missing",
    "deferred",
}

REQUIRED_INPUTS = (
    "Sentinel-1 collection",
    "orbit pass",
    "VV/VH bands",
    "filtering/masking",
    "median/composite logic",
    "RTC or pre-RTC status",
    "scaling/unit convention",
    "GRID alignment",
    "nodata policy",
)

REQUIRED_METADATA = (
    "CRS",
    "transform",
    "pixel size",
    "width",
    "height",
    "dtype",
    "nodata",
    "band count",
    "unit convention",
    "filtering status",
    "RTC or pre-RTC status",
)

_OUTPUT_SPECS = (
    ("s1_asc_vv_filtered_640_tif", "S1_ASC_VV_Filtered_640.tif", "GEOTIFF_RADAR_BANDS/S1_ASC_VV_Filtered_640.tif", "ASCENDING", "VV", "GeoTIFF"),
    ("s1_asc_vh_filtered_640_tif", "S1_ASC_VH_Filtered_640.tif", "GEOTIFF_RADAR_BANDS/S1_ASC_VH_Filtered_640.tif", "ASCENDING", "VH", "GeoTIFF"),
    ("s1_desc_vv_filtered_640_tif", "S1_DESC_VV_Filtered_640.tif", "GEOTIFF_RADAR_BANDS/S1_DESC_VV_Filtered_640.tif", "DESCENDING", "VV", "GeoTIFF"),
    ("s1_desc_vh_filtered_640_tif", "S1_DESC_VH_Filtered_640.tif", "GEOTIFF_RADAR_BANDS/S1_DESC_VH_Filtered_640.tif", "DESCENDING", "VH", "GeoTIFF"),
    ("s1_asc_vv_filtered_640_npy", "S1_ASC_VV_Filtered_640.npy", "NPY_RADAR_BANDS/S1_ASC_VV_Filtered_640.npy", "ASCENDING", "VV", "NPY"),
    ("s1_asc_vh_filtered_640_npy", "S1_ASC_VH_Filtered_640.npy", "NPY_RADAR_BANDS/S1_ASC_VH_Filtered_640.npy", "ASCENDING", "VH", "NPY"),
    ("s1_desc_vv_filtered_640_npy", "S1_DESC_VV_Filtered_640.npy", "NPY_RADAR_BANDS/S1_DESC_VV_Filtered_640.npy", "DESCENDING", "VV", "NPY"),
    ("s1_desc_vh_filtered_640_npy", "S1_DESC_VH_Filtered_640.npy", "NPY_RADAR_BANDS/S1_DESC_VH_Filtered_640.npy", "DESCENDING", "VH", "NPY"),
)


@dataclass(frozen=True)
class SarAscDescRecoveryItem:
    id: str
    notebook_output: str
    family: str
    current_app_status: str
    source_status: str
    authoritative_source_available: bool
    source_reference: str
    known_stage_file: str | None
    known_stage_class: str | None
    required_inputs: tuple[str, ...]
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
            raise ValueError("SAR ASC/DESC recovery items must not target public_shared")
        if self.runtime_output_verified:
            raise ValueError("Phase 4E does not verify runtime output presence")
        if self.notebook_value_parity_verified:
            raise ValueError("notebook value parity requires frozen reference comparison")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _build_item(
    item_id: str,
    notebook_output: str,
    reference_output: str,
    orbit_pass: str,
    polarization: str,
    container: str,
) -> SarAscDescRecoveryItem:
    return SarAscDescRecoveryItem(
        id=item_id,
        notebook_output=notebook_output,
        family="SAR/radar outputs",
        current_app_status=(
            "missing; app final RTC outputs are not equivalent to separate "
            f"{orbit_pass} {polarization} {container} filtered support stacks"
        ),
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=(
            "notebooks/new.ipynb lines around 26199-26308: filters COPERNICUS/S1_GRD "
            "by orbitProperties_pass ASCENDING/DESCENDING, selects the newest image "
            "per pass, applies focal_mean speckle_filter, grid-aligns bands, samples "
            "to a 640 grid, and writes per-band GeoTIFF/NPY outputs."
        ),
        known_stage_file="app/pipeline/stages/sar_rtc.py",
        known_stage_class="SarRtcStage",
        required_inputs=REQUIRED_INPUTS,
        required_reference_outputs=(reference_output,),
        required_metadata=REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "Notebook source is available, but frozen reference output, metadata, "
            "and numeric tolerance expectations are still required before implementation."
        ),
        recommended_next_action=(
            "Capture the frozen notebook output and metadata for this exact ASC/DESC "
            "support layer, then add a verifier or implementation slice without "
            "changing existing SAR RTC math."
        ),
        notes=(
            "Do not alias final SAR RTC products such as VV_dB.tif, VH_dB.tif, "
            "RADAR_*_640_app.*, or post_rtc arrays as ASC/DESC support stacks. "
            "The notebook support block is a distinct orbit-pass filtered export."
        ),
    )


_CHECKLIST: tuple[SarAscDescRecoveryItem, ...] = tuple(
    _build_item(*spec) for spec in _OUTPUT_SPECS
)


def get_sar_asc_desc_recovery_checklist() -> tuple[SarAscDescRecoveryItem, ...]:
    """Return the Phase 4E ASC/DESC Sentinel-1 support-stack recovery checklist."""

    return _CHECKLIST


def write_sar_asc_desc_recovery_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[SarAscDescRecoveryItem] | None = None,
    report_relative_path: str | Path = SAR_ASC_DESC_RECOVERY_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON recovery report without creating SAR rasters or arrays."""

    report_items = tuple(items or _CHECKLIST)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SAR_ASC_DESC_RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_source_status": _counts_by("source_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "phase_4e_sar_math_changes": False,
        "notes": (
            "Phase 4E locks source-recovery status for notebook ASC/DESC Sentinel-1 "
            "support stacks. It does not implement SAR generation, write rasters, "
            "write NPY arrays, call Earth Engine, or add aliases."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[SarAscDescRecoveryItem],
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
