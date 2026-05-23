from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.services.sar_processing_parity import SAR_PROCESSING_PARITY_PREFIX
from scripts.report_sar_processing_parity import main


def test_sar_processing_parity_script_writes_local_only_reports(tmp_path: Path, monkeypatch) -> None:
    app_run_dir = tmp_path / "data" / "runs" / "run-123"
    notebook_root = tmp_path / "NOTEBOOK_RUN"
    output_dir = tmp_path / "reports"
    _write_fixture(app_run_dir=app_run_dir, notebook_root=notebook_root)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "report_sar_processing_parity.py",
            "--app-run-dir",
            str(app_run_dir),
            "--notebook-root",
            str(notebook_root),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert main() == 0

    json_path = output_dir / f"{SAR_PROCESSING_PARITY_PREFIX}_run-123.json"
    csv_path = output_dir / f"{SAR_PROCESSING_PARITY_PREFIX}_run-123.csv"
    assert json_path.is_file()
    assert csv_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    serialized = json.dumps(payload, sort_keys=True)
    assert payload["artifact_class"] == "FILESYSTEM_ONLY"
    assert payload["local_only"] is True
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    assert any(item["relative_path"] == "SUMMARY_RADAR_demo.csv" for item in payload["notebook_files"])
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_check = {row["check"]: row for row in rows}
    assert by_check["logratio_formula_app_raster"]["status"] == "MATCH"
    assert by_check["f20_edge_interior_VV_dB_raster"]["status"] == "DIAGNOSTIC"
    assert by_check["f20_nodata_edge_overlap_VV_dB_raster"]["status"] == "DIAGNOSTIC"
    assert by_check["f20_angle_delta_distribution_raster"]["status"] == "DIAGNOSTIC"
    assert by_check["f21_residual_distribution_VV_dB_raster"]["status"] == "DIAGNOSTIC"
    assert by_check["f21_sign_balance_VV_dB_raster"]["status"] == "DIAGNOSTIC"
    assert by_check["f21_regression_residual_VV_dB_raster"]["status"] == "DIAGNOSTIC"
    assert by_check["f23_large_residual_spatial_bins_VV_dB_raster"]["status"] == "DIAGNOSTIC"
    assert by_check["f23_dtype_casting_profile_VV_dB_raster"]["status"] == "DIAGNOSTIC"
    assert by_check["radar_linear_support_stack"]["status"] == "DOWNSTREAM_DIAGNOSTIC"


def test_sar_processing_parity_script_finds_qa_summary_layout(tmp_path: Path, monkeypatch) -> None:
    app_run_dir = tmp_path / "data" / "runs" / "run-qa"
    notebook_root = tmp_path / "NOTEBOOK_RUN"
    output_dir = tmp_path / "reports"
    _write_fixture(app_run_dir=app_run_dir, notebook_root=notebook_root, summary_relative_path=Path("QA") / "SUMMARY_RADAR_demo.csv")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "report_sar_processing_parity.py",
            "--app-run-dir",
            str(app_run_dir),
            "--notebook-root",
            str(notebook_root),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert main() == 0

    json_path = output_dir / f"{SAR_PROCESSING_PARITY_PREFIX}_run-qa.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert {"root_label": "NOTEBOOK_RUN", "relative_path": "QA/SUMMARY_RADAR_demo.csv"} in payload["notebook_files"]
    serialized = json.dumps(payload, sort_keys=True)
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    assert "coordinates" not in serialized


def test_sar_processing_parity_script_accepts_prior_report(tmp_path: Path, monkeypatch) -> None:
    app_run_dir = tmp_path / "data" / "runs" / "run-prior"
    notebook_root = tmp_path / "NOTEBOOK_RUN"
    output_dir = tmp_path / "reports"
    prior_report = tmp_path / "prior.json"
    _write_fixture(app_run_dir=app_run_dir, notebook_root=notebook_root)
    prior_report.write_text(
        json.dumps(
            {
                "report_type": "sar_processing_parity",
                "artifact_class": "FILESYSTEM_ONLY",
                "local_only": True,
                "rows": [
                    {
                        "check": "VV_dB_raster",
                        "raw_matching_percent": 50.0,
                        "common_valid_matching_percent": 50.0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "report_sar_processing_parity.py",
            "--app-run-dir",
            str(app_run_dir),
            "--notebook-root",
            str(notebook_root),
            "--output-dir",
            str(output_dir),
            "--prior-report",
            str(prior_report),
        ],
    )

    assert main() == 0

    json_path = output_dir / f"{SAR_PROCESSING_PARITY_PREFIX}_run-prior.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    by_check = {row["check"]: row for row in payload["rows"]}
    assert by_check["prior_comparison_VV_dB_raster"]["status"] == "IMPROVED"
    serialized = json.dumps(payload, sort_keys=True)
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    assert "coordinates" not in serialized


def _write_fixture(
    *,
    app_run_dir: Path,
    notebook_root: Path,
    summary_relative_path: Path = Path("SUMMARY_RADAR_demo.csv"),
) -> None:
    _write_summary(
        notebook_root / summary_relative_path,
        [
            {"band_name": "VV_dB", "min": "1.0", "max": "2.0", "mean": "1.5", "nodata_count": "0"},
            {"band_name": "VH_dB", "min": "1.0", "max": "2.0", "mean": "1.5", "nodata_count": "0"},
            {"band_name": "logRatio_dB", "min": "0.0", "max": "0.0", "mean": "0.0", "nodata_count": "0"},
            {"band_name": "angle", "min": "30.0", "max": "31.0", "mean": "30.5", "nodata_count": "0"},
        ],
    )
    _write_summary(
        app_run_dir / "qa" / "sar" / "sar_summary.csv",
        [
            {"band_name": "VV_dB", "min": "1.0", "max": "2.0", "mean": "1.5", "nodata_count": "0"},
            {"band_name": "VH_dB", "min": "1.0", "max": "2.0", "mean": "1.5", "nodata_count": "0"},
            {"band_name": "logRatio_dB", "min": "0.0", "max": "0.0", "mean": "0.0", "nodata_count": "0"},
            {"band_name": "incidence", "min": "30.0", "max": "31.0", "mean": "30.5", "nodata_count": "0"},
        ],
    )
    vv = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    vh = np.array([[1.0, 1.5], [2.0, 2.5]], dtype=np.float32)
    log_ratio = vv - vh
    angle = np.array([[30.0, 30.5], [31.0, 31.5]], dtype=np.float32)
    _write_raster(notebook_root / "GEOTIFF_RADAR_BANDS" / "RADAR_VV_dB_640_demo.tif", vv)
    _write_raster(notebook_root / "GEOTIFF_RADAR_BANDS" / "RADAR_VH_dB_640_demo.tif", vh)
    _write_raster(notebook_root / "GEOTIFF_RADAR_BANDS" / "RADAR_logRatio_dB_640_demo.tif", log_ratio)
    _write_raster(notebook_root / "GEOTIFF_RADAR_BANDS" / "RADAR_angle_640_demo.tif", angle)
    _write_raster(app_run_dir / "VV_dB.tif", vv)
    _write_raster(app_run_dir / "VH_dB.tif", vh)
    _write_raster(app_run_dir / "logRatio_dB.tif", log_ratio)
    _write_raster(app_run_dir / "incidence.tif", angle + 1.0)
    (notebook_root / "NPY_RADAR_BANDS").mkdir(parents=True, exist_ok=True)
    (app_run_dir / "npy_radar_bands").mkdir(parents=True, exist_ok=True)
    np.save(notebook_root / "NPY_RADAR_BANDS" / "RADAR_VV_dB_640_demo.npy", vv)
    np.save(notebook_root / "NPY_RADAR_BANDS" / "RADAR_VH_dB_640_demo.npy", vh)
    np.save(notebook_root / "NPY_RADAR_BANDS" / "RADAR_logRatio_dB_640_demo.npy", log_ratio)
    np.save(notebook_root / "NPY_RADAR_BANDS" / "RADAR_angle_640_demo.npy", angle)
    np.save(app_run_dir / "npy_radar_bands" / "VV_dB.npy", vv)
    np.save(app_run_dir / "npy_radar_bands" / "VH_dB.npy", vh)
    np.save(app_run_dir / "npy_radar_bands" / "logRatio_dB.npy", log_ratio)
    np.save(app_run_dir / "npy_radar_bands" / "incidence.npy", angle + 1.0)
    (notebook_root / "NPY_STACKS").mkdir(parents=True, exist_ok=True)
    (app_run_dir / "stacks" / "tensor_support").mkdir(parents=True, exist_ok=True)
    np.save(notebook_root / "NPY_STACKS" / "RADAR_STACK_HWC_640_demo.npy", np.stack([vv, vh, log_ratio, angle], axis=-1))
    np.save(app_run_dir / "stacks" / "tensor_support" / "radar_linear_support_stack.npy", np.stack([vv, vh, log_ratio, angle + 1.0], axis=-1))


def _write_summary(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["band_name", "min", "max", "mean", "nodata_count"])
        writer.writeheader()
        writer.writerows(rows)


def _write_raster(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:32637",
        transform=from_origin(500000.0, 4100000.0, 10.0, 10.0),
        nodata=-9999.0,
    ) as dataset:
        dataset.write(array.astype(np.float32), 1)
