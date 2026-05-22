from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

from app.pipeline.stages.dem import write_raster_sidecar
from app.services.grid import build_grid_manifest
from app.services.numeric_parity_report import (
    ComparisonSpec,
    Tolerance,
    canonicalize_csv_rows,
    canonicalize_json_payload,
    canonicalize_kmz_payload,
    compare_arrays,
    compare_raster_files,
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


def test_compare_raster_files_checks_sidecar_metadata(tmp_path: Path) -> None:
    manifest = build_grid_manifest(35.0, -110.0)
    notebook_path = tmp_path / "notebook_dem.tif"
    app_path = tmp_path / "app_dem.tif"
    array = np.arange(4, dtype=np.float32).reshape(2, 2)
    Image.fromarray(array).save(notebook_path, format="TIFF")
    Image.fromarray(array).save(app_path, format="TIFF")
    write_raster_sidecar(notebook_path, grid_manifest=manifest, nodata=-9999.0, dtype="float32", shape=array.shape)

    shifted_manifest = manifest.model_copy(update={"crs_transform": [10.0, 0.0, 123.0, 0.0, -10.0, 456.0]})
    write_raster_sidecar(app_path, grid_manifest=shifted_manifest, nodata=-9999.0, dtype="float32", shape=array.shape)

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
