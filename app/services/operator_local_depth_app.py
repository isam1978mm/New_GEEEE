from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import rasterio

from app.config import Settings
from app.pipeline.depth.interpolation import OPERATOR_CANDIDATES_SCHEMA
from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.operator_overlay_access_foundation import OPERATOR_ROLE
from app.services.operator_run_authorization import resolve_run_authorization
from app.services.storage import get_run_dir
from scripts.build_operator_local_depth_package import build_operator_local_depth_package
from scripts.extract_operator_depth_signals import extract_operator_depth_signals
from scripts.run_operator_local_depth_for_existing_run import run_operator_depth_for_existing_run

WORK_ROOT_RELATIVE_PATH = "operator/local_depth_app"
GEOJSON_NAME = "reviewed_anchors.geojson"
EXTRACTION_DIR_NAME = "extraction"
PACKAGE_DIR_NAME = "package"
RESULT_NAME = "finding_depth_results.json"
ESTIMATES_RELATIVE_PATH = Path("depth") / "depth_estimates.csv"
CANONICAL_RASTER_NAME = "logRatio_dB.tif"
CLASSIFIER_RELATIVE_PATHS = (
    Path("classifier") / "classifications.csv",
    Path("experimental") / "classifications.csv",
)
REQUIRED_FINDING_COLUMNS = (
    "object_id",
    "row_min",
    "row_max",
    "col_min",
    "col_max",
)


class OperatorLocalDepthAppError(ValueError):
    """Raised when the private operator local-depth workflow cannot run safely."""


@dataclass(frozen=True, slots=True)
class OperatorLocalDepthAccessDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class OperatorLocalDepthAppResult:
    status_code: int
    body: dict[str, Any]
    allowed: bool
    decision_reason: str


def evaluate_operator_local_depth_access(
    *,
    settings: Settings,
    run_id: str,
    actor_id: str | None,
    is_authenticated: bool,
    roles: Iterable[str],
) -> OperatorLocalDepthAccessDecision:
    """Evaluate access without reading or writing any run file."""

    if not settings.operator_local_depth_app_enabled:
        return OperatorLocalDepthAccessDecision(False, "local_depth_app_disabled")
    if not is_authenticated:
        return OperatorLocalDepthAccessDecision(False, "not_authenticated")
    if OPERATOR_ROLE not in set(roles):
        return OperatorLocalDepthAccessDecision(False, "operator_role_required")
    authorization = resolve_run_authorization(
        settings=settings,
        actor_id=actor_id,
        run_id=run_id,
    )
    if not authorization.allowed:
        return OperatorLocalDepthAccessDecision(False, authorization.reason)
    return OperatorLocalDepthAccessDecision(True, "authorized")


def run_operator_local_depth_app(
    *,
    settings: Settings,
    run_id: str,
    geojson: dict[str, Any],
    site_id: str,
    calibration_dataset_version: str,
    method_version: str = "operator_local_depth_app_v2",
    input_crs: str = "EPSG:4326",
    erosion_pixels: int = 2,
    minimum_valid_pixels: int = 20,
    allow_run_quality_warning: bool = False,
    force: bool = False,
    operator_confirmed_review: bool = False,
) -> dict[str, Any]:
    """Calibrate from measured anchors and estimate every classifier finding.

    The uploaded GeoJSON may contain measured anchor polygons only. Candidate
    signals are generated automatically from every classifier object in the
    completed run. The caller must complete authentication and per-run
    authorization before calling this function. The response deliberately
    excludes geometry and filesystem paths.
    """

    if not operator_confirmed_review:
        raise OperatorLocalDepthAppError(
            "Operator review confirmation is required before local depth processing."
        )
    anchor_count = _validate_anchor_collection(geojson)
    if not str(site_id).strip():
        raise OperatorLocalDepthAppError("Site ID is required.")
    if not str(calibration_dataset_version).strip():
        raise OperatorLocalDepthAppError("Calibration dataset version is required.")
    if not str(method_version).strip():
        raise OperatorLocalDepthAppError("Method version is required.")
    if not str(input_crs).strip():
        raise OperatorLocalDepthAppError("Input CRS is required.")
    if erosion_pixels < 0 or erosion_pixels > 10:
        raise OperatorLocalDepthAppError("Erosion pixels must be between 0 and 10.")
    if minimum_valid_pixels < 1 or minimum_valid_pixels > 100000:
        raise OperatorLocalDepthAppError(
            "Minimum valid pixels must be between 1 and 100000."
        )

    run_dir = get_run_dir(settings, run_id)
    if not run_dir.is_dir():
        raise OperatorLocalDepthAppError("The selected completed run is unavailable.")

    work_root = resolve_run_output_path(run_dir, WORK_ROOT_RELATIVE_PATH)
    if work_root.exists():
        if not force:
            raise OperatorLocalDepthAppError(
                "This run already has operator local-depth inputs. Select replacement to continue."
            )
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=False)

    anchors_path = work_root / GEOJSON_NAME
    extraction_dir = work_root / EXTRACTION_DIR_NAME
    package_dir = work_root / PACKAGE_DIR_NAME
    anchors_path.write_text(
        json.dumps(geojson, separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8",
    )

    try:
        extraction = extract_operator_depth_signals(
            run_dir=run_dir,
            polygons_path=anchors_path,
            output_dir=extraction_dir,
            site_id=str(site_id).strip(),
            method_version=str(method_version).strip(),
            calibration_dataset_version=str(calibration_dataset_version).strip(),
            input_crs=str(input_crs).strip(),
            erosion_pixels=erosion_pixels,
            minimum_valid_pixels=minimum_valid_pixels,
            allow_run_quality_warning=allow_run_quality_warning,
        )
        finding_candidates = _write_classifier_finding_candidates(
            run_dir=run_dir,
            output_path=extraction_dir / "operator_depth_candidates.json",
        )
        package = build_operator_local_depth_package(
            config_path=extraction_dir / "operator_depth_config.json",
            output_dir=package_dir,
        )

        execution: dict[str, Any]
        base_estimates: list[dict[str, Any]]
        if finding_candidates["supported_count"] > 0:
            execution = run_operator_depth_for_existing_run(
                run_dir=run_dir,
                package_dir=package_dir,
                candidate_input=extraction_dir / "operator_depth_candidates.json",
                force=force,
            )
            base_estimates = _read_redacted_estimates(
                run_dir / ESTIMATES_RELATIVE_PATH
            )
        else:
            execution = {
                "status": "insufficient_data",
                "method_kind": package["method_kind"],
                "method_version": package["method_version"],
                "calibration_dataset_version": package[
                    "calibration_dataset_version"
                ],
                "run_quality_status": extraction["run_quality_status"],
                "warnings": ["no_classifier_finding_has_valid_signal_pixels"],
            }
            base_estimates = []

        estimates = _merge_finding_estimates(
            candidate_ids=finding_candidates["candidate_ids"],
            unsupported_ids=set(finding_candidates["unsupported_ids"]),
            estimates=base_estimates,
        )
        counts = _count_estimate_statuses(estimates)
        result = {
            "outcome": "completed",
            "run_id": run_id,
            "status": _result_status(estimates),
            "site_id": package["site_id"],
            "method_kind": execution["method_kind"],
            "method_version": execution["method_version"],
            "calibration_dataset_version": execution[
                "calibration_dataset_version"
            ],
            "run_quality_status": execution["run_quality_status"],
            "anchor_count": anchor_count,
            "candidate_count": len(estimates),
            "estimated_count": counts["estimated_count"],
            "insufficient_data_count": counts["insufficient_data_count"],
            "not_available_count": counts["not_available_count"],
            "estimates": estimates,
            "warnings": sorted(
                set(
                    [
                        "local_calibration_only",
                        "not_transferable",
                        "not_global_model",
                        "operator_review_required_for_measured_anchors",
                        "classifier_findings_used_as_automatic_candidates",
                        *execution.get("warnings", []),
                    ]
                )
            ),
            "filesystem_only": True,
            "http_servable": False,
            "geometry_returned": False,
            "local_only": True,
            "transferable": False,
            "app_depth_enabled_by_default": False,
            "automatic_finding_candidates": True,
            "results_attached_to_findings": True,
        }
        (work_root / RESULT_NAME).write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except Exception:
        shutil.rmtree(work_root, ignore_errors=True)
        raise

    return result


def get_operator_local_depth_result(
    *,
    settings: Settings,
    run_id: str,
) -> dict[str, Any]:
    """Return the saved redacted per-finding result for one authorized run."""

    run_dir = get_run_dir(settings, run_id)
    if not run_dir.is_dir():
        return _not_available_result(run_id)
    result_path = resolve_run_output_path(
        run_dir,
        (Path(WORK_ROOT_RELATIVE_PATH) / RESULT_NAME).as_posix(),
    )
    if not result_path.is_file():
        return _not_available_result(run_id)
    try:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OperatorLocalDepthAppError(
            "Saved local depth results are unreadable."
        ) from exc
    if not isinstance(payload, dict):
        raise OperatorLocalDepthAppError("Saved local depth results are invalid.")
    return payload


def build_denied_operator_local_depth_result(
    *,
    request_id: str,
    reason: str,
) -> OperatorLocalDepthAppResult:
    del reason
    return OperatorLocalDepthAppResult(
        status_code=403,
        allowed=False,
        decision_reason="access_denied",
        body={
            "outcome": "denied",
            "status": "access_denied",
            "reason_code": "ACCESS_DENIED",
            "request_id": request_id,
            "message": "Access to the requested resource is not available.",
            "retry_allowed": False,
            "support_reference": "contact_operator_administrator",
        },
    )


def _validate_anchor_collection(geojson: dict[str, Any]) -> int:
    if not isinstance(geojson, dict) or geojson.get("type") != "FeatureCollection":
        raise OperatorLocalDepthAppError(
            "Measured anchors must be a GeoJSON FeatureCollection."
        )
    features = geojson.get("features")
    if not isinstance(features, list) or not features:
        raise OperatorLocalDepthAppError(
            "Measured anchors must contain at least two features."
        )
    if len(features) > 100:
        raise OperatorLocalDepthAppError(
            "Measured anchors cannot contain more than 100 features."
        )

    anchor_count = 0
    for index, feature in enumerate(features):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise OperatorLocalDepthAppError(
                f"Measured anchor {index + 1} is not a valid GeoJSON feature."
            )
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            raise OperatorLocalDepthAppError(
                f"Measured anchor {index + 1} must contain properties."
            )
        role = str(properties.get("role") or "").strip().lower()
        if role != "anchor":
            raise OperatorLocalDepthAppError(
                "Upload measured anchor polygons only. Finding candidates are generated automatically."
            )
        anchor_count += 1

    if anchor_count < 2:
        raise OperatorLocalDepthAppError(
            "At least two measured anchor polygons are required."
        )
    return anchor_count


def _write_classifier_finding_candidates(
    *,
    run_dir: Path,
    output_path: Path,
) -> dict[str, Any]:
    rows = _read_classifier_rows(run_dir)
    raster_path = run_dir / CANONICAL_RASTER_NAME
    if not raster_path.is_file():
        raise OperatorLocalDepthAppError(
            "The completed run has no canonical signal raster."
        )

    candidates: list[dict[str, Any]] = []
    candidate_ids: list[str] = []
    unsupported_ids: list[str] = []
    seen_ids: set[str] = set()

    with rasterio.open(raster_path) as source:
        if source.count != 1:
            raise OperatorLocalDepthAppError(
                "The canonical signal raster must contain one band."
            )
        raster = source.read(1).astype(np.float64, copy=False)
        valid = np.isfinite(raster)
        if source.nodata is not None:
            valid &= raster != source.nodata

        for row in rows:
            object_id = str(row.get("object_id") or "").strip()
            if not object_id:
                raise OperatorLocalDepthAppError(
                    "Classifier finding contains an empty object ID."
                )
            candidate_id = f"finding-object-{object_id}"
            if candidate_id in seen_ids:
                raise OperatorLocalDepthAppError(
                    f"Duplicate classifier finding object ID: {object_id}."
                )
            seen_ids.add(candidate_id)
            candidate_ids.append(candidate_id)

            row_min = _required_bound(row, "row_min")
            row_max = _required_bound(row, "row_max")
            col_min = _required_bound(row, "col_min")
            col_max = _required_bound(row, "col_max")
            if (
                row_min < 0
                or col_min < 0
                or row_max < row_min
                or col_max < col_min
                or row_max >= source.height
                or col_max >= source.width
            ):
                raise OperatorLocalDepthAppError(
                    f"Classifier finding bounds are invalid for object {object_id}."
                )

            window_values = raster[
                row_min : row_max + 1,
                col_min : col_max + 1,
            ]
            window_valid = valid[
                row_min : row_max + 1,
                col_min : col_max + 1,
            ]
            values = window_values[window_valid]
            if values.size == 0:
                unsupported_ids.append(candidate_id)
                continue

            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "signal_name": "run_logRatio_dB_mean",
                    "signal_value": float(values.mean()),
                    "signal_uncertainty": (
                        float(values.std(ddof=1)) if values.size > 1 else 0.0
                    ),
                }
            )

    output_path.write_text(
        json.dumps(
            {
                "schema_version": OPERATOR_CANDIDATES_SCHEMA,
                "candidates": candidates,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "candidate_ids": candidate_ids,
        "unsupported_ids": unsupported_ids,
        "supported_count": len(candidates),
        "candidate_count": len(candidate_ids),
    }


def _read_classifier_rows(run_dir: Path) -> list[dict[str, str]]:
    path = next(
        (
            run_dir / relative
            for relative in CLASSIFIER_RELATIVE_PATHS
            if (run_dir / relative).is_file()
        ),
        None,
    )
    if path is None:
        raise OperatorLocalDepthAppError(
            "The completed run has no classifier findings."
        )
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    if not rows:
        raise OperatorLocalDepthAppError(
            "The completed run has no classifier findings."
        )
    missing = [
        column
        for column in REQUIRED_FINDING_COLUMNS
        if column not in rows[0]
    ]
    if missing:
        raise OperatorLocalDepthAppError(
            "Classifier findings are missing required pixel bounds."
        )
    return rows


def _required_bound(row: dict[str, str], key: str) -> int:
    try:
        return int(str(row.get(key) or "").strip())
    except ValueError as exc:
        raise OperatorLocalDepthAppError(
            f"Classifier finding contains an invalid {key} value."
        ) from exc


def _merge_finding_estimates(
    *,
    candidate_ids: list[str],
    unsupported_ids: set[str],
    estimates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {
        str(estimate.get("candidate_id") or ""): estimate
        for estimate in estimates
    }
    merged: list[dict[str, Any]] = []
    for candidate_id in candidate_ids:
        estimate = by_id.get(candidate_id)
        if estimate is not None:
            merged.append(estimate)
            continue
        warning = (
            "finding_has_no_valid_signal_pixels"
            if candidate_id in unsupported_ids
            else "finding_depth_result_missing"
        )
        merged.append(
            {
                "candidate_id": candidate_id,
                "depth_status": "insufficient_data",
                "estimated_depth_min_m": None,
                "estimated_depth_best_m": None,
                "estimated_depth_max_m": None,
                "depth_quality": "",
                "warnings": [warning],
            }
        )
    return merged


def _count_estimate_statuses(
    estimates: list[dict[str, Any]],
) -> dict[str, int]:
    estimated_statuses = {"calibrated_range", "validated_range"}
    return {
        "estimated_count": sum(
            str(item.get("depth_status") or "") in estimated_statuses
            for item in estimates
        ),
        "insufficient_data_count": sum(
            str(item.get("depth_status") or "") == "insufficient_data"
            for item in estimates
        ),
        "not_available_count": sum(
            str(item.get("depth_status") or "") == "not_available"
            for item in estimates
        ),
    }


def _result_status(estimates: list[dict[str, Any]]) -> str:
    statuses = {
        str(item.get("depth_status") or "")
        for item in estimates
    }
    if "validated_range" in statuses:
        return "validated_range"
    if "calibrated_range" in statuses:
        return "calibrated_range"
    if statuses == {"not_available"}:
        return "not_available"
    return "insufficient_data"


def _not_available_result(run_id: str) -> dict[str, Any]:
    return {
        "outcome": "not_available",
        "run_id": run_id,
        "status": "not_available",
        "site_id": "",
        "method_kind": "",
        "method_version": "",
        "calibration_dataset_version": "",
        "run_quality_status": "",
        "anchor_count": 0,
        "candidate_count": 0,
        "estimated_count": 0,
        "insufficient_data_count": 0,
        "not_available_count": 0,
        "estimates": [],
        "warnings": ["local_depth_not_calibrated_for_run"],
        "filesystem_only": True,
        "http_servable": False,
        "geometry_returned": False,
        "local_only": True,
        "transferable": False,
        "app_depth_enabled_by_default": False,
        "automatic_finding_candidates": True,
        "results_attached_to_findings": True,
    }


def _read_redacted_estimates(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise OperatorLocalDepthAppError("Local depth estimates were not produced.")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "candidate_id": str(row.get("candidate_id") or ""),
                    "depth_status": str(row.get("depth_status") or ""),
                    "estimated_depth_min_m": _optional_float(
                        row.get("estimated_depth_min_m")
                    ),
                    "estimated_depth_best_m": _optional_float(
                        row.get("estimated_depth_best_m")
                    ),
                    "estimated_depth_max_m": _optional_float(
                        row.get("estimated_depth_max_m")
                    ),
                    "depth_quality": str(row.get("depth_quality") or ""),
                    "warnings": [
                        value
                        for value in str(row.get("warnings") or "").split("|")
                        if value
                    ],
                }
            )
    return rows


def _optional_float(value: object) -> float | None:
    text = str(value or "").strip()
    return float(text) if text else None


__all__ = (
    "OperatorLocalDepthAccessDecision",
    "OperatorLocalDepthAppError",
    "OperatorLocalDepthAppResult",
    "build_denied_operator_local_depth_result",
    "evaluate_operator_local_depth_access",
    "get_operator_local_depth_result",
    "run_operator_local_depth_app",
)
