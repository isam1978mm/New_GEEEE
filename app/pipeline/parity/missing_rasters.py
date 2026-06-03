from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


MISSING_RASTER_REPORT_SCHEMA_VERSION = "missing_raster_families_report_v1"

ALLOWED_IMPLEMENTATION_STATUSES = {
    "missing",
    "partial",
    "source_writer_exists_unverified",
    "no_source_equivalent_identified",
    "requires_reference_notebook_output",
    "requires_formula_reconstruction",
    "requires_external_dependency",
    "deferred_to_later_phase",
}


@dataclass(frozen=True)
class MissingRasterFamilyItem:
    id: str
    family: str
    notebook_paths_or_patterns: tuple[str, ...]
    current_app_status: str
    known_stage_file: str | tuple[str, ...] | None
    known_stage_class: str | tuple[str, ...] | None
    target_mode: str
    target_phase: str
    parity_priority: str
    classification: str
    requires_coordinates: bool
    requires_external_dependency: bool
    source_formula_status: str
    runtime_output_verified: bool
    notebook_value_parity_verified: bool
    implementation_status: str
    blocker: str
    recommended_next_action: str
    notes: str

    def __post_init__(self) -> None:
        if self.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(f"unsupported implementation_status: {self.implementation_status}")
        if self.target_mode == "public_shared":
            raise ValueError("Phase 4A registry items must not target public_shared")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_REGISTRY: tuple[MissingRasterFamilyItem, ...] = (
    MissingRasterFamilyItem(
        id="dem_curvature_variants",
        family="DEM/terrain outputs",
        notebook_paths_or_patterns=(
            "curv_laplacian_640.tif",
            "curv_plan_640.tif",
            "curv_profile_640.tif",
        ),
        current_app_status="partial",
        known_stage_file="app/pipeline/stages/dem_derivatives.py",
        known_stage_class="DemDerivativesStage",
        target_mode="notebook_parity",
        target_phase="phase_4_missing_raster_families",
        parity_priority="medium_high",
        classification="notebook-parity",
        requires_coordinates=False,
        requires_external_dependency=False,
        source_formula_status="missing distinct notebook curvature variant formulas in app source",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_formula_reconstruction",
        blocker=(
            "App source writes one curvature raster, but distinct notebook laplacian, "
            "plan, and profile curvature formulas are not implemented as separate outputs."
        ),
        recommended_next_action=(
            "Recover exact notebook formulas and reference outputs before adding each "
            "curvature variant in a later Phase 4B task."
        ),
        notes="File existence of dem_derivatives.py is not parity proof for these three outputs.",
    ),
    MissingRasterFamilyItem(
        id="sar_asc_desc_filtered_support_stacks",
        family="SAR/radar outputs",
        notebook_paths_or_patterns=(
            "S1_ASC_VV_Filtered_640.tif",
            "S1_ASC_VH_Filtered_640.tif",
            "S1_DESC_VV_Filtered_640.tif",
            "S1_DESC_VH_Filtered_640.tif",
            "S1_ASC_VV_Filtered_640.npy",
            "S1_ASC_VH_Filtered_640.npy",
            "S1_DESC_VV_Filtered_640.npy",
            "S1_DESC_VH_Filtered_640.npy",
        ),
        current_app_status="missing",
        known_stage_file="app/pipeline/stages/sar_rtc.py",
        known_stage_class="SarRtcStage",
        target_mode="notebook_parity",
        target_phase="phase_4_missing_raster_families",
        parity_priority="high",
        classification="notebook-parity",
        requires_coordinates=False,
        requires_external_dependency=True,
        source_formula_status="no source-equivalent ASC/DESC filtered stack writer identified",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_source_equivalent_identified",
        blocker=(
            "Current SAR path writes final RTC products and aliases, not separate "
            "ASC/DESC filtered support stacks."
        ),
        recommended_next_action=(
            "Use frozen notebook source and reference outputs to design one ASC/DESC "
            "support-stack task without changing existing SAR math."
        ),
        notes="Do not fabricate ASC/DESC support outputs from final median products.",
    ),
    MissingRasterFamilyItem(
        id="panchromatic_optical_support_outputs",
        family="panchromatic/optical outputs",
        notebook_paths_or_patterns=(
            "PAN_LS_Panchromatic_640.tif",
            "PAN_S2_Panchromatic_10m_640.tif",
            "PAN_LS_Panchromatic_640.npy",
            "PAN_S2_Panchromatic_10m_640.npy",
            "PAN_LAYERS_STACK_640.npy",
        ),
        current_app_status="missing",
        known_stage_file="app/pipeline/stages/feature_stacks.py",
        known_stage_class="FeatureStacksStage",
        target_mode="notebook_parity",
        target_phase="phase_4_missing_raster_families",
        parity_priority="medium",
        classification="notebook-parity",
        requires_coordinates=False,
        requires_external_dependency=True,
        source_formula_status="no panchromatic output writer identified in app source",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_source_equivalent_identified",
        blocker=(
            "Feature stack source has an optical support mask, but no LS/S2 "
            "panchromatic raster or PAN stack writer."
        ),
        recommended_next_action=(
            "Recover notebook panchromatic formulas and source selection rules before "
            "implementing the optical support family."
        ),
        notes="Phase 4A records the gap only; no optical raster is generated.",
    ),
    MissingRasterFamilyItem(
        id="resampled_filtered_hypercube_variants",
        family="hypercube/tensor outputs",
        notebook_paths_or_patterns=(
            "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif",
            "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy",
            "S1_FILTERED_LAYERS_STACK_640.npy",
        ),
        current_app_status="missing",
        known_stage_file=(
            "app/pipeline/stages/hypercube.py",
            "app/pipeline/stages/feature_stacks.py",
        ),
        known_stage_class=("HypercubeStage", "FeatureStacksStage"),
        target_mode="notebook_parity",
        target_phase="phase_4_missing_raster_families",
        parity_priority="high",
        classification="notebook-parity",
        requires_coordinates=False,
        requires_external_dependency=False,
        source_formula_status="resampling and filtered stack source-equivalent rules not implemented",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_notebook_output",
        blocker=(
            "Current hypercube and feature-stack writers do not produce the 2.5 m "
            "resampled hypercube or S1 filtered layer stack."
        ),
        recommended_next_action=(
            "Capture notebook reference shapes, band order, dtype, and resampling "
            "rules before implementing these tensor variants."
        ),
        notes="Phase 3 aliases existing hypercube files only; these variants remain separate.",
    ),
    MissingRasterFamilyItem(
        id="broader_ai_beh_ai_ready_series",
        family="AI_BEH / AI_READY outputs",
        notebook_paths_or_patterns=(
            "AI_BEH_*",
            "AI_READY_*",
            "any notebook-only AI behavior raster family not already covered by the six AI_READY_640_Secret_* outputs",
        ),
        current_app_status="partial",
        known_stage_file=(
            "app/pipeline/stages/secret_layers.py",
            "app/pipeline/stages/feature_stacks.py",
        ),
        known_stage_class=("SecretLayersStage", "FeatureStacksStage"),
        target_mode="notebook_parity",
        target_phase="phase_4_missing_raster_families",
        parity_priority="high",
        classification="notebook-parity semantic raster stage",
        requires_coordinates=False,
        requires_external_dependency=True,
        source_formula_status="partial; six secret outputs have writer code, broader behavior series does not",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="partial",
        blocker=(
            "Only six AI_READY_640_Secret_* outputs and neutral support stack code are "
            "source-identified; broader AI_BEH/AI_READY formulas are incomplete."
        ),
        recommended_next_action=(
            "Split each broader behavior raster family into a separate Phase 4B task "
            "after source formulas and reference outputs are identified."
        ),
        notes="Do not promote AI behavior rasters to clean defensible core by default.",
    ),
    MissingRasterFamilyItem(
        id="report_640_runtime_value_parity",
        family="REPORT_640 outputs",
        notebook_paths_or_patterns=(
            "REPORT_640_Pottery_Report.tif",
            "REPORT_640_Mass_Report.tif",
            "REPORT_640_FINAL_Zero_Point_Targets.tif",
        ),
        current_app_status="unknown_needs_verification",
        known_stage_file="app/pipeline/stages/report_640.py",
        known_stage_class="Report640Stage",
        target_mode="notebook_parity",
        target_phase="phase_4_missing_raster_families",
        parity_priority="high",
        classification="notebook-parity report/semantic raster stage",
        requires_coordinates=False,
        requires_external_dependency=True,
        source_formula_status="source writer exists but runtime and notebook-value parity are unverified",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="source_writer_exists_unverified",
        blocker=(
            "Source writer is identified, but a real run/reference comparison has not "
            "proven output presence or value parity."
        ),
        recommended_next_action=(
            "Run a controlled reference comparison for report_640 outputs before "
            "marking them implemented."
        ),
        notes="report_640.py is not clean defensible core by default.",
    ),
    MissingRasterFamilyItem(
        id="secret_layer_runtime_value_parity",
        family="AI_BEH / AI_READY outputs",
        notebook_paths_or_patterns=(
            "AI_READY_640_Secret_Gold_Halo.tif",
            "AI_READY_640_Secret_Silver_Oxide.tif",
            "AI_READY_640_Secret_Tunnel_Ceiling.tif",
            "AI_READY_640_Secret_Thermal_Inertia.tif",
            "AI_READY_640_Secret_Chemical_Protector.tif",
            "AI_READY_640_Secret_Hidden_Doors.tif",
        ),
        current_app_status="unknown_needs_verification",
        known_stage_file="app/pipeline/stages/secret_layers.py",
        known_stage_class="SecretLayersStage",
        target_mode="notebook_parity",
        target_phase="phase_4_missing_raster_families",
        parity_priority="high",
        classification="notebook-parity semantic raster stage",
        requires_coordinates=False,
        requires_external_dependency=True,
        source_formula_status="source writer exists for six secret outputs but runtime and notebook-value parity are unverified",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="source_writer_exists_unverified",
        blocker=(
            "Source writer is identified, but no real run/reference comparison has "
            "proven output presence or value parity."
        ),
        recommended_next_action=(
            "Run a controlled reference comparison for the six secret layer outputs "
            "before marking them implemented."
        ),
        notes="secret_layers.py is not clean defensible core by default.",
    ),
)


def get_missing_raster_registry() -> tuple[MissingRasterFamilyItem, ...]:
    """Return the full Phase 4A missing-raster family registry."""

    return _REGISTRY


def filter_missing_raster_registry_by_status(
    implementation_status: str,
) -> tuple[MissingRasterFamilyItem, ...]:
    """Return registry items matching an allowed implementation status."""

    if implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
        raise ValueError(f"unsupported implementation_status: {implementation_status}")
    return tuple(
        item for item in _REGISTRY if item.implementation_status == implementation_status
    )


def write_missing_raster_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[MissingRasterFamilyItem] | None = None,
) -> Path:
    """Write a run-local JSON report; does not create or copy raster files."""

    report_items = tuple(items or _REGISTRY)
    report_path = resolve_run_output_path(
        run_dir,
        "manifests/missing_raster_families_report.json",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": MISSING_RASTER_REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_status": _counts_by_status(report_items),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by_status(
    items: Iterable[MissingRasterFamilyItem],
) -> dict[str, int]:
    counts = {status: 0 for status in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    for item in items:
        counts[item.implementation_status] += 1
    return counts
