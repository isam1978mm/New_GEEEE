"""Run Campaign 010 inside FDEP units with reported reclamation acreage growth.

Campaign 009 used a single 2021 status snapshot and found 19 raw upward-step
series but no spatial cluster satisfying the unchanged support gate. Campaign
010 compares the official 2018-2021 FDEP reclamation-unit layers and retains
stable units with a strictly positive year-over-year increase in TOTALACRECL.

This changes only the official activity constraint. All existing temporal,
stability, neighbour, cluster, context, terminal-stability, and recovery gates
remain unchanged. A surviving cluster is still only a terrain-step candidate;
it is not a measured depth anchor and does not change app behavior.
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
import scan_icesat2_fdep_active_reclamation_units_campaign as campaign009

CAMPAIGN_ID = "southeast_us_earthwork_pilot_v10_fdep_reclamation_acreage_change"
CAMPAIGN_DESCRIPTION = (
    "Tenth independent ATL08 terrain-step campaign constrained to official "
    "FDEP mandatory-phosphate reclamation units whose reported TOTALACRECL "
    "increases across at least one consecutive 2018-2021 annual layer, with "
    "all prior scientific and finalization gates preserved."
)
REGION_ID = "fdep_reclamation_acreage_change_2018_2021"
REGION_DESCRIPTION = (
    "Central Florida mandatory-phosphate reclamation units with an official "
    "positive year-over-year TOTALACRECL change in the 2018-2021 FDEP annual "
    "layers; tiles, ATL08 segments, and final clusters remain polygon-gated."
)
FDEP_RECLAMATION_SERVICE_ROOT = (
    "https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/"
    "MMP_RECLUNITS/MapServer"
)
ANNUAL_LAYER_IDS = {2018: 6, 2019: 7, 2020: 8, 2021: 9}
DEFAULT_BOUNDS = (-82.70, 27.10, -81.45, 28.65)
POLYGON_CACHE_SCHEMA = "icesat2_fdep_reclamation_acreage_change_tile_cache_v1"
UNIT_GEOJSON_FILENAME = "fdep_reclamation_acreage_change_units.geojson"
ALL_OFFICIAL_STATUSES = frozenset({"ND", "NMP", "OTH", "WC", "WF", "WP", "WS"})

FetchJson = Callable[[str, dict[str, str], float], dict[str, Any]]

_ORIGINAL_REGION_RESULT = campaign009._region_result
_ORIGINAL_SUMMARY = campaign009._summary


def _normal_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().upper().split())
    return normalized or None


def _stable_unit_key(feature: dict[str, Any]) -> str | None:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return None
    site_id = properties.get("SITE_ID")
    unit = _normal_text(properties.get("REC_UNITS"))
    if site_id is None or unit is None:
        return None
    if isinstance(site_id, float) and not math.isfinite(site_id):
        return None
    return f"{site_id}|{unit}"


def _total_reclaimed_acres(feature: dict[str, Any]) -> float | None:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return None
    value = properties.get("TOTALACRECL")
    if not isinstance(value, (int, float)):
        return None
    result = float(value)
    if not math.isfinite(result):
        return None
    return result


def _fetch_annual_layer(
    *,
    year: int,
    west: float,
    south: float,
    east: float,
    north: float,
    timeout_seconds: float,
    fetch_json: FetchJson,
) -> dict[str, Any]:
    layer_id = ANNUAL_LAYER_IDS[year]
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
        f"{FDEP_RECLAMATION_SERVICE_ROOT}/{layer_id}/query",
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
            "resultRecordCount": "1000",
            "f": "geojson",
        },
        timeout_seconds,
    )
    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"FDEP {year} response is not a GeoJSON FeatureCollection")
    if payload.get("exceededTransferLimit") is True:
        raise ValueError(f"FDEP {year} reclamation-unit query exceeded transfer limit")
    raw_features = payload.get("features")
    if not isinstance(raw_features, list):
        raise ValueError(f"FDEP {year} FeatureCollection has no features list")

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
        if _stable_unit_key(feature) is None:
            continue
        features.append(feature)
    return {"type": "FeatureCollection", "features": features}


def _index_year(
    feature_collection: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    index: dict[str, dict[str, Any]] = {}
    ambiguous: set[str] = set()
    raw_features = feature_collection.get("features")
    if not isinstance(raw_features, list):
        return index, ambiguous
    for feature in raw_features:
        if not isinstance(feature, dict):
            continue
        key = _stable_unit_key(feature)
        if key is None:
            continue
        if key in index:
            ambiguous.add(key)
            continue
        index[key] = feature
    for key in ambiguous:
        index.pop(key, None)
    return index, ambiguous


def _status(feature: dict[str, Any]) -> str | None:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return None
    return _normal_text(properties.get("REC_STATUS"))


def fetch_reclamation_activity_units(
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    timeout_seconds: float,
    fetch_json: FetchJson = campaign._default_fetch_json,
) -> dict[str, Any]:
    """Fetch units with a positive official TOTALACRECL annual change."""

    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("invalid WGS84 bounds")

    yearly: dict[int, dict[str, dict[str, Any]]] = {}
    ambiguous_by_year: dict[int, set[str]] = {}
    for year in sorted(ANNUAL_LAYER_IDS):
        collection = _fetch_annual_layer(
            year=year,
            west=west,
            south=south,
            east=east,
            north=north,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        )
        yearly[year], ambiguous_by_year[year] = _index_year(collection)

    all_keys = sorted({key for index in yearly.values() for key in index})
    years = sorted(ANNUAL_LAYER_IDS)
    selected: list[dict[str, Any]] = []

    for key in all_keys:
        if any(key in ambiguous_by_year[year] for year in years):
            continue

        transitions: list[dict[str, Any]] = []
        status_history: list[dict[str, Any]] = []
        for year in years:
            feature = yearly[year].get(key)
            if feature is None:
                continue
            status_history.append(
                {
                    "year": year,
                    "status": _status(feature),
                    "total_reclaimed_acres": _total_reclaimed_acres(feature),
                }
            )

        for before_year, after_year in zip(years, years[1:]):
            before = yearly[before_year].get(key)
            after = yearly[after_year].get(key)
            if before is None or after is None:
                continue
            before_acres = _total_reclaimed_acres(before)
            after_acres = _total_reclaimed_acres(after)
            if before_acres is None or after_acres is None:
                continue
            increase = after_acres - before_acres
            if increase <= 0:
                continue
            transitions.append(
                {
                    "from_year": before_year,
                    "to_year": after_year,
                    "from_status": _status(before),
                    "to_status": _status(after),
                    "from_total_reclaimed_acres": before_acres,
                    "to_total_reclaimed_acres": after_acres,
                    "increase_acres": increase,
                }
            )

        if not transitions:
            continue

        selected_year = max(int(item["to_year"]) for item in transitions)
        selected_feature = yearly[selected_year].get(key)
        if selected_feature is None:
            continue
        feature = copy.deepcopy(selected_feature)
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            properties = {}
            feature["properties"] = properties
        properties.update(
            {
                "ACTIVITY_UNIT_KEY": key,
                "ACTIVITY_SOURCE_YEARS": years,
                "ACTIVITY_SELECTED_GEOMETRY_YEAR": selected_year,
                "ACTIVITY_POSITIVE_TRANSITIONS": transitions,
                "ACTIVITY_STATUS_HISTORY": status_history,
                "ACTIVITY_TOTAL_POSITIVE_INCREASE_ACRES": sum(
                    float(item["increase_acres"]) for item in transitions
                ),
                "ACTIVITY_FIRST_YEAR": min(
                    int(item["from_year"]) for item in transitions
                ),
                "ACTIVITY_LAST_YEAR": max(
                    int(item["to_year"]) for item in transitions
                ),
            }
        )
        selected.append(feature)

    if not selected:
        raise ValueError(
            "no unambiguous FDEP reclamation units with a positive consecutive "
            "2018-2021 TOTALACRECL change intersect the bounds"
        )
    return {"type": "FeatureCollection", "features": selected}


def _activity_unit_identity(feature: dict[str, Any]) -> str:
    properties = feature.get("properties")
    values = properties if isinstance(properties, dict) else {}
    value = values.get("ACTIVITY_UNIT_KEY")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return _stable_unit_key(feature) or ""


def _activity_unit_metadata(feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature.get("properties")
    values = properties if isinstance(properties, dict) else {}
    return {
        "identity": _activity_unit_identity(feature),
        "mine_name": values.get("MINE_NAME"),
        "mine_operator": values.get("MINE_OPERATOR"),
        "site_id": values.get("SITE_ID"),
        "reclamation_unit": values.get("REC_UNITS"),
        "reclamation_status": _status(feature),
        "annual_report_year": values.get("AR_YEAR"),
        "release_status": values.get("RELEASESTATUS"),
        "gis_acres": values.get("GIS_ACRES"),
        "mined_acres": values.get("MINEDACRES"),
        "total_acres_reclaimed": values.get("TOTALACRECL"),
        "object_id": values.get("OBJECTID"),
        "activity_source_years": values.get("ACTIVITY_SOURCE_YEARS"),
        "activity_selected_geometry_year": values.get(
            "ACTIVITY_SELECTED_GEOMETRY_YEAR"
        ),
        "activity_positive_transitions": values.get(
            "ACTIVITY_POSITIVE_TRANSITIONS"
        ),
        "activity_status_history": values.get("ACTIVITY_STATUS_HISTORY"),
        "activity_total_positive_increase_acres": values.get(
            "ACTIVITY_TOTAL_POSITIVE_INCREASE_ACRES"
        ),
        "activity_first_year": values.get("ACTIVITY_FIRST_YEAR"),
        "activity_last_year": values.get("ACTIVITY_LAST_YEAR"),
    }


def _activity_unit_labels(feature_collection: dict[str, Any]) -> list[str]:
    raw_features = feature_collection.get("features")
    if not isinstance(raw_features, list):
        return []
    return sorted(
        {
            _activity_unit_identity(feature)
            for feature in raw_features
            if isinstance(feature, dict) and _activity_unit_identity(feature)
        }
    )


def _region_result(**kwargs) -> dict[str, object]:
    result = _ORIGINAL_REGION_RESULT(**kwargs)
    constraint = result.get("polygon_constraint")
    if not isinstance(constraint, dict):
        constraint = {}
        result["polygon_constraint"] = constraint
    constraint.pop("accepted_reclamation_statuses", None)
    constraint.update(
        {
            "source_layer": FDEP_RECLAMATION_SERVICE_ROOT,
            "source_description": (
                "FDEP Mandatory Phosphate 2018-2021 Reclamation Units annual layers"
            ),
            "annual_layer_ids": dict(ANNUAL_LAYER_IDS),
            "activity_metric": "TOTALACRECL",
            "activity_rule": "strictly_positive_consecutive_year_increase",
            "stable_identity_fields": ["SITE_ID", "REC_UNITS"],
            "ambiguous_duplicate_identity_policy": "reject",
        }
    )
    interpretation = result.get("interpretation")
    if not isinstance(interpretation, dict):
        interpretation = {}
        result["interpretation"] = interpretation
    interpretation.pop("reclamation_status_is_not_construction_date", None)
    interpretation.update(
        {
            "reported_reclaimed_acreage_change_is_not_construction_date": True,
            "reported_reclaimed_acreage_change_is_not_depth": True,
            "cause_confirmed": False,
            "candidate_is_depth_anchor": False,
            "app_behavior_changed": False,
        }
    )

    campaign_dir = Path(kwargs["campaign_dir"])
    region = kwargs["region"]
    region_dir = campaign_dir / region.region_id
    (region_dir / "region_scan.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (region_dir / "candidates.geojson").write_text(
        json.dumps(campaign._geojson(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _summary(**kwargs) -> dict[str, object]:
    summary = _ORIGINAL_SUMMARY(**kwargs)
    failed_tiles = int(summary.get("failed_tile_count", 0) or 0)
    candidate_count = int(summary.get("surviving_candidate_count", 0) or 0)
    summary["status"] = (
        "reclamation_acreage_change_candidates_found"
        if candidate_count
        else (
            "reclamation_acreage_change_scan_incomplete"
            if failed_tiles
            else "no_surviving_candidates_in_reclamation_acreage_change_units"
        )
    )
    summary.pop("accepted_reclamation_statuses", None)
    summary.update(
        {
            "annual_layer_ids": dict(ANNUAL_LAYER_IDS),
            "activity_metric": "TOTALACRECL",
            "activity_rule": "strictly_positive_consecutive_year_increase",
            "records_research_ready": False,
            "numerical_depth_unlocked": False,
            "record_lookup_priority_is_provisional": True,
        }
    )
    interpretation = summary.get("interpretation")
    if not isinstance(interpretation, dict):
        interpretation = {}
        summary["interpretation"] = interpretation
    interpretation.pop("reclamation_status_is_not_construction_date", None)
    interpretation.update(
        {
            "reported_reclaimed_acreage_change_is_not_construction_date": True,
            "reported_reclaimed_acreage_change_is_not_depth": True,
            "records_needed_only_for_finalized_survivors": True,
            "candidate_cause_confirmed": False,
            "candidate_is_depth_anchor": False,
            "app_behavior_changed": False,
        }
    )
    campaign_dir = Path(summary["output_directory"])
    (campaign_dir / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def install_campaign() -> None:
    campaign009.CAMPAIGN_ID = CAMPAIGN_ID
    campaign009.CAMPAIGN_DESCRIPTION = CAMPAIGN_DESCRIPTION
    campaign009.REGION_ID = REGION_ID
    campaign009.REGION_DESCRIPTION = REGION_DESCRIPTION
    campaign009.FDEP_ACTIVE_RECLAMATION_UNITS_LAYER_URL = FDEP_RECLAMATION_SERVICE_ROOT
    campaign009.TARGET_RECLAMATION_STATUSES = ALL_OFFICIAL_STATUSES
    campaign009.DEFAULT_BOUNDS = DEFAULT_BOUNDS
    campaign009.POLYGON_CACHE_SCHEMA = POLYGON_CACHE_SCHEMA
    campaign009.UNIT_GEOJSON_FILENAME = UNIT_GEOJSON_FILENAME
    campaign009.fetch_active_reclamation_units = fetch_reclamation_activity_units
    campaign009._unit_identity = _activity_unit_identity
    campaign009._unit_metadata = _activity_unit_metadata
    campaign009._work_unit_labels = _activity_unit_labels

    campaign009.install_campaign()
    campaign._region_result = _region_result
    campaign._summary = _summary


def main() -> int:
    install_campaign()
    return campaign.main()


if __name__ == "__main__":
    raise SystemExit(main())
