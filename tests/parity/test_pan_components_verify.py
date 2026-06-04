import importlib.util
import json

import numpy as np
import pytest

from app.pipeline.parity.pan_components_verify import (
    PAN_COMPONENT_OUTPUT_NAMES,
    PAN_COMPONENTS_VERIFICATION_SCHEMA_VERSION,
    verify_pan_components_parity,
)


RASTERIO_AVAILABLE = importlib.util.find_spec("rasterio") is not None


def _load_report(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_npy_pair(app_dir, reference_dir, name, values=None, *, dtype=np.float32):
    values = np.asarray(values if values is not None else [[1.0, 2.0], [3.0, 4.0]], dtype=dtype)
    app_path = app_dir / name
    reference_path = reference_dir / name
    app_path.parent.mkdir(parents=True, exist_ok=True)
    reference_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(app_path, values)
    np.save(reference_path, values)


def _write_npy(path, values, *, dtype=np.float32):
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.asarray(values, dtype=dtype))


def _write_tif_pair(app_dir, reference_dir, name, *, app_value=1.0, reference_value=1.0, width=2, height=2):
    _write_tif(app_dir / name, np.full((height, width), app_value, dtype=np.float32), width=width, height=height)
    _write_tif(reference_dir / name, np.full((height, width), reference_value, dtype=np.float32), width=width, height=height)


def _write_tif(path, values, *, width=2, height=2, crs="EPSG:32636", transform=None, dtype="float32", nodata=-9999.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not RASTERIO_AVAILABLE:
        path.write_bytes(b"placeholder-pan-component-raster")
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


def _write_all_matching_outputs(app_dir, reference_dir):
    for name in PAN_COMPONENT_OUTPUT_NAMES:
        if name.endswith(".npy"):
            _write_npy_pair(app_dir, reference_dir, name)
        else:
            _write_tif_pair(app_dir, reference_dir, name)


def _output_by_name(report, name):
    return {item["output_name"]: item for item in report["outputs"]}[name]


def test_all_four_pan_component_output_names_are_required():
    assert PAN_COMPONENT_OUTPUT_NAMES == (
        "PAN_LS_Panchromatic_640.tif",
        "PAN_S2_Panchromatic_10m_640.tif",
        "PAN_LS_Panchromatic_640.npy",
        "PAN_S2_Panchromatic_10m_640.npy",
    )


def test_missing_app_output_is_reported_clearly(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(reference_dir, reference_dir)

    result = verify_pan_components_parity(app_dir, reference_dir, run_dir, "run-missing-app")
    report = _load_report(result.report_path)

    assert result.overall_status == "incomplete"
    assert report["outputs"][0]["status"] == "missing_app_output"
    assert report["outputs"][0]["runtime_output_verified"] is False
    assert report["outputs"][0]["notebook_value_parity_verified"] is False


def test_missing_reference_output_is_reported_clearly(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(app_dir, app_dir)

    result = verify_pan_components_parity(app_dir, reference_dir, run_dir, "run-missing-reference")
    report = _load_report(result.report_path)

    assert result.overall_status == "incomplete"
    assert report["outputs"][0]["status"] == "missing_reference_output"
    assert report["outputs"][0]["runtime_output_verified"] is True
    assert report["outputs"][0]["notebook_value_parity_verified"] is False


def test_npy_matching_fixtures_pass_and_hashes_are_recorded(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(app_dir, reference_dir)

    result = verify_pan_components_parity(app_dir, reference_dir, run_dir, "run-npy-pass")
    report = _load_report(result.report_path)
    npy_outputs = [item for item in report["outputs"] if item["file_type"] == "npy"]

    assert report["schema_version"] == PAN_COMPONENTS_VERIFICATION_SCHEMA_VERSION
    assert len(npy_outputs) == 2
    for item in npy_outputs:
        assert item["status"] == "passed"
        assert item["values_compared"] is True
        assert item["shape_match"] is True
        assert item["dtype_match"] is True
        assert item["within_tolerance"] is True
        assert item["app_sha256"]
        assert item["reference_sha256"]
        assert item["hash_match"] is True
        assert item["notebook_value_parity_verified"] is True
    assert result.npy_outputs_passed is True


def test_npy_shape_mismatch_fails(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(app_dir, reference_dir)
    _write_npy(app_dir / "PAN_LS_Panchromatic_640.npy", [[1.0, 2.0]])

    result = verify_pan_components_parity(app_dir, reference_dir, run_dir, "run-shape")
    report = _load_report(result.report_path)
    item = _output_by_name(report, "PAN_LS_Panchromatic_640.npy")

    assert result.overall_status == "failed"
    assert item["status"] == "shape_mismatch"
    assert item["shape_match"] is False
    assert item["notebook_value_parity_verified"] is False


def test_npy_dtype_mismatch_fails(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(app_dir, reference_dir)
    _write_npy(app_dir / "PAN_S2_Panchromatic_10m_640.npy", [[1, 2], [3, 4]], dtype=np.int16)

    result = verify_pan_components_parity(app_dir, reference_dir, run_dir, "run-dtype")
    report = _load_report(result.report_path)
    item = _output_by_name(report, "PAN_S2_Panchromatic_10m_640.npy")

    assert result.overall_status == "failed"
    assert item["status"] == "dtype_mismatch"
    assert item["dtype_match"] is False
    assert item["notebook_value_parity_verified"] is False


def test_npy_value_mismatch_fails(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(app_dir, reference_dir)
    _write_npy(app_dir / "PAN_LS_Panchromatic_640.npy", [[100.0, 2.0], [3.0, 4.0]])

    result = verify_pan_components_parity(
        app_dir,
        reference_dir,
        run_dir,
        "run-value",
        atol=0.001,
        rtol=0.0,
    )
    report = _load_report(result.report_path)
    item = _output_by_name(report, "PAN_LS_Panchromatic_640.npy")

    assert result.overall_status == "failed"
    assert item["status"] == "value_mismatch"
    assert item["max_abs_diff"] > 0
    assert item["notebook_value_parity_verified"] is False


def test_tif_comparison_passes_when_rasterio_is_available(tmp_path):
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio is not available for raster value comparison")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(app_dir, reference_dir)

    result = verify_pan_components_parity(app_dir, reference_dir, run_dir, "run-tif-pass")
    report = _load_report(result.report_path)
    tif_outputs = [item for item in report["outputs"] if item["file_type"] == "tif"]

    assert result.raster_value_comparison_available is True
    for item in tif_outputs:
        assert item["status"] == "passed"
        assert item["metadata_compared"] is True
        assert item["values_compared"] is True
        assert item["notebook_value_parity_verified"] is True


def test_tif_value_mismatch_fails_when_rasterio_is_available(tmp_path):
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio is not available for raster value comparison")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(app_dir, reference_dir)
    _write_tif(app_dir / "PAN_S2_Panchromatic_10m_640.tif", np.full((2, 2), 9.0, dtype=np.float32))

    result = verify_pan_components_parity(app_dir, reference_dir, run_dir, "run-tif-value")
    report = _load_report(result.report_path)
    item = _output_by_name(report, "PAN_S2_Panchromatic_10m_640.tif")

    assert result.overall_status == "failed"
    assert item["status"] == "value_mismatch"
    assert item["notebook_value_parity_verified"] is False


def test_tif_comparison_unavailable_when_rasterio_is_not_available(tmp_path):
    if RASTERIO_AVAILABLE:
        pytest.skip("fallback comparison-unavailable path only applies without rasterio")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(app_dir, reference_dir)

    result = verify_pan_components_parity(app_dir, reference_dir, run_dir, "run-no-rasterio")
    report = _load_report(result.report_path)
    tif_outputs = [item for item in report["outputs"] if item["file_type"] == "tif"]

    assert result.raster_value_comparison_available is False
    assert result.overall_status == "comparison_unavailable"
    for item in tif_outputs:
        assert item["status"] == "comparison_unavailable"
        assert item["runtime_output_verified"] is True
        assert item["notebook_value_parity_verified"] is False


def test_report_json_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(app_dir, reference_dir)

    result = verify_pan_components_parity(app_dir, reference_dir, run_dir, "run-report")
    report = _load_report(result.report_path)

    assert result.report_path == run_dir / "manifests" / "pan_components_parity_verification.json"
    assert result.report_path.resolve().relative_to(run_dir.resolve())
    assert report["run_id"] == "run-report"
    assert report["app_output_dir"] == str(app_dir)
    assert report["notebook_reference_dir"] == str(reference_dir)
    assert len(report["outputs"]) == 4


def test_report_path_traversal_is_blocked(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(app_dir, reference_dir)

    with pytest.raises(ValueError, match="path traversal"):
        verify_pan_components_parity(
            app_dir,
            reference_dir,
            run_dir,
            "run-bad-path",
            report_relative_path="../escape.json",
        )


def test_verification_does_not_create_raster_npy_or_alias_files_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(app_dir, reference_dir)

    verify_pan_components_parity(app_dir, reference_dir, run_dir, "run-no-output-writes")
    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in {".tif", ".tiff", ".npy"}
    ]

    assert created == []
    assert not (run_dir / "OPT").exists()


def test_classification_and_exposure_remain_private_notebook_parity(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_all_matching_outputs(app_dir, reference_dir)

    result = verify_pan_components_parity(app_dir, reference_dir, run_dir, "run-classification")
    report = _load_report(result.report_path)

    for item in report["outputs"]:
        assert item["classification"] == "notebook-parity"
        assert item["target_mode"] == "notebook_parity"
        assert item["target_mode"] != "public_shared"
        assert item["http_servable"] is False
        assert item["requires_coordinates"] is False
        assert item["probability_only_required"] is False


def test_phase_4h_module_does_not_add_generation_alias_copy_or_optical_math_functions():
    import app.pipeline.parity.pan_components_verify as verifier

    forbidden_public_functions = [
        name for name in dir(verifier)
        if name.startswith(("compute_", "generate_", "alias_", "copy_", "build_final", "per_image", "select_pairs"))
        or name.startswith("write_georeferenced")
    ]

    assert forbidden_public_functions == []
