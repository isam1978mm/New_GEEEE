import importlib.util
import json

import numpy as np
import pytest

from app.pipeline.parity.secret_layers_verify import (
    SECRET_LAYERS_CLASSIFICATION,
    SECRET_LAYERS_OUTPUT_NAMES,
    SECRET_LAYERS_VERIFICATION_SCHEMA_VERSION,
    verify_secret_layers_parity,
)


RASTERIO_AVAILABLE = importlib.util.find_spec("rasterio") is not None


def _write_raster(
    path,
    values,
    *,
    width=2,
    height=2,
    crs="EPSG:32636",
    transform=None,
    dtype="float32",
    nodata=-9999.0,
):
    if not RASTERIO_AVAILABLE:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"placeholder-secret-layer-raster")
        return

    import rasterio
    from rasterio.transform import from_origin

    path.parent.mkdir(parents=True, exist_ok=True)
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


def _write_secret_layer_set(directory, *, value=1.0, width=2, height=2):
    for index, name in enumerate(SECRET_LAYERS_OUTPUT_NAMES):
        _write_raster(
            directory / name,
            np.full((height, width), value + index, dtype=np.float32),
            width=width,
            height=height,
        )


def _load_report(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_six_secret_layer_names_are_required():
    assert SECRET_LAYERS_OUTPUT_NAMES == (
        "AI_READY_640_Secret_Gold_Halo.tif",
        "AI_READY_640_Secret_Silver_Oxide.tif",
        "AI_READY_640_Secret_Tunnel_Ceiling.tif",
        "AI_READY_640_Secret_Thermal_Inertia.tif",
        "AI_READY_640_Secret_Chemical_Protector.tif",
        "AI_READY_640_Secret_Hidden_Doors.tif",
    )


def test_missing_app_output_is_reported_clearly(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_secret_layer_set(reference_dir)

    result = verify_secret_layers_parity(app_dir, reference_dir, run_dir, "run-missing-app")
    report = _load_report(result.report_path)

    assert result.overall_status == "incomplete"
    assert {item["status"] for item in report["outputs"]} == {"missing_app_output"}
    assert all(item["runtime_output_verified"] is False for item in report["outputs"])
    assert all(item["notebook_value_parity_verified"] is False for item in report["outputs"])


def test_missing_reference_output_is_reported_clearly(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_secret_layer_set(app_dir)

    result = verify_secret_layers_parity(app_dir, reference_dir, run_dir, "run-missing-reference")
    report = _load_report(result.report_path)

    assert result.overall_status == "incomplete"
    assert {item["status"] for item in report["outputs"]} == {"missing_reference_output"}
    assert all(item["runtime_output_verified"] is True for item in report["outputs"])
    assert all(item["notebook_value_parity_verified"] is False for item in report["outputs"])


def test_matching_tiny_fixture_rasters_pass_when_rasterio_is_available(tmp_path):
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio is not available for raster value comparison")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_secret_layer_set(app_dir)
    _write_secret_layer_set(reference_dir)

    result = verify_secret_layers_parity(app_dir, reference_dir, run_dir, "run-pass")
    report = _load_report(result.report_path)

    assert report["schema_version"] == SECRET_LAYERS_VERIFICATION_SCHEMA_VERSION
    assert report["overall_status"] == "passed"
    assert all(item["status"] == "passed" for item in report["outputs"])
    assert all(item["metadata_compared"] is True for item in report["outputs"])
    assert all(item["values_compared"] is True for item in report["outputs"])
    assert all(item["within_tolerance"] is True for item in report["outputs"])
    assert all(item["runtime_output_verified"] is True for item in report["outputs"])
    assert all(item["notebook_value_parity_verified"] is True for item in report["outputs"])


def test_value_mismatch_fails_when_rasterio_is_available(tmp_path):
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio is not available for raster value comparison")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_secret_layer_set(app_dir, value=1.0)
    _write_secret_layer_set(reference_dir, value=10.0)

    result = verify_secret_layers_parity(
        app_dir,
        reference_dir,
        run_dir,
        "run-value-mismatch",
        atol=0.001,
        rtol=0.0,
    )
    report = _load_report(result.report_path)

    assert result.overall_status == "failed"
    assert {item["status"] for item in report["outputs"]} == {"value_mismatch"}
    assert all(item["notebook_value_parity_verified"] is False for item in report["outputs"])
    assert all(item["max_abs_diff"] > 0 for item in report["outputs"])


def test_metadata_mismatch_fails_when_rasterio_is_available(tmp_path):
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio is not available for raster metadata comparison")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_secret_layer_set(app_dir, width=2, height=2)
    _write_secret_layer_set(reference_dir, width=3, height=2)

    result = verify_secret_layers_parity(app_dir, reference_dir, run_dir, "run-metadata-mismatch")
    report = _load_report(result.report_path)

    assert result.overall_status == "failed"
    assert {item["status"] for item in report["outputs"]} == {"metadata_mismatch"}
    assert all(item["width_match"] is False for item in report["outputs"])
    assert all(item["values_compared"] is False for item in report["outputs"])
    assert all(item["notebook_value_parity_verified"] is False for item in report["outputs"])


def test_existing_outputs_are_comparison_unavailable_without_raster_dependency(tmp_path):
    if RASTERIO_AVAILABLE:
        pytest.skip("fallback comparison-unavailable path only applies without rasterio")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_secret_layer_set(app_dir)
    _write_secret_layer_set(reference_dir)

    result = verify_secret_layers_parity(app_dir, reference_dir, run_dir, "run-no-rasterio")
    report = _load_report(result.report_path)

    assert result.overall_status == "comparison_unavailable"
    assert {item["status"] for item in report["outputs"]} == {"comparison_unavailable"}
    assert all(item["runtime_output_verified"] is True for item in report["outputs"])
    assert all(item["metadata_compared"] is False for item in report["outputs"])
    assert all(item["values_compared"] is False for item in report["outputs"])
    assert all(item["app_sha256"] == item["reference_sha256"] for item in report["outputs"])
    assert all(item["notebook_value_parity_verified"] is False for item in report["outputs"])


def test_report_json_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_secret_layer_set(app_dir)
    _write_secret_layer_set(reference_dir)

    result = verify_secret_layers_parity(app_dir, reference_dir, run_dir, "run-report")
    report = _load_report(result.report_path)

    assert result.report_path == run_dir / "manifests" / "secret_layers_parity_verification.json"
    assert result.report_path.resolve().relative_to(run_dir.resolve())
    assert report["run_id"] == "run-report"
    assert report["app_output_dir"] == str(app_dir)
    assert report["notebook_reference_dir"] == str(reference_dir)
    assert len(report["outputs"]) == 6


def test_report_path_traversal_is_blocked(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_secret_layer_set(app_dir)
    _write_secret_layer_set(reference_dir)

    with pytest.raises(ValueError, match="path traversal"):
        verify_secret_layers_parity(
            app_dir,
            reference_dir,
            run_dir,
            "run-bad-path",
            report_relative_path="../escape.json",
        )


def test_verification_does_not_create_raster_or_npy_files(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_secret_layer_set(app_dir)
    _write_secret_layer_set(reference_dir)

    verify_secret_layers_parity(app_dir, reference_dir, run_dir, "run-no-raster-writes")
    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in {".tif", ".tiff", ".npy"}
    ]

    assert created == []


def test_secret_layer_classification_and_exposure_remain_private_parity(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_secret_layer_set(app_dir)
    _write_secret_layer_set(reference_dir)

    result = verify_secret_layers_parity(app_dir, reference_dir, run_dir, "run-classification")
    report = _load_report(result.report_path)

    assert report["classification"] == SECRET_LAYERS_CLASSIFICATION
    assert report["classification"] == "notebook-parity semantic raster stage"
    assert report["target_mode"] == "notebook_parity"
    assert report["target_mode"] != "public_shared"
    assert report["http_servable"] is False
    assert all(item["classification"] == SECRET_LAYERS_CLASSIFICATION for item in report["outputs"])
    assert all(item["target_mode"] != "public_shared" for item in report["outputs"])
    assert all(item["http_servable"] is False for item in report["outputs"])
