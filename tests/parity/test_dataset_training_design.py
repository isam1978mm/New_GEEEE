import json
from pathlib import Path

from app.pipeline.parity import dataset_training_design as design


REQUIRED_OBJECTS = {
    "dataset_schema",
    "training_example_schema",
    "label_schema",
    "evidence_source_schema",
    "label_qa_policy",
    "split_policy",
    "leakage_policy",
    "negative_sampling_policy",
    "dataset_manifest_schema",
    "storage_policy",
    "evaluation_policy",
    "threshold_policy",
    "readiness_checklist",
    "stop_conditions",
    "quantitative_policy",
    "output_traceability_required",
}

TRAINING_EXAMPLE_FIELDS = {
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
}


def _claim_terms() -> tuple[str, ...]:
    return (
        "con" + "firmed",
        "fou" + "nd",
        "pro" + "ven",
        "dig " + "target",
        "defi" + "nitely",
        "dis" + "covery",
        "burial " + "pro" + "ven",
        "tomb " + "con" + "firmed",
        "target " + "con" + "firmed",
    )


def test_design_exposes_all_required_objects() -> None:
    payload = design.get_special_track_i1_dataset_training_design().to_dict()

    assert REQUIRED_OBJECTS.issubset(payload)


def test_training_example_schema_contains_required_fields() -> None:
    payload = design.get_special_track_i1_dataset_training_design().to_dict()

    assert TRAINING_EXAMPLE_FIELDS.issubset(payload["training_example_schema"]["fields"])


def test_label_and_evidence_enums_are_locked() -> None:
    payload = design.get_special_track_i1_dataset_training_design().to_dict()

    assert set(payload["label_schema"]["label_quality_values"]) == {
        "reviewed_independent",
        "reviewed_adjudicated",
        "weak_label",
        "synthetic_or_proxy",
        "uncertain",
        "excluded",
    }
    assert set(payload["evidence_source_schema"]["evidence_source_types"]) == {
        "field_validation",
        "authoritative_external_dataset",
        "expert_adjudication_independent_evidence",
        "independently_produced_reference",
        "weak_heuristic_hint",
        "synthetic_proxy",
        "unknown_or_missing",
    }


def test_reviewed_tier_label_gate_requires_independent_evidence() -> None:
    assert design.label_record_passes_reviewed_tier_gate(
        label_quality="reviewed_independent",
        evidence_source_type="field_validation",
        label_evidence_source="field-log-001",
    )
    assert not design.label_record_passes_reviewed_tier_gate(
        label_quality="reviewed_independent",
        evidence_source_type="unknown_or_missing",
        label_evidence_source="field-log-001",
    )
    assert not design.label_record_passes_reviewed_tier_gate(
        label_quality="reviewed_adjudicated",
        evidence_source_type="expert_adjudication_independent_evidence",
        label_evidence_source="",
    )
    assert not design.label_record_passes_reviewed_tier_gate(
        label_quality="weak_label",
        evidence_source_type="field_validation",
        label_evidence_source="field-log-001",
    )


def test_qa_split_negative_and_storage_policies_lock_hard_gates() -> None:
    payload = design.get_special_track_i1_dataset_training_design().to_dict()
    qa_policy = payload["label_qa_policy"]
    split_policy = payload["split_policy"]
    negative_policy = payload["negative_sampling_policy"]
    manifest_schema = payload["dataset_manifest_schema"]
    storage_policy = payload["storage_policy"]

    assert qa_policy["disagreement_record_required"] is True
    assert qa_policy["inter_rater_agreement_metric"] != ""
    assert qa_policy["no_agreement_action"] in {"exclude_sample", "escalate_then_exclude"}
    assert split_policy["group_by"] in {"area_id", "group_id"}
    assert split_policy["temporal_holdout_required"] is True
    assert split_policy["final_holdout_untouched"] is True
    assert split_policy["holdout_tuning_forbidden"] is True
    assert payload["leakage_policy"]["prevent_geographic_leakage"] is True
    assert payload["leakage_policy"]["prevent_group_leakage"] is True
    assert negative_policy["negative_background_required"] is True
    assert negative_policy["hard_negatives_required"] is True
    assert negative_policy["prevalence_recorded_per_split"] is True
    assert {"dataset_id", "dataset_manifest_hash", "dataset_content_hash"}.issubset(
        manifest_schema["fields"]
    )
    assert set(storage_policy["allowed_artifact_classes"]) == {
        "LOCAL_SENSITIVE",
        "FILESYSTEM_ONLY",
    }
    assert storage_policy["filesystem_only"] is True
    assert storage_policy["http_servable"] is False
    assert storage_policy["frontend_visible"] is False
    assert storage_policy["downloadable_via_api"] is False


def test_evaluation_threshold_quantitative_and_traceability_policies() -> None:
    payload = design.get_special_track_i1_dataset_training_design().to_dict()
    evaluation_policy = payload["evaluation_policy"]
    threshold_policy = payload["threshold_policy"]
    quantitative_policy = payload["quantitative_policy"]

    assert evaluation_policy["baseline_to_beat"] == "Phase F private CLI classifier baseline"
    assert evaluation_policy["preregistered_margin_required"] is True
    assert evaluation_policy["margin_must_clear_holdout_uncertainty"] is True
    assert "PR-AUC" in evaluation_policy["rare_class_metrics"]
    assert threshold_policy["holdout_threshold_selection_allowed"] is False
    assert threshold_policy["threshold_recorded_before_holdout"] is True
    assert {
        "minimum_holdout_size",
        "minimum_reviewed_tier_label_count_per_class",
        "minimum_negative_background_count",
        "minimum_hard_negative_count",
        "preregistered_baseline_margin",
    }.issubset(quantitative_policy["must_be_numeric_before_training"])
    assert {"dataset_id", "dataset_manifest_hash", "dataset_content_hash"}.issubset(
        payload["output_traceability_required"]
    )


def test_report_writes_json_under_run_dir_without_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    report_path = design.write_special_track_i1_dataset_training_design_report(
        run_dir=run_dir,
        run_id="i1-test-run",
    )

    assert report_path == run_dir / "manifests" / "special_track_i1_dataset_training_design.json"
    assert report_path.resolve().is_relative_to(run_dir.resolve())
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "i1-test-run"
    assert payload["i1_design_only"] is True
    assert payload["dataset_created"] is False
    assert payload["training_added"] is False
    assert payload["inference_added"] is False
    assert payload["weights_downloaded"] is False
    assert payload["ml_dependencies_added"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["artifact_generation"] is False

    blocked_suffixes = {
        ".tif",
        ".tiff",
        ".npy",
        ".geojson",
        ".kmz",
        ".kml",
        ".html",
        ".png",
        ".jpg",
        ".jpeg",
        ".csv",
        ".pt",
        ".pth",
        ".onnx",
        ".h5",
        ".pkl",
        ".joblib",
        ".parquet",
        ".sqlite",
        ".db",
        ".jsonl",
    }
    created = [p for p in run_dir.rglob("*") if p.is_file()]
    assert created == [report_path]
    assert not any(path.suffix.lower() in blocked_suffixes for path in created)


def test_design_module_has_no_runtime_or_heavy_ml_hooks() -> None:
    source = Path(design.__file__).read_text(encoding="utf-8")

    forbidden_tokens = [
        "import ee",
        "ee.Authenticate",
        "earthengine",
        "import torch",
        "import tensorflow",
        "import keras",
        "ultralytics",
        "segmentation_models_pytorch",
        "APIRouter",
        "BackgroundTasks",
        "serve_artifact_response",
        "can_serve_artifact",
        "requests.get",
        "urlretrieve",
        "run_orchestrator",
        "run_core_pipeline",
    ]
    for token in forbidden_tokens:
        assert token not in source


def test_no_forbidden_claim_wording_in_i1_docs_or_code() -> None:
    paths = [
        Path(design.__file__),
        Path("docs/SPECIAL_TRACK_I_DATASET_TRAINING_DESIGN.md"),
    ]
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for term in _claim_terms():
            assert term not in text
