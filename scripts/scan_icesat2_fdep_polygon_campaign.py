"""Run an ICESat-2 terrain-step scan constrained to official FDEP mine polygons.

Campaign 006 used a broad Central Florida rectangle and found persistent
sub-5 m terrain steps, but none of their supporting ATL08 segments intersected
the official active-mine, released-mine, or reclamation-unit layers. This
private research tool corrects that failure mode by:

1. downloading the official 2021 active mandatory phosphate mine polygons;
2. retaining only query tiles whose WGS84 bounds intersect those polygons; and
3. discarding every ATL08 segment outside the official polygons before time
   series scanning and spatial clustering.

A surviving cluster is still only a terrain-step candidate. This tool does not
prove engineered fill, placed-material thickness, depth to a buried object, or
radar transferability, and it does not modify app artifacts.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Sequence
from urllib.parse import urlencode
from urllib.request import Request, urlopen

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.pipeline.elevation_change.icesat2_repeat import Icesat2Segment
from app.pipeline.elevation_change.icesat2_step_scan import (
    cluster_step_candidates,
    scan_segment_series,
)
from audit_icesat2_repeat_points import (
    DEFAULT_END,
    DEFAULT_START,
    _query_atl08,
    _segments_from_frame,
)
from scan_all_icesat2_terrain_steps import rank_candidates
from scan_icesat2_broad_track_campaign import (
    REGION_SCHEMA,
    SUMMARY_SCHEMA,
    RegionSpec,
    _candidate_rows,
    _inside,
    build_tiles,
    read_cache,
    write_cache,
)
from scan_icesat2_regional_expansion import deduplicate_segments
from scan_icesat2_terrain_steps import _cluster_mapping, _geojson

CAMPAIGN_ID = "southeast_us_earthwork_pilot_v7_fdep_active_mines"
CAMPAIGN_DESCRIPTION = (
    "Seventh independent ATL08 terrain-step campaign constrained to official "
    "FDEP 2021 active mandatory phosphate mine polygons, with all prior "
    "temporal, stability, context, and manual-footprint gates preserved."
)
REGION_ID = "fdep_active_mandatory_phosphate_mines"
REGION_DESCRIPTION = (
    "Central Florida active mandatory phosphate mine footprints inside the "
    "Campaign 006 search envelope; tiles and ATL08 segments are polygon-filtered."
)
DEFAULT_OUTPUT_ROOT = Path("./data/research/icesat2_broad_track_scan")
FDEP_LAYER_URL = (
    "https://ca.dep.state.fl.us/arcgis/rest/services/"
    "OpenData/MMP_MANPHO/MapServer/13/query"
)
DEFAULT_BOUNDS = (-82.20, 27.20, -81.55, 28.20)
POLYGON_CACHE_SCHEMA = "icesat2_fdep_polygon_tile_cache_v1"

FetchJson = Callable[[str, dict[str, str], float], dict[str, Any]]


def _default_fetch_json(
    url: str,
    params: dict[str, str],
    timeout_seconds: float,
) -> dict[str, Any]:
    request = Request(
        f"{url}?{urlencode(params)}",
        headers={
            "Accept": "application/geo+json, application/json",
            "User-Agent": "New-GEE-FDEP-polygon-campaign/1.0",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"FDEP polygon request failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("FDEP polygon response was not a JSON object")
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message") or "unknown ArcGIS error"
        raise RuntimeError(f"FDEP ArcGIS error: {message}")
    return payload


def fetch_active_mines(
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    timeout_seconds: float,
    fetch_json: FetchJson = _default_fetch_json,
) -> dict[str, Any]:
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("invalid WGS84 bounds")
    envelope = json.dumps(
        {
            "xmin": west,
            "ymin": south,
            "xmax": east,
            "ymax": north,
            "spatialReference": {"wkid": 4326},
        },
        separators=(",", ":"),
    )
    payload = fetch_json(
        FDEP_LAYER_URL,
        {
            "where": "1=1",
            "geometry": envelope,
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "returnDomainNames": "true",
            "f": "geojson",
        },
        timeout_seconds,
    )
    if payload.get("type") != "FeatureCollection":
        raise ValueError("FDEP response is not a GeoJSON FeatureCollection")
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("FDEP FeatureCollection has no features list")
    polygon_features = [
        item
        for item in features
        if isinstance(item, dict)
        and isinstance(item.get("geometry"), dict)
        and item["geometry"].get("type") in {"Polygon", "MultiPolygon"}
    ]
    if not polygon_features:
        raise ValueError("no official active-mine polygons intersect the bounds")
    return {"type": "FeatureCollection", "features": polygon_features}


def _finite_pair(value: object) -> tuple[float, float] | None:
    if (
        not isinstance(value, (list, tuple))
        or len(value) < 2
        or not isinstance(value[0], (int, float))
        or not isinstance(value[1], (int, float))
    ):
        return None
    x = float(value[0])
    y = float(value[1])
    if not math.isfinite(x) or not math.isfinite(y):
        return None
    return x, y


def _geometry_polygons(geometry: dict[str, Any]) -> list[list[list[tuple[float, float]]]]:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    raw_polygons: object
    if geometry_type == "Polygon":
        raw_polygons = [coordinates]
    elif geometry_type == "MultiPolygon":
        raw_polygons = coordinates
    else:
        return []
    if not isinstance(raw_polygons, list):
        return []

    polygons: list[list[list[tuple[float, float]]]] = []
    for raw_polygon in raw_polygons:
        if not isinstance(raw_polygon, list):
            continue
        rings: list[list[tuple[float, float]]] = []
        for raw_ring in raw_polygon:
            if not isinstance(raw_ring, list):
                continue
            ring = [
                pair
                for pair in (_finite_pair(value) for value in raw_ring)
                if pair is not None
            ]
            if len(ring) >= 3:
                rings.append(ring)
        if rings:
            polygons.append(rings)
    return polygons


def _feature_polygons(
    feature_collection: dict[str, Any],
) -> list[list[list[tuple[float, float]]]]:
    values = feature_collection.get("features")
    if not isinstance(values, list):
        return []
    polygons: list[list[list[tuple[float, float]]]] = []
    for feature in values:
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry")
        if isinstance(geometry, dict):
            polygons.extend(_geometry_polygons(geometry))
    return polygons


def _point_on_segment(
    x: float,
    y: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
    *,
    tolerance: float = 1e-10,
) -> bool:
    cross = (x - ax) * (by - ay) - (y - ay) * (bx - ax)
    if abs(cross) > tolerance:
        return False
    return (
        min(ax, bx) - tolerance <= x <= max(ax, bx) + tolerance
        and min(ay, by) - tolerance <= y <= max(ay, by) + tolerance
    )


def _point_in_ring(x: float, y: float, ring: Sequence[tuple[float, float]]) -> bool:
    inside = False
    count = len(ring)
    for index in range(count):
        ax, ay = ring[index]
        bx, by = ring[(index + 1) % count]
        if _point_on_segment(x, y, ax, ay, bx, by):
            return True
        if (ay > y) != (by > y):
            intersection_x = ax + (y - ay) * (bx - ax) / (by - ay)
            if intersection_x >= x:
                inside = not inside
    return inside


def _point_in_polygon(
    x: float,
    y: float,
    polygon: Sequence[Sequence[tuple[float, float]]],
) -> bool:
    if not polygon or not _point_in_ring(x, y, polygon[0]):
        return False
    return not any(_point_in_ring(x, y, hole) for hole in polygon[1:])


def _point_in_polygons(
    longitude: float,
    latitude: float,
    polygons: Sequence[Sequence[Sequence[tuple[float, float]]]],
) -> bool:
    return any(
        _point_in_polygon(longitude, latitude, polygon)
        for polygon in polygons
    )


def _polygon_bbox(
    polygon: Sequence[Sequence[tuple[float, float]]],
) -> tuple[float, float, float, float]:
    points = [point for ring in polygon for point in ring]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def _bbox_intersects(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> bool:
    return not (
        left[2] < right[0]
        or right[2] < left[0]
        or left[3] < right[1]
        or right[3] < left[1]
    )


def _tile_bbox_wgs84(tile) -> tuple[float, float, float, float]:
    points = list(tile.polygon_wgs84)
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def select_polygon_tiles(tiles, polygons):
    polygon_bboxes = [_polygon_bbox(polygon) for polygon in polygons]
    return [
        tile
        for tile in tiles
        if any(
            _bbox_intersects(_tile_bbox_wgs84(tile), polygon_bbox)
            for polygon_bbox in polygon_bboxes
        )
    ]


def _cache_signature(
    *,
    tile_id: str,
    start: str,
    end: str,
    epsg: int,
    minimum_ground_photons: int,
    maximum_uncertainty_m: float | None,
) -> dict[str, object]:
    return {
        "schema": POLYGON_CACHE_SCHEMA,
        "campaign_id": CAMPAIGN_ID,
        "region_id": REGION_ID,
        "tile_id": tile_id,
        "query_start": start,
        "query_end": end,
        "epsg": epsg,
        "minimum_ground_photons": minimum_ground_photons,
        "maximum_uncertainty_m": maximum_uncertainty_m,
        "fdep_layer_url": FDEP_LAYER_URL,
        "segment_filter": "inside_official_active_mine_polygon",
    }


def _mine_names(feature_collection: dict[str, Any]) -> list[str]:
    names: set[str] = set()
    values = feature_collection.get("features")
    if isinstance(values, list):
        for feature in values:
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                continue
            value = properties.get("MINE_NAME")
            if value not in (None, ""):
                names.add(str(value))
    return sorted(names)


def _region_result(
    *,
    campaign_dir: Path,
    region: RegionSpec,
    active_mines: dict[str, Any],
    start: str,
    end: str,
    tile_size_m: float,
    tile_overlap_m: float,
    force: bool,
    continue_on_error: bool,
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
) -> dict[str, object]:
    polygons = _feature_polygons(active_mines)
    if not polygons:
        raise ValueError("official active-mine response contains no usable polygons")

    epsg, all_tiles = build_tiles(
        region,
        tile_size_m=tile_size_m,
        overlap_m=tile_overlap_m,
    )
    tiles = select_polygon_tiles(all_tiles, polygons)
    if not tiles:
        raise ValueError("no scan tiles intersect official active-mine polygons")

    region_dir = campaign_dir / region.region_id
    tile_dir = region_dir / "tiles"
    region_dir.mkdir(parents=True, exist_ok=True)
    (region_dir / "fdep_active_mines.geojson").write_text(
        json.dumps(active_mines, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    all_segments: list[Icesat2Segment] = []
    failures: list[dict[str, object]] = []
    cached_tile_count = 0
    for position, tile in enumerate(tiles, start=1):
        print(
            f"    polygon tile {position}/{len(tiles)} {tile.tile_id}",
            file=sys.stderr,
            flush=True,
        )
        signature = _cache_signature(
            tile_id=tile.tile_id,
            start=start,
            end=end,
            epsg=epsg,
            minimum_ground_photons=minimum_ground_photons,
            maximum_uncertainty_m=maximum_uncertainty_m,
        )
        cache_path = tile_dir / f"{tile.tile_id}.json"
        segments = None if force else read_cache(cache_path, signature)
        if segments is not None:
            cached_tile_count += 1
        else:
            try:
                frame = _query_atl08(
                    polygon=list(tile.polygon_wgs84),
                    start=start,
                    end=end,
                )
                segments, _, _ = _segments_from_frame(
                    frame,
                    epsg=epsg,
                    maximum_uncertainty_m=maximum_uncertainty_m,
                    minimum_ground_photons=minimum_ground_photons,
                )
                write_cache(cache_path, signature, segments)
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    {
                        "tile_id": tile.tile_id,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                if not continue_on_error:
                    raise
                continue
        all_segments.extend(segments)

    deduplicated = deduplicate_segments(all_segments)
    box_segments = [item for item in deduplicated if _inside(item, region)]
    segments = [
        item
        for item in box_segments
        if _point_in_polygons(item.longitude, item.latitude, polygons)
    ]
    assessments = (
        scan_segment_series(
            segments,
            minimum_epochs=minimum_epochs,
            minimum_side_epochs=minimum_side_epochs,
            minimum_step_m=minimum_step_m,
            maximum_plateau_nmad_m=maximum_plateau_nmad_m,
            minimum_step_dominance=minimum_step_dominance,
        )
        if segments
        else []
    )
    clusters = (
        cluster_step_candidates(
            assessments,
            neighbor_distance_m=neighbor_distance_m,
            minimum_neighbor_segments=minimum_neighbor_segments,
            maximum_cluster_step_nmad_m=maximum_cluster_step_nmad_m,
        )
        if assessments
        else []
    )
    mapped = [
        _cluster_mapping(
            cluster,
            clusters,
            cross_spot_distance_m=cross_spot_distance_m,
        )
        for cluster in clusters[: max(0, candidate_limit)]
    ]
    counts = Counter(item.classification for item in assessments)
    raw_steps = sum(
        item.classification == "step_up_candidate" for item in assessments
    )
    if not segments:
        status = "no_quality_atl08_segments_inside_official_mines"
    elif not raw_steps:
        status = "no_persistent_upward_steps_inside_official_mines"
    elif not clusters:
        status = "isolated_steps_rejected_inside_official_mines"
    else:
        status = "spatially_supported_steps_inside_official_mines"

    result: dict[str, object] = {
        "schema": REGION_SCHEMA,
        "status": status,
        "campaign_id": CAMPAIGN_ID,
        "region_id": REGION_ID,
        "description": REGION_DESCRIPTION,
        "bounds_wgs84": {
            "west": region.west,
            "south": region.south,
            "east": region.east,
            "north": region.north,
        },
        "analysis_epsg": epsg,
        "bounding_box_tile_count": len(all_tiles),
        "tile_count": len(tiles),
        "tiles_rejected_outside_polygon_envelopes": len(all_tiles) - len(tiles),
        "cached_tile_count": cached_tile_count,
        "completed_tile_count": len(tiles) - len(failures),
        "failed_tile_count": len(failures),
        "tile_failures": failures,
        "quality_segment_count_before_polygon_filter": len(box_segments),
        "quality_segment_count_after_deduplication": len(segments),
        "segments_rejected_outside_official_mines": len(box_segments) - len(segments),
        "exact_segment_series_count": len(assessments),
        "classification_counts": dict(sorted(counts.items())),
        "raw_step_up_segment_count": raw_steps,
        "surviving_step_cluster_count": len(clusters),
        "candidate_output_truncated": len(clusters) > candidate_limit,
        "surviving_step_clusters": mapped,
        "polygon_constraint": {
            "source_layer": FDEP_LAYER_URL,
            "source_description": "FDEP Mandatory Phosphate 2021 - Mine Boundaries",
            "official_feature_count": len(active_mines["features"]),
            "official_mine_names": _mine_names(active_mines),
            "every_retained_segment_inside_official_polygon": True,
            "polygon_geojson": str(region_dir / "fdep_active_mines.geojson"),
        },
        "interpretation": {
            "terrain_not_canopy_height": True,
            "official_polygon_constraint_applied_before_scanning": True,
            "records_needed_only_for_finalized_survivors": True,
            "cause_confirmed": False,
            "candidate_is_depth_anchor": False,
            "app_behavior_changed": False,
        },
        "does_not_prove": [
            "engineered_fill",
            "placed_material_thickness",
            "depth_to_a_buried_object",
            "radar_depth_prediction",
            "spatial_transfer_beyond_the_laser_strip",
        ],
    }
    (region_dir / "region_scan.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (region_dir / "candidates.geojson").write_text(
        json.dumps(_geojson(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _summary(
    *,
    campaign_dir: Path,
    region_result: dict[str, object],
) -> dict[str, object]:
    candidates = _candidate_rows(
        CAMPAIGN_ID,
        REGION_ID,
        region_result.get("surviving_step_clusters"),
    )
    ranked = rank_candidates(candidates)
    for index, item in enumerate(ranked, start=1):
        item["campaign_rank"] = index
    failed_tiles = int(region_result.get("failed_tile_count", 0) or 0)
    status = (
        "polygon_constrained_candidates_found"
        if ranked
        else (
            "polygon_constrained_scan_incomplete"
            if failed_tiles
            else "no_surviving_candidates_in_polygon_constrained_campaign"
        )
    )
    summary = {
        "schema": SUMMARY_SCHEMA,
        "status": status,
        "campaign_id": CAMPAIGN_ID,
        "campaign_description": CAMPAIGN_DESCRIPTION,
        "output_directory": str(campaign_dir),
        "selected_region_count": 1,
        "failed_tile_count": failed_tiles,
        "surviving_candidate_count": len(ranked),
        "record_lookup_priority": ranked,
        "region_summaries": [
            {
                "region_id": REGION_ID,
                "status": region_result.get("status"),
                "bounding_box_tile_count": region_result.get("bounding_box_tile_count"),
                "tile_count": region_result.get("tile_count"),
                "cached_tile_count": region_result.get("cached_tile_count"),
                "completed_tile_count": region_result.get("completed_tile_count"),
                "failed_tile_count": region_result.get("failed_tile_count"),
                "quality_segment_count_before_polygon_filter": region_result.get(
                    "quality_segment_count_before_polygon_filter"
                ),
                "quality_segment_count_after_deduplication": region_result.get(
                    "quality_segment_count_after_deduplication"
                ),
                "segments_rejected_outside_official_mines": region_result.get(
                    "segments_rejected_outside_official_mines"
                ),
                "exact_segment_series_count": region_result.get(
                    "exact_segment_series_count"
                ),
                "classification_counts": region_result.get(
                    "classification_counts", {}
                ),
                "raw_step_up_segment_count": region_result.get(
                    "raw_step_up_segment_count", 0
                ),
                "surviving_step_cluster_count": region_result.get(
                    "surviving_step_cluster_count", 0
                ),
                "result_json": str(campaign_dir / REGION_ID / "region_scan.json"),
                "result_geojson": str(campaign_dir / REGION_ID / "candidates.geojson"),
                "official_polygon_geojson": str(
                    campaign_dir / REGION_ID / "fdep_active_mines.geojson"
                ),
            }
        ],
        "record_lookup_priority_is_provisional": True,
        "records_research_ready": False,
        "numerical_depth_unlocked": False,
        "interpretation": {
            "every_retained_segment_inside_official_active_mine_polygon": True,
            "records_needed_only_for_finalized_survivors": True,
            "candidate_cause_confirmed": False,
            "candidate_is_depth_anchor": False,
            "app_behavior_changed": False,
        },
        "does_not_prove": [
            "engineered_fill",
            "placed_material_thickness",
            "depth_to_a_buried_object",
            "radar_depth_prediction",
            "spatial_transfer_beyond_the_laser_strip",
        ],
    }
    (campaign_dir / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def run_campaign(
    *,
    output_root: Path,
    west: float,
    south: float,
    east: float,
    north: float,
    start: str,
    end: str,
    tile_size_m: float,
    tile_overlap_m: float,
    force: bool,
    continue_on_error: bool,
    timeout_seconds: float,
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
    fetch_json: FetchJson = _default_fetch_json,
) -> dict[str, object]:
    region = RegionSpec(
        region_id=REGION_ID,
        description=REGION_DESCRIPTION,
        west=west,
        south=south,
        east=east,
        north=north,
    )
    active_mines = fetch_active_mines(
        west=west,
        south=south,
        east=east,
        north=north,
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
    )
    campaign_dir = output_root / CAMPAIGN_ID
    campaign_dir.mkdir(parents=True, exist_ok=True)
    result = _region_result(
        campaign_dir=campaign_dir,
        region=region,
        active_mines=active_mines,
        start=start,
        end=end,
        tile_size_m=tile_size_m,
        tile_overlap_m=tile_overlap_m,
        force=force,
        continue_on_error=continue_on_error,
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
        candidate_limit=candidate_limit,
    )
    return _summary(campaign_dir=campaign_dir, region_result=result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Campaign 007 inside official FDEP active-mine polygons."
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--west", type=float, default=DEFAULT_BOUNDS[0])
    parser.add_argument("--south", type=float, default=DEFAULT_BOUNDS[1])
    parser.add_argument("--east", type=float, default=DEFAULT_BOUNDS[2])
    parser.add_argument("--north", type=float, default=DEFAULT_BOUNDS[3])
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--tile-km", type=float, default=25.0)
    parser.add_argument("--tile-overlap-m", type=float, default=100.0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--stop-on-tile-error", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
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
    parser.add_argument("--candidate-limit", type=int, default=20)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        result = run_campaign(
            output_root=args.output_root,
            west=args.west,
            south=args.south,
            east=args.east,
            north=args.north,
            start=args.start,
            end=args.end,
            tile_size_m=float(args.tile_km) * 1000.0,
            tile_overlap_m=args.tile_overlap_m,
            force=args.force,
            continue_on_error=not args.stop_on_tile_error,
            timeout_seconds=args.timeout_seconds,
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
            candidate_limit=args.candidate_limit,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "fdep_polygon_campaign_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if int(result["failed_tile_count"]) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
