"""Run Campaign 014 inside the EPA Hidden Lane Landfill Superfund polygon.

Campaign 014 targets EPA ID VAD980829030 (Hidden Lane Landfill, Sterling, VA)
and requires any spatially supported ATL08 upward-step cluster to overlap the
EPA-documented OU3 LANDFILL CAP - SOURCE AREA remedial-action window from
2023-09-11 through 2025-11-06.

The EPA polygon and construction window are spatial/timing evidence only. They
are not treated as measured thickness, depth, exact cap as-built geometry, or
proof of radar transferability. Existing repeat-series, neighbour, cluster,
context, finalizer, terminal-stability, temporal-recovery, and evidence gates
remain unchanged.
"""

from __future__ import annotations

import copy
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import scan_icesat2_fdep_polygon_campaign as campaign
from scan_icesat2_fdep_polygon_campaign_fixed import tile_bbox_wgs84
from scan_icesat2_fdep_recent_released_units_campaign import (
    _ORIGINAL_REGION_RESULT,
    _ORIGINAL_SUMMARY,
)

CAMPAIGN_ID = "mid_atlantic_earthwork_pilot_v14_epa_hidden_lane_recent_earthwork"
CAMPAIGN_DESCRIPTION = (
    "Fourteenth independent ATL08 terrain-step campaign constrained to the "
    "official EPA Hidden Lane Landfill Superfund polygon, with final clusters "
    "required to overlap the documented 2023-09-11 through 2025-11-06 OU3 "
    "landfill-cap/source-area remedial-action window."
)
REGION_ID = "epa_hidden_lane_landfill_recent_ou3_earthwork"
REGION_DESCRIPTION = (
    "EPA Hidden Lane Landfill Superfund site (VAD980829030), Sterling, Virginia; "
    "ATL08 segments are constrained to the official site polygon and cluster "
    "transitions must overlap the documented OU3 recent-earthwork window."
)
EPA_SUPERFUND_LAYER_URL = (
    "https://geopub.epa.gov/ArcGIS/rest/services/NEPAssist/"
    "NEPAVELayersPublic_fgdb/MapServer/14/query"
)
TARGET_EPA_ID = "VAD980829030"
TARGET_SITE_NAME = "HIDDEN LANE LANDFILL"
EARTHWORK_START = datetime(2023, 9, 11, tzinfo=UTC)
EARTHWORK_END = datetime(2025, 11, 6, 23, 59, 59, tzinfo=UTC)
DEFAULT_BOUNDS = (-77.70, 38.80, -77.10, 39.20)
POLYGON_CACHE_SCHEMA = "icesat2_epa_hidden_lane_recent_earthwork_tile_cache_v1"
EPA_GEOJSON_FILENAME = "epa_hidden_lane_superfund_boundary.geojson"
MINIMUM_ENVELOPE_SPAN_M = 40.0

FetchJson = Callable[[str, dict[str, str], float], dict[str, Any]]


def _property(feature: dict[str, Any], *names: str) -> object:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return None
    for name in names:
        if name in properties:
            return properties.get(name)
    return None


def _normal_text(value: object) -> str | None:
    if value in (None, ""):
        return None
    text = " ".join(str(value).strip().upper().split())
    return text or None


def _epa_id(feature: dict[str, Any]) -> str | None:
    return _normal_text(_property(feature, "EPA_ID", "epa_id"))


def _site_name(feature: dict[str, Any]) -> str | None:
    return _normal_text(_property(feature, "Site_Name", "SITE_NAME", "site_name"))


def _finite_pair(value: object) -> tuple[float, float] | None:
    if (
        not isinstance(value, (list, tuple))
        or len(value) < 2
        or not isinstance(value[0], (int, float))
        or not isinstance(value[1], (int, float))
    ):
        return None
    longitude = float(value[0])
    latitude = float(value[1])
    if not math.isfinite(longitude) or not math.isfinite(latitude):
        return None
    return longitude, latitude


def _raw_polygon_span_m(raw_polygon: object) -> tuple[float, float] | None:
    if not isinstance(raw_polygon, list):
        return None
    points: list[tuple[float, float]] = []
    for raw_ring in raw_polygon:
        if not isinstance(raw_ring, list):
            continue
        for raw_point in raw_ring:
            pair = _finite_pair(raw_point)
            if pair is not None:
                points.append(pair)
    if len(points) < 3:
        return None
    longitudes = [item[0] for item in points]
    latitudes = [item[1] for item in points]
    west = min(longitudes)
    east = max(longitudes)
    south = min(latitudes)
    north = max(latitudes)
    mid_latitude = math.radians((south + north) / 2.0)
    east_west_m = abs(east - west) * 111_320.0 * max(0.01, math.cos(mid_latitude))
    north_south_m = abs(north - south) * 110_540.0
    return east_west_m, north_south_m


def _filtered_geometry(geometry: object) -> dict[str, Any] | None:
    """Retain only components that can contain the existing ~40 m footprint."""

    if not isinstance(geometry, dict):
        return None
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if geometry_type == "Polygon":
        span = _raw_polygon_span_m(coordinates)
        if span is None or min(span) < MINIMUM_ENVELOPE_SPAN_M:
            return None
        return copy.deepcopy(geometry)

    if geometry_type != "MultiPolygon" or not isinstance(coordinates, list):
        return None

    retained: list[object] = []
    for raw_polygon in coordinates:
        span = _raw_polygon_span_m(raw_polygon)
        if span is not None and min(span) >= MINIMUM_ENVELOPE_SPAN_M:
            retained.append(copy.deepcopy(raw_polygon))
    if not retained:
        return None
    if len(retained) == 1:
        return {"type": "Polygon", "coordinates": retained[0]}
    return {"type": "MultiPolygon", "coordinates": retained}


def fetch_hidden_lane_polygon(
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    timeout_seconds: float,
    fetch_json: FetchJson = campaign._default_fetch_json,
) -> dict[str, Any]:
    """Fetch the exact official EPA Superfund feature for Hidden Lane Landfill."""

    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("invalid WGS84 bounds")

    payload = fetch_json(
        EPA_SUPERFUND_LAYER_URL,
        {
            "where": f"EPA_ID = '{TARGET_EPA_ID}'",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "resultRecordCount": "10",
            "f": "geojson",
        },
        timeout_seconds,
    )
    if payload.get("type") != "FeatureCollection":
        raise ValueError("EPA response is not a GeoJSON FeatureCollection")
    raw_features = payload.get("features")
    if not isinstance(raw_features, list):
        raise ValueError("EPA FeatureCollection has no features list")

    retained: list[dict[str, Any]] = []
    diagnostics = {
        "raw_feature_count": len(raw_features),
        "wrong_epa_id": 0,
        "missing_or_small_geometry": 0,
        "retained_feature_count": 0,
    }
    for raw_feature in raw_features:
        if not isinstance(raw_feature, dict):
            continue
        if _epa_id(raw_feature) != TARGET_EPA_ID:
            diagnostics["wrong_epa_id"] += 1
            continue
        geometry = _filtered_geometry(raw_feature.get("geometry"))
        if geometry is None:
            diagnostics["missing_or_small_geometry"] += 1
            continue
        feature = copy.deepcopy(raw_feature)
        feature["geometry"] = geometry
        properties = feature.get("properties")
        if isinstance(properties, dict):
            properties["CAMPAIGN_EPA_ID"] = TARGET_EPA_ID
            properties["CAMPAIGN_EVENT_START"] = EARTHWORK_START.date().isoformat()
            properties["CAMPAIGN_EVENT_END"] = EARTHWORK_END.date().isoformat()
            properties["CAMPAIGN_MINIMUM_ENVELOPE_SPAN_M"] = MINIMUM_ENVELOPE_SPAN_M
        retained.append(feature)

    diagnostics["retained_feature_count"] = len(retained)
    if not retained:
        raise ValueError(
            "no usable official EPA Hidden Lane Landfill polygon; "
            + json.dumps(diagnostics, sort_keys=True)
        )
    return {
        "type": "FeatureCollection",
        "features": retained,
        "campaign_source_diagnostics": diagnostics,
    }


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def cluster_overlaps_earthwork_window(cluster: dict[str, Any]) -> bool:
    event_start = _parse_datetime(cluster.get("event_start"))
    event_end = _parse_datetime(cluster.get("event_end"))
    if event_start is None or event_end is None or event_end < event_start:
        return False
    return event_end >= EARTHWORK_START and event_start <= EARTHWORK_END


def filter_clusters_to_earthwork_window(
    clusters: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    survivors: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    for cluster in clusters:
        if not cluster_overlaps_earthwork_window(cluster):
            rejections.append(
                {
                    "reason": "transition_outside_epa_ou3_earthwork_window",
                    "event_start": cluster.get("event_start"),
                    "event_end": cluster.get("event_end"),
                    "centroid_longitude": cluster.get("centroid_longitude"),
                    "centroid_latitude": cluster.get("centroid_latitude"),
                    "median_step_m": cluster.get("median_step_m"),
                    "segment_count": cluster.get("segment_count"),
                }
            )
            continue
        item = dict(cluster)
        item["official_epa_hidden_lane_event"] = {
            "epa_id": TARGET_EPA_ID,
            "site_name": TARGET_SITE_NAME.title(),
            "operable_unit": "OU3 - LANDFILL CAP - SOURCE AREA",
            "remedial_action_start": EARTHWORK_START.date().isoformat(),
            "remedial_action_end": EARTHWORK_END.date().isoformat(),
            "event_window_is_not_depth": True,
        }
        survivors.append(item)
    return survivors, rejections


def _site_labels(feature_collection: dict[str, Any]) -> list[str]:
    values = feature_collection.get("features")
    if not isinstance(values, list):
        return []
    labels: set[str] = set()
    for feature in values:
        if not isinstance(feature, dict):
            continue
        epa_id = _epa_id(feature)
        name = _site_name(feature)
        if epa_id:
            labels.add(f"{epa_id} | {name or ''}".rstrip())
    return sorted(labels)


def _region_result(**kwargs) -> dict[str, object]:
    official_site = kwargs["active_mines"]
    result = _ORIGINAL_REGION_RESULT(**kwargs)
    raw_clusters = result.get("surviving_step_clusters")
    clusters = (
        [item for item in raw_clusters if isinstance(item, dict)]
        if isinstance(raw_clusters, list)
        else []
    )
    survivors, rejections = filter_clusters_to_earthwork_window(clusters)

    result["pre_event_window_cluster_count"] = len(clusters)
    result["event_window_rejected_count"] = len(rejections)
    result["event_window_rejections"] = rejections
    result["surviving_step_cluster_count"] = len(survivors)
    result["surviving_step_clusters"] = survivors
    result["segments_rejected_outside_epa_hidden_lane_polygon"] = result.get(
        "segments_rejected_outside_official_mines", 0
    )

    if survivors:
        result["status"] = "spatial_steps_overlapping_epa_hidden_lane_ou3_earthwork"
    elif clusters:
        result["status"] = "clusters_rejected_outside_epa_hidden_lane_ou3_earthwork_window"
    else:
        result["status"] = "no_persistent_upward_steps_inside_epa_hidden_lane_polygon"

    campaign_dir = Path(kwargs["campaign_dir"])
    region = kwargs["region"]
    region_dir = campaign_dir / region.region_id
    polygon_geojson = region_dir / EPA_GEOJSON_FILENAME
    polygon_geojson.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": official_site.get("features", []),
                "campaign_source_diagnostics": official_site.get(
                    "campaign_source_diagnostics", {}
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    constraint = result.get("polygon_constraint")
    if not isinstance(constraint, dict):
        constraint = {}
        result["polygon_constraint"] = constraint
    constraint.pop("official_mine_names", None)
    constraint.update(
        {
            "source_layer": EPA_SUPERFUND_LAYER_URL,
            "source_description": "EPA national Superfund site boundary",
            "target_epa_id": TARGET_EPA_ID,
            "target_site_name": TARGET_SITE_NAME.title(),
            "minimum_component_envelope_span_m": MINIMUM_ENVELOPE_SPAN_M,
            "official_feature_count": len(official_site.get("features", [])),
            "official_site_labels": _site_labels(official_site),
            "every_retained_segment_inside_official_epa_polygon": True,
            "polygon_geojson": str(polygon_geojson),
        }
    )

    interpretation = result.get("interpretation")
    if not isinstance(interpretation, dict):
        interpretation = {}
        result["interpretation"] = interpretation
    interpretation.pop("official_polygon_constraint_applied_before_scanning", None)
    interpretation.update(
        {
            "epa_hidden_lane_polygon_constraint_applied": True,
            "epa_ou3_event_window_gate_applied_after_clustering": True,
            "epa_ou3_event_start": EARTHWORK_START.date().isoformat(),
            "epa_ou3_event_end": EARTHWORK_END.date().isoformat(),
            "event_window_is_not_measured_thickness": True,
            "site_boundary_is_not_exact_cap_asbuilt_geometry": True,
            "forty_meter_envelope_screen_does_not_prove_clean_width": True,
            "cause_confirmed": False,
            "candidate_is_depth_anchor": False,
            "app_behavior_changed": False,
        }
    )

    (region_dir / "region_scan.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (region_dir / "candidates.geojson").write_text(
        json.dumps(campaign._geojson(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _candidate_cluster_match(
    candidate: dict[str, Any], clusters: list[dict[str, Any]]
) -> dict[str, Any] | None:
    latitude = candidate.get("latitude")
    longitude = candidate.get("longitude")
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return None
    for cluster in clusters:
        cluster_lat = cluster.get("centroid_latitude")
        cluster_lon = cluster.get("centroid_longitude")
        if not isinstance(cluster_lat, (int, float)) or not isinstance(cluster_lon, (int, float)):
            continue
        if abs(float(latitude) - float(cluster_lat)) <= 1e-8 and abs(
            float(longitude) - float(cluster_lon)
        ) <= 1e-8:
            return cluster
    return None


def _summary(**kwargs) -> dict[str, object]:
    summary = _ORIGINAL_SUMMARY(**kwargs)
    region_result = kwargs["region_result"]
    raw_clusters = region_result.get("surviving_step_clusters")
    clusters = (
        [item for item in raw_clusters if isinstance(item, dict)]
        if isinstance(raw_clusters, list)
        else []
    )

    priorities = summary.get("record_lookup_priority")
    if isinstance(priorities, list):
        for candidate in priorities:
            if not isinstance(candidate, dict):
                continue
            match = _candidate_cluster_match(candidate, clusters)
            if match is not None and isinstance(match.get("official_epa_hidden_lane_event"), dict):
                candidate["official_epa_hidden_lane_event"] = dict(
                    match["official_epa_hidden_lane_event"]
                )

    failed_tiles = int(summary.get("failed_tile_count", 0) or 0)
    candidate_count = int(summary.get("surviving_candidate_count", 0) or 0)
    summary["status"] = (
        "epa_hidden_lane_recent_earthwork_candidates_found"
        if candidate_count
        else (
            "epa_hidden_lane_recent_earthwork_scan_incomplete"
            if failed_tiles
            else "no_surviving_candidates_in_epa_hidden_lane_recent_earthwork"
        )
    )
    summary["target_epa_id"] = TARGET_EPA_ID
    summary["target_site_name"] = TARGET_SITE_NAME.title()
    summary["ou3_earthwork_start"] = EARTHWORK_START.date().isoformat()
    summary["ou3_earthwork_end"] = EARTHWORK_END.date().isoformat()
    summary["minimum_component_envelope_span_m"] = MINIMUM_ENVELOPE_SPAN_M
    summary["pre_event_window_cluster_count"] = region_result.get(
        "pre_event_window_cluster_count", 0
    )
    summary["event_window_rejected_count"] = region_result.get(
        "event_window_rejected_count", 0
    )
    summary["records_research_ready"] = False
    summary["numerical_depth_unlocked"] = False
    summary["record_lookup_priority_is_provisional"] = True

    region_summaries = summary.get("region_summaries")
    if isinstance(region_summaries, list) and region_summaries:
        first = region_summaries[0]
        if isinstance(first, dict):
            first["pre_event_window_cluster_count"] = region_result.get(
                "pre_event_window_cluster_count", 0
            )
            first["event_window_rejected_count"] = region_result.get(
                "event_window_rejected_count", 0
            )
            first["segments_rejected_outside_epa_hidden_lane_polygon"] = (
                region_result.get("segments_rejected_outside_epa_hidden_lane_polygon", 0)
            )
            first["official_polygon_geojson"] = str(
                Path(summary["output_directory"]) / REGION_ID / EPA_GEOJSON_FILENAME
            )

    interpretation = summary.get("interpretation")
    if not isinstance(interpretation, dict):
        interpretation = {}
        summary["interpretation"] = interpretation
    interpretation.pop("every_retained_segment_inside_official_active_mine_polygon", None)
    interpretation.update(
        {
            "every_retained_segment_inside_epa_hidden_lane_polygon": True,
            "every_candidate_cluster_overlaps_epa_ou3_earthwork_window": True,
            "epa_ou3_event_window_is_not_depth": True,
            "exact_cap_asbuilt_geometry_still_required_for_anchor": True,
            "records_needed_only_for_finalized_survivors": True,
            "candidate_cause_confirmed": False,
            "candidate_is_depth_anchor": False,
            "app_behavior_changed": False,
        }
    )

    campaign_dir = Path(summary["output_directory"])
    (campaign_dir / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def install_campaign() -> None:
    campaign.CAMPAIGN_ID = CAMPAIGN_ID
    campaign.CAMPAIGN_DESCRIPTION = CAMPAIGN_DESCRIPTION
    campaign.REGION_ID = REGION_ID
    campaign.REGION_DESCRIPTION = REGION_DESCRIPTION
    campaign.FDEP_LAYER_URL = EPA_SUPERFUND_LAYER_URL
    campaign.DEFAULT_BOUNDS = DEFAULT_BOUNDS
    campaign.POLYGON_CACHE_SCHEMA = POLYGON_CACHE_SCHEMA
    campaign._tile_bbox_wgs84 = tile_bbox_wgs84
    campaign.fetch_active_mines = fetch_hidden_lane_polygon
    campaign._mine_names = _site_labels
    campaign._region_result = _region_result
    campaign._summary = _summary


def main() -> int:
    install_campaign()
    return campaign.main()


if __name__ == "__main__":
    raise SystemExit(main())
