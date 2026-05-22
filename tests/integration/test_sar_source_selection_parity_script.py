from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from app.services.sar_source_selection_parity import SAR_SOURCE_SELECTION_PARITY_PREFIX
from scripts.report_sar_source_selection_parity import main


def test_sar_source_selection_parity_script_writes_local_only_reports(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app_run_dir = tmp_path / "data" / "runs" / "run-123"
    notebook_root = tmp_path / "NOTEBOOK_RUN"
    output_dir = tmp_path / "reports"
    _write_app_sar_metadata(app_run_dir)
    _write_notebook_summary(notebook_root)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "report_sar_source_selection_parity.py",
            "--app-run-dir",
            str(app_run_dir),
            "--notebook-root",
            str(notebook_root),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert main() == 0

    json_path = output_dir / f"{SAR_SOURCE_SELECTION_PARITY_PREFIX}_run-123.json"
    csv_path = output_dir / f"{SAR_SOURCE_SELECTION_PARITY_PREFIX}_run-123.csv"
    assert json_path.is_file()
    assert csv_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    serialized = json.dumps(payload, sort_keys=True)
    assert payload["artifact_class"] == "FILESYSTEM_ONLY"
    assert payload["local_only"] is True
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert any(row["check"] == "angle_incidence_mapping" for row in rows)


def _write_app_sar_metadata(app_run_dir: Path) -> None:
    path = app_run_dir / "qa" / "sar" / "sar_pair_diagnostics.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "collection_id": "COPERNICUS/S1_GRD",
                "date_window": {"start_date": "2026-01-01", "end_date": "2026-03-01"},
                "output_band_list": ["VV_dB", "VH_dB", "logRatio_dB", "incidence"],
                "angle_incidence_mapping": {"notebook_band": "angle", "app_output_band": "incidence"},
                "processing_path": {"local_dem_rtc": True, "speckle_refined_lee_filtering": False},
                "pairs": [{"asc_id": "ASC_1", "desc_id": "DESC_1", "dt_hours": 1.0}],
            }
        ),
        encoding="utf-8",
    )


def _write_notebook_summary(notebook_root: Path) -> None:
    notebook_root.mkdir(parents=True, exist_ok=True)
    with (notebook_root / "SUMMARY_RADAR_demo.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["collection_id", "start_date", "end_date", "asc_id", "desc_id", "dt_hours", "band_name"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "collection_id": "COPERNICUS/S1_GRD",
                "start_date": "2026-01-01",
                "end_date": "2026-03-01",
                "asc_id": "ASC_1",
                "desc_id": "DESC_1",
                "dt_hours": "1.0",
                "band_name": "angle",
            }
        )
