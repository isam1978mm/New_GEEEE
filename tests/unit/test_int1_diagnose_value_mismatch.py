from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import int1_diagnose_value_mismatch as diagnostic
import int1_generate_internal_rasters as writer

RASTERIO_AVAILABLE = importlib.util.find_spec("rasterio") is not None


def _write_run(root: Path) -> None:
    bands = ["B2", "B3", "B4", "B8", "B11", "B12", "B1", "B8A"]
    root.mkdir(parents=True, exist_ok=True)
    (root / "stage_s2_indices.manifest.json").write_text(
        json.dumps({"metadata": {"source_bands": bands}}),
        encoding="utf-8",
    )
    (root / "grid_manifest.json").write_text(
        json.dumps(
            {
                "epsg": 32637,
                "scale_m": 10.0,
                "size_px": 4,
                "crs_transform": [10.0, 0.0, 500000.0, 0.0, -10.0, 4100000.0],
            }
        ),
        encoding="utf-8",
    )
    cube = np.zeros((4, 4, len(bands)), dtype=np.float32)
    for index, _band in enumerate(bands):
        cube[..., index] = np.float32(index + 1)
    np.save(root / "s2_raw_cube.npy", cube)


@pytest.mark.skipif(not RASTERIO_AVAILABLE, reason="rasterio required")
def test_diagnostic_classifies_matching_app_and_reference(tmp_path: Path) -> None:
    _write_run(tmp_path)
    writer.generate_int1_internal_rasters(run_dir=tmp_path, write=True)

    output_name = writer.INT1_OUTPUT_SPECS[0].output_name
    result = diagnostic.diagnose_int1_value_mismatch(
        run_dir=tmp_path,
        app_output_dir=tmp_path,
        bundle_dir=tmp_path,
        outputs=(output_name,),
    )

    assert result["ok"] is True
    assert result["diagnostic_only"] is True
    assert result["writes_outputs"] is False
    assert result["selected_output_count"] == 1
    assert result["outputs"][0]["formula_to_app"]["allclose_pass"] is True
    assert result["outputs"][0]["formula_to_reference"]["allclose_pass"] is True
    assert result["outputs"][0]["app_to_reference"]["allclose_pass"] is True
    assert result["outputs"][0]["diagnosis"] == "app_reference_value_parity"


@pytest.mark.skipif(not RASTERIO_AVAILABLE, reason="rasterio required")
def test_diagnostic_classifies_reference_source_difference(tmp_path: Path) -> None:
    import rasterio

    _write_run(tmp_path / "app")
    writer.generate_int1_internal_rasters(run_dir=tmp_path / "app", write=True)
    reference_dir = tmp_path / "reference"
    reference_dir.mkdir()
    output_name = writer.INT1_OUTPUT_SPECS[0].output_name
    source_tif = tmp_path / "app" / output_name
    reference_tif = reference_dir / output_name
    reference_tif.write_bytes(source_tif.read_bytes())

    with rasterio.open(reference_tif, "r+") as dataset:
        data = dataset.read(1)
        dataset.write(data + np.float32(0.25), 1)

    result = diagnostic.diagnose_int1_value_mismatch(
        run_dir=tmp_path / "app",
        app_output_dir=tmp_path / "app",
        bundle_dir=reference_dir,
        outputs=(output_name,),
    )

    assert result["outputs"][0]["formula_to_app"]["allclose_pass"] is True
    assert result["outputs"][0]["formula_to_reference"]["allclose_pass"] is False
    assert result["outputs"][0]["app_to_reference"]["allclose_pass"] is False
    assert result["outputs"][0]["diagnosis"] == "local_source_formula_matches_app_reference_differs"


@pytest.mark.skipif(not RASTERIO_AVAILABLE, reason="rasterio required")
def test_cli_prints_safe_aggregate_payload(tmp_path: Path) -> None:
    _write_run(tmp_path)
    writer.generate_int1_internal_rasters(run_dir=tmp_path, write=True)
    output_name = writer.INT1_OUTPUT_SPECS[0].output_name

    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parent.parent.parent / "scripts" / "int1_diagnose_value_mismatch.py"),
            "--run-dir",
            str(tmp_path),
            "--bundle-dir",
            str(tmp_path),
            "--outputs",
            output_name,
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["status"] == "int1_value_mismatch_diagnosed"
    assert payload["diagnostic_only"] is True
    assert payload["writes_outputs"] is False
    assert "run_dir" not in payload
    assert "bundle_dir" not in payload
