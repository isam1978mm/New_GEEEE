import json
import re
from pathlib import Path

from app.pipeline.parity import tesla_flow_decomposition as decomposition


REQUIRED_CATEGORIES = {
    "data_acquisition",
    "roi_grid_alignment",
    "raster_feature_writer",
    "private_map_artifact",
    "private_classifier_scoring",
    "ml_model_attempt",
    "dataset_training",
    "generated_overlay_ui",
    "public_exposure",
    "provenance_report",
    "duplicate_or_variant",
    "unsupported_or_unclear",
    "blocked_by_policy",
}

REQUIRED_MAPPING_TARGETS = {
    "Phase A — map point picker + ROI/grid preview",
    "Phase B — controlled backend Earth Engine run flow",
    "Phase C — defensible raster/feature writers",
    "Phase D — private map artifact writers",
    "Phase E — private parity verifier against frozen notebook outputs",
    "Phase F — private neutral CLI classifier",
    "Special Track G/G1 — controlled location overlay policy",
    "Special Track G2 — operator-only private generated-overlay UI",
    "Special Track H/H1 — deep-learning feasibility",
    "Special Track I/I1 — real dataset/training design",
    "future_slice_required",
    "blocked_do_not_port",
    "duplicate_excluded",
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


def _items() -> tuple[decomposition.TeslaFlowDecompositionItem, ...]:
    return decomposition.get_special_track_j1_tesla_flow_decomposition()


def test_all_required_categories_and_mapping_targets_are_represented() -> None:
    items = _items()

    assert {item.category for item in items} == REQUIRED_CATEGORIES
    assert REQUIRED_MAPPING_TARGETS.issubset({item.app_mapping_target for item in items})


def test_status_and_decision_enums_are_valid_and_evidence_is_present() -> None:
    for item in _items():
        assert item.current_status in decomposition.ALLOWED_CURRENT_STATUSES
        assert item.implementation_decision in decomposition.ALLOWED_IMPLEMENTATION_DECISIONS
        assert item.source_evidence or item.notes
        assert item.risk_level in {"low", "medium", "high", "blocked"}


def test_policy_mapping_rules_are_locked() -> None:
    items = _items()

    data_items = [item for item in items if item.category == "data_acquisition"]
    assert data_items
    assert all(
        item.app_mapping_target
        in {
            "Phase B — controlled backend Earth Engine run flow",
            "future_slice_required",
        }
        for item in data_items
    )

    assert all(
        item.app_mapping_target == "Phase A — map point picker + ROI/grid preview"
        for item in items
        if item.category == "roi_grid_alignment"
    )
    assert all(
        item.app_mapping_target
        in {
            "Phase C — defensible raster/feature writers",
            "future_slice_required",
        }
        for item in items
        if item.category == "raster_feature_writer"
    )
    assert all(
        item.app_mapping_target
        in {
            "Phase D — private map artifact writers",
            "future_slice_required",
        }
        for item in items
        if item.category == "private_map_artifact"
    )
    assert all(
        item.app_mapping_target
        in {
            "Phase F — private neutral CLI classifier",
            "future_slice_required",
        }
        for item in items
        if item.category == "private_classifier_scoring"
    )
    assert all(
        item.app_mapping_target
        in {
            "Special Track H/H1 — deep-learning feasibility",
            "Special Track I/I1 — real dataset/training design",
        }
        or item.current_status in {"blocked_missing_data", "blocked_missing_weights"}
        for item in items
        if item.category == "ml_model_attempt"
    )


def test_public_overlay_duplicate_and_unclear_items_are_not_ready() -> None:
    for item in _items():
        assert item.implementation_decision != "already_covered" or not item.requires_public_exposure
        assert not item.public_allowed_now
        assert not item.requires_artifact_serving_change
        if item.category == "generated_overlay_ui":
            assert item.app_mapping_target == "Special Track G2 — operator-only private generated-overlay UI"
            assert item.public_allowed_now is False
        if item.category == "public_exposure":
            assert item.current_status == "blocked_policy"
            assert item.public_allowed_now is False
        if item.category == "duplicate_or_variant":
            assert item.current_status == "duplicate_excluded"
            assert item.implementation_decision == "duplicate_ignore"
        if item.category == "unsupported_or_unclear":
            assert item.implementation_decision in {"blocked_do_not_port", "research_only"}
        assert item.app_mapping_target != "full_tesla_runtime"


def test_recommended_execution_order_does_not_start_with_full_runtime() -> None:
    order = decomposition.get_recommended_future_execution_order()

    assert order
    assert "full Tesla runtime" not in order[0]
    assert order[0].startswith("J2")


def test_report_writes_json_under_run_dir_without_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    report_path = decomposition.write_special_track_j1_tesla_flow_decomposition_report(
        run_dir=run_dir,
        run_id="j1-test-run",
    )

    assert report_path == run_dir / "manifests" / "special_track_j1_tesla_flow_decomposition.json"
    assert report_path.resolve().is_relative_to(run_dir.resolve())
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "j1-test-run"
    assert payload["j1_decomposition_only"] is True
    assert payload["runtime_added"] is False
    assert payload["training_added"] is False
    assert payload["inference_added"] is False
    assert payload["weights_downloaded"] is False
    assert payload["dataset_created"] is False
    assert payload["earth_engine_calls_added"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["artifact_generation"] is False
    assert payload["counts_by_category"]["blocked_by_policy"] >= 1

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
    created = [path for path in run_dir.rglob("*") if path.is_file()]
    assert created == [report_path]
    assert not any(path.suffix.lower() in blocked_suffixes for path in created)


def test_module_has_no_runtime_or_heavy_ml_hooks() -> None:
    source = Path(decomposition.__file__).read_text(encoding="utf-8")

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


def test_no_forbidden_claim_wording_in_j1_docs_or_code() -> None:
    paths = [
        Path(decomposition.__file__),
        Path("docs/SPECIAL_TRACK_J_TESLA_FLOW_DECOMPOSITION.md"),
    ]
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for term in _claim_terms():
            pattern = re.compile(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])")
            assert not pattern.search(text)
