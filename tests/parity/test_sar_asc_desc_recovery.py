import json

import pytest

import app.pipeline.parity.sar_asc_desc_recovery as recovery
from app.pipeline.parity.sar_asc_desc_recovery import (
    ALLOWED_IMPLEMENTATION_STATUSES,
    ALLOWED_SOURCE_STATUSES,
    SAR_ASC_DESC_RECOVERY_SCHEMA_VERSION,
    SarAscDescRecoveryItem,
    get_sar_asc_desc_recovery_checklist,
    write_sar_asc_desc_recovery_report,
)


REQUIRED_OUTPUTS = {
    "S1_ASC_VV_Filtered_640.tif",
    "S1_ASC_VH_Filtered_640.tif",
    "S1_DESC_VV_Filtered_640.tif",
    "S1_DESC_VH_Filtered_640.tif",
    "S1_ASC_VV_Filtered_640.npy",
    "S1_ASC_VH_Filtered_640.npy",
    "S1_DESC_VV_Filtered_640.npy",
    "S1_DESC_VH_Filtered_640.npy",
}


def test_all_asc_desc_outputs_are_represented():
    checklist = get_sar_asc_desc_recovery_checklist()

    assert {item.notebook_output for item in checklist} == REQUIRED_OUTPUTS
    assert len(checklist) == 8


def test_items_are_private_notebook_parity_and_unverified():
    for item in get_sar_asc_desc_recovery_checklist():
        assert item.family == "SAR/radar outputs"
        assert item.target_mode == "notebook_parity"
        assert item.target_mode != "public_shared"
        assert item.classification == "notebook-parity"
        assert item.runtime_output_verified is False
        assert item.notebook_value_parity_verified is False


def test_exact_notebook_source_is_recorded_but_final_sar_is_not_equivalent():
    for item in get_sar_asc_desc_recovery_checklist():
        assert item.source_status == "exact_source_found"
        assert item.authoritative_source_available is True
        assert "notebooks/new.ipynb" in item.source_reference
        assert "final RTC" in item.current_app_status
        assert "not equivalent" in item.current_app_status
        assert item.source_status != "existing_app_equivalent_found"
        assert item.implementation_status == "requires_reference_output"


def test_required_inputs_and_metadata_are_locked_for_each_output():
    for item in get_sar_asc_desc_recovery_checklist():
        assert "Sentinel-1 collection" in item.required_inputs
        assert "orbit pass" in item.required_inputs
        assert "VV/VH bands" in item.required_inputs
        assert "filtering/masking" in item.required_inputs
        assert "median/composite logic" in item.required_inputs
        assert "RTC or pre-RTC status" in item.required_inputs
        assert "scaling/unit convention" in item.required_inputs
        assert "GRID alignment" in item.required_inputs
        assert "nodata policy" in item.required_inputs
        assert "CRS" in item.required_metadata
        assert "transform" in item.required_metadata
        assert "dtype" in item.required_metadata


def test_allowed_source_status_enum_is_enforced():
    assert ALLOWED_SOURCE_STATUSES == {
        "exact_source_found",
        "partial_source_found",
        "no_source_found",
        "existing_app_equivalent_found",
        "unknown_needs_reference",
    }

    with pytest.raises(ValueError, match="unsupported source_status"):
        SarAscDescRecoveryItem(
            id="bad",
            notebook_output="bad.tif",
            family="SAR/radar outputs",
            current_app_status="missing",
            source_status="invented_source",
            authoritative_source_available=False,
            source_reference="none",
            known_stage_file=None,
            known_stage_class=None,
            required_inputs=(),
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="notebook-parity",
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="requires_source_reconstruction",
            blocker="bad status",
            recommended_next_action="fix status",
            notes="test",
        )


def test_allowed_implementation_status_enum_is_enforced():
    assert ALLOWED_IMPLEMENTATION_STATUSES == {
        "ready_for_implementation_after_reference",
        "requires_reference_output",
        "requires_source_reconstruction",
        "blocked_no_source_formula",
        "blocked_dependency_missing",
        "deferred",
    }

    with pytest.raises(ValueError, match="unsupported implementation_status"):
        SarAscDescRecoveryItem(
            id="bad",
            notebook_output="bad.tif",
            family="SAR/radar outputs",
            current_app_status="missing",
            source_status="no_source_found",
            authoritative_source_available=False,
            source_reference="none",
            known_stage_file=None,
            known_stage_class=None,
            required_inputs=(),
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="notebook-parity",
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="implemented",
            blocker="bad status",
            recommended_next_action="fix status",
            notes="test",
        )


def test_verified_flags_and_public_shared_are_rejected():
    with pytest.raises(ValueError, match="must not target public_shared"):
        SarAscDescRecoveryItem(
            id="bad",
            notebook_output="bad.tif",
            family="SAR/radar outputs",
            current_app_status="missing",
            source_status="exact_source_found",
            authoritative_source_available=True,
            source_reference="notebooks/new.ipynb",
            known_stage_file=None,
            known_stage_class=None,
            required_inputs=(),
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="public_shared",
            classification="notebook-parity",
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="requires_reference_output",
            blocker="bad mode",
            recommended_next_action="fix mode",
            notes="test",
        )

    with pytest.raises(ValueError, match="does not verify runtime output presence"):
        SarAscDescRecoveryItem(
            id="bad-runtime",
            notebook_output="bad.tif",
            family="SAR/radar outputs",
            current_app_status="missing",
            source_status="exact_source_found",
            authoritative_source_available=True,
            source_reference="notebooks/new.ipynb",
            known_stage_file=None,
            known_stage_class=None,
            required_inputs=(),
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="notebook-parity",
            runtime_output_verified=True,
            notebook_value_parity_verified=False,
            implementation_status="requires_reference_output",
            blocker="bad runtime",
            recommended_next_action="fix runtime",
            notes="test",
        )


def test_report_json_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"

    report_path = write_sar_asc_desc_recovery_report(run_dir, "run-sar")
    parsed = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == run_dir / "manifests" / "sar_asc_desc_recovery_report.json"
    assert report_path.resolve().relative_to(run_dir.resolve())
    assert parsed["schema_version"] == SAR_ASC_DESC_RECOVERY_SCHEMA_VERSION
    assert parsed["run_id"] == "run-sar"
    assert {item["notebook_output"] for item in parsed["items"]} == REQUIRED_OUTPUTS
    assert parsed["counts_by_source_status"]["exact_source_found"] == 8
    assert parsed["counts_by_implementation_status"]["requires_reference_output"] == 8
    assert parsed["phase_4e_sar_math_changes"] is False


def test_report_path_traversal_is_blocked(tmp_path):
    with pytest.raises(ValueError, match="path traversal"):
        write_sar_asc_desc_recovery_report(
            tmp_path / "run",
            "run-bad-path",
            report_relative_path="../escape.json",
        )


def test_report_writing_does_not_create_raster_or_npy_files(tmp_path):
    run_dir = tmp_path / "run"

    write_sar_asc_desc_recovery_report(run_dir, "run-no-rasters")
    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in {".tif", ".tiff", ".npy"}
    ]

    assert created == []


def test_phase_4e_module_does_not_add_sar_math_or_alias_implementation():
    forbidden_public_functions = [
        name for name in dir(recovery)
        if name.startswith(("compute_", "write_", "alias_", "copy_", "generate_"))
        and name != "write_sar_asc_desc_recovery_report"
    ]

    assert forbidden_public_functions == []
