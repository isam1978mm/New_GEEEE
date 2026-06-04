import json

import numpy as np
import pytest

from app.pipeline.parity.pan_stack_verify import (
    PAN_STACK_OUTPUT_NAME,
    PAN_STACK_VERIFICATION_SCHEMA_VERSION,
    verify_pan_stack_parity,
)


def _load_report(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_npy(path, values, *, dtype=np.float32):
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.asarray(values, dtype=dtype))


def test_missing_app_output_is_reported_clearly(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_npy(reference_dir / PAN_STACK_OUTPUT_NAME, np.ones((2, 2, 2), dtype=np.float32))

    result = verify_pan_stack_parity(app_dir, reference_dir, run_dir, "run-missing-app")
    report = _load_report(result.report_path)

    assert result.overall_status == "incomplete"
    assert report["status"] == "missing_app_output"
    assert report["runtime_output_verified"] is False
    assert report["notebook_value_parity_verified"] is False


def test_missing_reference_output_is_reported_clearly(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_npy(app_dir / PAN_STACK_OUTPUT_NAME, np.ones((2, 2, 2), dtype=np.float32))

    result = verify_pan_stack_parity(app_dir, reference_dir, run_dir, "run-missing-reference")
    report = _load_report(result.report_path)

    assert result.overall_status == "incomplete"
    assert report["status"] == "missing_reference_output"
    assert report["runtime_output_verified"] is True
    assert report["notebook_value_parity_verified"] is False


def test_matching_npy_passes_and_hashes_are_recorded(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    values = np.arange(8, dtype=np.float32).reshape(2, 2, 2)
    _write_npy(app_dir / PAN_STACK_OUTPUT_NAME, values)
    _write_npy(reference_dir / PAN_STACK_OUTPUT_NAME, values)

    result = verify_pan_stack_parity(app_dir, reference_dir, run_dir, "run-pass")
    report = _load_report(result.report_path)

    assert result.overall_status == "passed"
    assert report["schema_version"] == PAN_STACK_VERIFICATION_SCHEMA_VERSION
    assert report["status"] == "passed"
    assert report["shape_match"] is True
    assert report["dtype_match"] is True
    assert report["within_tolerance"] is True
    assert report["app_sha256"]
    assert report["reference_sha256"]
    assert report["hash_match"] is True
    assert report["notebook_value_parity_verified"] is True


def test_shape_mismatch_fails(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_npy(app_dir / PAN_STACK_OUTPUT_NAME, np.ones((2, 2, 2), dtype=np.float32))
    _write_npy(reference_dir / PAN_STACK_OUTPUT_NAME, np.ones((2, 2, 3), dtype=np.float32))

    result = verify_pan_stack_parity(app_dir, reference_dir, run_dir, "run-shape")
    report = _load_report(result.report_path)

    assert result.overall_status == "failed"
    assert report["status"] == "shape_mismatch"
    assert report["shape_match"] is False
    assert report["notebook_value_parity_verified"] is False


def test_dtype_mismatch_fails(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_npy(app_dir / PAN_STACK_OUTPUT_NAME, np.ones((2, 2, 2), dtype=np.int16), dtype=np.int16)
    _write_npy(reference_dir / PAN_STACK_OUTPUT_NAME, np.ones((2, 2, 2), dtype=np.float32))

    result = verify_pan_stack_parity(app_dir, reference_dir, run_dir, "run-dtype")
    report = _load_report(result.report_path)

    assert result.overall_status == "failed"
    assert report["status"] == "dtype_mismatch"
    assert report["dtype_match"] is False
    assert report["notebook_value_parity_verified"] is False


def test_value_mismatch_fails(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_npy(app_dir / PAN_STACK_OUTPUT_NAME, np.arange(8, dtype=np.float32).reshape(2, 2, 2))
    bad = np.arange(8, dtype=np.float32).reshape(2, 2, 2)
    bad[0, 0, 0] = 99.0
    _write_npy(reference_dir / PAN_STACK_OUTPUT_NAME, bad)

    result = verify_pan_stack_parity(
        app_dir,
        reference_dir,
        run_dir,
        "run-value",
        atol=0.001,
        rtol=0.0,
    )
    report = _load_report(result.report_path)

    assert result.overall_status == "failed"
    assert report["status"] == "value_mismatch"
    assert report["max_abs_diff"] > 0
    assert report["notebook_value_parity_verified"] is False


def test_report_json_writes_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    values = np.arange(8, dtype=np.float32).reshape(2, 2, 2)
    _write_npy(app_dir / PAN_STACK_OUTPUT_NAME, values)
    _write_npy(reference_dir / PAN_STACK_OUTPUT_NAME, values)

    result = verify_pan_stack_parity(app_dir, reference_dir, run_dir, "run-report")
    report = _load_report(result.report_path)

    assert result.report_path == run_dir / "manifests" / "pan_layers_stack_verification.json"
    assert result.report_path.resolve().relative_to(run_dir.resolve())
    assert report["run_id"] == "run-report"
    assert report["app_output_dir"] == str(app_dir)
    assert report["notebook_reference_dir"] == str(reference_dir)


def test_report_path_traversal_is_blocked(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    values = np.arange(8, dtype=np.float32).reshape(2, 2, 2)
    _write_npy(app_dir / PAN_STACK_OUTPUT_NAME, values)
    _write_npy(reference_dir / PAN_STACK_OUTPUT_NAME, values)

    with pytest.raises(ValueError, match="path traversal"):
        verify_pan_stack_parity(
            app_dir,
            reference_dir,
            run_dir,
            "run-bad-path",
            report_relative_path="../escape.json",
        )


def test_verifier_does_not_create_npy_files_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    values = np.arange(8, dtype=np.float32).reshape(2, 2, 2)
    _write_npy(app_dir / PAN_STACK_OUTPUT_NAME, values)
    _write_npy(reference_dir / PAN_STACK_OUTPUT_NAME, values)

    verify_pan_stack_parity(app_dir, reference_dir, run_dir, "run-no-output-writes")
    created = [path for path in run_dir.rglob("*") if path.suffix.lower() == ".npy"]

    assert created == []


def test_phase_4g_modules_do_not_add_generation_alias_copy_or_optical_math_functions():
    import app.pipeline.parity.pan_stack_verify as verifier

    forbidden_public_functions = [
        name
        for name in dir(verifier)
        if name.startswith(("compute_", "generate_", "alias_", "copy_", "build_final", "per_image", "select_pairs"))
        or name.startswith("write_georeferenced")
    ]

    assert forbidden_public_functions == []
