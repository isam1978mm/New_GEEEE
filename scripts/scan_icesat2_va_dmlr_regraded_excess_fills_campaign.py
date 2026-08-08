"""Run Campaign 013 inside Virginia DMLR regraded excess-material fills.

Campaign 013 combines two official Virginia Department of Energy DMLR polygon
layers from the Current Permits service:

* Excess Material Disposal (Fills), used as the acquisition/segment footprint;
* Reclamation Status polygons where ``Rec_Stat = 'reg'`` (Regraded), used as
  an exact post-cluster spatial integrity gate.

A surviving cluster must share exactly one fill polygon and exactly one
regraded polygon from the same permit.  Regraded status is not treated as a
construction date, measured thickness, depth anchor, or proof of radar
transferability.  All existing repeat-series, spatial-support, context,
finalizer, terminal-stability, temporal-recovery, and evidence gates remain
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

CAMPAIGN_ID = "central_appalachia_earthwork_pilot_v13_va_dmlr_regraded_excess_fills"
CAMPAIGN_DESCRIPTION = (
    "Thirteenth independent ATL08 terrain-step campaign constrained to official "
    "Virginia DMLR Excess Material Disposal fill polygons associated with "
    "permits that contain exact Regraded reclamation-status polygons; final "
    "clusters must share one fill and one regraded polygon from the same permit."
)
REGION_ID = "va_dmlr_regraded_excess_material_fills"
REGION_DESCRIPTION = (
    "Southwest Virginia DMLR excess-material disposal fill polygons whose "
    "permits contain official Regraded reclamation-status polygons; ATL08 "
    "segments are fill-constrained and final clusters require exact overlap "
    "with one same-permit Regraded polygon."
)
VA_DMLR_RECLAMATION_STATUS_URL = (
    "https://energy.virginia.gov/gis/rest/services/DMLR/"
    "CurrentPermits/FeatureServer/0/query"
)
VA_DMLR_EXCESS_FILLS_URL = (
    "https://energy.virginia.gov/gis/rest/services/DMLR/"
    "CurrentPermits/FeatureServer/6/query"
)
TARGET_RECLAMATION_STATUS = "REG"
DEFAULT_BOUNDS = (-83.75, 36.45, -80.15, 37.65)
POLYGON_CACHE_SCHEMA = "icesat2_va_dmlr_regraded_excess_fill_tile_cache_v1"
FILL_GEOJSON_FILENAME = "va_dmlr_regraded_excess_material_fills.geojson"
REGRADED_GEOJSON_FILENAME = "va_dmlr_regraded_status_polygons.geojson"
MINIMUM_ENVELOPE_SPAN_M = 40.0
PAGE_SIZE = 1000
MAX_PAGES = 100

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
    if not isinstance(value, str):
        return None
    text = " ".join(value.strip().upper().split())
    return text or None


def _permit(feature: dict[str, Any]) -> str | None:
    value = _property(feature, "Permit", "PERMIT", "permit")
    if value in (None, ""):
        return None
    text = str(value).strip().upper()
    return text or None


def _reclamation_status(feature: dict[str, Any]) -> str | None:
    return _normal_text(_property(feature, "Rec_Stat", "REC_STAT", "rec_stat"))


def _global_id(feature: dict[str, Any]) -> str | None:
    value = _property(feature, "GlobalID", "GLOBALID", "globalid")
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _object_id(feature: dict[str, Any]) -> str | None:
    value = _property(feature, "OBJECTID", "objectid", "ObjectID")
    if value in (None, ""):
        return None
    return str(value).strip() or None


def _regraded_identity(feature: dict[str, Any]) -> str | None:
    global_id = _global_id(feature)
    if global_id:
        return f"GLOBALID:{global_id}"
    object_id = _object_id(feature)
    if object_id:
        return f"OBJECTID:{object_id}"
    permit = _permit(feature)
    return f"PERMIT:{permit}" if permit else None


def _fill_identity(feature: dict[str, Any]) -> str | None:
    global_id = _global_id(feature)
    if global_id:
        return f"GLOBALID:{global_id}"
    permit = _permit(feature)
    component = _property(feature, "Comp_ID", "COMP_ID", "comp_id")
    object_id = _object_id(feature)
    pieces = [
        str(item).strip()
        for item in (permit, component, object_id)
        if item not in (None, "")
    ]
    return " | ".join(pieces) if pieces else None


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
    """Keep polygon components that can contain the existing ~40 m footprint."""

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


def _envelope_json(*, west: float, south: float, east: float, north: float) -> str:
    return json.dumps(
        {
            "xmin": west,
            "ymin": south,
            "xmax": east,
            "ymax": north,
            "spatialReference": {"wkid": 4326},
        },
        separators=(",", ":"),
    )


def _fetch_paginated(
    *,
    url: str,
    where: str,
    west: float,
    south: float,
    east: float,
    north: float,
    timeout_seconds: float,
    fetch_json: FetchJson,
) -> list[dict[str, Any]]:
    envelope = _envelope_json(west=west, south=south, east=east, north=north)
    features: list[dict[str, Any]] = []
    offset = 0

    for _page_number in range(1, MAX_PAGES + 1):
        payload = fetch_json(
            url,
            {
                "where": where,
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
            raise ValueError("Virginia DMLR response is not a GeoJSON FeatureCollection")
        raw_features = payload.get("features")
        if not isinstance(raw_features, list):
            raise ValueError("Virginia DMLR FeatureCollection has no features list")
        if not raw_features:
            break
        features.extend(item for item in raw_features if isinstance(item, dict))
        offset += len(raw_features)
        exceeded = payload.get("exceededTransferLimit") is True
        if len(raw_features) < PAGE_SIZE and not exceeded:
            break
    else:
        raise ValueError("Virginia DMLR pagination exceeded the safety page limit")

    return features


def fetch_regraded_excess_fills(
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    timeout_seconds: float,
    fetch_json: FetchJson = campaign._default_fetch_json,
) -> dict[str, Any]:
    """Fetch official fills associated with exact DMLR Regraded polygons."""

    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("invalid WGS84 bounds")

    raw_regraded = _fetch_paginated(
        url=VA_DMLR_RECLAMATION_STATUS_URL,
        where="Rec_Stat = 'reg'",
        west=west,
        south=south,
        east=east,
        north=north,
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
    )

    regraded_features: list[dict[str, Any]] = []
    regraded_permits: set[str] = set()
    seen_regraded: set[str] = set()
    for raw_feature in raw_regraded:
        if _reclamation_status(raw_feature) != TARGET_RECLAMATION_STATUS:
            continue
        permit = _permit(raw_feature)
        identity = _regraded_identity(raw_feature)
        geometry = raw_feature.get("geometry")
        if (
            permit is None
            or identity is None
            or identity in seen_regraded
            or not isinstance(geometry, dict)
            or geometry.get("type") not in {"Polygon", "MultiPolygon"}
        ):
            continue
        feature = copy.deepcopy(raw_feature)
        properties = feature.get("properties")
        if isinstance(properties, dict):
            properties["CAMPAIGN_RECLAMATION_IDENTITY"] = identity
            properties["CAMPAIGN_RECLAMATION_STATUS"] = "Regraded"
        regraded_features.append(feature)
        regraded_permits.add(permit)
        seen_regraded.add(identity)

    if not regraded_features or not regraded_permits:
        raise ValueError("no official Virginia DMLR Regraded polygons intersect the bounds")

    raw_fills = _fetch_paginated(
        url=VA_DMLR_EXCESS_FILLS_URL,
        where="1=1",
        west=west,
        south=south,
        east=east,
        north=north,
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
    )

    retained_fills: list[dict[str, Any]] = []
    seen_fills: set[str] = set()
    source_counts = {
        "raw_regraded_feature_count": len(raw_regraded),
        "retained_regraded_feature_count": len(regraded_features),
        "regraded_permit_count": len(regraded_permits),
        "raw_fill_feature_count": len(raw_fills),
        "fill_rejected_without_regraded_permit": 0,
        "fill_rejected_below_40m_envelope": 0,
        "fill_rejected_missing_identity_or_geometry": 0,
        "fill_rejected_duplicate_identity": 0,
    }

    for raw_feature in raw_fills:
        permit = _permit(raw_feature)
        if permit is None or permit not in regraded_permits:
            source_counts["fill_rejected_without_regraded_permit"] += 1
            continue
        identity = _fill_identity(raw_feature)
        if identity is None:
            source_counts["fill_rejected_missing_identity_or_geometry"] += 1
            continue
        if identity in seen_fills:
            source_counts["fill_rejected_duplicate_identity"] += 1
            continue
        geometry = _filtered_geometry(raw_feature.get("geometry"))
        if geometry is None:
            source_counts["fill_rejected_below_40m_envelope"] += 1
            continue

        feature = copy.deepcopy(raw_feature)
        feature["geometry"] = geometry
        properties = feature.get("properties")
        if isinstance(properties, dict):
            properties["CAMPAIGN_FILL_IDENTITY"] = identity
            properties["CAMPAIGN_MINIMUM_ENVELOPE_SPAN_M"] = MINIMUM_ENVELOPE_SPAN_M
        retained_fills.append(feature)
        seen_fills.add(identity)

    source_counts["retained_fill_feature_count"] = len(retained_fills)
    if not retained_fills:
        raise ValueError(
            "no eligible Virginia DMLR excess-material fills associated with "
            "Regraded permits after the 40 m envelope pre-screen; "
            + json.dumps(source_counts, sort_keys=True)
        )

    return {
        "type": "FeatureCollection",
        "features": retained_fills,
        "campaign_regraded_status_features": regraded_features,
        "campaign_source_diagnostics": source_counts,
    }


def _fill_metadata(feature: dict[str, Any]) -> dict[str, Any]:
    return {
        "identity": _fill_identity(feature),
        "permit": _permit(feature),
        "component_id": _property(feature, "Comp_ID", "COMP_ID", "comp_id"),
        "description": _property(feature, "Descrip", "DESCRIP", "descrip"),
        "cf_cert_no": _property(feature, "CFCertNo", "CFCERTNO", "cfcertno"),
        "cf_cert_no_from": _property(
            feature, "CFCertNoFrom", "CFCERTNOFROM", "cfcertnofrom"
        ),
        "cf_cert_no_to": _property(
            feature, "CFCertNoTo", "CFCERTNOTO", "cfcertnoto"
        ),
        "object_id": _object_id(feature),
        "global_id": _global_id(feature),
    }


def _regraded_metadata(feature: dict[str, Any]) -> dict[str, Any]:
    return {
        "identity": _regraded_identity(feature),
        "permit": _permit(feature),
        "status_code": _reclamation_status(feature),
        "status": "Regraded",
        "object_id": _object_id(feature),
        "global_id": _global_id(feature),
    }


def _polygon_records(
    features: object,
    metadata_fn,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not isinstance(features, list):
        return records
    for feature in features:
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            continue
        metadata = metadata_fn(feature)
        if metadata.get("identity") is None or metadata.get("permit") is None:
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


def shared_fill_and_regraded_polygon(
    cluster: dict[str, Any],
    feature_collection: dict[str, Any],
) -> dict[str, Any] | None:
    """Require all cluster segments in one fill and one same-permit Regraded polygon."""

    segments = cluster.get("segments")
    if not isinstance(segments, list) or not segments:
        return None

    fill_records = _polygon_records(feature_collection.get("features"), _fill_metadata)
    regraded_records = _polygon_records(
        feature_collection.get("campaign_regraded_status_features"),
        _regraded_metadata,
    )
    if not fill_records or not regraded_records:
        return None

    common_fills: set[str] | None = None
    common_regraded: set[str] | None = None
    fill_meta_by_id: dict[str, dict[str, Any]] = {}
    regraded_meta_by_id: dict[str, dict[str, Any]] = {}

    for segment in segments:
        coordinate = _segment_coordinate(segment)
        if coordinate is None:
            return None
        longitude, latitude = coordinate

        fill_matches: set[str] = set()
        for record in fill_records:
            metadata = record["metadata"]
            identity = str(metadata["identity"])
            if campaign._point_in_polygon(longitude, latitude, record["polygon"]):
                fill_matches.add(identity)
                fill_meta_by_id[identity] = metadata
        if not fill_matches:
            return None

        regraded_matches: set[str] = set()
        for record in regraded_records:
            metadata = record["metadata"]
            identity = str(metadata["identity"])
            if campaign._point_in_polygon(longitude, latitude, record["polygon"]):
                regraded_matches.add(identity)
                regraded_meta_by_id[identity] = metadata
        if not regraded_matches:
            return None

        common_fills = (
            fill_matches if common_fills is None else common_fills.intersection(fill_matches)
        )
        common_regraded = (
            regraded_matches
            if common_regraded is None
            else common_regraded.intersection(regraded_matches)
        )
        if not common_fills or not common_regraded:
            return None

    if common_fills is None or len(common_fills) != 1:
        return None
    if common_regraded is None or len(common_regraded) != 1:
        return None

    fill_id = next(iter(common_fills))
    regraded_id = next(iter(common_regraded))
    fill_metadata = fill_meta_by_id[fill_id]
    regraded_metadata = regraded_meta_by_id[regraded_id]
    if fill_metadata.get("permit") != regraded_metadata.get("permit"):
        return None

    return {
        "permit": fill_metadata.get("permit"),
        "fill": dict(fill_metadata),
        "regraded_polygon": dict(regraded_metadata),
    }


def filter_clusters_to_fill_and_regraded_polygon(
    clusters: list[dict[str, Any]],
    feature_collection: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    survivors: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    for cluster in clusters:
        metadata = shared_fill_and_regraded_polygon(cluster, feature_collection)
        if metadata is None:
            rejections.append(
                {
                    "reason": (
                        "supporting_segments_do_not_share_exactly_one_fill_and_"
                        "one_same_permit_regraded_polygon"
                    ),
                    "centroid_longitude": cluster.get("centroid_longitude"),
                    "centroid_latitude": cluster.get("centroid_latitude"),
                    "median_step_m": cluster.get("median_step_m"),
                    "segment_count": cluster.get("segment_count"),
                }
            )
            continue
        item = dict(cluster)
        item["official_va_dmlr_regraded_fill"] = metadata
        survivors.append(item)
    return survivors, rejections


def _fill_labels(feature_collection: dict[str, Any]) -> list[str]:
    raw_features = feature_collection.get("features")
    if not isinstance(raw_features, list):
        return []
    labels: set[str] = set()
    for feature in raw_features:
        if not isinstance(feature, dict):
            continue
        metadata = _fill_metadata(feature)
        if metadata.get("identity") is None:
            continue
        labels.add(
            " | ".join(
                str(item or "")
                for item in (
                    metadata.get("identity"),
                    metadata.get("permit"),
                    metadata.get("component_id"),
                )
            ).rstrip(" |")
        )
    return sorted(labels)


def _region_result(**kwargs) -> dict[str, object]:
    official_fills = kwargs["active_mines"]
    result = _ORIGINAL_REGION_RESULT(**kwargs)
    raw_clusters = result.get("surviving_step_clusters")
    clusters = (
        [item for item in raw_clusters if isinstance(item, dict)]
        if isinstance(raw_clusters, list)
        else []
    )
    survivors, rejections = filter_clusters_to_fill_and_regraded_polygon(
        clusters, official_fills
    )

    result["pre_fill_regraded_gate_cluster_count"] = len(clusters)
    result["fill_regraded_gate_rejected_count"] = len(rejections)
    result["fill_regraded_gate_rejections"] = rejections
    result["surviving_step_cluster_count"] = len(survivors)
    result["surviving_step_clusters"] = survivors
    result["segments_rejected_outside_va_dmlr_fill_polygons"] = result.get(
        "segments_rejected_outside_official_mines", 0
    )

    if survivors:
        result["status"] = "spatially_supported_steps_inside_va_dmlr_regraded_fills"
    elif clusters:
        result["status"] = "clusters_rejected_without_exact_va_dmlr_regraded_fill_pair"
    else:
        result["status"] = "no_persistent_upward_steps_inside_va_dmlr_regraded_fills"

    campaign_dir = Path(kwargs["campaign_dir"])
    region = kwargs["region"]
    region_dir = campaign_dir / region.region_id
    fill_geojson = region_dir / FILL_GEOJSON_FILENAME
    regraded_geojson = region_dir / REGRADED_GEOJSON_FILENAME
    fill_geojson.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": official_fills.get("features", []),
                "campaign_source_diagnostics": official_fills.get(
                    "campaign_source_diagnostics", {}
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    regraded_geojson.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": official_fills.get("campaign_regraded_status_features", []),
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
            "source_fill_layer": VA_DMLR_EXCESS_FILLS_URL,
            "source_reclamation_status_layer": VA_DMLR_RECLAMATION_STATUS_URL,
            "source_description": (
                "Virginia DMLR Current Permits: Excess Material Disposal (Fills) "
                "+ Reclamation Status"
            ),
            "accepted_reclamation_status_code": "reg",
            "accepted_reclamation_status": "Regraded",
            "minimum_component_envelope_span_m": MINIMUM_ENVELOPE_SPAN_M,
            "official_fill_feature_count": len(official_fills.get("features", [])),
            "official_regraded_feature_count": len(
                official_fills.get("campaign_regraded_status_features", [])
            ),
            "official_fill_labels": _fill_labels(official_fills),
            "arcgis_pagination_enabled": True,
            "every_retained_segment_inside_official_fill_polygon": True,
            "every_surviving_cluster_shares_exactly_one_fill_polygon": True,
            "every_surviving_cluster_shares_exactly_one_regraded_polygon": True,
            "fill_and_regraded_polygon_share_same_permit": True,
            "fill_polygon_geojson": str(fill_geojson),
            "regraded_polygon_geojson": str(regraded_geojson),
            "source_diagnostics": official_fills.get("campaign_source_diagnostics", {}),
        }
    )

    interpretation = result.get("interpretation")
    if not isinstance(interpretation, dict):
        interpretation = {}
        result["interpretation"] = interpretation
    interpretation.pop("official_polygon_constraint_applied_before_scanning", None)
    interpretation.update(
        {
            "va_dmlr_fill_polygon_constraint_applied_before_scanning": True,
            "same_permit_regraded_polygon_gate_applied_after_clustering": True,
            "regraded_status_is_not_construction_date": True,
            "regraded_status_is_not_depth": True,
            "fill_polygon_does_not_prove_measured_thickness": True,
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
                match.get("official_va_dmlr_regraded_fill"), dict
            ):
                candidate["official_va_dmlr_regraded_fill"] = dict(
                    match["official_va_dmlr_regraded_fill"]
                )

    failed_tiles = int(summary.get("failed_tile_count", 0) or 0)
    candidate_count = int(summary.get("surviving_candidate_count", 0) or 0)
    summary["status"] = (
        "va_dmlr_regraded_fill_candidates_found"
        if candidate_count
        else (
            "va_dmlr_regraded_fill_scan_incomplete"
            if failed_tiles
            else "no_surviving_candidates_in_va_dmlr_regraded_fills"
        )
    )
    summary["accepted_reclamation_status"] = "Regraded"
    summary["minimum_component_envelope_span_m"] = MINIMUM_ENVELOPE_SPAN_M
    summary["pre_fill_regraded_gate_cluster_count"] = region_result.get(
        "pre_fill_regraded_gate_cluster_count", 0
    )
    summary["fill_regraded_gate_rejected_count"] = region_result.get(
        "fill_regraded_gate_rejected_count", 0
    )
    summary["records_research_ready"] = False
    summary["numerical_depth_unlocked"] = False
    summary["record_lookup_priority_is_provisional"] = True

    region_summaries = summary.get("region_summaries")
    if isinstance(region_summaries, list) and region_summaries:
        first = region_summaries[0]
        if isinstance(first, dict):
            first["pre_fill_regraded_gate_cluster_count"] = region_result.get(
                "pre_fill_regraded_gate_cluster_count", 0
            )
            first["fill_regraded_gate_rejected_count"] = region_result.get(
                "fill_regraded_gate_rejected_count", 0
            )
            first["segments_rejected_outside_va_dmlr_fill_polygons"] = (
                region_result.get("segments_rejected_outside_va_dmlr_fill_polygons", 0)
            )
            first["official_fill_geojson"] = str(
                Path(summary["output_directory"]) / REGION_ID / FILL_GEOJSON_FILENAME
            )
            first["official_regraded_geojson"] = str(
                Path(summary["output_directory"]) / REGION_ID / REGRADED_GEOJSON_FILENAME
            )

    interpretation = summary.get("interpretation")
    if not isinstance(interpretation, dict):
        interpretation = {}
        summary["interpretation"] = interpretation
    interpretation.pop("every_retained_segment_inside_official_active_mine_polygon", None)
    interpretation.update(
        {
            "every_retained_segment_inside_va_dmlr_excess_fill_polygon": True,
            "every_candidate_cluster_shares_one_fill_and_one_same_permit_regraded_polygon": True,
            "regraded_status_is_not_construction_date": True,
            "regraded_status_is_not_depth": True,
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
    campaign.FDEP_LAYER_URL = VA_DMLR_EXCESS_FILLS_URL
    campaign.DEFAULT_BOUNDS = DEFAULT_BOUNDS
    campaign.POLYGON_CACHE_SCHEMA = POLYGON_CACHE_SCHEMA
    campaign._tile_bbox_wgs84 = tile_bbox_wgs84
    campaign.fetch_active_mines = fetch_regraded_excess_fills
    campaign._mine_names = _fill_labels
    campaign._region_result = _region_result
    campaign._summary = _summary


def main() -> int:
    install_campaign()
    return campaign.main()


if __name__ == "__main__":
    raise SystemExit(main())
