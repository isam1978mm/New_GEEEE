import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from app.pipeline.parity.ai_ready_fraction_verify import (
    AI_READY_FRACTION_CLASSIFICATION,
    AI_READY_FRACTION_OUTPUT_NAMES,
    AI_READY_FRACTION_VERIFICATION_SCHEMA_VERSION,
    verify_ai_ready_fraction_parity,
)


RASTERIO_AVAILABLE = importlib.util.find_spec("rasterio") is not None
FORBIDDEN_WORDS = ("confirmed", "proven", "dig target", "definitely")


def _load_report(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_raster(
    path,
    values,
    *,
    width=2,
    height=2,
    crs="EPSG:32637",
    transform=None,
    dtype="float32",
    nodata=-9999.0,
):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not RASTERIO_AVAILABLE:
        path.write_bytes(b"placeholder-ai-ready-fraction-raster")
        return

    import rasterio
    from rasterio.transform import from_origin

    array = np.asarray(values, dtype=dtype).reshape((height, width))
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": dtype,
        "crs": crs,
        "transform": transform or from_origin(500000, 4100000, 10, 10),
        "nodata": nodata,
    }
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(array, 1)


def _write_output_set(directory, *, value=1.0, width=2, height=2):
    for index, name in enumerate(AI_READY_FRACTION_OUTPUT_NAMES):
        _write_raster(
            directory / name,
            np.full((height, width), value + index, dtype=np.float32),
            width=width,
            height=height,
        )


def test_recovery_checklist_names_are_required():
    assert AI_READY_FRACTION_OUTPUT_NAMES == (
        "AI_READY_640_Fraction_Gold.tif",
        "AI_READY_640_Fraction_Pottery.tif",
        "AI_READY_640_Fraction_Carbon_Age.tif",
        "AI_READY_640_Fraction_Silver_Lead.tif",
    )


def test_missing_app_output_is_reported_clearly(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_output_set(reference_dir)

    result = verify_ai_ready_fraction_parity(
        app_dir, reference_dir, run_dir, "run-missing-app"
    )
    report = _load_report(result.report_path)

    assert result.overall_status == "incomplete"
    assert {item["status"] for item in report["outputs"]} == {"missing_app_output"}
    assert all(item["runtime_output_verified"] is False for item in report["outputs"])
    assert all(item["notebook_value_parity_verified"] is False for item in report["outputs"])


def test_missing_reference_output_is_reported_clearly(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_output_set(app_dir)

    result = verify_ai_ready_fraction_parity(
        app_dir, reference_dir, run_dir, "run-missing-reference"
    )
    report = _load_report(result.report_path)

    assert result.overall_status == "incomplete"
    assert {item["status"] for item in report["outputs"]} == {"missing_reference_output"}
    assert all(item["runtime_output_verified"] is True for item in report["outputs"])
    assert all(item["notebook_value_parity_verified"] is False for item in report["outputs"])


def test_tif_comparison_passes_when_rasterio_is_available(tmp_path):
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio is not available for raster value comparison")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_output_set(app_dir)
    _write_output_set(reference_dir)

    result = verify_ai_ready_fraction_parity(app_dir, reference_dir, run_dir, "run-pass")
    report = _load_report(result.report_path)

    assert report["schema_version"] == AI_READY_FRACTION_VERIFICATION_SCHEMA_VERSION
    assert report["overall_status"] == "passed"
    assert all(item["status"] == "passed" for item in report["outputs"])
    assert all(item["metadata_compared"] is True for item in report["outputs"])
    assert all(item["values_compared"] is True for item in report["outputs"])
    assert all(item["within_tolerance"] is True for item in report["outputs"])
    assert all(item["runtime_output_verified"] is True for item in report["outputs"])
    assert all(item["notebook_value_parity_verified"] is True for item in report["outputs"])


def test_tif_value_mismatch_fails_when_rasterio_is_available(tmp_path):
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio is not available for raster value comparison")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_output_set(app_dir, value=1.0)
    _write_output_set(reference_dir, value=9.0)

    result = verify_ai_ready_fraction_parity(
        app_dir,
        reference_dir,
        run_dir,
        "run-mismatch",
        atol=0.001,
        rtol=0.0,
    )
    report = _load_report(result.report_path)

    assert result.overall_status == "failed"
    assert {item["status"] for item in report["outputs"]} == {"value_mismatch"}
    assert all(item["max_abs_diff"] > 0 for item in report["outputs"])
    assert all(item["notebook_value_parity_verified"] is False for item in report["outputs"])


def test_tif_comparison_unavailable_when_rasterio_is_not_available(tmp_path):
    if RASTERIO_AVAILABLE:
        pytest.skip("fallback comparison-unavailable path only applies without rasterio")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_output_set(app_dir)
    _write_output_set(reference_dir)

    result = verify_ai_ready_fraction_parity(
        app_dir, reference_dir, run_dir, "run-no-rasterio"
    )
    report = _load_report(result.report_path)

    assert result.raster_value_comparison_available is False
    assert result.overall_status == "comparison_unavailable"
    assert {item["status"] for item in report["outputs"]} == {"comparison_unavailable"}
    assert all(item["runtime_output_verified"] is True for item in report["outputs"])
    assert all(item["app_sha256"] == item["reference_sha256"] for item in report["outputs"])
    assert all(item["notebook_value_parity_verified"] is False for item in report["outputs"])


def test_hashes_report_json_and_run_dir_scope_are_recorded(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_output_set(app_dir)
    _write_output_set(reference_dir)

    result = verify_ai_ready_fraction_parity(app_dir, reference_dir, run_dir, "run-report")
    report = _load_report(result.report_path)

    assert result.report_path == run_dir / "manifests" / "ai_ready_fraction_parity_verification.json"
    assert result.report_path.resolve().relative_to(run_dir.resolve())
    assert report["run_id"] == "run-report"
    assert report["app_output_dir"] == str(app_dir)
    assert report["notebook_reference_dir"] == str(reference_dir)
    assert len(report["outputs"]) == 4
    assert all(item["app_sha256"] for item in report["outputs"])
    assert all(item["reference_sha256"] for item in report["outputs"])


def test_report_path_traversal_is_blocked(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_output_set(app_dir)
    _write_output_set(reference_dir)

    with pytest.raises(ValueError, match="path traversal"):
        verify_ai_ready_fraction_parity(
            app_dir,
            reference_dir,
            run_dir,
            "run-bad-path",
            report_relative_path="../escape.json",
        )


def test_verification_does_not_create_tif_or_npy_files_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_output_set(app_dir)
    _write_output_set(reference_dir)

    verify_ai_ready_fraction_parity(app_dir, reference_dir, run_dir, "run-no-writes")
    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in {".tif", ".tiff", ".npy"}
    ]

    assert created == []


def test_classification_exposure_and_runtime_flags_remain_private(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_output_set(app_dir)
    _write_output_set(reference_dir)

    result = verify_ai_ready_fraction_parity(
        app_dir, reference_dir, run_dir, "run-classification"
    )
    report = _load_report(result.report_path)

    assert report["classification"] == AI_READY_FRACTION_CLASSIFICATION
    assert report["target_mode"] == "notebook_parity"
    assert report["target_mode"] != "public_shared"
    assert report["http_servable"] is False
    assert all(item["classification"] == AI_READY_FRACTION_CLASSIFICATION for item in report["outputs"])
    assert all(item["http_servable"] is False for item in report["outputs"])
    assert all(item["requires_coordinates"] is False for item in report["outputs"])
    assert all(item["probability_only_required"] is False for item in report["outputs"])


def test_phase_4h4_module_does_not_add_compute_generate_alias_copy_or_semantic_math_functions():
    import app.pipeline.parity.ai_ready_fraction_verify as verifier

    forbidden_public_functions = [
        name
        for name in dir(verifier)
        if name.startswith(("compute_", "generate_", "alias_", "copy_", "build_semantic"))
    ]

    assert forbidden_public_functions == []


def test_no_forbidden_confirmation_wording_is_introduced_in_doc_or_code_comments():
    doc_text = Path("docs/AI_READY_FRACTION_PARITY_CONTRACT.md").read_text(
        encoding="utf-8"
    ).lower()
    verify_text = Path("app/pipeline/parity/ai_ready_fraction_verify.py").read_text(
        encoding="utf-8"
    ).lower()
    recovery_text = Path("app/pipeline/parity/ai_ready_fraction_recovery.py").read_text(
        encoding="utf-8"
    ).lower()

    for word in FORBIDDEN_WORDS:
        assert word not in doc_text
        assert word not in verify_text
        assert word not in recovery_text
