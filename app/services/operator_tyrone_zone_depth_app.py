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

CLASSIFICATIONS_RELATIVE_PATH = Path("classifier") / "classifications.csv"
REFERENCE_RELATIVE_PATH = Path("data") / "depth_reference" / "tyrone_3x_six_plot_reference_v1_wgs84.geojson"
WORK_ROOT_RELATIVE_PATH = Path("operator") / "tyrone_six_zone_depth"
PACKAGE_DIR_NAME = "package"
ROUTE_A_SOURCE = "tyrone_reviewed_six_zone_route_a_v1"
OUTSIDE_ZONE_ID = "outside_reviewed_tyrone_zones"
REVIEWED_PLOT_IDS = ("TP1", "TP2", "TP3", "TP5", "TP6", "TP7")


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


def _load_classifications(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise OperatorTyroneZoneDepthError("Classifier objects are unavailable for this run.")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"object_id", "row_min", "row_max", "col_min", "col_max"}
    if not rows:
        return []
    if not required.issubset(rows[0]):
        raise OperatorTyroneZoneDepthError("Classifier object geometry is unavailable for this run.")
    return rows


def _parse_int(row: dict[str, str], key: str) -> int:
    try:
        return int(str(row.get(key) or "").strip())
    except ValueError as exc:
        raise OperatorTyroneZoneDepthError("Classifier object geometry is invalid.") from exc


def _transform_xy(transform: list[float], *, col: float, row: float) -> tuple[float, float]:
    if len(transform) != 6:
        raise OperatorTyroneZoneDepthError("Run grid transform is invalid.")
    a, b, c, d, e, f = (float(value) for value in transform)
    return a * col + b * row + c, d * col + e * row + f


def _candidate_rectangle(row: dict[str, str], transform: list[float]) -> tuple[float, float, float, float]:
    row_min = _parse_int(row, "row_min")
    row_max = _parse_int(row, "row_max")
    col_min = _parse_int(row, "col_min")
    col_max = _parse_int(row, "col_max")
    if row_min < 0 or col_min < 0 or row_max < row_min or col_max < col_min:
        raise OperatorTyroneZoneDepthError("Classifier object geometry is invalid.")

    corners = [
        _transform_xy(transform, col=float(col_min), row=float(row_min)),
        _transform_xy(transform, col=float(col_max + 1), row=float(row_min)),
        _transform_xy(transform, col=float(col_max + 1), row=float(row_max + 1)),
        _transform_xy(transform, col=float(col_min), row=float(row_max + 1)),
    ]
    xs = [point[0] for point in corners]
    ys = [point[1] for point in corners]
    return min(xs), min(ys), max(xs), max(ys)


def _point_on_segment(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    tolerance: float = 1.0e-7,
) -> bool:
    px, py = point
    ax, ay = start
    bx, by = end
    cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax)
    if abs(cross) > tolerance:
        return False
    dot = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    if dot < -tolerance:
        return False
    length_sq = (bx - ax) ** 2 + (by - ay) ** 2
    return dot <= length_sq + tolerance


def _point_strictly_inside_ring(point: tuple[float, float], ring: list[tuple[float, float]]) -> bool:
    if len(ring) < 4:
        return False
    for start, end in zip(ring, ring[1:]):
        if _point_on_segment(point, start, end):
            return False

    x, y = point
    inside = False
    for start, end in zip(ring, ring[1:]):
        x1, y1 = start
        x2, y2 = end
        if (y1 > y) == (y2 > y):
            continue
        crossing_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
        if x < crossing_x:
            inside = not inside
    return inside


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    eps = 1.0e-7
    if ((o1 > eps and o2 < -eps) or (o1 < -eps and o2 > eps)) and (
        (o3 > eps and o4 < -eps) or (o3 < -eps and o4 > eps)
    ):
        return True
    if abs(o1) <= eps and _point_on_segment(c, a, b):
        return True
    if abs(o2) <= eps and _point_on_segment(d, a, b):
        return True
    if abs(o3) <= eps and _point_on_segment(a, c, d):
        return True
    if abs(o4) <= eps and _point_on_segment(b, c, d):
        return True
    return False


def _rectangle_fully_inside_ring(
    rectangle: tuple[float, float, float, float],
    ring: list[tuple[float, float]],
) -> bool:
    xmin, ymin, xmax, ymax = rectangle
    if xmax <= xmin or ymax <= ymin:
        return False
    corners = [
        (xmin, ymin),
        (xmax, ymin),
        (xmax, ymax),
        (xmin, ymax),
    ]
    # Boundary-touching candidates abstain. This keeps zone assignment conservative.
    if not all(_point_strictly_inside_ring(point, ring) for point in corners):
        return False

    # Reject concave-boundary intrusions through the rectangle.
    for x, y in ring[:-1]:
        if xmin < x < xmax and ymin < y < ymax:
            return False
    rectangle_edges = list(zip(corners, corners[1:] + corners[:1]))
    for start, end in zip(ring, ring[1:]):
        if any(_segments_intersect(start, end, edge_start, edge_end) for edge_start, edge_end in rectangle_edges):
            return False
    return True


def _load_reviewed_rings(*, target_crs: str) -> dict[str, list[tuple[float, float]]]:
    reference = _load_json_object(
        _repo_root() / REFERENCE_RELATIVE_PATH,
        label="Reviewed Tyrone geometry",
    )
    raw_features = reference.get("features")
    if not isinstance(raw_features, list):
        raise OperatorTyroneZoneDepthError("Reviewed Tyrone geometry is invalid.")
    transformer = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
    rings: dict[str, list[tuple[float, float]]] = {}
    for feature in raw_features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            continue
        plot_id = str(properties.get("plot_id") or "").strip().upper()
        if plot_id not in REVIEWED_PLOT_IDS or geometry.get("type") != "Polygon":
            continue
        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or not coordinates or not isinstance(coordinates[0], list):
            continue
        ring: list[tuple[float, float]] = []
        for point in coordinates[0]:
            if not isinstance(point, list | tuple) or len(point) < 2:
                continue
            x, y = transformer.transform(float(point[0]), float(point[1]))
            ring.append((float(x), float(y)))
        if ring and ring[0] != ring[-1]:
            ring.append(ring[0])
        if len(ring) >= 4:
            rings[plot_id] = ring
    if set(rings) != set(REVIEWED_PLOT_IDS):
        raise OperatorTyroneZoneDepthError("Reviewed Tyrone geometry is incomplete.")
    return rings


def _assign_zone(rectangle: tuple[float, float, float, float], rings: dict[str, list[tuple[float, float]]]) -> str:
    matches = [
        plot_id
        for plot_id in REVIEWED_PLOT_IDS
        if _rectangle_fully_inside_ring(rectangle, rings[plot_id])
    ]
    if len(matches) != 1:
        return OUTSIDE_ZONE_ID
    return f"tyrone_{matches[0].lower()}"


def _build_candidate_payload(run_dir: Path) -> tuple[dict[str, Any], int]:
    roi = _load_json_object(run_dir / ROI_CONTRACT_RELATIVE_PATH, label="Run grid")
    grid = roi.get("grid")
    if not isinstance(grid, dict):
        raise OperatorTyroneZoneDepthError("Run grid is invalid.")
    target_crs = str(grid.get("crs") or "").strip()
    raw_transform = grid.get("crs_transform")
    if not target_crs or not isinstance(raw_transform, list) or len(raw_transform) != 6:
        raise OperatorTyroneZoneDepthError("Run grid is invalid.")
    transform = [float(value) for value in raw_transform]
    rings = _load_reviewed_rings(target_crs=target_crs)
    rows = _load_classifications(run_dir / CLASSIFICATIONS_RELATIVE_PATH)

    candidates: list[dict[str, str]] = []
    matched_count = 0
    for row in rows:
        object_id = str(_parse_int(row, "object_id"))
        rectangle = _candidate_rectangle(row, transform)
        zone_id = _assign_zone(rectangle, rings)
        if zone_id != OUTSIDE_ZONE_ID:
            matched_count += 1
        candidates.append({"candidate_id": f"object-{object_id}", "zone_id": zone_id})
    return {
        "schema_version": "local_depth_candidates_v1",
        "source": ROUTE_A_SOURCE,
        "candidates": candidates,
    }, matched_count


def _write_route_a_candidates(path: Path, payload: dict[str, Any]) -> None:
    if path.is_file():
        existing = _load_json_object(path, label="Existing depth candidate input")
        if existing.get("source") != ROUTE_A_SOURCE:
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
    """Run original Route A on classifier objects using six reviewed Tyrone zones."""

    if not operator_confirmed_review:
        raise OperatorTyroneZoneDepthError(
            "Operator review confirmation is required before Route A depth processing."
        )
    run_dir = get_run_dir(settings, run_id)
    if not run_dir.is_dir():
        raise OperatorTyroneZoneDepthError("The selected completed run is unavailable.")

    work_root = run_dir / WORK_ROOT_RELATIVE_PATH
    package_dir = work_root / PACKAGE_DIR_NAME
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    build_tyrone_local_depth_package(package_dir, force=True)

    candidate_payload, spatial_match_count = _build_candidate_payload(run_dir)
    _write_route_a_candidates(run_dir / DEPTH_INPUT_RELATIVE_PATH, candidate_payload)
    paths, summary = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    estimates = _read_depth_estimates(paths.estimates_csv)

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
        "warnings": sorted(
            set(
                [
                    "local_only",
                    "provisional_calibration",
                    "derived_geometry",
                    "not_transferable",
                    "not_physical_confirmation",
                    *summary.get("warnings", []),
                ]
            )
        ),
        "filesystem_only": True,
        "http_servable": False,
        "geometry_returned": False,
        "transferable": False,
        "validated": False,
    }


__all__ = (
    "OUTSIDE_ZONE_ID",
    "REVIEWED_PLOT_IDS",
    "ROUTE_A_SOURCE",
    "OperatorTyroneZoneDepthError",
    "_assign_zone",
    "_candidate_rectangle",
    "_rectangle_fully_inside_ring",
    "run_operator_tyrone_zone_depth_app",
)
