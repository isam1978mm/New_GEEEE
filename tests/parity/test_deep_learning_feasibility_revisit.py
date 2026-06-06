from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

from app.pipeline.parity.deep_learning_feasibility import (
    get_special_track_h1_deep_learning_feasibility_candidates,
)
from app.pipeline.parity.deep_learning_feasibility_revisit import (
    ALLOWED_REVISITED_STATUSES,
    FUTURE_SLICE_07_H1_REVISIT_SCHEMA_VERSION,
    get_h1_revisit_candidates,
    get_h1_revisit_gate_references,
    get_h1_revisit_recommended_first_candidate,
    get_h1_revisit_recommended_next_ml_data_slice,
    write_future_slice_07_h1_revisit_report,
)


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


def _by_type() -> dict[str, object]:
    return {candidate.candidate_type: candidate for candidate in get_h1_revisit_candidates()}


def test_all_original_h1_candidate_categories_are_represented() -> None:
    original_types = {
        candidate.candidate_type
        for candidate in get_special_track_h1_deep_learning_feasibility_candidates()
    }
    revisited_types = {candidate.candidate_type for candidate in get_h1_revisit_candidates()}

    assert revisited_types == original_types


def test_every_revisited_candidate_has_a_valid_revisited_status() -> None:
    for candidate in get_h1_revisit_candidates():
        assert candidate.revisited_status in ALLOWED_REVISITED_STATUSES
        assert candidate.original_h1_status
        assert candidate.status_change_reason
        assert candidate.recommended_next_action
        assert candidate.blocker


def test_recommended_first_candidate_remains_private_feature_summary_classifier() -> None:
    recommended = get_h1_revisit_recommended_first_candidate()
    by_id = {candidate.id: candidate for candidate in get_h1_revisit_candidates()}

    assert recommended == "h1_private_feature_summary_probability_classifier"
    assert by_id[recommended].candidate_type == (
        "private_tabular_feature_summary_probability_classifier"
    )
    assert by_id[recommended].revisited_status == "still_best_first_candidate"


def test_cnn_candidate_remains_blocked_without_i2_dataset_pack() -> None:
    candidate = _by_type()["cnn_fixed_raster_chips"]
    assert candidate.revisited_status == "blocked_missing_dataset_pack"
    assert "i2" in candidate.dataset_pack_status.lower() or "i2" in candidate.blocker.lower()


def test_segmentation_candidate_remains_blocked_without_i2_dataset_pack() -> None:
    candidate = _by_type()["segmentation_labeled_masks"]
    assert candidate.revisited_status == "blocked_missing_dataset_pack"
    assert candidate.dataset_pack_status == "not_created_blocked_until_i2"


def test_object_detector_candidate_remains_blocked_without_i2_dataset_pack() -> None:
    candidate = _by_type()["object_detector_boxes_regions"]
    assert candidate.revisited_status == "blocked_missing_dataset_pack"
    assert candidate.dataset_pack_status == "not_created_blocked_until_i2"


def test_pretrained_candidate_remains_blocked_without_weights_and_holdout() -> None:
    candidate = _by_type()["pretrained_external_weight_inference_candidate"]
    assert candidate.revisited_status == "blocked_missing_weights_policy"
    holdout_text = candidate.holdout_policy_status.lower()
    assert "labeled holdout" in holdout_text or "labeled_holdout" in holdout_text
    assert "holdout" in candidate.independent_evidence_status.lower()


def test_tesla_style_candidate_remains_blocked_until_later_source_lock() -> None:
    candidate = _by_type()["notebook_custom_tesla_style_model_attempt"]
    assert candidate.revisited_status == "blocked_until_j2_or_later_source_lock"
    assert "j2" in candidate.recommended_next_action.lower() or (
        "source-lock" in candidate.recommended_next_action.lower()
    )


def test_no_candidate_permits_training_inference_weights_dependencies_or_exposure() -> None:
    for candidate in get_h1_revisit_candidates():
        assert candidate.can_train_now is False
        assert candidate.can_infer_now is False
        assert candidate.can_download_weights_now is False
        assert candidate.can_add_ml_dependencies_now is False
        assert candidate.can_expose_api_frontend_now is False


def test_i1_independent_evidence_gate_is_referenced() -> None:
    references = get_h1_revisit_gate_references()
    text = references["i1_independent_evidence_gate"].lower()
    assert "independent evidence" in text
    assert "label_evidence_source" in text


def test_i1_dataset_manifest_and_hash_gate_is_referenced() -> None:
    references = get_h1_revisit_gate_references()
    text = references["i1_dataset_manifest_hash_gate"].lower()
    assert "dataset_manifest_hash" in text
    assert "dataset_content_hash" in text


def test_i1_holdout_and_baseline_margin_gate_is_referenced() -> None:
    references = get_h1_revisit_gate_references()
    text = references["i1_holdout_and_baseline_margin_gate"].lower()
    assert "holdout" in text
    assert "baseline margin" in text


def test_j1_decomposition_gate_is_referenced() -> None:
    references = get_h1_revisit_gate_references()
    text = references["j1_decomposition_gate"].lower()
    assert "decompos" in text
    assert "tesla" in text


def test_phase_f_baseline_remains_the_baseline_to_beat() -> None:
    references = get_h1_revisit_gate_references()
    assert "Phase F" in references["phase_f_baseline_to_beat"]
    for candidate in get_h1_revisit_candidates():
        assert candidate.baseline_policy_status == "phase_f_baseline_to_beat_defined"


def test_report_recommends_i2_as_next_ml_data_slice() -> None:
    assert get_h1_revisit_recommended_next_ml_data_slice().startswith("I2")


def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    report_path = write_future_slice_07_h1_revisit_report(
        run_dir=run_dir,
        run_id="future-slice-07",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path.resolve().is_relative_to(run_dir.resolve())
    assert report_path == run_dir / "manifests" / "future_slice_07_h1_revisit_after_i1_j1.json"
    assert payload["schema_version"] == FUTURE_SLICE_07_H1_REVISIT_SCHEMA_VERSION
    assert payload["run_id"] == "future-slice-07"
    assert payload["revisit_id"] == "future_slice_07_h1_revisit_after_i1_j1"
    assert payload["recommended_first_candidate"] == (
        "h1_private_feature_summary_probability_classifier"
    )
    assert payload["recommended_next_ml_data_slice"].startswith("I2")
    assert payload["h1_revisit_only"] is True
    assert payload["training_added"] is False
    assert payload["inference_added"] is False
    assert payload["weights_downloaded"] is False
    assert payload["ml_dependencies_added"] is False
    assert payload["dataset_created"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["artifact_generation"] is False
    assert set(payload["counts_by_revisited_status"]) == ALLOWED_REVISITED_STATUSES
    assert sum(payload["counts_by_revisited_status"].values()) == len(payload["candidates"])


def test_report_result_fields_are_complete(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    report_path = write_future_slice_07_h1_revisit_report(
        run_dir=run_dir,
        run_id="future-slice-07-fields",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    required_fields = {
        "id",
        "candidate_name",
        "candidate_type",
        "original_h1_status",
        "revisited_status",
        "status_change_reason",
        "i1_dataset_gate_status",
        "j1_decomposition_gate_status",
        "independent_evidence_status",
        "dataset_pack_status",
        "holdout_policy_status",
        "baseline_policy_status",
        "weights_policy_status",
        "dependency_policy_status",
        "phase_c_e_feature_support_status",
        "phase_d_e_map_artifact_support_status",
        "recommended_next_action",
        "can_train_now",
        "can_infer_now",
        "can_download_weights_now",
        "can_add_ml_dependencies_now",
        "can_expose_api_frontend_now",
        "blocker",
        "notes",
    }
    for candidate in payload["candidates"]:
        assert set(candidate) >= required_fields


def test_report_creates_no_model_dataset_raster_map_or_public_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    write_future_slice_07_h1_revisit_report(
        run_dir=run_dir,
        run_id="future-slice-07-no-artifacts",
    )

    created = [
        path
        for path in run_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created == []


def test_module_adds_no_heavy_ml_runtime_pipeline_or_public_hooks() -> None:
    import app.pipeline.parity.deep_learning_feasibility_revisit as module

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


def test_revisit_doc_and_module_avoid_claim_wording() -> None:
    paths = (
        Path("app/pipeline/parity/deep_learning_feasibility_revisit.py"),
        Path("docs/FUTURE_SLICE_07_H1_REVISIT_AFTER_I1_J1.md"),
    )

    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in paths
        if path.exists()
    )

    assert all(not _wording_violation(combined, term) for term in _claim_terms())
