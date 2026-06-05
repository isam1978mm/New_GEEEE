from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


PHASE_10_CLEAN_VS_PARITY_SCHEMA_VERSION = "phase_10_clean_vs_parity_decision_v1"
PHASE_10_CLEAN_VS_PARITY_REPORT_RELATIVE_PATH = (
    "manifests/phase_10_clean_vs_parity_decision.json"
)

ALLOWED_CATEGORIES = {
    "clean_app_core_outputs",
    "private_notebook_parity_outputs",
    "verifier_only_outputs",
    "source_recovered_not_implemented_outputs",
    "private_coordinate_map_outputs",
    "experimental_classifier_outputs",
    "probability_only_model_outputs",
    "future_reference_driven_implementation_candidates",
    "public_api_and_frontend_boundary",
    "artifact_serving_boundary",
}

ALLOWED_DECISIONS = {
    "clean_app_allowed",
    "parity_mode_private_only",
    "verifier_only",
    "source_recovered_deferred",
    "experimental_cli_only",
    "probability_design_only",
    "future_reference_driven",
    "public_boundary_locked",
    "artifact_serving_locked",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "no_runtime_change_decision_only",
    "no_action_needed_current_boundary",
    "requires_reference_output",
    "requires_verifier_contract",
    "requires_user_approved_future_phase",
    "implementation_deferred",
}


@dataclass(frozen=True)
class CleanVsParityDecisionItem:
    id: str
    category: str
    decision: str
    applies_to: tuple[str, ...]
    source_contracts: tuple[str, ...]
    clean_app_allowed: bool
    parity_mode_allowed: bool
    experimental_allowed: bool
    filesystem_only: bool
    http_servable: bool
    frontend_visible: bool
    downloadable_via_api: bool
    called_by_api: bool
    called_by_background_tasks: bool
    called_by_core_orchestrator: bool
    requires_enable_experimental: bool
    requires_frozen_reference: bool
    runtime_output_verified: bool
    notebook_value_parity_verified: bool
    implementation_status: str
    blocker: str
    recommended_next_action: str
    notes: str

    def __post_init__(self) -> None:
        if self.category not in ALLOWED_CATEGORIES:
            raise ValueError(f"unsupported category: {self.category}")
        if self.decision not in ALLOWED_DECISIONS:
            raise ValueError(f"unsupported decision: {self.decision}")
        if self.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"unsupported implementation_status: {self.implementation_status}"
            )
        if self.notebook_value_parity_verified and not self.requires_frozen_reference:
            raise ValueError(
                "notebook value parity cannot be true without frozen reference coverage"
            )
        if self.category in {
            "private_notebook_parity_outputs",
            "verifier_only_outputs",
            "source_recovered_not_implemented_outputs",
            "private_coordinate_map_outputs",
        }:
            if not self.filesystem_only:
                raise ValueError(f"{self.category} must remain filesystem_only")
            if self.http_servable:
                raise ValueError(f"{self.category} must not be http_servable")
        if self.category in {
            "experimental_classifier_outputs",
            "probability_only_model_outputs",
        }:
            if not self.experimental_allowed:
                raise ValueError(f"{self.category} must remain experimental_allowed")
            if not self.requires_enable_experimental:
                raise ValueError(
                    f"{self.category} must require ENABLE_EXPERIMENTAL"
                )
            if self.called_by_api:
                raise ValueError(f"{self.category} must not be called by API")
            if self.called_by_background_tasks:
                raise ValueError(
                    f"{self.category} must not be called by BackgroundTasks"
                )
            if self.called_by_core_orchestrator:
                raise ValueError(
                    f"{self.category} must not be called by the core orchestrator"
                )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_DECISIONS: tuple[CleanVsParityDecisionItem, ...] = (
    CleanVsParityDecisionItem(
        id="phase10_clean_app_core_outputs",
        category="clean_app_core_outputs",
        decision="clean_app_allowed",
        applies_to=(
            "GRID and run lifecycle",
            "DEM and DEM derivatives",
            "SAR RTC support outputs",
            "thermal and Sentinel-2 index outputs",
            "hypercube, PCA anomaly, object extraction, and alignment QA",
        ),
        source_contracts=(
            "docs/PRD_v0.5.md",
            "docs/PARITY_MODE_CONTRACT.md",
            "docs/PARITY_PHASE_0_OUTPUT_INVENTORY_LOCK.md",
        ),
        clean_app_allowed=True,
        parity_mode_allowed=False,
        experimental_allowed=False,
        filesystem_only=False,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=True,
        called_by_background_tasks=True,
        called_by_core_orchestrator=True,
        requires_enable_experimental=False,
        requires_frozen_reference=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_action_needed_current_boundary",
        blocker="The clean app boundary must stay narrower than the private notebook-parity surface.",
        recommended_next_action="Keep clean app behavior tied to defensible runtime outputs and existing serving controls.",
        notes=(
            "This decision does not widen HTTP exposure. It records which output families "
            "belong to the normal runtime path."
        ),
    ),
    CleanVsParityDecisionItem(
        id="phase10_private_notebook_parity_outputs",
        category="private_notebook_parity_outputs",
        decision="parity_mode_private_only",
        applies_to=(
            "notebook-compatible report layers",
            "notebook-compatible semantic raster families",
            "private parity aliases and parity manifests",
        ),
        source_contracts=(
            "docs/PARITY_MODE_CONTRACT.md",
            "docs/PHASE_4_FINAL_COVERAGE_SUMMARY.md",
            "docs/PHASE_9_END_TO_END_PARITY_HARNESS.md",
        ),
        clean_app_allowed=False,
        parity_mode_allowed=True,
        experimental_allowed=False,
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        requires_enable_experimental=False,
        requires_frozen_reference=True,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_runtime_change_decision_only",
        blocker="Private notebook outputs are broader than the clean app runtime surface.",
        recommended_next_action="Keep notebook-parity outputs private unless a later user-approved phase changes exposure policy.",
        notes=(
            "Runtime output presence and notebook-value parity stay separate. Similar app "
            "outputs do not upgrade private notebook outputs into clean app behavior."
        ),
    ),
    CleanVsParityDecisionItem(
        id="phase10_verifier_only_outputs",
        category="verifier_only_outputs",
        decision="verifier_only",
        applies_to=(
            "REPORT_640 parity family",
            "secret-layer parity family",
            "support-stack verifier families",
        ),
        source_contracts=(
            "docs/PHASE_9_END_TO_END_PARITY_HARNESS.md",
            "docs/REPORT_640_PARITY_VERIFICATION_CONTRACT.md",
            "docs/SECRET_LAYERS_PARITY_VERIFICATION_CONTRACT.md",
        ),
        clean_app_allowed=False,
        parity_mode_allowed=True,
        experimental_allowed=False,
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        requires_enable_experimental=False,
        requires_frozen_reference=True,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_action_needed_current_boundary",
        blocker="A verifier contract does not make a private family part of the clean runtime surface.",
        recommended_next_action="Use verifier-backed families for private comparison only, not as public or default outputs.",
        notes=(
            "Verifier-backed notebook families remain private unless a later phase adds a "
            "separate runtime and exposure decision."
        ),
    ),
    CleanVsParityDecisionItem(
        id="phase10_source_recovered_not_implemented_outputs",
        category="source_recovered_not_implemented_outputs",
        decision="source_recovered_deferred",
        applies_to=(
            "source-recovered semantic families without runtime writers",
            "source-recovered support stacks that still need implementation review",
        ),
        source_contracts=(
            "docs/PHASE_4_FINAL_COVERAGE_SUMMARY.md",
            "docs/SEMANTIC_RASTER_RECOVERY_CONTRACT.md",
            "docs/PHASE_9_END_TO_END_PARITY_HARNESS.md",
        ),
        clean_app_allowed=False,
        parity_mode_allowed=True,
        experimental_allowed=False,
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        requires_enable_experimental=False,
        requires_frozen_reference=True,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="implementation_deferred",
        blocker="Source recovery alone does not justify runtime implementation or public exposure.",
        recommended_next_action="Keep these outputs deferred until a later source-driven and reference-driven phase is explicitly approved.",
        notes=(
            "Recovered formulas and metadata locks stay private planning inputs only until "
            "the user approves implementation work."
        ),
    ),
    CleanVsParityDecisionItem(
        id="phase10_private_coordinate_map_outputs",
        category="private_coordinate_map_outputs",
        decision="parity_mode_private_only",
        applies_to=(
            "KMZ outputs",
            "GeoJSON outputs",
            "heatmap and visual map outputs",
            "coordinate-bearing local filesystem artifacts",
        ),
        source_contracts=(
            "docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md",
            "docs/PRD_v0.5.md",
            "docs/PARITY_MODE_CONTRACT.md",
        ),
        clean_app_allowed=False,
        parity_mode_allowed=True,
        experimental_allowed=False,
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        requires_enable_experimental=False,
        requires_frozen_reference=True,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_action_needed_current_boundary",
        blocker="Coordinate-bearing artifacts remain outside the clean app and public HTTP surface.",
        recommended_next_action="Keep coordinate and map artifacts private until a later user-approved redaction or serving phase exists.",
        notes=(
            "Private coordinate-bearing artifacts stay filesystem-only by default and do "
            "not appear in API or frontend output lists."
        ),
    ),
    CleanVsParityDecisionItem(
        id="phase10_experimental_classifier_outputs",
        category="experimental_classifier_outputs",
        decision="experimental_cli_only",
        applies_to=(
            "neutral classifier CSV outputs",
            "experimental summary outputs",
            "experimental class mapping outputs",
        ),
        source_contracts=(
            "docs/PRD_v0.5.md",
            "docs/PHASE_7_CLASSIFIER_MODEL_PARITY_CONTRACT.md",
        ),
        clean_app_allowed=False,
        parity_mode_allowed=False,
        experimental_allowed=True,
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        requires_enable_experimental=True,
        requires_frozen_reference=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_action_needed_current_boundary",
        blocker="Experimental classifier outputs are private research artifacts, not clean app outputs.",
        recommended_next_action="Keep the classifier CLI-only and env-gated unless a later user-approved phase changes the runtime boundary.",
        notes=(
            "This decision preserves the current experimental gate and keeps classifier "
            "artifacts out of API, frontend, BackgroundTasks, and the core orchestrator."
        ),
    ),
    CleanVsParityDecisionItem(
        id="phase10_probability_only_model_outputs",
        category="probability_only_model_outputs",
        decision="probability_design_only",
        applies_to=(
            "future probability tables",
            "future uncertainty summaries",
            "future neutral probability labels",
        ),
        source_contracts=(
            "docs/PHASE_8_PROBABILITY_ONLY_CLASSIFIER_DESIGN.md",
            "docs/PRD_v0.5.md",
        ),
        clean_app_allowed=False,
        parity_mode_allowed=False,
        experimental_allowed=True,
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        requires_enable_experimental=True,
        requires_frozen_reference=True,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_runtime_change_decision_only",
        blocker="Probability-model interpretation remains a private design surface only.",
        recommended_next_action="Keep future model interpretation probability-only and private until references and verifier rules are locked.",
        notes=(
            "Future model interpretation may use probability, likelihood, score, rank, or "
            "uncertainty wording only."
        ),
    ),
    CleanVsParityDecisionItem(
        id="phase10_future_reference_driven_candidates",
        category="future_reference_driven_implementation_candidates",
        decision="future_reference_driven",
        applies_to=(
            "private notebook-only runtime candidates",
            "future parity writers that still need references",
            "future private verifiers that still need frozen bundles",
        ),
        source_contracts=(
            "docs/PHASE_4_FINAL_COVERAGE_SUMMARY.md",
            "docs/PHASE_9_END_TO_END_PARITY_HARNESS.md",
            "docs/PARITY_PHASE_0_OUTPUT_INVENTORY_LOCK.md",
        ),
        clean_app_allowed=False,
        parity_mode_allowed=True,
        experimental_allowed=True,
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        requires_enable_experimental=False,
        requires_frozen_reference=True,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_user_approved_future_phase",
        blocker="Later implementation candidates still need user approval plus frozen references and source-backed contracts.",
        recommended_next_action="Do not implement candidate private outputs unless a later phase is explicitly approved and reference material is available.",
        notes=(
            "Future private output work must be driven by source contracts and frozen "
            "reference bundles, not by nearby app outputs that look similar."
        ),
    ),
    CleanVsParityDecisionItem(
        id="phase10_public_api_and_frontend_boundary",
        category="public_api_and_frontend_boundary",
        decision="public_boundary_locked",
        applies_to=(
            "public API DTO surface",
            "frontend result views",
            "artifact lists and previews",
        ),
        source_contracts=(
            "docs/PRD_v0.5.md",
            "docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md",
            "docs/PHASE_7_CLASSIFIER_MODEL_PARITY_CONTRACT.md",
            "docs/PHASE_8_PROBABILITY_ONLY_CLASSIFIER_DESIGN.md",
        ),
        clean_app_allowed=True,
        parity_mode_allowed=False,
        experimental_allowed=False,
        filesystem_only=False,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=True,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        requires_enable_experimental=False,
        requires_frozen_reference=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_action_needed_current_boundary",
        blocker="Private notebook, coordinate, classifier, and model artifacts must stay out of public DTOs and UI surfaces.",
        recommended_next_action="Keep redaction and UI boundaries unchanged unless a later user-approved phase defines a narrower public-safe surface.",
        notes=(
            "Private artifacts remain absent from public API and frontend surfaces even "
            "when they exist locally."
        ),
    ),
    CleanVsParityDecisionItem(
        id="phase10_artifact_serving_boundary",
        category="artifact_serving_boundary",
        decision="artifact_serving_locked",
        applies_to=(
            "artifact classes",
            "serve_artifact_response guard path",
            "can_serve_artifact policy boundary",
        ),
        source_contracts=(
            "docs/PRD_v0.5.md",
            "docs/PARITY_MODE_CONTRACT.md",
        ),
        clean_app_allowed=True,
        parity_mode_allowed=False,
        experimental_allowed=False,
        filesystem_only=False,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=True,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        requires_enable_experimental=False,
        requires_frozen_reference=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_action_needed_current_boundary",
        blocker="Phase 10 is not allowed to change artifact-serving policy.",
        recommended_next_action="Leave artifact-serving behavior unchanged and treat any serving change as a separate user-approved phase.",
        notes=(
            "No Phase 10 serving-policy change is allowed. Existing artifact classes and "
            "guard paths remain the only approved HTTP boundary."
        ),
    ),
)


def get_phase_10_clean_vs_parity_decisions() -> tuple[CleanVsParityDecisionItem, ...]:
    return _DECISIONS


def write_phase_10_clean_vs_parity_decision_report(
    *,
    run_dir: str | Path,
    run_id: str,
    report_relative_path: str | Path = PHASE_10_CLEAN_VS_PARITY_REPORT_RELATIVE_PATH,
) -> Path:
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    items = get_phase_10_clean_vs_parity_decisions()
    payload = {
        "schema_version": PHASE_10_CLEAN_VS_PARITY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in items],
        "counts_by_category": _counts_by_attribute(items, "category"),
        "counts_by_decision": _counts_by_attribute(items, "decision"),
        "counts_by_implementation_status": _counts_by_attribute(
            items, "implementation_status"
        ),
        "phase_10_runtime_changes": False,
        "public_exposure_changes": False,
        "artifact_serving_changes": False,
        "notes": (
            "Phase 10 is a decision-only boundary lock. It does not implement runtime "
            "behavior and does not widen public exposure."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by_attribute(
    items: Iterable[CleanVsParityDecisionItem],
    attribute_name: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        key = str(getattr(item, attribute_name))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))
