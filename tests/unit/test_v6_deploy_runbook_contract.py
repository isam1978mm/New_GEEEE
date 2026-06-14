from pathlib import Path


DOC = Path("docs/V6_DEPLOY_RUNBOOK_1.md")


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_deploy_runbook_records_current_status_and_post_freeze_scope() -> None:
    content = _doc()

    assert "V6-DEPLOY-RUNBOOK-1" in content
    assert "post-freeze deployment document" in content
    assert "V6-READY-FREEZE-1 -> done and tested" in content
    assert "does not change the frozen V6 workflow logic" in content


def test_deploy_runbook_requires_default_off_operator_enablement() -> None:
    content = _doc()

    assert "V6_PACKAGE_FLOW_ENABLED=true" in content
    assert "AUTH_ENABLED=true" in content
    assert "Operator auth must remain enabled" in content
    assert "Do not enable the package flow in a public unauthenticated environment" in content


def test_deploy_runbook_covers_smoke_and_rollback() -> None:
    content = _doc()

    assert "Backend Smoke Checklist" in content
    assert "Frontend Smoke Checklist" in content
    assert "Manual Operator Smoke" in content
    assert "Rollback Plan" in content
    assert "python -m pytest tests/unit/test_v6_app_flow.py -q" in content
    assert "npm run build" in content


def test_deploy_runbook_preserves_safety_rules() -> None:
    content = _doc()

    assert "generated package artifacts remain outside Git" in content
    assert "frontend shows metadata only" in content
    assert "denied requests do not read package input" in content
    assert "provider ordering remains separate and manual" in content
    assert "post-freeze changes must be versioned or bug-fix scoped" in content
