from __future__ import annotations

import csv
import json
from pathlib import Path

from app.services.numeric_parity_diagnostics import (
    NUMERIC_PARITY_DIAGNOSIS_PREFIX,
    write_numeric_parity_diagnosis_report,
)


def test_numeric_parity_diagnostics_script_writes_local_only_reports(tmp_path: Path) -> None:
    parity_report_path = tmp_path / "reports" / "numeric_parity_run-123.json"
    app_run_dir = tmp_path / "data" / "runs" / "run-123"
    notebook_root = tmp_path / "NOTEBOOK_RUN"
    notebook_root_secondary = tmp_path / "NOTEBOOK_EXTRA"
    parity_report_path.parent.mkdir(parents=True, exist_ok=True)
    app_run_dir.mkdir(parents=True, exist_ok=True)
    notebook_root.mkdir(parents=True, exist_ok=True)
    notebook_root_secondary.mkdir(parents=True, exist_ok=True)
    (app_run_dir / "npy_radar_bands").mkdir(parents=True, exist_ok=True)
    (notebook_root_secondary / "NPY_RADAR_BANDS").mkdir(parents=True, exist_ok=True)
    (app_run_dir / "npy_radar_bands" / "VV_dB.npy").write_bytes(b"123")
    (notebook_root_secondary / "NPY_RADAR_BANDS" / "RADAR_VV_dB_640_demo.npy").write_bytes(b"123")
    parity_report_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "family": "sar_npy_bands",
                        "notebook_file": "",
                        "app_file": "npy_radar_bands/VV_dB.npy",
                        "comparison_type": "npy",
                        "status": "SKIP_MISSING_NOTEBOOK",
                        "shape_match": None,
                        "crs_match": None,
                        "transform_match": None,
                        "dtype_match": None,
                        "exact_equal": None,
                        "max_abs_diff": None,
                        "mean_abs_diff": None,
                        "differing_count": None,
                        "matching_percent": None,
                        "tolerance_used": {},
                        "skipped_reason": "notebook_file_missing",
                        "notes": "",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    json_path, csv_path = write_numeric_parity_diagnosis_report(
        parity_report_path=parity_report_path,
        app_run_dir=app_run_dir,
        notebook_roots=[notebook_root, notebook_root_secondary],
        output_dir=tmp_path / "output",
    )

    assert json_path == tmp_path / "output" / f"{NUMERIC_PARITY_DIAGNOSIS_PREFIX}_run-123.json"
    assert csv_path == tmp_path / "output" / f"{NUMERIC_PARITY_DIAGNOSIS_PREFIX}_run-123.csv"

    report = json.loads(json_path.read_text(encoding="utf-8"))
    serialized = json.dumps(report, sort_keys=True)
    assert report["artifact_class"] == "FILESYSTEM_ONLY"
    assert report["local_only"] is True
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    assert report["rows"][0]["diagnosis_category"] == "NEEDS_MULTI_ROOT_SEARCH"

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["diagnosis_category"] == "NEEDS_MULTI_ROOT_SEARCH"
