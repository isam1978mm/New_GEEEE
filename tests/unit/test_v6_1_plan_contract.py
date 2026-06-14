from pathlib import Path


DOC = Path("docs/V6_1_PLAN_1.md")


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_v6_1_plan_records_post_freeze_boundary() -> None:
    content = _doc()

    assert "V6.1-PLAN-1" in content
    assert "does not change frozen V6 generation" in content
    assert "V6-READY-FREEZE-1 -> done and tested" in content
    assert "V6-DEPLOY-RUNBOOK-1 -> done and tested" in content
    assert "V6-E2E-1 -> done and tested" in content


def test_v6_1_plan_requires_versioned_followups() -> None:
    content = _doc()

    assert "use a versioned task ID" in content
    assert "state whether it is docs-only, test-only, frontend-only, backend-only, or algorithmic" in content
    assert "include rollback instructions" in content
    assert "include safety assertions" in content


def test_v6_1_plan_prioritizes_safe_tracks_first() -> None:
    content = _doc()

    assert "Tier 1 — Production Readiness" in content
    assert "V6.1-PROD-SMOKE-1" in content
    assert "V6.1-OBSERVABILITY-1" in content
    assert "V6.1-E2E-EXPAND-1" in content
    assert "V6.1-PACKAGE-SCHEMA-1" in content


def test_v6_1_plan_preserves_private_output_safety() -> None:
    content = _doc()

    assert "no generated V6 package artifacts are committed" in content
    assert "no private rows are exposed in public API responses" in content
    assert "no spatial payload bodies are exposed in frontend panels" in content
    assert "no real coordinates are added to repo docs/tests/fixtures" in content
    assert "denied requests do not read private package inputs" in content
    assert "provider ordering remains manual" in content


def test_v6_1_plan_names_first_recommended_next_step() -> None:
    content = _doc()

    assert "Recommended first implementation track" in content
    assert "V6.1-PROD-SMOKE-1: run and document an operator-approved production-like smoke test" in content
