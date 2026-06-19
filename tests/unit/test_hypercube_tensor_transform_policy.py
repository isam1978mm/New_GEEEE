from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.pipeline.parity.hypercube_tensor_verify import (
    DEFAULT_TRANSFORM_ATOL,
    STATUS_BLOCKED_NOT_COMPARABLE,
    verify_hypercube_tensor_parity,
)


def _write_grid_manifest(root: Path, *, origin_delta: float = 0.0) -> None:
    transform = [
        10.0,
        0.0,
        500000.0 + origin_delta,
        0.0,
        -10.0,
        4100000.0 - origin_delta,
    ]
    root.mkdir(parents=True, exist_ok=True)
    (root / "grid_manifest.json").write_text(
        json.dumps(
            {
                "epsg": 32637,
                "scale_m": 10.0,
                "size_px": 640,
                "crs_transform": transform,
            }
        ),
        encoding="utf-8",
    )


def _write_tensors(app: Path, reference: Path) -> None:
    app_stack = app / "NPY_STACKS"
    reference_stack = reference / "NPY_STACKS"
    app_stack.mkdir(parents=True, exist_ok=True)
    reference_stack.mkdir(parents=True, exist_ok=True)

    final_tesla = np.arange(9 * 2 * 2, dtype=np.float32).reshape(9, 2, 2)
    radar = np.arange(2 * 2 * 4, dtype=np.float32).reshape(2, 2, 4)

    np.save(app_stack / "FINAL_TESLA_V7_2_HYPERCUBE.npy", final_tesla)
    np.save(reference_stack / "FINAL_TESLA_V7_2_HYPERCUBE.npy", final_tesla)
    np.save(app_stack / "RADAR_STACK_HWC_640_app.npy", radar)
    np.save(reference_stack / "RADAR_STACK_HWC_640_ref.npy", radar)


def test_tiny_transform_delta_is_comparable(tmp_path: Path) -> None:
    app = tmp_path / "app"
    reference = tmp_path / "reference"
    run = tmp_path / "run"
    _write_grid_manifest(app, origin_delta=DEFAULT_TRANSFORM_ATOL / 2)
    _write_grid_manifest(reference)
    _write_tensors(app, reference)

    result = verify_hypercube_tensor_parity(app, reference, run, "tiny-transform")

    assert result.overall_status == "passed"
    assert result.run_contract["status"] == "comparable"
    assert result.run_contract["transform_match"] is True
    assert result.run_contract["transform_atol"] == DEFAULT_TRANSFORM_ATOL
    assert 0 < result.run_contract["transform_max_abs_delta"] <= DEFAULT_TRANSFORM_ATOL
    assert {item["status"] for item in result.outputs} == {"passed"}


def test_large_transform_delta_blocks_run_contract(tmp_path: Path) -> None:
    app = tmp_path / "app"
    reference = tmp_path / "reference"
    run = tmp_path / "run"
    _write_grid_manifest(app, origin_delta=DEFAULT_TRANSFORM_ATOL * 10)
    _write_grid_manifest(reference)
    _write_tensors(app, reference)

    result = verify_hypercube_tensor_parity(app, reference, run, "large-transform")

    assert result.overall_status == STATUS_BLOCKED_NOT_COMPARABLE
    assert result.run_contract["status"] == "not_comparable"
    assert result.run_contract["transform_match"] is False
    assert result.run_contract["transform_max_abs_delta"] > DEFAULT_TRANSFORM_ATOL
    assert {item["status"] for item in result.outputs} == {"passed"}
