from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import d1_compare_report_value_parity as report_value
from app.pipeline.parity.report_640_verify import REPORT_640_OUTPUT_NAMES


def arr(seed: int) -> np.ma.MaskedArray:
    rng = np.random.default_rng(seed)
    return np.ma.asarray(rng.normal(size=(1, 6, 6)).astype(np.float32))


def make_raster(values: np.ma.MaskedArray) -> report_value.ReportRaster:
    return report_value.ReportRaster(
        values=values,
        dtype="float32",
        nodata=(-9999.0,),
        width=6,
        height=6,
        count=1,
        crs="EPSG:3857",
        transform=(1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0),
    )


def setup_dirs(tmp_path: Path, app_arrays: dict[str, np.ma.MaskedArray], ref_arrays: dict[str, np.ma.MaskedArray]):
    app = tmp_path / "app"
    ref = tmp_path / "ref"
    mapping = {}
    for name in REPORT_640_OUTPUT_NAMES:
        app_path = app / "nested" / name
        ref_path = ref / "nested" / name
        app_path.parent.mkdir(parents=True, exist_ok=True)
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        app_path.write_text("placeholder", encoding="utf-8")
        ref_path.write_text("placeholder", encoding="utf-8")
        mapping[app_path.resolve()] = make_raster(app_arrays[name])
        mapping[ref_path.resolve()] = make_raster(ref_arrays[name])

    def reader(path: Path) -> report_value.ReportRaster:
        return mapping[path.resolve()]

    return app, ref, reader


def test_report_value_parity_passes_when_arrays_match(tmp_path: Path) -> None:
    arrays = {name: arr(i) for i, name in enumerate(REPORT_640_OUTPUT_NAMES)}
    app, ref, reader = setup_dirs(tmp_path, arrays, arrays)
    result = report_value.compare_d1_report_value_parity(
        app_output_dir=app,
        reference_report_root=ref,
        reader=reader,
    )
    assert result["status"] == "passed"
    assert result["pass_count"] == len(REPORT_640_OUTPUT_NAMES)
    assert result["fail_count"] == 0


def test_report_value_parity_fails_on_value_mismatch(tmp_path: Path) -> None:
    app_arrays = {name: arr(i) for i, name in enumerate(REPORT_640_OUTPUT_NAMES)}
    ref_arrays = dict(app_arrays)
    first = REPORT_640_OUTPUT_NAMES[0]
    bad = np.ma.asarray(np.array(app_arrays[first], copy=True))
    bad[0, 3, 3] += 10.0
    ref_arrays[first] = bad
    app, ref, reader = setup_dirs(tmp_path, app_arrays, ref_arrays)
    result = report_value.compare_d1_report_value_parity(
        app_output_dir=app,
        reference_report_root=ref,
        reader=reader,
    )
    assert result["status"] == "failed"
    assert result["fail_count"] == 1


def test_report_value_parity_reports_missing_file(tmp_path: Path) -> None:
    arrays = {name: arr(i) for i, name in enumerate(REPORT_640_OUTPUT_NAMES)}
    app, ref, reader = setup_dirs(tmp_path, arrays, arrays)
    (app / "nested" / REPORT_640_OUTPUT_NAMES[1]).unlink()
    result = report_value.compare_d1_report_value_parity(
        app_output_dir=app,
        reference_report_root=ref,
        reader=reader,
    )
    assert result["status"] == "incomplete"
    assert result["missing_count"] == 1


def test_cli_writes_report_without_root_paths(tmp_path: Path) -> None:
    arrays = {name: arr(i) for i, name in enumerate(REPORT_640_OUTPUT_NAMES)}
    app, ref, reader = setup_dirs(tmp_path, arrays, arrays)
    original = report_value.read_report_raster
    report_value.read_report_raster = reader
    report = tmp_path / "report.json"
    try:
        rc = report_value.main([
            "--app-output-dir",
            str(app),
            "--reference-report-root",
            str(ref),
            "--report",
            str(report),
        ])
    finally:
        report_value.read_report_raster = original
    assert rc == 0
    text = report.read_text(encoding="utf-8")
    assert str(tmp_path) not in text
    assert "status" in text
