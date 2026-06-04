import json

import pytest

from app.pipeline.parity.ai_ready_metal_hardness_recovery import (
    AIReadyMetalHardnessRecoveryItem,
    AI_READY_METAL_HARDNESS_RECOVERY_SCHEMA_VERSION,
    ALLOWED_IMPLEMENTATION_STATUSES,
    ALLOWED_SOURCE_STATUSES,
    get_ai_ready_metal_hardness_recovery_checklist,
    write_ai_ready_metal_hardness_recovery_report,
)


def _load_report(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_recovery_checklist_represents_metal_hardness_output():
    checklist = get_ai_ready_metal_hardness_recovery_checklist()

    assert [item.notebook_output for item in checklist] == [
        "AI_READY_640_Metal_Hardness.tif"
    ]


def test_source_status_is_conservative_and_evidence_backed():
    item = get_ai_ready_metal_hardness_recovery_checklist()[0]

    assert item.source_status == "partial_source_found"
    assert item.authoritative_source_available is False
    assert "notebooks/new.ipynb" in item.source_reference
    assert item.expected_input_outputs == ()
    assert item.implementation_status == "blocked_no_source_formula"


def test_recovery_flags_remain_false_and_not_public():
    item = get_ai_ready_metal_hardness_recovery_checklist()[0]

    assert item.runtime_output_verified is False
    assert item.notebook_value_parity_verified is False
    assert item.target_mode == "notebook_parity"
    assert item.target_mode != "public_shared"
    assert item.http_servable is False


def test_allowed_enums_are_enforced():
    assert "partial_source_found" in ALLOWED_SOURCE_STATUSES
    assert "blocked_no_source_formula" in ALLOWED_IMPLEMENTATION_STATUSES

    with pytest.raises(ValueError, match="unsupported source_status"):
        AIReadyMetalHardnessRecoveryItem(
            id="bad-source",
            notebook_output="AI_BAD.tif",
            family="bad",
            current_app_status="bad",
            source_status="not-valid",
            authoritative_source_available=False,
            source_reference="none",
            expected_input_outputs=(),
            expected_formula_summary="none",
            expected_dtype="unknown",
            expected_units="unknown",
            expected_nodata_policy="unknown",
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="bad",
            http_servable=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="deferred",
            blocker="bad",
            recommended_next_action="bad",
            notes="bad",
        )

    with pytest.raises(ValueError, match="unsupported implementation_status"):
        AIReadyMetalHardnessRecoveryItem(
            id="bad-impl",
            notebook_output="AI_BAD.tif",
            family="bad",
            current_app_status="bad",
            source_status="partial_source_found",
            authoritative_source_available=False,
            source_reference="none",
            expected_input_outputs=(),
            expected_formula_summary="none",
            expected_dtype="unknown",
            expected_units="unknown",
            expected_nodata_policy="unknown",
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="bad",
            http_servable=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="implemented",
            blocker="bad",
            recommended_next_action="bad",
            notes="bad",
        )


def test_report_json_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"

    report_path = write_ai_ready_metal_hardness_recovery_report(run_dir, "run-4h3")
    report = _load_report(report_path)

    assert report_path == run_dir / "manifests" / "ai_ready_metal_hardness_recovery_report.json"
    assert report_path.resolve().relative_to(run_dir.resolve())
    assert report["schema_version"] == AI_READY_METAL_HARDNESS_RECOVERY_SCHEMA_VERSION
    assert report["run_id"] == "run-4h3"
    assert report["phase_4h3_formula_changes"] is False
    assert len(report["items"]) == 1


def test_report_counts_and_items_use_allowed_enums(tmp_path):
    report = _load_report(
        write_ai_ready_metal_hardness_recovery_report(tmp_path / "run", "run-counts")
    )

    assert set(report["counts_by_source_status"]) == ALLOWED_SOURCE_STATUSES
    assert set(report["counts_by_implementation_status"]) == ALLOWED_IMPLEMENTATION_STATUSES
    for item in report["items"]:
        assert item["source_status"] in ALLOWED_SOURCE_STATUSES
        assert item["implementation_status"] in ALLOWED_IMPLEMENTATION_STATUSES


def test_report_writing_does_not_create_tif_or_npy_files(tmp_path):
    run_dir = tmp_path / "run"

    write_ai_ready_metal_hardness_recovery_report(run_dir, "run-no-rasters")
    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in {".tif", ".tiff", ".npy"}
    ]

    assert created == []
