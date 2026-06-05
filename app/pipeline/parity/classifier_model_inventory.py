from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


PHASE_7_CLASSIFIER_MODEL_SCHEMA_VERSION = "phase_7_classifier_model_inventory_v1"
PHASE_7_CLASSIFIER_MODEL_REPORT_RELATIVE_PATH = (
    "manifests/phase_7_classifier_model_inventory.json"
)

ALLOWED_CATEGORIES = {
    "notebook_rule_based_classifier",
    "neutral_label_mapping",
    "experimental_cli_boundary",
    "deep_learning_model_cells",
    "classifier_inputs_outputs",
    "public_exposure_boundary",
}

ALLOWED_SOURCE_STATUSES = {
    "exact_source_found",
    "partial_source_found",
    "no_source_found",
    "existing_app_equivalent_found",
    "unknown_needs_reference",
}

ALLOWED_PARITY_STATUSES = {
    "covered_by_existing_contract",
    "inventory_only",
    "verifier_needed",
    "reference_needed",
    "source_recovery_needed",
    "implementation_later",
    "blocked",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "no_action_needed_existing_contract",
    "requires_verifier_contract",
    "requires_reference_output",
    "requires_source_reconstruction",
    "requires_private_cli_contract",
    "requires_inventory_reconciliation",
    "implementation_deferred",
}

ALLOWED_ARTIFACT_CLASSES = {
    "LOCAL_SENSITIVE",
    "EXPERIMENTAL_CLASSIFIER_ARTIFACT",
}

_COMMON_REQUIRED_METADATA = (
    "classifier output artifact class",
    "CLI-only execution boundary",
    "ENABLE_EXPERIMENTAL gate",
    "run-relative experimental path mapping",
    "neutral app-facing class identifiers",
    "reference artifact bundle and source cell mapping",
    "redaction boundary for any public DTO references",
)


@dataclass(frozen=True)
class ClassifierModelInventoryItem:
    id: str
    category: str
    notebook_artifact_or_pattern: str
    current_app_artifact_or_pattern: str
    source_status: str
    current_app_status: str
    parity_status: str
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
        if self.source_status not in ALLOWED_SOURCE_STATUSES:
            raise ValueError(f"unsupported source_status: {self.source_status}")
        if self.parity_status not in ALLOWED_PARITY_STATUSES:
            raise ValueError(f"unsupported parity_status: {self.parity_status}")
        if self.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"unsupported implementation_status: {self.implementation_status}"
            )
        if self.artifact_class not in ALLOWED_ARTIFACT_CLASSES:
            raise ValueError(f"unsupported artifact_class: {self.artifact_class}")
        if self.target_mode == "public_shared":
            raise ValueError("Phase 7 inventory items must not target public_shared")
        if not self.filesystem_only:
            raise ValueError("Phase 7 classifier artifacts must remain filesystem_only")
        if not self.cli_only:
            raise ValueError("Phase 7 classifier artifacts must remain cli_only")
        if not self.requires_enable_experimental:
            raise ValueError("Phase 7 classifier artifacts must require ENABLE_EXPERIMENTAL")
        if self.http_servable:
            raise ValueError("Phase 7 classifier artifacts must not be http_servable")
        if self.frontend_visible:
            raise ValueError("Phase 7 classifier artifacts must not be frontend_visible")
        if self.downloadable_via_api:
            raise ValueError("Phase 7 classifier artifacts must not be downloadable_via_api")
        if self.called_by_api:
            raise ValueError("Phase 7 classifier artifacts must not be called by API")
        if self.called_by_background_tasks:
            raise ValueError(
                "Phase 7 classifier artifacts must not be called by BackgroundTasks"
            )
        if self.called_by_core_orchestrator:
            raise ValueError(
                "Phase 7 classifier artifacts must not be called by core orchestrator"
            )
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 7 inventory only; notebook value parity must be false")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_INVENTORY: tuple[ClassifierModelInventoryItem, ...] = (
    ClassifierModelInventoryItem(
        id="phase7_notebook_rule_based_classifier",
        category="notebook_rule_based_classifier",
        notebook_artifact_or_pattern=(
            "Notebook hard-classifier CSV, JSON, GeoJSON, and text outputs from "
            "rule-based classifier cells"
        ),
        current_app_artifact_or_pattern=(
            "No app writer for original notebook hard-classifier output files"
        ),
        source_status="partial_source_found",
        current_app_status=(
            "Notebook cell summaries identify rule-based classifier branches; app parity "
            "does not implement those original output writers."
        ),
        parity_status="source_recovery_needed",
        expected_inputs=("hypercube bands", "focus mask", "object table", "GRID metadata"),
        expected_outputs=(
            "private original-reference classifier reports if a later parity slice approves them",
        ),
        required_reference_artifacts=(
            "frozen notebook classifier CSV, JSON, TXT, or GeoJSON artifacts",
            "source cell snippets for rule and output schema mapping",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="experimental_private",
        classification="private classifier/model parity inventory",
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
        implementation_status="requires_source_reconstruction",
        blocker="Notebook hard-classifier branches do not have a locked private reference bundle or app writer mapping.",
        recommended_next_action="Recover source and frozen references before any private classifier verifier or writer slice.",
        notes=(
            "This item records classifier parity planning only. It does not implement or "
            "run classifier rules."
        ),
    ),
    ClassifierModelInventoryItem(
        id="phase7_neutral_label_mapping",
        category="neutral_label_mapping",
        notebook_artifact_or_pattern=(
            "Original notebook label mapping retained only in private documentation"
        ),
        current_app_artifact_or_pattern=(
            "Class_A through Class_N in app/pipeline/stages_experimental/classes.py"
        ),
        source_status="exact_source_found",
        current_app_status=(
            "Experimental classes use neutral identifiers Class_A, Class_B, Class_C, "
            "and later neutral class IDs only."
        ),
        parity_status="covered_by_existing_contract",
        expected_inputs=("neutral class definitions", "private mapping documentation"),
        expected_outputs=(
            "experimental/neutral_target_labels.json",
            "neutral app-facing class identifiers",
        ),
        required_reference_artifacts=("private class mapping documentation",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="experimental_private",
        classification="private neutral classifier label inventory",
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
        implementation_status="no_action_needed_existing_contract",
        blocker="",
        recommended_next_action=(
            "Keep app-facing classifier labels neutral and keep original mappings in private docs only."
        ),
        notes=(
            "App-facing labels remain Class_A, Class_B, Class_C, and later neutral IDs. "
            "Original notebook labels must not enter app code, API responses, logs, or frontend files."
        ),
    ),
    ClassifierModelInventoryItem(
        id="phase7_experimental_cli_boundary",
        category="experimental_cli_boundary",
        notebook_artifact_or_pattern="Notebook classifier execution cells and model driver cells",
        current_app_artifact_or_pattern=(
            "python -m app.pipeline.stages_experimental.run --run-id <id>"
        ),
        source_status="exact_source_found",
        current_app_status=(
            "Existing experimental module is import-gated, CLI-only, and writes under the run experimental folder."
        ),
        parity_status="covered_by_existing_contract",
        expected_inputs=("completed core run", "validated required artifacts", "ENABLE_EXPERIMENTAL=1"),
        expected_outputs=("experimental/classifications.csv", "experimental/summary.json"),
        required_reference_artifacts=("experimental module README and source boundary",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="experimental_private",
        classification="private experimental CLI boundary inventory",
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
        implementation_status="no_action_needed_existing_contract",
        blocker="",
        recommended_next_action="Keep the experimental classifier out of API, frontend, BackgroundTasks, and core orchestration.",
        notes="Phase 7 does not change the existing CLI boundary or execute the classifier.",
    ),
    ClassifierModelInventoryItem(
        id="phase7_deep_learning_model_cells",
        category="deep_learning_model_cells",
        notebook_artifact_or_pattern=(
            "Swin, UnetPlusPlus, ResNet50, SegFormer, YOLO-style, CNN, and model "
            "training/inference notebook cells"
        ),
        current_app_artifact_or_pattern="No app deep-learning model implementation in Phase 7 scope",
        source_status="partial_source_found",
        current_app_status=(
            "Notebook cell summaries identify model build and inference attempts; no heavy ML dependency, model weights, or training path is added."
        ),
        parity_status="implementation_later",
        expected_inputs=("model tensors", "weights if later approved", "training data if later approved"),
        expected_outputs=("private model reports or probability-score artifacts if later approved",),
        required_reference_artifacts=(
            "frozen notebook model-cell outputs",
            "model weight and training-data availability evidence",
            "broken-cell and dependency status inventory",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="experimental_private",
        classification="private deep-learning model cell inventory",
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
        implementation_status="implementation_deferred",
        blocker="Model weights, training data, dependency policy, and runnable-cell status are not locked.",
        recommended_next_action="Defer model implementation until source, references, and dependency policy are approved in a later phase.",
        notes="Phase 7 does not train models, run inference, download pretrained weights, or add ML dependencies.",
    ),
    ClassifierModelInventoryItem(
        id="phase7_classifier_inputs_outputs",
        category="classifier_inputs_outputs",
        notebook_artifact_or_pattern=(
            "classifier input tensors, object rows, cluster rows, probability or score reports"
        ),
        current_app_artifact_or_pattern=(
            "hypercube.npy | pca_anomaly.tif | objects_index.csv | clusters_summary.csv | "
            "experimental/classifications.csv | experimental/summary.json | "
            "experimental/neutral_target_labels.json"
        ),
        source_status="existing_app_equivalent_found",
        current_app_status=(
            "Existing CLI validates core artifacts and writes local neutral outputs, but no frozen notebook classifier parity comparison exists."
        ),
        parity_status="verifier_needed",
        expected_inputs=("hypercube", "PCA anomaly", "object table", "cluster table"),
        expected_outputs=(
            "experimental/classifications.csv",
            "experimental/summary.json",
            "experimental/neutral_target_labels.json",
        ),
        required_reference_artifacts=(
            "frozen notebook classifier output bundle",
            "expected neutral or private mapping schema",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="experimental_private",
        classification="private classifier input/output inventory",
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
        implementation_status="requires_verifier_contract",
        blocker="No Phase 7 verifier compares local neutral classifier outputs against frozen notebook references.",
        recommended_next_action="Create a private classifier verifier only after frozen references and expected schemas are locked.",
        notes="Runtime output presence and notebook-value parity remain separate.",
    ),
    ClassifierModelInventoryItem(
        id="phase7_public_exposure_boundary",
        category="public_exposure_boundary",
        notebook_artifact_or_pattern=(
            "Classifier and model outputs are private notebook-parity artifacts by default"
        ),
        current_app_artifact_or_pattern=(
            "No API routes, frontend controls, BackgroundTasks hooks, or core orchestrator hooks for experimental classifier"
        ),
        source_status="exact_source_found",
        current_app_status=(
            "Project policy and experimental module rules keep classifier outputs filesystem-only and local."
        ),
        parity_status="covered_by_existing_contract",
        expected_inputs=("artifact class", "redaction policy", "experimental module boundary"),
        expected_outputs=("private inventory report only",),
        required_reference_artifacts=("redaction and experimental-boundary documentation",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="experimental_private",
        classification="private classifier public exposure boundary inventory",
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
        implementation_status="no_action_needed_existing_contract",
        blocker="",
        recommended_next_action="Keep classifier/model artifacts private unless a later user-approved phase changes policy.",
        notes="Phase 7 documents the boundary only; it does not change API, frontend, database, or artifact-serving code.",
    ),
)


def get_phase_7_classifier_model_inventory() -> tuple[
    ClassifierModelInventoryItem,
    ...
]:
    """Return the Phase 7 classifier/model parity inventory."""

    return _INVENTORY


def write_phase_7_classifier_model_inventory_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[ClassifierModelInventoryItem] | None = None,
    report_relative_path: str | Path = PHASE_7_CLASSIFIER_MODEL_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local Phase 7 inventory report without creating model artifacts."""

    report_items = tuple(items or _INVENTORY)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": PHASE_7_CLASSIFIER_MODEL_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_category": _counts_by("category", report_items),
        "counts_by_parity_status": _counts_by("parity_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "counts_by_artifact_class": _counts_by("artifact_class", report_items),
        "phase_7_runtime_changes": False,
        "public_exposure_changes": False,
        "notes": (
            "Phase 7 is inventory, private classifier/model contract, safety-boundary, "
            "and verification-planning only. It does not train models, run inference, "
            "change artifact serving, or claim notebook-value parity."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[ClassifierModelInventoryItem],
) -> dict[str, int]:
    if field_name == "category":
        counts = {value: 0 for value in sorted(ALLOWED_CATEGORIES)}
    elif field_name == "parity_status":
        counts = {value: 0 for value in sorted(ALLOWED_PARITY_STATUSES)}
    elif field_name == "implementation_status":
        counts = {value: 0 for value in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    elif field_name == "artifact_class":
        counts = {value: 0 for value in sorted(ALLOWED_ARTIFACT_CLASSES)}
    else:
        raise ValueError(f"unsupported count field: {field_name}")

    for item in items:
        counts[getattr(item, field_name)] += 1
    return counts
