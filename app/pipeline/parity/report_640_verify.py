from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

from app.pipeline.parity import resolve_run_output_path


REPORT_640_VERIFICATION_SCHEMA_VERSION = "report_640_parity_verification_v1"
REPORT_640_CLASSIFICATION = "notebook-parity report/semantic raster stage"
REPORT_640_REPORT_RELATIVE_PATH = "manifests/report_640_parity_verification.json"
REPORT_640_OUTPUT_NAMES = (
    "REPORT_640_Pottery_Report.tif",
    "REPORT_640_Mass_Report.tif",
    "REPORT_640_FINAL_Zero_Point_Targets.tif",
)

ALLOWED_OUTPUT_STATUSES = {
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
class Report640VerificationResult:
    report_path: Path
    overall_status: str
    outputs: tuple[dict[str, Any], ...]
    raster_value_comparison_available: bool


def verify_report_640_parity(
    app_output_dir: str | Path,
    notebook_reference_dir: str | Path,
    run_dir: str | Path,
    run_id: str,
    *,
    atol: float = 1e-6,
    rtol: float = 1e-6,
    report_relative_path: str | Path = REPORT_640_REPORT_RELATIVE_PATH,
) -> Report640VerificationResult:
    """Verify app REPORT_640 rasters against a frozen notebook reference tree.

    This helper is intentionally not integrated into the live pipeline. It writes
    only a JSON verification report under the run manifests directory.
    """

    app_root = Path(app_output_dir)
    reference_root = Path(notebook_reference_dir)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    rasterio_available = _rasterio_available()
    output_items = tuple(
        _verify_one_output(
            output_name,
            app_root / output_name,
            reference_root / output_name,
            rasterio_available=rasterio_available,
            atol=atol,
            rtol=rtol,
        )
        for output_name in REPORT_640_OUTPUT_NAMES
    )
    overall_status = _overall_status(output_items)
    payload = {
        "schema_version": REPORT_640_VERIFICATION_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "app_output_dir": str(app_root),
        "notebook_reference_dir": str(reference_root),
        "outputs": list(output_items),
        "classification": REPORT_640_CLASSIFICATION,
        "target_mode": "notebook_parity",
        "artifact_class": "LOCAL_SENSITIVE",
        "http_servable": False,
        "raster_value_comparison_available": rasterio_available,
        "overall_status": overall_status,
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return Report640VerificationResult(
        report_path=report_path,
        overall_status=overall_status,
        outputs=output_items,
        raster_value_comparison_available=rasterio_available,
    )


def _verify_one_output(
    output_name: str,
    app_path: Path,
    reference_path: Path,
    *,
    rasterio_available: bool,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    base = _base_output_item(output_name, app_path, reference_path)
    app_exists = app_path.is_file()
    reference_exists = reference_path.is_file()
    base["app_exists"] = app_exists
    base["reference_exists"] = reference_exists

    if not app_exists:
        return _finish_output(
            base,
            status="missing_app_output",
            notes="App REPORT_640 output is missing.",
        )
    if not reference_exists:
        return _finish_output(
            base,
            status="missing_reference_output",
            runtime_output_verified=True,
            notes="Frozen notebook reference output is missing.",
        )
    if not rasterio_available:
        return _finish_output(
            base,
            status="comparison_unavailable",
            runtime_output_verified=True,
            notes="Raster metadata/value comparison unavailable because rasterio is not importable.",
        )

    try:
        return _compare_rasters(base, app_path, reference_path, atol=atol, rtol=rtol)
    except Exception as exc:  # pragma: no cover - defensive report path
        return _finish_output(
            base,
            status="error",
            runtime_output_verified=True,
            notes=f"Raster comparison failed: {type(exc).__name__}: {exc}",
        )


def _base_output_item(output_name: str, app_path: Path, reference_path: Path) -> dict[str, Any]:
    return {
        "output_name": output_name,
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
        "classification": REPORT_640_CLASSIFICATION,
        "target_mode": "notebook_parity",
        "artifact_class": "LOCAL_SENSITIVE",
        "http_servable": False,
        "requires_coordinates": False,
        "probability_only_required": False,
        "notes": "",
    }


def _finish_output(
    item: dict[str, Any],
    *,
    status: str,
    runtime_output_verified: bool = False,
    notebook_value_parity_verified: bool = False,
    notes: str,
) -> dict[str, Any]:
    if status not in ALLOWED_OUTPUT_STATUSES:
        raise ValueError(f"unsupported REPORT_640 output status: {status}")
    item["status"] = status
    item["runtime_output_verified"] = runtime_output_verified
    item["notebook_value_parity_verified"] = notebook_value_parity_verified
    item["notes"] = notes
    return item


def _compare_rasters(
    item: dict[str, Any],
    app_path: Path,
    reference_path: Path,
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    import rasterio

    with rasterio.open(app_path) as app_dataset, rasterio.open(reference_path) as reference_dataset:
        metadata_matches = _compare_metadata(item, app_dataset, reference_dataset)
        item["metadata_compared"] = True
        if not metadata_matches:
            return _finish_output(
                item,
                status="metadata_mismatch",
                runtime_output_verified=True,
                notes="Raster metadata did not match; value comparison was not run.",
            )

        app_data = app_dataset.read(masked=True).astype("float64")
        reference_data = reference_dataset.read(masked=True).astype("float64")

    diff_stats = _diff_stats(app_data, reference_data, atol=atol, rtol=rtol)
    item.update(diff_stats)
    item["values_compared"] = True
    if diff_stats["within_tolerance"]:
        return _finish_output(
            item,
            status="passed",
            runtime_output_verified=True,
            notebook_value_parity_verified=True,
            notes="Runtime output and notebook reference match within tolerance.",
        )
    return _finish_output(
        item,
        status="value_mismatch",
        runtime_output_verified=True,
        notes="Raster values differ outside tolerance.",
    )


def _compare_metadata(item: dict[str, Any], app_dataset: Any, reference_dataset: Any) -> bool:
    matches = {
        "width_match": app_dataset.width == reference_dataset.width,
        "height_match": app_dataset.height == reference_dataset.height,
        "crs_match": str(app_dataset.crs) == str(reference_dataset.crs),
        "transform_match": tuple(app_dataset.transform) == tuple(reference_dataset.transform),
        "dtype_match": tuple(app_dataset.dtypes) == tuple(reference_dataset.dtypes),
        "nodata_match": tuple(app_dataset.nodatavals) == tuple(reference_dataset.nodatavals),
        "band_count_match": app_dataset.count == reference_dataset.count,
    }
    item.update(matches)
    return all(matches.values())


def _diff_stats(app_data: np.ma.MaskedArray, reference_data: np.ma.MaskedArray, *, atol: float, rtol: float) -> dict[str, Any]:
    app_mask = np.ma.getmaskarray(app_data) | ~np.isfinite(np.asarray(app_data.filled(np.nan)))
    reference_mask = np.ma.getmaskarray(reference_data) | ~np.isfinite(np.asarray(reference_data.filled(np.nan)))
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

    app_valid = np.asarray(app_data.filled(np.nan), dtype=np.float64)[valid]
    reference_valid = np.asarray(reference_data.filled(np.nan), dtype=np.float64)[valid]
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


def _overall_status(outputs: tuple[dict[str, Any], ...]) -> str:
    statuses = {item["status"] for item in outputs}
    if statuses == {"passed"}:
        return "passed"
    if statuses & {"missing_app_output", "missing_reference_output"}:
        return "incomplete"
    if statuses == {"comparison_unavailable"}:
        return "comparison_unavailable"
    return "failed"


def _rasterio_available() -> bool:
    return importlib.util.find_spec("rasterio") is not None
