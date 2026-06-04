from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


DEM_CURVATURE_RECONSTRUCTION_SCHEMA_VERSION = "dem_curvature_reconstruction_v1"
DEM_CURVATURE_RECONSTRUCTION_REPORT_RELATIVE_PATH = (
    "manifests/dem_curvature_reconstruction_report.json"
)

ALLOWED_FORMULA_STATUSES = {
    "exact_formula_found",
    "approximate_formula_found",
    "no_formula_found",
    "existing_app_equivalent_found",
    "unknown_needs_reference",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "ready_for_implementation",
    "requires_reference_output",
    "requires_formula_reconstruction",
    "blocked_no_source_formula",
    "blocked_dependency_missing",
}


@dataclass(frozen=True)
class DemCurvatureReconstructionItem:
    id: str
    notebook_output: str
    family: str
    current_app_status: str
    formula_status: str
    formula_source: str
    known_stage_file: str | None
    known_stage_class: str | None
    required_inputs: tuple[str, ...]
    target_mode: str
    classification: str
    requires_coordinates: bool
    probability_only_required: bool
    runtime_output_verified: bool
    notebook_value_parity_verified: bool
    implementation_status: str
    blocker: str
    recommended_next_action: str
    notes: str

    def __post_init__(self) -> None:
        if self.formula_status not in ALLOWED_FORMULA_STATUSES:
            raise ValueError(f"unsupported formula_status: {self.formula_status}")
        if self.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"unsupported implementation_status: {self.implementation_status}"
            )
        if self.target_mode == "public_shared":
            raise ValueError("DEM curvature reconstruction items must not target public_shared")
        if self.notebook_value_parity_verified and not self.runtime_output_verified:
            raise ValueError("notebook value parity cannot be verified without runtime output proof")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_REGISTRY: tuple[DemCurvatureReconstructionItem, ...] = (
    DemCurvatureReconstructionItem(
        id="curv_laplacian_640",
        notebook_output="curv_laplacian_640.tif",
        family="DEM/terrain outputs",
        current_app_status="partial; app writes one root curvature.tif only",
        formula_status="existing_app_equivalent_found",
        formula_source=(
            "app/pipeline/stages/dem_derivatives.py computes curvature as "
            "d2z_dxx + d2z_dyy; no exact notebook curv_laplacian formula text "
            "was found in docs/Notebook_Cells_E.md."
        ),
        known_stage_file="app/pipeline/stages/dem_derivatives.py",
        known_stage_class="DemDerivativesStage",
        required_inputs=(
            "DEM",
            "cell size / transform",
            "second derivatives",
            "nodata mask",
        ),
        target_mode="notebook_parity",
        classification="notebook-parity",
        requires_coordinates=False,
        probability_only_required=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "The app formula is a Laplacian-style curvature equivalent, but the "
            "exact notebook formula and frozen reference output are still needed "
            "before promoting it to notebook-value parity."
        ),
        recommended_next_action=(
            "Capture frozen curv_laplacian_640.tif from the notebook and compare it "
            "against app curvature.tif metadata and values before implementing a "
            "notebook-compatible alias or dedicated writer."
        ),
        notes=(
            "Do not assume app curvature.tif is identical to curv_laplacian_640.tif "
            "until reference comparison passes."
        ),
    ),
    DemCurvatureReconstructionItem(
        id="curv_plan_640",
        notebook_output="curv_plan_640.tif",
        family="DEM/terrain outputs",
        current_app_status="missing; no separate app writer identified",
        formula_status="no_formula_found",
        formula_source=(
            "No plan-curvature formula was found in current app source, "
            "docs/Notebook_Cells_E.md, or inspected parity docs."
        ),
        known_stage_file=None,
        known_stage_class=None,
        required_inputs=(
            "DEM",
            "cell size / transform",
            "slope",
            "aspect",
            "first derivatives",
            "second derivatives",
            "nodata mask",
        ),
        target_mode="notebook_parity",
        classification="notebook-parity",
        requires_coordinates=False,
        probability_only_required=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="blocked_no_source_formula",
        blocker="The exact notebook plan-curvature equation and reference output are missing.",
        recommended_next_action=(
            "Recover the original notebook cell source or a frozen reference bundle "
            "before designing a Phase 4D2 implementation."
        ),
        notes="The root app curvature.tif is not a plan-curvature equivalent.",
    ),
    DemCurvatureReconstructionItem(
        id="curv_profile_640",
        notebook_output="curv_profile_640.tif",
        family="DEM/terrain outputs",
        current_app_status="missing; no separate app writer identified",
        formula_status="no_formula_found",
        formula_source=(
            "No profile-curvature formula was found in current app source, "
            "docs/Notebook_Cells_E.md, or inspected parity docs."
        ),
        known_stage_file=None,
        known_stage_class=None,
        required_inputs=(
            "DEM",
            "cell size / transform",
            "slope",
            "aspect",
            "first derivatives",
            "second derivatives",
            "nodata mask",
        ),
        target_mode="notebook_parity",
        classification="notebook-parity",
        requires_coordinates=False,
        probability_only_required=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="blocked_no_source_formula",
        blocker=(
            "The exact notebook profile-curvature equation and reference output are missing."
        ),
        recommended_next_action=(
            "Recover the original notebook cell source or a frozen reference bundle "
            "before designing a Phase 4D2 implementation."
        ),
        notes="The root app curvature.tif is not a profile-curvature equivalent.",
    ),
)


def get_dem_curvature_reconstruction_registry() -> tuple[DemCurvatureReconstructionItem, ...]:
    """Return the Phase 4D DEM curvature reconstruction registry."""

    return _REGISTRY


def write_dem_curvature_reconstruction_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[DemCurvatureReconstructionItem] | None = None,
    report_relative_path: str | Path = DEM_CURVATURE_RECONSTRUCTION_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON reconstruction report without creating raster files."""

    report_items = tuple(items or _REGISTRY)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": DEM_CURVATURE_RECONSTRUCTION_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_formula_status": _counts_by("formula_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "phase_4d_formula_changes": False,
        "notes": (
            "Phase 4D records reconstruction status only. It does not implement DEM "
            "curvature formulas or write raster outputs."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[DemCurvatureReconstructionItem],
) -> dict[str, int]:
    if field_name == "formula_status":
        counts = {status: 0 for status in sorted(ALLOWED_FORMULA_STATUSES)}
    elif field_name == "implementation_status":
        counts = {status: 0 for status in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    else:
        raise ValueError(f"unsupported count field: {field_name}")

    for item in items:
        value = getattr(item, field_name)
        counts[value] += 1
    return counts
