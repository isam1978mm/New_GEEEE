from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


PHASE_8_PROBABILITY_ONLY_SCHEMA_VERSION = "phase_8_probability_only_classifier_design_v1"
PHASE_8_PROBABILITY_ONLY_REPORT_RELATIVE_PATH = (
    "manifests/phase_8_probability_only_classifier_design.json"
)

ALLOWED_CATEGORIES = {
    "probability_output_schema",
    "neutral_class_probability_labels",
    "threshold_and_uncertainty_policy",
    "private_cli_only_boundary",
    "forbidden_wording_policy",
    "future_reference_and_verifier_requirements",
}

ALLOWED_DESIGN_STATUSES = {
    "design_contract_only",
    "source_recovery_needed",
    "reference_needed",
    "verifier_needed",
    "implementation_later",
    "blocked",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "no_runtime_change_design_only",
    "requires_reference_output",
    "requires_verifier_contract",
    "requires_private_cli_contract",
    "requires_source_reconstruction",
    "implementation_deferred",
}

ALLOWED_ARTIFACT_CLASSES = {
    "LOCAL_SENSITIVE",
    "EXPERIMENTAL_CLASSIFIER_ARTIFACT",
}

_FORBIDDEN_WORDING: tuple[str, ...] = (
    "confirmed",
    "found",
    "proven",
    "dig target",
    "definitely",
    "discovery",
    "burial proven",
    "tomb confirmed",
    "target confirmed",
)

_ALLOWED_WORDING: tuple[str, ...] = (
    "probability",
    "likelihood",
    "score",
    "confidence_interval",
    "uncertainty",
    "class_probability",
    "rank",
)

_COMMON_REQUIRED_METADATA = (
    "neutral class label map",
    "private CLI execution boundary",
    "ENABLE_EXPERIMENTAL gate",
    "run-relative experimental path mapping",
    "frozen notebook reference bundle path",
    "model or rule source context",
    "calibration status",
    "public DTO redaction boundary",
)

_COMMON_ALLOWED_FIELDS = (
    "object_id",
    "cluster_id",
    "class_id",
    "Class_A_probability",
    "Class_B_probability",
    "Class_C_probability",
    "class_probability",
    "class_score",
    "probability_band",
    "confidence_interval",
    "uncertainty",
    "rank",
    "model_version",
    "calibration_status",
)

_COMMON_FORBIDDEN_FIELDS = (
    "classifier_label",
    "model_output_public_payload",
    "raw_coordinates",
    "geometry",
    "bounds",
    "crs_transform",
    "local_path",
    "private_artifact_hash",
    "field_action",
    "certainty_label",
)


@dataclass(frozen=True)
class ProbabilityOnlyClassifierDesignItem:
    id: str
    category: str
    design_status: str
    source_context: str
    future_app_artifact_or_pattern: str
    probability_only_required: bool
    allowed_output_fields: tuple[str, ...]
    forbidden_output_fields: tuple[str, ...]
    allowed_wording: tuple[str, ...]
    forbidden_wording: tuple[str, ...]
    expected_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    required_reference_artifacts: tuple[str, ...]
    required_metadata: tuple[str, ...]
    target_mode: str
    classification: str
    artifact_class: str
    filesystem_only: bool
    cli_only: bool
    requires_enable_experimental: bool
    http_servable: bool
    frontend_visible: bool
    downloadable_via_api: bool
    called_by_api: bool
    called_by_background_tasks: bool
    called_by_core_orchestrator: bool
    runtime_output_verified: bool
    notebook_value_parity_verified: bool
    implementation_status: str
    blocker: str
    recommended_next_action: str
    notes: str

    def __post_init__(self) -> None:
        if self.category not in ALLOWED_CATEGORIES:
            raise ValueError(f"unsupported category: {self.category}")
        if self.design_status not in ALLOWED_DESIGN_STATUSES:
            raise ValueError(f"unsupported design_status: {self.design_status}")
        if self.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"unsupported implementation_status: {self.implementation_status}"
            )
        if self.artifact_class not in ALLOWED_ARTIFACT_CLASSES:
            raise ValueError(f"unsupported artifact_class: {self.artifact_class}")
        if not self.probability_only_required:
            raise ValueError("Phase 8 items must require probability-only output")
        if self.target_mode == "public_shared":
            raise ValueError("Phase 8 design items must not target public_shared")
        if not self.filesystem_only:
            raise ValueError("Phase 8 classifier artifacts must remain filesystem_only")
        if not self.cli_only:
            raise ValueError("Phase 8 classifier artifacts must remain cli_only")
        if not self.requires_enable_experimental:
            raise ValueError("Phase 8 classifier artifacts must require ENABLE_EXPERIMENTAL")
        if self.http_servable:
            raise ValueError("Phase 8 classifier artifacts must not be http_servable")
        if self.frontend_visible:
            raise ValueError("Phase 8 classifier artifacts must not be frontend_visible")
        if self.downloadable_via_api:
            raise ValueError("Phase 8 classifier artifacts must not be downloadable_via_api")
        if self.called_by_api:
            raise ValueError("Phase 8 classifier artifacts must not be called by API")
        if self.called_by_background_tasks:
            raise ValueError(
                "Phase 8 classifier artifacts must not be called by BackgroundTasks"
            )
        if self.called_by_core_orchestrator:
            raise ValueError(
                "Phase 8 classifier artifacts must not be called by core orchestrator"
            )
        if self.runtime_output_verified:
            raise ValueError("Phase 8 design only; runtime output verification must be false")
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 8 design only; notebook value parity must be false")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_DESIGN_ITEMS: tuple[ProbabilityOnlyClassifierDesignItem, ...] = (
    ProbabilityOnlyClassifierDesignItem(
        id="phase8_probability_output_schema",
        category="probability_output_schema",
        design_status="design_contract_only",
        source_context=(
            "Notebook classifier and model cells include hard labels, softmax-style "
            "probability vectors, and private coordinate outputs; app-side Phase 8 "
            "keeps only a private probability schema contract."
        ),
        future_app_artifact_or_pattern=(
            "experimental/probability_scores.json or experimental/probability_scores.csv"
        ),
        probability_only_required=True,
        allowed_output_fields=_COMMON_ALLOWED_FIELDS,
        forbidden_output_fields=_COMMON_FORBIDDEN_FIELDS,
        allowed_wording=_ALLOWED_WORDING,
        forbidden_wording=_FORBIDDEN_WORDING,
        expected_inputs=("neutral classifier rows", "object table", "cluster table"),
        expected_outputs=(
            "private probability table with Class_A_probability, Class_B_probability, and Class_C_probability fields",
            "private summary with calibration_status and uncertainty fields",
        ),
        required_reference_artifacts=(
            "frozen notebook probability or score reports",
            "source-cell schema notes for future app writer mapping",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="experimental_private",
        classification="private probability-only classifier design",
        artifact_class="EXPERIMENTAL_CLASSIFIER_ARTIFACT",
        filesystem_only=True,
        cli_only=True,
        requires_enable_experimental=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_runtime_change_design_only",
        blocker="",
        recommended_next_action="Use this schema only after a later source/reference-backed implementation slice is approved.",
        notes="Phase 8 records a schema contract only and does not calculate probabilities.",
    ),
    ProbabilityOnlyClassifierDesignItem(
        id="phase8_neutral_class_probability_labels",
        category="neutral_class_probability_labels",
        design_status="design_contract_only",
        source_context=(
            "Phase 7 locked app-facing classifier labels as Class_A through Class_N. "
            "Phase 8 extends that boundary to future probability fields."
        ),
        future_app_artifact_or_pattern="experimental/neutral_class_probabilities.*",
        probability_only_required=True,
        allowed_output_fields=(
            "Class_A_probability",
            "Class_B_probability",
            "Class_C_probability",
            "Class_D_probability",
            "Class_E_probability",
            "class_probability",
            "class_score",
            "rank",
        ),
        forbidden_output_fields=_COMMON_FORBIDDEN_FIELDS,
        allowed_wording=_ALLOWED_WORDING,
        forbidden_wording=_FORBIDDEN_WORDING,
        expected_inputs=("neutral class definitions", "private class mapping documentation"),
        expected_outputs=("private neutral class-probability rows",),
        required_reference_artifacts=("private label mapping and frozen notebook references",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="experimental_private",
        classification="private neutral class probability design",
        artifact_class="EXPERIMENTAL_CLASSIFIER_ARTIFACT",
        filesystem_only=True,
        cli_only=True,
        requires_enable_experimental=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_runtime_change_design_only",
        blocker="",
        recommended_next_action="Keep future app-facing probability columns neutral and private.",
        notes="Original notebook label names stay out of app-facing probability artifacts.",
    ),
    ProbabilityOnlyClassifierDesignItem(
        id="phase8_threshold_and_uncertainty_policy",
        category="threshold_and_uncertainty_policy",
        design_status="design_contract_only",
        source_context=(
            "Notebook cells mix threshold logic and reliability-style values. Phase 8 "
            "requires future outputs to state calibration and uncertainty context."
        ),
        future_app_artifact_or_pattern="experimental/probability_threshold_policy.json",
        probability_only_required=True,
        allowed_output_fields=(
            "threshold_name",
            "threshold_value",
            "calibration_status",
            "uncertainty",
            "confidence_interval",
            "probability_band",
            "rank",
        ),
        forbidden_output_fields=_COMMON_FORBIDDEN_FIELDS,
        allowed_wording=_ALLOWED_WORDING,
        forbidden_wording=_FORBIDDEN_WORDING,
        expected_inputs=("validation metadata if later available", "probability or score rows"),
        expected_outputs=("private threshold and uncertainty metadata",),
        required_reference_artifacts=(
            "frozen notebook threshold outputs",
            "calibration or validation evidence if later available",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="experimental_private",
        classification="private probability threshold design",
        artifact_class="LOCAL_SENSITIVE",
        filesystem_only=True,
        cli_only=True,
        requires_enable_experimental=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="implementation_deferred",
        blocker="No frozen probability reference bundle or calibration evidence is locked.",
        recommended_next_action="Lock reference outputs and calibration vocabulary before any threshold writer is implemented.",
        notes="Uncalibrated values must remain labeled as scores or uncalibrated probabilities.",
    ),
    ProbabilityOnlyClassifierDesignItem(
        id="phase8_private_cli_only_boundary",
        category="private_cli_only_boundary",
        design_status="design_contract_only",
        source_context=(
            "Phase 6 and Phase 7 keep coordinate and classifier artifacts private, "
            "filesystem-only, and outside API/frontend behavior."
        ),
        future_app_artifact_or_pattern="experimental/probability_* private files only",
        probability_only_required=True,
        allowed_output_fields=_COMMON_ALLOWED_FIELDS,
        forbidden_output_fields=_COMMON_FORBIDDEN_FIELDS,
        allowed_wording=_ALLOWED_WORDING,
        forbidden_wording=_FORBIDDEN_WORDING,
        expected_inputs=("ENABLE_EXPERIMENTAL=1", "completed core run", "private run directory"),
        expected_outputs=("filesystem-only experimental probability artifacts",),
        required_reference_artifacts=("private boundary contract and source references",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="experimental_private",
        classification="private CLI-only probability artifact boundary",
        artifact_class="EXPERIMENTAL_CLASSIFIER_ARTIFACT",
        filesystem_only=True,
        cli_only=True,
        requires_enable_experimental=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_runtime_change_design_only",
        blocker="",
        recommended_next_action="Keep probability artifacts outside API, frontend, BackgroundTasks, and core orchestration.",
        notes="Phase 8 does not change the existing experimental CLI boundary.",
    ),
    ProbabilityOnlyClassifierDesignItem(
        id="phase8_forbidden_wording_policy",
        category="forbidden_wording_policy",
        design_status="design_contract_only",
        source_context=(
            "Project policy requires interpreted classifier/model outputs to avoid "
            "certainty or field-action wording."
        ),
        future_app_artifact_or_pattern="all future private classifier/model probability artifacts",
        probability_only_required=True,
        allowed_output_fields=_COMMON_ALLOWED_FIELDS,
        forbidden_output_fields=_COMMON_FORBIDDEN_FIELDS,
        allowed_wording=_ALLOWED_WORDING,
        forbidden_wording=_FORBIDDEN_WORDING,
        expected_inputs=("future private classifier/model outputs",),
        expected_outputs=("private probability wording that avoids certainty claims",),
        required_reference_artifacts=("source/references for wording and schema checks",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="experimental_private",
        classification="private probability wording policy",
        artifact_class="LOCAL_SENSITIVE",
        filesystem_only=True,
        cli_only=True,
        requires_enable_experimental=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_runtime_change_design_only",
        blocker="",
        recommended_next_action="Apply the blocked term list in any later private classifier writer or verifier slice.",
        notes="The explicit blocked wording set is stored in this inventory item for future checks.",
    ),
    ProbabilityOnlyClassifierDesignItem(
        id="phase8_future_reference_and_verifier_requirements",
        category="future_reference_and_verifier_requirements",
        design_status="reference_needed",
        source_context=(
            "Notebook cells contain probability-style values and model attempts, but "
            "future parity requires frozen references before notebook-value checks can pass."
        ),
        future_app_artifact_or_pattern="experimental/probability parity report",
        probability_only_required=True,
        allowed_output_fields=_COMMON_ALLOWED_FIELDS,
        forbidden_output_fields=_COMMON_FORBIDDEN_FIELDS,
        allowed_wording=_ALLOWED_WORDING,
        forbidden_wording=_FORBIDDEN_WORDING,
        expected_inputs=(
            "frozen notebook classifier/model references",
            "private app probability outputs from a later implementation",
        ),
        expected_outputs=("private verifier report comparing schema, labels, values, and wording",),
        required_reference_artifacts=(
            "frozen notebook probability outputs",
            "source-cell mapping",
            "expected schema and tolerance metadata",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="experimental_private",
        classification="private probability verifier planning",
        artifact_class="EXPERIMENTAL_CLASSIFIER_ARTIFACT",
        filesystem_only=True,
        cli_only=True,
        requires_enable_experimental=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        called_by_api=False,
        called_by_background_tasks=False,
        called_by_core_orchestrator=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker="Frozen probability references, schema expectations, and tolerance metadata are not locked.",
        recommended_next_action="Recover frozen references and source-cell mappings before creating a probability verifier.",
        notes="Notebook-value parity cannot pass without reference artifacts and a later verifier.",
    ),
)


def get_phase_8_probability_only_classifier_design() -> tuple[
    ProbabilityOnlyClassifierDesignItem,
    ...
]:
    """Return the Phase 8 probability-only classifier design inventory."""

    return _DESIGN_ITEMS


def write_phase_8_probability_only_classifier_design_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[ProbabilityOnlyClassifierDesignItem] | None = None,
    report_relative_path: str | Path = PHASE_8_PROBABILITY_ONLY_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local Phase 8 design report without creating classifier artifacts."""

    report_items = tuple(items or _DESIGN_ITEMS)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": PHASE_8_PROBABILITY_ONLY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_category": _counts_by("category", report_items),
        "counts_by_design_status": _counts_by("design_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "counts_by_artifact_class": _counts_by("artifact_class", report_items),
        "phase_8_runtime_changes": False,
        "public_exposure_changes": False,
        "probability_only_contract": True,
        "notes": (
            "Phase 8 is probability-only design, private classifier/model boundary, "
            "and verification planning. It does not train models, run inference, "
            "calculate scores, change artifact serving, or claim notebook-value parity."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[ProbabilityOnlyClassifierDesignItem],
) -> dict[str, int]:
    if field_name == "category":
        counts = {value: 0 for value in sorted(ALLOWED_CATEGORIES)}
    elif field_name == "design_status":
        counts = {value: 0 for value in sorted(ALLOWED_DESIGN_STATUSES)}
    elif field_name == "implementation_status":
        counts = {value: 0 for value in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    elif field_name == "artifact_class":
        counts = {value: 0 for value in sorted(ALLOWED_ARTIFACT_CLASSES)}
    else:
        raise ValueError(f"unsupported count field: {field_name}")

    for item in items:
        counts[getattr(item, field_name)] += 1
    return counts
