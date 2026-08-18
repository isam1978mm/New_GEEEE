from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.services.operator_outputs import build_operator_output_tree, is_operator_tree_listable_relative_path

ROOT = Path(__file__).resolve().parents[2]
EXPORTS_TAB = ROOT / "frontend-v2" / "src" / "app" / "components" / "ExportsTab.tsx"
CLASSIFIER_STAGE = ROOT / "app" / "pipeline" / "stages" / "classifier.py"
RUN_QUALITY_STAGE = ROOT / "app" / "pipeline" / "stages" / "run_quality.py"


def test_exports_ui_clearly_separates_user_focus_and_candidate_focus() -> None:
    source = EXPORTS_TAB.read_text(encoding="utf-8")

    assert 'label: "User Focus"' in source
    assert 'label: "Candidate Focus"' in source
    assert 'normalized.startsWith("full_job/focus/")' in source
    assert 'normalized.startsWith("full_job/candidate_focus/")' in source
    assert "screening evidence, not physical confirmation" in source


def test_candidate_focus_is_downstream_and_classifier_source_is_not_coupled_to_it() -> None:
    classifier_source = CLASSIFIER_STAGE.read_text(encoding="utf-8")
    run_quality_source = RUN_QUALITY_STAGE.read_text(encoding="utf-8")

    assert "candidate_focus" not in classifier_source
    assert "run_candidate_focus_analysis" in run_quality_source
    assert "candidate_focus_inputs_ready" in run_quality_source


def test_operator_output_tree_lists_and_distinguishes_user_and_candidate_focus(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    run_id = "run-1"
    run_dir = data_dir / "runs" / run_id
    user_focus = run_dir / "full_job" / "focus" / "focus_zone_summary.json"
    candidate_focus = (
        run_dir
        / "full_job"
        / "candidate_focus"
        / "candidate_01_object_22"
        / "candidate_focus_summary.json"
    )
    classifier_summary = run_dir / "classifier" / "summary.json"
    for path, payload in (
        (user_focus, {"focus_kind": "user_focus"}),
        (candidate_focus, {"focus_kind": "candidate_focus", "candidate_id": "object_22"}),
        (classifier_summary, {"classifier_stage": "core"}),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    settings = Settings(data_dir=data_dir, database_path=data_dir / "test.db")
    tree = build_operator_output_tree(settings=settings, run_id=run_id)
    by_path = {item.relative_path: item for item in tree.outputs}

    assert by_path["full_job/focus/focus_zone_summary.json"].group == "user_focus"
    assert by_path[
        "full_job/candidate_focus/candidate_01_object_22/candidate_focus_summary.json"
    ].group == "candidate_focus"
    assert by_path["classifier/summary.json"].group == "classifier"


def test_candidate_focus_output_allowlist_keeps_sensitive_files_blocked() -> None:
    assert is_operator_tree_listable_relative_path(
        "full_job/candidate_focus/candidate_01_object_22/candidate_focus_summary.json"
    )
    assert is_operator_tree_listable_relative_path("full_job/focus/focus_zone_summary.json")
    assert not is_operator_tree_listable_relative_path(
        "full_job/candidate_focus/candidate_01_object_22/.env"
    )
    assert not is_operator_tree_listable_relative_path(
        "full_job/candidate_focus/candidate_01_object_22/credentials.json"
    )
