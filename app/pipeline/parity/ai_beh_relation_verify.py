from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from app.pipeline.parity import resolve_run_output_path


AI_BEH_RELATION_VERIFICATION_SCHEMA_VERSION = (
    "ai_beh_relation_parity_verification_v1"
)
AI_BEH_RELATION_REPORT_RELATIVE_PATH = (
    "manifests/ai_beh_relation_parity_verification.json"
)
AI_BEH_RELATION_CLASSIFICATION = "notebook-parity semantic raster stage"
AI_BEH_RELATION_FAMILY = "AI_BEH semantic rasters"
AI_BEH_RELATION_OUTPUT_NAMES = (
    "AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif",
    "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif",
    "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif",
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
class AIBehRelationVerificationResult:
    report_path: Path
    overall_status: str
    outputs: tuple[dict[str, Any], ...]
    raster_value_comparison_available: bool


def verify_ai_beh_relation_parity(
    app_output_dir: str | Path,
    notebook_reference_dir: str | Path,
    run_dir: str | Path,
    run_id: str,
    *,
    atol: float = 1e-6,
    rtol: float = 1e-6,
    report_relative_path: str | Path = AI_BEH_RELATION_REPORT_RELATIVE_PATH,
) -> AIBehRelationVerificationResult:
    """Verify AI_BEH relation parity against frozen notebook reference rasters."""

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
        for output_name in AI_BEH_RELATION_OUTPUT_NAMES
    )
    overall_status = _overall_status(output_items)
    payload = {
        "schema_version": AI_BEH_RELATION_VERIFICATION_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "app_output_dir": str(app_root),
        "notebook_reference_dir": str(reference_root),
        "outputs": list(output_items),
        "classification": AI_BEH_RELATION_CLASSIFICATION,
        "family": AI_BEH_RELATION_FAMILY,
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
    return AIBehRelationVerificationResult(
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
            notes="App AI_BEH relation output is missing.",
        )
    if not reference_exists:
        return _finish_output(
            item,
            status="missing_reference_output",
            runtime_output_verified=True,
            notes="Frozen notebook AI_BEH relation reference is missing.",
        )
    if not rasterio_available:
        return _finish_output(
            item,
            status="comparison_unavailable",
            runtime_output_verified=True,
            notes=(
                "Raster metadata/value comparison unavailable because rasterio is not "
                "importable; SHA256 hashes were recorded for presence tracking only."
            ),
        )

    try:
        return _compare_rasters(item, app_path, reference_path, atol=atol, rtol=rtol)
    except Exception as exc:  # pragma: no cover
        return _finish_output(
            item,
            status="error",
            runtime_output_verified=True,
            notes=f"Raster comparison failed: {type(exc).__name__}: {exc}",
        )


def _base_output_item(
    output_name: str, app_path: Path, reference_path: Path
) -> dict[str, Any]:
    return {
        "output_name": output_name,
        "app_path": str(app_path),
        "reference_path": str(reference_path),
        "app_exists": False,
        "reference_exists": False,
        "file_type": "tif",
        "app_sha256": None,
        "reference_sha256": None,
        "hash_match": None,
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
        "count_compared_values": 0,
        "count_nan_or_nodata_values": 0,
        "within_tolerance": False,
        "runtime_output_verified": False,
        "notebook_value_parity_verified": False,
        "status": "comparison_unavailable",
        "classification": AI_BEH_RELATION_CLASSIFICATION,
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
        raise ValueError(f"unsupported AI_BEH relation output status: {status}")
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
    import numpy as np
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

    item.update(_diff_stats(np, app_data, reference_data, atol=atol, rtol=rtol))
    item["values_compared"] = True
    if item["within_tolerance"]:
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
        "transform_match": tuple(app_dataset.transform)
        == tuple(reference_dataset.transform),
        "dtype_match": tuple(app_dataset.dtypes) == tuple(reference_dataset.dtypes),
        "nodata_match": tuple(app_dataset.nodatavals)
        == tuple(reference_dataset.nodatavals),
        "band_count_match": app_dataset.count == reference_dataset.count,
    }
    item.update(matches)
    return all(matches.values())


def _diff_stats(
    np: Any,
    app_data: Any,
    reference_data: Any,
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    app_filled = np.ma.filled(app_data, np.nan)
    reference_filled = np.ma.filled(reference_data, np.nan)
    valid = np.isfinite(app_filled) & np.isfinite(reference_filled)
    nan_or_nodata = (~valid).sum()

    if valid.any():
        diffs = np.abs(app_filled[valid] - reference_filled[valid])
        max_abs_diff = float(diffs.max())
        mean_abs_diff = float(diffs.mean())
        within = bool(
            np.allclose(
                app_filled[valid],
                reference_filled[valid],
                atol=atol,
                rtol=rtol,
                equal_nan=True,
            )
        )
        count_compared = int(valid.sum())
    else:
        max_abs_diff = 0.0
        mean_abs_diff = 0.0
        within = True
        count_compared = 0

    return {
        "max_abs_diff": max_abs_diff,
        "mean_abs_diff": mean_abs_diff,
        "count_compared_values": count_compared,
        "count_nan_or_nodata_values": int(nan_or_nodata),
        "within_tolerance": within,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rasterio_available() -> bool:
    return importlib.util.find_spec("rasterio") is not None


def _overall_status(outputs: tuple[dict[str, Any], ...]) -> str:
    statuses = {item["status"] for item in outputs}
    if statuses == {"passed"}:
        overall_status = "passed"
    elif statuses <= {"comparison_unavailable"}:
        overall_status = "comparison_unavailable"
    elif "missing_app_output" in statuses or "missing_reference_output" in statuses:
        overall_status = "incomplete"
    else:
        overall_status = "failed"

    if overall_status not in ALLOWED_OVERALL_STATUSES:
        raise ValueError(f"unsupported AI_BEH relation overall status: {overall_status}")
    return overall_status
