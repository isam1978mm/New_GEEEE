from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from app.cli import internal_raster_verify as cli
from app.services.reference_bundle_validator import REFERENCE_MANIFEST_NAME

RASTERIO_AVAILABLE = importlib.util.find_spec("rasterio") is not None


def _all_output_names() -> tuple[str, ...]:
    names: list[str] = []
    for spec in cli.INT1_AI_BEH_FAMILIES:
        names.extend(spec.output_names)
    return tuple(names)


def _write_raster(path: Path, value: float, *, width: int = 2, height: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not RASTERIO_AVAILABLE:
        path.write_bytes(f"placeholder::{value}::{width}x{height}".encode())
        return

    import rasterio
    from rasterio.transform import from_origin

    array = np.full((height, width), value, dtype=np.float32)
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32637",
        "transform": from_origin(500000, 4100000, 10, 10),
        "nodata": -9999.0,
    }
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(array, 1)


def _write_set(directory: Path, *, base_value: float = 1.0) -> None:
    for index, name in enumerate(_all_output_names()):
        _write_raster(directory / name, base_value + index)


def _write_bundle_manifest(bundle: Path) -> None:
    files = []
    for name in _all_output_names():
        data = (bundle / name).read_bytes()
        files.append(
            {
                "relative_path": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size_bytes": len(data),
                "role": "int1_internal_raster",
            }
        )
    manifest = {
        "source_notebook": "notebooks/new.ipynb",
        "repo_commit": "abc1234",
        "created_at": "2026-06-10T00:00:00Z",
        "bundle_name": "synthetic_int1_internal_raster_bundle",
        "files": files,
    }
    (bundle / REFERENCE_MANIFEST_NAME).write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )


def _valid_bundle(tmp_path: Path, *, base_value: float = 1.0) -> Path:
    bundle = tmp_path / "bundle"
    _write_set(bundle, base_value=base_value)
    _write_bundle_manifest(bundle)
    return bundle


def test_cli_refuses_invalid_reference_bundle(tmp_path: Path, capsys) -> None:
    app = tmp_path / "app"
    _write_set(app)
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    exit_code = cli.main(["--app-output-dir", str(app), "--bundle-dir", str(bundle)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["overall_status"] == "reference_invalid"
    assert "per_output" not in payload


def test_cli_default_output_is_path_safe(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for value comparison")

    app = tmp_path / "app"
    _write_set(app)
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
    assert payload["expected_count"] == 13
    assert payload["tolerance"] == {"atol": 1e-6, "rtol": 1e-6}
    assert str(tmp_path) not in out
    assert ".tif" not in out
    assert "report_path" not in out
    assert "AI_BEH_VegRoot_REL_ND_DOM_lin_640" in payload["per_output"]
    vegroot = payload["per_output"]["AI_BEH_VegRoot_REL_ND_DOM_lin_640"]
    assert vegroot["app_width"] == 2
    assert vegroot["app_height"] == 2
    assert vegroot["app_crs"] == "EPSG:32637"
    assert vegroot["app_dtype"] == ["float32"]
    assert vegroot["app_nodata"] == [-9999.0]
    assert vegroot["app_band_count"] == 1
    assert vegroot["app_transform"] == [
        10.0,
        0.0,
        500000.0,
        0.0,
        -10.0,
        4100000.0,
        0.0,
        0.0,
        1.0,
    ]
    assert vegroot["finite_compared_pixel_count"] == 4


def test_cli_show_details_includes_relative_paths(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for value comparison")

    app = tmp_path / "app"
    _write_set(app)
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
    assert "family_details" in payload
    relation = payload["family_details"]["ai_beh_relation"]
    assert relation["report_path"] == "manifests/ai_beh_relation_parity_verification.json"
    assert all(not Path(item["app_path"]).is_absolute() for item in relation["outputs"])
    assert any(item["app_sha256"] for item in relation["outputs"])


def test_cli_value_mismatch_fails_nonzero(tmp_path: Path, capsys) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required for value comparison")

    app = tmp_path / "app"
    _write_set(app, base_value=1.0)
    bundle = _valid_bundle(tmp_path, base_value=50.0)

    exit_code = cli.main(
        [
            "--app-output-dir",
            str(app),
            "--bundle-dir",
            str(bundle),
            "--run-dir",
            str(tmp_path / "run"),
            "--atol",
            "0.001",
            "--rtol",
            "0",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["overall_status"] == "failed"
    assert payload["counts_by_status"].get("value_mismatch") == 13
