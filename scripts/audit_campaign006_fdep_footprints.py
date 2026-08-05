"""Audit Campaign 006 ATL08 support points against official FDEP phosphate layers.

This read-only research tool queries the Florida Department of Environmental
Protection ArcGIS service point by point. It checks whether every supporting
ATL08 segment for a candidate falls inside one common:

1. 2021 active mandatory phosphate mine boundary;
2. released mandatory phosphate mine boundary; or
3. released phosphate reclamation unit.

A positive footprint match is only a geometry/context result. It does not prove
that the detected elevation rise was caused by placed material, does not prove a
certified thickness, does not create a depth anchor, and does not modify app
artifacts.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = (
    "https://ca.dep.state.fl.us/arcgis/rest/services/"
    "OpenData/MMP_MANPHO/MapServer"
)
SCHEMA = "campaign006_fdep_footprint_audit_v1"

LAYERS = (
    {
        "key": "active_mine_2021",
        "layer_id": 13,
        "label": "Mandatory Phosphate 2021 - Mine Boundaries",
    },
    {
        "key": "released_mine_2024",
        "layer_id": 12,
        "label": "Mandatory Released Phosphate - Mine Boundaries",
    },
    {
        "key": "released_reclamation_units",
        "layer_id": 14,
        "label": "Mandatory Released Phosphate - Reclamation Units",
    },
)

FetchJson = Callable[[str, dict[str, str], float], dict[str, Any]]


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _finite_number(value: object) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _default_fetch_json(
    url: str,
    params: dict[str, str],
    timeout_seconds: float,
) -> dict[str, Any]:
    request_url = f"{url}?{urlencode(params)}"
    request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "New-GEE-Campaign006-FDEP-footprint-audit/1.0",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"FDEP request failed for {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"FDEP response for {url} was not a JSON object")
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message") or "unknown ArcGIS error"
        raise RuntimeError(f"FDEP ArcGIS error for {url}: {message}")
    return payload


def _coded_domains(metadata: dict[str, Any]) -> dict[str, dict[object, object]]:
    result: dict[str, dict[object, object]] = {}
    fields = metadata.get("fields")
    if not isinstance(fields, list):
        return result
    for raw in fields:
        if not isinstance(raw, dict):
            continue
        name = raw.get("name")
        domain = raw.get("domain")
        if not isinstance(name, str) or not isinstance(domain, dict):
            continue
        coded = domain.get("codedValues")
        if not isinstance(coded, list):
            continue
        values: dict[object, object] = {}
        for item in coded:
            if not isinstance(item, dict):
                continue
            code = item.get("code")
            label = item.get("name")
            if code is not None and label is not None:
                values[code] = label
                values[str(code)] = label
        if values:
            result[name] = values
    return result


def _decode_attributes(
    attributes: dict[str, Any],
    domains: dict[str, dict[object, object]],
) -> dict[str, Any]:
    decoded = dict(attributes)
    for field, values in domains.items():
        if field in decoded:
            raw = decoded[field]
            decoded[field] = values.get(raw, values.get(str(raw), raw))
    return decoded


def _feature_identity(attributes: dict[str, Any]) -> str:
    parts = [
        attributes.get("MINE_NAME"),
        attributes.get("SITE_ID"),
        attributes.get("REC_UNITS"),
        attributes.get("OBJECTID"),
    ]
    normalized = [str(value).strip() for value in parts if value not in (None, "")]
    return " | ".join(normalized) if normalized else json.dumps(attributes, sort_keys=True)


def _metadata_for_layer(
    layer_id: int,
    *,
    timeout_seconds: float,
    fetch_json: FetchJson,
) -> dict[str, Any]:
    return fetch_json(
        f"{BASE_URL}/{layer_id}",
        {"f": "json"},
        timeout_seconds,
    )


def _query_point(
    *,
    layer_id: int,
    longitude: float,
    latitude: float,
    timeout_seconds: float,
    fetch_json: FetchJson,
) -> dict[str, Any]:
    geometry = json.dumps(
        {
            "x": longitude,
            "y": latitude,
            "spatialReference": {"wkid": 4326},
        },
        separators=(",", ":"),
    )
    return fetch_json(
        f"{BASE_URL}/{layer_id}/query",
        {
            "where": "1=1",
            "geometry": geometry,
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "false",
            "returnUnformattedValues": "false",
            "f": "json",
        },
        timeout_seconds,
    )


def _segment_coordinates(dossier: dict[str, Any]) -> list[dict[str, object]]:
    values = dossier.get("segments")
    rows: list[dict[str, object]] = []
    if not isinstance(values, list):
        return rows
    for raw in values:
        if not isinstance(raw, dict):
            continue
        longitude = _finite_number(raw.get("longitude"))
        latitude = _finite_number(raw.get("latitude"))
        if longitude is None or latitude is None:
            continue
        rows.append(
            {
                "segment_id": raw.get("segment_id"),
                "longitude": longitude,
                "latitude": latitude,
            }
        )
    return rows


def _shared_identities(point_results: list[dict[str, Any]]) -> list[str]:
    identity_sets: list[set[str]] = []
    for row in point_results:
        identities = row.get("feature_identities")
        values = {
            str(value)
            for value in identities
            if isinstance(value, str) and value
        } if isinstance(identities, list) else set()
        identity_sets.append(values)
    if not identity_sets:
        return []
    shared = set.intersection(*identity_sets)
    return sorted(shared)


def audit_layer(
    dossier: dict[str, Any],
    *,
    layer: dict[str, object],
    timeout_seconds: float,
    fetch_json: FetchJson = _default_fetch_json,
) -> dict[str, Any]:
    layer_id = int(layer["layer_id"])
    metadata = _metadata_for_layer(
        layer_id,
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
    )
    domains = _coded_domains(metadata)
    points = _segment_coordinates(dossier)
    if not points:
        raise ValueError("candidate dossier contains no usable segment coordinates")

    point_results: list[dict[str, Any]] = []
    for point in points:
        payload = _query_point(
            layer_id=layer_id,
            longitude=float(point["longitude"]),
            latitude=float(point["latitude"]),
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        )
        raw_features = payload.get("features")
        raw_features = raw_features if isinstance(raw_features, list) else []
        features: list[dict[str, Any]] = []
        identities: list[str] = []
        for raw_feature in raw_features:
            if not isinstance(raw_feature, dict):
                continue
            attributes = raw_feature.get("attributes")
            if not isinstance(attributes, dict):
                continue
            decoded = _decode_attributes(attributes, domains)
            features.append(decoded)
            identities.append(_feature_identity(decoded))
        point_results.append(
            {
                **point,
                "feature_count": len(features),
                "feature_identities": sorted(set(identities)),
                "features": features,
            }
        )

    shared = _shared_identities(point_results)
    matched_count = sum(1 for item in point_results if item["feature_count"] > 0)
    return {
        "layer_key": layer["key"],
        "layer_id": layer_id,
        "layer_label": layer["label"],
        "source_url": f"{BASE_URL}/{layer_id}",
        "supporting_point_count": len(point_results),
        "matched_point_count": matched_count,
        "all_supporting_points_matched": matched_count == len(point_results),
        "all_supporting_points_share_one_feature": bool(shared),
        "shared_features": shared,
        "point_results": point_results,
    }


def _candidate_decision(layer_audits: list[dict[str, Any]]) -> dict[str, Any]:
    by_key = {
        str(item.get("layer_key")): item
        for item in layer_audits
        if isinstance(item, dict)
    }
    reclamation = by_key.get("released_reclamation_units", {})
    active = by_key.get("active_mine_2021", {})
    released = by_key.get("released_mine_2024", {})

    if reclamation.get("all_supporting_points_share_one_feature"):
        status = "single_official_reclamation_unit_covers_all_segments"
        manual_review_survives = True
    elif active.get("all_supporting_points_share_one_feature"):
        status = "single_active_mine_covers_all_segments_unit_not_resolved"
        manual_review_survives = True
    elif released.get("all_supporting_points_share_one_feature"):
        status = "single_released_mine_covers_all_segments_unit_not_resolved"
        manual_review_survives = True
    else:
        status = "no_single_official_phosphate_footprint_covers_all_segments"
        manual_review_survives = False

    return {
        "status": status,
        "manual_footprint_review_survives": manual_review_survives,
        "records_research_ready": False,
        "candidate_is_depth_anchor": False,
        "placed_thickness_confirmed": False,
        "cause_confirmed": False,
    }


def audit_candidate(
    dossier: dict[str, Any],
    *,
    timeout_seconds: float,
    fetch_json: FetchJson = _default_fetch_json,
) -> dict[str, Any]:
    layer_audits = [
        audit_layer(
            dossier,
            layer=layer,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        )
        for layer in LAYERS
    ]
    summary = dossier.get("candidate_summary")
    summary = summary if isinstance(summary, dict) else {}
    return {
        "candidate_id": dossier.get("candidate_id"),
        "campaign_rank": dossier.get("campaign_rank"),
        "longitude": summary.get("longitude"),
        "latitude": summary.get("latitude"),
        "median_step_m": summary.get("median_step_m"),
        "segment_count": dossier.get("segment_count"),
        "layer_audits": layer_audits,
        "decision": _candidate_decision(layer_audits),
    }


def run_audit(
    *,
    campaign_dir: Path,
    ranks: list[int],
    timeout_seconds: float,
    fetch_json: FetchJson = _default_fetch_json,
) -> dict[str, Any]:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if not ranks or any(rank <= 0 for rank in ranks):
        raise ValueError("candidate ranks must be positive")

    candidates: list[dict[str, Any]] = []
    for rank in ranks:
        dossier = _load_object(
            campaign_dir / f"candidate_{rank:03d}_dossier.json",
            label=f"candidate {rank:03d} dossier",
        )
        candidates.append(
            audit_candidate(
                dossier,
                timeout_seconds=timeout_seconds,
                fetch_json=fetch_json,
            )
        )

    survivors = [
        item
        for item in candidates
        if item.get("decision", {}).get("manual_footprint_review_survives")
    ]
    return {
        "schema": SCHEMA,
        "status": (
            "official_fdep_footprint_survivors_found"
            if survivors
            else "no_official_fdep_footprint_survivors"
        ),
        "campaign_dir": str(campaign_dir),
        "candidate_count": len(candidates),
        "footprint_survivor_count": len(survivors),
        "footprint_survivor_ranks": [item.get("campaign_rank") for item in survivors],
        "candidates": candidates,
        "record_lookup_priority": [],
        "records_research_ready": False,
        "numerical_depth_unlocked": False,
        "interpretation": {
            "official_geometry_gate_only": True,
            "all_supporting_points_are_checked_individually": True,
            "positive_match_does_not_prove_event_cause": True,
            "positive_match_does_not_prove_placed_thickness": True,
            "candidate_is_depth_anchor": False,
            "app_behavior_changed": False,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Campaign 006 candidates against official FDEP footprints."
    )
    parser.add_argument("--campaign-dir", type=Path, required=True)
    parser.add_argument("--candidate-ranks", type=int, nargs="+", default=[1, 2, 3, 4])
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    return parser


def main() -> int:
    args = _parser().parse_args()
    output = args.output_json or (
        args.campaign_dir / "campaign_006_fdep_footprint_audit.json"
    )
    try:
        result = run_audit(
            campaign_dir=args.campaign_dir,
            ranks=list(args.candidate_ranks),
            timeout_seconds=args.timeout_seconds,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "fdep_footprint_audit_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
