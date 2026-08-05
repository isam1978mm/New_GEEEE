#!/usr/bin/env python3
"""Discovery-only spatial matcher for Tyrone Route B.

Finds possible geometric correspondences between seven monitoring-well markers
read from the official 2020 Tyrone map and Tyrone-owned NMOSE points. Results are
hypotheses only: they do not unlock geometry or numerical depth.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from pyproj import Transformer

OWNER_TOKENS = ("phelps", "freeport", "tyrone")
OUTPUT_NAME = "tyrone_ose_spatial_pattern_hypotheses.json"


@dataclass(frozen=True)
class MapPoint:
    point_id: str
    x: float
    y: float


@dataclass(frozen=True)
class CandidatePoint:
    index: int
    longitude: float
    latitude: float
    easting_m: float
    northing_m: float
    attributes: dict[str, Any]


def load_map_points(path: Path) -> tuple[list[MapPoint], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = payload.get("points")
    if not isinstance(rows, list):
        raise ValueError("map-point JSON must contain a points list")
    points = [MapPoint(str(row["id"]), float(row["x"]), float(row["y"])) for row in rows]
    if len(points) < 4:
        raise ValueError("at least four map points are required")
    if len({point.point_id for point in points}) != len(points):
        raise ValueError("map-point IDs must be unique")
    return points, payload


def _owner_text(row: dict[str, Any]) -> str:
    fields = ("own_lname", "own_fname", "other_loc", "pod_name", "pod_file", "well_tag")
    return " | ".join(str(row.get(field) or "") for field in fields).lower()


def filter_and_project_candidates(
    rows: list[dict[str, Any]], target_epsg: int = 32612
) -> list[CandidatePoint]:
    usable: list[tuple[dict[str, Any], float, float]] = []
    for row in rows:
        try:
            lon = float(row.get("longitude"))
            lat = float(row.get("latitude"))
        except (TypeError, ValueError):
            continue
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            continue
        if not any(token in _owner_text(row) for token in OWNER_TOKENS):
            continue
        usable.append((row, lon, lat))
    if not usable:
        return []

    transformer = Transformer.from_crs(4326, target_epsg, always_xy=True)
    eastings, northings = transformer.transform(
        [item[1] for item in usable], [item[2] for item in usable]
    )

    # Collapse duplicate rights/records at essentially the same mapped point.
    dedup: dict[tuple[int, int], tuple[float, dict[str, Any], float, float, float, float]] = {}
    for (row, lon, lat), easting, northing in zip(usable, eastings, northings, strict=True):
        key = (round(float(easting) / 2.0), round(float(northing) / 2.0))
        score = float(row.get("priority_score") or 0)
        previous = dedup.get(key)
        if previous is None or score > previous[0]:
            dedup[key] = (score, row, lon, lat, float(easting), float(northing))

    candidates: list[CandidatePoint] = []
    for index, (_, row, lon, lat, easting, northing) in enumerate(dedup.values()):
        candidates.append(
            CandidatePoint(index, lon, lat, easting, northing, row)
        )
    return candidates


def _spatial_hash(candidates: list[CandidatePoint], cell_m: float) -> dict[tuple[int, int], list[int]]:
    result: dict[tuple[int, int], list[int]] = {}
    for candidate in candidates:
        key = (
            math.floor(candidate.easting_m / cell_m),
            math.floor(candidate.northing_m / cell_m),
        )
        result.setdefault(key, []).append(candidate.index)
    return result


def _nearby(
    index: dict[tuple[int, int], list[int]], x: float, y: float, cell_m: float
) -> list[int]:
    gx, gy = math.floor(x / cell_m), math.floor(y / cell_m)
    found: list[int] = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            found.extend(index.get((gx + dx, gy + dy), ()))
    return found


def _transform(
    source: np.ndarray,
    map_a: int,
    map_b: int,
    candidate_a: CandidatePoint,
    candidate_b: CandidatePoint,
    reflected: bool,
) -> tuple[np.ndarray, complex]:
    z = source[:, 0] + 1j * source[:, 1]
    z = np.conj(z) if reflected else z
    target_a = candidate_a.easting_m + 1j * candidate_a.northing_m
    target_b = candidate_b.easting_m + 1j * candidate_b.northing_m
    alpha = (target_b - target_a) / (z[map_b] - z[map_a])
    beta = target_a - alpha * z[map_a]
    transformed = alpha * z + beta
    return np.column_stack((transformed.real, transformed.imag)), alpha


def _assign(
    transformed: np.ndarray,
    candidates: list[CandidatePoint],
    spatial_index: dict[tuple[int, int], list[int]],
    tolerance_m: float,
    anchors: dict[int, int],
) -> tuple[dict[int, int], dict[int, float]]:
    matches = dict(anchors)
    residuals = {index: 0.0 for index in anchors}
    used = set(anchors.values())
    for map_index, (x, y) in enumerate(transformed):
        if map_index in anchors:
            continue
        best: tuple[float, int] | None = None
        for candidate_index in _nearby(spatial_index, float(x), float(y), tolerance_m):
            if candidate_index in used:
                continue
            candidate = candidates[candidate_index]
            distance = math.hypot(candidate.easting_m - x, candidate.northing_m - y)
            if distance <= tolerance_m and (best is None or distance < best[0]):
                best = (distance, candidate_index)
        if best:
            residuals[map_index], matches[map_index] = best
            used.add(best[1])
    return matches, residuals


def find_hypotheses(
    map_points: list[MapPoint],
    candidates: list[CandidatePoint],
    tolerance_m: float = 120.0,
    minimum_matches: int = 6,
    max_anchor_pairs: int = 8,
    max_hypotheses: int = 25,
) -> list[dict[str, Any]]:
    if len(candidates) < minimum_matches:
        return []
    # Image y grows downward; negate it before considering rotation/reflection.
    source = np.array([[point.x, -point.y] for point in map_points], dtype=float)
    map_pairs: list[tuple[float, int, int]] = []
    for first in range(len(map_points)):
        for second in range(first + 1, len(map_points)):
            map_pairs.append((float(np.linalg.norm(source[second] - source[first])), first, second))
    map_pairs.sort(reverse=True)
    spatial_index = _spatial_hash(candidates, tolerance_m)
    unique: dict[tuple[tuple[int, ...], bool], dict[str, Any]] = {}

    for map_distance, map_a, map_b in map_pairs[:max_anchor_pairs]:
        for candidate_a in candidates:
            for candidate_b in candidates:
                if candidate_a.index == candidate_b.index:
                    continue
                target_distance = math.hypot(
                    candidate_b.easting_m - candidate_a.easting_m,
                    candidate_b.northing_m - candidate_a.northing_m,
                )
                scale = target_distance / map_distance
                if not 0.5 <= scale <= 30.0:
                    continue
                for reflected in (False, True):
                    transformed, alpha = _transform(
                        source, map_a, map_b, candidate_a, candidate_b, reflected
                    )
                    matches, residuals = _assign(
                        transformed,
                        candidates,
                        spatial_index,
                        tolerance_m,
                        {map_a: candidate_a.index, map_b: candidate_b.index},
                    )
                    if len(matches) < minimum_matches:
                        continue
                    assignment = tuple(matches.get(index, -1) for index in range(len(map_points)))
                    non_anchor = [
                        value for index, value in residuals.items() if index not in (map_a, map_b)
                    ]
                    ranking = (
                        -len(matches),
                        float(np.median(non_anchor)) if non_anchor else 0.0,
                        max(non_anchor) if non_anchor else 0.0,
                    )
                    key = (assignment, reflected)
                    if key not in unique or ranking < unique[key]["ranking"]:
                        unique[key] = {
                            "ranking": ranking,
                            "matches": matches,
                            "residuals": residuals,
                            "transformed": transformed,
                            "anchors": (map_a, map_b),
                            "reflected": reflected,
                            "scale_m_per_pixel": abs(alpha),
                        }
    hypotheses = sorted(unique.values(), key=lambda item: item["ranking"])
    return hypotheses[:max_hypotheses]


def _serialize(
    hypothesis: dict[str, Any], map_points: list[MapPoint], candidates: list[CandidatePoint]
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for map_index, point in enumerate(map_points):
        candidate_index = hypothesis["matches"].get(map_index)
        predicted = hypothesis["transformed"][map_index]
        row: dict[str, Any] = {
            "map_point_id": point.point_id,
            "predicted_easting_m": float(predicted[0]),
            "predicted_northing_m": float(predicted[1]),
            "matched": candidate_index is not None,
        }
        if candidate_index is not None:
            candidate = candidates[candidate_index]
            attrs = candidate.attributes
            row.update(
                {
                    "residual_m": float(hypothesis["residuals"][map_index]),
                    "candidate_OBJECTID": attrs.get("OBJECTID"),
                    "candidate_longitude": candidate.longitude,
                    "candidate_latitude": candidate.latitude,
                    "candidate_pod_file": attrs.get("pod_file"),
                    "candidate_well_tag": attrs.get("well_tag"),
                    "candidate_owner": attrs.get("own_lname"),
                    "candidate_utm_accuracy": attrs.get("utm_accura"),
                    "candidate_xy_accuracy": attrs.get("xy_accurac"),
                }
            )
        rows.append(row)
    anchors = set(hypothesis["anchors"])
    checked = [value for index, value in hypothesis["residuals"].items() if index not in anchors]
    return {
        "matched_count": len(hypothesis["matches"]),
        "discovery_median_residual_m": float(np.median(checked)) if checked else 0.0,
        "discovery_max_residual_m": max(checked) if checked else 0.0,
        "scale_m_per_pixel": hypothesis["scale_m_per_pixel"],
        "reflected": hypothesis["reflected"],
        "anchor_map_points": [map_points[index].point_id for index in hypothesis["anchors"]],
        "matches": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates-json", type=Path, required=True)
    parser.add_argument("--map-points-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--discovery-tolerance-m", type=float, default=120.0)
    parser.add_argument("--minimum-matches", type=int, default=6)
    parser.add_argument("--max-candidates", type=int, default=500)
    args = parser.parse_args()

    try:
        if args.discovery_tolerance_m <= 0 or args.minimum_matches < 4:
            raise ValueError("invalid discovery thresholds")
        payload = json.loads(args.candidates_json.read_text(encoding="utf-8-sig"))
        rows = payload.get("candidates")
        if not isinstance(rows, list):
            raise ValueError("candidate JSON lacks candidates list")
        map_points, map_config = load_map_points(args.map_points_json)
        candidates = filter_and_project_candidates(rows)
        candidates.sort(key=lambda item: -float(item.attributes.get("priority_score") or 0))
        candidates = candidates[: args.max_candidates]
        candidates = [
            CandidatePoint(index, item.longitude, item.latitude, item.easting_m, item.northing_m, item.attributes)
            for index, item in enumerate(candidates)
        ]
        hypotheses = find_hypotheses(
            map_points,
            candidates,
            tolerance_m=args.discovery_tolerance_m,
            minimum_matches=args.minimum_matches,
        )
        serialized = [_serialize(item, map_points, candidates) for item in hypotheses]
        status = "candidate_spatial_patterns_found" if serialized else "no_required_spatial_pattern_found"
        report = {
            "schema": "tyrone_ose_spatial_pattern_hypotheses_v1",
            "status": status,
            "map_config": map_config,
            "filtered_deduplicated_candidate_count": len(candidates),
            "discovery_tolerance_m": args.discovery_tolerance_m,
            "minimum_matches": args.minimum_matches,
            "hypothesis_count": len(serialized),
            "hypotheses": serialized,
            "warning": "Discovery hypotheses are not verified well matches.",
            "coordinate_geometry_unblocked": False,
            "numerical_depth_unlocked": False,
        }
        args.output_dir.mkdir(parents=True, exist_ok=True)
        output = args.output_dir / OUTPUT_NAME
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({
            "status": "spatial_pattern_match_failed",
            "error": str(exc),
            "coordinate_geometry_unblocked": False,
            "numerical_depth_unlocked": False,
        }, indent=2), file=sys.stderr)
        return 1

    summary: dict[str, Any] = {
        "status": status,
        "filtered_deduplicated_candidate_count": len(candidates),
        "hypothesis_count": len(serialized),
        "best_matched_count": serialized[0]["matched_count"] if serialized else 0,
        "json": str(output.resolve()),
        "coordinate_geometry_unblocked": False,
        "numerical_depth_unlocked": False,
    }
    if serialized:
        summary["best_discovery_median_residual_m"] = serialized[0]["discovery_median_residual_m"]
        summary["best_discovery_max_residual_m"] = serialized[0]["discovery_max_residual_m"]
        summary["best_map_point_matches"] = [
            {
                "map_point_id": row["map_point_id"],
                "candidate_OBJECTID": row.get("candidate_OBJECTID"),
                "residual_m": row.get("residual_m"),
            }
            for row in serialized[0]["matches"] if row["matched"]
        ]
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
