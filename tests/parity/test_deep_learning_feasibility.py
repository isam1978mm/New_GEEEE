from __future__ import annotations

import inspect
import json
import re
from pathlib import Path


REQUIRED_CANDIDATE_TYPES = {
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

FORBIDDEN_ARTIFACT_SUFFIXES = {
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
}

TRACEABILITY_FIELDS = {
    "dataset_id",
    "dataset_manifest_hash",
    "dataset_content_hash",
}


def _claim_terms() -> tuple[str, ...]:
    return (
        "con" + "firmed",
        "fou" + "nd",
        "pro" + "ven",
        "dig" + " target",
        "def" + "initely",
        "disc" + "overy",
        "burial " + "pro" + "ven",
        "tomb " + "con" + "firmed",
        "target " + "con" + "firmed",
    )


def _wording_violation(content: str, term: str) -> bool:
    if " " in term:
        return term in content
    return re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", content) is not None


def test_all_required_candidate_categories_are_present() -> None:
    from app.pipeline.parity.deep_learning_feasibility import (
        get_special_track_h1_deep_learning_feasibility_candidates,
    )

    candidates = get_special_track_h1_deep_learning_feasibility_candidates()

    assert {candidate.candidate_type for candidate in candidates} == REQUIRED_CANDIDATE_TYPES


def test_every_candidate_declares_required_readiness_policies() -> None:
    from app.pipeline.parity.deep_learning_feasibility import (
        get_special_track_h1_deep_learning_feasibility_candidates,
    )

    for candidate in get_special_track_h1_deep_learning_feasibility_candidates():
        assert candidate.feasibility_status in ALLOWED_FEASIBILITY_STATUSES
        assert candidate.independent_evidence_required
        assert candidate.minimum_dataset_requirements
        assert candidate.minimum_holdout_requirements
        assert candidate.baseline_to_beat
        assert candidate.baseline_margin_policy
        assert candidate.leakage_controls_required
        assert candidate.weights_policy
        assert candidate.dependency_policy
        assert candidate.evaluation_metrics
        assert candidate.threshold_policy
        assert candidate.feeds_i1_requirements is True
        assert candidate.revisit_after_i1 is True


def test_recommended_first_candidate_is_private_feature_summary_probability_path() -> None:
    from app.pipeline.parity.deep_learning_feasibility import (
        get_special_track_h1_deep_learning_feasibility_candidates,
        get_special_track_h1_recommended_first_candidate,
    )

    recommended = get_special_track_h1_recommended_first_candidate()
    candidates = {
        candidate.id: candidate
        for candidate in get_special_track_h1_deep_learning_feasibility_candidates()
    }

    assert recommended == "h1_private_feature_summary_probability_classifier"
    assert candidates[recommended].candidate_type == (
        "private_tabular_feature_summary_probability_classifier"
    )
    assert candidates[recommended].feasibility_status == "best_first_candidate"


def test_large_model_candidates_are_not_ready_without_i1_data() -> None:
    from app.pipeline.parity.deep_learning_feasibility import (
        get_special_track_h1_deep_learning_feasibility_candidates,
    )

    large_candidate_types = {
        "cnn_fixed_raster_chips",
        "segmentation_labeled_masks",
        "object_detector_boxes_regions",
    }
    blocked_statuses = {
        "blocked_missing_dataset",
        "blocked_missing_independent_labels",
        "blocked_missing_weights",
        "blocked_dependency_risk",
        "feasible_later_after_i1",
    }

    for candidate in get_special_track_h1_deep_learning_feasibility_candidates():
        if candidate.candidate_type in large_candidate_types:
            assert candidate.feasibility_status in blocked_statuses
            assert candidate.training_allowed_now is False
            assert candidate.inference_allowed_now is False


def test_pretrained_weight_candidate_still_requires_labeled_holdout_validation() -> None:
    from app.pipeline.parity.deep_learning_feasibility import (
        get_special_track_h1_deep_learning_feasibility_candidates,
    )

    candidate = next(
        item
        for item in get_special_track_h1_deep_learning_feasibility_candidates()
        if item.candidate_type == "pretrained_external_weight_inference_candidate"
    )

    policy_text = " ".join(candidate.weights_policy).lower()
    holdout_text = " ".join(candidate.minimum_holdout_requirements).lower()

    assert candidate.weights_required is True
    assert "approved weights do not bypass holdout validation" in policy_text
    assert "labeled holdout" in holdout_text
    assert candidate.zero_validation_inference_allowed is False


def test_no_candidate_permits_training_inference_or_public_integration_now() -> None:
    from app.pipeline.parity.deep_learning_feasibility import (
        get_special_track_h1_deep_learning_feasibility_candidates,
    )

    for candidate in get_special_track_h1_deep_learning_feasibility_candidates():
        assert candidate.training_allowed_now is False
        assert candidate.inference_allowed_now is False
        assert candidate.zero_validation_inference_allowed is False
        assert candidate.api_frontend_integration_allowed_now is False
        assert "api" not in candidate.output_boundary.lower()
        assert "frontend" not in candidate.output_boundary.lower()


def test_output_traceability_requires_dataset_identity_and_hashes() -> None:
    from app.pipeline.parity.deep_learning_feasibility import (
        get_special_track_h1_deep_learning_feasibility_candidates,
    )

    for candidate in get_special_track_h1_deep_learning_feasibility_candidates():
        assert TRACEABILITY_FIELDS <= set(candidate.output_traceability_required)


def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path: Path) -> None:
    from app.pipeline.parity.deep_learning_feasibility import (
        SPECIAL_TRACK_H1_SCHEMA_VERSION,
        write_special_track_h1_deep_learning_feasibility_report,
    )

    run_dir = tmp_path / "run"
    report_path = write_special_track_h1_deep_learning_feasibility_report(
        run_dir=run_dir,
        run_id="special-track-h1",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path.resolve().is_relative_to(run_dir.resolve())
    assert payload["schema_version"] == SPECIAL_TRACK_H1_SCHEMA_VERSION
    assert payload["run_id"] == "special-track-h1"
    assert payload["recommended_first_candidate"] == (
        "h1_private_feature_summary_probability_classifier"
    )
    assert payload["h1_design_only"] is True
    assert payload["training_added"] is False
    assert payload["inference_added"] is False
    assert payload["weights_downloaded"] is False
    assert payload["ml_dependencies_added"] is False
    assert payload["api_frontend_integration_added"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["artifact_generation"] is False
    assert set(payload["counts_by_feasibility_status"]) == ALLOWED_FEASIBILITY_STATUSES


def test_report_creates_no_model_dataset_raster_map_or_public_classifier_artifacts(
    tmp_path: Path,
) -> None:
    from app.pipeline.parity.deep_learning_feasibility import (
        write_special_track_h1_deep_learning_feasibility_report,
    )

    run_dir = tmp_path / "run"
    write_special_track_h1_deep_learning_feasibility_report(
        run_dir=run_dir,
        run_id="special-track-h1-no-artifacts",
    )

    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created == []


def test_module_adds_no_heavy_ml_runtime_pipeline_or_public_hooks() -> None:
    import app.pipeline.parity.deep_learning_feasibility as module

    source = inspect.getsource(module)
    lowered = source.lower()

    assert "import torch" not in source
    assert "import tensorflow" not in source
    assert "keras" not in lowered
    assert "import cuda" not in lowered
    assert "ultralytics" not in lowered
    assert "segmentation_models_pytorch" not in lowered
    assert "urlretrieve" not in lowered
    assert "requests.get" not in lowered
    assert "serve_artifact_response" not in source
    assert "can_serve_artifact" not in source
    assert "FileResponse" not in source
    assert "StreamingResponse" not in source
    assert "APIRouter" not in source
    assert "BackgroundTasks" not in source
    assert "enqueue_core_pipeline_run" not in source
    assert "run_core_pipeline" not in source
    assert "ee.Authenticate" not in source
    assert "import ee" not in source
    assert "earthengine" not in lowered
    assert "google.colab" not in source
    assert "drive.mount" not in source
    assert "/content/drive" not in source


def test_h1_docs_and_module_avoid_claim_wording() -> None:
    paths = (
        Path("app/pipeline/parity/deep_learning_feasibility.py"),
        Path("docs/SPECIAL_TRACK_H_DEEP_LEARNING_FEASIBILITY.md"),
    )

    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in paths
        if path.exists()
    )

    assert all(not _wording_violation(combined, term) for term in _claim_terms())
