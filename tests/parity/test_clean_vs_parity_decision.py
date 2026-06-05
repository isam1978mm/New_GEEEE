import json
import re
from pathlib import Path

from app.pipeline.parity.clean_vs_parity_decision import (
    ALLOWED_CATEGORIES,
    ALLOWED_DECISIONS,
    ALLOWED_IMPLEMENTATION_STATUSES,
    PHASE_10_CLEAN_VS_PARITY_SCHEMA_VERSION,
    get_phase_10_clean_vs_parity_decisions,
    write_phase_10_clean_vs_parity_decision_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "app" / "pipeline" / "parity" / "clean_vs_parity_decision.py"
CONTRACT_PATH = REPO_ROOT / "docs" / "PHASE_10_CLEAN_VS_PARITY_DECISION.md"
FULL_CHECKLIST = REPO_ROOT / "docs" / "NOTEBOOK_PARITY_FULL_CHECKLIST.md"

REQUIRED_CATEGORIES = {
    "clean_app_core_outputs",
    "private_notebook_parity_outputs",
    "verifier_only_outputs",
    "source_recovered_not_implemented_outputs",
    "private_coordinate_map_outputs",
    "experimental_classifier_outputs",
    "probability_only_model_outputs",
    "future_reference_driven_implementation_candidates",
    "public_api_and_frontend_boundary",
    "artifact_serving_boundary",
}

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

FORBIDDEN_SUFFIXES = {
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
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_all_required_phase_10_categories_are_present():
    items = get_phase_10_clean_vs_parity_decisions()

    assert {item.category for item in items} == REQUIRED_CATEGORIES
    assert REQUIRED_CATEGORIES <= ALLOWED_CATEGORIES


def test_each_item_has_valid_decision_and_implementation_status():
    items = get_phase_10_clean_vs_parity_decisions()

    for item in items:
        assert item.decision in ALLOWED_DECISIONS
        assert item.implementation_status in ALLOWED_IMPLEMENTATION_STATUSES


def test_each_item_has_nonblank_source_contracts_or_notes():
    items = get_phase_10_clean_vs_parity_decisions()

    for item in items:
        assert item.source_contracts or item.notes.strip()


def test_private_parity_items_are_filesystem_only_and_not_http_servable():
    items = {
        item.category: item for item in get_phase_10_clean_vs_parity_decisions()
    }

    for category in {
        "private_notebook_parity_outputs",
        "verifier_only_outputs",
        "source_recovered_not_implemented_outputs",
    }:
        item = items[category]
        assert item.filesystem_only is True
        assert item.http_servable is False


def test_coordinate_map_items_are_filesystem_only_and_not_http_servable():
    item = {
        entry.category: entry for entry in get_phase_10_clean_vs_parity_decisions()
    }["private_coordinate_map_outputs"]

    assert item.filesystem_only is True
    assert item.http_servable is False
    assert item.frontend_visible is False
    assert item.downloadable_via_api is False


def test_classifier_and_model_items_stay_experimental_and_not_called_by_runtime_paths():
    items = {
        item.category: item for item in get_phase_10_clean_vs_parity_decisions()
    }

    for category in {
        "experimental_classifier_outputs",
        "probability_only_model_outputs",
    }:
        item = items[category]
        assert item.experimental_allowed is True
        assert item.requires_enable_experimental is True
        assert item.called_by_api is False
        assert item.called_by_background_tasks is False
        assert item.called_by_core_orchestrator is False


def test_probability_only_items_do_not_allow_certainty_wording():
    item = {
        entry.category: entry for entry in get_phase_10_clean_vs_parity_decisions()
    }["probability_only_model_outputs"]
    merged = " ".join(
        [item.blocker.lower(), item.recommended_next_action.lower(), item.notes.lower()]
    )

    assert "probability" in merged or "score" in merged
    for term in FORBIDDEN_WORDING:
        assert re.search(rf"\b{re.escape(term)}\b", merged) is None


def test_public_api_and_frontend_boundary_locks_private_artifacts_out_of_http_surfaces():
    item = {
        entry.category: entry for entry in get_phase_10_clean_vs_parity_decisions()
    }["public_api_and_frontend_boundary"]

    assert item.http_servable is False
    assert item.frontend_visible is False
    assert item.downloadable_via_api is False


def test_artifact_serving_boundary_states_no_phase_10_policy_change():
    item = {
        entry.category: entry for entry in get_phase_10_clean_vs_parity_decisions()
    }["artifact_serving_boundary"]

    merged = " ".join(
        [item.blocker.lower(), item.recommended_next_action.lower(), item.notes.lower()]
    )
    assert "no phase 10 serving-policy change is allowed" in merged


def test_runtime_and_notebook_value_parity_flags_remain_false():
    items = get_phase_10_clean_vs_parity_decisions()

    assert all(item.runtime_output_verified is False for item in items)
    assert all(item.notebook_value_parity_verified is False for item in items)


def test_report_writes_and_parses_and_path_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"

    report_path = write_phase_10_clean_vs_parity_decision_report(
        run_dir=run_dir,
        run_id="phase10-report",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path.resolve().relative_to(run_dir.resolve())
    assert payload["schema_version"] == PHASE_10_CLEAN_VS_PARITY_SCHEMA_VERSION
    assert payload["run_id"] == "phase10-report"
    assert payload["phase_10_runtime_changes"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["artifact_serving_changes"] is False


def test_report_creates_no_forbidden_artifact_files(tmp_path):
    run_dir = tmp_path / "run"

    write_phase_10_clean_vs_parity_decision_report(
        run_dir=run_dir,
        run_id="phase10-no-artifacts",
    )

    created = [
        path for path in run_dir.rglob("*") if path.suffix.lower() in FORBIDDEN_SUFFIXES
    ]
    assert created == []


def test_docs_and_code_do_not_introduce_forbidden_certainty_wording():
    merged = "\n".join([_read(MODULE_PATH).lower(), _read(CONTRACT_PATH).lower()])

    for term in FORBIDDEN_WORDING:
        assert re.search(rf"\b{re.escape(term)}\b", merged) is None


def test_checklist_does_not_introduce_phase_11():
    text = _read(FULL_CHECKLIST)

    assert "[ ] Phase 11" not in text
    assert "[x] Phase 11" not in text
