from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from app.services.sar_processing_parity import (
    SAR_PROCESSING_PARITY_PREFIX,
    analyze_array_pair,
    build_sar_processing_parity_report,
    compare_sar_summary_rows,
    validate_log_ratio_relationship,
    write_sar_processing_parity_report,
)


def test_compare_sar_summary_rows_reports_band_mismatch() -> None:
    diffs = compare_sar_summary_rows(
        notebook_rows={
            "VV_dB": {"band_name": "VV_dB", "min": "1.0", "max": "5.0", "mean": "3.0", "nodata_count": "2"},
            "VH_dB": {"band_name": "VH_dB", "min": "1.0", "max": "5.0", "mean": "3.0", "nodata_count": "2"},
            "logRatio_dB": {"band_name": "logRatio_dB", "min": "1.0", "max": "5.0", "mean": "3.0", "nodata_count": "2"},
            "angle": {"band_name": "angle", "min": "30.0", "max": "40.0", "mean": "35.0", "nodata_count": "0"},
        },
        app_rows={
            "VV_dB": {"band_name": "VV_dB", "min": "2.0", "max": "5.0", "mean": "3.0", "nodata_count": "2"},
            "VH_dB": {"band_name": "VH_dB", "min": "1.0", "max": "5.0", "mean": "3.0", "nodata_count": "2"},
            "logRatio_dB": {"band_name": "logRatio_dB", "min": "1.0", "max": "5.0", "mean": "3.0", "nodata_count": "2"},
            "incidence": {"band_name": "incidence", "min": "30.0", "max": "40.0", "mean": "35.0", "nodata_count": "0"},
        },
    )

    by_band = {item.band_name: item for item in diffs}
    assert by_band["VV_dB"].status == "MISMATCH"
    assert "min" in by_band["VV_dB"].evidence
    assert by_band["incidence"].status == "MATCH"


def test_validate_log_ratio_relationship_reports_match() -> None:
    vv = np.array([[4.0, 6.0], [8.0, 10.0]], dtype=np.float32)
    vh = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    log_ratio = vv - vh

    result = validate_log_ratio_relationship(vv_array=vv, vh_array=vh, log_ratio_array=log_ratio, nodata=None)

    assert result["status"] == "MATCH"
    assert result["matching_percent"] == 100.0


def test_analyze_array_pair_uses_common_valid_mask_for_incidence_mapping() -> None:
    nodata = -9999.0
    notebook_angle = np.array([[30.0, 31.0], [32.0, nodata]], dtype=np.float32)
    app_incidence = np.array([[30.0, 31.0], [32.0, 99.0]], dtype=np.float32)

    analysis = analyze_array_pair(
        band_name="incidence",
        notebook_array=notebook_angle,
        app_array=app_incidence,
        notebook_nodata=nodata,
        app_nodata=None,
    )

    assert analysis["status"] == "MATCH_COMMON_VALID_MASK"
    assert analysis["likely_cause"] == "ANGLE_MAPPING_OR_MASKING"
    assert analysis["common_valid_matching_percent"] == 100.0
    assert "angle-to-incidence mapping" in analysis["evidence"]


def test_analyze_array_pair_detects_constant_offset() -> None:
    notebook = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    app = notebook + 2.0

    analysis = analyze_array_pair(
        band_name="VV_dB",
        notebook_array=notebook,
        app_array=app,
        notebook_nodata=None,
        app_nodata=None,
    )

    assert analysis["status"] == "MISMATCH"
    assert analysis["likely_cause"] == "CONSTANT_OFFSET"
    assert analysis["linear_slope"] == pytest.approx(1.0)
    assert analysis["linear_intercept"] == pytest.approx(2.0)


def test_sar_processing_report_writer_stays_local_only_and_relative(tmp_path: Path) -> None:
    app_run_dir = tmp_path / "data" / "runs" / "run-123"
    notebook_root = tmp_path / "NOTEBOOK_RUN"
    output_dir = tmp_path / "reports"
    _write_sar_fixture(app_run_dir=app_run_dir, notebook_root=notebook_root)

    report = build_sar_processing_parity_report(app_run_dir=app_run_dir, notebook_roots=[notebook_root])
    by_check = {row["check"]: row for row in report["rows"]}

    assert report["artifact_class"] == "FILESYSTEM_ONLY"
    assert report["local_only"] is True
    assert by_check["sar_summary_VV_dB"]["status"] == "MISMATCH"
    assert by_check["incidence_raster"]["status"] == "MATCH_COMMON_VALID_MASK"
    assert by_check["incidence_raster"]["likely_cause"] == "ANGLE_MAPPING_OR_MASKING"
    assert by_check["logratio_formula_notebook_raster"]["status"] == "MATCH"
    assert by_check["radar_linear_support_stack"]["status"] == "DOWNSTREAM_DIAGNOSTIC"

    json_path, csv_path = write_sar_processing_parity_report(
        app_run_dir=app_run_dir,
        notebook_roots=[notebook_root],
        output_dir=output_dir,
    )

    assert json_path == output_dir / f"{SAR_PROCESSING_PARITY_PREFIX}_run-123.json"
    assert csv_path == output_dir / f"{SAR_PROCESSING_PARITY_PREFIX}_run-123.csv"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    serialized = json.dumps(payload, sort_keys=True)
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    assert "coordinates" not in serialized
    assert "bounds" not in serialized
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert any(row["check"] == "VV_dB_raster" for row in rows)


def _write_sar_fixture(*, app_run_dir: Path, notebook_root: Path) -> None:
    notebook_summary_path = notebook_root / "SUMMARY_RADAR_demo.csv"
    app_summary_path = app_run_dir / "qa" / "sar" / "sar_summary.csv"
    notebook_summary_path.parent.mkdir(parents=True, exist_ok=True)
    app_summary_path.parent.mkdir(parents=True, exist_ok=True)
    _write_summary_csv(
        notebook_summary_path,
        [
            {"band_name": "VV_dB", "min": "1.0", "max": "4.0", "mean": "2.5", "nodata_count": "1"},
            {"band_name": "VH_dB", "min": "1.0", "max": "4.0", "mean": "2.5", "nodata_count": "1"},
            {"band_name": "logRatio_dB", "min": "0.0", "max": "0.0", "mean": "0.0", "nodata_count": "1"},
            {"band_name": "angle", "min": "30.0", "max": "32.0", "mean": "31.0", "nodata_count": "1"},
        ],
    )
    _write_summary_csv(
        app_summary_path,
        [
            {"band_name": "VV_dB", "min": "2.0", "max": "5.0", "mean": "3.5", "nodata_count": "1"},
            {"band_name": "VH_dB", "min": "1.0", "max": "4.0", "mean": "2.5", "nodata_count": "1"},
            {"band_name": "logRatio_dB", "min": "0.0", "max": "0.0", "mean": "0.0", "nodata_count": "1"},
            {"band_name": "incidence", "min": "30.0", "max": "99.0", "mean": "48.0", "nodata_count": "0"},
        ],
    )

    notebook_vv = np.array([[1.0, 2.0], [3.0, -9999.0]], dtype=np.float32)
    notebook_vh = np.array([[1.0, 2.0], [3.0, -9999.0]], dtype=np.float32)
    notebook_log_ratio = notebook_vv - notebook_vh
    notebook_angle = np.array([[30.0, 31.0], [32.0, -9999.0]], dtype=np.float32)
    app_vv = notebook_vv + np.array([[1.0, 1.0], [1.0, 0.0]], dtype=np.float32)
    app_vh = notebook_vh.copy()
    app_log_ratio = app_vv - app_vh
    app_incidence = np.array([[30.0, 31.0], [32.0, 99.0]], dtype=np.float32)

    _write_raster(notebook_root / "GEOTIFF_RADAR_BANDS" / "RADAR_VV_dB_640_demo.tif", notebook_vv, nodata=-9999.0)
    _write_raster(notebook_root / "GEOTIFF_RADAR_BANDS" / "RADAR_VH_dB_640_demo.tif", notebook_vh, nodata=-9999.0)
    _write_raster(notebook_root / "GEOTIFF_RADAR_BANDS" / "RADAR_logRatio_dB_640_demo.tif", notebook_log_ratio, nodata=-9999.0)
    _write_raster(notebook_root / "GEOTIFF_RADAR_BANDS" / "RADAR_angle_640_demo.tif", notebook_angle, nodata=-9999.0)
    _write_raster(app_run_dir / "VV_dB.tif", app_vv, nodata=-9999.0)
    _write_raster(app_run_dir / "VH_dB.tif", app_vh, nodata=-9999.0)
    _write_raster(app_run_dir / "logRatio_dB.tif", app_log_ratio, nodata=-9999.0)
    _write_raster(app_run_dir / "incidence.tif", app_incidence, nodata=None)

    (notebook_root / "NPY_RADAR_BANDS").mkdir(parents=True, exist_ok=True)
    (app_run_dir / "npy_radar_bands").mkdir(parents=True, exist_ok=True)
    np.save(notebook_root / "NPY_RADAR_BANDS" / "RADAR_VV_dB_640_demo.npy", notebook_vv)
    np.save(notebook_root / "NPY_RADAR_BANDS" / "RADAR_VH_dB_640_demo.npy", notebook_vh)
    np.save(notebook_root / "NPY_RADAR_BANDS" / "RADAR_logRatio_dB_640_demo.npy", notebook_log_ratio)
    np.save(notebook_root / "NPY_RADAR_BANDS" / "RADAR_angle_640_demo.npy", notebook_angle)
    np.save(app_run_dir / "npy_radar_bands" / "VV_dB.npy", app_vv)
    np.save(app_run_dir / "npy_radar_bands" / "VH_dB.npy", app_vh)
    np.save(app_run_dir / "npy_radar_bands" / "logRatio_dB.npy", app_log_ratio)
    np.save(app_run_dir / "npy_radar_bands" / "incidence.npy", app_incidence)

    (notebook_root / "NPY_STACKS").mkdir(parents=True, exist_ok=True)
    (app_run_dir / "stacks" / "tensor_support").mkdir(parents=True, exist_ok=True)
    np.save(notebook_root / "NPY_STACKS" / "RADAR_STACK_HWC_640_demo.npy", np.stack([notebook_vv, notebook_vh, notebook_log_ratio, notebook_angle], axis=-1))
    np.save(app_run_dir / "stacks" / "tensor_support" / "radar_linear_support_stack.npy", np.stack([app_vv, app_vh, app_log_ratio, app_incidence], axis=-1))


def _write_summary_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["band_name", "min", "max", "mean", "nodata_count"])
        writer.writeheader()
        writer.writerows(rows)


def _write_raster(path: Path, array: np.ndarray, *, nodata: float | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_kwargs = {
        "driver": "GTiff",
        "height": array.shape[0],
        "width": array.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32637",
        "transform": from_origin(500000.0, 4100000.0, 10.0, 10.0),
    }
    if nodata is not None:
        write_kwargs["nodata"] = nodata
    with rasterio.open(path, "w", **write_kwargs) as dataset:
        dataset.write(array.astype(np.float32), 1)
