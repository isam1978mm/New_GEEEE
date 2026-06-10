"""Unit tests for the REPORT_640 verifier extension (size/sha) and the D2-gated
local CLI. All bundles/rasters are synthetic under tmp_path; no real frozen
reference artifacts are read or committed.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from app.cli import report_640_verify as cli
from app.pipeline.parity.report_640_verify import (
    REPORT_640_OUTPUT_NAMES,
    verify_report_640_parity,
)
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


def _write_report_set(directory: Path, *, base_value: float = 1.0) -> None:
    for index, name in enumerate(REPORT_640_OUTPUT_NAMES):
        _write_raster(directory / name, base_value + index)


def _write_bundle_manifest(bundle: Path) -> None:
    files = []
    for name in REPORT_640_OUTPUT_NAMES:
        data = (bundle / name).read_bytes()
        files.append({
            "relative_path": name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
            "role": "report",
        })
    manifest = {
        "source_notebook": "notebooks/new.ipynb", "repo_commit": "abc1234",
        "created_at": "2026-06-10T00:00:00Z", "bundle_name": "syn_report_bundle",
        "files": files,
    }
    (bundle / REFERENCE_MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")


def _valid_bundle(tmp_path: Path, *, base_value: float = 1.0) -> Path:
    bundle = tmp_path / "bundle"
    _write_report_set(bundle, base_value=base_value)
    _write_bundle_manifest(bundle)
    return bundle


# --- verifier extension: size + sha256 informational fields -------------------


def test_size_and_sha_fields_match_for_identical_files(tmp_path: Path) -> None:
    app = tmp_path / "app"
    reference = tmp_path / "ref"
    _write_report_set(app)
    _write_report_set(reference)

    result = verify_report_640_parity(app, reference, tmp_path / "run", "run-size")
    for item in result.outputs:
        assert item["app_size_bytes"] is not None
        assert item["reference_size_bytes"] is not None
        assert item["app_sha256"] is not None and len(item["app_sha256"]) == 64
        assert item["size_match"] is True
        assert item["sha256_match"] is True


def test_sha_fields_none_when_app_missing(tmp_path: Path) -> None:
    reference = tmp_path / "ref"
    _write_report_set(reference)
    result = verify_report_640_parity(tmp_path / "app", reference, tmp_path / "run", "run-miss")
    for item in result.outputs:
        assert item["app_sha256"] is None
        assert item["reference_sha256"] is not None
        assert item["size_match"] is None  # cannot compare when one side absent


# --- CLI: D2 gate -------------------------------------------------------------


def test_cli_refuses_invalid_reference_bundle(tmp_path: Path, capsys) -> None:
    app = tmp_path / "app"
    _write_report_set(app)
    bundle = tmp_path / "bundle"
    bundle.mkdir()  # no manifest -> D2 invalid

    exit_code = cli.main(["--app-output-dir", str(app), "--bundle-dir", str(bundle)])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert exit_code == 1
    assert payload["overall_status"] == "reference_invalid"
    assert "outputs" not in payload


# --- CLI: safe summary / details ---------------------------------------------


def test_cli_default_output_is_path_safe(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for value comparison")
    app = tmp_path / "app"
    _write_report_set(app)
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
        "counts_by_status", "per_output",
    }
    # path-safe: no absolute paths, no .tif filenames, no report path leak.
    assert str(tmp_path) not in out
    assert ".tif" not in out
    assert "report_path" not in out
    # per_output keyed by logical name (no extension).
    assert "REPORT_640_Pottery_Report" in payload["per_output"]


def test_cli_show_details_includes_paths(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for value comparison")
    app = tmp_path / "app"
    _write_report_set(app)
    bundle = _valid_bundle(tmp_path)

    exit_code = cli.main([
        "--app-output-dir", str(app), "--bundle-dir", str(bundle),
        "--run-dir", str(tmp_path / "run"), "--show-details",
    ])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert exit_code == 0
    assert "outputs" in payload and "report_path" in payload
    assert any(item["app_sha256"] for item in payload["outputs"])


def test_cli_metadata_mismatch_fails_nonzero(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for metadata comparison")
    app = tmp_path / "app"
    # App rasters at a different size -> metadata mismatch vs the bundle.
    for index, name in enumerate(REPORT_640_OUTPUT_NAMES):
        _write_raster(app / name, 1.0 + index, width=3, height=2)
    bundle = _valid_bundle(tmp_path)

    exit_code = cli.main([
        "--app-output-dir", str(app), "--bundle-dir", str(bundle),
        "--run-dir", str(tmp_path / "run"),
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["overall_status"] == "failed"
