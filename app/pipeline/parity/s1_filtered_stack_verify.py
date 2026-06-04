from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from app.pipeline.parity import resolve_run_output_path


S1_FILTERED_STACK_VERIFICATION_SCHEMA_VERSION = (
    "s1_filtered_layers_stack_verification_v1"
)
S1_FILTERED_STACK_REPORT_RELATIVE_PATH = (
    "manifests/s1_filtered_layers_stack_verification.json"
)
S1_FILTERED_STACK_OUTPUT_NAME = "S1_FILTERED_LAYERS_STACK_640.npy"
S1_FILTERED_STACK_FAMILY = "SAR/radar outputs"
S1_FILTERED_STACK_CLASSIFICATION = "notebook-parity"

ALLOWED_STATUSES = {
    "passed",
    "missing_app_output",
    "missing_reference_output",
    "shape_mismatch",
    "dtype_mismatch",
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
class S1FilteredStackVerificationResult:
    report_path: Path
    overall_status: str
    status: str


def verify_s1_filtered_stack_parity(
    app_output_dir: str | Path,
    notebook_reference_dir: str | Path,
    run_dir: str | Path,
    run_id: str,
    *,
    atol: float = 1e-6,
    rtol: float = 1e-6,
    report_relative_path: str | Path = S1_FILTERED_STACK_REPORT_RELATIVE_PATH,
) -> S1FilteredStackVerificationResult:
    """Verify a future app S1 filtered layers stack against a notebook reference."""

    app_root = Path(app_output_dir)
    reference_root = Path(notebook_reference_dir)
    app_path = _find_expected_file(app_root)
    reference_path = _find_expected_file(reference_root)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload = _base_report(
        run_id=run_id,
        app_root=app_root,
        reference_root=reference_root,
        app_path=app_path,
        reference_path=reference_path,
    )
    app_exists = app_path.is_file()
    reference_exists = reference_path.is_file()
    payload["app_exists"] = app_exists
    payload["reference_exists"] = reference_exists
    payload["app_sha256"] = _sha256_file(app_path) if app_exists else None
    payload["reference_sha256"] = _sha256_file(reference_path) if reference_exists else None
    payload["hash_match"] = (
        payload["app_sha256"] == payload["reference_sha256"]
        if payload["app_sha256"] and payload["reference_sha256"]
        else None
    )

    if not app_exists:
        _finish_report(
            payload,
            status="missing_app_output",
            overall_status="incomplete",
            notes="App S1_FILTERED_LAYERS_STACK_640.npy output is missing.",
        )
    elif not reference_exists:
        _finish_report(
            payload,
            status="missing_reference_output",
            overall_status="incomplete",
            runtime_output_verified=True,
            notes="Frozen notebook S1_FILTERED_LAYERS_STACK_640.npy reference is missing.",
        )
    else:
        try:
            _compare_npy(payload, app_path, reference_path, atol=atol, rtol=rtol)
        except Exception as exc:  # pragma: no cover - defensive report path
            _finish_report(
                payload,
                status="error",
                overall_status="failed",
                runtime_output_verified=True,
                notes=f"NPY comparison failed: {type(exc).__name__}: {exc}",
            )

    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return S1FilteredStackVerificationResult(
        report_path=report_path,
        overall_status=str(payload["overall_status"]),
        status=str(payload["status"]),
    )


def _base_report(
    *,
    run_id: str,
    app_root: Path,
    reference_root: Path,
    app_path: Path,
    reference_path: Path,
) -> dict[str, Any]:
    return {
        "schema_version": S1_FILTERED_STACK_VERIFICATION_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "app_output_dir": str(app_root),
        "notebook_reference_dir": str(reference_root),
        "output_name": S1_FILTERED_STACK_OUTPUT_NAME,
        "app_path": str(app_path),
        "reference_path": str(reference_path),
        "app_exists": False,
        "reference_exists": False,
        "app_sha256": None,
        "reference_sha256": None,
        "hash_match": None,
        "shape_match": None,
        "dtype_match": None,
        "max_abs_diff": None,
        "mean_abs_diff": None,
        "count_compared_values": 0,
        "count_nan_or_nodata_values": 0,
        "within_tolerance": False,
        "values_compared": False,
        "runtime_output_verified": False,
        "notebook_value_parity_verified": False,
        "status": "comparison_unavailable",
        "overall_status": "comparison_unavailable",
        "family": S1_FILTERED_STACK_FAMILY,
        "classification": S1_FILTERED_STACK_CLASSIFICATION,
        "target_mode": "notebook_parity",
        "artifact_class": "FILESYSTEM_ONLY",
        "http_servable": False,
        "requires_coordinates": False,
        "probability_only_required": False,
        "notes": "",
    }


def _compare_npy(
    payload: dict[str, Any],
    app_path: Path,
    reference_path: Path,
    *,
    atol: float,
    rtol: float,
) -> None:
    app_data = np.load(app_path, allow_pickle=False)
    reference_data = np.load(reference_path, allow_pickle=False)

    payload["shape_match"] = app_data.shape == reference_data.shape
    payload["dtype_match"] = app_data.dtype == reference_data.dtype
    if not payload["shape_match"]:
        _finish_report(
            payload,
            status="shape_mismatch",
            overall_status="failed",
            runtime_output_verified=True,
            notes="NPY shapes did not match; value comparison was not run.",
        )
        return
    if not payload["dtype_match"]:
        _finish_report(
            payload,
            status="dtype_mismatch",
            overall_status="failed",
            runtime_output_verified=True,
            notes="NPY dtypes did not match; value comparison was not run.",
        )
        return

    payload.update(_diff_stats(app_data, reference_data, atol=atol, rtol=rtol))
    payload["values_compared"] = True
    if payload["within_tolerance"]:
        _finish_report(
            payload,
            status="passed",
            overall_status="passed",
            runtime_output_verified=True,
            notebook_value_parity_verified=True,
            notes="App and notebook S1 filtered stack outputs match within tolerance.",
        )
        return

    _finish_report(
        payload,
        status="value_mismatch",
        overall_status="failed",
        runtime_output_verified=True,
        notes="NPY values differ outside tolerance.",
    )


def _diff_stats(
    app_data: np.ndarray,
    reference_data: np.ndarray,
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    app_float = np.asarray(app_data, dtype=np.float64)
    reference_float = np.asarray(reference_data, dtype=np.float64)
    invalid = ~np.isfinite(app_float) | ~np.isfinite(reference_float)
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

    app_valid = app_float[valid]
    reference_valid = reference_float[valid]
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
        raise ValueError(f"unsupported S1 filtered stack status: {status}")
    if overall_status not in ALLOWED_OVERALL_STATUSES:
        raise ValueError(
            f"unsupported S1 filtered stack overall_status: {overall_status}"
        )
    payload["status"] = status
    payload["overall_status"] = overall_status
    payload["runtime_output_verified"] = runtime_output_verified
    payload["notebook_value_parity_verified"] = notebook_value_parity_verified
    payload["notes"] = notes


def _find_expected_file(root: Path) -> Path:
    direct = root / S1_FILTERED_STACK_OUTPUT_NAME
    if direct.is_file():
        return direct
    nested = root / "NPY_STACKS" / S1_FILTERED_STACK_OUTPUT_NAME
    if nested.is_file():
        return nested
    return direct


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
