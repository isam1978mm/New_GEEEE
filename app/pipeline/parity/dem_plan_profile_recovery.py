from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


DEM_PLAN_PROFILE_RECOVERY_SCHEMA_VERSION = "dem_plan_profile_recovery_v1"
DEM_PLAN_PROFILE_RECOVERY_REPORT_RELATIVE_PATH = (
    "manifests/dem_plan_profile_recovery_report.json"
)

ALLOWED_FORMULA_STATUSES = {
    "no_formula_found",
    "candidate_non_authoritative_formula_only",
    "authoritative_formula_found",
    "unknown_needs_reference",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "blocked_no_source_formula",
    "blocked_missing_reference_output",
    "blocked_missing_metadata_contract",
    "ready_for_formula_implementation_after_evidence",
    "deferred",
}

REQUIRED_METADATA = (
    "CRS",
    "transform",
    "pixel size",
    "units",
    "nodata",
    "dtype",
    "sign convention",
    "scaling/normalization",
)

REQUIRED_EVIDENCE = (
    "notebook source cell lines for first and second derivatives",
    "notebook source cell lines for plan/profile formulas",
    "notebook source cell lines for save_tif filename behavior",
    "frozen notebook reference GeoTIFF",
    "reference metadata contract",
    "numeric tolerance contract",
)


@dataclass(frozen=True)
class DemPlanProfileRecoveryItem:
    id: str
    notebook_output: str
    family: str
    current_app_status: str
    formula_status: str
    authoritative_formula_available: bool
    candidate_formula_documented: bool
    candidate_formula_authoritative: bool
    required_evidence: tuple[str, ...]
    required_reference_outputs: tuple[str, ...]
    required_metadata: tuple[str, ...]
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
            raise ValueError("plan/profile recovery items must not target public_shared")
        if self.notebook_value_parity_verified:
            raise ValueError("notebook value parity requires a passing reference comparison")
        if self.runtime_output_verified:
            raise ValueError("Phase 4D3 does not verify runtime output presence")
        if (
            self.candidate_formula_authoritative
            and not self.authoritative_formula_available
        ):
            raise ValueError(
                "candidate formula cannot be authoritative without an authoritative formula"
            )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_CHECKLIST: tuple[DemPlanProfileRecoveryItem, ...] = (
    DemPlanProfileRecoveryItem(
        id="curv_plan_640",
        notebook_output="curv_plan_640.tif",
        family="DEM/terrain outputs",
        current_app_status="missing; no app writer or alias exists",
        formula_status="authoritative_formula_found",
        authoritative_formula_available=True,
        candidate_formula_documented=False,
        candidate_formula_authoritative=False,
        required_evidence=REQUIRED_EVIDENCE,
        required_reference_outputs=("DEM_GEO8_TIFS/curv_plan_640.tif",),
        required_metadata=REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity",
        requires_coordinates=False,
        probability_only_required=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="blocked_missing_reference_output",
        blocker=(
            "Authoritative notebook formula text was found, but frozen reference "
            "curv_plan_640.tif output and its metadata contract are still missing."
        ),
        recommended_next_action=(
            "Capture the frozen notebook curv_plan_640.tif reference, lock metadata "
            "and tolerance expectations, then implement in a later formula slice."
        ),
        notes=(
            "notebooks/new.ipynb contains the source formula around the DEM_GEO8_TIFS "
            "curvature cell: p=dz_dx, q=dz_dy, r=d2z_dxx, s=d2z_dxy, t=d2z_dyy; "
            "curv_plan is saved through save_tif(\"curv_plan\", curv_plan)."
        ),
    ),
    DemPlanProfileRecoveryItem(
        id="curv_profile_640",
        notebook_output="curv_profile_640.tif",
        family="DEM/terrain outputs",
        current_app_status="missing; no app writer or alias exists",
        formula_status="authoritative_formula_found",
        authoritative_formula_available=True,
        candidate_formula_documented=False,
        candidate_formula_authoritative=False,
        required_evidence=REQUIRED_EVIDENCE,
        required_reference_outputs=("DEM_GEO8_TIFS/curv_profile_640.tif",),
        required_metadata=REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity",
        requires_coordinates=False,
        probability_only_required=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="blocked_missing_reference_output",
        blocker=(
            "Authoritative notebook formula text was found, but frozen reference "
            "curv_profile_640.tif output and its metadata contract are still missing."
        ),
        recommended_next_action=(
            "Capture the frozen notebook curv_profile_640.tif reference, lock metadata "
            "and tolerance expectations, then implement in a later formula slice."
        ),
        notes=(
            "notebooks/new.ipynb contains the source formula around the DEM_GEO8_TIFS "
            "curvature cell: p=dz_dx, q=dz_dy, r=d2z_dxx, s=d2z_dxy, t=d2z_dyy; "
            "curv_profile is saved through save_tif(\"curv_profile\", curv_profile)."
        ),
    ),
)


def get_dem_plan_profile_recovery_checklist() -> tuple[DemPlanProfileRecoveryItem, ...]:
    """Return the Phase 4D3 plan/profile curvature recovery checklist."""

    return _CHECKLIST


def write_dem_plan_profile_recovery_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[DemPlanProfileRecoveryItem] | None = None,
    report_relative_path: str | Path = DEM_PLAN_PROFILE_RECOVERY_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON recovery report without creating raster files."""

    report_items = tuple(items or _CHECKLIST)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": DEM_PLAN_PROFILE_RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_formula_status": _counts_by("formula_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "phase_4d3_formula_changes": False,
        "notes": (
            "Phase 4D3 locks plan/profile curvature formula recovery status only. "
            "It does not implement formulas, write rasters, or add aliases."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[DemPlanProfileRecoveryItem],
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
