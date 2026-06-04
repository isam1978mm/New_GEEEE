import json

import pytest

from app.pipeline.parity.semantic_raster_recovery import (
    ALLOWED_IMPLEMENTATION_STATUSES,
    ALLOWED_SOURCE_STATUSES,
    SEMANTIC_RASTER_RECOVERY_SCHEMA_VERSION,
    SemanticRasterRecoveryItem,
    filter_semantic_raster_recovery_by_status,
    get_semantic_raster_recovery_inventory,
    write_semantic_raster_recovery_report,
)


def _inventory_by_id():
    return {item.id: item for item in get_semantic_raster_recovery_inventory()}


def _load_report(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_inventory_includes_or_explicitly_links_secret_and_report_outputs():
    inventory = get_semantic_raster_recovery_inventory()
    names = {item.notebook_output_or_pattern for item in inventory}

    assert {
        "AI_READY_640_Secret_Gold_Halo.tif",
        "AI_READY_640_Secret_Silver_Oxide.tif",
        "AI_READY_640_Secret_Tunnel_Ceiling.tif",
        "AI_READY_640_Secret_Thermal_Inertia.tif",
        "AI_READY_640_Secret_Chemical_Protector.tif",
        "AI_READY_640_Secret_Hidden_Doors.tif",
        "REPORT_640_Pottery_Report.tif",
        "REPORT_640_Mass_Report.tif",
        "REPORT_640_FINAL_Zero_Point_Targets.tif",
    }.issubset(names)


def test_inventory_includes_broader_ai_beh_and_ai_ready_patterns():
    names = {item.notebook_output_or_pattern for item in get_semantic_raster_recovery_inventory()}

    assert "AI_BEH_*" in names
    assert "AI_READY_*" in names


def test_inventory_includes_hypercube_and_final_tesla_semantic_linkage():
    names = {item.notebook_output_or_pattern for item in get_semantic_raster_recovery_inventory()}

    assert "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif" in names
    assert "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy" in names
    assert "semantic/report rasters used by FINAL_TESLA_V7_2_HYPERCUBE*" in names


def test_covered_outputs_are_marked_covered_by_existing_contract():
    items = _inventory_by_id()

    covered_ids = {
        "secret_gold_halo",
        "secret_silver_oxide",
        "secret_tunnel_ceiling",
        "secret_thermal_inertia",
        "secret_chemical_protector",
        "secret_hidden_doors",
        "report_pottery",
        "report_mass",
        "report_zero_point_targets",
        "hypercube_res25_tif",
        "hypercube_res25_npy",
    }

    for item_id in covered_ids:
        assert items[item_id].covered_by_existing_contract is True
        assert items[item_id].source_status == "covered_by_existing_contract"
        assert items[item_id].implementation_status == "covered_no_action_needed"


def test_uncovered_outputs_are_not_marked_implemented():
    for item in get_semantic_raster_recovery_inventory():
        if item.covered_by_existing_contract:
            continue
        assert item.implementation_status != "covered_no_action_needed"
        assert item.notebook_value_parity_verified is False


def test_runtime_and_value_parity_flags_remain_false_and_not_public():
    for item in get_semantic_raster_recovery_inventory():
        assert item.runtime_output_verified is False
        assert item.notebook_value_parity_verified is False
        assert item.target_mode != "public_shared"
        assert item.http_servable is False


def test_filtering_by_implementation_status_returns_expected_subset():
    blocked = filter_semantic_raster_recovery_by_status("blocked_no_source_formula")

    assert {item.id for item in blocked} >= {
        "ai_ready_magnetic_anomaly",
        "ai_ready_em_anomaly",
        "ai_ready_metal_hardness",
    }


def test_allowed_enums_are_enforced():
    assert "covered_by_existing_contract" in ALLOWED_SOURCE_STATUSES
    assert "covered_no_action_needed" in ALLOWED_IMPLEMENTATION_STATUSES

    with pytest.raises(ValueError, match="unsupported source_status"):
        SemanticRasterRecoveryItem(
            id="bad-source",
            notebook_output_or_pattern="AI_BAD.tif",
            family="bad",
            current_app_status="bad",
            source_status="not-valid",
            authoritative_source_available=False,
            source_reference="none",
            covered_by_existing_contract=False,
            existing_contract_reference=None,
            known_stage_file=None,
            known_stage_class=None,
            expected_input_outputs=(),
            expected_formula_summary="none",
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
        SemanticRasterRecoveryItem(
            id="bad-impl",
            notebook_output_or_pattern="AI_BAD.tif",
            family="bad",
            current_app_status="bad",
            source_status="partial_source_found",
            authoritative_source_available=False,
            source_reference="none",
            covered_by_existing_contract=False,
            existing_contract_reference=None,
            known_stage_file=None,
            known_stage_class=None,
            expected_input_outputs=(),
            expected_formula_summary="none",
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


def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"

    report_path = write_semantic_raster_recovery_report(run_dir, "run-4j")
    report = _load_report(report_path)

    assert report_path == run_dir / "manifests" / "semantic_raster_recovery_report.json"
    assert report_path.resolve().relative_to(run_dir.resolve())
    assert report["schema_version"] == SEMANTIC_RASTER_RECOVERY_SCHEMA_VERSION
    assert report["run_id"] == "run-4j"
    assert report["phase_4j_formula_changes"] is False
    assert len(report["items"]) == len(get_semantic_raster_recovery_inventory())


def test_report_counts_and_items_use_allowed_enums(tmp_path):
    report = _load_report(
        write_semantic_raster_recovery_report(tmp_path / "run", "run-counts")
    )

    assert set(report["counts_by_source_status"]) == ALLOWED_SOURCE_STATUSES
    assert set(report["counts_by_implementation_status"]) == ALLOWED_IMPLEMENTATION_STATUSES
    for item in report["items"]:
        assert item["source_status"] in ALLOWED_SOURCE_STATUSES
        assert item["implementation_status"] in ALLOWED_IMPLEMENTATION_STATUSES


def test_report_writing_does_not_create_tif_or_npy_files(tmp_path):
    run_dir = tmp_path / "run"

    write_semantic_raster_recovery_report(run_dir, "run-no-rasters")
    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in {".tif", ".tiff", ".npy"}
    ]

    assert created == []


def test_phase_4j_module_does_not_add_compute_generate_alias_copy_or_raster_math_functions():
    import app.pipeline.parity.semantic_raster_recovery as module

    forbidden_public_functions = [
        name
        for name in dir(module)
        if name.startswith(("compute_", "generate_", "alias_", "copy_", "resample_"))
    ]

    assert forbidden_public_functions == []
