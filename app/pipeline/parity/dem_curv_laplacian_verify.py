from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

from app.pipeline.parity import resolve_run_output_path


DEM_CURV_LAPLACIAN_VERIFICATION_SCHEMA_VERSION = "dem_curv_laplacian_parity_verification_v1"
DEM_CURV_LAPLACIAN_CLASSIFICATION = "notebook-parity"
DEM_CURV_LAPLACIAN_REPORT_RELATIVE_PATH = (
    "manifests/dem_curv_laplacian_parity_verification.json"
)
APP_CURVATURE_OUTPUT_NAME = "curvature.tif"
NOTEBOOK_CURV_LAPLACIAN_OUTPUT_NAME = "curv_laplacian_640.tif"

ALLOWED_STATUSES = {
    "passed",
    "missing_app_output",
    "missing_reference_output",
    "metadata_mismatch",
    "value_mismatch",
    "comparison_unavailable",
    "error",
}
ALLOWED_OVERALL_STATUSES = {
    "passed",
    "failed",
    "incomplete",
    "comparison_unavailable",
}


@dataclass(frozen=True)
class DemCurvLaplacianVerificationResult:
    report_path: Path
    overall_status: str
    status: str
    raster_value_comparison_available: bool


def verify_dem_curv_laplacian_parity(
    app_output_dir: str | Path,
    notebook_reference_dir: str | Path,
    run_dir: str | Path,
    run_id: str,
    *,
    atol: float = 1e-6,
    rtol: float = 1e-6,
    report_relative_path: str | Path = DEM_CURV_LAPLACIAN_REPORT_RELATIVE_PATH,
) -> DemCurvLaplacianVerificationResult:
    """Compare app curvature.tif against notebook curv_laplacian_640.tif.

    This helper is verification-only. It writes one JSON report and does not
    create aliases, rasters, or live pipeline artifacts.
    """

    app_root = Path(app_output_dir)
    reference_root = Path(notebook_reference_dir)
    app_path = app_root / APP_CURVATURE_OUTPUT_NAME
    reference_path = reference_root / NOTEBOOK_CURV_LAPLACIAN_OUTPUT_NAME
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    rasterio_available = _rasterio_available()
    payload = _base_report(
        run_id=run_id,
        app_root=app_root,
        reference_root=reference_root,
        app_path=app_path,
        reference_path=reference_path,
        rasterio_available=rasterio_available,
    )

    app_exists = app_path.is_file()
    reference_exists = reference_path.is_file()
    payload["app_exists"] = app_exists
    payload["reference_exists"] = reference_exists

    if not app_exists:
        _finish_report(
            payload,
            status="missing_app_output",
            overall_status="incomplete",
            notes="App curvature.tif output is missing.",
        )
    elif not reference_exists:
        _finish_report(
            payload,
            status="missing_reference_output",
            overall_status="incomplete",
            runtime_output_verified=True,
            notes="Frozen notebook curv_laplacian_640.tif reference output is missing.",
        )
    elif not rasterio_available:
        _finish_report(
            payload,
            status="comparison_unavailable",
            overall_status="comparison_unavailable",
            runtime_output_verified=True,
            notes="Raster metadata/value comparison unavailable because rasterio is not importable.",
        )
    else:
        try:
            _compare_rasters(payload, app_path, reference_path, atol=atol, rtol=rtol)
        except Exception as exc:  # pragma: no cover - defensive report path
            _finish_report(
                payload,
                status="error",
                overall_status="failed",
                runtime_output_verified=True,
                notes=f"Raster comparison failed: {type(exc).__name__}: {exc}",
            )

    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return DemCurvLaplacianVerificationResult(
        report_path=report_path,
        overall_status=str(payload["overall_status"]),
        status=str(payload["status"]),
        raster_value_comparison_available=rasterio_available,
    )


def _base_report(
    *,
    run_id: str,
    app_root: Path,
    reference_root: Path,
    app_path: Path,
    reference_path: Path,
    rasterio_available: bool,
) -> dict[str, Any]:
    return {
        "schema_version": DEM_CURV_LAPLACIAN_VERIFICATION_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "app_output_dir": str(app_root),
        "notebook_reference_dir": str(reference_root),
        "app_output_name": APP_CURVATURE_OUTPUT_NAME,
        "reference_output_name": NOTEBOOK_CURV_LAPLACIAN_OUTPUT_NAME,
        "app_path": str(app_path),
        "reference_path": str(reference_path),
        "app_exists": False,
        "reference_exists": False,
        "metadata_compared": False,
        "values_compared": False,
        "width_match": None,
        "height_match": None,
        "crs_match": None,
        "transform_match": None,
        "dtype_match": None,
        "nodata_match": None,
        "band_count_match": None,
        "max_abs_diff": None,
        "mean_abs_diff": None,
        "count_compared_pixels": 0,
        "count_nan_or_nodata_pixels": 0,
        "within_tolerance": False,
        "runtime_output_verified": False,
        "notebook_value_parity_verified": False,
        "status": "comparison_unavailable",
        "overall_status": "comparison_unavailable",
        "classification": DEM_CURV_LAPLACIAN_CLASSIFICATION,
        "target_mode": "notebook_parity",
        "artifact_class": "LOCAL_SENSITIVE",
        "http_servable": False,
        "requires_coordinates": False,
        "probability_only_required": False,
        "raster_value_comparison_available": rasterio_available,
        "notes": "",
    }


def _finish_report(
    payload: dict[str, Any],
    *,
    status: str,
    overall_status: str,
    runtime_output_verified: bool = False,
    notebook_value_parity_verified: bool = False,
    notes: str,
) -> None:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"unsupported DEM curv_laplacian status: {status}")
    if overall_status not in ALLOWED_OVERALL_STATUSES:
        raise ValueError(f"unsupported DEM curv_laplacian overall_status: {overall_status}")
    payload["status"] = status
    payload["overall_status"] = overall_status
    payload["runtime_output_verified"] = runtime_output_verified
    payload["notebook_value_parity_verified"] = notebook_value_parity_verified
    payload["notes"] = notes


def _compare_rasters(
    payload: dict[str, Any],
    app_path: Path,
    reference_path: Path,
    *,
    atol: float,
    rtol: float,
) -> None:
    import rasterio

    with rasterio.open(app_path) as app_dataset, rasterio.open(reference_path) as reference_dataset:
        metadata_matches = _compare_metadata(payload, app_dataset, reference_dataset)
        payload["metadata_compared"] = True
        if not metadata_matches:
            _finish_report(
                payload,
                status="metadata_mismatch",
                overall_status="failed",
                runtime_output_verified=True,
                notes="Raster metadata did not match; value comparison was not run.",
            )
            return

        app_data = app_dataset.read(masked=True).astype("float64")
        reference_data = reference_dataset.read(masked=True).astype("float64")

    payload.update(_diff_stats(app_data, reference_data, atol=atol, rtol=rtol))
    payload["values_compared"] = True
    if payload["within_tolerance"]:
        _finish_report(
            payload,
            status="passed",
            overall_status="passed",
            runtime_output_verified=True,
            notebook_value_parity_verified=True,
            notes="App curvature.tif and notebook curv_laplacian_640.tif match within tolerance.",
        )
        return

    _finish_report(
        payload,
        status="value_mismatch",
        overall_status="failed",
        runtime_output_verified=True,
        notes="Raster values differ outside tolerance.",
    )


def _compare_metadata(payload: dict[str, Any], app_dataset: Any, reference_dataset: Any) -> bool:
    matches = {
        "width_match": app_dataset.width == reference_dataset.width,
        "height_match": app_dataset.height == reference_dataset.height,
        "crs_match": str(app_dataset.crs) == str(reference_dataset.crs),
        "transform_match": tuple(app_dataset.transform) == tuple(reference_dataset.transform),
        "dtype_match": tuple(app_dataset.dtypes) == tuple(reference_dataset.dtypes),
        "nodata_match": tuple(app_dataset.nodatavals) == tuple(reference_dataset.nodatavals),
        "band_count_match": app_dataset.count == reference_dataset.count,
    }
    payload.update(matches)
    return all(matches.values())


def _diff_stats(
    app_data: np.ma.MaskedArray,
    reference_data: np.ma.MaskedArray,
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    app_filled = np.asarray(app_data.filled(np.nan), dtype=np.float64)
    reference_filled = np.asarray(reference_data.filled(np.nan), dtype=np.float64)
    app_mask = np.ma.getmaskarray(app_data) | ~np.isfinite(app_filled)
    reference_mask = np.ma.getmaskarray(reference_data) | ~np.isfinite(reference_filled)
    invalid = app_mask | reference_mask
    valid = ~invalid
    count_compared = int(np.count_nonzero(valid))
    count_invalid = int(np.count_nonzero(invalid))

    if count_compared == 0:
        return {
            "max_abs_diff": None,
            "mean_abs_diff": None,
            "count_compared_pixels": 0,
            "count_nan_or_nodata_pixels": count_invalid,
            "within_tolerance": False,
        }

    app_valid = app_filled[valid]
    reference_valid = reference_filled[valid]
    abs_diff = np.abs(app_valid - reference_valid)
    return {
        "max_abs_diff": float(np.max(abs_diff)),
        "mean_abs_diff": float(np.mean(abs_diff)),
        "count_compared_pixels": count_compared,
        "count_nan_or_nodata_pixels": count_invalid,
        "within_tolerance": bool(
            np.allclose(app_valid, reference_valid, atol=atol, rtol=rtol, equal_nan=True)
        ),
    }


def _rasterio_available() -> bool:
    return importlib.util.find_spec("rasterio") is not None
