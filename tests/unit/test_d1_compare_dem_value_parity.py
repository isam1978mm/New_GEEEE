from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import d1_compare_dem_value_parity as dem_value
from app.pipeline.parity.dem_curvature_end_to_end_parity import END_TO_END_ARTIFACTS
from app.pipeline.parity.dem_curvature_formula_parity import RawRaster

NODATA = -9999.0
RELS = [rel for _name, rel in END_TO_END_ARTIFACTS]


def arr(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(size=(8, 8)).astype(np.float32)


def setup_dirs(tmp_path: Path, app_arrays: dict[str, np.ndarray], ref_arrays: dict[str, np.ndarray]):
    app = tmp_path / "app"
    ref = tmp_path / "ref"
    mapping = {}
    for rel in RELS:
        app_path = app / rel
        ref_path = ref / rel
        app_path.parent.mkdir(parents=True, exist_ok=True)
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        app_path.write_text("placeholder", encoding="utf-8")
        ref_path.write_text("placeholder", encoding="utf-8")
        mapping[app_path.resolve()] = RawRaster(app_arrays[rel].astype(np.float64), "float32", NODATA)
        mapping[ref_path.resolve()] = RawRaster(ref_arrays[rel].astype(np.float64), "float32", NODATA)

    def reader(path: Path) -> RawRaster:
        return mapping[path.resolve()]

    return app, ref, reader


def test_dem_value_parity_passes_when_arrays_match(tmp_path: Path) -> None:
    arrays = {rel: arr(i) for i, rel in enumerate(RELS)}
    app, ref, reader = setup_dirs(tmp_path, arrays, arrays)
    result = dem_value.compare_d1_dem_value_parity(
        app_output_dir=app,
        reference_dem_root=ref,
        raster_reader=reader,
    )
    assert result["status"] == "passed"
    assert result["pass_count"] == 4
    assert result["fail_count"] == 0
    assert result["dem_matches"] is True


def test_dem_value_parity_fails_on_interior_dem_mismatch(tmp_path: Path) -> None:
    app_arrays = {rel: arr(i) for i, rel in enumerate(RELS)}
    ref_arrays = dict(app_arrays)
    bad = np.array(app_arrays["DEM_GEO8_TIFS/DEM_640.tif"], copy=True)
    bad[4, 4] += 5.0
    ref_arrays["DEM_GEO8_TIFS/DEM_640.tif"] = bad
    app, ref, reader = setup_dirs(tmp_path, app_arrays, ref_arrays)
    result = dem_value.compare_d1_dem_value_parity(
        app_output_dir=app,
        reference_dem_root=ref,
        raster_reader=reader,
    )
    assert result["status"] == "failed"
    assert result["fail_count"] == 1
    assert result["dem_matches"] is False


def test_dem_value_parity_reports_missing_file(tmp_path: Path) -> None:
    arrays = {rel: arr(i) for i, rel in enumerate(RELS)}
    app, ref, reader = setup_dirs(tmp_path, arrays, arrays)
    (app / "DEM_GEO8_TIFS" / "curv_plan_640.tif").unlink()
    result = dem_value.compare_d1_dem_value_parity(
        app_output_dir=app,
        reference_dem_root=ref,
        raster_reader=reader,
    )
    assert result["status"] == "incomplete"
    assert result["missing_count"] == 1


def test_cli_writes_report_without_private_root_paths(tmp_path: Path) -> None:
    arrays = {rel: arr(i) for i, rel in enumerate(RELS)}
    app, ref, reader = setup_dirs(tmp_path, arrays, arrays)
    original = dem_value._read_raw_raster
    dem_value._read_raw_raster = reader
    report = tmp_path / "report.json"
    try:
        rc = dem_value.main([
            "--app-output-dir",
            str(app),
            "--reference-dem-root",
            str(ref),
            "--report",
            str(report),
        ])
    finally:
        dem_value._read_raw_raster = original
    assert rc == 0
    text = report.read_text(encoding="utf-8")
    assert str(tmp_path) not in text
    assert "status" in text
