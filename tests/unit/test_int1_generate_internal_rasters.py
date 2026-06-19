from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import int1_generate_internal_rasters as writer

RASTERIO_AVAILABLE = importlib.util.find_spec("rasterio") is not None


def _write_run(root: Path, *, include_b8a: bool) -> None:
    bands = ["B2", "B3", "B4", "B8", "B11", "B12", "B1"]
    if include_b8a:
        bands.append("B8A")
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


def test_dry_run_blocks_full_generation_when_b8a_is_missing(tmp_path: Path) -> None:
    _write_run(tmp_path, include_b8a=False)

    result = writer.generate_int1_internal_rasters(run_dir=tmp_path)

    assert result["ok"] is False
    assert result["status"] == "blocked_missing_source_bands"
    assert result["missing_source_bands"] == ["B8A"]
    assert result["expected_output_count"] == 13
    assert result["runnable_output_count"] == 11
    assert result["blocked_output_count"] == 2
    assert result["outputs_written"] is False
    assert not any(tmp_path.glob("AI_BEH_*.tif"))


def test_write_refuses_full_generation_when_b8a_is_missing(tmp_path: Path) -> None:
    _write_run(tmp_path, include_b8a=False)

    with pytest.raises(writer.MissingBandsError, match="B8A"):
        writer.generate_int1_internal_rasters(run_dir=tmp_path, write=True)


@pytest.mark.skipif(not RASTERIO_AVAILABLE, reason="rasterio required")
def test_write_generates_all_outputs_when_complete_source_exists(tmp_path: Path) -> None:
    import rasterio

    _write_run(tmp_path, include_b8a=True)

    result = writer.generate_int1_internal_rasters(run_dir=tmp_path, write=True)

    assert result["ok"] is True
    assert result["status"] == "int1_internal_rasters_written"
    assert result["written_output_count"] == 13
    outputs = sorted(tmp_path.glob("AI_BEH_*.tif"))
    assert len(outputs) == 13

    with rasterio.open(tmp_path / "AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif") as dataset:
        assert dataset.width == 4
        assert dataset.height == 4
        assert dataset.count == 1
        assert dataset.dtypes == ("float32",)
        assert str(dataset.crs) == "EPSG:32637"
        assert tuple(round(abs(value), 6) for value in dataset.res) == (10.0, 10.0)
        values = dataset.read(1)

    expected = (4.0 - 3.0) / (4.0 + 3.0)
    assert np.allclose(values, expected, atol=1e-6, rtol=1e-6)


def test_cli_dry_run_reports_blocked_missing_b8a(tmp_path: Path) -> None:
    _write_run(tmp_path, include_b8a=False)

    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parent.parent.parent / "scripts" / "int1_generate_internal_rasters.py"),
            "--run-dir",
            str(tmp_path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["status"] == "blocked_missing_source_bands"
    assert payload["missing_source_bands"] == ["B8A"]
