"""Unit tests for the D3 DEM curvature reference comparison and its CLI.

All rasters and bundles are synthetic and created under pytest ``tmp_path``; no
real frozen D1 reference artifacts are read or committed. Raster reading is
injected with a lightweight numpy-backed reader so the comparison logic runs
without rasterio/GDAL installed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from app.cli import dem_curvature_reference_comparison as cli
from app.pipeline.parity.dem_curvature_reference_comparison import (
    CURVATURE_ARTIFACTS,
    OVERALL_FAILED,
    OVERALL_PASSED,
    OVERALL_REFERENCE_INVALID,
    RasterData,
    compare_dem_curvature_references,
)
from app.services.reference_bundle_validator import REFERENCE_MANIFEST_NAME

CURV_FILES = [filename for _name, filename in CURVATURE_ARTIFACTS]


def _raster(values: np.ndarray, *, dtype: str = "float32", nodata: float | None = None) -> RasterData:
    arr = np.asarray(values, dtype=np.float64)
    return RasterData(
        values=arr,
        shape=tuple(int(v) for v in arr.shape),
        dtype=dtype,
        band_count=1,
        crs="EPSG:32637",
        transform=(10.0, 0.0, 500000.0, 0.0, -10.0, 4000000.0),
        nodata=nodata,
    )


def _write_bundle(bundle: Path, filenames: list[str]) -> None:
    """Write placeholder files + a D2-valid reference_manifest.json."""

    bundle.mkdir(parents=True, exist_ok=True)
    files = []
    for name in filenames:
        data = f"raster-bytes::{name}".encode()
        (bundle / name).parent.mkdir(parents=True, exist_ok=True)
        (bundle / name).write_bytes(data)
        files.append(
            {
                "relative_path": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size_bytes": len(data),
                "role": "raster",
            }
        )
    manifest = {
        "source_notebook": "notebooks/new.ipynb",
        "repo_commit": "abc1234",
        "created_at": "2026-06-10T00:00:00Z",
        "bundle_name": "synthetic_d3_bundle",
        "files": files,
    }
    (bundle / REFERENCE_MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")


def _write_app(app_dir: Path, filenames: list[str]) -> None:
    app_dir.mkdir(parents=True, exist_ok=True)
    for name in filenames:
        (app_dir / name).parent.mkdir(parents=True, exist_ok=True)
        (app_dir / name).write_bytes(f"app-bytes::{name}".encode())


def _reader_for(mapping: dict[Path, RasterData]):
    resolved = {Path(p).resolve(): r for p, r in mapping.items()}

    def reader(path: Path) -> RasterData:
        return resolved[Path(path).resolve()]

    return reader


def _matching_setup(tmp_path: Path, base: np.ndarray):
    app = tmp_path / "app"
    bundle = tmp_path / "bundle"
    _write_app(app, CURV_FILES)
    _write_bundle(bundle, CURV_FILES)
    mapping: dict[Path, RasterData] = {}
    for name in CURV_FILES:
        mapping[app / name] = _raster(base)
        mapping[bundle / name] = _raster(base)
    return app, bundle, mapping


# --- pass / fail core --------------------------------------------------------


def test_exact_match_passes(tmp_path: Path) -> None:
    base = np.array([[1.0, 2.0], [3.0, 4.0]])
    app, bundle, mapping = _matching_setup(tmp_path, base)
    result = compare_dem_curvature_references(app, bundle, raster_reader=_reader_for(mapping))

    assert result.status == OVERALL_PASSED
    assert result.pass_count == 3
    assert result.compared_count == 3
    assert result.missing_count == 0
    assert all(a.passed for a in result.artifacts)


def test_missing_app_output_fails(tmp_path: Path) -> None:
    base = np.array([[1.0, 2.0], [3.0, 4.0]])
    app, bundle, mapping = _matching_setup(tmp_path, base)
    (app / CURV_FILES[0]).unlink()  # remove one app output

    result = compare_dem_curvature_references(app, bundle, raster_reader=_reader_for(mapping))
    assert result.status != OVERALL_PASSED
    assert result.missing_count == 1
    statuses = {a.logical_name: a.status for a in result.artifacts}
    assert statuses[CURVATURE_ARTIFACTS[0][0]] == "missing_app_output"


def test_missing_reference_output_fails(tmp_path: Path) -> None:
    base = np.array([[1.0, 2.0], [3.0, 4.0]])
    app = tmp_path / "app"
    bundle = tmp_path / "bundle"
    _write_app(app, CURV_FILES)
    # Reference bundle is missing one curvature file (still a valid D2 bundle).
    present = CURV_FILES[1:]
    _write_bundle(bundle, present)
    mapping = {app / n: _raster(base) for n in CURV_FILES}
    mapping.update({bundle / n: _raster(base) for n in present})

    result = compare_dem_curvature_references(app, bundle, raster_reader=_reader_for(mapping))
    assert result.status != OVERALL_PASSED
    assert result.missing_count == 1
    statuses = {a.logical_name: a.status for a in result.artifacts}
    assert statuses[CURVATURE_ARTIFACTS[0][0]] == "missing_reference_output"


def test_shape_mismatch_fails(tmp_path: Path) -> None:
    base = np.array([[1.0, 2.0], [3.0, 4.0]])
    app, bundle, mapping = _matching_setup(tmp_path, base)
    # Override the app raster for one artifact with a different shape.
    mapping[app / CURV_FILES[0]] = _raster(np.array([[1.0, 2.0, 3.0]]))

    result = compare_dem_curvature_references(app, bundle, raster_reader=_reader_for(mapping))
    assert result.status == OVERALL_FAILED
    assert result.shape_mismatch_count == 1
    statuses = {a.logical_name: a.status for a in result.artifacts}
    assert statuses[CURVATURE_ARTIFACTS[0][0]] == "shape_mismatch"


def test_numeric_tolerance_pass(tmp_path: Path) -> None:
    base = np.array([[1.0, 2.0], [3.0, 4.0]])
    app, bundle, mapping = _matching_setup(tmp_path, base)
    # Perturb app values by less than the default atol.
    mapping[app / CURV_FILES[0]] = _raster(base + 1e-9)

    result = compare_dem_curvature_references(app, bundle, raster_reader=_reader_for(mapping))
    assert result.status == OVERALL_PASSED
    assert result.pass_count == 3


def test_numeric_tolerance_fail(tmp_path: Path) -> None:
    base = np.array([[1.0, 2.0], [3.0, 4.0]])
    app, bundle, mapping = _matching_setup(tmp_path, base)
    mapping[app / CURV_FILES[0]] = _raster(base + 1e-3)  # well outside default tolerance

    result = compare_dem_curvature_references(
        app, bundle, atol=1e-6, rtol=0.0, raster_reader=_reader_for(mapping)
    )
    assert result.status == OVERALL_FAILED
    statuses = {a.logical_name: a.status for a in result.artifacts}
    assert statuses[CURVATURE_ARTIFACTS[0][0]] == "value_mismatch"
    failing = next(a for a in result.artifacts if a.logical_name == CURVATURE_ARTIFACTS[0][0])
    assert failing.max_abs_diff is not None and failing.max_abs_diff > 1e-6


def test_nodata_nan_handling(tmp_path: Path) -> None:
    # NaNs in matching positions are excluded; finite values match -> passes.
    base = np.array([[1.0, np.nan], [3.0, 4.0]])
    app, bundle, mapping = _matching_setup(tmp_path, base)

    result = compare_dem_curvature_references(app, bundle, raster_reader=_reader_for(mapping))
    assert result.status == OVERALL_PASSED
    artifact = result.artifacts[0]
    assert artifact.finite_pixel_count == 3
    assert artifact.compared_pixel_count == 3  # the NaN pixel is excluded


def test_invalid_reference_bundle_refuses_comparison(tmp_path: Path) -> None:
    app = tmp_path / "app"
    bundle = tmp_path / "bundle"
    _write_app(app, CURV_FILES)
    bundle.mkdir()  # no manifest -> D2 invalid

    result = compare_dem_curvature_references(app, bundle)
    assert result.status == OVERALL_REFERENCE_INVALID
    assert result.compared_count == 0
    assert result.artifacts == ()


# --- CLI ---------------------------------------------------------------------


def test_cli_default_output_does_not_expose_detailed_paths(tmp_path: Path, capsys, monkeypatch) -> None:
    base = np.array([[1.0, 2.0], [3.0, 4.0]])
    app, bundle, mapping = _matching_setup(tmp_path, base)
    mapping[app / CURV_FILES[0]] = _raster(base + 1e-3)  # force a failure

    # Inject the numpy-backed reader as the default backend for the CLI path.
    monkeypatch.setattr(
        "app.pipeline.parity.dem_curvature_reference_comparison.default_raster_reader",
        _reader_for(mapping),
    )

    exit_code = cli.main(
        ["--app-output-dir", str(app), "--bundle-dir", str(bundle), "--atol", "1e-6", "--rtol", "0"]
    )
    out = capsys.readouterr().out

    assert exit_code == 1
    payload = json.loads(out)
    # Safe summary keys only; no raw paths / per-file detail block.
    assert "artifacts" not in payload
    assert "max_abs_diff" in payload and "pass" in payload
    assert "curv_laplacian_640" in payload["max_abs_diff"]
    assert str(tmp_path) not in out
    assert "relative_path" not in out
    assert ".tif" not in out  # filenames are detail-only


def test_cli_show_details_includes_paths(tmp_path: Path, capsys, monkeypatch) -> None:
    base = np.array([[1.0, 2.0], [3.0, 4.0]])
    app, bundle, mapping = _matching_setup(tmp_path, base)
    monkeypatch.setattr(
        "app.pipeline.parity.dem_curvature_reference_comparison.default_raster_reader",
        _reader_for(mapping),
    )

    exit_code = cli.main(["--app-output-dir", str(app), "--bundle-dir", str(bundle), "--show-details"])
    out = capsys.readouterr().out

    assert exit_code == 0
    payload = json.loads(out)
    assert "artifacts" in payload
    assert payload["artifacts"]["curv_laplacian_640"]["filename"] == "DEM_GEO8_TIFS/curv_laplacian_640.tif"
