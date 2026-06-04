import json

from app.pipeline.parity.hypercube_res25_recovery import (
    ALLOWED_IMPLEMENTATION_STATUSES,
    ALLOWED_SOURCE_STATUSES,
    HYPERCUBE_RES25_RECOVERY_SCHEMA_VERSION,
    get_hypercube_res25_recovery_checklist,
    write_hypercube_res25_recovery_report,
)


def _load_report(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_recovery_checklist_represents_both_2p5m_hypercube_outputs():
    checklist = get_hypercube_res25_recovery_checklist()

    assert [item.notebook_output for item in checklist] == [
        "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif",
        "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy",
    ]


def test_source_status_and_expected_fields_are_evidence_backed():
    checklist = get_hypercube_res25_recovery_checklist()

    for item in checklist:
        assert item.source_status == "exact_source_found"
        assert item.authoritative_source_available is True
        assert "notebooks/new.ipynb" in item.source_reference
        assert item.expected_input_outputs == ("FINAL_TESLA_V7_2_HYPERCUBE.tif",)
        assert item.expected_band_order == (
            "AI_READY_640_Secret_Gold_Halo",
            "AI_READY_640_Secret_Silver_Oxide",
            "AI_READY_640_Secret_Tunnel_Ceiling",
            "AI_READY_640_Secret_Thermal_Inertia",
            "AI_READY_640_Secret_Chemical_Protector",
            "AI_READY_640_Secret_Hidden_Doors",
            "REPORT_640_FINAL_Zero_Point_Targets",
            "REPORT_640_Mass_Report",
            "REPORT_640_Pottery_Report",
        )
        assert item.expected_band_count == 9
        assert item.expected_pixel_size_m == 2.5
        assert item.expected_resampling_method == "cubic"
        assert item.expected_dtype == "float32"


def test_shape_and_layout_expectations_are_explicit():
    checklist = {item.notebook_output: item for item in get_hypercube_res25_recovery_checklist()}

    assert checklist["FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy"].expected_shape_convention == "CHW"
    assert checklist["FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif"].expected_geotiff_band_layout == (
        "multi-band GeoTIFF with preserved source band order and band descriptions when available"
    )


def test_recovery_flags_remain_unverified_and_not_public_shared():
    for item in get_hypercube_res25_recovery_checklist():
        assert item.runtime_output_verified is False
        assert item.notebook_value_parity_verified is False
        assert item.target_mode == "notebook_parity"
        assert item.target_mode != "public_shared"
        assert item.classification == "notebook-parity"


def test_allowed_enums_are_enforced_via_report_content(tmp_path):
    run_dir = tmp_path / "run"

    report_path = write_hypercube_res25_recovery_report(run_dir, "run-recovery")
    report = _load_report(report_path)

    assert report["schema_version"] == HYPERCUBE_RES25_RECOVERY_SCHEMA_VERSION
    assert len(report["items"]) == 2
    for item in report["items"]:
        assert item["source_status"] in ALLOWED_SOURCE_STATUSES
        assert item["implementation_status"] in ALLOWED_IMPLEMENTATION_STATUSES


def test_recovery_report_json_writes_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"

    report_path = write_hypercube_res25_recovery_report(run_dir, "run-recovery-report")
    report = _load_report(report_path)

    assert report_path == run_dir / "manifests" / "hypercube_res25_recovery_report.json"
    assert report_path.resolve().relative_to(run_dir.resolve())
    assert report["run_id"] == "run-recovery-report"
    assert len(report["items"]) == 2


def test_recovery_report_does_not_create_tif_or_npy_files(tmp_path):
    run_dir = tmp_path / "run"

    write_hypercube_res25_recovery_report(run_dir, "run-no-arrays")
    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in {".tif", ".tiff", ".npy"}
    ]

    assert created == []
