import importlib.util
import json

import numpy as np
import pytest

from app.pipeline.parity.dem_curv_laplacian_verify import (
    APP_CURVATURE_OUTPUT_NAME,
    DEM_CURV_LAPLACIAN_CLASSIFICATION,
    DEM_CURV_LAPLACIAN_VERIFICATION_SCHEMA_VERSION,
    NOTEBOOK_CURV_LAPLACIAN_OUTPUT_NAME,
    verify_dem_curv_laplacian_parity,
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
        path.write_bytes(b"placeholder-curvature-raster")
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


def _write_pair(app_dir, reference_dir, *, app_value=1.0, reference_value=1.0, width=2, height=2):
    _write_raster(
        app_dir / APP_CURVATURE_OUTPUT_NAME,
        np.full((height, width), app_value, dtype=np.float32),
        width=width,
        height=height,
    )
    _write_raster(
        reference_dir / NOTEBOOK_CURV_LAPLACIAN_OUTPUT_NAME,
        np.full((height, width), reference_value, dtype=np.float32),
        width=width,
        height=height,
    )


def _load_report(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_expected_app_and_reference_names():
    assert APP_CURVATURE_OUTPUT_NAME == "curvature.tif"
    assert NOTEBOOK_CURV_LAPLACIAN_OUTPUT_NAME == "curv_laplacian_640.tif"


def test_missing_app_output_is_reported_clearly(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_raster(reference_dir / NOTEBOOK_CURV_LAPLACIAN_OUTPUT_NAME, [1, 1, 1, 1])

    result = verify_dem_curv_laplacian_parity(app_dir, reference_dir, run_dir, "run-missing-app")
    report = _load_report(result.report_path)

    assert result.overall_status == "incomplete"
    assert report["status"] == "missing_app_output"
    assert report["runtime_output_verified"] is False
    assert report["notebook_value_parity_verified"] is False


def test_missing_reference_output_is_reported_clearly(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_raster(app_dir / APP_CURVATURE_OUTPUT_NAME, [1, 1, 1, 1])

    result = verify_dem_curv_laplacian_parity(app_dir, reference_dir, run_dir, "run-missing-reference")
    report = _load_report(result.report_path)

    assert result.overall_status == "incomplete"
    assert report["status"] == "missing_reference_output"
    assert report["runtime_output_verified"] is True
    assert report["notebook_value_parity_verified"] is False


def test_matching_tiny_rasters_pass_when_rasterio_is_available(tmp_path):
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio is not available for raster value comparison")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_pair(app_dir, reference_dir, app_value=2.0, reference_value=2.0)

    result = verify_dem_curv_laplacian_parity(app_dir, reference_dir, run_dir, "run-pass")
    report = _load_report(result.report_path)

    assert report["schema_version"] == DEM_CURV_LAPLACIAN_VERIFICATION_SCHEMA_VERSION
    assert report["overall_status"] == "passed"
    assert report["status"] == "passed"
    assert report["metadata_compared"] is True
    assert report["values_compared"] is True
    assert report["within_tolerance"] is True
    assert report["runtime_output_verified"] is True
    assert report["notebook_value_parity_verified"] is True


def test_value_mismatch_fails_when_rasterio_is_available(tmp_path):
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio is not available for raster value comparison")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_pair(app_dir, reference_dir, app_value=1.0, reference_value=10.0)

    result = verify_dem_curv_laplacian_parity(
        app_dir,
        reference_dir,
        run_dir,
        "run-value-mismatch",
        atol=0.001,
        rtol=0.0,
    )
    report = _load_report(result.report_path)

    assert result.overall_status == "failed"
    assert report["status"] == "value_mismatch"
    assert report["notebook_value_parity_verified"] is False
    assert report["max_abs_diff"] > 0


def test_metadata_mismatch_fails_when_rasterio_is_available(tmp_path):
    if not RASTERIO_AVAILABLE:
        pytest.skip("rasterio is not available for raster metadata comparison")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_raster(app_dir / APP_CURVATURE_OUTPUT_NAME, np.ones((2, 2)), width=2, height=2)
    _write_raster(
        reference_dir / NOTEBOOK_CURV_LAPLACIAN_OUTPUT_NAME,
        np.ones((2, 3)),
        width=3,
        height=2,
    )

    result = verify_dem_curv_laplacian_parity(app_dir, reference_dir, run_dir, "run-metadata-mismatch")
    report = _load_report(result.report_path)

    assert result.overall_status == "failed"
    assert report["status"] == "metadata_mismatch"
    assert report["width_match"] is False
    assert report["values_compared"] is False
    assert report["notebook_value_parity_verified"] is False


def test_existing_outputs_are_comparison_unavailable_without_raster_dependency(tmp_path):
    if RASTERIO_AVAILABLE:
        pytest.skip("fallback comparison-unavailable path only applies without rasterio")

    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_pair(app_dir, reference_dir)

    result = verify_dem_curv_laplacian_parity(app_dir, reference_dir, run_dir, "run-no-rasterio")
    report = _load_report(result.report_path)

    assert result.overall_status == "comparison_unavailable"
    assert report["status"] == "comparison_unavailable"
    assert report["runtime_output_verified"] is True
    assert report["metadata_compared"] is False
    assert report["values_compared"] is False
    assert report["notebook_value_parity_verified"] is False


def test_report_json_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_pair(app_dir, reference_dir)

    result = verify_dem_curv_laplacian_parity(app_dir, reference_dir, run_dir, "run-report")
    report = _load_report(result.report_path)

    assert result.report_path == run_dir / "manifests" / "dem_curv_laplacian_parity_verification.json"
    assert result.report_path.resolve().relative_to(run_dir.resolve())
    assert report["run_id"] == "run-report"
    assert report["app_output_dir"] == str(app_dir)
    assert report["notebook_reference_dir"] == str(reference_dir)
    assert report["app_output_name"] == APP_CURVATURE_OUTPUT_NAME
    assert report["reference_output_name"] == NOTEBOOK_CURV_LAPLACIAN_OUTPUT_NAME


def test_report_path_traversal_is_blocked(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_pair(app_dir, reference_dir)

    with pytest.raises(ValueError, match="path traversal"):
        verify_dem_curv_laplacian_parity(
            app_dir,
            reference_dir,
            run_dir,
            "run-bad-path",
            report_relative_path="../escape.json",
        )


def test_verification_does_not_create_raster_npy_or_alias_files(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_pair(app_dir, reference_dir)

    verify_dem_curv_laplacian_parity(app_dir, reference_dir, run_dir, "run-no-raster-writes")
    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in {".tif", ".tiff", ".npy"}
    ]

    assert created == []
    assert not (run_dir / "parity" / "DEM_GEO8_TIFS" / NOTEBOOK_CURV_LAPLACIAN_OUTPUT_NAME).exists()


def test_classification_and_exposure_remain_private_notebook_parity(tmp_path):
    run_dir = tmp_path / "run"
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    _write_pair(app_dir, reference_dir)

    result = verify_dem_curv_laplacian_parity(app_dir, reference_dir, run_dir, "run-classification")
    report = _load_report(result.report_path)

    assert report["classification"] == DEM_CURV_LAPLACIAN_CLASSIFICATION
    assert report["classification"] == "notebook-parity"
    assert report["target_mode"] == "notebook_parity"
    assert report["target_mode"] != "public_shared"
    assert report["artifact_class"] == "LOCAL_SENSITIVE"
    assert report["http_servable"] is False
    assert report["requires_coordinates"] is False
    assert report["probability_only_required"] is False


def test_phase_4d2_module_does_not_add_formula_or_alias_implementation():
    import app.pipeline.parity.dem_curv_laplacian_verify as verifier

    public_formula_or_alias_functions = [
        name for name in dir(verifier)
        if name.startswith("compute_")
        or name.startswith("write_georeferenced")
        or name.startswith("copy_")
        or name.startswith("alias_")
    ]

    assert public_formula_or_alias_functions == []
