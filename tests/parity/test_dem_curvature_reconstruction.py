import json

import pytest

import app.pipeline.parity.dem_curvature_reconstruction as reconstruction
from app.pipeline.parity.dem_curvature_reconstruction import (
    ALLOWED_FORMULA_STATUSES,
    ALLOWED_IMPLEMENTATION_STATUSES,
    DEM_CURVATURE_RECONSTRUCTION_SCHEMA_VERSION,
    DemCurvatureReconstructionItem,
    get_dem_curvature_reconstruction_registry,
    write_dem_curvature_reconstruction_report,
)


REQUIRED_OUTPUTS = {
    "curv_laplacian_640.tif",
    "curv_plan_640.tif",
    "curv_profile_640.tif",
}


def _registry_by_output():
    return {
        item.notebook_output: item
        for item in get_dem_curvature_reconstruction_registry()
    }


def test_all_three_curvature_outputs_are_represented():
    registry = get_dem_curvature_reconstruction_registry()

    assert {item.notebook_output for item in registry} == REQUIRED_OUTPUTS
    assert len(registry) == 3


def test_required_classification_and_mode_are_private_notebook_parity():
    for item in get_dem_curvature_reconstruction_registry():
        assert item.family == "DEM/terrain outputs"
        assert item.target_mode == "notebook_parity"
        assert item.target_mode != "public_shared"
        assert item.classification == "notebook-parity"
        assert item.requires_coordinates is False
        assert item.probability_only_required is False


def test_runtime_and_notebook_value_parity_are_not_marked_verified():
    for item in get_dem_curvature_reconstruction_registry():
        assert item.runtime_output_verified is False
        assert item.notebook_value_parity_verified is False


def test_formula_status_for_each_required_output_is_conservative():
    items = _registry_by_output()

    assert items["curv_laplacian_640.tif"].formula_status == "existing_app_equivalent_found"
    assert items["curv_plan_640.tif"].formula_status == "no_formula_found"
    assert items["curv_profile_640.tif"].formula_status == "no_formula_found"


def test_allowed_formula_status_enum_is_enforced():
    assert ALLOWED_FORMULA_STATUSES == {
        "exact_formula_found",
        "approximate_formula_found",
        "no_formula_found",
        "existing_app_equivalent_found",
        "unknown_needs_reference",
    }

    with pytest.raises(ValueError, match="unsupported formula_status"):
        DemCurvatureReconstructionItem(
            id="bad",
            notebook_output="bad.tif",
            family="DEM/terrain outputs",
            current_app_status="missing",
            formula_status="invented_formula",
            formula_source="none",
            known_stage_file=None,
            known_stage_class=None,
            required_inputs=(),
            target_mode="notebook_parity",
            classification="notebook-parity",
            requires_coordinates=False,
            probability_only_required=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="requires_formula_reconstruction",
            blocker="bad status",
            recommended_next_action="fix status",
            notes="test",
        )


def test_allowed_implementation_status_enum_is_enforced():
    assert ALLOWED_IMPLEMENTATION_STATUSES == {
        "ready_for_implementation",
        "requires_reference_output",
        "requires_formula_reconstruction",
        "blocked_no_source_formula",
        "blocked_dependency_missing",
    }

    with pytest.raises(ValueError, match="unsupported implementation_status"):
        DemCurvatureReconstructionItem(
            id="bad",
            notebook_output="bad.tif",
            family="DEM/terrain outputs",
            current_app_status="missing",
            formula_status="no_formula_found",
            formula_source="none",
            known_stage_file=None,
            known_stage_class=None,
            required_inputs=(),
            target_mode="notebook_parity",
            classification="notebook-parity",
            requires_coordinates=False,
            probability_only_required=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="implemented_anyway",
            blocker="bad status",
            recommended_next_action="fix status",
            notes="test",
        )


def test_report_json_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"

    report_path = write_dem_curvature_reconstruction_report(run_dir, "run-curvature")
    parsed = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == run_dir / "manifests" / "dem_curvature_reconstruction_report.json"
    assert report_path.resolve().relative_to(run_dir.resolve())
    assert parsed["schema_version"] == DEM_CURVATURE_RECONSTRUCTION_SCHEMA_VERSION
    assert parsed["run_id"] == "run-curvature"
    assert {item["notebook_output"] for item in parsed["items"]} == REQUIRED_OUTPUTS
    assert parsed["counts_by_formula_status"]["no_formula_found"] == 2
    assert parsed["counts_by_formula_status"]["existing_app_equivalent_found"] == 1


def test_report_path_traversal_is_blocked(tmp_path):
    with pytest.raises(ValueError, match="path traversal"):
        write_dem_curvature_reconstruction_report(
            tmp_path / "run",
            "run-bad-path",
            report_relative_path="../escape.json",
        )


def test_report_writing_does_not_create_raster_or_npy_files(tmp_path):
    run_dir = tmp_path / "run"

    write_dem_curvature_reconstruction_report(run_dir, "run-no-rasters")
    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in {".tif", ".tiff", ".npy"}
    ]

    assert created == []


def test_phase_4d_module_does_not_add_formula_implementation():
    public_compute_functions = [
        name for name in dir(reconstruction)
        if name.startswith("compute_") or name.startswith("write_georeferenced")
    ]

    assert public_compute_functions == []
