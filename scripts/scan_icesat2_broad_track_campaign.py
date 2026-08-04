"""Run a resumable broad ICESat-2 ATL08 terrain-step campaign.

This private research tool scans explicit WGS84 boxes outside the existing app
AOIs. It caches normalized ATL08 terrain segments per tile and keeps only
persistent upward-step clusters with neighbouring-segment support. It does not
create depth anchors, invoke the depth engine, or modify the app.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence

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
    _query_atl08,
    _segments_from_frame,
)
from scan_all_icesat2_terrain_steps import rank_candidates
from scan_icesat2_regional_expansion import (
    QueryTile,
    _tile_polygon_wgs84,
    deduplicate_segments,
)
from scan_icesat2_terrain_steps import _cluster_mapping, _geojson

CONFIG_SCHEMA = "icesat2_broad_track_campaign_config_v1"
SUMMARY_SCHEMA = "icesat2_broad_track_campaign_scan_v1"
REGION_SCHEMA = "icesat2_broad_track_region_scan_v1"
CACHE_SCHEMA = "icesat2_broad_track_tile_cache_v1"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
DEFAULT_CONFIG = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "icesat2_broad_track_campaign_v1.json"
)
DEFAULT_OUTPUT_ROOT = Path("./data/research/icesat2_broad_track_scan")


@dataclass(frozen=True, slots=True)
class RegionSpec:
    region_id: str
    description: str
    west: float
    south: float
    east: float
    north: float


@dataclass(frozen=True, slots=True)
class CampaignSpec:
    campaign_id: str
    description: str
    regions: tuple[RegionSpec, ...]


def _number(value: object, field: str) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{field} must be a finite number")
    return float(value)


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValueError(f"{field} has invalid characters")
    return value


def load_campaign(path: Path) -> CampaignSpec:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read campaign file: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != CONFIG_SCHEMA:
        raise ValueError("campaign configuration schema is not supported")
    campaign_id = _identifier(payload.get("campaign_id"), "campaign_id")
    description = payload.get("description", "")
    if not isinstance(description, str):
        raise ValueError("campaign description must be text")
    raw_regions = payload.get("regions")
    if not isinstance(raw_regions, list):
        raise ValueError("campaign regions must be a list")

    regions: list[RegionSpec] = []
    seen: set[str] = set()
    for raw in raw_regions:
        if not isinstance(raw, dict):
            raise ValueError("each campaign region must be an object")
        if raw.get("enabled", True) is False:
            continue
        region_id = _identifier(raw.get("region_id"), "region_id")
        if region_id in seen:
            raise ValueError(f"duplicate region_id: {region_id}")
        seen.add(region_id)
        description_value = raw.get("description", "")
        if not isinstance(description_value, str):
            raise ValueError(f"{region_id}.description must be text")
        west = _number(raw.get("west"), f"{region_id}.west")
        south = _number(raw.get("south"), f"{region_id}.south")
        east = _number(raw.get("east"), f"{region_id}.east")
        north = _number(raw.get("north"), f"{region_id}.north")
        if not (-180.0 <= west < east <= 180.0):
            raise ValueError(f"{region_id} longitude bounds are invalid")
        if not (-80.0 <= south < north <= 84.0):
            raise ValueError(f"{region_id} latitude bounds are outside UTM")
        if east - west > 6.0 or north - south > 6.0:
            raise ValueError(f"{region_id} is too large for one UTM region")
        regions.append(
            RegionSpec(
                region_id=region_id,
                description=description_value,
                west=west,
                south=south,
                east=east,
                north=north,
            )
        )
    if not regions:
        raise ValueError("campaign has no enabled regions")
    return CampaignSpec(campaign_id, description, tuple(regions))


def utm_epsg(longitude: float, latitude: float) -> int:
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError("longitude is outside WGS84")
    if not (-80.0 <= latitude <= 84.0):
        raise ValueError("latitude is outside UTM")
    zone = int(math.floor((min(longitude, 179.999999) + 180.0) / 6.0)) + 1
    zone = min(max(zone, 1), 60)
    return (32600 if latitude >= 0.0 else 32700) + zone


def build_tiles(
    region: RegionSpec,
    *,
    tile_size_m: float,
    overlap_m: float,
) -> tuple[int, list[QueryTile]]:
    if tile_size_m <= 0:
        raise ValueError("tile_size_m must be positive")
    if overlap_m < 0 or overlap_m * 2 >= tile_size_m:
        raise ValueError("tile overlap is invalid")

    center_lon = (region.west + region.east) / 2.0
    center_lat = (region.south + region.north) / 2.0
    epsg = utm_epsg(center_lon, center_lat)
    to_local = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    corners = (
        (region.west, region.south),
        (region.east, region.south),
        (region.east, region.north),
        (region.west, region.north),
    )
    projected = [to_local.transform(lon, lat) for lon, lat in corners]
    xmin = min(float(item[0]) for item in projected)
    ymin = min(float(item[1]) for item in projected)
    xmax = max(float(item[0]) for item in projected)
    ymax = max(float(item[1]) for item in projected)

    tiles: list[QueryTile] = []
    row = 0
    y0 = ymin
    while y0 < ymax:
        y1 = min(y0 + tile_size_m, ymax)
        column = 0
        x0 = xmin
        while x0 < xmax:
            x1 = min(x0 + tile_size_m, xmax)
            qxmin = max(xmin, x0 - overlap_m)
            qymin = max(ymin, y0 - overlap_m)
            qxmax = min(xmax, x1 + overlap_m)
            qymax = min(ymax, y1 + overlap_m)
            tile_id = f"r{row:03d}_c{column:03d}"
            tiles.append(
                QueryTile(
                    tile_id=tile_id,
                    xmin=qxmin,
                    ymin=qymin,
                    xmax=qxmax,
                    ymax=qymax,
                    polygon_wgs84=_tile_polygon_wgs84(
                        epsg=epsg,
                        xmin=qxmin,
                        ymin=qymin,
                        xmax=qxmax,
                        ymax=qymax,
                    ),
                )
            )
            column += 1
            x0 = x1
        row += 1
        y0 = y1
    return epsg, tiles


def _segment_json(item: Icesat2Segment) -> dict[str, object]:
    return {
        "segment_id": item.segment_id,
        "observed_at": item.observed_at.isoformat(),
        "longitude": item.longitude,
        "latitude": item.latitude,
        "x_m": item.x_m,
        "y_m": item.y_m,
        "height_m": item.height_m,
        "height_uncertainty_m": item.height_uncertainty_m,
        "terrain_slope": item.terrain_slope,
        "ground_photon_count": item.ground_photon_count,
        "rgt": item.rgt,
        "cycle": item.cycle,
        "spot": item.spot,
        "gt": item.gt,
    }


def _segment_from_json(item: object) -> Icesat2Segment:
    if not isinstance(item, dict):
        raise ValueError("cached segment must be an object")
    observed_at = datetime.fromisoformat(str(item["observed_at"]))
    if observed_at.tzinfo is None:
        raise ValueError("cached timestamp must include a timezone")
    return Icesat2Segment(
        segment_id=str(item["segment_id"]),
        observed_at=observed_at,
        longitude=float(item["longitude"]),
        latitude=float(item["latitude"]),
        x_m=float(item["x_m"]),
        y_m=float(item["y_m"]),
        height_m=float(item["height_m"]),
        height_uncertainty_m=(
            None
            if item.get("height_uncertainty_m") is None
            else float(item["height_uncertainty_m"])
        ),
        terrain_slope=(
            None
            if item.get("terrain_slope") is None
            else float(item["terrain_slope"])
        ),
        ground_photon_count=int(item["ground_photon_count"]),
        rgt=int(item["rgt"]),
        cycle=int(item["cycle"]),
        spot=int(item["spot"]),
        gt=str(item["gt"]),
    )


def _signature(
    region_id: str,
    tile_id: str,
    start: str,
    end: str,
    epsg: int,
    minimum_ground_photons: int,
    maximum_uncertainty_m: float | None,
) -> dict[str, object]:
    return {
        "region_id": region_id,
        "tile_id": tile_id,
        "query_start": start,
        "query_end": end,
        "epsg": epsg,
        "minimum_ground_photons": minimum_ground_photons,
        "maximum_uncertainty_m": maximum_uncertainty_m,
    }


def read_cache(
    path: Path,
    expected: dict[str, object],
) -> list[Icesat2Segment] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != CACHE_SCHEMA
            or payload.get("signature") != expected
            or not isinstance(payload.get("segments"), list)
        ):
            return None
        return [_segment_from_json(item) for item in payload["segments"]]
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def write_cache(
    path: Path,
    signature: dict[str, object],
    segments: Sequence[Icesat2Segment],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": CACHE_SCHEMA,
                "signature": signature,
                "segment_count": len(segments),
                "segments": [_segment_json(item) for item in segments],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _inside(item: Icesat2Segment, region: RegionSpec) -> bool:
    return (
        region.west <= item.longitude <= region.east
        and region.south <= item.latitude <= region.north
    )


def scan_region(
    *,
    campaign_id: str,
    region: RegionSpec,
    campaign_dir: Path,
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
    epsg, tiles = build_tiles(
        region,
        tile_size_m=tile_size_m,
        overlap_m=tile_overlap_m,
    )
    region_dir = campaign_dir / region.region_id
    tile_dir = region_dir / "tiles"
    all_segments: list[Icesat2Segment] = []
    failures: list[dict[str, object]] = []
    cached_tile_count = 0

    for position, tile in enumerate(tiles, start=1):
        print(
            f"    tile {position}/{len(tiles)} {tile.tile_id}",
            file=sys.stderr,
            flush=True,
        )
        signature = _signature(
            region.region_id,
            tile.tile_id,
            start,
            end,
            epsg,
            minimum_ground_photons,
            maximum_uncertainty_m,
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
            except Exception as exc:  # noqa: BLE001 - keep successful tile caches
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

    segments = [
        item for item in deduplicate_segments(all_segments) if _inside(item, region)
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
        status = "no_quality_atl08_segments"
    elif not raw_steps:
        status = "no_persistent_upward_steps"
    elif not clusters:
        status = "isolated_steps_rejected_by_neighbor_filter"
    else:
        status = "spatially_supported_step_candidates_found"

    result = {
        "schema": REGION_SCHEMA,
        "status": status,
        "campaign_id": campaign_id,
        "region_id": region.region_id,
        "description": region.description,
        "bounds_wgs84": {
            "west": region.west,
            "south": region.south,
            "east": region.east,
            "north": region.north,
        },
        "analysis_epsg": epsg,
        "tile_count": len(tiles),
        "cached_tile_count": cached_tile_count,
        "completed_tile_count": len(tiles) - len(failures),
        "failed_tile_count": len(failures),
        "tile_failures": failures,
        "quality_segment_count_after_deduplication": len(segments),
        "exact_segment_series_count": len(assessments),
        "classification_counts": dict(sorted(counts.items())),
        "raw_step_up_segment_count": raw_steps,
        "surviving_step_cluster_count": len(clusters),
        "candidate_output_truncated": len(clusters) > candidate_limit,
        "surviving_step_clusters": mapped,
        "interpretation": {
            "terrain_not_canopy_height": True,
            "records_needed_only_for_survivors": True,
            "cause_confirmed": False,
            "candidate_is_depth_anchor": False,
            "private_resumable_tile_cache": True,
        },
        "does_not_prove": [
            "engineered_fill",
            "placed_material_thickness",
            "depth_to_a_buried_object",
            "radar_depth_prediction",
            "spatial_transfer_beyond_the_laser_strip",
        ],
    }
    region_dir.mkdir(parents=True, exist_ok=True)
    (region_dir / "region_scan.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (region_dir / "candidates.geojson").write_text(
        json.dumps(_geojson(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _candidate_rows(
    campaign_id: str,
    region_id: str,
    clusters: object,
) -> list[dict[str, object]]:
    if not isinstance(clusters, list):
        return []
    rows: list[dict[str, object]] = []
    for local_rank, item in enumerate(clusters, start=1):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "campaign_id": campaign_id,
                "region_id": region_id,
                "region_local_rank": local_rank,
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
            }
        )
    return rows


def scan_campaign(
    *,
    campaign: CampaignSpec,
    output_root: Path,
    selected_region_ids: Sequence[str],
    start: str,
    end: str,
    tile_size_m: float,
    tile_overlap_m: float,
    force: bool,
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
    candidate_limit_per_region: int = 20,
) -> dict[str, object]:
    requested = set(selected_region_ids)
    known = {item.region_id for item in campaign.regions}
    unknown = sorted(requested - known)
    if unknown:
        raise ValueError(f"unknown campaign region(s): {', '.join(unknown)}")
    regions = [
        item
        for item in campaign.regions
        if not requested or item.region_id in requested
    ]

    campaign_dir = output_root / campaign.campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    failed_tiles = 0
    for position, region in enumerate(regions, start=1):
        print(
            f"[{position}/{len(regions)}] scanning {region.region_id}",
            file=sys.stderr,
            flush=True,
        )
        result = scan_region(
            campaign_id=campaign.campaign_id,
            region=region,
            campaign_dir=campaign_dir,
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
            candidate_limit=candidate_limit_per_region,
        )
        failed_tiles += int(result["failed_tile_count"])
        candidates.extend(
            _candidate_rows(
                campaign.campaign_id,
                region.region_id,
                result.get("surviving_step_clusters"),
            )
        )
        summaries.append(
            {
                "region_id": region.region_id,
                "status": result.get("status"),
                "tile_count": result.get("tile_count"),
                "cached_tile_count": result.get("cached_tile_count"),
                "completed_tile_count": result.get("completed_tile_count"),
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
                "result_json": str(
                    campaign_dir / region.region_id / "region_scan.json"
                ),
                "result_geojson": str(
                    campaign_dir / region.region_id / "candidates.geojson"
                ),
            }
        )

    ranked = rank_candidates(candidates)
    for index, item in enumerate(ranked, start=1):
        item["campaign_rank"] = index
    status = (
        "broad_track_candidates_found"
        if ranked
        else (
            "broad_track_scan_incomplete_no_candidates_yet"
            if failed_tiles
            else "no_surviving_candidates_in_broad_track_campaign"
        )
    )
    summary = {
        "schema": SUMMARY_SCHEMA,
        "status": status,
        "campaign_id": campaign.campaign_id,
        "campaign_description": campaign.description,
        "output_directory": str(campaign_dir),
        "selected_region_count": len(regions),
        "failed_tile_count": failed_tiles,
        "surviving_candidate_count": len(ranked),
        "record_lookup_priority": ranked,
        "region_summaries": summaries,
        "interpretation": {
            "independent_of_existing_app_aois": True,
            "records_needed_only_for_ranked_survivors": True,
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a resumable broad ATL08 terrain-step campaign."
    )
    parser.add_argument("--campaign-file", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--region-id", action="append", default=None)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--tile-km", type=float, default=25.0)
    parser.add_argument("--tile-overlap-m", type=float, default=100.0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--stop-on-tile-error", action="store_true")
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
    parser.add_argument("--candidate-limit-per-region", type=int, default=20)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        result = scan_campaign(
            campaign=load_campaign(args.campaign_file),
            output_root=args.output_root,
            selected_region_ids=args.region_id or [],
            start=args.start,
            end=args.end,
            tile_size_m=float(args.tile_km) * 1000.0,
            tile_overlap_m=args.tile_overlap_m,
            force=args.force,
            continue_on_error=not args.stop_on_tile_error,
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
            candidate_limit_per_region=args.candidate_limit_per_region,
        )
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "broad_track_campaign_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if int(result["failed_tile_count"]) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
