from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.services.nb_exact_support import (
    ASC_DESC_CONSISTENCY_FILENAME,
    NB_EXACT_SUPPORT_DIR,
    THERMAL_DELTA_FILENAME,
)
from app.services.nb_results import _load_produced_exact_support


SHAPE = (12, 12)


def _write(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype="float32",
        nodata=-9999.0,
        transform=from_origin(0.0, 120.0, 10.0, 10.0),
    ) as dataset:
        dataset.write(array.astype(np.float32), 1)


def test_load_produced_exact_support_preserves_normalized_zero(tmp_path: Path) -> None:
    ascdesc = np.zeros(SHAPE, dtype=np.float32)
    thermal_delta = np.zeros(SHAPE, dtype=np.float32)
    ascdesc[5, 6] = np.float32(0.72)
    thermal_delta[5, 6] = np.float32(0.38)
    support_dir = tmp_path / NB_EXACT_SUPPORT_DIR
    _write(support_dir / ASC_DESC_CONSISTENCY_FILENAME, ascdesc)
    _write(support_dir / THERMAL_DELTA_FILENAME, thermal_delta)

    loaded_ascdesc, loaded_delta = _load_produced_exact_support(tmp_path, shape=SHAPE)

    assert loaded_ascdesc is not None
    assert loaded_delta is not None
    assert float(loaded_ascdesc[0, 0]) == 0.0
    assert float(loaded_delta[0, 0]) == 0.0
    assert float(loaded_ascdesc[5, 6]) == float(ascdesc[5, 6])
    assert float(loaded_delta[5, 6]) == float(thermal_delta[5, 6])


def test_load_produced_exact_support_abstains_on_shape_mismatch(tmp_path: Path) -> None:
    support_dir = tmp_path / NB_EXACT_SUPPORT_DIR
    _write(support_dir / ASC_DESC_CONSISTENCY_FILENAME, np.ones((10, 10), dtype=np.float32))
    _write(support_dir / THERMAL_DELTA_FILENAME, np.ones((10, 10), dtype=np.float32))

    loaded_ascdesc, loaded_delta = _load_produced_exact_support(tmp_path, shape=SHAPE)

    assert loaded_ascdesc is None
    assert loaded_delta is None
