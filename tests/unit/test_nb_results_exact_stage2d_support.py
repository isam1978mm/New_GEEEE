from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from app.services.nb_results import _load_stage2d_exact_support, build_nb_results


SHAPE = (12, 12)


def _write_single_band(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype="float32",
        transform=from_origin(0.0, 120.0, 10.0, 10.0),
    ) as dataset:
        dataset.write(array.astype(np.float32), 1)


def _write_stage2d(path: Path, ascdesc: np.ndarray, thermal_delta: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=ascdesc.shape[0],
        width=ascdesc.shape[1],
        count=2,
        dtype="float32",
        nodata=0.0,
        transform=from_origin(0.0, 120.0, 10.0, 10.0),
    ) as dataset:
        dataset.write(ascdesc.astype(np.float32), 1)
        dataset.set_band_description(1, "FS_ASC_DESC_CONSISTENCY_640")
        dataset.write(thermal_delta.astype(np.float32), 2)
        dataset.set_band_description(2, "THERMAL_DELTA_DAY_NIGHT_PROXY")


def _write_object_index(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["object_id", "row_center", "col_center"])
        writer.writeheader()
        writer.writerow({"object_id": 1, "row_center": 5, "col_center": 6})


def test_exact_stage2d_loader_uses_notebook_bands_and_preserves_valid_zero(tmp_path: Path) -> None:
    ascdesc = np.zeros(SHAPE, dtype=np.float32)
    thermal_delta = np.zeros(SHAPE, dtype=np.float32)
    ascdesc[5, 6] = np.float32(0.75)
    thermal_delta[5, 6] = np.float32(0.42)
    _write_stage2d(
        tmp_path / "NPY_STACKS" / "AI_MASTER_MATRIX_640_STAGE2D_FALSE_SIGNATURE.tif",
        ascdesc,
        thermal_delta,
    )

    loaded_ascdesc, loaded_delta = _load_stage2d_exact_support(tmp_path, shape=SHAPE)

    assert loaded_ascdesc is not None
    assert loaded_delta is not None
    assert loaded_ascdesc[5, 6] == pytest.approx(0.75)
    assert loaded_delta[5, 6] == pytest.approx(0.42)
    # new.ipynb Stage 2D declares nodata=0 even though normalized zero is valid.
    assert loaded_ascdesc[0, 0] == pytest.approx(0.0)
    assert loaded_delta[0, 0] == pytest.approx(0.0)


def test_nb_results_no_longer_marks_exact_stage2d_support_unavailable(tmp_path: Path) -> None:
    _write_object_index(tmp_path / "objects_index.csv")
    _write_single_band(tmp_path / "VV_dB.tif", np.full(SHAPE, -10.0, dtype=np.float32))
    _write_single_band(tmp_path / "VH_dB.tif", np.full(SHAPE, -15.0, dtype=np.float32))

    ascdesc = np.full(SHAPE, 0.65, dtype=np.float32)
    thermal_delta = np.full(SHAPE, 0.35, dtype=np.float32)
    _write_stage2d(
        tmp_path / "NPY_STACKS" / "AI_MASTER_MATRIX_640_STAGE2D_FALSE_SIGNATURE.tif",
        ascdesc,
        thermal_delta,
    )

    result = build_nb_results(tmp_path)

    assert result["status"] == "partial"
    assert "asc_desc_consistency" not in result["unavailable_support"]
    assert "thermal_delta" not in result["unavailable_support"]
    assert result["object_count"] == 1
    # Exact Stage 2D support alone must not invent the other missing notebook inputs.
    assert result["objects"][0]["nb_depth_available"] is False


def test_exact_stage2d_loader_rejects_shape_mismatch(tmp_path: Path) -> None:
    wrong_shape = (10, 10)
    _write_stage2d(
        tmp_path / "NPY_STACKS" / "AI_MASTER_MATRIX_640_STAGE2D_FALSE_SIGNATURE.tif",
        np.full(wrong_shape, 0.7, dtype=np.float32),
        np.full(wrong_shape, 0.3, dtype=np.float32),
    )

    loaded_ascdesc, loaded_delta = _load_stage2d_exact_support(tmp_path, shape=SHAPE)

    assert loaded_ascdesc is None
    assert loaded_delta is None
