from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.pipeline.parity.ai_beh_alloy_statue_verify import (
    AI_BEH_ALLOY_STATUE_OUTPUT_NAME,
    verify_ai_beh_alloy_statue_parity,
)


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _rasterio_available() -> bool:
    import importlib.util

    return importlib.util.find_spec("rasterio") is not None


def _write_tif(path: Path, values, *, transform=None) -> None:
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin

    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.array(values, dtype="float32")
    use_transform = transform or from_origin(0, 2, 1, 1)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:32637",
        transform=use_transform,
        nodata=-9999.0,
    ) as dataset:
        dataset.write(data, 1)


def test_verifier_requires_alloy_statue_output_name() -> None:
    assert AI_BEH_ALLOY_STATUE_OUTPUT_NAME == "AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.tif"


def test_verifier_reports_missing_app_output(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    ref_dir = tmp_path / "ref"
    run_dir = tmp_path / "run"
    _write_bytes(ref_dir / AI_BEH_ALLOY_STATUE_OUTPUT_NAME, b"ref")

    result = verify_ai_beh_alloy_statue_parity(app_dir, ref_dir, run_dir, "run-4h10")

    assert result.overall_status == "incomplete"
    assert result.output["status"] == "missing_app_output"


def test_verifier_reports_missing_reference_output(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    ref_dir = tmp_path / "ref"
    run_dir = tmp_path / "run"
    _write_bytes(app_dir / AI_BEH_ALLOY_STATUE_OUTPUT_NAME, b"app")

    result = verify_ai_beh_alloy_statue_parity(app_dir, ref_dir, run_dir, "run-4h10")

    assert result.overall_status == "incomplete"
    assert result.output["status"] == "missing_reference_output"
    assert result.output["runtime_output_verified"] is True


@pytest.mark.skipif(not _rasterio_available(), reason="rasterio not importable")
def test_verifier_passes_for_matching_tif(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    ref_dir = tmp_path / "ref"
    run_dir = tmp_path / "run"

    _write_tif(app_dir / AI_BEH_ALLOY_STATUE_OUTPUT_NAME, [[1.0, 2.0], [3.0, 4.0]])
    _write_tif(ref_dir / AI_BEH_ALLOY_STATUE_OUTPUT_NAME, [[1.0, 2.0], [3.0, 4.0]])

    result = verify_ai_beh_alloy_statue_parity(app_dir, ref_dir, run_dir, "run-4h10")

    assert result.overall_status == "passed"
    assert result.output["status"] == "passed"
    assert result.output["notebook_value_parity_verified"] is True


@pytest.mark.skipif(not _rasterio_available(), reason="rasterio not importable")
def test_verifier_reports_value_mismatch(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    ref_dir = tmp_path / "ref"
    run_dir = tmp_path / "run"

    _write_tif(app_dir / AI_BEH_ALLOY_STATUE_OUTPUT_NAME, [[1.0, 2.0], [3.0, 4.0]])
    _write_tif(ref_dir / AI_BEH_ALLOY_STATUE_OUTPUT_NAME, [[9.0, 9.0], [9.0, 9.0]])

    result = verify_ai_beh_alloy_statue_parity(app_dir, ref_dir, run_dir, "run-4h10")

    assert result.overall_status == "failed"
    assert result.output["status"] == "value_mismatch"


def test_verifier_reports_comparison_unavailable_without_rasterio(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    ref_dir = tmp_path / "ref"
    run_dir = tmp_path / "run"
    _write_bytes(app_dir / AI_BEH_ALLOY_STATUE_OUTPUT_NAME, b"app")
    _write_bytes(ref_dir / AI_BEH_ALLOY_STATUE_OUTPUT_NAME, b"ref")

    result = verify_ai_beh_alloy_statue_parity(app_dir, ref_dir, run_dir, "run-4h10")

    if result.raster_value_comparison_available:
        pytest.skip("rasterio importable in this environment")

    assert result.overall_status == "comparison_unavailable"
    assert result.output["status"] == "comparison_unavailable"
    assert result.output["notebook_value_parity_verified"] is False


def test_verifier_records_hashes_and_writes_json_report(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    ref_dir = tmp_path / "ref"
    run_dir = tmp_path / "run"
    _write_bytes(app_dir / AI_BEH_ALLOY_STATUE_OUTPUT_NAME, b"app-bytes")
    _write_bytes(ref_dir / AI_BEH_ALLOY_STATUE_OUTPUT_NAME, b"ref-bytes")

    result = verify_ai_beh_alloy_statue_parity(app_dir, ref_dir, run_dir, "run-4h10")
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))

    assert result.report_path == run_dir / "manifests" / "ai_beh_alloy_statue_parity_verification.json"
    assert payload["run_id"] == "run-4h10"
    assert payload["classification"] == "notebook-parity semantic raster stage"
    assert payload["http_servable"] is False
    assert payload["outputs"][0]["app_sha256"]
    assert payload["outputs"][0]["reference_sha256"]


def test_verifier_report_path_stays_under_run_dir(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        verify_ai_beh_alloy_statue_parity(
            tmp_path / "app",
            tmp_path / "ref",
            tmp_path / "run",
            "run-4h10",
            report_relative_path="../escape.json",
        )


def test_verifier_does_not_create_tif_or_npy_under_run_dir(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    ref_dir = tmp_path / "ref"
    run_dir = tmp_path / "run"
    _write_bytes(app_dir / AI_BEH_ALLOY_STATUE_OUTPUT_NAME, b"app")
    _write_bytes(ref_dir / AI_BEH_ALLOY_STATUE_OUTPUT_NAME, b"ref")

    verify_ai_beh_alloy_statue_parity(app_dir, ref_dir, run_dir, "run-4h10")

    assert not list(run_dir.rglob("*.tif"))
    assert not list(run_dir.rglob("*.npy"))


def test_docs_and_code_avoid_confirmation_wording() -> None:
    doc_text = Path("docs/AI_BEH_ALLOY_STATUE_PARITY_CONTRACT.md").read_text(
        encoding="utf-8"
    ).lower()
    code_text = Path("app/pipeline/parity/ai_beh_alloy_statue_recovery.py").read_text(
        encoding="utf-8"
    ).lower()

    for forbidden in ("confirmed", "proven", "dig target", "definitely"):
        assert forbidden not in doc_text
        assert forbidden not in code_text
