from pathlib import Path

DOC = Path("docs/V6_1_E2E_EXPAND_1_PLAN.md")


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_plan_declares_planning_only_and_frozen_boundary() -> None:
    content = _doc()
    assert "V6.1-E2E-EXPAND-1-PLAN" in content
    assert "Planning/checklist only" in content
    assert "Do not implement Playwright changes in this task" in content
    assert "frozen V6 checkpoint remains unchanged" in content
    assert "no frozen V6 generation changes" in content


def test_plan_lists_required_scenarios() -> None:
    content = _doc()
    required = [
        "Scenario 0 - existing success path baseline",
        "Scenario 1 - disabled rollback state",
        "Scenario 2 - unauthenticated denied state",
        "Scenario 3 - wrong role denied state",
        "Scenario 4 - run not authorized state",
        "Scenario 5 - unavailable package state",
        "Scenario 6 - invalid package input state",
        "Scenario 7 - retrieval failure state",
        "Scenario 8 - observability-safe assertions",
    ]
    for phrase in required:
        assert phrase in content


def test_plan_preserves_private_output_safety() -> None:
    content = _doc()
    required = [
        "No real spatial values in tests",
        "No real V6 artifacts in repo",
        "No auth secrets in tests or logs",
        "No private rows or spatial payload bodies rendered in UI",
        "Only safe metadata assertions are allowed",
    ]
    for phrase in required:
        assert phrase in content


def test_plan_has_implementation_rules_before_code_changes() -> None:
    content = _doc()
    required = [
        "Create a separate Playwright spec or clearly separated describe block",
        "Use mocks only",
        "Use exact locators",
        "Use safe fake run IDs and safe fake filenames",
        "Keep all payload bodies synthetic and non-spatial",
        "Do not weaken the existing success-path E2E",
    ]
    for phrase in required:
        assert phrase in content


def test_plan_has_validation_commands_and_next_track() -> None:
    content = _doc()
    required = [
        "python -m pytest tests/unit/test_v6_e2e_contract.py -q",
        "python -m pytest tests/unit/test_v6_1_e2e_expand_plan_contract.py -q",
        "npm run e2e:v6",
        "V6.1-E2E-EXPAND-1-IMPLEMENT",
    ]
    for phrase in required:
        assert phrase in content
