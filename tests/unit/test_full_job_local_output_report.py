from __future__ import annotations

import json

from app.db.models.enums import ArtifactClass
from app.services.full_job_local_output_report import (
    FULL_JOB_LOCAL_OUTPUT_REPORT_NAME,
    APPROVED_OUTPUT_FAMILIES,
    build_full_job_local_output_comparison_report,
    write_full_job_local_output_comparison_report,
)


def test_full_job_local_output_report_has_required_sections_and_on_hold_families(tmp_path) -> None:
    report = build_full_job_local_output_comparison_report(tmp_path)

    assert report["report_type"] == "full_job_local_output_comparison"
    assert report["artifact_class"] == ArtifactClass.FILESYSTEM_ONLY.value
    assert report["local_only"] is True
    assert report["scan_mode"] == "actual_run_directory"
    assert report["scan_root_included"] is False
    assert "approved_output_families" in report
    assert "covered_outputs" in report
    assert "missing_approved_outputs" in report
    assert "intentionally_excluded_outputs" in report
    assert "on_hold_outputs" in report

    assert report["covered_outputs"] == []
    assert report["summary"]["approved_output_family_count"] == len(APPROVED_OUTPUT_FAMILIES)
    assert report["summary"]["covered_output_family_count"] == 0
    assert report["summary"]["missing_approved_output_family_count"] == len(APPROVED_OUTPUT_FAMILIES)
    assert report["summary"]["missing_expected_file_count"] > 0

    missing_ids = {entry["family_id"] for entry in report["missing_approved_outputs"]}
    on_hold_ids = {entry["family_id"] for entry in report["on_hold_outputs"]}
    excluded_ids = {entry["family_id"] for entry in report["intentionally_excluded_outputs"]}

    assert "gps_comparison_local" in missing_ids
    assert "reference_locator_local" in missing_ids
    assert "full_job_comparison_local" in missing_ids
    assert "training_scaffolding" in on_hold_ids
    assert "deep_learning_inference" in on_hold_ids
    assert "broken_model_build_cells" in on_hold_ids
    assert "raw_notebook_runtime_mirrors" in excluded_ids

    report_path = write_full_job_local_output_comparison_report(tmp_path)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_path == tmp_path / FULL_JOB_LOCAL_OUTPUT_REPORT_NAME
    assert payload["summary"]["covered_output_family_count"] == 0
    assert payload["summary"]["missing_expected_file_count"] > 0


def test_full_job_local_output_report_marks_family_covered_only_when_files_exist(tmp_path) -> None:
    for relative_path in (
        "grid_manifest.json",
        "dem.tif",
        "dem.npy",
        "QA/grid_dem/grid_guard_summary.json",
        "QA/grid_dem/dem_audit_summary.json",
    ):
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok", encoding="utf-8")

    report = build_full_job_local_output_comparison_report(tmp_path)

    covered_ids = {entry["family_id"] for entry in report["covered_outputs"]}
    assert "grid_dem_core" in covered_ids
    grid_family = next(entry for entry in report["approved_output_families"] if entry["family_id"] == "grid_dem_core")
    assert grid_family["status"] == "covered"
    assert grid_family["missing_outputs"] == []
    assert grid_family["present_output_count"] == len(grid_family["outputs"])


def test_full_job_local_output_report_marks_partial_family_and_lists_missing_files(tmp_path) -> None:
    (tmp_path / "grid_manifest.json").write_text("ok", encoding="utf-8")
    (tmp_path / "dem.tif").write_text("ok", encoding="utf-8")

    report = build_full_job_local_output_comparison_report(tmp_path)

    partial_family = next(entry for entry in report["approved_output_families"] if entry["family_id"] == "grid_dem_core")
    assert partial_family["status"] == "partial"
    assert partial_family["present_outputs"] == ["grid_manifest.json", "dem.tif"]
    assert "dem.npy" in partial_family["missing_outputs"]
    assert "qa/grid_dem/dem_audit_summary.json" in partial_family["missing_outputs"]
    assert partial_family in report["missing_approved_outputs"]
    assert report["summary"]["partial_output_family_count"] >= 1


def test_full_job_local_output_report_supports_pattern_outputs(tmp_path) -> None:
    for relative_path in (
        "hypercube.tif",
        "hypercube.npy",
        "hypercube_band_order.csv",
        "hypercube_band_stats.csv",
        "hypercube_norm_params.csv",
        "QA/parity/hypercube_audit.csv",
        "pca_anomaly.tif",
        "pca_eigenvalues.json",
        "QA/parity/parity_qa_summary.json",
        "objects_index.csv",
        "clusters_summary.csv",
        "objects/object_mask.npy",
        "objects/object_patches/object_001.npy",
        "alignment_qa.json",
        "alignment_audit.json",
        "alignment_mask_selection.json",
        "QA/alignment/alignment_summary_redacted.json",
    ):
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok", encoding="utf-8")

    report = build_full_job_local_output_comparison_report(tmp_path)
    family = next(entry for entry in report["approved_output_families"] if entry["family_id"] == "hypercube_pca_objects_alignment")

    assert family["status"] == "covered"
    assert "objects/object_patches/object_###.npy" in family["present_outputs"]
    assert family["missing_outputs"] == []


def test_full_job_local_output_report_does_not_embed_local_paths_or_coordinates(tmp_path) -> None:
    report = build_full_job_local_output_comparison_report(tmp_path)
    serialized = json.dumps(report, sort_keys=True)

    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    assert "35.59499" not in serialized
    assert "36.12694" not in serialized
    assert "npy_radar_bands/VV_dB.npy" in serialized
    assert "full_job/gps/gps_point_comparison.json" in serialized
