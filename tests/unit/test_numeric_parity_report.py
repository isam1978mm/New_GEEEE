from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.services.numeric_parity_report import (
    ComparisonSpec,
    Tolerance,
    build_default_comparison_specs,
    canonicalize_csv_rows,
    canonicalize_json_payload,
    canonicalize_kmz_payload,
    compare_arrays,
    compare_raster_files,
    resolve_notebook_file,
)


def test_compare_arrays_uses_float_tolerance() -> None:
    notebook = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    app = notebook + np.array([[0.0, 1e-6], [0.0, -1e-6]], dtype=np.float32)

    close_result = compare_arrays(notebook, app, tolerance=Tolerance(abs_tol=1e-5, rel_tol=1e-5))
    strict_result = compare_arrays(notebook, app, tolerance=Tolerance(abs_tol=1e-8, rel_tol=1e-8))

    assert close_result["pass"] is True
    assert close_result["shape_match"] is True
    assert close_result["differing_count"] == 0
    assert strict_result["pass"] is False
    assert strict_result["differing_count"] == 2


def test_compare_raster_files_checks_real_tiff_metadata(tmp_path: Path) -> None:
    notebook_path = tmp_path / "notebook_dem.tif"
    app_path = tmp_path / "app_dem.tif"
    array = np.arange(4, dtype=np.float32).reshape(2, 2)
    _write_geotiff(notebook_path, array=array, crs="EPSG:32612", transform=from_origin(500000.0, 4100000.0, 10.0, 10.0))
    _write_geotiff(app_path, array=array, crs="EPSG:32612", transform=from_origin(500010.0, 4100000.0, 10.0, 10.0))

    row = compare_raster_files(
        ComparisonSpec(family="dem_core", comparison_type="raster", app_file="dem.tif", notebook_candidates=("dem.tif",)),
        notebook_path=notebook_path,
        app_path=app_path,
        notebook_file="dem.tif",
    )

    assert row.status == "FAIL"
    assert row.shape_match is True
    assert row.crs_match is True
    assert row.transform_match is False
    assert row.dtype_match is True
    assert "missing" not in row.notes


def test_compare_raster_files_fails_when_real_tiff_georef_metadata_is_missing(tmp_path: Path) -> None:
    notebook_path = tmp_path / "notebook_dem.tif"
    app_path = tmp_path / "app_dem.tif"
    array = np.arange(4, dtype=np.float32).reshape(2, 2)
    _write_geotiff(notebook_path, array=array, crs="EPSG:32612", transform=from_origin(500000.0, 4100000.0, 10.0, 10.0))
    _write_geotiff(app_path, array=array, crs=None, transform=None)

    row = compare_raster_files(
        ComparisonSpec(family="dem_core", comparison_type="raster", app_file="dem.tif", notebook_candidates=("dem.tif",)),
        notebook_path=notebook_path,
        app_path=app_path,
        notebook_file="dem.tif",
    )

    assert row.status == "FAIL"
    assert row.crs_match is False
    assert row.transform_match is False
    assert "missing_crs_metadata" in row.notes
    assert "missing_transform_metadata" in row.notes


def test_csv_and_json_canonicalization_strip_unstable_fields(tmp_path: Path) -> None:
    csv_path = tmp_path / "objects.csv"
    csv_path.write_text(
        "object_id,score,run_id,absolute_path\n2,1.500000000,C:\\\\temp\\\\b\n1,1.5,run-1,C:\\\\temp\\\\a\n",
        encoding="utf-8",
    )
    canonical_csv = canonicalize_csv_rows(csv_path)

    assert canonical_csv == [
        {"object_id": 1, "score": 1.5},
        {"object_id": 2, "score": 1.5},
    ]

    payload = {
        "run_id": "run-1",
        "created_at": "2026-05-22T12:00:00Z",
        "metrics": {"score": 1.234567891, "path_hint": "C:/temp/file.txt"},
        "features": [
            {"properties": {"export_role": "b"}, "geometry": {"type": "Point", "coordinates": [2.0, 1.0]}},
            {"properties": {"export_role": "a"}, "geometry": {"type": "Point", "coordinates": [1.0, 2.0]}},
        ],
    }
    canonical_json = canonicalize_json_payload(payload)

    assert "run_id" not in canonical_json
    assert "created_at" not in canonical_json
    assert canonical_json["metrics"]["score"] == 1.23456789
    assert "path_hint" not in canonical_json["metrics"]
    assert [item["properties"]["export_role"] for item in canonical_json["features"]] == ["a", "b"]


def test_kmz_canonicalization_uses_kml_content_not_zip_bytes(tmp_path: Path) -> None:
    kmz_path = tmp_path / "location.kmz"
    with zipfile.ZipFile(kmz_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "doc.kml",
            """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>site_point</name>
      <Point>
        <coordinates>-110.123456789,35.123456789,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>
""",
        )

    payload = canonicalize_kmz_payload(kmz_path)

    assert payload["feature_count"] == 1
    assert payload["placemarks"][0]["name"] == "site_point"
    assert payload["placemarks"][0]["coordinates"] == [[-110.123457, 35.123457, 0.0]]


def test_notebook_mapping_patterns_cover_requested_downloaded_names(tmp_path: Path) -> None:
    files = [
        "DEM_GEO8_TIFS/DEM_640.tif",
        "DEM_GEO8_TIFS/slope_local_640.tif",
        "DEM_GEO8_TIFS/roughness_local_640.tif",
        "DEM_GEO8_TIFS/tpi_local_640.tif",
        "GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_match.tif",
        "GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_match.tif",
        "GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_match.tif",
        "GEOTIFF_RADAR_BANDS/RADAR_angle_640_match.tif",
        "NPY_RADAR_BANDS/RADAR_VV_dB_640_match.npy",
        "NPY_STACKS/RADAR_STACK_HWC_640_match.npy",
        "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_match.tif",
        "QA/FOCUS_" "MASK_17m_inside_640.tif",
        "SUMMARY_RADAR_match.csv",
    ]
    for relative_path in files:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")

    specs = build_default_comparison_specs()
    expected_matches = {
        "dem.tif": "DEM_GEO8_TIFS/DEM_640.tif",
        "slope.tif": "DEM_GEO8_TIFS/slope_local_640.tif",
        "roughness.tif": "DEM_GEO8_TIFS/roughness_local_640.tif",
        "TPI.tif": "DEM_GEO8_TIFS/tpi_local_640.tif",
        "VV_dB.tif": "GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_match.tif",
        "VH_dB.tif": "GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_match.tif",
        "logRatio_dB.tif": "GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_match.tif",
        "incidence.tif": "GEOTIFF_RADAR_BANDS/RADAR_angle_640_match.tif",
        "npy_radar_bands/VV_dB.npy": "NPY_RADAR_BANDS/RADAR_VV_dB_640_match.npy",
        "stacks/tensor_support/radar_linear_support_stack.npy": "NPY_STACKS/RADAR_STACK_HWC_640_match.npy",
        "hypercube.tif": "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_match.tif",
        "full_job/focus/focus_zone_17m.tif": "QA/FOCUS_" "MASK_17m_inside_640.tif",
        "qa/sar/sar_summary.csv": "SUMMARY_RADAR_match.csv",
    }

    for app_file, notebook_path in expected_matches.items():
        spec = next(item for item in specs if item.app_file == app_file)
        resolved_path, status = resolve_notebook_file(tmp_path, spec.notebook_candidates)
        assert status == "ok"
        assert resolved_path == notebook_path


def _write_geotiff(
    path: Path,
    *,
    array: np.ndarray,
    crs: str | None,
    transform,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": int(array.shape[0]),
        "width": int(array.shape[1]),
        "count": 1,
        "dtype": "float32",
    }
    if crs is not None:
        profile["crs"] = crs
    if transform is not None:
        profile["transform"] = transform
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(array.astype(np.float32), 1)
