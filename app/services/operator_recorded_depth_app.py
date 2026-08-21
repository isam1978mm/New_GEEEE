from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from pyproj import Transformer

from app.config import Settings
from app.pipeline.depth.recorded import (
    RECORDED_METHOD_KIND,
    RecordedDepthPackage,
    RecordedDepthPackageError,
    load_recorded_depth_package,
)
from app.services.operator_local_depth_app import OperatorLocalDepthAppError
from app.services.roi_contract import ROI_CONTRACT_RELATIVE_PATH
from app.services.storage import get_run_dir
from scripts.build_tyrone_recorded_depth_package import build_tyrone_recorded_depth_package

WORK_ROOT_RELATIVE_PATH = Path("operator") / "recorded_depth_app"
PACKAGE_DIR_NAME = "tyrone_recorded_package"
REFERENCE_RELATIVE_PATH = Path("data") / "depth_reference" / "tyrone_3x_six_plot_reference_v1_wgs84.geojson"
REVIEWED_PLOT_TO_ZONE = {"TP5": "tyrone_tp5", "TP6": "tyrone_tp6"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise OperatorLocalDepthAppError(f"{label} is unavailable.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OperatorLocalDepthAppError(f"{label} is unreadable.") from exc
    if not isinstance(payload, dict):
        raise OperatorLocalDepthAppError(f"{label} is invalid.")
    return payload


def _iter_xy(coordinates: Any) -> Iterable[tuple[float, float]]:
    if isinstance(coordinates, (list, tuple)):
        if len(coordinates) >= 2 and all(isinstance(value, (int, float)) for value in coordinates[:2]):
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
        raise OperatorLocalDepthAppError("Run footprint is invalid.")
    target_crs = str(grid.get("crs") or "").strip()
    bounds = grid.get("bounds_m")
    if not target_crs or not isinstance(bounds, dict):
        raise OperatorLocalDepthAppError("Run footprint is invalid.")

    reference = _load_json_object(_repo_root() / REFERENCE_RELATIVE_PATH, label="Reviewed Tyrone geometry")
    raw_features = reference.get("features")
    if not isinstance(raw_features, list):
        raise OperatorLocalDepthAppError("Reviewed Tyrone geometry is invalid.")

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
        if plot_id not in REVIEWED_PLOT_TO_ZONE:
            continue
        if _geometry_inside_run_bounds(geometry, transformer=transformer, bounds=bounds):
            matched.append(plot_id)
    return sorted(set(matched))


def _load_or_rebuild_recorded_package(package_dir: Path) -> RecordedDepthPackage:
    """Load the deterministic generated package, rebuilding one stale copy if needed.

    The package is generated entirely from reviewed repository constants. A stale or
    partially generated run-local copy is safe to replace. The rebuilt copy is always
    verified again, so a genuinely invalid generated package still fails closed.
    """

    package_dir = Path(package_dir)
    if not package_dir.is_dir():
        package_dir.mkdir(parents=True, exist_ok=True)
        build_tyrone_recorded_depth_package(package_dir)

    try:
        return load_recorded_depth_package(package_dir)
    except RecordedDepthPackageError:
        build_tyrone_recorded_depth_package(package_dir, force=True)
        return load_recorded_depth_package(package_dir)


def _measurement_payload(*, plot_id: str, zone: Any) -> dict[str, Any]:
    measurement = zone.measurement
    return {
        "plot_id": plot_id,
        "zone_id": zone.zone_id,
        "depth_status": "recorded_measurement",
        "recorded_depth_mean_m": measurement.mean_m,
        "recorded_depth_ci95_low_m": measurement.ci95_low_m,
        "recorded_depth_ci95_high_m": measurement.ci95_high_m,
        "recorded_sample_min_m": measurement.sample_min_m,
        "recorded_sample_max_m": measurement.sample_max_m,
        "recorded_sample_count": measurement.sample_count,
        "reported_design_depth_m": measurement.reported_design_depth_m,
        "measurement_source": measurement.measurement_source,
        "measurement_date": measurement.measurement_date,
        "measurement_method": measurement.measurement_method,
        "measurement_timing": measurement.measurement_timing,
        "depth_quality": "recorded_reviewed",
        "warnings": sorted(set(["recorded_measurement_only", "no_predictive_extrapolation", "reviewed_zone_only", *zone.warnings])),
    }


def run_operator_recorded_depth_app(
    *,
    settings: Settings,
    run_id: str,
    operator_confirmed_review: bool = False,
) -> dict[str, Any]:
    """Return official recorded measurements only for reviewed Tyrone plots inside a run footprint.

    This is a record lookup, not a prediction. It never converts run signals into metres and
    never assigns a Tyrone measurement to an unknown zone.
    """

    if not operator_confirmed_review:
        raise OperatorLocalDepthAppError("Operator review confirmation is required before recorded-depth lookup.")

    run_dir = get_run_dir(settings, run_id)
    if not run_dir.is_dir():
        raise OperatorLocalDepthAppError("The selected completed run is unavailable.")

    matched_plot_ids = _reviewed_plot_ids_inside_run(run_dir)
    work_root = run_dir / WORK_ROOT_RELATIVE_PATH
    package_dir = work_root / PACKAGE_DIR_NAME
    package = _load_or_rebuild_recorded_package(package_dir)

    records: list[dict[str, Any]] = []
    for plot_id in matched_plot_ids:
        zone_id = REVIEWED_PLOT_TO_ZONE[plot_id]
        zone = package.zone(zone_id)
        if zone is None:
            continue
        records.append(_measurement_payload(plot_id=plot_id, zone=zone))

    status = "recorded_measurement" if records else "not_available"
    warnings = list(package.warnings)
    if not records:
        warnings.extend(["no_reviewed_recorded_zone_in_run_footprint", "no_predictive_extrapolation"])

    return {
        "outcome": "completed",
        "run_id": run_id,
        "status": status,
        "site_id": package.site_id,
        "method_kind": RECORDED_METHOD_KIND,
        "method_version": package.method_version,
        "record_dataset_version": package.record_dataset_version,
        "review_status": package.review_status,
        "recorded_measurement_count": len(records),
        "records": records,
        "warnings": sorted(set(warnings)),
        "prediction": False,
        "interpolation": False,
        "extrapolation": False,
        "transferable": False,
        "geometry_returned": False,
        "filesystem_only": True,
        "http_servable": False,
    }


__all__ = (
    "REVIEWED_PLOT_TO_ZONE",
    "_geometry_inside_run_bounds",
    "_load_or_rebuild_recorded_package",
    "_reviewed_plot_ids_inside_run",
    "run_operator_recorded_depth_app",
)
