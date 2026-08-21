from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any, Iterable

from pyproj import Transformer

from app.config import Settings
from app.pipeline.stages.depth_estimation import DEPTH_INPUT_RELATIVE_PATH, write_depth_outputs
from app.services.roi_contract import ROI_CONTRACT_RELATIVE_PATH
from app.services.storage import get_run_dir
from scripts.build_tyrone_local_depth_package import build_tyrone_local_depth_package

REFERENCE_RELATIVE_PATH = Path("data") / "depth_reference" / "tyrone_3x_six_plot_reference_v1_wgs84.geojson"
RUN_QUALITY_RELATIVE_PATH = Path("QA") / "run_quality" / "run_quality_summary.json"
WORK_ROOT_RELATIVE_PATH = Path("operator") / "tyrone_six_zone_depth"
PACKAGE_DIR_NAME = "package"
ROUTE_A_SOURCE = "tyrone_reviewed_six_zone_route_a_v2"
OUTSIDE_ZONE_ID = "outside_reviewed_tyrone_zones"
REVIEWED_PLOT_IDS = ("TP1", "TP2", "TP3", "TP5", "TP6", "TP7")
CLASSIFIER_ONLY_WARNING = "classifier_no_objects_classified"


class OperatorTyroneZoneDepthError(ValueError):
    """Raised when the reviewed six-zone Route A lookup cannot run safely."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise OperatorTyroneZoneDepthError(f"{label} is unavailable.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OperatorTyroneZoneDepthError(f"{label} is unreadable.") from exc
    if not isinstance(payload, dict):
        raise OperatorTyroneZoneDepthError(f"{label} is invalid.")
    return payload


def _iter_xy(coordinates: Any) -> Iterable[tuple[float, float]]:
    if isinstance(coordinates, (list, tuple)):
        if len(coordinates) >= 2 and all(
            isinstance(value, (int, float)) for value in coordinates[:2]
        ):
            yield float(coordinates[0]), float(coordinates[1])
            return
        for item in coordinates:
            yield from _iter_xy(item)


def _geometry_inside_run_bounds(
    geometry: dict[str, Any],
    *,
    transformer: Transformer,
    bounds: dict[str, Any],
) -> bool:
    if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
        return False
    points = list(_iter_xy(geometry.get("coordinates")))
    if not points:
        return False
    try:
        xmin = float(bounds["xmin"])
        ymin = float(bounds["ymin"])
        xmax = float(bounds["xmax"])
        ymax = float(bounds["ymax"])
    except (KeyError, TypeError, ValueError):
        return False
    for lon, lat in points:
        x, y = transformer.transform(lon, lat)
        if not (xmin <= x <= xmax and ymin <= y <= ymax):
            return False
    return True


def _reviewed_plot_ids_inside_run(run_dir: Path) -> list[str]:
    roi = _load_json_object(run_dir / ROI_CONTRACT_RELATIVE_PATH, label="Run footprint")
    grid = roi.get("grid")
    if not isinstance(grid, dict):
        raise OperatorTyroneZoneDepthError("Run footprint is invalid.")
    target_crs = str(grid.get("crs") or "").strip()
    bounds = grid.get("bounds_m")
    if not target_crs or not isinstance(bounds, dict):
        raise OperatorTyroneZoneDepthError("Run footprint is invalid.")

    reference = _load_json_object(
        _repo_root() / REFERENCE_RELATIVE_PATH,
        label="Reviewed Tyrone geometry",
    )
    raw_features = reference.get("features")
    if not isinstance(raw_features, list):
        raise OperatorTyroneZoneDepthError("Reviewed Tyrone geometry is invalid.")

    transformer = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
    matched: list[str] = []
    for raw_feature in raw_features:
        if not isinstance(raw_feature, dict):
            continue
        properties = raw_feature.get("properties")
        geometry = raw_feature.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            continue
        plot_id = str(properties.get("plot_id") or "").strip().upper()
        if plot_id not in REVIEWED_PLOT_IDS:
            continue
        if _geometry_inside_run_bounds(geometry, transformer=transformer, bounds=bounds):
            matched.append(plot_id)

    matched_set = set(matched)
    return [plot_id for plot_id in REVIEWED_PLOT_IDS if plot_id in matched_set]


def _classifier_only_warning_is_safe(run_dir: Path) -> bool:
    """Allow only the exact usable classifier-zero warning for Route A.

    Route A does not consume classifier output. An otherwise usable run may proceed
    when its sole warning is that the classifier produced zero objects. Every other
    warning stays subject to the normal depth-stage fail-closed quality gate.
    """

    payload = _load_json_object(run_dir / RUN_QUALITY_RELATIVE_PATH, label="Run quality")
    if str(payload.get("status") or "").strip().upper() != "WARNING":
        return False
    if not bool(payload.get("is_usable", False)):
        return False

    warnings = payload.get("warnings")
    if not isinstance(warnings, list) or set(map(str, warnings)) != {CLASSIFIER_ONLY_WARNING}:
        return False
    if payload.get("blocking_reasons") not in ([], None):
        return False
    if payload.get("unknowns") not in ([], None):
        return False

    checks = payload.get("checks")
    if not isinstance(checks, list) or not checks:
        return False

    classifier_seen = False
    for check in checks:
        if not isinstance(check, dict):
            return False
        name = str(check.get("name") or "").strip()
        status = str(check.get("status") or "").strip().upper()
        if name == "classifier":
            classifier_seen = True
            details = check.get("details")
            if status != "WARNING" or not isinstance(details, dict):
                return False
            try:
                object_count = int(details.get("object_count"))
            except (TypeError, ValueError):
                return False
            if object_count != 0:
                return False
            continue
        if status != "PASS":
            return False

    return classifier_seen


def _build_candidate_payload(run_dir: Path) -> tuple[dict[str, Any], int]:
    """Build reviewed Route A candidates without reading classifier outputs."""

    plot_ids = _reviewed_plot_ids_inside_run(run_dir)
    candidates = [
        {
            "candidate_id": f"reviewed-zone-{plot_id.lower()}",
            "zone_id": f"tyrone_{plot_id.lower()}",
        }
        for plot_id in plot_ids
    ]
    return {
        "schema_version": "local_depth_candidates_v1",
        "source": ROUTE_A_SOURCE,
        "candidates": candidates,
    }, len(plot_ids)


def _write_route_a_candidates(path: Path, payload: dict[str, Any]) -> None:
    if path.is_file():
        existing = _load_json_object(path, label="Existing depth candidate input")
        if existing.get("source") not in {
            ROUTE_A_SOURCE,
            "tyrone_reviewed_six_zone_route_a_v1",
        }:
            raise OperatorTyroneZoneDepthError(
                "This run already has a different local-depth candidate input."
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_depth_estimates(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise OperatorTyroneZoneDepthError("Route A depth estimates were not produced.")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "candidate_id": str(row.get("candidate_id") or ""),
                    "zone_id": str(row.get("zone_id") or ""),
                    "depth_status": str(row.get("depth_status") or ""),
                    "estimated_depth_min_m": _optional_float(row.get("estimated_depth_min_m")),
                    "estimated_depth_best_m": _optional_float(row.get("estimated_depth_best_m")),
                    "estimated_depth_max_m": _optional_float(row.get("estimated_depth_max_m")),
                    "depth_quality": str(row.get("depth_quality") or ""),
                    "warnings": [
                        value for value in str(row.get("warnings") or "").split("|") if value
                    ],
                }
            )
    return rows


def _optional_float(value: object) -> float | None:
    text = str(value or "").strip()
    return float(text) if text else None


def run_operator_tyrone_zone_depth_app(
    *,
    settings: Settings,
    run_id: str,
    operator_confirmed_review: bool = False,
) -> dict[str, Any]:
    """Run Route A using reviewed Tyrone-zone candidates inside the run footprint."""

    if not operator_confirmed_review:
        raise OperatorTyroneZoneDepthError(
            "Operator review confirmation is required before Route A depth processing."
        )
    run_dir = get_run_dir(settings, run_id)
    if not run_dir.is_dir():
        raise OperatorTyroneZoneDepthError("The selected completed run is unavailable.")

    allow_classifier_only_warning = _classifier_only_warning_is_safe(run_dir)

    work_root = run_dir / WORK_ROOT_RELATIVE_PATH
    package_dir = work_root / PACKAGE_DIR_NAME
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    build_tyrone_local_depth_package(
        package_dir,
        force=True,
        allow_run_quality_warning=allow_classifier_only_warning,
    )

    candidate_payload, spatial_match_count = _build_candidate_payload(run_dir)
    _write_route_a_candidates(run_dir / DEPTH_INPUT_RELATIVE_PATH, candidate_payload)
    paths, summary = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    estimates = _read_depth_estimates(paths.estimates_csv)

    service_warnings = [
        "local_only",
        "provisional_calibration",
        "derived_geometry",
        "not_transferable",
        "not_physical_confirmation",
    ]
    if allow_classifier_only_warning:
        service_warnings.append("classifier_only_warning_irrelevant_to_route_a")

    return {
        "outcome": "completed",
        "run_id": run_id,
        "status": summary["status"],
        "site_id": "tyrone_3x",
        "method_kind": summary["method_kind"],
        "method_version": summary["method_version"],
        "calibration_dataset_version": summary["calibration_dataset_version"],
        "validation_status": "provisional",
        "run_quality_status": summary["run_quality_status"],
        "candidate_count": summary["candidate_count"],
        "spatial_match_count": spatial_match_count,
        "estimated_count": summary["estimated_count"],
        "not_available_count": summary["not_available_count"],
        "insufficient_data_count": summary["insufficient_data_count"],
        "estimates": estimates,
        "warnings": sorted(set(service_warnings)),
        "classifier_used": False,
        "prediction": False,
        "interpolation": False,
        "extrapolation": False,
        "transferable": False,
        "geometry_returned": False,
        "filesystem_only": True,
        "http_servable": False,
    }


__all__ = (
    "CLASSIFIER_ONLY_WARNING",
    "OUTSIDE_ZONE_ID",
    "REVIEWED_PLOT_IDS",
    "ROUTE_A_SOURCE",
    "OperatorTyroneZoneDepthError",
    "_build_candidate_payload",
    "_classifier_only_warning_is_safe",
    "_geometry_inside_run_bounds",
    "_reviewed_plot_ids_inside_run",
    "run_operator_tyrone_zone_depth_app",
)
