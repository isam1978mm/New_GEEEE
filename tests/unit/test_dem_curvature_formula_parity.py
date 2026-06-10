"""Unit tests for D3B-1 DEM curvature formula-isolation parity.

Synthetic DEM + bundles under tmp_path; raster reads are injected so the test
needs no rasterio/GDAL and touches no real D1C artifacts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from app.cli import dem_curvature_formula_parity as cli
from app.pipeline.parity.dem_curvature_formula_parity import (
    CURVATURE_TARGETS,
    REFERENCE_DEM_PATH,
    RawRaster,
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_REFERENCE_INVALID,
    compare_dem_curvature_formula_parity,
)
from app.pipeline.stages.dem_derivatives import compute_dem_derivatives
from app.services.reference_bundle_validator import REFERENCE_MANIFEST_NAME

NODATA = -9999.0
SCALE = 10.0


def _dem(n: int = 10) -> np.ndarray:
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float64)
    # Smooth quadratic-ish surface so curvature is finite and non-trivial.
    return (0.01 * xx**2 + 0.008 * yy**2 + 0.5 * xx - 0.3 * yy + 100.0).astype(np.float32)


def _ref_curvatures(dem: np.ndarray) -> dict[str, np.ndarray]:
    out = compute_dem_derivatives(dem, nodata=NODATA, scale_m=SCALE)
    return {ref_rel: out[key] for _name, key, ref_rel in CURVATURE_TARGETS}


def _build(tmp_path: Path, dem: np.ndarray, ref_overrides: dict[str, np.ndarray] | None = None):
    bundle = tmp_path / "bundle"
    bundle.mkdir(parents=True, exist_ok=True)
    refs = _ref_curvatures(dem)
    if ref_overrides:
        refs.update(ref_overrides)

    mapping: dict[Path, RawRaster] = {}
    files = []
    rel_paths = [REFERENCE_DEM_PATH] + [r for _n, _k, r in CURVATURE_TARGETS]
    for rel in rel_paths:
        target = bundle / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        data = f"raster::{rel}".encode()
        target.write_bytes(data)
        files.append(
            {"relative_path": rel, "sha256": hashlib.sha256(data).hexdigest(),
             "size_bytes": len(data), "role": "raster"}
        )
        if rel == REFERENCE_DEM_PATH:
            mapping[target] = RawRaster(dem.astype(np.float64), "float32", NODATA)
        else:
            mapping[target] = RawRaster(np.asarray(refs[rel], dtype=np.float64), "float32", NODATA)

    manifest = {
        "source_notebook": "notebooks/new.ipynb", "repo_commit": "abc1234",
        "created_at": "2026-06-10T00:00:00Z", "bundle_name": "synthetic_d3b1", "files": files,
    }
    (bundle / REFERENCE_MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")

    resolved = {Path(p).resolve(): r for p, r in mapping.items()}

    def reader(path: Path) -> RawRaster:
        return resolved[Path(path).resolve()]

    return bundle, reader


def test_formula_parity_passes_for_same_dem(tmp_path: Path) -> None:
    dem = _dem()
    bundle, reader = _build(tmp_path, dem)
    result = compare_dem_curvature_formula_parity(
        bundle, atol=1e-6, rtol=1e-6, scale_m=SCALE, raster_reader=reader
    )
    assert result.status == STATUS_PASSED
    assert result.pass_count == 3
    for a in result.artifacts:
        assert a.interior_allclose
        assert a.interior_max_abs_diff == 0.0


def test_interior_mismatch_is_formula_finding(tmp_path: Path) -> None:
    dem = _dem()
    refs = _ref_curvatures(dem)
    # Perturb an interior pixel of the plan curvature reference.
    bad = np.array(refs["DEM_GEO8_TIFS/curv_plan_640.tif"], copy=True)
    bad[5, 5] += 1.0
    bundle, reader = _build(tmp_path, dem, {"DEM_GEO8_TIFS/curv_plan_640.tif": bad})

    result = compare_dem_curvature_formula_parity(
        bundle, atol=1e-6, rtol=1e-6, scale_m=SCALE, raster_reader=reader
    )
    assert result.status == STATUS_FAILED
    statuses = {a.logical_name: a.status for a in result.artifacts}
    assert statuses["curv_plan_640"] == "interior_mismatch"
    plan = next(a for a in result.artifacts if a.logical_name == "curv_plan_640")
    assert plan.interior_max_abs_diff is not None and plan.interior_max_abs_diff > 1e-6


def test_edge_only_mismatch_reported_separately(tmp_path: Path) -> None:
    dem = _dem()
    refs = _ref_curvatures(dem)
    bad = np.array(refs["DEM_GEO8_TIFS/curv_profile_640.tif"], copy=True)
    bad[0, 3] += 5.0  # border pixel only
    bundle, reader = _build(tmp_path, dem, {"DEM_GEO8_TIFS/curv_profile_640.tif": bad})

    result = compare_dem_curvature_formula_parity(
        bundle, atol=1e-6, rtol=1e-6, scale_m=SCALE, raster_reader=reader
    )
    # Interior is clean -> overall still passes; the edge diff is classified, not hidden.
    assert result.status == STATUS_PASSED
    prof = next(a for a in result.artifacts if a.logical_name == "curv_profile_640")
    assert prof.status == "edge_or_nodata_only_mismatch"
    assert prof.interior_allclose
    assert prof.edge_nodata_max_abs_diff is not None and prof.edge_nodata_max_abs_diff > 1e-6


def test_nodata_pixels_excluded(tmp_path: Path) -> None:
    dem = _dem()
    dem[2, 2] = NODATA  # inject a nodata cell
    bundle, reader = _build(tmp_path, dem)
    result = compare_dem_curvature_formula_parity(
        bundle, atol=1e-6, rtol=1e-6, scale_m=SCALE, raster_reader=reader
    )
    assert result.status == STATUS_PASSED
    lap = next(a for a in result.artifacts if a.logical_name == "curv_laplacian_640")
    # The nodata cell (and its propagation) is excluded from compared pixels.
    assert lap.finite_compared_count < dem.size


def test_missing_reference_output(tmp_path: Path) -> None:
    dem = _dem()
    bundle, reader = _build(tmp_path, dem)
    # Remove one reference curvature file (manifest no longer lists it -> rebuild).
    (bundle / "DEM_GEO8_TIFS" / "curv_profile_640.tif").unlink()
    manifest = json.loads((bundle / REFERENCE_MANIFEST_NAME).read_text())
    manifest["files"] = [f for f in manifest["files"]
                         if f["relative_path"] != "DEM_GEO8_TIFS/curv_profile_640.tif"]
    (bundle / REFERENCE_MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")

    result = compare_dem_curvature_formula_parity(
        bundle, atol=1e-6, rtol=1e-6, scale_m=SCALE, raster_reader=reader
    )
    statuses = {a.logical_name: a.status for a in result.artifacts}
    assert statuses["curv_profile_640"] == "missing_reference_output"
    assert result.status != STATUS_PASSED


def test_invalid_bundle_refuses(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()  # no manifest -> D2 invalid
    result = compare_dem_curvature_formula_parity(bundle, scale_m=SCALE)
    assert result.status == STATUS_REFERENCE_INVALID
    assert result.artifacts == ()


def test_cli_default_output_is_path_safe(tmp_path: Path, capsys) -> None:
    dem = _dem()
    bundle, reader = _build(tmp_path, dem)
    import app.pipeline.parity.dem_curvature_formula_parity as mod

    # Inject the synthetic reader as the default backend for the CLI path.
    orig = mod._read_raw_raster
    mod._read_raw_raster = reader  # type: ignore[assignment]
    try:
        exit_code = cli.main(["--bundle-dir", str(bundle), "--scale-m", "10"])
    finally:
        mod._read_raw_raster = orig  # type: ignore[assignment]
    out = capsys.readouterr().out

    assert exit_code == 0
    payload = json.loads(out)
    assert "artifacts" not in payload
    assert "interior_max_abs_diff" in payload
    assert str(tmp_path) not in out
    assert ".tif" not in out
