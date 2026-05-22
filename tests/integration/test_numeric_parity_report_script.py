from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

from app.pipeline.stages.dem import write_raster_sidecar
from app.services.grid import build_grid_manifest
from app.services.numeric_parity_report import NUMERIC_PARITY_REPORT_PREFIX, write_numeric_parity_report


def test_numeric_parity_report_script_writes_local_only_reports_without_absolute_paths(tmp_path: Path) -> None:
    notebook_root = tmp_path / "notebook_outputs"
    app_run_dir = tmp_path / "app_run" / "run-123"
    output_dir = tmp_path / "reports"
    notebook_root.mkdir(parents=True, exist_ok=True)
    app_run_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_grid_manifest(35.0, -110.0)
    _write_matching_raster(notebook_root / "dem.tif", manifest)
    _write_matching_raster(app_run_dir / "dem.tif", manifest)
    np.save(notebook_root / "dem.npy", np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32))
    np.save(app_run_dir / "dem.npy", np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32))
    (notebook_root / "grid_manifest.json").write_text(
        json.dumps({"epsg": manifest.epsg, "scale_m": manifest.scale_m, "size_px": manifest.size_px}, sort_keys=True),
        encoding="utf-8",
    )
    (app_run_dir / "grid_manifest.json").write_text(
        json.dumps({"epsg": manifest.epsg, "scale_m": manifest.scale_m, "size_px": manifest.size_px}, sort_keys=True),
        encoding="utf-8",
    )

    json_path, csv_path = write_numeric_parity_report(
        notebook_root=notebook_root,
        app_run_dir=app_run_dir,
        output_dir=output_dir,
    )

    assert json_path == output_dir / f"{NUMERIC_PARITY_REPORT_PREFIX}_run-123.json"
    assert csv_path == output_dir / f"{NUMERIC_PARITY_REPORT_PREFIX}_run-123.csv"

    report = json.loads(json_path.read_text(encoding="utf-8"))
    serialized = json.dumps(report, sort_keys=True)
    assert report["artifact_class"] == "FILESYSTEM_ONLY"
    assert report["local_only"] is True
    assert "C:\\" not in serialized
    assert "/home/" not in serialized
    assert "/Users/" not in serialized
    assert any(row["status"] == "PASS" for row in report["rows"])
    assert any(row["status"] == "SKIP_MISSING_APP" for row in report["rows"])
    assert any(row["app_file"] == "dem.tif" for row in report["rows"])

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert any(row["app_file"] == "dem.tif" and row["status"] == "PASS" for row in rows)


def _write_matching_raster(path: Path, manifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    array = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    Image.fromarray(array).save(path, format="TIFF")
    write_raster_sidecar(path, grid_manifest=manifest, nodata=-9999.0, dtype="float32", shape=array.shape)
