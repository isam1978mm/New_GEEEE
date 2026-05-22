from __future__ import annotations

import json

from app.db.models.enums import ArtifactClass
from app.services.full_job_local_output_report import (
    FULL_JOB_LOCAL_OUTPUT_REPORT_NAME,
    build_full_job_local_output_comparison_report,
    write_full_job_local_output_comparison_report,
)


def test_full_job_local_output_report_has_required_sections_and_on_hold_families(tmp_path) -> None:
    report = build_full_job_local_output_comparison_report()

    assert report["report_type"] == "full_job_local_output_comparison"
    assert report["artifact_class"] == ArtifactClass.FILESYSTEM_ONLY.value
    assert report["local_only"] is True
    assert "covered_outputs" in report
    assert "missing_approved_outputs" in report
    assert "intentionally_excluded_outputs" in report
    assert "on_hold_outputs" in report
    assert report["missing_approved_outputs"] == []

    covered_ids = {entry["family_id"] for entry in report["covered_outputs"]}
    on_hold_ids = {entry["family_id"] for entry in report["on_hold_outputs"]}
    excluded_ids = {entry["family_id"] for entry in report["intentionally_excluded_outputs"]}

    assert "gps_comparison_local" in covered_ids
    assert "reference_locator_local" in covered_ids
    assert "full_job_comparison_local" in covered_ids
    assert "training_scaffolding" in on_hold_ids
    assert "deep_learning_inference" in on_hold_ids
    assert "broken_model_build_cells" in on_hold_ids
    assert "raw_notebook_runtime_mirrors" in excluded_ids

    report_path = write_full_job_local_output_comparison_report(tmp_path)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_path == tmp_path / FULL_JOB_LOCAL_OUTPUT_REPORT_NAME
    assert payload["summary"]["missing_approved_output_family_count"] == 0


def test_full_job_local_output_report_does_not_embed_local_paths_or_coordinates() -> None:
    report = build_full_job_local_output_comparison_report()
    serialized = json.dumps(report, sort_keys=True)

    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    assert "35.59499" not in serialized
    assert "36.12694" not in serialized
    assert "full_job/gps/gps_point_comparison.json" in serialized
