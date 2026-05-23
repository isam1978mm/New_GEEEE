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


def test_sar_source_selection_report_parses_qa_s1_master_units_json(tmp_path: Path) -> None:
    app_run_dir = tmp_path / "data" / "runs" / "run-123"
    notebook_root = tmp_path / "NOTEBOOK_RUN"
    _write_app_sar_metadata(
        app_run_dir,
        pairs=[
            {"asc_id": "ASC_A", "desc_id": "DESC_A", "dt_hours": 1.0},
            {"asc_id": "ASC_B", "desc_id": "DESC_B", "dt_hours": 2.0},
        ],
        source_filters={"max_orbit_dt_days": 12, "max_pair_dt_hours": 48},
    )
    _write_notebook_master_units(
        notebook_root,
        pairs_used=[
            {"asc_id": "ASC_A", "desc_id": "DESC_A", "dt_hours": 1.0},
            {"asc_id": "ASC_B", "desc_id": "DESC_B", "dt_hours": 2.0},
        ],
        orbit_window_days=12,
        pair_cap_hours=48,
        master_id="ASC_A",
    )

    report = build_sar_source_selection_parity_report(app_run_dir=app_run_dir, notebook_roots=[notebook_root])
    by_check = {row["check"]: row for row in report["rows"]}

    assert report["notebook_metadata_files"] == [
        {"root_label": "NOTEBOOK_RUN", "relative_path": "QA/QA_S1_MASTER_UNITS.json"}
    ]
    assert by_check["image_identity"]["status"] == "MATCH"
    assert by_check["image_identity"]["notebook_value"] == "ASC_A>DESC_A|ASC_B>DESC_B"
    assert by_check["image_identity"]["app_value"] == "ASC_A>DESC_A|ASC_B>DESC_B"
    assert by_check["orbit_pairing"]["status"] == "MATCH"
    assert by_check["orbit_pairing"]["notebook_value"] == "1|2"
    assert by_check["vv_vh_pair_count"]["status"] == "MATCH"
    assert by_check["vv_vh_pair_count"]["notebook_value"] == "2"
    assert by_check["source_parameters"]["status"] == "MATCH"
    assert by_check["source_parameters"]["notebook_value"] == '{"orbit_window_days":"12","pair_cap_hours":"48"}'
    assert by_check["source_parameters"]["app_value"] == '{"orbit_window_days":"12","pair_cap_hours":"48"}'
    assert by_check["master_id"]["status"] == "NOTEBOOK_ONLY"
    assert by_check["master_id"]["notebook_value"] == "ASC_A"

    serialized = json.dumps(report, sort_keys=True)
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    assert "bounds" not in serialized
    assert "coordinates" not in serialized


def test_sar_source_selection_report_distinguishes_cell25_pixel_profile_from_cell21_qa(tmp_path: Path) -> None:
    app_run_dir = tmp_path / "data" / "runs" / "run-123"
    notebook_root = tmp_path / "NOTEBOOK_RUN"
    _write_app_sar_metadata(
        app_run_dir,
        pairs=[{"asc_id": "ASC_CELL25", "desc_id": "DESC_CELL25", "dt_hours": 12.0}],
        source_filters={
            "selection_profile": "cell25_pixel_export",
            "max_orbit_dt_days": 9,
            "max_pair_dt_hours": 36,
        },
    )
    _write_notebook_master_units(
        notebook_root,
        pairs_used=[{"asc_id": "ASC_CELL21", "desc_id": "DESC_CELL21", "dt_hours": 42.0}],
        orbit_window_days=12,
        pair_cap_hours=48,
        master_id="ASC_CELL21",
    )
    _write_notebook_radar_meta(notebook_root)

    report = build_sar_source_selection_parity_report(app_run_dir=app_run_dir, notebook_roots=[notebook_root])
    by_check = {row["check"]: row for row in report["rows"]}

    assert {"root_label": "NOTEBOOK_RUN", "relative_path": "QA/QA_RADAR_META_pairs4_pairdt36h_orbitpm9d.json"} in report[
        "notebook_metadata_files"
    ]
    assert by_check["cell25_pixel_export_profile"]["status"] == "MATCH"
    assert by_check["cell21_master_units_qa_profile"]["status"] == "AUXILIARY_QA"
    assert by_check["source_parameters"]["status"] == "MATCH"
    assert by_check["source_parameters"]["notebook_value"] == '{"orbit_window_days":"9","pair_cap_hours":"36"}'
    assert by_check["source_parameters"]["app_value"] == '{"orbit_window_days":"9","pair_cap_hours":"36"}'
    assert by_check["image_identity"]["status"] == "MISSING_CELL25_PAIR_IDS"
    assert by_check["orbit_pairing"]["status"] == "MISSING_CELL25_PAIR_IDS"
    assert "lacks per-pair ASC/DESC IDs" in by_check["image_identity"]["evidence"]
    assert by_check["vv_vh_pair_count"]["status"] == "MISMATCH"
    assert by_check["vv_vh_pair_count"]["notebook_value"] == "4"
    serialized = json.dumps(report, sort_keys=True)
    assert "C:\\" not in serialized
    assert "/content/" not in serialized
    assert "bounds" not in serialized
    assert "coordinates" not in serialized


def test_sar_source_selection_report_compares_true_cell25_pair_ids_when_present(tmp_path: Path) -> None:
    app_run_dir = tmp_path / "data" / "runs" / "run-123"
    notebook_root = tmp_path / "NOTEBOOK_RUN"
    cell25_pairs = [
        {"asc_id": "ASC_CELL25_A", "desc_id": "DESC_CELL25_A", "dt_hours": 11.5},
        {"asc_id": "ASC_CELL25_B", "desc_id": "DESC_CELL25_B", "dt_hours": 12.25},
    ]
    _write_app_sar_metadata(
        app_run_dir,
        pairs=cell25_pairs,
        source_filters={
            "selection_profile": "cell25_pixel_export",
            "max_orbit_dt_days": 9,
            "max_pair_dt_hours": 36,
        },
    )
    _write_notebook_master_units(
        notebook_root,
        pairs_used=[{"asc_id": "ASC_CELL21", "desc_id": "DESC_CELL21", "dt_hours": 42.0}],
        orbit_window_days=12,
        pair_cap_hours=48,
        master_id="ASC_CELL21",
    )
    _write_notebook_radar_meta(notebook_root, pairs_used=cell25_pairs)

    report = build_sar_source_selection_parity_report(app_run_dir=app_run_dir, notebook_roots=[notebook_root])
    by_check = {row["check"]: row for row in report["rows"]}

    assert by_check["image_identity"]["status"] == "MATCH"
    assert by_check["image_identity"]["notebook_value"] == "ASC_CELL25_A>DESC_CELL25_A|ASC_CELL25_B>DESC_CELL25_B"
    assert by_check["orbit_pairing"]["status"] == "MATCH"
    assert by_check["orbit_pairing"]["notebook_value"] == "11.5|12.25"
    assert by_check["vv_vh_pair_count"]["status"] == "MATCH"


def _write_app_sar_metadata(
    app_run_dir: Path,
    *,
    pairs: list[dict[str, object]] | None = None,
    source_filters: dict[str, object] | None = None,
) -> None:
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
                "source_filters": source_filters or {},
                "selected_band_list": ["VV", "VH", "angle"],
                "output_band_list": ["VV_dB", "VH_dB", "logRatio_dB", "incidence"],
                "angle_incidence_mapping": {"notebook_band": "angle", "app_output_band": "incidence"},
                "processing_path": {
                    "local_dem_rtc": True,
                    "speckle_refined_lee_filtering": False,
                    "db_to_linear_to_db": True,
                    "grid_sampling": "sampleRectangle",
                },
                "pairs": pairs or [{"asc_id": "ASC_1", "desc_id": "DESC_1", "dt_hours": 1.0}],
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


def _write_notebook_master_units(
    notebook_root: Path,
    *,
    pairs_used: list[dict[str, object]],
    orbit_window_days: int,
    pair_cap_hours: int,
    master_id: str,
) -> None:
    path = notebook_root / "QA" / "QA_S1_MASTER_UNITS.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "orbit_window_days": orbit_window_days,
                "pair_cap_hours": pair_cap_hours,
                "pairs_used": pairs_used,
                "MASTER_ID": master_id,
            }
        ),
        encoding="utf-8",
    )


def _write_notebook_radar_meta(notebook_root: Path, *, pairs_used: int | list[dict[str, object]] = 4) -> None:
    path = notebook_root / "QA" / "QA_RADAR_META_pairs4_pairdt36h_orbitpm9d.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "START": "2026-01-01",
                "END": "2026-03-01",
                "pairs_used": pairs_used,
                "LOCAL_DEM_RTC": True,
                "outputs": {
                    "summary_csv": "/content/run/QA/SUMMARY_RADAR_pairs4_pairdt36h_orbitpm9d.csv",
                },
            }
        ),
        encoding="utf-8",
    )
