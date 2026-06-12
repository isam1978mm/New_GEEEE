"""Unit tests for the D2-gated 2.5 m hypercube/tensor parity CLI.

All bundles/tensors are synthetic under tmp_path; no real frozen reference
artifacts are read or committed. The CLI reuses verify_hypercube_res25_parity.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from app.cli import hypercube_res25_verify as cli
from app.pipeline.parity.hypercube_res25_verify import HYPERCUBE_RES25_OUTPUT_NAMES
from app.services.reference_bundle_validator import REFERENCE_MANIFEST_NAME

RASTERIO_AVAILABLE = importlib.util.find_spec("rasterio") is not None


def _write_npy(path: Path, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, values)


def _write_tif(path: Path, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not RASTERIO_AVAILABLE:
        path.write_bytes(b"placeholder-hypercube-tif")
        return
    import rasterio
    from rasterio.transform import from_origin

    count, height, width = values.shape
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": count,
        "dtype": "float32",
        "crs": "EPSG:32637",
        "transform": from_origin(500000, 4100000, 2.5, 2.5),
        "nodata": -9999.0,
    }
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(values.astype(np.float32, copy=False))


def _write_outputs(root: Path, *, base_value: float = 1.0) -> None:
    for name in HYPERCUBE_RES25_OUTPUT_NAMES:
        values = np.full((9, 2, 2), base_value, dtype=np.float32)
        if name.endswith(".npy"):
            _write_npy(root / "NPY_STACKS" / name, values)
        else:
            _write_tif(root / "NPY_STACKS" / name, values)


def _write_bundle_manifest(bundle: Path) -> None:
    files = []
    for name in HYPERCUBE_RES25_OUTPUT_NAMES:
        relative_path = f"NPY_STACKS/{name}"
        data = (bundle / relative_path).read_bytes()
        files.append(
            {
                "relative_path": relative_path,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size_bytes": len(data),
                "role": "hypercube_tensor",
            }
        )
    manifest = {
        "source_notebook": "notebooks/new.ipynb",
        "repo_commit": "abc1234",
        "created_at": "2026-06-10T00:00:00Z",
        "bundle_name": "syn_hypercube_bundle",
        "files": files,
    }
    (bundle / REFERENCE_MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")


def _valid_bundle(tmp_path: Path, *, base_value: float = 1.0) -> Path:
    bundle = tmp_path / "bundle"
    _write_outputs(bundle, base_value=base_value)
    _write_bundle_manifest(bundle)
    return bundle


def test_cli_refuses_invalid_reference_bundle(tmp_path: Path, capsys) -> None:
    app = tmp_path / "app"
    _write_outputs(app)
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    exit_code = cli.main(["--app-output-dir", str(app), "--bundle-dir", str(bundle)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["overall_status"] == "reference_invalid"
    assert "outputs" not in payload


def test_cli_default_output_is_path_safe(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for full pass")
    app = tmp_path / "app"
    _write_outputs(app)
    bundle = _valid_bundle(tmp_path)

    exit_code = cli.main(
        [
            "--app-output-dir",
            str(app),
            "--bundle-dir",
            str(bundle),
            "--run-dir",
            str(tmp_path / "run"),
        ]
    )
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert exit_code == 0
    assert payload["overall_status"] == "passed"
    assert set(payload) == {
        "overall_status",
        "expected_count",
        "compared_count",
        "tolerance",
        "counts_by_status",
        "per_output",
    }
    assert str(tmp_path) not in out
    assert ".tif" not in out
    assert ".npy" not in out
    assert "report_path" not in out
    assert payload["per_output"]["resampled_hypercube_npy"]["app_finite_count"] == 36
    assert payload["per_output"]["resampled_hypercube_npy"]["allclose_pass"] is True


def test_cli_show_details_uses_relative_paths(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for full pass")
    app = tmp_path / "app"
    _write_outputs(app)
    bundle = _valid_bundle(tmp_path)

    exit_code = cli.main(
        [
            "--app-output-dir",
            str(app),
            "--bundle-dir",
            str(bundle),
            "--run-dir",
            str(tmp_path / "run"),
            "--show-details",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["report_path"] == "manifests/hypercube_res_2p5m_parity_verification.json"
    assert "outputs" in payload
    assert all(not Path(item["app_path"]).is_absolute() for item in payload["outputs"])
    assert any(item["app_sha256"] for item in payload["outputs"])


def test_cli_value_mismatch_fails_nonzero(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for value comparison")
    app = tmp_path / "app"
    _write_outputs(app, base_value=1.0)
    bundle = _valid_bundle(tmp_path, base_value=5.0)

    exit_code = cli.main(
        [
            "--app-output-dir",
            str(app),
            "--bundle-dir",
            str(bundle),
            "--run-dir",
            str(tmp_path / "run"),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["overall_status"] == "failed"
    assert payload["counts_by_status"].get("value_mismatch", 0) == 2
