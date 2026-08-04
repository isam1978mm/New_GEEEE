"""Extract one broad-track ICESat-2 survivor into a review dossier.

This tool is local and read-only with respect to the app. It reads the private
broad-campaign summary and region result, selects one ranked survivor, and
writes a compact JSON dossier plus a GeoJSON footprint containing the exact
ATL08 segment histories used by the cluster.

It does not query SlideRule, research records, create a depth anchor, invoke the
radar depth engine, register app artifacts, or modify the frontend.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

DEFAULT_CAMPAIGN_DIR = Path(
    "./data/research/icesat2_broad_track_scan/southwest_us_earthwork_pilot_v1"
)
DEFAULT_SUMMARY_FILENAME = "campaign_summary.json"
DOSSIER_SCHEMA = "icesat2_broad_candidate_dossier_v1"


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _number(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _candidate_by_rank(
    campaign_summary: dict[str, Any],
    *,
    candidate_rank: int,
) -> dict[str, Any]:
    rows = campaign_summary.get("record_lookup_priority")
    if not isinstance(rows, list):
        raise ValueError("campaign summary has no record_lookup_priority list")
    for row in rows:
        if not isinstance(row, dict):
            continue
        rank = row.get("campaign_rank", row.get("global_rank"))
        if rank == candidate_rank:
            return row
    raise ValueError(f"candidate rank {candidate_rank} was not found")


def _cluster_by_local_rank(
    region_result: dict[str, Any],
    *,
    local_rank: int,
) -> dict[str, Any]:
    clusters = region_result.get("surviving_step_clusters")
    if not isinstance(clusters, list):
        raise ValueError("region result has no surviving_step_clusters list")
    index = local_rank - 1
    if index < 0 or index >= len(clusters) or not isinstance(clusters[index], dict):
        raise ValueError(f"region-local candidate rank {local_rank} was not found")
    return clusters[index]


def _segment_rows(cluster: dict[str, Any]) -> list[dict[str, Any]]:
    values = cluster.get("segments")
    if not isinstance(values, list):
        return []
    rows = [dict(value) for value in values if isinstance(value, dict)]
    rows.sort(
        key=lambda item: (
            int(item.get("rgt", 0) or 0),
            int(item.get("spot", 0) or 0),
            str(item.get("segment_id", "")),
        )
    )
    return rows


def _finite_numbers(values: Iterable[object]) -> list[float]:
    result: list[float] = []
    for value in values:
        number = _number(value)
        if number is not None:
            result.append(number)
    return result


def _quality_checks(
    candidate: dict[str, Any],
    cluster: dict[str, Any],
    segments: list[dict[str, Any]],
) -> dict[str, Any]:
    expected_count = int(cluster.get("segment_count", 0) or 0)
    event_keys = {
        (
            item.get("rgt"),
            item.get("spot"),
            item.get("pre_cycle"),
            item.get("post_cycle"),
            item.get("event_start"),
            item.get("event_end"),
        )
        for item in segments
    }
    steps = _finite_numbers(item.get("step_m") for item in segments)
    return {
        "cluster_segment_count_matches": expected_count == len(segments),
        "all_segments_share_one_event_key": len(event_keys) == 1,
        "campaign_and_cluster_coordinates_match": (
            candidate.get("longitude") == cluster.get("centroid_longitude")
            and candidate.get("latitude") == cluster.get("centroid_latitude")
        ),
        "cross_spot_supported": bool(cluster.get("cross_spot_supported")),
        "segment_step_min_m": min(steps) if steps else None,
        "segment_step_max_m": max(steps) if steps else None,
        "segment_step_range_m": (max(steps) - min(steps)) if steps else None,
    }


def build_dossier(
    *,
    campaign_summary: dict[str, Any],
    region_result: dict[str, Any],
    candidate_rank: int,
) -> dict[str, Any]:
    candidate = _candidate_by_rank(
        campaign_summary,
        candidate_rank=candidate_rank,
    )
    region_id = candidate.get("region_id")
    if not isinstance(region_id, str) or not region_id:
        raise ValueError("candidate is missing region_id")
    if region_result.get("region_id") != region_id:
        raise ValueError("region result does not match the selected candidate")

    local_rank = candidate.get("region_local_rank")
    if not isinstance(local_rank, int):
        raise ValueError("candidate is missing region_local_rank")
    cluster = _cluster_by_local_rank(region_result, local_rank=local_rank)
    segments = _segment_rows(cluster)

    return {
        "schema": DOSSIER_SCHEMA,
        "status": "candidate_requires_cause_and_thickness_confirmation",
        "candidate_id": f"{campaign_summary.get('campaign_id', 'campaign')}_rank_{candidate_rank:03d}",
        "campaign_id": campaign_summary.get("campaign_id"),
        "campaign_rank": candidate_rank,
        "region_id": region_id,
        "region_local_rank": local_rank,
        "candidate_summary": candidate,
        "cluster": cluster,
        "segment_count": len(segments),
        "segments": segments,
        "quality_checks": _quality_checks(candidate, cluster, segments),
        "record_search_requirements": [
            "exact parcel or project footprint containing all supporting segments",
            "activity that occurred inside the measured event window",
            "as-built or certified placed-material thickness",
            "evidence that the placed material covered the ATL08 segment footprint",
            "surface and spatial-uniformity evidence needed before radar transfer",
        ],
        "interpretation": {
            "persistent_terrain_step_supported": True,
            "cause_confirmed": False,
            "placed_thickness_confirmed": False,
            "candidate_is_depth_anchor": False,
            "cross_spot_support_required_for_acceptance": False,
        },
        "does_not_prove": [
            "engineered_fill",
            "placed_material_thickness",
            "depth_to_a_buried_object",
            "radar_depth_prediction",
            "spatial_transfer_beyond_the_laser_strip",
        ],
    }


def _geojson(dossier: dict[str, Any]) -> dict[str, Any]:
    cluster = dossier.get("cluster")
    cluster = cluster if isinstance(cluster, dict) else {}
    features: list[dict[str, Any]] = []
    segments = dossier.get("segments")
    if isinstance(segments, list):
        for item in segments:
            if not isinstance(item, dict):
                continue
            longitude = _number(item.get("longitude"))
            latitude = _number(item.get("latitude"))
            if longitude is None or latitude is None:
                continue
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude],
                    },
                    "properties": {
                        "feature_role": "supporting_atl08_segment",
                        "segment_id": item.get("segment_id"),
                        "rgt": item.get("rgt"),
                        "spot": item.get("spot"),
                        "step_m": item.get("step_m"),
                        "event_start": item.get("event_start"),
                        "event_end": item.get("event_end"),
                    },
                }
            )
    longitude = _number(cluster.get("centroid_longitude"))
    latitude = _number(cluster.get("centroid_latitude"))
    if longitude is not None and latitude is not None:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude],
                },
                "properties": {
                    "feature_role": "cluster_centroid",
                    "candidate_id": dossier.get("candidate_id"),
                    "segment_count": dossier.get("segment_count"),
                    "median_step_m": cluster.get("median_step_m"),
                    "step_nmad_m": cluster.get("step_nmad_m"),
                    "interpretation": "terrain-step candidate; cause unconfirmed",
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def extract(
    *,
    campaign_dir: Path,
    candidate_rank: int,
    output_json: Path,
    output_geojson: Path,
) -> dict[str, Any]:
    if candidate_rank <= 0:
        raise ValueError("candidate_rank must be positive")
    summary = _load_object(
        campaign_dir / DEFAULT_SUMMARY_FILENAME,
        label="campaign summary",
    )
    candidate = _candidate_by_rank(summary, candidate_rank=candidate_rank)
    region_id = candidate.get("region_id")
    if not isinstance(region_id, str) or not region_id:
        raise ValueError("candidate is missing region_id")
    region_result = _load_object(
        campaign_dir / region_id / "region_scan.json",
        label="region result",
    )
    dossier = build_dossier(
        campaign_summary=summary,
        region_result=region_result,
        candidate_rank=candidate_rank,
    )
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(dossier, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output_geojson.parent.mkdir(parents=True, exist_ok=True)
    output_geojson.write_text(
        json.dumps(_geojson(dossier), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return dossier


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract one ranked ICESat-2 broad-track candidate dossier."
    )
    parser.add_argument("--campaign-dir", type=Path, default=DEFAULT_CAMPAIGN_DIR)
    parser.add_argument("--candidate-rank", type=int, default=1)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-geojson", type=Path, default=None)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    output_json = args.output_json or (
        args.campaign_dir / f"candidate_{args.candidate_rank:03d}_dossier.json"
    )
    output_geojson = args.output_geojson or (
        args.campaign_dir / f"candidate_{args.candidate_rank:03d}_dossier.geojson"
    )
    try:
        result = extract(
            campaign_dir=args.campaign_dir,
            candidate_rank=args.candidate_rank,
            output_json=output_json,
            output_geojson=output_geojson,
        )
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "candidate_dossier_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
