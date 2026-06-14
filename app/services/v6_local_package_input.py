"""Local-only V6 package input builder.

This creates the private run-local input file consumed by the V6 package flow.
It is limited to loopback development mode and stores rows/geometry only under the
run's private directory; UI responses continue to expose metadata only.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

from app.config import Settings
from app.services.storage import get_run_dir
from app.services.v6_app_flow import V6_PRIVATE_INPUT_RELATIVE_PATH
from app.services.v6_real_gee_runtime import V6AoiBounds, V6GridCell, validate_v6_aoi_bounds
from app.services.v6_real_scoring import V6ScoredCandidate
from app.services.v6_real_zones import V6RequestZone, V6RequestZoneConfig, generate_v6_request_zones

_LOCAL_SCHEMA_VERSION = "v6_1_local_package_input_v1"
_MAX_LOCAL_CANDIDATES = 25
_POINT_BUFFER_DEGREES = 0.001


@dataclass(frozen=True)
class V6LocalPackageInputResult:
    created: bool
    path: Path | None
    reason: str
    safe_summary: dict[str, Any]


def ensure_local_v6_package_input(settings: Settings, run_id: str) -> V6LocalPackageInputResult:
    """Create the V6 private package input for local loopback runs when missing."""
    input_path = Path(get_run_dir(settings, run_id)) / V6_PRIVATE_INPUT_RELATIVE_PATH
    if input_path.is_file():
        return _result(False, input_path, "already_exists", run_id, 0, 0)
    if not _local_loopback_mode(settings):
        return _result(False, None, "not_local_loopback_mode", run_id, 0, 0)

    run_dir = Path(get_run_dir(settings, run_id))
    if not run_dir.is_dir():
        return _result(False, None, "run_dir_missing", run_id, 0, 0)

    aoi = _load_private_aoi(run_dir)
    if aoi is None:
        return _result(False, None, "aoi_source_missing", run_id, 0, 0)

    source_rows = _load_source_rows(run_dir)
    if not source_rows:
        return _result(False, None, "candidate_source_missing", run_id, 0, 0)

    candidates = _build_candidates(source_rows[:_MAX_LOCAL_CANDIDATES])
    grid_cells = _build_grid_cells_for_candidates(aoi=aoi, candidates=candidates)
    zones = generate_v6_request_zones(
        candidates,
        grid_cells,
        config=V6RequestZoneConfig(max_zones=len(candidates)),
    )
    _write_input_file(input_path=input_path, run_id=run_id, candidates=candidates, zones=zones)
    return _result(True, input_path, "created", run_id, len(candidates), len(zones))


def _local_loopback_mode(settings: Settings) -> bool:
    return bool(settings.v6_package_flow_enabled) and not settings.operator_auth_oidc_enabled and not settings.allow_network_bind


def _load_private_aoi(run_dir: Path) -> V6AoiBounds | None:
    preferred = run_dir / "full_job" / "location" / "site_location.geojson"
    paths = [preferred] if preferred.is_file() else []
    paths.extend(path for path in sorted(run_dir.rglob("*.geojson")) if path not in paths and "private" not in path.parts)
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            bounds = _bounds_from_geojson_payload(payload)
            if bounds is not None:
                return bounds
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return None


def _bounds_from_geojson_payload(payload: object) -> V6AoiBounds | None:
    numbers = list(_iter_geojson_positions(payload))
    if not numbers:
        return None
    xs = [item[0] for item in numbers]
    ys = [item[1] for item in numbers]
    west, east = min(xs), max(xs)
    south, north = min(ys), max(ys)
    if west == east:
        west -= _POINT_BUFFER_DEGREES
        east += _POINT_BUFFER_DEGREES
    if south == north:
        south -= _POINT_BUFFER_DEGREES
        north += _POINT_BUFFER_DEGREES
    return validate_v6_aoi_bounds(west=west, south=south, east=east, north=north)


def _iter_geojson_positions(value: object) -> Iterable[tuple[float, float]]:
    if isinstance(value, Mapping):
        if value.get("type") == "FeatureCollection":
            for feature in value.get("features", []) if isinstance(value.get("features"), list) else []:
                yield from _iter_geojson_positions(feature)
            return
        if value.get("type") == "Feature":
            yield from _iter_geojson_positions(value.get("geometry"))
            return
        if "coordinates" in value:
            yield from _iter_coordinate_tree(value.get("coordinates"))
            return
    if isinstance(value, list):
        for item in value:
            yield from _iter_geojson_positions(item)


def _iter_coordinate_tree(value: object) -> Iterable[tuple[float, float]]:
    if isinstance(value, (list, tuple)) and len(value) >= 2 and _is_finite_number(value[0]) and _is_finite_number(value[1]):
        yield (float(value[0]), float(value[1]))
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_coordinate_tree(item)


def _load_source_rows(run_dir: Path) -> list[dict[str, str]]:
    for relative in ("objects_index.csv", "clusters_summary.csv"):
        path = run_dir / relative
        if not path.is_file():
            continue
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = [dict(row) for row in csv.DictReader(handle)]
        except OSError:
            continue
        if rows:
            return rows
    return []


def _build_candidates(rows: list[Mapping[str, object]]) -> tuple[V6ScoredCandidate, ...]:
    scored_rows = [(_score_from_row(row, index), row) for index, row in enumerate(rows)]
    min_score = min(item[0] for item in scored_rows)
    max_score = max(item[0] for item in scored_rows)
    ranked = sorted(scored_rows, key=lambda item: (-item[0], _row_id(item[1])))
    candidates: list[V6ScoredCandidate] = []
    for rank, (raw_score, _row) in enumerate(ranked, start=1):
        score = _normalize_score(raw_score, min_score, max_score)
        cell_id = f"V6_CELL_R001_C{rank:03d}"
        candidates.append(
            V6ScoredCandidate(
                cell_id=cell_id,
                candidate_score=score,
                remote_sensing_contrast=score,
                s2_confidence=1.0,
                builtup_warning=0,
                cropland_heavy_warning=0,
                water_edge_warning=0,
                modern_linear_edge_warning=0,
                v6_building_warning=0,
                v6_road_like_warning=0,
                false_positive_warning_count=0,
                v6_false_positive_warning_count=0,
                v6_false_positive_penalty=0.0,
                v6_quality_adjusted_score=score,
                v6_no_warning_bonus=1.0,
                v6_review_priority_score=score,
                final_priority_rank_v6=rank,
            )
        )
    return tuple(candidates)


def _build_grid_cells_for_candidates(*, aoi: V6AoiBounds, candidates: tuple[V6ScoredCandidate, ...]) -> tuple[V6GridCell, ...]:
    count = max(len(candidates), 1)
    width = aoi.width_degrees / count
    cells: list[V6GridCell] = []
    for index, candidate in enumerate(candidates):
        west = aoi.west + (index * width)
        east = aoi.east if index == count - 1 else aoi.west + ((index + 1) * width)
        cells.append(
            V6GridCell(
                cell_id=candidate.cell_id,
                row=1,
                col=index + 1,
                bounds=V6AoiBounds(west=west, south=aoi.south, east=east, north=aoi.north),
            )
        )
    return tuple(cells)


def _write_input_file(
    *,
    input_path: Path,
    run_id: str,
    candidates: tuple[V6ScoredCandidate, ...],
    zones: tuple[V6RequestZone, ...],
) -> None:
    input_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": _LOCAL_SCHEMA_VERSION,
        "source_mode": "local_existing_run_outputs",
        "run_id": run_id,
        "timestamp": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "scored_candidates": [candidate.as_package_row() for candidate in candidates],
        "request_zones": [_zone_input_row(zone) for zone in zones],
    }
    input_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _zone_input_row(zone: V6RequestZone) -> dict[str, Any]:
    return {
        "request_zone_id": zone.request_zone_id,
        "source_cell_id": zone.source_cell_id,
        "quote_id": zone.quote_id,
        "final_priority_rank_v6": zone.final_priority_rank_v6,
        "v6_review_priority_score": zone.v6_review_priority_score,
        "v6_false_positive_warning_count": zone.v6_false_positive_warning_count,
        "bounds": {
            "west": zone.bounds.west,
            "south": zone.bounds.south,
            "east": zone.bounds.east,
            "north": zone.bounds.north,
        },
    }


def _score_from_row(row: Mapping[str, object], index: int) -> float:
    for key in (
        "v6_review_priority_score",
        "candidate_score",
        "score",
        "mean_score",
        "confidence",
        "area",
        "pixel_count",
    ):
        value = row.get(key)
        if _is_finite_number(value):
            return float(value)
    return float(len(row) - index)


def _normalize_score(value: float, min_score: float, max_score: float) -> float:
    if max_score == min_score:
        return 0.75
    return round(0.55 + (0.40 * ((value - min_score) / (max_score - min_score))), 6)


def _row_id(row: Mapping[str, object]) -> str:
    for key in ("object_id", "id", "cell_id", "cluster_id"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def _result(
    created: bool,
    path: Path | None,
    reason: str,
    run_id: str,
    candidate_count: int,
    zone_count: int,
) -> V6LocalPackageInputResult:
    return V6LocalPackageInputResult(
        created=created,
        path=path,
        reason=reason,
        safe_summary={
            "run_id": run_id,
            "created": created,
            "reason": reason,
            "candidate_count": candidate_count,
            "request_zone_count": zone_count,
            "contains_rows": False,
            "contains_geometry": False,
            "private_file_only": True,
        },
    )


__all__ = ("V6LocalPackageInputResult", "ensure_local_v6_package_input")
