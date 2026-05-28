from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.services.phase5_numeric_output_parity_summary import (
    Phase5Case,
    build_phase5_numeric_output_parity_summary,
)


def test_phase5_numeric_output_parity_summary_is_config_required_without_paths() -> None:
    report = build_phase5_numeric_output_parity_summary(
        app_run_dir=None,
        notebook_reference_bundle_dir=None,
        alias_cases=(),
        reference_cases=(),
    )

    assert report["summary"]["overall_status"] == "CONFIG_REQUIRED"
    assert report["summary"]["final_reference_proof_complete"] is False
    assert report["phase5d_alias_integrity"]["status"] == "CONFIG_REQUIRED"
    assert report["phase5e_reference_parity"]["status"] == "CONFIG_REQUIRED"
    assert report["known_not_implemented_outputs"]["status"] == "CONFIG_REQUIRED"


def test_phase5_numeric_output_parity_summary_reports_classified_exceptions(tmp_path: Path) -> None:
    app_run_dir = tmp_path / "runs" / "run-123"
    notebook_root = tmp_path / "reference_bundle"
    app_run_dir.mkdir(parents=True, exist_ok=True)
    notebook_root.mkdir(parents=True, exist_ok=True)

    _write_geotiff(app_run_dir / "alias_left.tif", value=1.0, dtype="float32", nodata=-9999.0)
    _write_geotiff(app_run_dir / "alias_right.tif", value=1.0, dtype="float32", nodata=-9999.0)
    _write_geotiff(app_run_dir / "reference_raster.tif", value=2.0, dtype="float32", nodata=-9999.0)
    _write_geotiff(notebook_root / "reference_raster.tif", value=2.0, dtype="float32", nodata=-9999.0)

    np.save(app_run_dir / "reference_fail.npy", np.array([[10.0, 20.0]], dtype=np.float32))
    np.save(notebook_root / "reference_fail.npy", np.array([[9999.0, 20.0]], dtype=np.float32))

    (app_run_dir / "QA").mkdir(parents=True, exist_ok=True)
    (app_run_dir / "QA" / "REPORT_640_manifest.json").write_text(
        json.dumps(
            {
                "reports": {
                    "REPORT_640_Pottery_Report.tif": {"status": "not_implemented_no_source_equivalent"},
                    "REPORT_640_Mass_Report.tif": {"status": "not_implemented_no_source_equivalent"},
                    "REPORT_640_FINAL_Zero_Point_Targets.tif": {"status": "not_implemented_no_source_equivalent"},
                }
            }
        ),
        encoding="utf-8",
    )
    (app_run_dir / "QA" / "sar" / "intermediates").mkdir(parents=True, exist_ok=True)
    (app_run_dir / "QA" / "sar" / "intermediates" / "sar_intermediate_manifest.json").write_text(
        json.dumps(
            {
                "stages": {
                    "post_rtc": {
                        "status": "not_implemented_no_source_equivalent",
                        "bands": {
                            "VV_dB": "post_rtc/final_VV_dB.npy",
                            "VH_dB": "post_rtc/final_VH_dB.npy",
                            "logRatio_dB": "post_rtc/final_logRatio_dB.npy",
                            "angle": "post_rtc/final_angle.npy",
                        },
                        "missing_reason": "contract-ambiguous notebook intermediate family",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    alias_cases = (
        Phase5Case("alias", "alias pass", "raster_alias", "alias_left.tif", "alias_right.tif"),
    )
    reference_cases = (
        Phase5Case("reference", "reference pass", "raster_reference", "reference_raster.tif", "reference_raster.tif", tolerance=0.0),
        Phase5Case(
            "reference",
            "reference expected mismatch",
            "npy_reference",
            "reference_fail.npy",
            "reference_fail.npy",
            tolerance=0.0,
            expected="xfail",
            xfail_reason="expected mismatch",
        ),
    )

    report = build_phase5_numeric_output_parity_summary(
        app_run_dir=app_run_dir,
        notebook_reference_bundle_dir=notebook_root,
        alias_cases=alias_cases,
        reference_cases=reference_cases,
    )

    assert report["summary"]["overall_status"] == "PASS_WITH_CLASSIFIED_EXCEPTIONS"
    assert report["summary"]["phase5d_alias_integrity_status"] == "PASS"
    assert report["summary"]["phase5e_reference_parity_status"] == "PASS_WITH_CLASSIFIED_EXCEPTIONS"
    assert report["summary"]["not_implemented_inventory_status"] == "PASS"
    assert report["summary"]["final_reference_proof_complete"] is False

    alias_results = report["phase5d_alias_integrity"]["cases"]
    assert alias_results[0]["status"] == "pass"

    reference_results = report["phase5e_reference_parity"]["cases"]
    assert [row["status"] for row in reference_results] == ["pass", "xfail"]
    assert reference_results[1]["classification"] == "value mismatch"

    entries = report["known_not_implemented_outputs"]["entries"]
    assert {entry["relative_path"] for entry in entries} == {
        "REPORT_640_Pottery_Report.tif",
        "REPORT_640_Mass_Report.tif",
        "REPORT_640_FINAL_Zero_Point_Targets.tif",
        "QA/sar/intermediates/post_rtc/final_VV_dB.npy",
        "QA/sar/intermediates/post_rtc/final_VH_dB.npy",
        "QA/sar/intermediates/post_rtc/final_logRatio_dB.npy",
        "QA/sar/intermediates/post_rtc/final_angle.npy",
    }
    assert all(entry["status"] == "not_implemented_no_source_equivalent" for entry in entries)
    assert all(entry["file_exists"] is False for entry in entries)


def test_phase5_numeric_output_parity_summary_resolves_sar_geotiff_reference_by_prefix(tmp_path: Path) -> None:
    app_run_dir = tmp_path / "runs" / "run-123"
    notebook_root = tmp_path / "reference_bundle"
    app_run_dir.mkdir(parents=True, exist_ok=True)
    notebook_root.mkdir(parents=True, exist_ok=True)

    _write_geotiff(
        app_run_dir / "GEOTIFF_RADAR_BANDS" / "RADAR_VV_dB_640_app.tif",
        value=3.0,
        dtype="float32",
        nodata=-9999.0,
    )
    _write_geotiff(
        notebook_root / "GEOTIFF_RADAR_BANDS" / "RADAR_VV_dB_640_reference_case.tif",
        value=3.0,
        dtype="float32",
        nodata=-9999.0,
    )

    (app_run_dir / "QA").mkdir(parents=True, exist_ok=True)
    (app_run_dir / "QA" / "REPORT_640_manifest.json").write_text(
        json.dumps(
            {
                "reports": {
                    "REPORT_640_Pottery_Report.tif": {"status": "not_implemented_no_source_equivalent"},
                    "REPORT_640_Mass_Report.tif": {"status": "not_implemented_no_source_equivalent"},
                    "REPORT_640_FINAL_Zero_Point_Targets.tif": {"status": "not_implemented_no_source_equivalent"},
                }
            }
        ),
        encoding="utf-8",
    )
    (app_run_dir / "QA" / "sar" / "intermediates").mkdir(parents=True, exist_ok=True)
    (app_run_dir / "QA" / "sar" / "intermediates" / "sar_intermediate_manifest.json").write_text(
        json.dumps(
            {
                "stages": {
                    "post_rtc": {
                        "status": "not_implemented_no_source_equivalent",
                        "bands": {
                            "VV_dB": "post_rtc/final_VV_dB.npy",
                            "VH_dB": "post_rtc/final_VH_dB.npy",
                            "logRatio_dB": "post_rtc/final_logRatio_dB.npy",
                            "angle": "post_rtc/final_angle.npy",
                        },
                        "missing_reason": "contract-ambiguous notebook intermediate family",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    report = build_phase5_numeric_output_parity_summary(
        app_run_dir=app_run_dir,
        notebook_reference_bundle_dir=notebook_root,
        alias_cases=(),
        reference_cases=(
            Phase5Case(
                "sar",
                "VV_dB geotiff reference",
                "raster_reference",
                "GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_app.tif",
                "GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_",
                tolerance=0.0,
            ),
        ),
    )

    assert report["phase5e_reference_parity"]["cases"][0]["status"] == "pass"
    assert report["phase5e_reference_parity"]["status"] == "PASS"


def _write_geotiff(path: Path, *, value: float, dtype: str, nodata: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype=dtype,
        crs="EPSG:32637",
        transform=from_origin(500000.0, 4100000.0, 10.0, 10.0),
        nodata=nodata,
    ) as dataset:
        dataset.write(np.full((1, 2, 2), value, dtype=np.float32))
