import json

from app.pipeline.parity.missing_rasters import (
    ALLOWED_IMPLEMENTATION_STATUSES,
    MISSING_RASTER_REPORT_SCHEMA_VERSION,
    filter_missing_raster_registry_by_status,
    get_missing_raster_registry,
    write_missing_raster_report,
)


REQUIRED_NOTEBOOK_OUTPUTS = {
    "curv_laplacian_640.tif",
    "curv_plan_640.tif",
    "curv_profile_640.tif",
    "S1_ASC_VV_Filtered_640.tif",
    "S1_ASC_VH_Filtered_640.tif",
    "S1_DESC_VV_Filtered_640.tif",
    "S1_DESC_VH_Filtered_640.tif",
    "S1_ASC_VV_Filtered_640.npy",
    "S1_ASC_VH_Filtered_640.npy",
    "S1_DESC_VV_Filtered_640.npy",
    "S1_DESC_VH_Filtered_640.npy",
    "PAN_LS_Panchromatic_640.tif",
    "PAN_S2_Panchromatic_10m_640.tif",
    "PAN_LS_Panchromatic_640.npy",
    "PAN_S2_Panchromatic_10m_640.npy",
    "PAN_LAYERS_STACK_640.npy",
    "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif",
    "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy",
    "S1_FILTERED_LAYERS_STACK_640.npy",
    "AI_BEH_*",
    "AI_READY_*",
    "REPORT_640_Pottery_Report.tif",
    "REPORT_640_Mass_Report.tif",
    "REPORT_640_FINAL_Zero_Point_Targets.tif",
    "AI_READY_640_Secret_Gold_Halo.tif",
    "AI_READY_640_Secret_Silver_Oxide.tif",
    "AI_READY_640_Secret_Tunnel_Ceiling.tif",
    "AI_READY_640_Secret_Thermal_Inertia.tif",
    "AI_READY_640_Secret_Chemical_Protector.tif",
    "AI_READY_640_Secret_Hidden_Doors.tif",
}


def _registry_by_id():
    return {item.id: item for item in get_missing_raster_registry()}


def test_registry_contains_all_required_phase_4a_families_and_outputs():
    registry = get_missing_raster_registry()
    all_outputs = {
        output
        for item in registry
        for output in item.notebook_paths_or_patterns
    }

    assert len(registry) == 7
    assert REQUIRED_NOTEBOOK_OUTPUTS.issubset(all_outputs)


def test_secret_and_report_stage_classifications_are_not_clean_core():
    items = _registry_by_id()

    assert (
        items["secret_layer_runtime_value_parity"].classification
        == "notebook-parity semantic raster stage"
    )
    assert (
        items["report_640_runtime_value_parity"].classification
        == "notebook-parity report/semantic raster stage"
    )


def test_runtime_and_value_parity_default_unverified():
    for item in get_missing_raster_registry():
        assert item.runtime_output_verified is False
        assert item.notebook_value_parity_verified is False


def test_no_item_defaults_to_public_shared():
    for item in get_missing_raster_registry():
        assert item.target_mode != "public_shared"


def test_filtering_by_implementation_status():
    missing_items = filter_missing_raster_registry_by_status("no_source_equivalent_identified")

    assert {item.id for item in missing_items} >= {
        "sar_asc_desc_filtered_support_stacks",
        "panchromatic_optical_support_outputs",
    }


def test_required_statuses_are_restricted_to_allowed_enum():
    assert ALLOWED_IMPLEMENTATION_STATUSES == {
        "missing",
        "partial",
        "source_writer_exists_unverified",
        "no_source_equivalent_identified",
        "requires_reference_notebook_output",
        "requires_formula_reconstruction",
        "requires_external_dependency",
        "deferred_to_later_phase",
    }
    for item in get_missing_raster_registry():
        assert item.implementation_status in ALLOWED_IMPLEMENTATION_STATUSES


def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"

    report_path = write_missing_raster_report(run_dir, "run-4a")
    parsed = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path.resolve().relative_to(run_dir.resolve())
    assert report_path == run_dir / "manifests" / "missing_raster_families_report.json"
    assert parsed["schema_version"] == MISSING_RASTER_REPORT_SCHEMA_VERSION
    assert parsed["run_id"] == "run-4a"
    assert len(parsed["items"]) == len(get_missing_raster_registry())
    assert parsed["counts_by_status"]["source_writer_exists_unverified"] == 2
    assert parsed["counts_by_status"]["no_source_equivalent_identified"] == 2


def test_report_writing_does_not_create_raster_files(tmp_path):
    run_dir = tmp_path / "run"

    write_missing_raster_report(run_dir, "run-no-rasters")
    raster_like_files = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in {".tif", ".npy"}
    ]

    assert raster_like_files == []
