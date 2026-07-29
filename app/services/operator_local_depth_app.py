from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from app.config import Settings
from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.operator_overlay_access_foundation import OPERATOR_ROLE
from app.services.operator_run_authorization import resolve_run_authorization
from app.services.storage import get_run_dir
from scripts.build_operator_local_depth_package import build_operator_local_depth_package
from scripts.extract_operator_depth_signals import extract_operator_depth_signals
from scripts.run_operator_local_depth_for_existing_run import run_operator_depth_for_existing_run

WORK_ROOT_RELATIVE_PATH = "operator/local_depth_app"
GEOJSON_NAME = "reviewed_zones.geojson"
EXTRACTION_DIR_NAME = "extraction"
PACKAGE_DIR_NAME = "package"
ESTIMATES_RELATIVE_PATH = Path("depth") / "depth_estimates.csv"


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
    method_version: str = "operator_local_depth_app_v1",
    input_crs: str = "EPSG:4326",
    erosion_pixels: int = 2,
    minimum_valid_pixels: int = 20,
    allow_run_quality_warning: bool = False,
    force: bool = False,
    operator_confirmed_review: bool = False,
) -> dict[str, Any]:
    """Run the merged private local-depth workflow for one completed run.

    The caller must complete authentication and per-run authorization before calling
    this function. The response deliberately excludes geometry and filesystem paths.
    """

    if not operator_confirmed_review:
        raise OperatorLocalDepthAppError(
            "Operator review confirmation is required before local depth processing."
        )
    if not isinstance(geojson, dict) or geojson.get("type") != "FeatureCollection":
        raise OperatorLocalDepthAppError("Reviewed zones must be a GeoJSON FeatureCollection.")
    features = geojson.get("features")
    if not isinstance(features, list) or not features:
        raise OperatorLocalDepthAppError("Reviewed zones must contain at least one feature.")
    if len(features) > 100:
        raise OperatorLocalDepthAppError("Reviewed zones cannot contain more than 100 features.")
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

    zones_path = work_root / GEOJSON_NAME
    extraction_dir = work_root / EXTRACTION_DIR_NAME
    package_dir = work_root / PACKAGE_DIR_NAME
    zones_path.write_text(
        json.dumps(geojson, separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8",
    )

    try:
        extraction = extract_operator_depth_signals(
            run_dir=run_dir,
            polygons_path=zones_path,
            output_dir=extraction_dir,
            site_id=str(site_id).strip(),
            method_version=str(method_version).strip(),
            calibration_dataset_version=str(calibration_dataset_version).strip(),
            input_crs=str(input_crs).strip(),
            erosion_pixels=erosion_pixels,
            minimum_valid_pixels=minimum_valid_pixels,
            allow_run_quality_warning=allow_run_quality_warning,
        )
        package = build_operator_local_depth_package(
            config_path=extraction_dir / "operator_depth_config.json",
            output_dir=package_dir,
        )
        execution = run_operator_depth_for_existing_run(
            run_dir=run_dir,
            package_dir=package_dir,
            candidate_input=extraction_dir / "operator_depth_candidates.json",
            force=force,
        )
        estimates = _read_redacted_estimates(run_dir / ESTIMATES_RELATIVE_PATH)
    except Exception:
        # Do not leave an incomplete calibration package or uploaded geometry after a
        # failed attempt. Existing depth outputs are protected by the downstream
        # command unless force was explicitly requested.
        shutil.rmtree(work_root, ignore_errors=True)
        raise

    return {
        "outcome": "completed",
        "run_id": run_id,
        "status": execution["status"],
        "site_id": package["site_id"],
        "method_kind": execution["method_kind"],
        "method_version": execution["method_version"],
        "calibration_dataset_version": execution["calibration_dataset_version"],
        "run_quality_status": execution["run_quality_status"],
        "anchor_count": extraction["anchor_count"],
        "candidate_count": execution["candidate_count"],
        "estimated_count": execution["estimated_count"],
        "insufficient_data_count": execution["insufficient_data_count"],
        "not_available_count": execution["not_available_count"],
        "estimates": estimates,
        "warnings": sorted(
            set(
                [
                    "local_calibration_only",
                    "not_transferable",
                    "not_global_model",
                    "operator_review_required",
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
    }


def build_denied_operator_local_depth_result(
    *,
    request_id: str,
    reason: str,
) -> OperatorLocalDepthAppResult:
    del reason  # All denial causes intentionally share one public response.
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
                    "estimated_depth_min_m": _optional_float(row.get("estimated_depth_min_m")),
                    "estimated_depth_best_m": _optional_float(row.get("estimated_depth_best_m")),
                    "estimated_depth_max_m": _optional_float(row.get("estimated_depth_max_m")),
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
    "run_operator_local_depth_app",
)
