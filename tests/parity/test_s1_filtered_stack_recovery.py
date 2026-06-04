import json

from app.pipeline.parity.s1_filtered_stack_recovery import (
    ALLOWED_IMPLEMENTATION_STATUSES,
    ALLOWED_SOURCE_STATUSES,
    S1_FILTERED_STACK_RECOVERY_SCHEMA_VERSION,
    get_s1_filtered_stack_recovery_checklist,
    write_s1_filtered_stack_recovery_report,
)


def _load_report(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_recovery_checklist_represents_s1_filtered_layers_stack_640_npy():
    checklist = get_s1_filtered_stack_recovery_checklist()

    assert len(checklist) == 1
    item = checklist[0]
    assert item.notebook_output == "S1_FILTERED_LAYERS_STACK_640.npy"
    assert item.family == "SAR/radar outputs"


def test_source_status_is_conservative_and_evidence_backed():
    item = get_s1_filtered_stack_recovery_checklist()[0]

    assert item.source_status == "exact_source_found"
    assert item.authoritative_source_available is True
    assert "notebooks/new.ipynb" in item.source_reference
    assert item.expected_input_outputs == (
        "S1_ASC_VV_Filtered_640.npy",
        "S1_ASC_VH_Filtered_640.npy",
        "S1_DESC_VV_Filtered_640.npy",
        "S1_DESC_VH_Filtered_640.npy",
    )
    assert item.expected_band_order == (
        "S1_ASC_VV_Filtered",
        "S1_ASC_VH_Filtered",
        "S1_DESC_VV_Filtered",
        "S1_DESC_VH_Filtered",
    )
    assert item.expected_shape_convention == "HWC"
    assert item.expected_dtype == "float32"


def test_recovery_flags_remain_unverified_and_not_public_shared():
    item = get_s1_filtered_stack_recovery_checklist()[0]

    assert item.runtime_output_verified is False
    assert item.notebook_value_parity_verified is False
    assert item.target_mode == "notebook_parity"
    assert item.target_mode != "public_shared"
    assert item.classification == "notebook-parity"


def test_allowed_enums_are_enforced_via_report_content(tmp_path):
    run_dir = tmp_path / "run"

    report_path = write_s1_filtered_stack_recovery_report(run_dir, "run-recovery")
    report = _load_report(report_path)
    item = report["items"][0]

    assert report["schema_version"] == S1_FILTERED_STACK_RECOVERY_SCHEMA_VERSION
    assert item["source_status"] in ALLOWED_SOURCE_STATUSES
    assert item["implementation_status"] in ALLOWED_IMPLEMENTATION_STATUSES


def test_recovery_report_json_writes_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"

    report_path = write_s1_filtered_stack_recovery_report(run_dir, "run-recovery-report")
    report = _load_report(report_path)

    assert report_path == run_dir / "manifests" / "s1_filtered_stack_recovery_report.json"
    assert report_path.resolve().relative_to(run_dir.resolve())
    assert report["run_id"] == "run-recovery-report"
    assert len(report["items"]) == 1


def test_recovery_report_does_not_create_npy_files(tmp_path):
    run_dir = tmp_path / "run"

    write_s1_filtered_stack_recovery_report(run_dir, "run-no-npy")
    created = [path for path in run_dir.rglob("*") if path.suffix.lower() == ".npy"]

    assert created == []
