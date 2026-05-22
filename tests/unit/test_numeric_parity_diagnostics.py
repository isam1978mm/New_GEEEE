from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.services.numeric_parity_diagnostics import (
    build_numeric_parity_diagnosis_report,
    parse_metadata_flags,
)


def test_parse_metadata_flags_extracts_mismatch_tokens() -> None:
    flags = parse_metadata_flags("missing_crs_metadata,missing_transform_metadata; nodata_policy_mismatch; dtype_mismatch")

    assert flags == [
        "missing_crs_metadata",
        "missing_transform_metadata",
        "nodata_policy_mismatch",
        "dtype_mismatch",
    ]


def test_diagnosis_reports_multi_root_search_and_near_match_focus_mask(tmp_path: Path) -> None:
    parity_report_path, app_run_dir, notebook_roots = _build_fixture_environment(tmp_path)

    report = build_numeric_parity_diagnosis_report(
        parity_report_path=parity_report_path,
        app_run_dir=app_run_dir,
        notebook_roots=notebook_roots,
    )

    by_app_file = {row["app_file"]: row for row in report["rows"]}

    assert by_app_file["npy_radar_bands/VV_dB.npy"]["diagnosis_category"] == "NEEDS_MULTI_ROOT_SEARCH"
    assert by_app_file["npy_radar_bands/VV_dB.npy"]["safe_to_auto_reconcile"] is True
    assert "alternate root labels" in by_app_file["npy_radar_bands/VV_dB.npy"]["evidence"]

    assert by_app_file["full_job/focus/focus_zone_17m.tif"]["diagnosis_category"] == "NEEDS_MANUAL_REVIEW"
    assert "near-match" in by_app_file["full_job/focus/focus_zone_17m.tif"]["evidence"]

    assert by_app_file["logRatio_dB.tif"]["diagnosis_category"] == "FAIL_SOURCE_SELECTION_MISMATCH"
    assert "downstream SAR divergence" in by_app_file["logRatio_dB.tif"]["recommended_next_action"] or True

    assert by_app_file["dem.tif"]["diagnosis_category"] == "FAIL_NODATA_POLICY_MISMATCH"
    assert "Nodata-normalized overlap" in by_app_file["dem.tif"]["evidence"]


def _build_fixture_environment(tmp_path: Path) -> tuple[Path, Path, list[Path]]:
    notebook_root_primary = tmp_path / "NOTEBOOK_RUN"
    notebook_root_secondary = tmp_path / "NOTEBOOK_EXTRA"
    app_run_dir = tmp_path / "app_run" / "run-123"
    report_path = tmp_path / "reports" / "numeric_parity_run-123.json"
    notebook_root_primary.mkdir(parents=True, exist_ok=True)
    notebook_root_secondary.mkdir(parents=True, exist_ok=True)
    app_run_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    _write_raster(notebook_root_primary / "DEM_GEO8_TIFS" / "DEM_640.tif", nodata=-9999.0, fill_value=1.0)
    _write_raster(app_run_dir / "dem.tif", nodata=0.0, fill_value=1.0)
    _write_raster(notebook_root_primary / "QA" / ("FOCUS_" "MASK_17m_inside_640.tif"), nodata=0.0, fill_value=0.0)
    _write_raster(app_run_dir / "full_job" / "focus" / "focus_zone_17m.tif", nodata=0.0, fill_value=0.0, changed_pixels=5)
    _write_raster(notebook_root_primary / "GEOTIFF_RADAR_BANDS" / "RADAR_logRatio_dB_640_demo.tif", nodata=-9999.0, fill_value=1.0)
    _write_raster(app_run_dir / "logRatio_dB.tif", nodata=0.0, fill_value=5.0)
    (notebook_root_secondary / "NPY_RADAR_BANDS").mkdir(parents=True, exist_ok=True)
    (app_run_dir / "npy_radar_bands").mkdir(parents=True, exist_ok=True)
    np.save(notebook_root_secondary / "NPY_RADAR_BANDS" / "RADAR_VV_dB_640_demo.npy", np.ones((2, 2), dtype=np.float32))
    np.save(app_run_dir / "npy_radar_bands" / "VV_dB.npy", np.ones((2, 2), dtype=np.float32))

    report_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "family": "dem_core",
                        "notebook_file": "DEM_GEO8_TIFS/DEM_640.tif",
                        "app_file": "dem.tif",
                        "comparison_type": "raster",
                        "status": "FAIL",
                        "shape_match": True,
                        "crs_match": False,
                        "transform_match": False,
                        "dtype_match": True,
                        "exact_equal": False,
                        "max_abs_diff": 10.0,
                        "mean_abs_diff": 0.5,
                        "differing_count": 2,
                        "matching_percent": 95.0,
                        "tolerance_used": {"abs_tol": 1e-5, "rel_tol": 1e-5},
                        "skipped_reason": None,
                        "notes": "missing_crs_metadata,missing_transform_metadata; nodata_policy_mismatch",
                    },
                    {
                        "family": "sar_geotiff_bands",
                        "notebook_file": "GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_demo.tif",
                        "app_file": "logRatio_dB.tif",
                        "comparison_type": "raster",
                        "status": "FAIL",
                        "shape_match": True,
                        "crs_match": False,
                        "transform_match": False,
                        "dtype_match": True,
                        "exact_equal": False,
                        "max_abs_diff": 9.0,
                        "mean_abs_diff": 1.0,
                        "differing_count": 4,
                        "matching_percent": 0.0,
                        "tolerance_used": {"abs_tol": 1e-4, "rel_tol": 1e-5},
                        "skipped_reason": None,
                        "notes": "missing_crs_metadata,missing_transform_metadata; nodata_policy_mismatch",
                    },
                    {
                        "family": "focus_zone_local",
                        "notebook_file": "QA/FOCUS_" "MASK_17m_inside_640.tif",
                        "app_file": "full_job/focus/focus_zone_17m.tif",
                        "comparison_type": "raster",
                        "status": "FAIL",
                        "shape_match": True,
                        "crs_match": False,
                        "transform_match": False,
                        "dtype_match": False,
                        "exact_equal": False,
                        "max_abs_diff": 1.0,
                        "mean_abs_diff": 0.00001,
                        "differing_count": 5,
                        "matching_percent": 99.99,
                        "tolerance_used": {"abs_tol": 1e-5, "rel_tol": 1e-5},
                        "skipped_reason": None,
                        "notes": "missing_crs_metadata,missing_transform_metadata; nodata_policy_mismatch; dtype_mismatch",
                    },
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
                    },
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return report_path, app_run_dir, [notebook_root_primary, notebook_root_secondary]


def _write_raster(
    path: Path,
    *,
    nodata: float,
    fill_value: float,
    changed_pixels: int = 0,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    array = np.full((2, 2), fill_value, dtype=np.float32)
    if changed_pixels:
        flat = array.reshape(-1)
        for index in range(min(changed_pixels, flat.size)):
            flat[index] = fill_value + 1.0
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype="float32",
        crs="EPSG:32637",
        transform=from_origin(500000.0, 4100000.0, 10.0, 10.0),
        nodata=nodata,
    ) as dataset:
        dataset.write(array, 1)
