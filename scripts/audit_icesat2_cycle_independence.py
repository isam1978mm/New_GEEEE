"""Audit whether ICESat-2 repeat precision recurs across independent cycles.

The first ATL08 repeat audit can produce many adjacent 100 m segments from one
pair of satellite passes.  Those segments are spatial samples, but they share
pass-level errors.  This script separates the observations into actual
RGT/spot/early-cycle/late-cycle cohorts and requires the target precision to
recur across at least two independent early cycles and two independent late
cycles.

This is read-only.  It writes no run artifacts and does not invoke the depth
engine or frontend.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.pipeline.elevation_change.icesat2_independence import (
    build_cycle_pair_cohorts,
    independence_decision,
    summarize_cohort,
)
from audit_icesat2_repeat_points import (
    DEFAULT_END,
    DEFAULT_SPLIT,
    DEFAULT_START,
    Icesat2AuditError,
    _load_manifest,
    _parse_time,
    _query_atl08,
    _segments_from_frame,
    _wgs84_polygon,
)


def audit(
    *,
    run_dir: Path,
    start: str,
    end: str,
    split_time: datetime,
    target_m: float,
    minimum_ground_photons: int,
    minimum_pairs: int,
    maximum_uncertainty_m: float | None,
    cohort_preview_limit: int,
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
    cohorts = build_cycle_pair_cohorts(
        segments,
        split_time=split_time,
        max_distance_m=15.0,
    )
    summaries = [
        summarize_cohort(
            cohort,
            target_m=target_m,
            minimum_pairs=minimum_pairs,
        )
        for cohort in cohorts
    ]
    decision = independence_decision(summaries)

    summaries.sort(
        key=lambda item: (
            not bool(item["supports_target"]),
            -int(item["pair_count_within_15m"]),
            int(item["early_cycle"]),
            int(item["late_cycle"]),
            int(item["rgt"]),
            int(item["spot"]),
        )
    )

    if not segments:
        status = "no_quality_atl08_segments"
    elif not cohorts:
        status = "no_independent_cycle_pair_cohorts"
    elif decision["multi_epoch_repeatability_supported"]:
        status = "multi_epoch_repeatability_supported"
    elif decision["single_cycle_pair_precision_supported"]:
        status = "single_cycle_pair_only"
    else:
        status = "target_precision_not_repeated"

    return {
        "schema": "icesat2_cycle_independence_audit_v1",
        "status": status,
        "run": run_dir.name,
        "run_epsg": manifest.epsg,
        "source": "ICESat-2 ATL08 via SlideRule atl08x",
        "query_start": start,
        "query_end": end,
        "split_time": split_time.isoformat(),
        "target_m": float(target_m),
        "minimum_pairs_per_cycle_cohort": int(minimum_pairs),
        "quality_segment_count": len(segments),
        "cycle_pair_cohort_count": len(cohorts),
        "input_diagnostics": diagnostics,
        "rejected": rejected,
        "independence_decision": decision,
        "cycle_pair_cohorts": summaries[: max(0, int(cohort_preview_limit))],
        "cohort_output_truncated": len(summaries) > int(cohort_preview_limit),
        "does_not_prove": [
            "target_intersection",
            "construction_event_bracketing",
            "placed_material_thickness",
            "depth_to_a_buried_object",
            "radar_depth_prediction",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit ICESat-2 precision across independent cycle pairs."
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--split-date", default=DEFAULT_SPLIT)
    parser.add_argument("--target-m", type=float, default=0.7)
    parser.add_argument("--minimum-ground-photons", type=int, default=3)
    parser.add_argument("--minimum-pairs", type=int, default=30)
    parser.add_argument("--maximum-uncertainty-m", type=float, default=None)
    parser.add_argument("--cohort-preview-limit", type=int, default=50)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        result = audit(
            run_dir=args.run_dir,
            start=args.start,
            end=args.end,
            split_time=_parse_time(args.split_date),
            target_m=args.target_m,
            minimum_ground_photons=args.minimum_ground_photons,
            minimum_pairs=args.minimum_pairs,
            maximum_uncertainty_m=args.maximum_uncertainty_m,
            cohort_preview_limit=args.cohort_preview_limit,
        )
    except Icesat2AuditError as exc:
        print(
            json.dumps(
                {"status": "audit_unavailable", "error": str(exc)},
                indent=2,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
