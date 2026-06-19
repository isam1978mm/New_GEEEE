from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from app.pipeline.parity.hypercube_res25_verify import (
    DEFAULT_TRANSFORM_ATOL,
    HYPERCUBE_RES25_OUTPUT_NAMES,
    verify_hypercube_res25_parity,
)

RASTERIO_AVAILABLE = importlib.util.find_spec("rasterio") is not None


def _write_npy(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.arange(9 * 2 * 2, dtype=np.float32).reshape(9, 2, 2))


def _write_tif(path: Path, *, x_offset_delta: float = 0.0, y_offset_delta: float = 0.0) -> None:
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
        "transform": from_origin(500000.0 + x_offset_delta, 4100000.0 + y_offset_delta, 2.5, 2.5),
        "nodata": -9999.0,
    }
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(data)


def _write_pair(app: Path, reference: Path, *, app_transform_delta: float) -> None:
    for root in (app, reference):
        _write_npy(root / HYPERCUBE_RES25_OUTPUT_NAMES[1])
    _write_tif(reference / HYPERCUBE_RES25_OUTPUT_NAMES[0])
    _write_tif(
        app / HYPERCUBE_RES25_OUTPUT_NAMES[0],
        x_offset_delta=app_transform_delta,
        y_offset_delta=-app_transform_delta,
    )


def _report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _item(report: dict, name: str) -> dict:
    return {item["output_name"]: item for item in report["outputs"]}[name]


def test_tif_allows_tiny_transform_delta_and_compares_values(tmp_path: Path) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required")
    app = tmp_path / "app"
    reference = tmp_path / "reference"
    run = tmp_path / "run"
    _write_pair(app, reference, app_transform_delta=DEFAULT_TRANSFORM_ATOL / 2)

    result = verify_hypercube_res25_parity(app, reference, run, "tiny-transform")
    report = _report(result.report_path)
    tif = _item(report, HYPERCUBE_RES25_OUTPUT_NAMES[0])

    assert result.overall_status == "passed"
    assert tif["status"] == "passed"
    assert tif["transform_match"] is True
    assert tif["transform_max_abs_delta"] == pytest.approx(DEFAULT_TRANSFORM_ATOL / 2)
    assert tif["transform_atol"] == DEFAULT_TRANSFORM_ATOL
    assert tif["values_compared"] is True
    assert tif["max_abs_diff"] == 0.0


def test_tif_rejects_large_transform_delta_before_value_comparison(tmp_path: Path) -> None:
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio required")
    app = tmp_path / "app"
    reference = tmp_path / "reference"
    run = tmp_path / "run"
    _write_pair(app, reference, app_transform_delta=DEFAULT_TRANSFORM_ATOL * 10)

    result = verify_hypercube_res25_parity(app, reference, run, "large-transform")
    report = _report(result.report_path)
    tif = _item(report, HYPERCUBE_RES25_OUTPUT_NAMES[0])

    assert result.overall_status == "failed"
    assert tif["status"] == "metadata_mismatch"
    assert tif["transform_match"] is False
    assert tif["values_compared"] is False
