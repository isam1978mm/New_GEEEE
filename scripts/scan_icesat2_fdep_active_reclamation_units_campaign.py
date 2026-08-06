"""Run Campaign 009 inside active FDEP reclamation units.

Campaign 007 used broad active-mine boundaries and its only finalized candidate
fell inside a future-work unit. Campaign 008 constrained the search to recently
released units, but all retained segment series lacked enough repeat epochs.
Campaign 009 instead targets exact official 2021 reclamation-unit polygons whose
FDEP status is Work in Progress (WP) or Work Complete (WC).

All existing temporal, stability, neighbour, cluster, context, terminal-
stability, and temporal-recovery thresholds remain unchanged. A surviving
cluster is still only a terrain-step candidate. It does not prove engineered
fill, placed-material thickness, buried-object depth, or radar transferability,
and it does not modify app artifacts.
"""

from __future__ import annotations

import json
import math
import sys
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

CAMPAIGN_ID = "southeast_us_earthwork_pilot_v9_fdep_active_reclamation_units"
CAMPAIGN_DESCRIPTION = (
    "Ninth independent ATL08 terrain-step campaign constrained to official "
    "FDEP 2021 mandatory-phosphate reclamation units marked Work in Progress "
    "or Work Complete, with all prior temporal, stability, context, and "
    "evidence gates preserved."
)
REGION_ID = "fdep_work_in_progress_complete_phosphate_units"
REGION_DESCRIPTION = (
    "Central Florida mandatory-phosphate reclamation units whose official "
    "2021 FDEP status is Work in Progress or Work Complete; tiles, ATL08 "
    "segments, and final clusters are constrained to exact named-unit geometry."
)
FDEP_ACTIVE_RECLAMATION_UNITS_LAYER_URL = (
    "https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/"
    "MMP_RECLUNITS/MapServer/9/query"
)
TARGET_RECLAMATION_STATUSES = frozenset({"WP", "WC"})
DEFAULT_BOUNDS = (-82.70, 27.10, -81.45, 28.65)
POLYGON_CACHE_SCHEMA = "icesat2_fdep_active_reclamation_unit_tile_cache_v1"
UNIT_GEOJSON_FILENAME = "fdep_active_reclamation_units.geojson"

FetchJson = Callable[[str, dict[str, str], float], dict[str, Any]]


def _status_code(feature: dict[str, Any]) -> str | None:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return None
    value = properties.get("REC_STATUS")
    if not isinstance(value, str):
        return None
    status = value.strip().upper()
    return status or None


def fetch_active_reclamation_units(
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    timeout_seconds: float,
    fetch_json: FetchJson = campaign._default_fetch_json,
) -> dict[str, Any]:
    """Fetch official WP/WC reclamation units intersecting the bounds."""

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
        FDEP_ACTIVE_RECLAMATION_UNITS_LAYER_URL,
        {
            "where": "REC_STATUS IN ('WP','WC')",
            "geometry": envelope,
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "returnDomainNames": "true",
            "resultRecordCount": "1000",
            "f": "geojson",
        },
        timeout_seconds,
    )
    if payload.get("type") != "FeatureCollection":
        raise ValueError("FDEP response is not a GeoJSON FeatureCollection")
    if payload.get("exceededTransferLimit") is True:
        raise ValueError("FDEP active-unit query exceeded the transfer limit")
    raw_features = payload.get("features")
    if not isinstance(raw_features, list):
        raise ValueError("FDEP FeatureCollection has no features list")

    features: list[dict[str, Any]] = []
    for feature in raw_features:
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict) or geometry.get("type") not in {
            "Polygon",
            "MultiPolygon",
        }:
            continue
        if _status_code(feature) not in TARGET_RECLAMATION_STATUSES:
            continue
        features.append(feature)
    if not features:
        raise ValueError(
            "no official Work in Progress or Work Complete reclamation units "
            "intersect the bounds"
        )
    return {"type": "FeatureCollection", "features": features}


def _unit_identity(feature: dict[str, Any]) -> str:
    properties = feature.get("properties")
    values = properties if isinstance(properties, dict) else {}
    return " | ".join(
        str(values.get(key, ""))
        for key in ("MINE_NAME", "SITE_ID", "REC_UNITS", "REC_STATUS", "OBJECTID")
    )


def _unit_metadata(feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature.get("properties")
    values = properties if isinstance(properties, dict) else {}
    return {
        "identity": _unit_identity(feature),
        "mine_name": values.get("MINE_NAME"),
        "mine_operator": values.get("MINE_OPERATOR"),
        "site_id": values.get("SITE_ID"),
        "reclamation_unit": values.get("REC_UNITS"),
        "reclamation_status": _status_code(feature),
        "annual_report_year": values.get("AR_YEAR"),
        "release_status": values.get("RELEASESTATUS"),
        "gis_acres": values.get("GIS_ACRES"),
        "mined_acres": values.get("MINEDACRES"),
        "total_acres_reclaimed": values.get("TOTALACRECL"),
        "object_id": values.get("OBJECTID"),
    }


def _unit_records(
    feature_collection: dict[str, Any],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    raw_features = feature_collection.get("features")
    if not isinstance(raw_features, list):
        return records
    for feature in raw_features:
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            continue
        metadata = _unit_metadata(feature)
        for polygon in campaign._geometry_polygons(geometry):
            records.append({"polygon": polygon, "metadata": metadata})
    return records


def _segment_coordinate(segment: object) -> tuple[float, float] | None:
    if not isinstance(segment, dict):
        return None
    longitude = segment.get("longitude")
    latitude = segment.get("latitude")
    if not isinstance(longitude, (int, float)) or not isinstance(
        latitude, (int, float)
    ):
        return None
    lon = float(longitude)
    lat = float(latitude)
    if not math.isfinite(lon) or not math.isfinite(lat):
        return None
    return lon, lat


def shared_active_reclamation_unit(
    cluster: dict[str, Any],
    feature_collection: dict[str, Any],
) -> dict[str, Any] | None:
    """Return one common active reclamation unit for all cluster segments."""

    segments = cluster.get("segments")
    if not isinstance(segments, list) or not segments:
        return None
    records = _unit_records(feature_collection)
    if not records:
        return None

    common_identities: set[str] | None = None
    metadata_by_identity: dict[str, dict[str, Any]] = {}
    for segment in segments:
        coordinate = _segment_coordinate(segment)
        if coordinate is None:
            return None
        longitude, latitude = coordinate
        matches: set[str] = set()
        for record in records:
            polygon = record["polygon"]
            metadata = record["metadata"]
            if campaign._point_in_polygon(longitude, latitude, polygon):
                identity = str(metadata["identity"])
                matches.add(identity)
                metadata_by_identity[identity] = metadata
        if not matches:
            return None
        common_identities = (
            matches
            if common_identities is None
            else common_identities.intersection(matches)
        )
        if not common_identities:
            return None

    if common_identities is None or len(common_identities) != 1:
        return None
    identity = next(iter(common_identities))
    return dict(metadata_by_identity[identity])


def filter_clusters_to_single_unit(
    clusters: list[dict[str, Any]],
    feature_collection: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    survivors: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    for cluster in clusters:
        metadata = shared_active_reclamation_unit(cluster, feature_collection)
        if metadata is None:
            rejections.append(
                {
                    "reason": (
                        "supporting_segments_do_not_share_one_active_"
                        "reclamation_unit"
                    ),
                    "centroid_longitude": cluster.get("centroid_longitude"),
                    "centroid_latitude": cluster.get("centroid_latitude"),
                    "median_step_m": cluster.get("median_step_m"),
                    "segment_count": cluster.get("segment_count"),
                }
            )
            continue
        item = dict(cluster)
        item["official_active_reclamation_unit"] = metadata
        survivors.append(item)
    return survivors, rejections


def _work_unit_labels(feature_collection: dict[str, Any]) -> list[str]:
    raw_features = feature_collection.get("features")
    if not isinstance(raw_features, list):
        return []
    return sorted(
        {
            _unit_identity(feature)
            for feature in raw_features
            if isinstance(feature, dict)
        }
    )


def _region_result(**kwargs) -> dict[str, object]:
    active_units = kwargs["active_mines"]
    result = _ORIGINAL_REGION_RESULT(**kwargs)
    raw_clusters = result.get("surviving_step_clusters")
    clusters = (
        [item for item in raw_clusters if isinstance(item, dict)]
        if isinstance(raw_clusters, list)
        else []
    )
    survivors, rejections = filter_clusters_to_single_unit(clusters, active_units)

    result["pre_unit_gate_cluster_count"] = len(clusters)
    result["unit_gate_rejected_count"] = len(rejections)
    result["unit_gate_rejections"] = rejections
    result["surviving_step_cluster_count"] = len(survivors)
    result["surviving_step_clusters"] = survivors
    if survivors:
        result["status"] = (
            "spatially_supported_steps_inside_active_reclamation_units"
        )
    elif clusters:
        result["status"] = (
            "clusters_rejected_without_single_active_reclamation_unit"
        )
    else:
        result["status"] = (
            "no_persistent_upward_steps_inside_active_reclamation_units"
        )

    campaign_dir = Path(kwargs["campaign_dir"])
    region = kwargs["region"]
    region_dir = campaign_dir / region.region_id
    unit_geojson = region_dir / UNIT_GEOJSON_FILENAME
    unit_geojson.write_text(
        json.dumps(active_units, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    constraint = result.get("polygon_constraint")
    if not isinstance(constraint, dict):
        constraint = {}
        result["polygon_constraint"] = constraint
    constraint.update(
        {
            "source_layer": FDEP_ACTIVE_RECLAMATION_UNITS_LAYER_URL,
            "source_description": (
                "FDEP Mandatory Phosphate 2021 - Reclamation Units"
            ),
            "accepted_reclamation_statuses": sorted(
                TARGET_RECLAMATION_STATUSES
            ),
            "official_feature_count": len(active_units.get("features", [])),
            "official_unit_identities": _work_unit_labels(active_units),
            "every_retained_segment_inside_official_polygon": True,
            "every_surviving_cluster_shares_exactly_one_named_unit": True,
            "polygon_geojson": str(unit_geojson),
        }
    )
    interpretation = result.get("interpretation")
    if not isinstance(interpretation, dict):
        interpretation = {}
        result["interpretation"] = interpretation
    interpretation.pop("official_polygon_constraint_applied_before_scanning", None)
    interpretation.update(
        {
            "active_reclamation_unit_constraint_applied_before_scanning": True,
            "single_named_unit_gate_applied_after_clustering": True,
            "reclamation_status_is_not_construction_date": True,
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
    if not isinstance(latitude, (int, float)) or not isinstance(
        longitude, (int, float)
    ):
        return None
    for cluster in clusters:
        cluster_lat = cluster.get("centroid_latitude")
        cluster_lon = cluster.get("centroid_longitude")
        if not isinstance(cluster_lat, (int, float)) or not isinstance(
            cluster_lon, (int, float)
        ):
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
            if match is not None and isinstance(
                match.get("official_active_reclamation_unit"), dict
            ):
                candidate["official_active_reclamation_unit"] = dict(
                    match["official_active_reclamation_unit"]
                )

    failed_tiles = int(summary.get("failed_tile_count", 0) or 0)
    candidate_count = int(summary.get("surviving_candidate_count", 0) or 0)
    summary["status"] = (
        "active_reclamation_unit_candidates_found"
        if candidate_count
        else (
            "active_reclamation_unit_scan_incomplete"
            if failed_tiles
            else "no_surviving_candidates_in_active_reclamation_units"
        )
    )
    summary["accepted_reclamation_statuses"] = sorted(
        TARGET_RECLAMATION_STATUSES
    )
    summary["pre_unit_gate_cluster_count"] = region_result.get(
        "pre_unit_gate_cluster_count", 0
    )
    summary["unit_gate_rejected_count"] = region_result.get(
        "unit_gate_rejected_count", 0
    )
    summary["records_research_ready"] = False
    summary["numerical_depth_unlocked"] = False
    summary["record_lookup_priority_is_provisional"] = True

    region_summaries = summary.get("region_summaries")
    if isinstance(region_summaries, list) and region_summaries:
        first = region_summaries[0]
        if isinstance(first, dict):
            first["pre_unit_gate_cluster_count"] = region_result.get(
                "pre_unit_gate_cluster_count", 0
            )
            first["unit_gate_rejected_count"] = region_result.get(
                "unit_gate_rejected_count", 0
            )
            first["official_polygon_geojson"] = str(
                Path(summary["output_directory"])
                / REGION_ID
                / UNIT_GEOJSON_FILENAME
            )

    interpretation = summary.get("interpretation")
    if not isinstance(interpretation, dict):
        interpretation = {}
        summary["interpretation"] = interpretation
    interpretation.pop(
        "every_retained_segment_inside_official_active_mine_polygon", None
    )
    interpretation.update(
        {
            "every_retained_segment_inside_active_reclamation_unit_polygon": True,
            "every_candidate_cluster_shares_exactly_one_named_unit": True,
            "reclamation_status_is_not_construction_date": True,
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
    campaign.FDEP_LAYER_URL = FDEP_ACTIVE_RECLAMATION_UNITS_LAYER_URL
    campaign.DEFAULT_BOUNDS = DEFAULT_BOUNDS
    campaign.POLYGON_CACHE_SCHEMA = POLYGON_CACHE_SCHEMA
    campaign._tile_bbox_wgs84 = tile_bbox_wgs84
    campaign.fetch_active_mines = fetch_active_reclamation_units
    campaign._mine_names = _work_unit_labels
    campaign._region_result = _region_result
    campaign._summary = _summary


def main() -> int:
    install_campaign()
    return campaign.main()


if __name__ == "__main__":
    raise SystemExit(main())
