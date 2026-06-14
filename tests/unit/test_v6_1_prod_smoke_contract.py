from pathlib import Path


DOC = Path("docs/V6_1_PROD_SMOKE_1.md")


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_prod_smoke_records_frozen_baseline_and_no_behavior_change() -> None:
    content = _doc()

    assert "V6.1-PROD-SMOKE-1" in content
    assert "does not change frozen V6 generation" in content
    assert "V6-READY-FREEZE-1 -> done and tested" in content
    assert "V6-DEPLOY-RUNBOOK-1 -> done and tested" in content
    assert "V6-E2E-1 -> done and tested" in content
    assert "V6.1-PLAN-1 -> done and tested" in content


def test_prod_smoke_requires_operator_approval_and_default_off_gate() -> None:
    content = _doc()

    assert "Operator Approval Required" in content
    assert "operator approves the target environment" in content
    assert "V6_PACKAGE_FLOW_ENABLED=true only for the approved smoke window" in content
    assert "V6_PACKAGE_FLOW_ENABLED=false" in content
    assert "auth is enabled" in content


def test_prod_smoke_includes_preflight_commands() -> None:
    content = _doc()

    assert "python -m pytest tests/unit/test_v6_ready_freeze_contract.py -q" in content
    assert "python -m pytest tests/unit/test_v6_deploy_runbook_contract.py -q" in content
    assert "python -m pytest tests/unit/test_v6_e2e_contract.py -q" in content
    assert "python -m pytest tests/unit/test_v6_1_plan_contract.py -q" in content
    assert "npm run build" in content
    assert "npm run e2e:v6" in content


def test_prod_smoke_preserves_private_output_safety() -> None:
    content = _doc()

    assert "UI does not show candidate rows" in content
    assert "UI does not show spatial payload bodies" in content
    assert "logs did not include bearer token" in content
    assert "logs did not include real coordinates" in content
    assert "no generated ZIP or payload file is committed to Git" in content
    assert "provider ordering" in content


def test_prod_smoke_includes_safe_evidence_template_and_failure_handling() -> None:
    content = _doc()

    assert "Safe Evidence Record Template" in content
    assert "Payload count" in content
    assert "ZIP entry count" in content
    assert "Do not record" in content
    assert "generated CSV/GeoJSON/report bodies" in content
    assert "Failure Handling" in content
    assert "Open a versioned bug-fix task" in content


def test_prod_smoke_names_next_observability_track() -> None:
    content = _doc()

    assert "V6.1-OBSERVABILITY-1" in content
    assert "safe metadata-only counters and logs" in content
