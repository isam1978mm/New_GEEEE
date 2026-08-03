"""Scan ICESat-2 ATL08 terrain histories for persistent upward steps.

This is the scan-first stage.  It queries ATL08, groups exact terrain segments
through time, rejects stable/ramp/irregular histories, and keeps only spatially
supported upward-step clusters.  It does not identify the cause, create depth
anchors, invoke the radar depth engine, or modify the app.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.pipeline.elevation_change.icesat2_step_scan import (
    SegmentStepAssessment,
    StepCluster,
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
    _wgs84_polygon,
)


def _assessment_mapping(item: SegmentStepAssessment) -> dict[str, object]:
    return {
        "rgt": item.rgt,
        "spot": item.spot,
        "segment_id": item.segment_id,
        "classification": item.classification,
        "longitude": item.longitude,
        "latitude": item.latitude,
        "observation_count": item.observation_count,
        "cycle_count": item.cycle_count,
        "pre_cycle": item.pre_cycle,
        "post_cycle": item.post_cycle,
        "event_start": item.event_start.isoformat() if item.event_start else None,
        "event_end": item.event_end.isoformat() if item.event_end else None,
        "pre_median_m": item.pre_median_m,
        "post_median_m": item.post_median_m,
        "step_m": item.step_m,
        "pre_nmad_m": item.pre_nmad_m,
        "post_nmad_m": item.post_nmad_m,
        "residual_nmad_m": item.residual_nmad_m,
        "linear_residual_nmad_m": item.linear_residual_nmad_m,
        "dominant_increment_ratio": item.dominant_increment_ratio,
        "positive_increment_fraction": item.positive_increment_fraction,
        "score": item.score,
        "timeline": [
            {
                "cycle": observation.cycle,
                "observed_at": observation.observed_at.isoformat(),
                "height_m": observation.height_m,
                "height_uncertainty_m": observation.height_uncertainty_m,
                "ground_photon_count": observation.ground_photon_count,
            }
            for observation in item.observations
        ],
    }


def _cross_spot_support(
    cluster: StepCluster,
    all_clusters: list[StepCluster],
    *,
    maximum_distance_m: float,
) -> list[dict[str, object]]:
    support: list[dict[str, object]] = []
    for other in all_clusters:
        if other is cluster or other.spot == cluster.spot:
            continue
        if (
            other.rgt != cluster.rgt
            or other.pre_cycle != cluster.pre_cycle
            or other.post_cycle != cluster.post_cycle
        ):
            continue
        distance = math.hypot(
            other.centroid_x_m - cluster.centroid_x_m,
            other.centroid_y_m - cluster.centroid_y_m,
        )
        if distance <= maximum_distance_m:
            support.append(
                {
                    "spot": other.spot,
                    "distance_m": distance,
                    "segment_count": len(other.assessments),
                    "median_step_m": other.median_step_m,
                }
            )
    support.sort(key=lambda item: (float(item["distance_m"]), int(item["spot"])))
    return support


def _cluster_mapping(
    cluster: StepCluster,
    all_clusters: list[StepCluster],
    *,
    cross_spot_distance_m: float,
) -> dict[str, object]:
    cross_spot = _cross_spot_support(
        cluster,
        all_clusters,
        maximum_distance_m=cross_spot_distance_m,
    )
    return {
        "rgt": cluster.rgt,
        "spot": cluster.spot,
        "pre_cycle": cluster.pre_cycle,
        "post_cycle": cluster.post_cycle,
        "event_start": cluster.event_start.isoformat(),
        "event_end": cluster.event_end.isoformat(),
        "segment_count": len(cluster.assessments),
        "median_step_m": cluster.median_step_m,
        "step_nmad_m": cluster.step_nmad_m,
        "centroid_longitude": cluster.centroid_longitude,
        "centroid_latitude": cluster.centroid_latitude,
        "spatial_extent_m": cluster.spatial_extent_m,
        "cross_spot_supported": bool(cross_spot),
        "cross_spot_support": cross_spot,
        "segment_ids": [item.segment_id for item in cluster.assessments],
        "segments": [
            _assessment_mapping(item) for item in cluster.assessments
        ],
    }


def _geojson(result: dict[str, object]) -> dict[str, object]:
    features: list[dict[str, object]] = []
    candidates = result.get("surviving_step_clusters", [])
    if not isinstance(candidates, list):
        candidates = []
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            continue
        features.append(
            {
                "type": "Feature",
                "id": f"icesat2_step_cluster_{index}",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        candidate.get("centroid_longitude"),
                        candidate.get("centroid_latitude"),
                    ],
                },
                "properties": {
                    "rgt": candidate.get("rgt"),
                    "spot": candidate.get("spot"),
                    "pre_cycle": candidate.get("pre_cycle"),
                    "post_cycle": candidate.get("post_cycle"),
                    "event_start": candidate.get("event_start"),
                    "event_end": candidate.get("event_end"),
                    "segment_count": candidate.get("segment_count"),
                    "median_step_m": candidate.get("median_step_m"),
                    "step_nmad_m": candidate.get("step_nmad_m"),
                    "spatial_extent_m": candidate.get("spatial_extent_m"),
                    "cross_spot_supported": candidate.get("cross_spot_supported"),
                    "interpretation": "terrain step candidate; cause unconfirmed",
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def audit(
    *,
    run_dir: Path,
    start: str,
    end: str,
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
    manifest = _load_manifest(run_dir)
    frame = _query_atl08(
        polygon=_wgs84_polygon(manifest),
        start=start,
        end=end,
    )
    segments, rejected, diagnostics = _segments_from_frame(
        frame,
        epsg=manifest.epsg,
        maximum_uncertainty_m=maximum_uncertainty_m,
        minimum_ground_photons=minimum_ground_photons,
    )
    assessments = scan_segment_series(
        segments,
        minimum_epochs=minimum_epochs,
        minimum_side_epochs=minimum_side_epochs,
        minimum_step_m=minimum_step_m,
        maximum_plateau_nmad_m=maximum_plateau_nmad_m,
        minimum_step_dominance=minimum_step_dominance,
    )
    clusters = cluster_step_candidates(
        assessments,
        neighbor_distance_m=neighbor_distance_m,
        minimum_neighbor_segments=minimum_neighbor_segments,
        maximum_cluster_step_nmad_m=maximum_cluster_step_nmad_m,
    )
    classification_counts = Counter(
        item.classification for item in assessments
    )
    step_segments = [
        item for item in assessments if item.classification == "step_up_candidate"
    ]
    mapped_clusters = [
        _cluster_mapping(
            cluster,
            clusters,
            cross_spot_distance_m=cross_spot_distance_m,
        )
        for cluster in clusters[: max(0, int(candidate_limit))]
    ]

    if not segments:
        status = "no_quality_atl08_segments"
    elif not step_segments:
        status = "no_persistent_upward_steps"
    elif not clusters:
        status = "isolated_steps_rejected_by_neighbor_filter"
    else:
        status = "spatially_supported_step_candidates_found"

    return {
        "schema": "icesat2_terrain_step_scan_v1",
        "status": status,
        "run": run_dir.name,
        "run_epsg": manifest.epsg,
        "source": "ICESat-2 ATL08 terrain via SlideRule atl08x",
        "query_start": start,
        "query_end": end,
        "quality_segment_count": len(segments),
        "exact_segment_series_count": len(assessments),
        "classification_counts": dict(sorted(classification_counts.items())),
        "raw_step_up_segment_count": len(step_segments),
        "surviving_step_cluster_count": len(clusters),
        "candidate_output_truncated": len(clusters) > int(candidate_limit),
        "scan_parameters": {
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
        "input_diagnostics": diagnostics,
        "rejected": rejected,
        "surviving_step_clusters": mapped_clusters,
        "record_lookup_priority": [
            {
                "rank": index,
                "longitude": item["centroid_longitude"],
                "latitude": item["centroid_latitude"],
                "event_start": item["event_start"],
                "event_end": item["event_end"],
                "median_step_m": item["median_step_m"],
                "segment_count": item["segment_count"],
                "cross_spot_supported": item["cross_spot_supported"],
            }
            for index, item in enumerate(mapped_clusters, start=1)
        ],
        "interpretation": {
            "terrain_not_canopy_height": True,
            "step_pattern_required": True,
            "gradual_ramps_rejected": True,
            "neighbor_agreement_required": True,
            "cause_confirmed": False,
            "records_needed_only_for_survivors": True,
        },
        "does_not_prove": [
            "engineered_fill",
            "placed_material_thickness",
            "depth_to_a_buried_object",
            "radar_depth_prediction",
            "spatial_transfer_beyond_the_laser_strip",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan ATL08 terrain histories for persistent step changes."
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
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
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-geojson", type=Path, default=None)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        result = audit(
            run_dir=args.run_dir,
            start=args.start,
            end=args.end,
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
    except Icesat2AuditError as exc:
        print(json.dumps({"status": "audit_unavailable", "error": str(exc)}, indent=2))
        return 2

    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(payload + "\n", encoding="utf-8")
    if args.output_geojson is not None:
        args.output_geojson.parent.mkdir(parents=True, exist_ok=True)
        args.output_geojson.write_text(
            json.dumps(_geojson(result), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
