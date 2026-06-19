from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import hyper_1a_generate_res_2p5m as generator

RASTERIO_AVAILABLE = importlib.util.find_spec("rasterio") is not None
SCIPY_AVAILABLE = importlib.util.find_spec("scipy") is not None


def _write_source_hypercube(path: Path) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required")
    import rasterio
    from rasterio.transform import from_origin

    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.arange(9 * 2 * 2, dtype=np.float32).reshape(9, 2, 2)
    profile = {
        "driver": "GTiff",
        "height": 2,
        "width": 2,
        "count": 9,
        "dtype": "float32",
        "crs": "EPSG:32637",
        "transform": from_origin(500000, 4100000, 10, 10),
        "nodata": -9999.0,
    }
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(data)
        for band_index in range(1, 10):
            dataset.set_band_description(band_index, f"band_{band_index}")


def test_dry_run_reports_expected_shape_without_writing(tmp_path: Path) -> None:
    _write_source_hypercube(tmp_path / "NPY_STACKS" / generator.SOURCE_HYPERCUBE_NAME)

    result = generator.generate_hyper_1a_res_2p5m(
        source_dir=tmp_path,
        output_dir=tmp_path / "NPY_STACKS",
        write=False,
    )

    assert result["status"] == "dry_run_ready"
    assert result["source_band_count"] == 9
    assert result["zoom_factor"] == 4.0
    assert result["expected_output_shape_chw"] == [9, 8, 8]
    assert result["output_tif_written"] is False
    assert result["output_npy_written"] is False
    assert not (tmp_path / "NPY_STACKS" / generator.OUTPUT_TIF_NAME).exists()
    assert not (tmp_path / "NPY_STACKS" / generator.OUTPUT_NPY_NAME).exists()


def test_write_generates_resampled_tif_and_npy(tmp_path: Path) -> None:
    if not SCIPY_AVAILABLE:
        pytest.skip("scipy required")
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required")
    import rasterio

    output_dir = tmp_path / "NPY_STACKS"
    _write_source_hypercube(output_dir / generator.SOURCE_HYPERCUBE_NAME)

    result = generator.generate_hyper_1a_res_2p5m(
        source_dir=output_dir,
        output_dir=output_dir,
        write=True,
    )

    assert result["status"] == "hyper_1a_res_2p5m_written"
    assert result["output_tif_written"] is True
    assert result["output_npy_written"] is True

    npy = np.load(output_dir / generator.OUTPUT_NPY_NAME, allow_pickle=False)
    assert npy.shape == (9, 8, 8)
    assert npy.dtype == np.float32

    with rasterio.open(output_dir / generator.OUTPUT_TIF_NAME) as dataset:
        assert dataset.count == 9
        assert dataset.width == 8
        assert dataset.height == 8
        assert tuple(round(abs(value), 6) for value in dataset.res) == (2.5, 2.5)
        assert dataset.dtypes == ("float32",) * 9
        assert dataset.descriptions[0] == "band_1"


def test_write_refuses_existing_outputs_without_overwrite(tmp_path: Path) -> None:
    if not SCIPY_AVAILABLE:
        pytest.skip("scipy required")
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required")

    output_dir = tmp_path / "NPY_STACKS"
    _write_source_hypercube(output_dir / generator.SOURCE_HYPERCUBE_NAME)
    (output_dir / generator.OUTPUT_NPY_NAME).write_bytes(b"already here")

    with pytest.raises(generator.Hyper1AGenerationError, match="output already exists"):
        generator.generate_hyper_1a_res_2p5m(
            source_dir=output_dir,
            output_dir=output_dir,
            write=True,
        )
