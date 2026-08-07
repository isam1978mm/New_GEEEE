"""Run Campaign 011 inside PA DEP reclamation-complete AML polygons.

Campaigns 007-010 were Florida/FDEP phosphate-reclamation discovery passes.
Campaign 011 leaves Florida and constrains ATL08 terrain-step discovery to the
Pennsylvania DEP eMapPA AML Polygon Feature layer where SF_STATUS is exactly
"Reclamation Complete".

The PA DEP status is only a spatial/status screen. It is not treated as a
construction date, placed-material thickness, or depth anchor. All existing
repeat-series, spatial-support, context, finalizer, and evidence gates remain
unchanged.
"""

from __future__ import annotations

import copy
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

CAMPAIGN_ID = "northeast_us_earthwork_pilot_v11_pa_aml_reclamation_complete"
CAMPAIGN_DESCRIPTION = (
    "Eleventh independent ATL08 terrain-step campaign constrained to official "
    "Pennsylvania DEP abandoned-mine-land polygons whose status is Reclamation "
    "Complete, with all prior scientific and finalization gates preserved."
)
REGION_ID = "pa_dep_reclamation_complete_aml_polygons"
REGION_DESCRIPTION = (
    "Pennsylvania DEP eMapPA AML polygons officially marked Reclamation "
    "Complete and large enough in envelope to potentially contain the existing "
    "30-40 m clean-area requirement; ATL08 segments and clusters remain "
    "polygon-constrained."
)
PA_DEP_AML_LAYER_URL = (
    "https://gis.dep.pa.gov/depgisprd/rest/services/emappa/"
    "eMapPA_External/FeatureServer/74/query"
)
TARGET_STATUS = "RECLAMATION COMPLETE"
DEFAULT_BOUNDS = (-80.53, 39.71, -75.44, 41.92)
POLYGON_CACHE_SCHEMA = "icesat2_pa_dep_aml_reclamation_complete_tile_cache_v1"
AML_GEOJSON_FILENAME = "pa_dep_reclamation_complete_aml_polygons.geojson"
MINIMUM_ENVELOPE_SPAN_M = 40.0
PAGE_SIZE = 1000
MAX_PAGES = 100

FetchJson = Callable[[str, dict[str, str], float], dict[str, Any]]


def _normal_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.strip().upper().split())
    return text or None


def _status(feature: dict[str, Any]) -> str | None:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return None
    return _normal_text(properties.get("SF_STATUS"))


def _identity(feature: dict[str, Any]) -> str | None:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return None
    sf_id = properties.get("SF_ID")
    if sf_id not in (None, ""):
        return f"SF_ID:{sf_id}"
    object_id = properties.get("OBJECTID")
    if object_id not in (None, ""):
        return f"OBJECTID:{object_id}"
    return None


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
    longitudes = [point[0] for point in points]
    latitudes = [point[1] for point in points]
    west = min(longitudes)
    east = max(longitudes)
    south = min(latitudes)
    north = max(latitudes)
    mid_latitude = math.radians((south + north) / 2.0)
    east_west_m = abs(east - west) * 111_320.0 * max(0.01, math.cos(mid_latitude))
    north_south_m = abs(north - south) * 110_540.0
    return east_west_m, north_south_m


def _filtered_geometry(geometry: object) -> dict[str, Any] | None:
    """Retain only polygon components with >=40 m envelope span both ways."""

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


def fetch_reclamation_complete_aml(
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    timeout_seconds: float,
    fetch_json: FetchJson = campaign._default_fetch_json,
) -> dict[str, Any]:
    """Fetch all eligible PA DEP AML polygons, using ArcGIS pagination."""

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
    retained: list[dict[str, Any]] = []
    seen_identities: set[str] = set()
    offset = 0

    for _page_number in range(1, MAX_PAGES + 1):
        payload = fetch_json(
            PA_DEP_AML_LAYER_URL,
            {
                "where": "SF_STATUS = 'Reclamation Complete'",
                "geometry": envelope,
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "orderByFields": "OBJECTID ASC",
                "resultOffset": str(offset),
                "resultRecordCount": str(PAGE_SIZE),
                "f": "geojson",
            },
            timeout_seconds,
        )
        if payload.get("type") != "FeatureCollection":
            raise ValueError("PA DEP response is not a GeoJSON FeatureCollection")
        raw_features = payload.get("features")
        if not isinstance(raw_features, list):
            raise ValueError("PA DEP FeatureCollection has no features list")
        if not raw_features:
            break

        for raw_feature in raw_features:
            if not isinstance(raw_feature, dict):
                continue
            if _status(raw_feature) != TARGET_STATUS:
                continue
            identity = _identity(raw_feature)
            if identity is None or identity in seen_identities:
                continue
            geometry = _filtered_geometry(raw_feature.get("geometry"))
            if geometry is None:
                continue
            feature = copy.deepcopy(raw_feature)
            feature["geometry"] = geometry
            properties = feature.get("properties")
            if isinstance(properties, dict):
                properties["CAMPAIGN_AML_IDENTITY"] = identity
                properties["CAMPAIGN_MINIMUM_ENVELOPE_SPAN_M"] = (
                    MINIMUM_ENVELOPE_SPAN_M
                )
            retained.append(feature)
            seen_identities.add(identity)

        offset += len(raw_features)
        exceeded = payload.get("exceededTransferLimit") is True
        if len(raw_features) < PAGE_SIZE and not exceeded:
            break
    else:
        raise ValueError("PA DEP AML pagination exceeded the safety page limit")

    if not retained:
        raise ValueError(
            "no eligible PA DEP Reclamation Complete AML polygons intersect the bounds"
        )
    return {"type": "FeatureCollection", "features": retained}


def _metadata(feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature.get("properties")
    values = properties if isinstance(properties, dict) else {}
    return {
        "identity": _identity(feature),
        "sf_id": values.get("SF_ID"),
        "object_id": values.get("OBJECTID"),
        "other_id": values.get("OTHER_ID"),
        "name": values.get("SF_NAME"),
        "type_code": values.get("SF_TYPE_CD"),
        "type": values.get("SF_TYPE"),
        "status_code": values.get("SF_STATUS_CD"),
        "status": _status(feature),
        "priority_code": values.get("SF_PRIORITY_CD"),
        "priority": values.get("SF_PRIORITY"),
        "problem_code": values.get("SF_PROBLEM_CODE"),
        "problem_description": values.get("SF_PROBLEM_CODE_DESCRIPTION"),
        "height_ft_context_only": values.get("HEIGHT_FT"),
        "volume_cy_context_only": values.get("VOLUME_CY"),
        "flow_gpm_context_only": values.get("FLOW_GPM"),
        "keywords": values.get("KEYWORDS"),
        "quantity_context_only": values.get("QUANTITY"),
        "uom_context_only": values.get("UOM"),
        "legacy_status": values.get("STATUS"),
    }


def _polygon_records(
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
        metadata = _metadata(feature)
        if metadata["identity"] is None:
            continue
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


def shared_reclamation_complete_polygon(
    cluster: dict[str, Any],
    feature_collection: dict[str, Any],
) -> dict[str, Any] | None:
    """Require all supporting segments to share exactly one PA DEP polygon."""

    segments = cluster.get("segments")
    if not isinstance(segments, list) or not segments:
        return None
    records = _polygon_records(feature_collection)
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
            metadata = record["metadata"]
            identity = str(metadata["identity"])
            if campaign._point_in_polygon(longitude, latitude, record["polygon"]):
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


def filter_clusters_to_single_polygon(
    clusters: list[dict[str, Any]],
    feature_collection: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    survivors: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    for cluster in clusters:
        metadata = shared_reclamation_complete_polygon(cluster, feature_collection)
        if metadata is None:
            rejections.append(
                {
                    "reason": (
                        "supporting_segments_do_not_share_exactly_one_pa_dep_"
                        "reclamation_complete_aml_polygon"
                    ),
                    "centroid_longitude": cluster.get("centroid_longitude"),
                    "centroid_latitude": cluster.get("centroid_latitude"),
                    "median_step_m": cluster.get("median_step_m"),
                    "segment_count": cluster.get("segment_count"),
                }
            )
            continue
        item = dict(cluster)
        item["official_pa_dep_aml_polygon"] = metadata
        survivors.append(item)
    return survivors, rejections


def _polygon_labels(feature_collection: dict[str, Any]) -> list[str]:
    raw_features = feature_collection.get("features")
    if not isinstance(raw_features, list):
        return []
    labels: set[str] = set()
    for feature in raw_features:
        if not isinstance(feature, dict):
            continue
        metadata = _metadata(feature)
        identity = metadata.get("identity")
        if identity is None:
            continue
        name = metadata.get("name")
        labels.add(f"{identity} | {name or ''}".rstrip())
    return sorted(labels)


def _region_result(**kwargs) -> dict[str, object]:
    official_polygons = kwargs["active_mines"]
    result = _ORIGINAL_REGION_RESULT(**kwargs)
    raw_clusters = result.get("surviving_step_clusters")
    clusters = (
        [item for item in raw_clusters if isinstance(item, dict)]
        if isinstance(raw_clusters, list)
        else []
    )
    survivors, rejections = filter_clusters_to_single_polygon(
        clusters, official_polygons
    )

    result["pre_polygon_identity_gate_cluster_count"] = len(clusters)
    result["polygon_identity_gate_rejected_count"] = len(rejections)
    result["polygon_identity_gate_rejections"] = rejections
    result["surviving_step_cluster_count"] = len(survivors)
    result["surviving_step_clusters"] = survivors
    result["segments_rejected_outside_pa_dep_aml_polygons"] = result.get(
        "segments_rejected_outside_official_mines", 0
    )

    if survivors:
        result["status"] = "spatially_supported_steps_inside_pa_dep_reclaimed_aml"
    elif clusters:
        result["status"] = "clusters_rejected_without_single_pa_dep_aml_polygon"
    else:
        result["status"] = "no_persistent_upward_steps_inside_pa_dep_reclaimed_aml"

    campaign_dir = Path(kwargs["campaign_dir"])
    region = kwargs["region"]
    region_dir = campaign_dir / region.region_id
    polygon_geojson = region_dir / AML_GEOJSON_FILENAME
    polygon_geojson.write_text(
        json.dumps(official_polygons, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    constraint = result.get("polygon_constraint")
    if not isinstance(constraint, dict):
        constraint = {}
        result["polygon_constraint"] = constraint
    constraint.pop("official_mine_names", None)
    constraint.update(
        {
            "source_layer": PA_DEP_AML_LAYER_URL,
            "source_description": "PA DEP eMapPA AML Polygon Feature",
            "accepted_sf_status": "Reclamation Complete",
            "minimum_component_envelope_span_m": MINIMUM_ENVELOPE_SPAN_M,
            "official_feature_count": len(official_polygons.get("features", [])),
            "official_polygon_labels": _polygon_labels(official_polygons),
            "arcgis_pagination_enabled": True,
            "every_retained_segment_inside_official_polygon": True,
            "every_surviving_cluster_shares_exactly_one_official_polygon": True,
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
            "pa_dep_reclamation_complete_polygon_constraint_applied": True,
            "single_official_polygon_gate_applied_after_clustering": True,
            "reclamation_complete_status_is_not_construction_date": True,
            "inventory_height_volume_quantity_are_not_assumed_depth": True,
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
    if not isinstance(latitude, (int, float)) or not isinstance(
        longitude, (int, float)
    ):
        return None
    for cluster in clusters:
        cluster_latitude = cluster.get("centroid_latitude")
        cluster_longitude = cluster.get("centroid_longitude")
        if not isinstance(cluster_latitude, (int, float)) or not isinstance(
            cluster_longitude, (int, float)
        ):
            continue
        if abs(float(latitude) - float(cluster_latitude)) <= 1e-8 and abs(
            float(longitude) - float(cluster_longitude)
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
                match.get("official_pa_dep_aml_polygon"), dict
            ):
                candidate["official_pa_dep_aml_polygon"] = dict(
                    match["official_pa_dep_aml_polygon"]
                )

    failed_tiles = int(summary.get("failed_tile_count", 0) or 0)
    candidate_count = int(summary.get("surviving_candidate_count", 0) or 0)
    summary["status"] = (
        "pa_dep_reclamation_complete_aml_candidates_found"
        if candidate_count
        else (
            "pa_dep_reclamation_complete_aml_scan_incomplete"
            if failed_tiles
            else "no_surviving_candidates_in_pa_dep_reclamation_complete_aml"
        )
    )
    summary["accepted_sf_status"] = "Reclamation Complete"
    summary["minimum_component_envelope_span_m"] = MINIMUM_ENVELOPE_SPAN_M
    summary["pre_polygon_identity_gate_cluster_count"] = region_result.get(
        "pre_polygon_identity_gate_cluster_count", 0
    )
    summary["polygon_identity_gate_rejected_count"] = region_result.get(
        "polygon_identity_gate_rejected_count", 0
    )
    summary["records_research_ready"] = False
    summary["numerical_depth_unlocked"] = False
    summary["record_lookup_priority_is_provisional"] = True

    region_summaries = summary.get("region_summaries")
    if isinstance(region_summaries, list) and region_summaries:
        first = region_summaries[0]
        if isinstance(first, dict):
            first["pre_polygon_identity_gate_cluster_count"] = region_result.get(
                "pre_polygon_identity_gate_cluster_count", 0
            )
            first["polygon_identity_gate_rejected_count"] = region_result.get(
                "polygon_identity_gate_rejected_count", 0
            )
            first["segments_rejected_outside_pa_dep_aml_polygons"] = (
                region_result.get("segments_rejected_outside_pa_dep_aml_polygons", 0)
            )
            first["official_polygon_geojson"] = str(
                Path(summary["output_directory"]) / REGION_ID / AML_GEOJSON_FILENAME
            )

    interpretation = summary.get("interpretation")
    if not isinstance(interpretation, dict):
        interpretation = {}
        summary["interpretation"] = interpretation
    interpretation.pop("every_retained_segment_inside_official_active_mine_polygon", None)
    interpretation.update(
        {
            "every_retained_segment_inside_pa_dep_reclamation_complete_polygon": True,
            "every_candidate_cluster_shares_exactly_one_official_polygon": True,
            "reclamation_complete_status_is_not_construction_date": True,
            "inventory_height_volume_quantity_are_not_assumed_depth": True,
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
    campaign.FDEP_LAYER_URL = PA_DEP_AML_LAYER_URL
    campaign.DEFAULT_BOUNDS = DEFAULT_BOUNDS
    campaign.POLYGON_CACHE_SCHEMA = POLYGON_CACHE_SCHEMA
    campaign._tile_bbox_wgs84 = tile_bbox_wgs84
    campaign.fetch_active_mines = fetch_reclamation_complete_aml
    campaign._mine_names = _polygon_labels
    campaign._region_result = _region_result
    campaign._summary = _summary


def main() -> int:
    install_campaign()
    return campaign.main()


if __name__ == "__main__":
    raise SystemExit(main())
