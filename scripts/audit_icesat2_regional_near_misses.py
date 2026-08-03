"""Audit isolated ICESat-2 regional step candidates without lowering gates.

The strict regional expansion keeps only at least three neighbouring ATL08
terrain segments with one event window and consistent step magnitude.  This
read-only follow-up re-queries only geographies that produced raw upward-step
segments but no surviving cluster.  It explains whether those steps were:

- genuinely isolated even at wider diagnostic distances;
- spatially close but split across event windows or detector spots; or
- a coherent near-miss for which the 250 m neighbour radius was the binding
  screen.

The audit does not change any production threshold, research records, create a
depth anchor, invoke the radar depth engine, or modify app artifacts.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.pipeline.elevation_change.icesat2_repeat import Icesat2Segment
from app.pipeline.elevation_change.icesat2_step_scan import (
    SegmentStepAssessment,
    nmad,
    scan_segment_series,
)
from audit_icesat2_repeat_points import (
    DEFAULT_END,
    DEFAULT_START,
    _load_manifest,
    _query_atl08,
    _segments_from_frame,
)
from scan_all_icesat2_terrain_steps import discover_completed_runs
from scan_icesat2_regional_expansion import (
    DEFAULT_OUTPUT_DIRNAME,
    GeographySeed,
    build_query_tiles,
    deduplicate_geographies,
    deduplicate_segments,
)

SCHEMA = "icesat2_regional_near_miss_audit_v1"
DEFAULT_OUTPUT_DIRNAME = "icesat2_regional_near_miss_audit"
DEFAULT_SUMMARY_FILENAME = "icesat2_regional_near_miss_summary.json"
DEFAULT_REGIONAL_SUMMARY_FILENAME = "icesat2_regional_expansion_summary.json"


def _distance_m(
    first: SegmentStepAssessment,
    second: SegmentStepAssessment,
) -> float:
    return float(math.hypot(first.x_m - second.x_m, first.y_m - second.y_m))


def _event_key(item: SegmentStepAssessment) -> tuple[int, int, int, int]:
    if item.pre_cycle is None or item.post_cycle is None:
        raise ValueError("step candidate is missing an event cycle")
    return item.rgt, item.spot, item.pre_cycle, item.post_cycle


def _cross_spot_event_key(item: SegmentStepAssessment) -> tuple[int, int, int]:
    if item.pre_cycle is None or item.post_cycle is None:
        raise ValueError("step candidate is missing an event cycle")
    return item.rgt, item.pre_cycle, item.post_cycle


def _connected_components(
    items: Sequence[SegmentStepAssessment],
    *,
    distance_m: float,
) -> list[list[SegmentStepAssessment]]:
    if distance_m <= 0:
        raise ValueError("distance_m must be positive")
    remaining = set(range(len(items)))
    components: list[list[SegmentStepAssessment]] = []
    distance_sq = float(distance_m) ** 2
    while remaining:
        seed = remaining.pop()
        component = {seed}
        frontier = [seed]
        while frontier:
            current = frontier.pop()
            current_item = items[current]
            neighbours: list[int] = []
            for candidate in list(remaining):
                other = items[candidate]
                dx = current_item.x_m - other.x_m
                dy = current_item.y_m - other.y_m
                if dx * dx + dy * dy <= distance_sq:
                    neighbours.append(candidate)
            for candidate in neighbours:
                remaining.remove(candidate)
                component.add(candidate)
                frontier.append(candidate)
        components.append([items[index] for index in sorted(component)])
    components.sort(key=lambda component: (-len(component), component[0].segment_id))
    return components


def _component_mapping(
    component: Sequence[SegmentStepAssessment],
    *,
    radius_m: float,
    maximum_step_nmad_m: float,
    minimum_segments: int,
) -> dict[str, object]:
    steps = [float(item.step_m) for item in component if item.step_m is not None]
    spread = float(nmad(steps) or 0.0)
    return {
        "radius_m": float(radius_m),
        "segment_count": len(component),
        "segment_ids": [item.segment_id for item in component],
        "median_step_m": float(sorted(steps)[len(steps) // 2]) if steps else None,
        "step_nmad_m": spread if steps else None,
        "enough_segments": len(component) >= int(minimum_segments),
        "step_spread_supported": bool(steps) and spread <= maximum_step_nmad_m,
        "would_pass_at_this_radius": (
            len(component) >= int(minimum_segments)
            and bool(steps)
            and spread <= maximum_step_nmad_m
        ),
    }


def diagnose_event_groups(
    candidates: Sequence[SegmentStepAssessment],
    *,
    strict_radius_m: float = 250.0,
    diagnostic_radii_m: Sequence[float] = (500.0, 1000.0),
    minimum_segments: int = 3,
    maximum_step_nmad_m: float = 0.25,
) -> list[dict[str, object]]:
    grouped: dict[tuple[int, int, int, int], list[SegmentStepAssessment]] = defaultdict(list)
    for item in candidates:
        grouped[_event_key(item)].append(item)

    groups: list[dict[str, object]] = []
    radii = [float(strict_radius_m)] + [
        float(value) for value in diagnostic_radii_m if float(value) != float(strict_radius_m)
    ]
    for key, items in sorted(grouped.items()):
        rgt, spot, pre_cycle, post_cycle = key
        radius_results: list[dict[str, object]] = []
        for radius in radii:
            components = _connected_components(items, distance_m=radius)
            mapped = [
                _component_mapping(
                    component,
                    radius_m=radius,
                    maximum_step_nmad_m=maximum_step_nmad_m,
                    minimum_segments=minimum_segments,
                )
                for component in components
            ]
            radius_results.append(
                {
                    "radius_m": radius,
                    "component_count": len(mapped),
                    "largest_component_size": max(
                        (int(item["segment_count"]) for item in mapped),
                        default=0,
                    ),
                    "passing_component_count": sum(
                        bool(item["would_pass_at_this_radius"]) for item in mapped
                    ),
                    "components": mapped,
                }
            )

        strict_pass = bool(radius_results and radius_results[0]["passing_component_count"])
        wider_pass = any(
            int(item["passing_component_count"]) > 0 for item in radius_results[1:]
        )
        if strict_pass:
            diagnosis = "unexpected_strict_pass"
        elif wider_pass:
            diagnosis = "strict_neighbor_radius_was_binding"
        elif len(items) >= minimum_segments:
            diagnosis = "event_peers_exist_but_remain_disconnected_or_inconsistent"
        elif len(items) == 2:
            diagnosis = "only_two_same_event_segments"
        else:
            diagnosis = "single_same_event_segment"

        groups.append(
            {
                "rgt": rgt,
                "spot": spot,
                "pre_cycle": pre_cycle,
                "post_cycle": post_cycle,
                "candidate_count": len(items),
                "diagnosis": diagnosis,
                "radius_diagnostics": radius_results,
            }
        )

    groups.sort(
        key=lambda item: (
            item["diagnosis"] != "strict_neighbor_radius_was_binding",
            -int(item["candidate_count"]),
            int(item["rgt"]),
            int(item["spot"]),
            int(item["pre_cycle"]),
            int(item["post_cycle"]),
        )
    )
    return groups


def _assessment_mapping(
    item: SegmentStepAssessment,
    candidates: Sequence[SegmentStepAssessment],
    *,
    cross_spot_distance_m: float,
) -> dict[str, object]:
    same_event = [
        other
        for other in candidates
        if other is not item and _event_key(other) == _event_key(item)
    ]
    same_event_any_spot = [
        other
        for other in candidates
        if other is not item
        and _cross_spot_event_key(other) == _cross_spot_event_key(item)
    ]
    any_other = [other for other in candidates if other is not item]

    nearest_same = min((_distance_m(item, other) for other in same_event), default=None)
    nearest_event_any_spot = min(
        (_distance_m(item, other) for other in same_event_any_spot),
        default=None,
    )
    nearest_any = min((_distance_m(item, other) for other in any_other), default=None)
    cross_spot = [
        {
            "spot": other.spot,
            "segment_id": other.segment_id,
            "distance_m": _distance_m(item, other),
            "step_m": other.step_m,
        }
        for other in same_event_any_spot
        if other.spot != item.spot
        and _distance_m(item, other) <= cross_spot_distance_m
    ]
    cross_spot.sort(key=lambda value: (float(value["distance_m"]), int(value["spot"])))

    return {
        "rgt": item.rgt,
        "spot": item.spot,
        "segment_id": item.segment_id,
        "longitude": item.longitude,
        "latitude": item.latitude,
        "pre_cycle": item.pre_cycle,
        "post_cycle": item.post_cycle,
        "event_start": item.event_start.isoformat() if item.event_start else None,
        "event_end": item.event_end.isoformat() if item.event_end else None,
        "step_m": item.step_m,
        "pre_nmad_m": item.pre_nmad_m,
        "post_nmad_m": item.post_nmad_m,
        "residual_nmad_m": item.residual_nmad_m,
        "dominant_increment_ratio": item.dominant_increment_ratio,
        "score": item.score,
        "nearest_same_event_same_spot_m": nearest_same,
        "nearest_same_event_any_spot_m": nearest_event_any_spot,
        "nearest_any_step_candidate_m": nearest_any,
        "cross_spot_supported_within_m": bool(cross_spot),
        "cross_spot_support": cross_spot,
        "timeline": [
            {
                "cycle": observation.cycle,
                "observed_at": observation.observed_at.isoformat(),
                "height_m": observation.height_m,
                "height_uncertainty_m": observation.height_uncertainty_m,
                "ground_photon_count": observation.ground_photon_count,
            }
            for observation in item.observations
        ],
    }


def _selected_geography_ids(summary: dict[str, object]) -> list[str]:
    rows = summary.get("geography_summaries", [])
    if not isinstance(rows, list):
        return []
    selected: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_count = row.get("raw_step_up_segment_count")
        cluster_count = row.get("surviving_step_cluster_count")
        geography_id = row.get("geography_id")
        if (
            isinstance(geography_id, str)
            and isinstance(raw_count, int)
            and raw_count > 0
            and int(cluster_count or 0) == 0
        ):
            selected.append(geography_id)
    return sorted(set(selected))


def _load_regional_summary(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read regional summary: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("regional summary must be a JSON object")
    if payload.get("schema") != "icesat2_regional_expansion_scan_v1":
        raise ValueError("regional summary schema is not supported")
    return payload


def _query_geography_candidates(
    *,
    seed: GeographySeed,
    start: str,
    end: str,
    buffer_m: float,
    tile_size_m: float,
    minimum_ground_photons: int,
    maximum_uncertainty_m: float | None,
    minimum_epochs: int,
    minimum_side_epochs: int,
    minimum_step_m: float,
    maximum_plateau_nmad_m: float,
    minimum_step_dominance: float,
) -> tuple[list[SegmentStepAssessment], dict[str, object]]:
    manifest = _load_manifest(seed.representative.run_dir)
    tiles = build_query_tiles(
        manifest,
        buffer_m=buffer_m,
        tile_size_m=tile_size_m,
    )
    all_segments: list[Icesat2Segment] = []
    failures: list[dict[str, object]] = []
    returned_rows = 0
    for position, tile in enumerate(tiles, start=1):
        print(
            f"    tile {position}/{len(tiles)} {tile.tile_id}",
            file=sys.stderr,
            flush=True,
        )
        try:
            frame = _query_atl08(
                polygon=list(tile.polygon_wgs84),
                start=start,
                end=end,
            )
            returned_rows += int(len(frame)) if hasattr(frame, "__len__") else 0
            segments, _, _ = _segments_from_frame(
                frame,
                epsg=manifest.epsg,
                maximum_uncertainty_m=maximum_uncertainty_m,
                minimum_ground_photons=minimum_ground_photons,
            )
            all_segments.extend(segments)
        except Exception as exc:  # noqa: BLE001 - isolate one remote tile
            failures.append(
                {
                    "tile_id": tile.tile_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )

    segments = deduplicate_segments(all_segments)
    assessments = scan_segment_series(
        segments,
        minimum_epochs=minimum_epochs,
        minimum_side_epochs=minimum_side_epochs,
        minimum_step_m=minimum_step_m,
        maximum_plateau_nmad_m=maximum_plateau_nmad_m,
        minimum_step_dominance=minimum_step_dominance,
    ) if segments else []
    candidates = [
        item for item in assessments if item.classification == "step_up_candidate"
    ]
    diagnostics = {
        "tile_count": len(tiles),
        "failed_tile_count": len(failures),
        "tile_failures": failures,
        "returned_row_count_before_deduplication": returned_rows,
        "quality_segment_count_after_deduplication": len(segments),
        "exact_segment_series_count": len(assessments),
        "raw_step_up_segment_count": len(candidates),
    }
    return candidates, diagnostics


def audit_near_misses(
    *,
    runs_dir: Path,
    regional_summary_path: Path,
    output_dir: Path,
    summary_path: Path,
    start: str,
    end: str,
    buffer_m: float,
    tile_size_m: float,
    strict_radius_m: float,
    diagnostic_radii_m: Sequence[float],
    minimum_segments: int,
    maximum_step_nmad_m: float,
    cross_spot_distance_m: float,
    minimum_ground_photons: int,
    maximum_uncertainty_m: float | None,
    minimum_epochs: int,
    minimum_side_epochs: int,
    minimum_step_m: float,
    maximum_plateau_nmad_m: float,
    minimum_step_dominance: float,
) -> dict[str, object]:
    regional_summary = _load_regional_summary(regional_summary_path)
    selected_ids = _selected_geography_ids(regional_summary)
    selections, skipped = discover_completed_runs(runs_dir)
    seeds, rejected = deduplicate_geographies(selections)
    seeds_by_id = {
        seed.representative.run_dir.name: seed
        for seed in seeds
    }
    missing = [value for value in selected_ids if value not in seeds_by_id]
    output_dir.mkdir(parents=True, exist_ok=True)

    geography_results: list[dict[str, object]] = []
    binding_groups: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for position, geography_id in enumerate(selected_ids, start=1):
        seed = seeds_by_id.get(geography_id)
        if seed is None:
            continue
        print(
            f"[{position}/{len(selected_ids)}] auditing {geography_id}",
            file=sys.stderr,
            flush=True,
        )
        try:
            candidates, diagnostics = _query_geography_candidates(
                seed=seed,
                start=start,
                end=end,
                buffer_m=buffer_m,
                tile_size_m=tile_size_m,
                minimum_ground_photons=minimum_ground_photons,
                maximum_uncertainty_m=maximum_uncertainty_m,
                minimum_epochs=minimum_epochs,
                minimum_side_epochs=minimum_side_epochs,
                minimum_step_m=minimum_step_m,
                maximum_plateau_nmad_m=maximum_plateau_nmad_m,
                minimum_step_dominance=minimum_step_dominance,
            )
        except Exception as exc:  # noqa: BLE001 - isolate one geography
            failures.append(
                {
                    "geography_id": geography_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            continue

        groups = diagnose_event_groups(
            candidates,
            strict_radius_m=strict_radius_m,
            diagnostic_radii_m=diagnostic_radii_m,
            minimum_segments=minimum_segments,
            maximum_step_nmad_m=maximum_step_nmad_m,
        )
        mapped_candidates = [
            _assessment_mapping(
                item,
                candidates,
                cross_spot_distance_m=cross_spot_distance_m,
            )
            for item in candidates
        ]
        result = {
            "schema": "icesat2_regional_near_miss_geography_v1",
            "geography_id": geography_id,
            "member_runs": list(seed.member_runs),
            "center_longitude": seed.center_longitude,
            "center_latitude": seed.center_latitude,
            "diagnostics": diagnostics,
            "step_candidates": mapped_candidates,
            "event_groups": groups,
            "strict_neighbor_radius_binding_group_count": sum(
                item["diagnosis"] == "strict_neighbor_radius_was_binding"
                for item in groups
            ),
            "interpretation": {
                "production_thresholds_changed": False,
                "cause_confirmed": False,
                "depth_anchor_created": False,
            },
        }
        result_path = output_dir / f"{geography_id}.json"
        result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        geography_results.append(
            {
                "geography_id": geography_id,
                "member_runs": list(seed.member_runs),
                "raw_step_up_segment_count": len(candidates),
                "event_group_count": len(groups),
                "strict_neighbor_radius_binding_group_count": result[
                    "strict_neighbor_radius_binding_group_count"
                ],
                "failed_tile_count": diagnostics["failed_tile_count"],
                "result_json": str(result_path),
            }
        )
        for group in groups:
            if group["diagnosis"] == "strict_neighbor_radius_was_binding":
                binding_groups.append(
                    {
                        "geography_id": geography_id,
                        "member_runs": list(seed.member_runs),
                        **group,
                    }
                )

    if binding_groups:
        status = "near_miss_groups_require_scientific_review"
    elif geography_results:
        status = "isolated_steps_confirmed_not_clustered_within_1km"
    else:
        status = "near_miss_audit_unavailable"

    summary = {
        "schema": SCHEMA,
        "status": status,
        "runs_directory": str(runs_dir),
        "regional_summary": str(regional_summary_path),
        "selected_geography_count": len(selected_ids),
        "completed_geography_audit_count": len(geography_results),
        "failed_geography_count": len(failures),
        "strict_neighbor_radius_binding_group_count": len(binding_groups),
        "scientific_review_priority": binding_groups,
        "geography_results": geography_results,
        "failures": failures,
        "missing_selected_geographies": missing,
        "skipped_directories": skipped,
        "rejected_geographies": rejected,
        "audit_parameters": {
            "query_start": start,
            "query_end": end,
            "buffer_m": buffer_m,
            "tile_size_m": tile_size_m,
            "strict_radius_m": strict_radius_m,
            "diagnostic_radii_m": list(diagnostic_radii_m),
            "minimum_segments": minimum_segments,
            "maximum_step_nmad_m": maximum_step_nmad_m,
            "cross_spot_distance_m": cross_spot_distance_m,
            "minimum_ground_photons": minimum_ground_photons,
            "maximum_uncertainty_m": maximum_uncertainty_m,
            "minimum_epochs": minimum_epochs,
            "minimum_side_epochs": minimum_side_epochs,
            "minimum_step_m": minimum_step_m,
            "maximum_plateau_nmad_m": maximum_plateau_nmad_m,
            "minimum_step_dominance": minimum_step_dominance,
        },
        "interpretation": {
            "strict_250m_gate_remains_unchanged": True,
            "diagnostic_500m_and_1000m_are_not_acceptance_thresholds": True,
            "records_not_researched": True,
            "candidate_cause_confirmed": False,
            "candidate_is_depth_anchor": False,
        },
        "does_not_prove": [
            "engineered_fill",
            "placed_material_thickness",
            "depth_to_a_buried_object",
            "radar_depth_prediction",
        ],
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit rejected regional ICESat-2 step candidates."
    )
    parser.add_argument("--runs-dir", type=Path, default=Path("./data/runs"))
    parser.add_argument("--regional-summary", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--summary-json", type=Path, default=None)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--buffer-km", type=float, default=10.0)
    parser.add_argument("--tile-km", type=float, default=10.0)
    parser.add_argument("--strict-radius-m", type=float, default=250.0)
    parser.add_argument(
        "--diagnostic-radius-m",
        type=float,
        action="append",
        default=None,
        help="Diagnostic-only radius; may be repeated. Defaults to 500 and 1000.",
    )
    parser.add_argument("--minimum-segments", type=int, default=3)
    parser.add_argument("--maximum-step-nmad-m", type=float, default=0.25)
    parser.add_argument("--cross-spot-distance-m", type=float, default=500.0)
    parser.add_argument("--minimum-ground-photons", type=int, default=3)
    parser.add_argument("--maximum-uncertainty-m", type=float, default=None)
    parser.add_argument("--minimum-epochs", type=int, default=4)
    parser.add_argument("--minimum-side-epochs", type=int, default=2)
    parser.add_argument("--minimum-step-m", type=float, default=0.3)
    parser.add_argument("--maximum-plateau-nmad-m", type=float, default=0.25)
    parser.add_argument("--minimum-step-dominance", type=float, default=0.6)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    regional_dir = args.runs_dir / DEFAULT_OUTPUT_DIRNAME
    regional_summary = args.regional_summary or (
        regional_dir / DEFAULT_REGIONAL_SUMMARY_FILENAME
    )
    output_dir = args.output_dir or (
        args.runs_dir / DEFAULT_OUTPUT_DIRNAME
    )
    summary_path = args.summary_json or (
        output_dir / DEFAULT_SUMMARY_FILENAME
    )
    diagnostic_radii = args.diagnostic_radius_m or [500.0, 1000.0]
    try:
        result = audit_near_misses(
            runs_dir=args.runs_dir,
            regional_summary_path=regional_summary,
            output_dir=output_dir,
            summary_path=summary_path,
            start=args.start,
            end=args.end,
            buffer_m=float(args.buffer_km) * 1000.0,
            tile_size_m=float(args.tile_km) * 1000.0,
            strict_radius_m=args.strict_radius_m,
            diagnostic_radii_m=diagnostic_radii,
            minimum_segments=args.minimum_segments,
            maximum_step_nmad_m=args.maximum_step_nmad_m,
            cross_spot_distance_m=args.cross_spot_distance_m,
            minimum_ground_photons=args.minimum_ground_photons,
            maximum_uncertainty_m=args.maximum_uncertainty_m,
            minimum_epochs=args.minimum_epochs,
            minimum_side_epochs=args.minimum_side_epochs,
            minimum_step_m=args.minimum_step_m,
            maximum_plateau_nmad_m=args.maximum_plateau_nmad_m,
            minimum_step_dominance=args.minimum_step_dominance,
        )
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "near_miss_audit_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["failed_geography_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
