import json
import re
from pathlib import Path

import pytest

from app.pipeline.parity.classifier_model_inventory import (
    ALLOWED_ARTIFACT_CLASSES,
    ALLOWED_CATEGORIES,
    ALLOWED_IMPLEMENTATION_STATUSES,
    ALLOWED_PARITY_STATUSES,
    ALLOWED_SOURCE_STATUSES,
    PHASE_7_CLASSIFIER_MODEL_SCHEMA_VERSION,
    ClassifierModelInventoryItem,
    get_phase_7_classifier_model_inventory,
    write_phase_7_classifier_model_inventory_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_7_CONTRACT = REPO_ROOT / "docs" / "PHASE_7_CLASSIFIER_MODEL_PARITY_CONTRACT.md"
FULL_CHECKLIST = REPO_ROOT / "docs" / "NOTEBOOK_PARITY_FULL_CHECKLIST.md"
MODULE_PATH = REPO_ROOT / "app" / "pipeline" / "parity" / "classifier_model_inventory.py"

FORBIDDEN_WORDING = {
    "confirmed",
    "found",
    "proven",
    "dig target",
    "definitely",
}

REQUIRED_CATEGORIES = {
    "notebook_rule_based_classifier",
    "neutral_label_mapping",
    "experimental_cli_boundary",
    "deep_learning_model_cells",
    "classifier_inputs_outputs",
    "public_exposure_boundary",
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
    ".pt",
    ".pth",
    ".onnx",
    ".h5",
    ".pkl",
    ".joblib",
}

NON_NEUTRAL_LABEL_MARKERS = {
    "Gold_Metal",
    "Sarcophagus",
    "Mercury_Trace",
    "Buried_Entrance",
    "Weapons_Shield",
    "Ancient_Well",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_required_status_tokens(text: str) -> str:
    for token in (
        ALLOWED_SOURCE_STATUSES
        | ALLOWED_PARITY_STATUSES
        | ALLOWED_IMPLEMENTATION_STATUSES
        | ALLOWED_ARTIFACT_CLASSES
    ):
        text = text.replace(token.lower(), "")
    return text


def test_inventory_includes_all_required_categories():
    categories = {item.category for item in get_phase_7_classifier_model_inventory()}

    assert categories == REQUIRED_CATEGORIES


def test_each_item_uses_valid_enums_and_nonblank_actions():
    for item in get_phase_7_classifier_model_inventory():
        assert item.category in ALLOWED_CATEGORIES
        assert item.source_status in ALLOWED_SOURCE_STATUSES
        assert item.parity_status in ALLOWED_PARITY_STATUSES
        assert item.implementation_status in ALLOWED_IMPLEMENTATION_STATUSES
        assert item.artifact_class in ALLOWED_ARTIFACT_CLASSES
        assert item.blocker.strip() or item.recommended_next_action.strip()


def test_classifier_items_stay_cli_only_experimental_and_private():
    for item in get_phase_7_classifier_model_inventory():
        assert item.target_mode != "public_shared"
        assert item.filesystem_only is True
        assert item.cli_only is True
        assert item.requires_enable_experimental is True
        assert item.http_servable is False
        assert item.frontend_visible is False
        assert item.downloadable_via_api is False
        assert item.called_by_api is False
        assert item.called_by_background_tasks is False
        assert item.called_by_core_orchestrator is False


def test_runtime_and_notebook_value_parity_flags_remain_false():
    for item in get_phase_7_classifier_model_inventory():
        assert item.runtime_output_verified is False
        assert item.notebook_value_parity_verified is False


def test_allowed_enums_and_safety_boundaries_are_enforced():
    base_kwargs = dict(
        id="bad",
        category="notebook_rule_based_classifier",
        notebook_artifact_or_pattern="bad",
        current_app_artifact_or_pattern="bad",
        source_status="exact_source_found",
        current_app_status="bad",
        parity_status="inventory_only",
        expected_inputs=(),
        expected_outputs=(),
        required_reference_artifacts=(),
        required_metadata=(),
        target_mode="experimental_private",
        classification="bad",
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
        blocker="bad",
        recommended_next_action="bad",
        notes="bad",
    )

    with pytest.raises(ValueError, match="unsupported category"):
        ClassifierModelInventoryItem(**{**base_kwargs, "category": "bad_category"})
    with pytest.raises(ValueError, match="unsupported source_status"):
        ClassifierModelInventoryItem(**{**base_kwargs, "source_status": "bad"})
    with pytest.raises(ValueError, match="unsupported parity_status"):
        ClassifierModelInventoryItem(**{**base_kwargs, "parity_status": "bad"})
    with pytest.raises(ValueError, match="unsupported implementation_status"):
        ClassifierModelInventoryItem(**{**base_kwargs, "implementation_status": "bad"})
    with pytest.raises(ValueError, match="unsupported artifact_class"):
        ClassifierModelInventoryItem(**{**base_kwargs, "artifact_class": "bad"})
    with pytest.raises(ValueError, match="must not target public_shared"):
        ClassifierModelInventoryItem(**{**base_kwargs, "target_mode": "public_shared"})
    with pytest.raises(ValueError, match="must remain filesystem_only"):
        ClassifierModelInventoryItem(**{**base_kwargs, "filesystem_only": False})
    with pytest.raises(ValueError, match="must remain cli_only"):
        ClassifierModelInventoryItem(**{**base_kwargs, "cli_only": False})
    with pytest.raises(ValueError, match="must require ENABLE_EXPERIMENTAL"):
        ClassifierModelInventoryItem(
            **{**base_kwargs, "requires_enable_experimental": False}
        )
    with pytest.raises(ValueError, match="must not be http_servable"):
        ClassifierModelInventoryItem(**{**base_kwargs, "http_servable": True})
    with pytest.raises(ValueError, match="must not be frontend_visible"):
        ClassifierModelInventoryItem(**{**base_kwargs, "frontend_visible": True})
    with pytest.raises(ValueError, match="must not be downloadable_via_api"):
        ClassifierModelInventoryItem(**{**base_kwargs, "downloadable_via_api": True})
    with pytest.raises(ValueError, match="must not be called by API"):
        ClassifierModelInventoryItem(**{**base_kwargs, "called_by_api": True})
    with pytest.raises(ValueError, match="must not be called by BackgroundTasks"):
        ClassifierModelInventoryItem(
            **{**base_kwargs, "called_by_background_tasks": True}
        )
    with pytest.raises(ValueError, match="must not be called by core orchestrator"):
        ClassifierModelInventoryItem(
            **{**base_kwargs, "called_by_core_orchestrator": True}
        )


def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    report_path = write_phase_7_classifier_model_inventory_report(
        run_dir,
        "phase7-run",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == run_dir / "manifests" / "phase_7_classifier_model_inventory.json"
    assert report_path.resolve().relative_to(run_dir.resolve())
    assert payload["schema_version"] == PHASE_7_CLASSIFIER_MODEL_SCHEMA_VERSION
    assert payload["run_id"] == "phase7-run"
    assert payload["phase_7_runtime_changes"] is False
    assert payload["public_exposure_changes"] is False
    assert set(payload["counts_by_category"]) == ALLOWED_CATEGORIES
    assert set(payload["counts_by_parity_status"]) == ALLOWED_PARITY_STATUSES
    assert set(payload["counts_by_implementation_status"]) == ALLOWED_IMPLEMENTATION_STATUSES
    assert set(payload["counts_by_artifact_class"]) == ALLOWED_ARTIFACT_CLASSES


def test_report_creates_no_raster_coordinate_map_or_model_artifacts(tmp_path):
    run_dir = tmp_path / "run"
    write_phase_7_classifier_model_inventory_report(run_dir, "phase7-no-artifacts")

    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]

    assert created == []


def test_module_does_not_add_train_infer_predict_classify_generate_or_export_functions():
    import app.pipeline.parity.classifier_model_inventory as module

    forbidden_public_functions = [
        name
        for name in dir(module)
        if name.startswith(
            (
                "train_",
                "infer_",
                "predict_",
                "classify_",
                "generate_",
                "export_",
                "run_model_",
                "load_model_",
            )
        )
    ]

    assert forbidden_public_functions == []


def test_docs_do_not_claim_public_availability_for_classifier_artifacts():
    contract = _read(PHASE_7_CONTRACT).lower()

    assert "does not expose classifier/model artifacts through http" in contract
    assert "frontend_visible=false" in contract
    assert "downloadable_via_api=false" in contract
    assert "public availability" not in contract


def test_docs_and_module_avoid_forbidden_certainty_wording():
    merged = "\n".join([_read(PHASE_7_CONTRACT).lower(), _read(MODULE_PATH).lower()])
    merged = _strip_required_status_tokens(merged)

    for term in FORBIDDEN_WORDING:
        assert re.search(rf"\b{re.escape(term)}\b", merged) is None


def test_docs_and_module_use_neutral_app_facing_class_names_only():
    merged = "\n".join([_read(PHASE_7_CONTRACT), _read(MODULE_PATH)])

    assert "Class_A" in merged
    assert "Class_B" in merged
    assert "Class_C" in merged
    for marker in NON_NEUTRAL_LABEL_MARKERS:
        assert marker not in merged


def test_phase_7_contract_and_checklist_reference_exist():
    checklist = _read(FULL_CHECKLIST)

    assert PHASE_7_CONTRACT.exists()
    assert "Phase 7 — Classifier/model parity" in checklist
    assert "docs/PHASE_7_CLASSIFIER_MODEL_PARITY_CONTRACT.md" in checklist
    assert "Phase 8 — Probability-only ML classifier design" in checklist
