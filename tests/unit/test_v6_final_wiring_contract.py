from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs" / "V6_FINAL_WIRING_1.md"


def _doc() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_final_wiring_doc_covers_backend_and_frontend_smoke() -> None:
    content = _doc()

    assert "Backend Smoke Checklist" in content
    assert "Frontend Smoke Checklist" in content
    assert "Manual Browser Smoke" in content
    assert "python -m pytest tests/unit/test_v6_app_flow.py -q" in content
    assert "python -m pytest tests/unit/test_v6_app_ui_contract.py -q" in content
    assert "npm run build" in content


def test_final_wiring_doc_covers_operator_gate_and_safe_metadata() -> None:
    content = _doc()

    assert "v6_package_flow_enabled=true" in content
    assert "operator_auth_trusted_proxy_enabled=true" in content
    assert "X-Operator-Roles: operator" in content
    assert "metadata-only" in content
    assert "generic denial" in content


def test_final_wiring_doc_lists_full_regression_suite() -> None:
    content = _doc()

    required = [
        "test_v6_app_flow.py",
        "test_v6_real_package.py",
        "test_v6_real_zones.py",
        "test_v6_real_reduce.py",
        "test_v6_real_scoring.py",
        "test_v6_real_gee_features.py",
        "test_v6_real_gee_runtime.py",
        "test_v6_generator_package.py",
        "test_notebook_safety.py",
    ]
    for item in required:
        assert item in content


def test_final_wiring_doc_has_production_safety_checks() -> None:
    content = _doc()

    assert "Keep v6_package_flow_enabled default-off" in content
    assert "provider request submission manual and separate" in content
    assert "desk-based shortlist/review aids" in content
    assert "Never expose rows" in content
