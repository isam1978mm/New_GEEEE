from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


SPECIAL_TRACK_H1_SCHEMA_VERSION = "special_track_h1_deep_learning_feasibility_v1"
SPECIAL_TRACK_H1_REPORT_RELATIVE_PATH = (
    "manifests/special_track_h1_deep_learning_feasibility.json"
)

ALLOWED_CANDIDATE_TYPES = {
    "private_tabular_feature_summary_probability_classifier",
    "cnn_fixed_raster_chips",
    "segmentation_labeled_masks",
    "object_detector_boxes_regions",
    "pretrained_external_weight_inference_candidate",
    "notebook_custom_tesla_style_model_attempt",
    "research_only_or_blocked",
}

ALLOWED_FEASIBILITY_STATUSES = {
    "feasible_later_after_i1",
    "best_first_candidate",
    "blocked_missing_independent_labels",
    "blocked_missing_dataset",
    "blocked_missing_weights",
    "blocked_dependency_risk",
    "research_only",
    "duplicate_or_unclear",
    "blocked_until_j1_decomposition",
    "not_recommended",
}

RECOMMENDED_FIRST_CANDIDATE_ID = "h1_private_feature_summary_probability_classifier"

_TRACEABILITY_FIELDS = (
    "dataset_id",
    "dataset_manifest_hash",
    "dataset_content_hash",
    "model_id",
    "model_version",
    "weights_hash_if_weights_used",
    "evaluation_summary",
)

_COMMON_INDEPENDENT_EVIDENCE = (
    "reviewed-tier labels require label_evidence_source",
    "notebook and heuristic outputs may be weak signals but not sole labels",
    "independent support such as field validation, authoritative external data, or expert adjudication is required",
)

_COMMON_MINIMUM_DATASET_REQUIREMENTS = (
    "I1 must define one training example and one neutral label",
    "dataset manifest is required",
    "dataset_id is required",
    "dataset_manifest_hash is required",
    "dataset_content_hash is required",
    "class prevalence and base rate must be recorded by split",
    "negative and hard-negative sampling must be documented",
    "storage must be LOCAL_SENSITIVE or FILESYSTEM_ONLY outside git",
)

_COMMON_MINIMUM_HOLDOUT_REQUIREMENTS = (
    "untouched labeled holdout with independent evidence is required",
    "I1 must set quantitative minimum holdout size",
    "holdout must record class prevalence and label evidence source counts",
    "holdout is not used for threshold, feature, model, calibration, or hyperparameter choices",
)

_COMMON_BASELINE_TO_BEAT = "Phase F private neutral probability CLI classifier baseline"

_COMMON_BASELINE_MARGIN_POLICY = (
    "Future ML must beat the Phase F baseline on untouched holdout by an I1-preregistered margin; "
    "the margin must clear holdout noise using confidence intervals or paired bootstrap-style evidence."
)

_COMMON_LEAKAGE_CONTROLS = (
    "geographic split guard",
    "group split guard by area_id or stronger group_id",
    "temporal split guard",
    "near-duplicate chip isolation",
    "final holdout protection",
)

_COMMON_DEPENDENCY_POLICY = (
    "base app must not require PyTorch, TensorFlow, CUDA, or heavy ML packages",
    "optional ML dependency group may be considered only in a later approved slice",
    "normal app startup must remain free of heavy ML imports",
)

_COMMON_EVALUATION_METRICS = (
    "preregistered primary metric",
    "PR-AUC",
    "recall at fixed precision",
    "calibration and Brier score for probability outputs",
    "precision",
    "recall",
    "F1",
    "class prevalence or base rate in every metric table",
    "confidence intervals or bootstrap uncertainty when feasible",
)

_COMMON_THRESHOLD_POLICY = (
    "thresholds selected on train and validation only",
    "final holdout is never used for threshold selection",
    "threshold choice must be recorded before final holdout evaluation",
)

_COMMON_PRIVACY_BOUNDARY = (
    "private CLI and filesystem-only first; no public overlay, public DTO, or serving change",
    "coordinate-bearing metadata remains redacted from public summaries",
    "public exposure requires intended-use, acceptable-use, misuse, redaction, access-control, audit, and serving review",
)


@dataclass(frozen=True)
class DeepLearningFeasibilityCandidate:
    id: str
    candidate_name: str
    candidate_type: str
    notebook_evidence: str
    input_data_required: tuple[str, ...]
    label_data_required: tuple[str, ...]
    independent_evidence_required: tuple[str, ...]
    minimum_dataset_requirements: tuple[str, ...]
    minimum_holdout_requirements: tuple[str, ...]
    baseline_to_beat: str
    baseline_margin_policy: str
    leakage_controls_required: tuple[str, ...]
    weights_required: bool
    weights_policy: tuple[str, ...]
    dependency_policy: tuple[str, ...]
    evaluation_metrics: tuple[str, ...]
    threshold_policy: tuple[str, ...]
    output_boundary: str
    privacy_boundary: tuple[str, ...]
    feasibility_status: str
    blocker: str
    recommended_next_action: str
    feeds_i1_requirements: bool
    revisit_after_i1: bool
    notes: str
    training_allowed_now: bool
    inference_allowed_now: bool
    zero_validation_inference_allowed: bool
    api_frontend_integration_allowed_now: bool
    output_traceability_required: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.candidate_type not in ALLOWED_CANDIDATE_TYPES:
            raise ValueError(f"unsupported candidate_type: {self.candidate_type}")
        if self.feasibility_status not in ALLOWED_FEASIBILITY_STATUSES:
            raise ValueError(
                f"unsupported feasibility_status: {self.feasibility_status}"
            )
        if not self.independent_evidence_required:
            raise ValueError("H1 candidates require independent evidence policy")
        if not self.baseline_to_beat:
            raise ValueError("H1 candidates require a baseline")
        if not self.baseline_margin_policy:
            raise ValueError("H1 candidates require a baseline margin policy")
        if not self.leakage_controls_required:
            raise ValueError("H1 candidates require leakage controls")
        if not self.weights_policy:
            raise ValueError("H1 candidates require a weights policy")
        if not self.dependency_policy:
            raise ValueError("H1 candidates require a dependency policy")
        if self.training_allowed_now:
            raise ValueError("H1 is design only and does not allow training")
        if self.inference_allowed_now:
            raise ValueError("H1 is design only and does not allow inference")
        if self.zero_validation_inference_allowed:
            raise ValueError("H1 does not allow zero-validation inference")
        if self.api_frontend_integration_allowed_now:
            raise ValueError("H1 does not allow app public integration now")
        required_traceability = {
            "dataset_id",
            "dataset_manifest_hash",
            "dataset_content_hash",
        }
        if not required_traceability <= set(self.output_traceability_required):
            raise ValueError("H1 output traceability requires dataset identity hashes")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def get_special_track_h1_recommended_first_candidate() -> str:
    return RECOMMENDED_FIRST_CANDIDATE_ID


def get_special_track_h1_deep_learning_feasibility_candidates() -> tuple[
    DeepLearningFeasibilityCandidate,
    ...
]:
    return _CANDIDATES


def write_special_track_h1_deep_learning_feasibility_report(
    *,
    run_dir: str | Path,
    run_id: str,
    candidates: Iterable[DeepLearningFeasibilityCandidate] | None = None,
    report_relative_path: str | Path = SPECIAL_TRACK_H1_REPORT_RELATIVE_PATH,
) -> Path:
    report_candidates = tuple(candidates or _CANDIDATES)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": SPECIAL_TRACK_H1_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "candidates": [candidate.to_dict() for candidate in report_candidates],
        "recommended_first_candidate": RECOMMENDED_FIRST_CANDIDATE_ID,
        "counts_by_feasibility_status": _counts_by_feasibility_status(
            report_candidates
        ),
        "h1_design_only": True,
        "training_added": False,
        "inference_added": False,
        "weights_downloaded": False,
        "ml_dependencies_added": False,
        "api_frontend_integration_added": False,
        "public_exposure_changes": False,
        "artifact_generation": False,
        "notes": (
            "Special Track H1 is feasibility and ranking only. It records candidate "
            "model paths, data gates, weights policy, dependency policy, evaluation "
            "policy, and private boundaries without runtime ML behavior."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _weights_policy(*, weights_required: bool) -> tuple[str, ...]:
    base = (
        "source, license, version, sha256, storage class, reproducibility notes, and model card are required before any weight use",
        "random or unpinned external retrieval is blocked",
        "approved weights do not bypass holdout validation",
        "labeled holdout validation with independent evidence is required before private inference",
    )
    if not weights_required:
        return (
            "no model weights required for the first feature-summary candidate",
            *base,
        )
    return base


def _candidate(
    *,
    id: str,
    candidate_name: str,
    candidate_type: str,
    notebook_evidence: str,
    input_data_required: tuple[str, ...],
    label_data_required: tuple[str, ...],
    feasibility_status: str,
    blocker: str,
    recommended_next_action: str,
    notes: str,
    weights_required: bool = False,
    extra_metrics: tuple[str, ...] = (),
) -> DeepLearningFeasibilityCandidate:
    return DeepLearningFeasibilityCandidate(
        id=id,
        candidate_name=candidate_name,
        candidate_type=candidate_type,
        notebook_evidence=notebook_evidence,
        input_data_required=input_data_required,
        label_data_required=label_data_required,
        independent_evidence_required=_COMMON_INDEPENDENT_EVIDENCE,
        minimum_dataset_requirements=_COMMON_MINIMUM_DATASET_REQUIREMENTS,
        minimum_holdout_requirements=_COMMON_MINIMUM_HOLDOUT_REQUIREMENTS,
        baseline_to_beat=_COMMON_BASELINE_TO_BEAT,
        baseline_margin_policy=_COMMON_BASELINE_MARGIN_POLICY,
        leakage_controls_required=_COMMON_LEAKAGE_CONTROLS,
        weights_required=weights_required,
        weights_policy=_weights_policy(weights_required=weights_required),
        dependency_policy=_COMMON_DEPENDENCY_POLICY,
        evaluation_metrics=(*_COMMON_EVALUATION_METRICS, *extra_metrics),
        threshold_policy=_COMMON_THRESHOLD_POLICY,
        output_boundary="Private CLI filesystem report only; public HTTP and UI surfaces are blocked.",
        privacy_boundary=_COMMON_PRIVACY_BOUNDARY,
        feasibility_status=feasibility_status,
        blocker=blocker,
        recommended_next_action=recommended_next_action,
        feeds_i1_requirements=True,
        revisit_after_i1=True,
        notes=notes,
        training_allowed_now=False,
        inference_allowed_now=False,
        zero_validation_inference_allowed=False,
        api_frontend_integration_allowed_now=False,
        output_traceability_required=_TRACEABILITY_FIELDS,
    )


_CANDIDATES: tuple[DeepLearningFeasibilityCandidate, ...] = (
    _candidate(
        id="h1_private_feature_summary_probability_classifier",
        candidate_name="Private probability classifier over verified feature summaries",
        candidate_type="private_tabular_feature_summary_probability_classifier",
        notebook_evidence=(
            "Phase F already writes a private neutral score report. Notebook training "
            "and classifier cells suggest tabular summaries, score rows, object tables, "
            "and feature means can be candidates for a later probability model."
        ),
        input_data_required=(
            "verified Phase C semantic feature summaries",
            "SAR, DEM, thermal, optical, PCA, and object-summary features",
            "grid and acquisition metadata",
            "Phase F neutral score rows for baseline comparison",
        ),
        label_data_required=(
            "neutral Class_A/Class_B/Class_C style labels",
            "reviewed_independent or reviewed_adjudicated label quality",
            "negative and hard-negative examples",
        ),
        feasibility_status="best_first_candidate",
        blocker="I1 has not yet defined the dataset schema, label source policy, holdout size, or baseline margin.",
        recommended_next_action="Feed this candidate into I1 as the safest first future ML path.",
        notes=(
            "Lowest dependency risk and easiest comparison against the Phase F baseline; "
            "does not require masks, boxes, or image-model weights."
        ),
    ),
    _candidate(
        id="h1_cnn_fixed_raster_chips",
        candidate_name="CNN over fixed raster chips",
        candidate_type="cnn_fixed_raster_chips",
        notebook_evidence=(
            "Notebook cell summaries reference fixed chip tensors, RGB-like stacks, "
            "and CNN-style model attempts over local raster chips."
        ),
        input_data_required=(
            "versioned raster chips with fixed band order",
            "chip-level preprocessing commit and sensor window",
            "private chip metadata with redaction rules",
        ),
        label_data_required=(
            "chip-level neutral labels with independent evidence",
            "negative and hard-negative chip examples",
            "grouped chip families to avoid leakage",
        ),
        feasibility_status="blocked_missing_dataset",
        blocker="I1 has not defined chip schema, chip label sources, holdout size, or split policy.",
        recommended_next_action="Defer CNN chips until I1 proves enough independent chip labels exist.",
        notes="A chip model needs stronger data controls than the feature-summary path.",
        extra_metrics=("top-k precision", "ranking stability"),
    ),
    _candidate(
        id="h1_segmentation_labeled_masks",
        candidate_name="Segmentation model over labeled masks",
        candidate_type="segmentation_labeled_masks",
        notebook_evidence=(
            "Notebook summaries reference segmentation-style model attempts and mask-like "
            "outputs, but no app-approved labeled-mask dataset exists."
        ),
        input_data_required=(
            "fixed raster chips",
            "pixel-aligned labeled masks",
            "mask QA and class prevalence by split",
        ),
        label_data_required=(
            "pixel or polygon masks with independent evidence",
            "reviewer disagreement policy",
            "negative/background masks",
        ),
        feasibility_status="blocked_missing_dataset",
        blocker="No independently labeled mask dataset or mask QA policy is defined.",
        recommended_next_action="Let I1 decide whether mask labels are realistic before any segmentation work.",
        notes="Segmentation is not a first implementation candidate.",
        weights_required=True,
        extra_metrics=("IoU", "Dice score", "false positive analysis", "false negative analysis"),
    ),
    _candidate(
        id="h1_object_detector_boxes_regions",
        candidate_name="Object detector over boxes or regions",
        candidate_type="object_detector_boxes_regions",
        notebook_evidence=(
            "Notebook summaries reference detector-style cells and region outputs, but "
            "box or region labels are not defined as independent training data."
        ),
        input_data_required=(
            "chip imagery or feature rasters",
            "box or region annotation schema",
            "object table linkage",
        ),
        label_data_required=(
            "box or region labels with independent evidence",
            "negative regions and near-miss examples",
            "per-area group identifiers",
        ),
        feasibility_status="blocked_missing_dataset",
        blocker="No independent box or region annotation dataset exists.",
        recommended_next_action="Defer object detection until I1 defines label schema and data volume.",
        notes="Detector paths require more annotation work than feature summaries.",
        weights_required=True,
        extra_metrics=("average precision", "recall at fixed precision", "localization error"),
    ),
    _candidate(
        id="h1_pretrained_external_weight_inference",
        candidate_name="Pretrained or external-weight inference candidate",
        candidate_type="pretrained_external_weight_inference_candidate",
        notebook_evidence=(
            "Notebook summaries reference external encoders and image-model attempts, "
            "but reproducible weights, licenses, hashes, and holdout validation are not locked."
        ),
        input_data_required=(
            "model-specific input tensors",
            "weight source traceability record",
            "private evaluation manifest",
        ),
        label_data_required=(
            "labeled holdout with independent evidence",
            "neutral labels and prevalence report",
            "baseline comparison rows",
        ),
        feasibility_status="blocked_missing_weights",
        blocker="Weight source, license, version, hash, storage, and labeled holdout validation are missing.",
        recommended_next_action="Do not use external weights until H1 policy inputs and I1 holdout gates are satisfied.",
        notes="Approved weights still need independent labeled holdout validation.",
        weights_required=True,
    ),
    _candidate(
        id="h1_notebook_custom_tesla_style_model_attempt",
        candidate_name="Notebook custom/Tesla-style model attempt",
        candidate_type="notebook_custom_tesla_style_model_attempt",
        notebook_evidence=(
            "Notebook summaries describe custom multi-step Tesla-style model and map "
            "output attempts mixed with feature, classifier, and overlay behavior."
        ),
        input_data_required=(
            "J1-decomposed feature inputs",
            "private model-step inventory",
            "per-step source and reference evidence",
        ),
        label_data_required=(
            "I1-defined neutral labels",
            "independent evidence for reviewed-tier labels",
            "holdout and baseline comparison data",
        ),
        feasibility_status="blocked_until_j1_decomposition",
        blocker="The Tesla-style flow must be decomposed by J1 before any model path can be evaluated.",
        recommended_next_action="Defer until J1 separates acquisition, feature writers, classifier logic, models, and overlay outputs.",
        notes="H1 must not copy the Tesla flow as a monolithic engine.",
        weights_required=True,
    ),
    _candidate(
        id="h1_research_only_or_blocked_candidates",
        candidate_name="Research-only or blocked candidates",
        candidate_type="research_only_or_blocked",
        notebook_evidence=(
            "Notebook summaries include broken, duplicate, dependency-heavy, and "
            "coordinate-exposure-adjacent model attempts."
        ),
        input_data_required=(
            "case-by-case source review",
            "I1 data gate evidence",
            "J1 decomposition where flow coupling exists",
        ),
        label_data_required=(
            "none until a candidate is split into a later approved design",
        ),
        feasibility_status="research_only",
        blocker="These paths are not candidates for near-term implementation.",
        recommended_next_action="Keep as research inventory unless I1 or J1 creates a narrower approved slice.",
        notes="This bucket prevents unclear notebook attempts from becoming runtime behavior by default.",
    ),
)


def _counts_by_feasibility_status(
    candidates: Iterable[DeepLearningFeasibilityCandidate],
) -> dict[str, int]:
    counts = {status: 0 for status in sorted(ALLOWED_FEASIBILITY_STATUSES)}
    for candidate in candidates:
        counts[candidate.feasibility_status] += 1
    return counts
