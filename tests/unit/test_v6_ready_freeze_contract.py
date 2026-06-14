from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs" / "V6_READY_FREEZE_1.md"


def _doc() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_ready_freeze_doc_records_frozen_statuses() -> None:
    content = _doc()

    required_statuses = [
        "V6-SCAFFOLD-1 -> done and tested",
        "V6-REAL-GEE-1 -> done and tested",
        "V6-REAL-GEE-2 -> done and tested",
        "V6-REAL-SCORING-1 -> done and tested",
        "V6-REAL-REDUCE-1 -> done and tested",
        "V6-REAL-ZONES-1 -> done and tested",
        "V6-REAL-PACKAGE-1 -> done and tested",
        "V6-APP-FLOW-1 -> done and tested",
        "V6-APP-UI-1 -> done and tested",
        "V6-FINAL-WIRING-1 -> done and tested",
    ]
    for status in required_statuses:
        assert status in content


def test_ready_freeze_doc_records_regression_closeout() -> None:
    content = _doc()

    required_tests = [
        "test_v6_app_ui_contract.py -> 4 passed",
        "test_v6_final_wiring_contract.py -> 4 passed",
        "test_v6_app_flow.py -> 5 passed",
        "test_v6_real_package.py -> 4 passed",
        "test_v6_real_zones.py -> 7 passed",
        "test_v6_real_reduce.py -> 6 passed",
        "test_v6_real_scoring.py -> 6 passed",
        "test_v6_real_gee_features.py -> 5 passed",
        "test_v6_real_gee_runtime.py -> 6 passed",
        "test_v6_generator_package.py -> 7 passed",
        "test_notebook_safety.py -> 7 passed",
        "frontend-v2 npm run build -> passed",
    ]
    for item in required_tests:
        assert item in content


def test_ready_freeze_doc_preserves_safety_rules() -> None:
    content = _doc()

    assert "keep the V6 package flow default-off" in content
    assert "provider request submission manual and separate" in content
    assert "do not expose candidate rows" in content
    assert "do not weaken notebook safety tests" in content
    assert "Not allowed in UI/API metadata surfaces" in content


def test_ready_freeze_doc_says_followups_must_be_versioned() -> None:
    content = _doc()

    assert "Post-freeze: only make versioned follow-up changes" in content
    assert "do not change V6 scoring math without a new versioned task" in content
