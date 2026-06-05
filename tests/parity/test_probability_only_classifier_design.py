import json
import re
from pathlib import Path

import pytest

from app.pipeline.parity.probability_only_classifier_design import (
    ALLOWED_ARTIFACT_CLASSES,
    ALLOWED_CATEGORIES,
    ALLOWED_DESIGN_STATUSES,
    ALLOWED_IMPLEMENTATION_STATUSES,
    PHASE_8_PROBABILITY_ONLY_SCHEMA_VERSION,
    ProbabilityOnlyClassifierDesignItem,
    get_phase_8_probability_only_classifier_design,
    write_phase_8_probability_only_classifier_design_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_8_CONTRACT = REPO_ROOT / "docs" / "PHASE_8_PROBABILITY_ONLY_CLASSIFIER_DESIGN.md"
FULL_CHECKLIST = REPO_ROOT / "docs" / "NOTEBOOK_PARITY_FULL_CHECKLIST.md"
MODULE_PATH = REPO_ROOT / "app" / "pipeline" / "parity" / "probability_only_classifier_design.py"

FORBIDDEN_WORDING = {
    "confirmed",
    "found",
    "proven",
    "dig target",
    "definitely",
    "discovery",
    "burial proven",
    "tomb confirmed",
    "target confirmed",
}

REQUIRED_CATEGORIES = {
    "probability_output_schema",
    "neutral_class_probability_labels",
    "threshold_and_uncertainty_policy",
    "private_cli_only_boundary",
    "forbidden_wording_policy",
    "future_reference_and_verifier_requirements",
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
    ".csv",
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


def _strip_required_forbidden_wording_policy(text: str) -> str:
    text = re.sub(
        r"_forbidden_wording: tuple\[str, \.\.\.\] = \([\s\S]*?\n\)",
        "",
        text,
    )
    text = re.sub(r"_forbidden_wording = \([\s\S]*?\n\)", "", text)
    text = re.sub(
        r"forbidden_wording=\(_FORBIDDEN_WORDING\),?",
        "",
        text,
    )
    return text


def test_design_inventory_includes_all_required_categories():
    categories = {item.category for item in get_phase_8_probability_only_classifier_design()}

    assert categories == REQUIRED_CATEGORIES


def test_each_item_uses_valid_enums_and_nonblank_actions():
    for item in get_phase_8_probability_only_classifier_design():
        assert item.category in ALLOWED_CATEGORIES
        assert item.design_status in ALLOWED_DESIGN_STATUSES
        assert item.implementation_status in ALLOWED_IMPLEMENTATION_STATUSES
        assert item.artifact_class in ALLOWED_ARTIFACT_CLASSES
        assert item.blocker.strip() or item.recommended_next_action.strip()


def test_every_item_is_probability_only_private_cli_experimental():
    for item in get_phase_8_probability_only_classifier_design():
        assert item.probability_only_required is True
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
    for item in get_phase_8_probability_only_classifier_design():
        assert item.runtime_output_verified is False
        assert item.notebook_value_parity_verified is False


def test_probability_only_allowed_fields_and_neutral_labels_are_recorded():
    merged = "\n".join(
        str(value)
        for item in get_phase_8_probability_only_classifier_design()
        for value in (
            item.allowed_output_fields,
            item.allowed_wording,
            item.expected_outputs,
            item.notes,
        )
    )

    assert "Class_A_probability" in merged
    assert "Class_B_probability" in merged
    assert "Class_C_probability" in merged
    assert "probability" in merged
    assert "score" in merged
    for marker in NON_NEUTRAL_LABEL_MARKERS:
        assert marker not in merged


def test_allowed_enums_and_safety_boundaries_are_enforced():
    base_kwargs = dict(
        id="bad",
        category="probability_output_schema",
        design_status="design_contract_only",
        source_context="bad",
        future_app_artifact_or_pattern="bad",
        probability_only_required=True,
        allowed_output_fields=("class_probability",),
        forbidden_output_fields=("certainty_label",),
        allowed_wording=("probability",),
        forbidden_wording=tuple(FORBIDDEN_WORDING),
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
        implementation_status="no_runtime_change_design_only",
        blocker="bad",
        recommended_next_action="bad",
        notes="bad",
    )

    with pytest.raises(ValueError, match="unsupported category"):
        ProbabilityOnlyClassifierDesignItem(**{**base_kwargs, "category": "bad"})
    with pytest.raises(ValueError, match="unsupported design_status"):
        ProbabilityOnlyClassifierDesignItem(**{**base_kwargs, "design_status": "bad"})
    with pytest.raises(ValueError, match="unsupported implementation_status"):
        ProbabilityOnlyClassifierDesignItem(**{**base_kwargs, "implementation_status": "bad"})
    with pytest.raises(ValueError, match="unsupported artifact_class"):
        ProbabilityOnlyClassifierDesignItem(**{**base_kwargs, "artifact_class": "bad"})
    with pytest.raises(ValueError, match="must require probability-only output"):
        ProbabilityOnlyClassifierDesignItem(
            **{**base_kwargs, "probability_only_required": False}
        )
    with pytest.raises(ValueError, match="must not target public_shared"):
        ProbabilityOnlyClassifierDesignItem(**{**base_kwargs, "target_mode": "public_shared"})
    with pytest.raises(ValueError, match="must remain filesystem_only"):
        ProbabilityOnlyClassifierDesignItem(**{**base_kwargs, "filesystem_only": False})
    with pytest.raises(ValueError, match="must remain cli_only"):
        ProbabilityOnlyClassifierDesignItem(**{**base_kwargs, "cli_only": False})
    with pytest.raises(ValueError, match="must require ENABLE_EXPERIMENTAL"):
        ProbabilityOnlyClassifierDesignItem(
            **{**base_kwargs, "requires_enable_experimental": False}
        )
    with pytest.raises(ValueError, match="must not be http_servable"):
        ProbabilityOnlyClassifierDesignItem(**{**base_kwargs, "http_servable": True})
    with pytest.raises(ValueError, match="must not be frontend_visible"):
        ProbabilityOnlyClassifierDesignItem(**{**base_kwargs, "frontend_visible": True})
    with pytest.raises(ValueError, match="must not be downloadable_via_api"):
        ProbabilityOnlyClassifierDesignItem(**{**base_kwargs, "downloadable_via_api": True})
    with pytest.raises(ValueError, match="must not be called by API"):
        ProbabilityOnlyClassifierDesignItem(**{**base_kwargs, "called_by_api": True})
    with pytest.raises(ValueError, match="must not be called by BackgroundTasks"):
        ProbabilityOnlyClassifierDesignItem(
            **{**base_kwargs, "called_by_background_tasks": True}
        )
    with pytest.raises(ValueError, match="must not be called by core orchestrator"):
        ProbabilityOnlyClassifierDesignItem(
            **{**base_kwargs, "called_by_core_orchestrator": True}
        )
    with pytest.raises(ValueError, match="notebook value parity must be false"):
        ProbabilityOnlyClassifierDesignItem(
            **{**base_kwargs, "notebook_value_parity_verified": True}
        )


def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    report_path = write_phase_8_probability_only_classifier_design_report(
        run_dir,
        "phase8-run",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == run_dir / "manifests" / "phase_8_probability_only_classifier_design.json"
    assert report_path.resolve().relative_to(run_dir.resolve())
    assert payload["schema_version"] == PHASE_8_PROBABILITY_ONLY_SCHEMA_VERSION
    assert payload["run_id"] == "phase8-run"
    assert payload["phase_8_runtime_changes"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["probability_only_contract"] is True
    assert set(payload["counts_by_category"]) == ALLOWED_CATEGORIES
    assert set(payload["counts_by_design_status"]) == ALLOWED_DESIGN_STATUSES
    assert set(payload["counts_by_implementation_status"]) == ALLOWED_IMPLEMENTATION_STATUSES
    assert set(payload["counts_by_artifact_class"]) == ALLOWED_ARTIFACT_CLASSES


def test_report_creates_no_raster_coordinate_map_model_csv_or_classifier_artifacts(tmp_path):
    run_dir = tmp_path / "run"
    write_phase_8_probability_only_classifier_design_report(run_dir, "phase8-no-artifacts")

    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]

    assert created == []


def test_module_does_not_add_train_infer_predict_classify_score_generate_or_export_functions():
    import app.pipeline.parity.probability_only_classifier_design as module

    forbidden_public_functions = [
        name
        for name in dir(module)
        if name.startswith(
            (
                "train_",
                "infer_",
                "predict_",
                "classify_",
                "score_",
                "generate_",
                "export_",
                "run_model_",
                "load_model_",
            )
        )
    ]

    assert forbidden_public_functions == []


def test_docs_do_not_claim_public_availability_for_probability_artifacts():
    contract = _read(PHASE_8_CONTRACT).lower()

    assert "does not expose classifier/model/probability artifacts through http" in contract
    assert "frontend_visible=false" in contract
    assert "downloadable_via_api=false" in contract
    assert "public availability" not in contract


def test_docs_and_module_avoid_forbidden_certainty_wording_outside_policy_list():
    merged = "\n".join([_read(PHASE_8_CONTRACT).lower(), _read(MODULE_PATH).lower()])
    merged = _strip_required_forbidden_wording_policy(merged)

    for term in FORBIDDEN_WORDING:
        assert re.search(rf"\b{re.escape(term)}\b", merged) is None


def test_docs_and_module_use_probability_only_wording_for_future_model_interpretation():
    merged = "\n".join([_read(PHASE_8_CONTRACT), _read(MODULE_PATH)])

    assert "probability-only" in merged.lower()
    assert "Class_A" in merged
    assert "Class_B" in merged
    assert "Class_C" in merged
    for marker in NON_NEUTRAL_LABEL_MARKERS:
        assert marker not in merged


def test_phase_8_contract_and_checklist_reference_exist():
    checklist = _read(FULL_CHECKLIST)

    assert PHASE_8_CONTRACT.exists()
    assert "Phase 8 — Probability-only ML classifier design" in checklist
    assert "docs/PHASE_8_PROBABILITY_ONLY_CLASSIFIER_DESIGN.md" in checklist
    assert "Phase 9 — End-to-end parity harness" in checklist
