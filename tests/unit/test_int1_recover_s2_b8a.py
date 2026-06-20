from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import int1_recover_s2_b8a as recovery

RASTERIO_AVAILABLE = importlib.util.find_spec("rasterio") is not None


def _write_run(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
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
    (root / "stage_s2_indices.manifest.json").write_text(
        json.dumps({"metadata": {"source_bands": ["B2", "B3", "B4", "B8", "B11", "B12", "B1"]}}),
        encoding="utf-8",
    )


def test_dry_run_does_not_write_outputs(tmp_path: Path) -> None:
    _write_run(tmp_path)

    result = recovery.recover_b8a_from_local_array(app_run_dir=tmp_path)

    assert result["ok"] is True
    assert result["status"] == "dry_run_ready"
    assert result["output_npy_written"] is False
    assert result["output_tif_written"] is False
    assert result["reference_outputs_read"] is False
    assert result["earth_engine_called"] is False
    assert not (tmp_path / recovery.B8A_NPY_NAME).exists()


def test_write_requires_local_b8a_array(tmp_path: Path) -> None:
    _write_run(tmp_path)

    with pytest.raises(recovery.B8ARecoveryError, match="--b8a-array"):
        recovery.recover_b8a_from_local_array(app_run_dir=tmp_path, write=True)


@pytest.mark.skipif(not RASTERIO_AVAILABLE, reason="rasterio required")
def test_write_registers_local_b8a_array(tmp_path: Path) -> None:
    import rasterio

    _write_run(tmp_path)
    source = tmp_path / "same_run_b8a.npy"
    np.save(source, np.full((4, 4), 8.0, dtype=np.float32))

    result = recovery.recover_b8a_from_local_array(
        app_run_dir=tmp_path,
        b8a_array=source,
        write=True,
    )

    assert result["status"] == "s2_b8a_recovery_written"
    assert result["output_npy_written"] is True
    assert result["output_tif_written"] is True
    assert result["manifest_written"] is True
    assert (tmp_path / recovery.B8A_NPY_NAME).is_file()
    assert (tmp_path / recovery.B8A_TIF_NAME).is_file()
    assert (tmp_path / recovery.B8A_MANIFEST_NAME).is_file()

    loaded = np.load(tmp_path / recovery.B8A_NPY_NAME, allow_pickle=False)
    assert loaded.shape == (4, 4)
    assert loaded.dtype == np.float32
    assert np.allclose(loaded, 8.0)

    with rasterio.open(tmp_path / recovery.B8A_TIF_NAME) as dataset:
        assert dataset.count == 1
        assert dataset.width == 4
        assert dataset.height == 4
        assert dataset.descriptions == ("B8A",)
        assert str(dataset.crs) == "EPSG:32637"


def test_write_rejects_wrong_shape(tmp_path: Path) -> None:
    _write_run(tmp_path)
    source = tmp_path / "bad_b8a.npy"
    np.save(source, np.zeros((3, 4), dtype=np.float32))

    with pytest.raises(recovery.B8ARecoveryError, match="shape"):
        recovery.recover_b8a_from_local_array(app_run_dir=tmp_path, b8a_array=source, write=True)


def test_cli_dry_run(tmp_path: Path) -> None:
    _write_run(tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parent.parent.parent / "scripts" / "int1_recover_s2_b8a.py"),
            "--app-run-dir",
            str(tmp_path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["status"] == "dry_run_ready"
    assert payload["output_npy_written"] is False
