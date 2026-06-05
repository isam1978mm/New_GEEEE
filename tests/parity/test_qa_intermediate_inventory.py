import json
import re
from pathlib import Path

import pytest

from app.pipeline.parity.qa_intermediate_inventory import (
    ALLOWED_CATEGORIES,
    ALLOWED_IMPLEMENTATION_STATUSES,
    ALLOWED_PARITY_STATUSES,
    ALLOWED_SOURCE_STATUSES,
    PHASE_5_QA_INTERMEDIATE_SCHEMA_VERSION,
    QaIntermediateInventoryItem,
    get_phase_5_qa_intermediate_inventory,
    write_phase_5_qa_intermediate_inventory_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_5_CONTRACT = REPO_ROOT / "docs" / "PHASE_5_QA_INTERMEDIATE_PARITY_CONTRACT.md"
FULL_CHECKLIST = REPO_ROOT / "docs" / "NOTEBOOK_PARITY_FULL_CHECKLIST.md"
MODULE_PATH = REPO_ROOT / "app" / "pipeline" / "parity" / "qa_intermediate_inventory.py"

FORBIDDEN_WORDING = {
    "confirmed",
    "proven",
    "dig target",
    "definitely",
}


def _inventory_by_id():
    return {item.id: item for item in get_phase_5_qa_intermediate_inventory()}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_inventory_includes_all_required_categories():
    categories = {item.category for item in get_phase_5_qa_intermediate_inventory()}

    assert categories == {
        "qa_manifests",
        "provenance_reports",
        "alignment_checks",
        "sar_provenance",
        "pca_stack_qa",
        "grid_consistency_reports",
    }


def test_each_item_uses_valid_enums_and_nonblank_actions():
    for item in get_phase_5_qa_intermediate_inventory():
        assert item.category in ALLOWED_CATEGORIES
        assert item.source_status in ALLOWED_SOURCE_STATUSES
        assert item.parity_status in ALLOWED_PARITY_STATUSES
        assert item.implementation_status in ALLOWED_IMPLEMENTATION_STATUSES
        assert item.blocker.strip() or item.recommended_next_action.strip()


def test_items_remain_private_and_not_public():
    for item in get_phase_5_qa_intermediate_inventory():
        assert item.target_mode != "public_shared"
        assert item.http_servable is False


def test_runtime_and_notebook_value_parity_flags_remain_false():
    for item in get_phase_5_qa_intermediate_inventory():
        assert item.runtime_output_verified is False
        assert item.notebook_value_parity_verified is False


def test_allowed_enums_are_enforced():
    with pytest.raises(ValueError, match="unsupported category"):
        QaIntermediateInventoryItem(
            id="bad",
            category="bad_category",
            notebook_artifact_or_pattern="bad",
            current_app_artifact_or_pattern="bad",
            source_status="exact_source_found",
            current_app_status="bad",
            parity_status="inventory_only",
            expected_inputs=(),
            expected_outputs=(),
            required_reference_artifacts=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="bad",
            http_servable=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="implementation_deferred",
            blocker="bad",
            recommended_next_action="bad",
            notes="bad",
        )

    with pytest.raises(ValueError, match="unsupported source_status"):
        QaIntermediateInventoryItem(
            id="bad",
            category="qa_manifests",
            notebook_artifact_or_pattern="bad",
            current_app_artifact_or_pattern="bad",
            source_status="bad",
            current_app_status="bad",
            parity_status="inventory_only",
            expected_inputs=(),
            expected_outputs=(),
            required_reference_artifacts=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="bad",
            http_servable=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="implementation_deferred",
            blocker="bad",
            recommended_next_action="bad",
            notes="bad",
        )

    with pytest.raises(ValueError, match="unsupported parity_status"):
        QaIntermediateInventoryItem(
            id="bad",
            category="qa_manifests",
            notebook_artifact_or_pattern="bad",
            current_app_artifact_or_pattern="bad",
            source_status="exact_source_found",
            current_app_status="bad",
            parity_status="bad",
            expected_inputs=(),
            expected_outputs=(),
            required_reference_artifacts=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="bad",
            http_servable=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="implementation_deferred",
            blocker="bad",
            recommended_next_action="bad",
            notes="bad",
        )

    with pytest.raises(ValueError, match="unsupported implementation_status"):
        QaIntermediateInventoryItem(
            id="bad",
            category="qa_manifests",
            notebook_artifact_or_pattern="bad",
            current_app_artifact_or_pattern="bad",
            source_status="exact_source_found",
            current_app_status="bad",
            parity_status="inventory_only",
            expected_inputs=(),
            expected_outputs=(),
            required_reference_artifacts=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="bad",
            http_servable=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="bad",
            blocker="bad",
            recommended_next_action="bad",
            notes="bad",
        )


def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    report_path = write_phase_5_qa_intermediate_inventory_report(run_dir, "phase5-run")
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == run_dir / "manifests" / "phase_5_qa_intermediate_inventory.json"
    assert report_path.resolve().relative_to(run_dir.resolve())
    assert payload["schema_version"] == PHASE_5_QA_INTERMEDIATE_SCHEMA_VERSION
    assert payload["run_id"] == "phase5-run"
    assert payload["phase_5_runtime_changes"] is False
    assert set(payload["counts_by_category"]) == ALLOWED_CATEGORIES
    assert set(payload["counts_by_parity_status"]) == ALLOWED_PARITY_STATUSES
    assert set(payload["counts_by_implementation_status"]) == ALLOWED_IMPLEMENTATION_STATUSES


def test_report_creates_no_binary_or_coordinate_artifacts(tmp_path):
    run_dir = tmp_path / "run"
    write_phase_5_qa_intermediate_inventory_report(run_dir, "phase5-no-binary")

    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in {".tif", ".tiff", ".npy", ".geojson", ".kmz"}
    ]

    assert created == []


def test_module_does_not_add_compute_generate_alias_or_copy_functions():
    import app.pipeline.parity.qa_intermediate_inventory as module

    forbidden_public_functions = [
        name
        for name in dir(module)
        if name.startswith(("compute_", "generate_", "alias_", "copy_", "resample_"))
    ]

    assert forbidden_public_functions == []


def test_docs_and_module_avoid_forbidden_certainty_wording():
    merged = "\n".join(
        [
            _read(PHASE_5_CONTRACT).lower(),
            _read(FULL_CHECKLIST).lower(),
            _read(MODULE_PATH).lower(),
        ]
    )

    for term in FORBIDDEN_WORDING:
        assert re.search(rf"\b{re.escape(term)}\b", merged) is None


def test_phase_5_contract_and_checklist_reference_exist():
    assert PHASE_5_CONTRACT.exists()
    assert "Phase 5 — QA and intermediate parity" in _read(FULL_CHECKLIST)
    assert "docs/PHASE_5_QA_INTERMEDIATE_PARITY_CONTRACT.md" in _read(FULL_CHECKLIST)


def test_inventory_items_have_expected_parity_statuses():
    items = _inventory_by_id()

    assert items["phase5_qa_manifests"].parity_status == "verifier_needed"
    assert items["phase5_provenance_reports"].parity_status == "inventory_only"
    assert items["phase5_alignment_checks"].parity_status == "verifier_needed"
    assert items["phase5_sar_provenance"].parity_status == "reference_needed"
    assert items["phase5_pca_stack_qa"].parity_status == "verifier_needed"
    assert items["phase5_grid_consistency_reports"].parity_status == "inventory_only"
