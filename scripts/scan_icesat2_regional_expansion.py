"""Expand the scan-first ICESat-2 search around unique completed-run geographies.

The existing-run scan can contain duplicate runs at the same place. This tool:

1. discovers completed run directories;
2. deduplicates nearly identical run geographies;
3. expands each unique geography by a configurable buffer;
4. queries the expanded area in local projected tiles;
5. combines and deduplicates ATL08 terrain observations across tiles;
6. keeps only persistent upward steps with neighbouring-segment support;
7. ranks survivors for later record lookup.

It does not research records, create depth anchors, invoke the radar depth
engine, register app artifacts, or modify the frontend.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from pyproj import Transformer

from app.pipeline.elevation_change.icesat2_repeat import Icesat2Segment
from app.pipeline.elevation_change.icesat2_step_scan import (
    cluster_step_candidates,
    scan_segment_series,
)
from audit_icesat2_repeat_points import (
    DEFAULT_END,
    DEFAULT_START,
    Icesat2AuditError,
    _load_manifest,
    _query_atl08,
    _segments_from_frame,
)
from scan_all_icesat2_terrain_steps import (
    RunSelection,
    discover_completed_runs,
    rank_candidates,
)
from scan_icesat2_terrain_steps import _cluster_mapping, _geojson

SCHEMA = "icesat2_regional_expansion_scan_v1"
DEFAULT_OUTPUT_DIRNAME = "icesat2_regional_expansion"
DEFAULT_SUMMARY_FILENAME = "icesat2_regional_expansion_summary.json"


@dataclass(frozen=True, slots=True)
class GeographySeed:
    representative: RunSelection
    member_runs: tuple[str, ...]
    center_longitude: float
    center_latitude: float
    width_m: float
    height_m: float


@dataclass(frozen=True, slots=True)
class QueryTile:
    tile_id: str
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    polygon_wgs84: tuple[dict[str, float], ...]


def _manifest_bounds(manifest) -> tuple[float, float, float, float]:
    bounds = manifest.bounds_m
    required = ("xmin", "ymin", "xmax", "ymax")
    if not all(key in bounds for key in required):
        raise ValueError("grid manifest has incomplete bounds_m")
    xmin = float(bounds["xmin"])
    ymin = float(bounds["ymin"])
    xmax = float(bounds["xmax"])
    ymax = float(bounds["ymax"])
    if not all(math.isfinite(value) for value in (xmin, ymin, xmax, ymax)):
        raise ValueError("grid manifest bounds are not finite")
    if xmax <= xmin or ymax <= ymin:
        raise ValueError("grid manifest bounds are not ordered")
    return xmin, ymin, xmax, ymax


def _projected_point_to_wgs84(
    *,
    epsg: int,
    x_m: float,
    y_m: float,
) -> tuple[float, float]:
    transformer = Transformer.from_crs(
        f"EPSG:{int(epsg)}", "EPSG:4326", always_xy=True
    )
    longitude, latitude = transformer.transform(float(x_m), float(y_m))
    return float(longitude), float(latitude)


def _manifest_center(manifest) -> tuple[float, float, float, float]:
    xmin, ymin, xmax, ymax = _manifest_bounds(manifest)
    longitude, latitude = _projected_point_to_wgs84(
        epsg=manifest.epsg,
        x_m=(xmin + xmax) / 2.0,
        y_m=(ymin + ymax) / 2.0,
    )
    return longitude, latitude, xmax - xmin, ymax - ymin


def _haversine_m(
    longitude_a: float,
    latitude_a: float,
    longitude_b: float,
    latitude_b: float,
) -> float:
    radius_m = 6_371_008.8
    lon1 = math.radians(longitude_a)
    lat1 = math.radians(latitude_a)
    lon2 = math.radians(longitude_b)
    lat2 = math.radians(latitude_b)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    value = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    )
    return float(2.0 * radius_m * math.asin(min(1.0, math.sqrt(value))))


def deduplicate_geographies(
    selections: Sequence[RunSelection],
    *,
    center_tolerance_m: float = 250.0,
    size_tolerance_m: float = 250.0,
    manifest_loader: Callable[[Path], object] = _load_manifest,
) -> tuple[list[GeographySeed], list[dict[str, object]]]:
    """Collapse completed runs that cover essentially the same projected grid."""

    if center_tolerance_m < 0 or size_tolerance_m < 0:
        raise ValueError("deduplication tolerances must be non-negative")

    groups: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    for selection in selections:
        try:
            manifest = manifest_loader(selection.run_dir)
            longitude, latitude, width_m, height_m = _manifest_center(manifest)
        except Exception as exc:  # noqa: BLE001 - report malformed local run
            rejected.append(
                {
                    "run": selection.run_dir.name,
                    "reason": "unreadable_grid_manifest",
                    "error": str(exc),
                }
            )
            continue

        matched = None
        for group in groups:
            representative_manifest = group["manifest"]
            if int(representative_manifest.epsg) != int(manifest.epsg):
                continue
            distance = _haversine_m(
                float(group["center_longitude"]),
                float(group["center_latitude"]),
                longitude,
                latitude,
            )
            if (
                distance <= center_tolerance_m
                and abs(float(group["width_m"]) - width_m) <= size_tolerance_m
                and abs(float(group["height_m"]) - height_m) <= size_tolerance_m
            ):
                matched = group
                break

        if matched is None:
            groups.append(
                {
                    "representative": selection,
                    "manifest": manifest,
                    "members": [selection.run_dir.name],
                    "center_longitude": longitude,
                    "center_latitude": latitude,
                    "width_m": width_m,
                    "height_m": height_m,
                }
            )
        else:
            matched["members"].append(selection.run_dir.name)

    seeds = [
        GeographySeed(
            representative=group["representative"],
            member_runs=tuple(sorted(group["members"])),
            center_longitude=float(group["center_longitude"]),
            center_latitude=float(group["center_latitude"]),
            width_m=float(group["width_m"]),
            height_m=float(group["height_m"]),
        )
        for group in groups
    ]
    seeds.sort(
        key=lambda item: (
            item.center_longitude,
            item.center_latitude,
            item.representative.run_dir.name,
        )
    )
    return seeds, rejected


def _tile_polygon_wgs84(
    *,
    epsg: int,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
) -> tuple[dict[str, float], ...]:
    transformer = Transformer.from_crs(
        f"EPSG:{int(epsg)}", "EPSG:4326", always_xy=True
    )
    corners = (
        (xmin, ymin),
        (xmax, ymin),
        (xmax, ymax),
        (xmin, ymax),
        (xmin, ymin),
    )
    result: list[dict[str, float]] = []
    for x_m, y_m in corners:
        longitude, latitude = transformer.transform(x_m, y_m)
        result.append({"lon": float(longitude), "lat": float(latitude)})
    return tuple(result)


def build_query_tiles(
    manifest,
    *,
    buffer_m: float,
    tile_size_m: float,
) -> list[QueryTile]:
    """Build non-overlapping projected tiles covering one buffered run grid."""

    if buffer_m <= 0:
        raise ValueError("buffer_m must be positive")
    if tile_size_m <= 0:
        raise ValueError("tile_size_m must be positive")

    xmin, ymin, xmax, ymax = _manifest_bounds(manifest)
    expanded_xmin = xmin - buffer_m
    expanded_ymin = ymin - buffer_m
    expanded_xmax = xmax + buffer_m
    expanded_ymax = ymax + buffer_m

    tiles: list[QueryTile] = []
    row = 0
    y0 = expanded_ymin
    while y0 < expanded_ymax:
        y1 = min(y0 + tile_size_m, expanded_ymax)
        column = 0
        x0 = expanded_xmin
        while x0 < expanded_xmax:
            x1 = min(x0 + tile_size_m, expanded_xmax)
            tile_id = f"r{row:03d}_c{column:03d}"
            tiles.append(
                QueryTile(
                    tile_id=tile_id,
                    xmin=x0,
                    ymin=y0,
                    xmax=x1,
                    ymax=y1,
                    polygon_wgs84=_tile_polygon_wgs84(
                        epsg=manifest.epsg,
                        xmin=x0,
                        ymin=y0,
                        xmax=x1,
                        ymax=y1,
                    ),
                )
            )
            column += 1
            x0 = x1
        row += 1
        y0 = y1
    return tiles


def deduplicate_segments(
    segments: Iterable[Icesat2Segment],
) -> list[Icesat2Segment]:
    unique = {
        (
            item.rgt,
            item.spot,
            item.cycle,
            item.segment_id,
            item.observed_at,
        ): item
        for item in segments
    }
    return sorted(
        unique.values(),
        key=lambda item: (
            item.observed_at,
            item.rgt,
            item.spot,
            item.segment_id,
        ),
    )


def _point_inside_manifest(
    *,
    longitude: float,
    latitude: float,
    manifest,
) -> bool:
    transformer = Transformer.from_crs(
        "EPSG:4326", f"EPSG:{int(manifest.epsg)}", always_xy=True
    )
    x_m, y_m = transformer.transform(float(longitude), float(latitude))
    xmin, ymin, xmax, ymax = _manifest_bounds(manifest)
    return xmin <= x_m <= xmax and ymin <= y_m <= ymax


def _candidate_rows(
    clusters: Sequence[dict[str, object]],
    *,
    geography_id: str,
    member_runs: Sequence[str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for local_rank, item in enumerate(clusters, start=1):
        rows.append(
            {
                "geography_id": geography_id,
                "member_runs": list(member_runs),
                "run_local_rank": local_rank,
                "longitude": item.get("centroid_longitude"),
                "latitude": item.get("centroid_latitude"),
                "event_start": item.get("event_start"),
                "event_end": item.get("event_end"),
                "median_step_m": item.get("median_step_m"),
                "step_nmad_m": item.get("step_nmad_m"),
                "segment_count": item.get("segment_count"),
                "cross_spot_supported": bool(item.get("cross_spot_supported")),
                "rgt": item.get("rgt"),
                "spot": item.get("spot"),
                "pre_cycle": item.get("pre_cycle"),
                "post_cycle": item.get("post_cycle"),
                "inside_existing_run_aoi": bool(
                    item.get("inside_existing_run_aoi")
                ),
            }
        )
    return rows


def scan_geography(
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
    neighbor_distance_m: float,
    minimum_neighbor_segments: int,
    maximum_cluster_step_nmad_m: float,
    cross_spot_distance_m: float,
    candidate_limit: int,
    query_callable: Callable[..., object] = _query_atl08,
    manifest_loader: Callable[[Path], object] = _load_manifest,
) -> dict[str, object]:
    manifest = manifest_loader(seed.representative.run_dir)
    tiles = build_query_tiles(
        manifest,
        buffer_m=buffer_m,
        tile_size_m=tile_size_m,
    )

    all_segments: list[Icesat2Segment] = []
    tile_failures: list[dict[str, object]] = []
    returned_rows = 0
    for position, tile in enumerate(tiles, start=1):
        print(
            f"    tile {position}/{len(tiles)} {tile.tile_id}",
            file=sys.stderr,
            flush=True,
        )
        try:
            frame = query_callable(
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
            tile_failures.append(
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
    clusters = cluster_step_candidates(
        assessments,
        neighbor_distance_m=neighbor_distance_m,
        minimum_neighbor_segments=minimum_neighbor_segments,
        maximum_cluster_step_nmad_m=maximum_cluster_step_nmad_m,
    ) if assessments else []

    mapped_clusters = [
        _cluster_mapping(
            cluster,
            clusters,
            cross_spot_distance_m=cross_spot_distance_m,
        )
        for cluster in clusters[: max(0, int(candidate_limit))]
    ]
    for item in mapped_clusters:
        longitude = item.get("centroid_longitude")
        latitude = item.get("centroid_latitude")
        item["inside_existing_run_aoi"] = (
            isinstance(longitude, (int, float))
            and isinstance(latitude, (int, float))
            and _point_inside_manifest(
                longitude=float(longitude),
                latitude=float(latitude),
                manifest=manifest,
            )
        )

    classification_counts = Counter(item.classification for item in assessments)
    raw_steps = sum(
        item.classification == "step_up_candidate" for item in assessments
    )
    if not segments:
        status = "no_quality_atl08_segments"
    elif not raw_steps:
        status = "no_persistent_upward_steps"
    elif not clusters:
        status = "isolated_steps_rejected_by_neighbor_filter"
    else:
        status = "spatially_supported_step_candidates_found"

    geography_id = seed.representative.run_dir.name
    return {
        "schema": "icesat2_regional_geography_scan_v1",
        "status": status,
        "geography_id": geography_id,
        "representative_run": seed.representative.run_dir.name,
        "member_runs": list(seed.member_runs),
        "run_epsg": manifest.epsg,
        "center_longitude": seed.center_longitude,
        "center_latitude": seed.center_latitude,
        "buffer_m": buffer_m,
        "tile_size_m": tile_size_m,
        "tile_count": len(tiles),
        "failed_tile_count": len(tile_failures),
        "tile_failures": tile_failures,
        "returned_row_count_before_deduplication": returned_rows,
        "quality_segment_count_after_deduplication": len(segments),
        "exact_segment_series_count": len(assessments),
        "classification_counts": dict(sorted(classification_counts.items())),
        "raw_step_up_segment_count": raw_steps,
        "surviving_step_cluster_count": len(clusters),
        "surviving_step_clusters": mapped_clusters,
        "candidate_output_truncated": len(clusters) > int(candidate_limit),
        "scan_parameters": {
            "query_start": start,
            "query_end": end,
            "minimum_ground_photons": minimum_ground_photons,
            "maximum_uncertainty_m": maximum_uncertainty_m,
            "minimum_epochs": minimum_epochs,
            "minimum_side_epochs": minimum_side_epochs,
            "minimum_step_m": minimum_step_m,
            "maximum_plateau_nmad_m": maximum_plateau_nmad_m,
            "minimum_step_dominance": minimum_step_dominance,
            "neighbor_distance_m": neighbor_distance_m,
            "minimum_neighbor_segments": minimum_neighbor_segments,
            "maximum_cluster_step_nmad_m": maximum_cluster_step_nmad_m,
            "cross_spot_distance_m": cross_spot_distance_m,
        },
        "interpretation": {
            "existing_run_geographies_deduplicated": True,
            "records_needed_only_for_survivors": True,
            "candidate_cause_confirmed": False,
            "candidate_is_depth_anchor": False,
        },
        "does_not_prove": [
            "engineered_fill",
            "placed_material_thickness",
            "depth_to_a_buried_object",
            "radar_depth_prediction",
            "spatial_transfer_beyond_the_laser_strip",
        ],
    }


def scan_regional_expansion(
    *,
    runs_dir: Path,
    output_dir: Path,
    summary_path: Path,
    start: str,
    end: str,
    buffer_m: float,
    tile_size_m: float,
    center_tolerance_m: float,
    size_tolerance_m: float,
    continue_on_error: bool,
    minimum_ground_photons: int = 3,
    maximum_uncertainty_m: float | None = None,
    minimum_epochs: int = 4,
    minimum_side_epochs: int = 2,
    minimum_step_m: float = 0.3,
    maximum_plateau_nmad_m: float = 0.25,
    minimum_step_dominance: float = 0.6,
    neighbor_distance_m: float = 250.0,
    minimum_neighbor_segments: int = 3,
    maximum_cluster_step_nmad_m: float = 0.25,
    cross_spot_distance_m: float = 500.0,
    candidate_limit_per_geography: int = 20,
) -> dict[str, object]:
    selections, skipped = discover_completed_runs(runs_dir)
    seeds, rejected = deduplicate_geographies(
        selections,
        center_tolerance_m=center_tolerance_m,
        size_tolerance_m=size_tolerance_m,
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    geography_summaries: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    all_candidates: list[dict[str, object]] = []

    for position, seed in enumerate(seeds, start=1):
        geography_id = seed.representative.run_dir.name
        print(
            f"[{position}/{len(seeds)}] expanding {geography_id} "
            f"({len(seed.member_runs)} run(s))",
            file=sys.stderr,
            flush=True,
        )
        try:
            result = scan_geography(
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
                neighbor_distance_m=neighbor_distance_m,
                minimum_neighbor_segments=minimum_neighbor_segments,
                maximum_cluster_step_nmad_m=maximum_cluster_step_nmad_m,
                cross_spot_distance_m=cross_spot_distance_m,
                candidate_limit=candidate_limit_per_geography,
            )
        except Exception as exc:  # noqa: BLE001 - isolate one geography
            failure = {
                "geography_id": geography_id,
                "member_runs": list(seed.member_runs),
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            failures.append(failure)
            if not continue_on_error:
                raise
            continue

        result_path = output_dir / f"{geography_id}.json"
        geojson_path = output_dir / f"{geography_id}.geojson"
        result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        geojson_path.write_text(
            json.dumps(_geojson(result), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        clusters = result.get("surviving_step_clusters", [])
        if not isinstance(clusters, list):
            clusters = []
        all_candidates.extend(
            _candidate_rows(
                [item for item in clusters if isinstance(item, dict)],
                geography_id=geography_id,
                member_runs=seed.member_runs,
            )
        )
        geography_summaries.append(
            {
                "geography_id": geography_id,
                "member_runs": list(seed.member_runs),
                "center_longitude": seed.center_longitude,
                "center_latitude": seed.center_latitude,
                "status": result.get("status"),
                "tile_count": result.get("tile_count"),
                "failed_tile_count": result.get("failed_tile_count"),
                "quality_segment_count_after_deduplication": result.get(
                    "quality_segment_count_after_deduplication"
                ),
                "exact_segment_series_count": result.get(
                    "exact_segment_series_count"
                ),
                "classification_counts": result.get("classification_counts", {}),
                "raw_step_up_segment_count": result.get(
                    "raw_step_up_segment_count", 0
                ),
                "surviving_step_cluster_count": result.get(
                    "surviving_step_cluster_count", 0
                ),
                "result_json": str(result_path),
                "result_geojson": str(geojson_path),
            }
        )

    ranked = rank_candidates(all_candidates)
    outside_existing = [
        item for item in ranked if not item.get("inside_existing_run_aoi")
    ]
    for index, item in enumerate(outside_existing, start=1):
        item["regional_rank"] = index

    status = (
        "regional_surviving_candidates_found"
        if outside_existing
        else "no_surviving_candidates_in_regional_expansion"
    )
    summary = {
        "schema": SCHEMA,
        "status": status,
        "runs_directory": str(runs_dir),
        "output_directory": str(output_dir),
        "selected_completed_run_count": len(selections),
        "unique_geography_count": len(seeds),
        "duplicate_run_count": max(0, len(selections) - len(seeds)),
        "completed_geography_scan_count": len(geography_summaries),
        "failed_geography_count": len(failures),
        "surviving_candidate_count": len(outside_existing),
        "record_lookup_priority": outside_existing,
        "geography_summaries": geography_summaries,
        "failures": failures,
        "rejected_geographies": rejected,
        "skipped_directories": skipped,
        "scan_parameters": {
            "query_start": start,
            "query_end": end,
            "buffer_m": buffer_m,
            "tile_size_m": tile_size_m,
            "center_tolerance_m": center_tolerance_m,
            "size_tolerance_m": size_tolerance_m,
            "minimum_ground_photons": minimum_ground_photons,
            "maximum_uncertainty_m": maximum_uncertainty_m,
            "minimum_epochs": minimum_epochs,
            "minimum_side_epochs": minimum_side_epochs,
            "minimum_step_m": minimum_step_m,
            "maximum_plateau_nmad_m": maximum_plateau_nmad_m,
            "minimum_step_dominance": minimum_step_dominance,
            "neighbor_distance_m": neighbor_distance_m,
            "minimum_neighbor_segments": minimum_neighbor_segments,
            "maximum_cluster_step_nmad_m": maximum_cluster_step_nmad_m,
            "cross_spot_distance_m": cross_spot_distance_m,
        },
        "interpretation": {
            "existing_runs_deduplicated_before_expansion": True,
            "existing_aoi_candidates_excluded_from_priority": True,
            "records_needed_only_for_ranked_survivors": True,
            "candidate_cause_confirmed": False,
            "candidate_is_depth_anchor": False,
        },
        "does_not_prove": [
            "engineered_fill",
            "placed_material_thickness",
            "depth_to_a_buried_object",
            "radar_depth_prediction",
            "spatial_transfer_beyond_the_laser_strip",
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
        description=(
            "Deduplicate completed-run geographies and scan a buffered regional "
            "expansion for persistent ICESat-2 terrain steps."
        )
    )
    parser.add_argument("--runs-dir", type=Path, default=Path("./data/runs"))
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--summary-json", type=Path, default=None)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--buffer-km", type=float, default=10.0)
    parser.add_argument("--tile-km", type=float, default=10.0)
    parser.add_argument("--duplicate-center-tolerance-m", type=float, default=250.0)
    parser.add_argument("--duplicate-size-tolerance-m", type=float, default=250.0)
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--minimum-ground-photons", type=int, default=3)
    parser.add_argument("--maximum-uncertainty-m", type=float, default=None)
    parser.add_argument("--minimum-epochs", type=int, default=4)
    parser.add_argument("--minimum-side-epochs", type=int, default=2)
    parser.add_argument("--minimum-step-m", type=float, default=0.3)
    parser.add_argument("--maximum-plateau-nmad-m", type=float, default=0.25)
    parser.add_argument("--minimum-step-dominance", type=float, default=0.6)
    parser.add_argument("--neighbor-distance-m", type=float, default=250.0)
    parser.add_argument("--minimum-neighbor-segments", type=int, default=3)
    parser.add_argument("--maximum-cluster-step-nmad-m", type=float, default=0.25)
    parser.add_argument("--cross-spot-distance-m", type=float, default=500.0)
    parser.add_argument("--candidate-limit-per-geography", type=int, default=20)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.buffer_km <= 0 or args.tile_km <= 0:
        print(
            json.dumps(
                {
                    "status": "regional_scan_failed",
                    "error": "buffer-km and tile-km must be positive",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    output_dir = args.output_dir or args.runs_dir / DEFAULT_OUTPUT_DIRNAME
    summary_path = args.summary_json or output_dir / DEFAULT_SUMMARY_FILENAME
    try:
        result = scan_regional_expansion(
            runs_dir=args.runs_dir,
            output_dir=output_dir,
            summary_path=summary_path,
            start=args.start,
            end=args.end,
            buffer_m=args.buffer_km * 1000.0,
            tile_size_m=args.tile_km * 1000.0,
            center_tolerance_m=args.duplicate_center_tolerance_m,
            size_tolerance_m=args.duplicate_size_tolerance_m,
            continue_on_error=not args.stop_on_error,
            minimum_ground_photons=args.minimum_ground_photons,
            maximum_uncertainty_m=args.maximum_uncertainty_m,
            minimum_epochs=args.minimum_epochs,
            minimum_side_epochs=args.minimum_side_epochs,
            minimum_step_m=args.minimum_step_m,
            maximum_plateau_nmad_m=args.maximum_plateau_nmad_m,
            minimum_step_dominance=args.minimum_step_dominance,
            neighbor_distance_m=args.neighbor_distance_m,
            minimum_neighbor_segments=args.minimum_neighbor_segments,
            maximum_cluster_step_nmad_m=args.maximum_cluster_step_nmad_m,
            cross_spot_distance_m=args.cross_spot_distance_m,
            candidate_limit_per_geography=args.candidate_limit_per_geography,
        )
    except (Icesat2AuditError, OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "regional_scan_failed",
                    "error": str(exc),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["failed_geography_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
