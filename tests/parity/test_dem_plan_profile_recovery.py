import json

import pytest

import app.pipeline.parity.dem_plan_profile_recovery as recovery
from app.pipeline.parity.dem_plan_profile_recovery import (
    ALLOWED_FORMULA_STATUSES,
    ALLOWED_IMPLEMENTATION_STATUSES,
    DEM_PLAN_PROFILE_RECOVERY_SCHEMA_VERSION,
    DemPlanProfileRecoveryItem,
    get_dem_plan_profile_recovery_checklist,
    write_dem_plan_profile_recovery_report,
)


REQUIRED_OUTPUTS = {
    "curv_plan_640.tif",
    "curv_profile_640.tif",
}


def _items_by_output():
    return {
        item.notebook_output: item
        for item in get_dem_plan_profile_recovery_checklist()
    }


def test_plan_and_profile_outputs_are_represented():
    checklist = get_dem_plan_profile_recovery_checklist()

    assert {item.notebook_output for item in checklist} == REQUIRED_OUTPUTS
    assert len(checklist) == 2


def test_plan_profile_items_are_private_notebook_parity():
    for item in get_dem_plan_profile_recovery_checklist():
        assert item.family == "DEM/terrain outputs"
        assert item.target_mode == "notebook_parity"
        assert item.target_mode != "public_shared"
        assert item.classification == "notebook-parity"
        assert item.requires_coordinates is False
        assert item.probability_only_required is False


def test_runtime_outputs_are_present_but_notebook_value_parity_is_not_verified():
    for item in get_dem_plan_profile_recovery_checklist():
        assert item.runtime_output_verified is True
        assert item.notebook_value_parity_verified is False


def test_authoritative_notebook_formula_source_is_recorded_and_reference_is_pending():
    items = _items_by_output()

    for output in REQUIRED_OUTPUTS:
        item = items[output]
        assert item.formula_status == "authoritative_formula_found"
        assert item.authoritative_formula_available is True
        assert "notebooks/new.ipynb" in item.notes
        assert item.implementation_status == "runtime_implemented_reference_pending"
        assert "frozen reference" in item.blocker


def test_candidate_formula_authoritative_requires_authoritative_formula():
    for item in get_dem_plan_profile_recovery_checklist():
        assert item.candidate_formula_authoritative is True
        assert item.authoritative_formula_available is True

    with pytest.raises(ValueError, match="candidate formula cannot be authoritative"):
        DemPlanProfileRecoveryItem(
            id="bad",
            notebook_output="bad.tif",
            family="DEM/terrain outputs",
            current_app_status="missing",
            formula_status="no_formula_found",
            authoritative_formula_available=False,
            candidate_formula_documented=True,
            candidate_formula_authoritative=True,
            required_evidence=("source notebook cell",),
            required_reference_outputs=("bad.tif",),
            required_metadata=("CRS",),
            target_mode="notebook_parity",
            classification="notebook-parity",
            requires_coordinates=False,
            probability_only_required=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="blocked_no_source_formula",
            blocker="missing formula",
            recommended_next_action="recover source",
            notes="test",
        )


def test_allowed_formula_status_enum_is_enforced():
    assert ALLOWED_FORMULA_STATUSES == {
        "no_formula_found",
        "candidate_non_authoritative_formula_only",
        "authoritative_formula_found",
        "unknown_needs_reference",
    }

    with pytest.raises(ValueError, match="unsupported formula_status"):
        DemPlanProfileRecoveryItem(
            id="bad",
            notebook_output="bad.tif",
            family="DEM/terrain outputs",
            current_app_status="missing",
            formula_status="invented_formula",
            authoritative_formula_available=False,
            candidate_formula_documented=False,
            candidate_formula_authoritative=False,
            required_evidence=(),
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="notebook-parity",
            requires_coordinates=False,
            probability_only_required=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="blocked_no_source_formula",
            blocker="bad status",
            recommended_next_action="fix status",
            notes="test",
        )


def test_allowed_implementation_status_enum_is_enforced():
    assert ALLOWED_IMPLEMENTATION_STATUSES == {
        "blocked_no_source_formula",
        "blocked_missing_reference_output",
        "blocked_missing_metadata_contract",
        "ready_for_formula_implementation_after_evidence",
        "runtime_implemented_reference_pending",
        "deferred",
    }

    with pytest.raises(ValueError, match="unsupported implementation_status"):
        DemPlanProfileRecoveryItem(
            id="bad",
            notebook_output="bad.tif",
            family="DEM/terrain outputs",
            current_app_status="missing",
            formula_status="no_formula_found",
            authoritative_formula_available=False,
            candidate_formula_documented=False,
            candidate_formula_authoritative=False,
            required_evidence=(),
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="notebook-parity",
            requires_coordinates=False,
            probability_only_required=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="implemented",
            blocker="bad status",
            recommended_next_action="fix status",
            notes="test",
        )


def test_report_json_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"

    report_path = write_dem_plan_profile_recovery_report(run_dir, "run-plan-profile")
    parsed = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == run_dir / "manifests" / "dem_plan_profile_recovery_report.json"
    assert report_path.resolve().relative_to(run_dir.resolve())
    assert parsed["schema_version"] == DEM_PLAN_PROFILE_RECOVERY_SCHEMA_VERSION
    assert parsed["run_id"] == "run-plan-profile"
    assert {item["notebook_output"] for item in parsed["items"]} == REQUIRED_OUTPUTS
    assert parsed["counts_by_formula_status"]["authoritative_formula_found"] == 2
    assert parsed["counts_by_implementation_status"]["runtime_implemented_reference_pending"] == 2
    assert parsed["phase_4d3_formula_changes"] is False


def test_report_path_traversal_is_blocked(tmp_path):
    with pytest.raises(ValueError, match="path traversal"):
        write_dem_plan_profile_recovery_report(
            tmp_path / "run",
            "run-bad-path",
            report_relative_path="../escape.json",
        )


def test_report_writing_does_not_create_raster_or_npy_files(tmp_path):
    run_dir = tmp_path / "run"

    write_dem_plan_profile_recovery_report(run_dir, "run-no-rasters")
    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in {".tif", ".tiff", ".npy"}
    ]

    assert created == []


def test_phase_4d3_module_does_not_add_formula_or_alias_implementation():
    forbidden_public_functions = [
        name for name in dir(recovery)
        if name.startswith(("compute_", "alias_", "copy_"))
        or name.startswith("write_georeferenced")
    ]

    assert forbidden_public_functions == []
