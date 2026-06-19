"""Unit tests for the D2-gated AI_READY secret-layer parity CLI.

All bundles/rasters are synthetic under tmp_path; no real frozen reference
artifacts are read or committed. The CLI reuses verify_secret_layers_parity.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from app.cli import secret_layers_verify as cli
from app.pipeline.parity.secret_layers_verify import SECRET_LAYERS_OUTPUT_NAMES
from app.services.reference_bundle_validator import REFERENCE_MANIFEST_NAME

RASTERIO_AVAILABLE = importlib.util.find_spec("rasterio") is not None


def _write_raster(path: Path, value: float, *, width: int = 2, height: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not RASTERIO_AVAILABLE:
        path.write_bytes(f"placeholder::{value}::{width}x{height}".encode())
        return
    import rasterio
    from rasterio.transform import from_origin

    array = np.full((height, width), value, dtype=np.float32)
    profile = {
        "driver": "GTiff", "height": height, "width": width, "count": 1,
        "dtype": "float32", "crs": "EPSG:32637",
        "transform": from_origin(500000, 4100000, 10, 10), "nodata": -9999.0,
    }
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(array, 1)


def _write_set(directory: Path, *, base_value: float = 1.0) -> None:
    for index, name in enumerate(SECRET_LAYERS_OUTPUT_NAMES):
        _write_raster(directory / name, base_value + index)


def _write_bundle_manifest(bundle: Path, *, reference_dir: Path | None = None) -> None:
    files = []
    for name in SECRET_LAYERS_OUTPUT_NAMES:
        source = (reference_dir or bundle) / name
        data = source.read_bytes()
        files.append({
            "relative_path": str(source.relative_to(bundle)).replace("\\", "/"),
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
            "role": "ai_ready",
        })
    manifest = {
        "source_notebook": "notebooks/new.ipynb", "repo_commit": "abc1234",
        "created_at": "2026-06-10T00:00:00Z", "bundle_name": "syn_ai_ready_bundle",
        "files": files,
    }
    (bundle / REFERENCE_MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")


def _valid_bundle(tmp_path: Path, *, base_value: float = 1.0) -> Path:
    bundle = tmp_path / "bundle"
    _write_set(bundle, base_value=base_value)
    _write_bundle_manifest(bundle)
    return bundle


def _valid_nested_bundle(tmp_path: Path, *, base_value: float = 1.0) -> tuple[Path, Path]:
    bundle = tmp_path / "bundle"
    reference_output_dir = bundle / "AI_READY_640"
    _write_set(reference_output_dir, base_value=base_value)
    _write_bundle_manifest(bundle, reference_dir=reference_output_dir)
    return bundle, reference_output_dir


# --- D2 gate ------------------------------------------------------------------


def test_cli_refuses_invalid_reference_bundle(tmp_path: Path, capsys) -> None:
    app = tmp_path / "app"
    _write_set(app)
    bundle = tmp_path / "bundle"
    bundle.mkdir()  # no manifest -> D2 invalid

    exit_code = cli.main(["--app-output-dir", str(app), "--bundle-dir", str(bundle)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["overall_status"] == "reference_invalid"
    assert "outputs" not in payload


# --- safe summary / details ---------------------------------------------------


def test_cli_default_output_is_path_safe(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for value comparison")
    app = tmp_path / "app"
    _write_set(app)
    bundle = _valid_bundle(tmp_path)

    exit_code = cli.main([
        "--app-output-dir", str(app), "--bundle-dir", str(bundle),
        "--run-dir", str(tmp_path / "run"),
    ])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert exit_code == 0
    assert payload["overall_status"] == "passed"
    assert set(payload) == {
        "overall_status", "expected_count", "compared_count",
        "tolerance", "counts_by_status", "per_output",
    }
    assert payload["tolerance"] == {"atol": 1e-6, "rtol": 1e-6}
    # path-safe: no absolute paths, no .tif filenames, no report path leak.
    assert str(tmp_path) not in out
    assert ".tif" not in out
    assert "report_path" not in out
    assert "AI_READY_640_Secret_Gold_Halo" in payload["per_output"]


def test_cli_accepts_nested_reference_output_dir(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for value comparison")
    app = tmp_path / "app"
    _write_set(app)
    bundle, reference_output_dir = _valid_nested_bundle(tmp_path)

    exit_code = cli.main([
        "--app-output-dir", str(app),
        "--bundle-dir", str(bundle),
        "--reference-output-dir", str(reference_output_dir),
        "--run-dir", str(tmp_path / "run"),
    ])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert exit_code == 0
    assert payload["overall_status"] == "passed"
    assert payload["counts_by_status"] == {"passed": len(SECRET_LAYERS_OUTPUT_NAMES)}
    assert str(tmp_path) not in out
    assert ".tif" not in out


def test_cli_show_details_includes_paths(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for value comparison")
    app = tmp_path / "app"
    _write_set(app)
    bundle = _valid_bundle(tmp_path)

    exit_code = cli.main([
        "--app-output-dir", str(app), "--bundle-dir", str(bundle),
        "--run-dir", str(tmp_path / "run"), "--show-details",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert "outputs" in payload and "report_path" in payload
    assert any(item["app_sha256"] for item in payload["outputs"])


def test_cli_value_mismatch_fails_nonzero(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for value comparison")
    app = tmp_path / "app"
    _write_set(app, base_value=1.0)
    bundle = _valid_bundle(tmp_path, base_value=50.0)

    exit_code = cli.main([
        "--app-output-dir", str(app), "--bundle-dir", str(bundle),
        "--run-dir", str(tmp_path / "run"), "--atol", "0.001", "--rtol", "0",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["overall_status"] == "failed"
    assert payload["counts_by_status"].get("value_mismatch", 0) == 6
