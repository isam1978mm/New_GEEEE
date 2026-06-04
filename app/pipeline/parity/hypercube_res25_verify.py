from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

from app.pipeline.parity import resolve_run_output_path


HYPERCUBE_RES25_VERIFICATION_SCHEMA_VERSION = (
    "hypercube_res_2p5m_parity_verification_v1"
)
HYPERCUBE_RES25_REPORT_RELATIVE_PATH = (
    "manifests/hypercube_res_2p5m_parity_verification.json"
)
HYPERCUBE_RES25_CLASSIFICATION = "notebook-parity"
HYPERCUBE_RES25_FAMILY = "hypercube/tensor outputs"
HYPERCUBE_RES25_OUTPUT_NAMES = (
    "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif",
    "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy",
)

ALLOWED_OUTPUT_STATUSES = {
    "passed",
    "missing_app_output",
    "missing_reference_output",
    "metadata_mismatch",
    "value_mismatch",
    "shape_mismatch",
    "dtype_mismatch",
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
class HypercubeRes25VerificationResult:
    report_path: Path
    overall_status: str
    outputs: tuple[dict[str, Any], ...]
    raster_value_comparison_available: bool
    npy_outputs_passed: bool


def verify_hypercube_res25_parity(
    app_output_dir: str | Path,
    notebook_reference_dir: str | Path,
    run_dir: str | Path,
    run_id: str,
    *,
    atol: float = 1e-6,
    rtol: float = 1e-6,
    report_relative_path: str | Path = HYPERCUBE_RES25_REPORT_RELATIVE_PATH,
) -> HypercubeRes25VerificationResult:
    """Verify future 2.5 m hypercube outputs against frozen notebook references."""

    app_root = Path(app_output_dir)
    reference_root = Path(notebook_reference_dir)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    rasterio_available = _rasterio_available()
    output_items = tuple(
        _verify_one_output(
            output_name,
            app_root,
            reference_root,
            rasterio_available=rasterio_available,
            atol=atol,
            rtol=rtol,
        )
        for output_name in HYPERCUBE_RES25_OUTPUT_NAMES
    )
    overall_status = _overall_status(output_items)
    npy_outputs_passed = all(
        item["status"] == "passed" for item in output_items if item["file_type"] == "npy"
    )
    payload = {
        "schema_version": HYPERCUBE_RES25_VERIFICATION_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "app_output_dir": str(app_root),
        "notebook_reference_dir": str(reference_root),
        "outputs": list(output_items),
        "classification": HYPERCUBE_RES25_CLASSIFICATION,
        "family": HYPERCUBE_RES25_FAMILY,
        "target_mode": "notebook_parity",
        "http_servable": False,
        "raster_value_comparison_available": rasterio_available,
        "npy_outputs_passed": npy_outputs_passed,
        "overall_status": overall_status,
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return HypercubeRes25VerificationResult(
        report_path=report_path,
        overall_status=overall_status,
        outputs=output_items,
        raster_value_comparison_available=rasterio_available,
        npy_outputs_passed=npy_outputs_passed,
    )


def _verify_one_output(
    output_name: str,
    app_root: Path,
    reference_root: Path,
    *,
    rasterio_available: bool,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    app_path = _find_expected_file(app_root, output_name)
    reference_path = _find_expected_file(reference_root, output_name)
    item = _base_output_item(output_name, app_path, reference_path)

    app_exists = app_path.is_file()
    reference_exists = reference_path.is_file()
    item["app_exists"] = app_exists
    item["reference_exists"] = reference_exists
    item["app_sha256"] = _sha256_file(app_path) if app_exists else None
    item["reference_sha256"] = _sha256_file(reference_path) if reference_exists else None
    item["hash_match"] = (
        item["app_sha256"] == item["reference_sha256"]
        if item["app_sha256"] and item["reference_sha256"]
        else None
    )

    if not app_exists:
        return _finish_output(
            item,
            status="missing_app_output",
            notes="App 2.5 m hypercube output is missing.",
        )
    if not reference_exists:
        return _finish_output(
            item,
            status="missing_reference_output",
            runtime_output_verified=True,
            notes="Frozen notebook 2.5 m hypercube reference is missing.",
        )

    if output_name.endswith(".npy"):
        try:
            return _compare_npy(item, app_path, reference_path, atol=atol, rtol=rtol)
        except Exception as exc:  # pragma: no cover
            return _finish_output(
                item,
                status="error",
                runtime_output_verified=True,
                notes=f"NPY comparison failed: {type(exc).__name__}: {exc}",
            )

    if not rasterio_available:
        return _finish_output(
            item,
            status="comparison_unavailable",
            runtime_output_verified=True,
            notes="Raster metadata/value comparison unavailable because rasterio is not importable.",
        )

    try:
        return _compare_tif(item, app_path, reference_path, atol=atol, rtol=rtol)
    except Exception as exc:  # pragma: no cover
        return _finish_output(
            item,
            status="error",
            runtime_output_verified=True,
            notes=f"Raster comparison failed: {type(exc).__name__}: {exc}",
        )


def _base_output_item(output_name: str, app_path: Path, reference_path: Path) -> dict[str, Any]:
    file_type = "npy" if output_name.endswith(".npy") else "tif"
    return {
        "output_name": output_name,
        "app_path": str(app_path),
        "reference_path": str(reference_path),
        "app_exists": False,
        "reference_exists": False,
        "file_type": file_type,
        "app_sha256": None,
        "reference_sha256": None,
        "hash_match": None,
        "metadata_compared": False,
        "values_compared": False,
        "width_match": None,
        "height_match": None,
        "crs_match": None,
        "transform_match": None,
        "pixel_size_match": None,
        "dtype_match": None,
        "nodata_match": None,
        "band_count_match": None,
        "shape_match": None,
        "max_abs_diff": None,
        "mean_abs_diff": None,
        "count_compared_values": 0,
        "count_nan_or_nodata_values": 0,
        "within_tolerance": False,
        "runtime_output_verified": False,
        "notebook_value_parity_verified": False,
        "status": "comparison_unavailable",
        "classification": HYPERCUBE_RES25_CLASSIFICATION,
        "target_mode": "notebook_parity",
        "artifact_class": "FILESYSTEM_ONLY" if file_type == "npy" else "LOCAL_SENSITIVE",
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
        raise ValueError(f"unsupported hypercube_res25 output status: {status}")
    item["status"] = status
    item["runtime_output_verified"] = runtime_output_verified
    item["notebook_value_parity_verified"] = notebook_value_parity_verified
    item["notes"] = notes
    return item


def _compare_npy(
    item: dict[str, Any],
    app_path: Path,
    reference_path: Path,
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    app_data = np.load(app_path, allow_pickle=False)
    reference_data = np.load(reference_path, allow_pickle=False)

    item["shape_match"] = app_data.shape == reference_data.shape
    item["dtype_match"] = app_data.dtype == reference_data.dtype
    if not item["shape_match"]:
        return _finish_output(
            item,
            status="shape_mismatch",
            runtime_output_verified=True,
            notes="NPY shapes did not match; value comparison was not run.",
        )
    if not item["dtype_match"]:
        return _finish_output(
            item,
            status="dtype_mismatch",
            runtime_output_verified=True,
            notes="NPY dtypes did not match; value comparison was not run.",
        )

    item.update(_diff_stats(app_data, reference_data, atol=atol, rtol=rtol))
    item["values_compared"] = True
    if item["within_tolerance"]:
        return _finish_output(
            item,
            status="passed",
            runtime_output_verified=True,
            notebook_value_parity_verified=True,
            notes="App and notebook 2.5 m hypercube NPY outputs match within tolerance.",
        )
    return _finish_output(
        item,
        status="value_mismatch",
        runtime_output_verified=True,
        notes="NPY values differ outside tolerance.",
    )


def _compare_tif(
    item: dict[str, Any],
    app_path: Path,
    reference_path: Path,
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    import rasterio

    with rasterio.open(app_path) as app_dataset, rasterio.open(reference_path) as reference_dataset:
        metadata_matches = _compare_raster_metadata(item, app_dataset, reference_dataset)
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

    item.update(_diff_stats(app_data, reference_data, atol=atol, rtol=rtol))
    item["values_compared"] = True
    if item["within_tolerance"]:
        return _finish_output(
            item,
            status="passed",
            runtime_output_verified=True,
            notebook_value_parity_verified=True,
            notes="App and notebook 2.5 m hypercube raster outputs match within tolerance.",
        )
    return _finish_output(
        item,
        status="value_mismatch",
        runtime_output_verified=True,
        notes="Raster values differ outside tolerance.",
    )


def _compare_raster_metadata(
    item: dict[str, Any],
    app_dataset: Any,
    reference_dataset: Any,
) -> bool:
    app_res = tuple(float(abs(value)) for value in app_dataset.res)
    reference_res = tuple(float(abs(value)) for value in reference_dataset.res)
    matches = {
        "width_match": app_dataset.width == reference_dataset.width,
        "height_match": app_dataset.height == reference_dataset.height,
        "crs_match": str(app_dataset.crs) == str(reference_dataset.crs),
        "transform_match": tuple(app_dataset.transform) == tuple(reference_dataset.transform),
        "pixel_size_match": app_res == reference_res,
        "dtype_match": tuple(app_dataset.dtypes) == tuple(reference_dataset.dtypes),
        "nodata_match": tuple(app_dataset.nodatavals) == tuple(reference_dataset.nodatavals),
        "band_count_match": app_dataset.count == reference_dataset.count,
    }
    item.update(matches)
    return all(matches.values())


def _diff_stats(
    app_data: np.ndarray | np.ma.MaskedArray,
    reference_data: np.ndarray | np.ma.MaskedArray,
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    app_filled = _as_float_array(app_data)
    reference_filled = _as_float_array(reference_data)
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
            "count_compared_values": 0,
            "count_nan_or_nodata_values": count_invalid,
            "within_tolerance": False,
        }

    app_valid = app_filled[valid]
    reference_valid = reference_filled[valid]
    abs_diff = np.abs(app_valid - reference_valid)
    return {
        "max_abs_diff": float(np.max(abs_diff)),
        "mean_abs_diff": float(np.mean(abs_diff)),
        "count_compared_values": count_compared,
        "count_nan_or_nodata_values": count_invalid,
        "within_tolerance": bool(
            np.allclose(app_valid, reference_valid, atol=atol, rtol=rtol, equal_nan=True)
        ),
    }


def _as_float_array(data: np.ndarray | np.ma.MaskedArray) -> np.ndarray:
    if isinstance(data, np.ma.MaskedArray):
        return np.asarray(data.filled(np.nan), dtype=np.float64)
    return np.asarray(data, dtype=np.float64)


def _find_expected_file(root: Path, output_name: str) -> Path:
    direct = root / output_name
    if direct.is_file():
        return direct
    nested = root / "NPY_STACKS" / output_name
    if nested.is_file():
        return nested
    return direct


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _overall_status(outputs: tuple[dict[str, Any], ...]) -> str:
    statuses = {item["status"] for item in outputs}
    if statuses == {"passed"}:
        return "passed"
    if statuses & {"missing_app_output", "missing_reference_output"}:
        return "incomplete"
    if statuses & {"metadata_mismatch", "value_mismatch", "shape_mismatch", "dtype_mismatch", "error"}:
        return "failed"
    if "comparison_unavailable" in statuses:
        return "comparison_unavailable"
    return "failed"


def _rasterio_available() -> bool:
    return importlib.util.find_spec("rasterio") is not None
