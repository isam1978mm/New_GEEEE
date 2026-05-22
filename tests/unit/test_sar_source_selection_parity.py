from __future__ import annotations

import csv
import json
from pathlib import Path

from app.services.sar_source_selection_parity import (
    SAR_SOURCE_SELECTION_PARITY_PREFIX,
    build_sar_source_selection_parity_report,
    write_sar_source_selection_parity_report,
)


def test_sar_source_selection_report_compares_metadata_and_stays_local_only(tmp_path: Path) -> None:
    app_run_dir = tmp_path / "data" / "runs" / "run-123"
    notebook_root = tmp_path / "NOTEBOOK_RUN"
    _write_app_sar_metadata(app_run_dir)
    _write_notebook_summary(notebook_root, asc_id="ASC_1", desc_id="DESC_2")

    report = build_sar_source_selection_parity_report(app_run_dir=app_run_dir, notebook_roots=[notebook_root])
    by_check = {row["check"]: row for row in report["rows"]}

    assert report["artifact_class"] == "FILESYSTEM_ONLY"
    assert report["local_only"] is True
    assert report["app_metadata_file"] == "qa/sar/sar_pair_diagnostics.json"
    assert report["notebook_metadata_files"] == [
        {"root_label": "NOTEBOOK_RUN", "relative_path": "SUMMARY_RADAR_demo.csv"}
    ]
    assert by_check["collection_id"]["status"] == "MATCH"
    assert by_check["date_window"]["status"] == "MATCH"
    assert by_check["image_identity"]["status"] == "MISMATCH"
    assert "selected Sentinel-1 image ids" in by_check["image_identity"]["recommended_next_action"]
    assert by_check["angle_incidence_mapping"]["status"] == "DOCUMENTED"
    assert "angle->incidence" in by_check["angle_incidence_mapping"]["evidence"]
    assert by_check["radar_linear_support_stack"]["status"] == "DOWNSTREAM_DIAGNOSTIC"

    serialized = json.dumps(report, sort_keys=True)
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    assert "bounds" not in serialized
    assert "crs_transform" not in serialized


def test_sar_source_selection_report_writer_outputs_json_and_csv(tmp_path: Path) -> None:
    app_run_dir = tmp_path / "data" / "runs" / "run-123"
    notebook_root = tmp_path / "NOTEBOOK_RUN"
    _write_app_sar_metadata(app_run_dir)
    _write_notebook_summary(notebook_root, asc_id="ASC_1", desc_id="DESC_1")

    json_path, csv_path = write_sar_source_selection_parity_report(
        app_run_dir=app_run_dir,
        notebook_roots=[notebook_root],
        output_dir=tmp_path / "reports",
    )

    assert json_path == tmp_path / "reports" / f"{SAR_SOURCE_SELECTION_PARITY_PREFIX}_run-123.json"
    assert csv_path == tmp_path / "reports" / f"{SAR_SOURCE_SELECTION_PARITY_PREFIX}_run-123.csv"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["summary"]["status_counts"]["MATCH"] >= 3
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["check"] for row in rows} >= {"collection_id", "image_identity", "angle_incidence_mapping"}


def _write_app_sar_metadata(app_run_dir: Path) -> None:
    path = app_run_dir / "qa" / "sar" / "sar_pair_diagnostics.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "stage": "sar_rtc",
                "artifact_class": "FILESYSTEM_ONLY",
                "local_only": True,
                "collection_id": "COPERNICUS/S1_GRD",
                "date_window": {"start_date": "2026-01-01", "end_date": "2026-03-01"},
                "selected_band_list": ["VV", "VH", "angle"],
                "output_band_list": ["VV_dB", "VH_dB", "logRatio_dB", "incidence"],
                "angle_incidence_mapping": {"notebook_band": "angle", "app_output_band": "incidence"},
                "processing_path": {
                    "local_dem_rtc": True,
                    "speckle_refined_lee_filtering": False,
                    "db_to_linear_to_db": True,
                    "grid_sampling": "sampleRectangle",
                },
                "pairs": [{"asc_id": "ASC_1", "desc_id": "DESC_1", "dt_hours": 1.0}],
            }
        ),
        encoding="utf-8",
    )


def _write_notebook_summary(notebook_root: Path, *, asc_id: str, desc_id: str) -> None:
    notebook_root.mkdir(parents=True, exist_ok=True)
    with (notebook_root / "SUMMARY_RADAR_demo.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "collection_id",
                "start_date",
                "end_date",
                "asc_id",
                "desc_id",
                "dt_hours",
                "band_name",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "collection_id": "COPERNICUS/S1_GRD",
                "start_date": "2026-01-01",
                "end_date": "2026-03-01",
                "asc_id": asc_id,
                "desc_id": desc_id,
                "dt_hours": "1.0",
                "band_name": "angle",
            }
        )
