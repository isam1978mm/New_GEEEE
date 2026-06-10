"""Unit tests for D3B-2 end-to-end app-generated DEM curvature parity.

Synthetic app/reference dirs under tmp_path; raster reads are injected so the
tests need no rasterio/GDAL and touch no real D1C artifacts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from app.cli import dem_curvature_end_to_end_parity as cli
from app.pipeline.parity.dem_curvature_end_to_end_parity import (
    END_TO_END_ARTIFACTS,
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_REFERENCE_INVALID,
    compare_dem_curvature_end_to_end,
)
from app.pipeline.parity.dem_curvature_formula_parity import RawRaster
from app.services.reference_bundle_validator import REFERENCE_MANIFEST_NAME

NODATA = -9999.0
RELS = [rel for _name, rel in END_TO_END_ARTIFACTS]


def _arr(seed: int, n: int = 10) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(size=(n, n)).astype(np.float32)


def _write_dir(root: Path, rels: list[str]) -> None:
    for rel in rels:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(f"raster::{rel}".encode())


def _write_bundle_manifest(bundle: Path, rels: list[str]) -> None:
    files = []
    for rel in rels:
        data = f"raster::{rel}".encode()
        files.append({"relative_path": rel, "sha256": hashlib.sha256(data).hexdigest(),
                      "size_bytes": len(data), "role": "raster"})
    manifest = {"source_notebook": "notebooks/new.ipynb", "repo_commit": "abc",
                "created_at": "2026-06-10T00:00:00Z", "bundle_name": "syn", "files": files}
    (bundle / REFERENCE_MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")


def _setup(tmp_path: Path, app_arrays: dict[str, np.ndarray], ref_arrays: dict[str, np.ndarray]):
    app = tmp_path / "app"
    bundle = tmp_path / "bundle"
    _write_dir(app, RELS)
    _write_dir(bundle, RELS)
    _write_bundle_manifest(bundle, RELS)

    mapping: dict[Path, RawRaster] = {}
    for rel in RELS:
        mapping[app / rel] = RawRaster(app_arrays[rel].astype(np.float64), "float32", NODATA)
        mapping[bundle / rel] = RawRaster(ref_arrays[rel].astype(np.float64), "float32", NODATA)
    resolved = {Path(p).resolve(): r for p, r in mapping.items()}

    def reader(path: Path) -> RawRaster:
        return resolved[Path(path).resolve()]

    return app, bundle, reader


def test_dem_and_curvature_match_passes(tmp_path: Path) -> None:
    arrays = {rel: _arr(i) for i, rel in enumerate(RELS)}
    app, bundle, reader = _setup(tmp_path, arrays, arrays)
    result = compare_dem_curvature_end_to_end(app, bundle, raster_reader=reader)

    assert result.status == STATUS_PASSED
    assert result.dem_matches is True
    assert result.pass_count == 4
    assert "accepted" in result.diagnostic


def test_dem_mismatch_classified_as_upstream(tmp_path: Path) -> None:
    app_arrays = {rel: _arr(i) for i, rel in enumerate(RELS)}
    ref_arrays = dict(app_arrays)
    bad_dem = np.array(app_arrays["DEM_GEO8_TIFS/DEM_640.tif"], copy=True)
    bad_dem[5, 5] += 10.0  # interior DEM difference
    ref_arrays["DEM_GEO8_TIFS/DEM_640.tif"] = bad_dem
    app, bundle, reader = _setup(tmp_path, app_arrays, ref_arrays)

    result = compare_dem_curvature_end_to_end(app, bundle, raster_reader=reader)
    assert result.status == STATUS_FAILED
    assert result.dem_matches is False
    assert "upstream DEM/grid/source mismatch" in result.diagnostic


def test_dem_match_but_curvature_mismatch_is_integration_issue(tmp_path: Path) -> None:
    app_arrays = {rel: _arr(i) for i, rel in enumerate(RELS)}
    ref_arrays = dict(app_arrays)
    bad_curv = np.array(app_arrays["DEM_GEO8_TIFS/curv_plan_640.tif"], copy=True)
    bad_curv[5, 5] += 10.0
    ref_arrays["DEM_GEO8_TIFS/curv_plan_640.tif"] = bad_curv
    app, bundle, reader = _setup(tmp_path, app_arrays, ref_arrays)

    result = compare_dem_curvature_end_to_end(app, bundle, raster_reader=reader)
    assert result.status == STATUS_FAILED
    assert result.dem_matches is True
    assert "writer/path/integration issue" in result.diagnostic


def test_edge_only_difference_still_passes(tmp_path: Path) -> None:
    app_arrays = {rel: _arr(i) for i, rel in enumerate(RELS)}
    ref_arrays = dict(app_arrays)
    bad = np.array(app_arrays["DEM_GEO8_TIFS/curv_profile_640.tif"], copy=True)
    bad[0, 4] += 9.0  # border-only
    ref_arrays["DEM_GEO8_TIFS/curv_profile_640.tif"] = bad
    app, bundle, reader = _setup(tmp_path, app_arrays, ref_arrays)

    result = compare_dem_curvature_end_to_end(app, bundle, raster_reader=reader)
    assert result.status == STATUS_PASSED
    prof = next(a for a in result.artifacts if a.logical_name == "curv_profile_640")
    assert prof.status == "edge_or_nodata_only_mismatch"
    assert prof.interior_allclose


def test_missing_app_output(tmp_path: Path) -> None:
    arrays = {rel: _arr(i) for i, rel in enumerate(RELS)}
    app, bundle, reader = _setup(tmp_path, arrays, arrays)
    (app / "DEM_GEO8_TIFS" / "curv_plan_640.tif").unlink()
    result = compare_dem_curvature_end_to_end(app, bundle, raster_reader=reader)
    statuses = {a.logical_name: a.status for a in result.artifacts}
    assert statuses["curv_plan_640"] == "missing_app_output"
    assert result.status != STATUS_PASSED


def test_invalid_bundle_refuses(tmp_path: Path) -> None:
    app = tmp_path / "app"
    bundle = tmp_path / "bundle"
    _write_dir(app, RELS)
    bundle.mkdir()  # no manifest
    result = compare_dem_curvature_end_to_end(app, bundle)
    assert result.status == STATUS_REFERENCE_INVALID
    assert result.artifacts == ()


def test_cli_default_output_is_path_safe(tmp_path: Path, capsys) -> None:
    arrays = {rel: _arr(i) for i, rel in enumerate(RELS)}
    app, bundle, reader = _setup(tmp_path, arrays, arrays)
    import app.pipeline.parity.dem_curvature_end_to_end_parity as mod

    orig = mod._read_raw_raster
    mod._read_raw_raster = reader  # type: ignore[assignment]
    try:
        exit_code = cli.main(["--app-output-dir", str(app), "--bundle-dir", str(bundle)])
    finally:
        mod._read_raw_raster = orig  # type: ignore[assignment]
    out = capsys.readouterr().out

    assert exit_code == 0
    payload = json.loads(out)
    assert "artifacts" not in payload
    assert "interior_max_abs_diff" in payload
    assert str(tmp_path) not in out
    assert ".tif" not in out
