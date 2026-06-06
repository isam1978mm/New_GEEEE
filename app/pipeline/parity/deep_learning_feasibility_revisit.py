from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.deep_learning_feasibility import (
    RECOMMENDED_FIRST_CANDIDATE_ID,
    get_special_track_h1_deep_learning_feasibility_candidates,
)


FUTURE_SLICE_07_H1_REVISIT_SCHEMA_VERSION = "future_slice_07_h1_revisit_after_i1_j1_v1"
FUTURE_SLICE_07_H1_REVISIT_REPORT_RELATIVE_PATH = (
    "manifests/future_slice_07_h1_revisit_after_i1_j1.json"
)
FUTURE_SLICE_07_REVISIT_ID = "future_slice_07_h1_revisit_after_i1_j1"

# The recommended first future ML path is unchanged after the I1 dataset gates and
# the J1 Tesla-flow decomposition: a private probability classifier over verified
# feature summaries.
REVISITED_RECOMMENDED_FIRST_CANDIDATE_ID = RECOMMENDED_FIRST_CANDIDATE_ID
RECOMMENDED_NEXT_ML_DATA_SLICE = "I2 — create private dataset pack outside git"

PHASE_F_BASELINE_TO_BEAT = "Phase F private neutral probability CLI classifier baseline"

# Gate references carried into the revisit report. These name the binding gates from
# the I1 dataset design and the J1 Tesla-flow decomposition. They do not weaken any
# gate; they only record which gate each candidate is measured against.
I1_INDEPENDENT_EVIDENCE_GATE = (
    "I1 independent evidence gate: reviewed_independent or reviewed_adjudicated labels "
    "require a nonblank label_evidence_source from independent evidence; notebook and "
    "heuristic outputs are weak signals only."
)
I1_DATASET_MANIFEST_HASH_GATE = (
    "I1 dataset manifest gate: dataset_id, dataset_manifest_hash, and dataset_content_hash "
    "are required, with storage outside git as LOCAL_SENSITIVE or FILESYSTEM_ONLY."
)
I1_HOLDOUT_AND_BASELINE_MARGIN_GATE = (
    "I1 holdout and baseline-margin gate: a numeric minimum holdout size and a "
    "preregistered baseline margin over the Phase F baseline on an untouched holdout "
    "are required before training is considered."
)
J1_DECOMPOSITION_GATE = (
    "J1 decomposition gate: the Tesla-style flow is decomposed into mapped substeps; "
    "ml_model_attempt substeps remain blocked by the H/I data gates and any custom model "
    "path stays blocked until a later J2 or source-lock slice isolates a small safe step."
)

ALLOWED_REVISITED_STATUSES = {
    "still_best_first_candidate",
    "feasible_later_after_i2",
    "blocked_missing_independent_evidence",
    "blocked_missing_dataset_pack",
    "blocked_missing_holdout_policy_values",
    "blocked_missing_weights_policy",
    "blocked_dependency_policy",
    "blocked_until_j2_or_later_source_lock",
    "blocked_public_exposure",
    "research_only",
    "not_recommended",
}


@dataclass(frozen=True)
class H1RevisitCandidate:
    id: str
    candidate_name: str
    candidate_type: str
    original_h1_status: str
    revisited_status: str
    status_change_reason: str
    i1_dataset_gate_status: str
    j1_decomposition_gate_status: str
    independent_evidence_status: str
    dataset_pack_status: str
    holdout_policy_status: str
    baseline_policy_status: str
    weights_policy_status: str
    dependency_policy_status: str
    phase_c_e_feature_support_status: str
    phase_d_e_map_artifact_support_status: str
    recommended_next_action: str
    can_train_now: bool
    can_infer_now: bool
    can_download_weights_now: bool
    can_add_ml_dependencies_now: bool
    can_expose_api_frontend_now: bool
    blocker: str
    notes: str

    def __post_init__(self) -> None:
        if self.revisited_status not in ALLOWED_REVISITED_STATUSES:
            raise ValueError(f"unsupported revisited_status: {self.revisited_status}")
        if self.can_train_now:
            raise ValueError("H1 revisit is design only and does not allow training")
        if self.can_infer_now:
            raise ValueError("H1 revisit is design only and does not allow inference")
        if self.can_download_weights_now:
            raise ValueError("H1 revisit does not allow weight retrieval")
        if self.can_add_ml_dependencies_now:
            raise ValueError("H1 revisit does not allow adding ML dependencies")
        if self.can_expose_api_frontend_now:
            raise ValueError("H1 revisit does not allow API/frontend exposure")
        if not self.status_change_reason:
            raise ValueError("H1 revisit candidates require a status_change_reason")
        if not self.recommended_next_action:
            raise ValueError("H1 revisit candidates require a recommended_next_action")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def get_h1_revisit_recommended_first_candidate() -> str:
    return REVISITED_RECOMMENDED_FIRST_CANDIDATE_ID


def get_h1_revisit_recommended_next_ml_data_slice() -> str:
    return RECOMMENDED_NEXT_ML_DATA_SLICE


def get_h1_revisit_gate_references() -> dict[str, str]:
    return {
        "i1_independent_evidence_gate": I1_INDEPENDENT_EVIDENCE_GATE,
        "i1_dataset_manifest_hash_gate": I1_DATASET_MANIFEST_HASH_GATE,
        "i1_holdout_and_baseline_margin_gate": I1_HOLDOUT_AND_BASELINE_MARGIN_GATE,
        "j1_decomposition_gate": J1_DECOMPOSITION_GATE,
        "phase_f_baseline_to_beat": PHASE_F_BASELINE_TO_BEAT,
    }


def get_h1_revisit_candidates() -> tuple[H1RevisitCandidate, ...]:
    return _REVISIT_CANDIDATES


def write_future_slice_07_h1_revisit_report(
    *,
    run_dir: str | Path,
    run_id: str,
    candidates: Iterable[H1RevisitCandidate] | None = None,
    report_relative_path: str | Path = FUTURE_SLICE_07_H1_REVISIT_REPORT_RELATIVE_PATH,
) -> Path:
    """Write the private Future Slice 07 H1 revisit report under ``run_dir``.

    This is an H1 revisit / design report only. It does not train, run inference,
    download weights, add ML dependencies, create datasets, generate artifacts,
    call Earth Engine, or expose model outputs through API or frontend.
    """

    report_candidates = tuple(candidates or _REVISIT_CANDIDATES)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": FUTURE_SLICE_07_H1_REVISIT_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "revisit_id": FUTURE_SLICE_07_REVISIT_ID,
        "candidates": [candidate.to_dict() for candidate in report_candidates],
        "recommended_first_candidate": REVISITED_RECOMMENDED_FIRST_CANDIDATE_ID,
        "recommended_next_ml_data_slice": RECOMMENDED_NEXT_ML_DATA_SLICE,
        "gate_references": get_h1_revisit_gate_references(),
        "baseline_to_beat": PHASE_F_BASELINE_TO_BEAT,
        "counts_by_revisited_status": _counts_by_revisited_status(report_candidates),
        "h1_revisit_only": True,
        "training_added": False,
        "inference_added": False,
        "weights_downloaded": False,
        "ml_dependencies_added": False,
        "dataset_created": False,
        "public_exposure_changes": False,
        "artifact_generation": False,
        "notes": (
            "Future Slice 07 revisits the H1 deep-learning feasibility ranking using the "
            "I1 dataset gates and the J1 Tesla-flow decomposition. The recommended first "
            "future model remains a private feature-summary probability classifier. I2 "
            "remains required before training can be considered. The report is private "
            "design metadata only and changes no runtime ML behavior."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _revisit_candidate(
    *,
    id: str,
    candidate_name: str,
    candidate_type: str,
    original_h1_status: str,
    revisited_status: str,
    status_change_reason: str,
    i1_dataset_gate_status: str,
    j1_decomposition_gate_status: str,
    independent_evidence_status: str,
    dataset_pack_status: str,
    holdout_policy_status: str,
    weights_policy_status: str,
    phase_c_e_feature_support_status: str,
    phase_d_e_map_artifact_support_status: str,
    recommended_next_action: str,
    blocker: str,
    notes: str,
    baseline_policy_status: str = "phase_f_baseline_to_beat_defined",
    dependency_policy_status: str = "lightweight_base_app_no_heavy_ml_required",
) -> H1RevisitCandidate:
    return H1RevisitCandidate(
        id=id,
        candidate_name=candidate_name,
        candidate_type=candidate_type,
        original_h1_status=original_h1_status,
        revisited_status=revisited_status,
        status_change_reason=status_change_reason,
        i1_dataset_gate_status=i1_dataset_gate_status,
        j1_decomposition_gate_status=j1_decomposition_gate_status,
        independent_evidence_status=independent_evidence_status,
        dataset_pack_status=dataset_pack_status,
        holdout_policy_status=holdout_policy_status,
        baseline_policy_status=baseline_policy_status,
        weights_policy_status=weights_policy_status,
        dependency_policy_status=dependency_policy_status,
        phase_c_e_feature_support_status=phase_c_e_feature_support_status,
        phase_d_e_map_artifact_support_status=phase_d_e_map_artifact_support_status,
        recommended_next_action=recommended_next_action,
        can_train_now=False,
        can_infer_now=False,
        can_download_weights_now=False,
        can_add_ml_dependencies_now=False,
        can_expose_api_frontend_now=False,
        blocker=blocker,
        notes=notes,
    )


_REVISIT_CANDIDATES: tuple[H1RevisitCandidate, ...] = (
    _revisit_candidate(
        id="h1_private_feature_summary_probability_classifier",
        candidate_name="Private probability classifier over verified feature summaries",
        candidate_type="private_tabular_feature_summary_probability_classifier",
        original_h1_status="best_first_candidate",
        revisited_status="still_best_first_candidate",
        status_change_reason=(
            "The I1 dataset gates and the J1 decomposition do not displace this path. The "
            "Phase C semantic feature writer with its Phase E3 comparator and the Phase D "
            "private map writers with the Phase E4 comparator now provide verified, "
            "parity-checked private feature inputs, which strengthens this tabular path "
            "relative to image-model paths. It stays the safest first future ML path."
        ),
        i1_dataset_gate_status="schema_defined_dataset_pack_pending_i2",
        j1_decomposition_gate_status="mapped_to_h_i_gates_no_monolithic_runtime",
        independent_evidence_status="policy_defined_evidence_not_yet_available",
        dataset_pack_status="not_created_blocked_until_i2",
        holdout_policy_status="policy_defined_numeric_values_pending_i2",
        weights_policy_status="not_required_for_this_candidate",
        phase_c_e_feature_support_status=(
            "available: Phase C writer plus Phase E3 comparator supply verified tabular "
            "feature summaries"
        ),
        phase_d_e_map_artifact_support_status=(
            "available_as_private_parity_context_only: Phase D writers plus Phase E4 "
            "comparator verify private map artifacts but are not a training-label source"
        ),
        recommended_next_action=(
            "Carry this candidate into I2 as the first dataset pack target; keep the Phase F "
            "classifier as the baseline to beat. Do not train until the I1 dataset gates pass."
        ),
        blocker=(
            "No I2 dataset pack with independent evidence-backed labels, dataset manifest "
            "hashes, and a numeric holdout/baseline margin exists yet."
        ),
        notes=(
            "Lowest dependency risk, easiest to validate against the Phase F baseline and "
            "Phase E references; does not require chips, masks, boxes, or model weights."
        ),
    ),
    _revisit_candidate(
        id="h1_cnn_fixed_raster_chips",
        candidate_name="CNN over fixed raster chips",
        candidate_type="cnn_fixed_raster_chips",
        original_h1_status="blocked_missing_dataset",
        revisited_status="blocked_missing_dataset_pack",
        status_change_reason=(
            "I1 defined the chip and split schema, but no I2 dataset pack with reviewed "
            "chip labels exists. The Phase C/E and Phase D/E slices provide tabular feature "
            "and map-artifact parity, not chip-level labeled training data."
        ),
        i1_dataset_gate_status="schema_defined_chip_dataset_pack_missing",
        j1_decomposition_gate_status="mapped_to_h_i_gates",
        independent_evidence_status="blocked_no_independent_chip_labels",
        dataset_pack_status="not_created_blocked_until_i2",
        holdout_policy_status="policy_defined_numeric_values_pending_i2",
        weights_policy_status="not_applicable_until_dataset_pack_exists",
        phase_c_e_feature_support_status="insufficient_for_chip_targets_tabular_only",
        phase_d_e_map_artifact_support_status="not_a_training_label_source",
        recommended_next_action=(
            "Defer until I2 demonstrates enough independent chip labels and a leakage-safe "
            "split with a numeric holdout."
        ),
        blocker="No I2 chip dataset pack with independent labels and split manifest exists.",
        notes="A chip model needs stronger data controls than the feature-summary path.",
    ),
    _revisit_candidate(
        id="h1_segmentation_labeled_masks",
        candidate_name="Segmentation model over labeled masks",
        candidate_type="segmentation_labeled_masks",
        original_h1_status="blocked_missing_dataset",
        revisited_status="blocked_missing_dataset_pack",
        status_change_reason=(
            "I1 defined dataset and label QA policy, but no I2 labeled-mask dataset pack "
            "with independent evidence and mask QA exists. Phase C/E and Phase D/E do not "
            "supply pixel-aligned mask labels."
        ),
        i1_dataset_gate_status="schema_defined_mask_dataset_pack_missing",
        j1_decomposition_gate_status="mapped_to_h_i_gates",
        independent_evidence_status="blocked_no_independent_mask_labels",
        dataset_pack_status="not_created_blocked_until_i2",
        holdout_policy_status="policy_defined_numeric_values_pending_i2",
        weights_policy_status="blocked_missing_weights_policy_inputs",
        phase_c_e_feature_support_status="insufficient_for_mask_targets",
        phase_d_e_map_artifact_support_status="not_a_training_label_source",
        recommended_next_action=(
            "Let I2 decide whether independently labeled masks and mask QA are realistic "
            "before any segmentation work."
        ),
        blocker="No independently labeled mask dataset pack or mask QA record exists.",
        notes="Segmentation remains a later, data-heavy path and not a first candidate.",
    ),
    _revisit_candidate(
        id="h1_object_detector_boxes_regions",
        candidate_name="Object detector over boxes or regions",
        candidate_type="object_detector_boxes_regions",
        original_h1_status="blocked_missing_dataset",
        revisited_status="blocked_missing_dataset_pack",
        status_change_reason=(
            "I1 defined the label schema, but no I2 dataset pack with independent box or "
            "region labels exists. Phase C/E and Phase D/E do not supply detection labels."
        ),
        i1_dataset_gate_status="schema_defined_box_dataset_pack_missing",
        j1_decomposition_gate_status="mapped_to_h_i_gates",
        independent_evidence_status="blocked_no_independent_box_or_region_labels",
        dataset_pack_status="not_created_blocked_until_i2",
        holdout_policy_status="policy_defined_numeric_values_pending_i2",
        weights_policy_status="blocked_missing_weights_policy_inputs",
        phase_c_e_feature_support_status="insufficient_for_detection_targets",
        phase_d_e_map_artifact_support_status="not_a_training_label_source",
        recommended_next_action=(
            "Defer object detection until I2 defines a box/region label schema and the "
            "required independently supported data volume."
        ),
        blocker="No I2 box or region annotation dataset pack with independent evidence exists.",
        notes="Detector paths require more annotation work than feature summaries.",
    ),
    _revisit_candidate(
        id="h1_pretrained_external_weight_inference",
        candidate_name="Pretrained or external-weight inference candidate",
        candidate_type="pretrained_external_weight_inference_candidate",
        original_h1_status="blocked_missing_weights",
        revisited_status="blocked_missing_weights_policy",
        status_change_reason=(
            "I1 and J1 do not relax the weights policy. Approved weights still require an "
            "approved source, license, version pin, sha256, storage outside git, and a "
            "labeled holdout validation with independent evidence and a baseline comparison."
        ),
        i1_dataset_gate_status="holdout_and_baseline_required_dataset_pack_missing",
        j1_decomposition_gate_status="mapped_to_h_i_gates",
        independent_evidence_status="blocked_no_labeled_holdout_with_independent_evidence",
        dataset_pack_status="not_created_blocked_until_i2",
        holdout_policy_status="labeled_holdout_validation_required_not_available",
        weights_policy_status=(
            "blocked: source, license, version, sha256, storage, and model card are not "
            "accepted; approved weights do not bypass labeled holdout validation"
        ),
        phase_c_e_feature_support_status="not_a_weights_or_holdout_source",
        phase_d_e_map_artifact_support_status="not_a_weights_or_holdout_source",
        recommended_next_action=(
            "Do not retrieve or use external weights until the weights policy inputs and the "
            "I1 labeled-holdout and baseline-margin gates are satisfied."
        ),
        blocker=(
            "Weight source, license, version, hash, storage, and labeled holdout validation "
            "are missing; zero-validation inference stays blocked."
        ),
        notes="Approved weights still need an independent labeled holdout and a baseline comparison.",
    ),
    _revisit_candidate(
        id="h1_notebook_custom_tesla_style_model_attempt",
        candidate_name="Notebook custom/Tesla-style model attempt",
        candidate_type="notebook_custom_tesla_style_model_attempt",
        original_h1_status="blocked_until_j1_decomposition",
        revisited_status="blocked_until_j2_or_later_source_lock",
        status_change_reason=(
            "J1 has decomposed the Tesla-style flow and mapped ml_model_attempt substeps to "
            "the H/I gates, but the full flow must not be ported as one engine. Any custom "
            "model path stays blocked until a later J2 or source-lock slice isolates a small, "
            "evidence-backed step."
        ),
        i1_dataset_gate_status="dataset_pack_missing_blocked_until_i2",
        j1_decomposition_gate_status=(
            "decomposed: monolithic Tesla runtime blocked; small safe slice not yet "
            "source-locked"
        ),
        independent_evidence_status="blocked_no_independent_labels",
        dataset_pack_status="not_created_blocked_until_i2",
        holdout_policy_status="policy_defined_numeric_values_pending_i2",
        weights_policy_status="blocked_missing_weights_policy_inputs",
        phase_c_e_feature_support_status="partial_feature_inputs_only_not_a_model_path",
        phase_d_e_map_artifact_support_status="private_parity_context_only",
        recommended_next_action=(
            "Defer until a later J2 or source-lock slice isolates one small, source-driven "
            "substep, then route it through the I2 and H gates."
        ),
        blocker=(
            "No source-locked small Tesla substep and no I2 dataset pack exist; the flow "
            "must not be ported as a monolithic engine."
        ),
        notes="The revisit must not copy the Tesla flow as a single unreviewed app engine.",
    ),
    _revisit_candidate(
        id="h1_research_only_or_blocked_candidates",
        candidate_name="Research-only or blocked candidates",
        candidate_type="research_only_or_blocked",
        original_h1_status="research_only",
        revisited_status="research_only",
        status_change_reason=(
            "I1 and J1 do not turn broken, duplicate, dependency-heavy, or "
            "coordinate-exposure-adjacent attempts into implementation candidates. They "
            "remain research inventory only."
        ),
        i1_dataset_gate_status="not_applicable_research_inventory",
        j1_decomposition_gate_status="mapped_to_duplicate_or_unsupported_categories",
        independent_evidence_status="not_applicable_until_a_candidate_is_split_out",
        dataset_pack_status="not_applicable",
        holdout_policy_status="not_applicable",
        weights_policy_status="not_applicable",
        phase_c_e_feature_support_status="not_applicable",
        phase_d_e_map_artifact_support_status="not_applicable",
        recommended_next_action=(
            "Keep as research inventory unless I2 or a later source-lock slice creates a "
            "narrower approved design."
        ),
        blocker="These paths are not candidates for near-term implementation.",
        notes="This bucket keeps unclear notebook attempts out of runtime behavior by default.",
    ),
)


def _counts_by_revisited_status(
    candidates: Iterable[H1RevisitCandidate],
) -> dict[str, int]:
    counts = {status: 0 for status in sorted(ALLOWED_REVISITED_STATUSES)}
    for candidate in candidates:
        counts[candidate.revisited_status] += 1
    return counts
