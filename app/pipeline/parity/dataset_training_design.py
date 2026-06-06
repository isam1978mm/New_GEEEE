from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from app.pipeline.parity import resolve_run_output_path


SPECIAL_TRACK_I1_SCHEMA_VERSION = "special_track_i1_dataset_training_design_v1"
SPECIAL_TRACK_I1_REPORT_RELATIVE_PATH = (
    "manifests/special_track_i1_dataset_training_design.json"
)

LABEL_QUALITY_VALUES = (
    "reviewed_independent",
    "reviewed_adjudicated",
    "weak_label",
    "synthetic_or_proxy",
    "uncertain",
    "excluded",
)

REVIEWED_TIER_LABEL_QUALITIES = (
    "reviewed_independent",
    "reviewed_adjudicated",
)

EVIDENCE_SOURCE_TYPES = (
    "field_validation",
    "authoritative_external_dataset",
    "expert_adjudication_independent_evidence",
    "independently_produced_reference",
    "weak_heuristic_hint",
    "synthetic_proxy",
    "unknown_or_missing",
)

INDEPENDENT_EVIDENCE_SOURCE_TYPES = (
    "field_validation",
    "authoritative_external_dataset",
    "expert_adjudication_independent_evidence",
    "independently_produced_reference",
)

TRAINING_EXAMPLE_FIELDS = (
    "schema_version",
    "sample_id",
    "dataset_id",
    "area_id",
    "group_id",
    "chip_id",
    "split",
    "label",
    "label_quality",
    "label_evidence_source",
    "evidence_source_type",
    "evidence_source_version",
    "evidence_review_method",
    "reviewer_or_source_reference",
    "acquisition_window",
    "sensor_sources",
    "grid_version",
    "preprocessing_commit",
    "features_ref",
    "metadata_ref",
    "redaction_class",
    "notes",
)

DATASET_MANIFEST_FIELDS = (
    "dataset_id",
    "schema_version",
    "created_at",
    "build_commit",
    "build_command_or_procedure",
    "dataset_manifest_hash",
    "dataset_content_hash",
    "split_seed",
    "split_policy_version",
    "data_source_list",
    "label_source_list",
    "label_evidence_source_counts",
    "label_quality_counts",
    "class_prevalence_by_split",
    "storage_path_outside_git",
    "artifact_class",
    "filesystem_only",
    "http_servable",
    "frontend_visible",
    "downloadable_via_api",
    "redaction_policy",
    "dataset_card_ref",
    "known_limitations",
    "intended_use",
    "unacceptable_use",
    "misuse_review_status",
)

OUTPUT_TRACEABILITY_FIELDS = (
    "dataset_id",
    "dataset_manifest_hash",
    "dataset_content_hash",
    "model_id",
    "model_version",
    "evaluation_summary",
)


@dataclass(frozen=True)
class DatasetTrainingDesign:
    dataset_schema: dict[str, Any]
    training_example_schema: dict[str, Any]
    label_schema: dict[str, Any]
    evidence_source_schema: dict[str, Any]
    label_qa_policy: dict[str, Any]
    split_policy: dict[str, Any]
    leakage_policy: dict[str, Any]
    negative_sampling_policy: dict[str, Any]
    dataset_manifest_schema: dict[str, Any]
    storage_policy: dict[str, Any]
    evaluation_policy: dict[str, Any]
    threshold_policy: dict[str, Any]
    readiness_checklist: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    quantitative_policy: dict[str, Any]
    output_traceability_required: tuple[str, ...]
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def label_record_passes_reviewed_tier_gate(
    *,
    label_quality: str,
    evidence_source_type: str,
    label_evidence_source: str,
) -> bool:
    """Return whether a label is eligible for reviewed-tier ML accounting."""
    if label_quality not in REVIEWED_TIER_LABEL_QUALITIES:
        return False
    if evidence_source_type not in INDEPENDENT_EVIDENCE_SOURCE_TYPES:
        return False
    return bool(label_evidence_source.strip())


def get_special_track_i1_dataset_training_design() -> DatasetTrainingDesign:
    return DatasetTrainingDesign(
        dataset_schema={
            "schema_version": SPECIAL_TRACK_I1_SCHEMA_VERSION,
            "one_training_example": (
                "one fixed GRID-consistent private chip or feature-summary sample tied to one neutral label"
            ),
            "one_label": (
                "one neutral class assignment with label_quality and independent label_evidence_source"
            ),
            "required_ids": (
                "dataset_id",
                "sample_id",
                "area_id",
                "group_id",
                "chip_id",
            ),
            "splits": ("train", "validation", "test", "final_holdout"),
            "dataset_card_required": True,
            "h1_rankings_revisited_after_i1": True,
        },
        training_example_schema={
            "fields": TRAINING_EXAMPLE_FIELDS,
            "required_fields": TRAINING_EXAMPLE_FIELDS,
            "redaction_class_values": ("LOCAL_SENSITIVE", "FILESYSTEM_ONLY"),
            "coordinate_proxy_fields": (
                "area_id",
                "chip_id",
                "features_ref",
                "metadata_ref",
                "grid_version",
            ),
        },
        label_schema={
            "label_quality_values": LABEL_QUALITY_VALUES,
            "reviewed_tier_values": REVIEWED_TIER_LABEL_QUALITIES,
            "reviewed_tier_requires_independent_evidence": True,
            "weak_or_proxy_values_not_reviewed_tier": (
                "weak_label",
                "synthetic_or_proxy",
                "uncertain",
                "excluded",
            ),
            "neutral_label_examples": ("Class_A", "Class_B", "Class_C"),
        },
        evidence_source_schema={
            "evidence_source_types": EVIDENCE_SOURCE_TYPES,
            "independent_evidence_source_types": INDEPENDENT_EVIDENCE_SOURCE_TYPES,
            "unknown_or_missing_passes_reviewed_tier": False,
            "notebook_or_heuristic_only_passes_reviewed_tier": False,
            "required_fields": (
                "label_evidence_source",
                "evidence_source_type",
                "evidence_source_version",
                "evidence_review_method",
                "reviewer_or_source_reference",
            ),
        },
        label_qa_policy={
            "disagreement_record_required": True,
            "multiple_reviewers_required_for_adjudication": True,
            "final_label_selection_rule": (
                "use independent adjudication record; otherwise exclude sample from reviewed-tier accounting"
            ),
            "inter_rater_agreement_metric": "required or explicitly deferred with written reason",
            "disagreement_notes_required": True,
            "no_agreement_action": "escalate_then_exclude",
        },
        split_policy={
            "group_by": "group_id",
            "area_id_or_stronger_grouping_required": True,
            "near_duplicate_chip_families_split_together": True,
            "same_area_across_dates_split_together_unless_approved": True,
            "temporal_holdout_required": True,
            "final_holdout_untouched": True,
            "deterministic_split_seed_required": True,
            "split_manifest_hash_required": True,
            "holdout_tuning_forbidden": True,
            "forbidden_holdout_uses": (
                "threshold_selection",
                "feature_selection",
                "model_selection",
                "hyperparameter_selection",
                "calibration_selection",
            ),
        },
        leakage_policy={
            "prevent_geographic_leakage": True,
            "prevent_group_leakage": True,
            "prevent_temporal_leakage": True,
            "prevent_near_duplicate_pixel_leakage": True,
            "prevent_chip_family_leakage": True,
            "same_area_date_exception_requires_written_approval": True,
        },
        negative_sampling_policy={
            "negative_background_required": True,
            "hard_negatives_required": True,
            "visually_similar_non_class_areas_required": True,
            "terrain_vegetation_soil_background_diversity_required": True,
            "cloud_shadow_sensor_noise_edge_cases_required": True,
            "false_positive_like_hard_negatives_from_prior_heuristics_required": True,
            "prevalence_recorded_per_split": True,
            "positive_negative_counts_per_class_per_split_required": True,
        },
        dataset_manifest_schema={
            "fields": DATASET_MANIFEST_FIELDS,
            "required_fields": DATASET_MANIFEST_FIELDS,
            "hash_fields_required": (
                "dataset_manifest_hash",
                "dataset_content_hash",
                "split_manifest_hash",
            ),
            "source_count_fields_required": (
                "label_evidence_source_counts",
                "label_quality_counts",
                "class_prevalence_by_split",
            ),
        },
        storage_policy={
            "allowed_artifact_classes": ("LOCAL_SENSITIVE", "FILESYSTEM_ONLY"),
            "datasets_committed_to_git": False,
            "labels_committed_to_git": False,
            "chips_committed_to_git": False,
            "coordinate_metadata_committed_to_git": False,
            "filesystem_only": True,
            "http_servable": False,
            "frontend_visible": False,
            "downloadable_via_api": False,
            "coordinate_proxy_fields_redacted_from_public_summaries": True,
            "coordinate_proxy_examples": (
                "area_id",
                "chip_id",
                "bounds",
                "grid metadata",
                "local paths",
            ),
        },
        evaluation_policy={
            "primary_metric_preregistered_before_training": True,
            "rare_class_metrics": (
                "PR-AUC",
                "recall_at_fixed_precision",
                "calibration",
            ),
            "roc_auc_secondary_unless_prevalence_reported": True,
            "metric_table_required_fields": (
                "split_name",
                "sample_count",
                "class_prevalence",
                "base_rate",
                "label_evidence_counts",
                "uncertainty_or_bootstrap_interval",
            ),
            "baseline_to_beat": "Phase F private CLI classifier baseline",
            "preregistered_margin_required": True,
            "margin_must_clear_holdout_uncertainty": True,
            "if_margin_not_met": "keep Phase F baseline",
        },
        threshold_policy={
            "thresholds_selected_on": ("train", "validation"),
            "holdout_threshold_selection_allowed": False,
            "final_holdout_used_for_threshold_selection": False,
            "threshold_recorded_before_holdout": True,
            "threshold_selection_record_required": True,
        },
        readiness_checklist=(
            "dataset_id assigned",
            "dataset manifest written outside git",
            "dataset_manifest_hash recorded",
            "dataset_content_hash recorded",
            "reviewed-tier labels have independent evidence",
            "minimum holdout size set as a numeric gate",
            "minimum reviewed-tier label count per class set as a numeric gate",
            "negative and hard-negative counts set as numeric gates",
            "split manifest hash recorded",
            "Phase F baseline metric recorded",
            "baseline margin set before training",
            "public exposure review completed before any public surface change",
        ),
        stop_conditions=(
            "missing independent evidence for reviewed-tier labels",
            "missing dataset manifest or required dataset hashes",
            "missing leakage-safe split policy",
            "missing untouched holdout",
            "missing numeric holdout-size gate",
            "missing preregistered baseline margin",
            "storage class outside LOCAL_SENSITIVE or FILESYSTEM_ONLY",
            "requested public exposure without intended-use and misuse review",
        ),
        quantitative_policy={
            "must_be_numeric_before_training": (
                "minimum_holdout_size",
                "minimum_reviewed_tier_label_count_per_class",
                "minimum_negative_background_count",
                "minimum_hard_negative_count",
                "preregistered_baseline_margin",
                "minimum_prevalence_reporting_requirement",
                "minimum_confidence_or_uncertainty_reporting_requirement",
            ),
            "set_in": "dataset readiness record before training begins",
            "holdout_noise_policy": (
                "baseline gain must exceed holdout uncertainty using confidence intervals or paired bootstrap-style evidence"
            ),
        },
        output_traceability_required=OUTPUT_TRACEABILITY_FIELDS,
        notes=(
            "I1 is design, schema, and policy only.",
            "No dataset, training, inference, model weights, public surface, or runtime pipeline behavior is added.",
            "H1 model feasibility rankings remain provisional and must be revisited after this dataset gate is applied.",
        ),
    )


def write_special_track_i1_dataset_training_design_report(
    *,
    run_dir: str | Path,
    run_id: str,
    design: DatasetTrainingDesign | None = None,
    report_relative_path: str = SPECIAL_TRACK_I1_REPORT_RELATIVE_PATH,
) -> Path:
    selected_design = design or get_special_track_i1_dataset_training_design()
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": SPECIAL_TRACK_I1_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        **selected_design.to_dict(),
        "i1_design_only": True,
        "dataset_created": False,
        "training_added": False,
        "inference_added": False,
        "weights_downloaded": False,
        "ml_dependencies_added": False,
        "public_exposure_changes": False,
        "artifact_generation": False,
    }
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return report_path
