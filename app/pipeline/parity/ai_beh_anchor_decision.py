from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


AI_BEH_ANCHOR_DECISION_SCHEMA_VERSION = "ai_beh_anchor_pattern_decision_v1"
AI_BEH_ANCHOR_DECISION_REPORT_RELATIVE_PATH = (
    "manifests/ai_beh_anchor_pattern_decision_report.json"
)

ALLOWED_SOURCE_STATUSES = {
    "exact_source_available",
    "partial_source_available",
    "no_source_available",
    "existing_app_equivalent_available",
    "unknown_needs_reference",
}

ALLOWED_DECISIONS = {
    "standalone_output_required",
    "internal_report_precursor_only",
    "unresolved_requires_source_reference",
    "covered_by_report_640_downstream_only",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "no_action_needed_internal_precursor",
    "requires_future_standalone_parity_slice",
    "requires_reference_output",
    "requires_source_reconstruction",
    "blocked_missing_metadata_contract",
    "deferred_by_user_decision",
}

_COMMON_REQUIRED_METADATA = (
    "dtype if persisted separately",
    "nodata or NaN policy if persisted separately",
    "CRS if persisted separately",
    "transform if persisted separately",
    "shape if persisted separately",
    "value tolerance for downstream parity",
)


@dataclass(frozen=True)
class AIBehAnchorDecisionItem:
    id: str
    notebook_pattern: str
    family: str
    source_status: str
    authoritative_source_available: bool
    source_reference: str
    standalone_export_evidence: str
    report_640_internal_evidence: str
    existing_contract_reference: str | None
    expected_formula_summary: str
    expected_input_outputs: tuple[str, ...]
    decision: str
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
        if self.decision not in ALLOWED_DECISIONS:
            raise ValueError(f"unsupported decision: {self.decision}")
        if self.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"unsupported implementation_status: {self.implementation_status}"
            )
        if self.target_mode == "public_shared":
            raise ValueError("Phase 4H11 items must not target public_shared")
        if self.http_servable:
            raise ValueError("Phase 4H11 items must not default http_servable true")
        if self.runtime_output_verified:
            raise ValueError("Phase 4H11 decision items must not verify runtime output")
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 4H11 decision items must not verify notebook parity")
        if not self.source_reference.strip():
            raise ValueError("source_reference must not be blank")
        if not self.standalone_export_evidence.strip():
            raise ValueError("standalone_export_evidence must not be blank")
        if not self.report_640_internal_evidence.strip():
            raise ValueError("report_640_internal_evidence must not be blank")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_ITEMS: tuple[AIBehAnchorDecisionItem, ...] = (
    AIBehAnchorDecisionItem(
        id="ai_beh_vegroot_anomaly_anchor",
        notebook_pattern="AI_BEH_VegRoot_Anomaly",
        family="AI_BEH semantic rasters",
        source_status="exact_source_available",
        authoritative_source_available=True,
        source_reference=(
            "notebooks/new.ipynb lines around 24457-24460 build beh_tensors and define "
            "AI_BEH_VegRoot_Anomaly as normalizedDifference(['B8', 'B4'])."
        ),
        standalone_export_evidence=(
            "No standalone notebook export filename was recovered for AI_BEH_VegRoot_Anomaly. "
            "The notebook uses the tensor inside beh_tensors and the zero-point threshold logic."
        ),
        report_640_internal_evidence=(
            "app/pipeline/stages/report_640.py lines around 105-108 reproduce the same "
            "NDVI-style tensor internally as the third REPORT_640 zero-point condition."
        ),
        existing_contract_reference="docs/REPORT_640_PARITY_VERIFICATION_CONTRACT.md",
        expected_formula_summary="normalizedDifference(B8, B4)",
        expected_input_outputs=("S2:B4", "S2:B8"),
        decision="internal_report_precursor_only",
        required_reference_outputs=(
            "REPORT_640_FINAL_Zero_Point_Targets.tif downstream reference",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic item",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_action_needed_internal_precursor",
        blocker=(
            "No standalone notebook export file was recovered for this tensor, so standalone "
            "parity cannot be asserted from current evidence."
        ),
        recommended_next_action=(
            "Keep this pattern documented as an internal REPORT_640 precursor unless a "
            "standalone notebook export file appears in a future reference bundle."
        ),
        notes=(
            "This tensor participates in the REPORT_640 threshold logic but is not currently "
            "treated as a separate exported notebook parity artifact."
        ),
    ),
    AIBehAnchorDecisionItem(
        id="ai_beh_ironoxide_hardness_anchor",
        notebook_pattern="AI_BEH_IronOxide_Hardness",
        family="AI_BEH semantic rasters",
        source_status="exact_source_available",
        authoritative_source_available=True,
        source_reference=(
            "notebooks/new.ipynb lines around 24462-24463 define "
            "AI_BEH_IronOxide_Hardness as B4 / B3 inside beh_tensors."
        ),
        standalone_export_evidence=(
            "No standalone notebook export filename was recovered for AI_BEH_IronOxide_Hardness. "
            "The notebook uses the tensor inside beh_tensors and the zero-point threshold logic."
        ),
        report_640_internal_evidence=(
            "app/pipeline/stages/report_640.py lines around 100-103 reproduce the same "
            "B4 / B3 tensor internally as the second REPORT_640 zero-point condition."
        ),
        existing_contract_reference="docs/REPORT_640_PARITY_VERIFICATION_CONTRACT.md",
        expected_formula_summary="B4 / B3",
        expected_input_outputs=("S2:B3", "S2:B4"),
        decision="internal_report_precursor_only",
        required_reference_outputs=(
            "REPORT_640_FINAL_Zero_Point_Targets.tif downstream reference",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic item",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_action_needed_internal_precursor",
        blocker=(
            "No standalone notebook export file was recovered for this tensor, so standalone "
            "parity cannot be asserted from current evidence."
        ),
        recommended_next_action=(
            "Keep this pattern documented as an internal REPORT_640 precursor unless a "
            "standalone notebook export file appears in a future reference bundle."
        ),
        notes=(
            "This tensor participates in the REPORT_640 threshold logic but is not currently "
            "treated as a separate exported notebook parity artifact."
        ),
    ),
    AIBehAnchorDecisionItem(
        id="ai_beh_goldalloy_signal_anchor",
        notebook_pattern="AI_BEH_GoldAlloy_Signal",
        family="AI_BEH semantic rasters",
        source_status="existing_app_equivalent_available",
        authoritative_source_available=True,
        source_reference=(
            "notebooks/new.ipynb lines around 24465-24466 define "
            "AI_BEH_GoldAlloy_Signal as B12 / B11 inside beh_tensors."
        ),
        standalone_export_evidence=(
            "No standalone notebook export filename was recovered for AI_BEH_GoldAlloy_Signal. "
            "Instead, the notebook renames beh_tensors.select('AI_BEH_GoldAlloy_Signal') "
            "to REPORT_640_Pottery_Report inside the exported output stack."
        ),
        report_640_internal_evidence=(
            "notebooks/new.ipynb lines around 24483-24484 rename the tensor into "
            "REPORT_640_Pottery_Report, and app/pipeline/stages/report_640.py computes the "
            "same B12 / B11 report output plus the threshold use in zero-point logic."
        ),
        existing_contract_reference="docs/REPORT_640_PARITY_VERIFICATION_CONTRACT.md",
        expected_formula_summary="B12 / B11",
        expected_input_outputs=("S2:B11", "S2:B12"),
        decision="covered_by_report_640_downstream_only",
        required_reference_outputs=("REPORT_640_Pottery_Report.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic item",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_action_needed_internal_precursor",
        blocker=(
            "Current evidence shows downstream REPORT_640 export coverage rather than a "
            "standalone AI_BEH_GoldAlloy_Signal file."
        ),
        recommended_next_action=(
            "Treat the pattern as covered by REPORT_640 downstream parity unless a "
            "standalone notebook export file is recovered later."
        ),
        notes=(
            "The downstream REPORT_640 verifier covers the exported effect, but that does "
            "not imply a separate notebook-named AI_BEH file exists."
        ),
    ),
    AIBehAnchorDecisionItem(
        id="ai_beh_massvolume_shadow_anchor",
        notebook_pattern="AI_BEH_MassVolume_Shadow",
        family="AI_BEH semantic rasters",
        source_status="existing_app_equivalent_available",
        authoritative_source_available=True,
        source_reference=(
            "notebooks/new.ipynb lines around 24468-24469 define "
            "AI_BEH_MassVolume_Shadow as B12 * ST_B10 / 1000 inside beh_tensors."
        ),
        standalone_export_evidence=(
            "No standalone notebook export filename was recovered for AI_BEH_MassVolume_Shadow. "
            "Instead, the notebook renames beh_tensors.select('AI_BEH_MassVolume_Shadow') "
            "to REPORT_640_Mass_Report inside the exported output stack."
        ),
        report_640_internal_evidence=(
            "notebooks/new.ipynb line 24483 renames the tensor into REPORT_640_Mass_Report, "
            "and app/pipeline/stages/report_640.py computes the same B12 * ST_B10 / 1000 "
            "report output."
        ),
        existing_contract_reference="docs/REPORT_640_PARITY_VERIFICATION_CONTRACT.md",
        expected_formula_summary="B12 * ST_B10 / 1000",
        expected_input_outputs=("S2:B12", "L9:ST_B10"),
        decision="covered_by_report_640_downstream_only",
        required_reference_outputs=("REPORT_640_Mass_Report.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic item",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_action_needed_internal_precursor",
        blocker=(
            "Current evidence shows downstream REPORT_640 export coverage rather than a "
            "standalone AI_BEH_MassVolume_Shadow file."
        ),
        recommended_next_action=(
            "Treat the pattern as covered by REPORT_640 downstream parity unless a "
            "standalone notebook export file is recovered later."
        ),
        notes=(
            "The downstream REPORT_640 verifier covers the exported effect, but that does "
            "not imply a separate notebook-named AI_BEH file exists."
        ),
    ),
)


def get_ai_beh_anchor_pattern_decisions() -> tuple[AIBehAnchorDecisionItem, ...]:
    """Return the four Phase 4H11 anchor-pattern decision items."""

    return _ITEMS


def write_ai_beh_anchor_pattern_decision_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[AIBehAnchorDecisionItem] | None = None,
    report_relative_path: str | Path = AI_BEH_ANCHOR_DECISION_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON decision report without creating raster or NPY outputs."""

    report_items = tuple(items or _ITEMS)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": AI_BEH_ANCHOR_DECISION_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_decision": _counts_by("decision", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status", report_items
        ),
        "phase_4h11_formula_changes": False,
        "notes": (
            "Phase 4H11 is decision and documentation work only. It does not implement "
            "AI_BEH anchor patterns, add new raster writers, or change REPORT_640 formulas."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[AIBehAnchorDecisionItem],
) -> dict[str, int]:
    if field_name == "decision":
        counts = {value: 0 for value in sorted(ALLOWED_DECISIONS)}
    elif field_name == "implementation_status":
        counts = {value: 0 for value in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    else:
        raise ValueError(f"unsupported count field: {field_name}")

    for item in items:
        counts[getattr(item, field_name)] += 1
    return counts
