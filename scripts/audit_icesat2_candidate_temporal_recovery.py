"""Audit whether an ICESat-2 step candidate is a lasting rise or a recovery.

The broad step scanner can find a robust median split even when an older
observation already sits near the later plateau and only the immediately
pre-event observations are low.  This local, read-only audit checks that case
before any permit or records research.

It does not query SlideRule, change scanner thresholds, create a depth anchor,
research records, invoke the radar engine, or modify app artifacts.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

DEFAULT_DOSSIER = Path(
    "./data/research/icesat2_broad_track_scan/"
    "southwest_us_earthwork_pilot_v1/candidate_001_dossier.json"
)
SCHEMA = "icesat2_candidate_temporal_recovery_audit_v1"


def _load_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read candidate dossier: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("candidate dossier must be a JSON object")
    return payload


def _number(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _timeline_rows(segment: dict[str, Any]) -> list[dict[str, Any]]:
    values = segment.get("timeline")
    if not isinstance(values, list):
        return []
    rows = [dict(value) for value in values if isinstance(value, dict)]
    rows.sort(
        key=lambda item: (
            int(item.get("cycle", 0) or 0),
            str(item.get("observed_at", "")),
        )
    )
    return rows


def audit_segment(
    segment: dict[str, Any],
    *,
    maximum_net_fraction: float,
) -> dict[str, Any]:
    timeline = _timeline_rows(segment)
    pre_cycle = segment.get("pre_cycle")
    post_cycle = segment.get("post_cycle")
    reported_step = _number(segment.get("step_m"))
    pre_median = _number(segment.get("pre_median_m"))
    post_median = _number(segment.get("post_median_m"))

    usable = [
        item
        for item in timeline
        if _number(item.get("height_m")) is not None
        and isinstance(item.get("cycle"), int)
    ]
    earliest = usable[0] if usable else None
    earliest_height = _number(earliest.get("height_m")) if earliest else None
    earliest_cycle = earliest.get("cycle") if earliest else None

    post_heights = [
        float(item["height_m"])
        for item in usable
        if isinstance(post_cycle, int) and int(item["cycle"]) >= post_cycle
    ]
    calculated_post_median = (
        float(statistics.median(post_heights)) if post_heights else post_median
    )
    net_change = (
        calculated_post_median - earliest_height
        if calculated_post_median is not None and earliest_height is not None
        else None
    )
    net_fraction = (
        abs(net_change) / abs(reported_step)
        if net_change is not None
        and reported_step is not None
        and abs(reported_step) > 0.0
        else None
    )
    distance_to_pre = (
        abs(earliest_height - pre_median)
        if earliest_height is not None and pre_median is not None
        else None
    )
    distance_to_post = (
        abs(earliest_height - calculated_post_median)
        if earliest_height is not None and calculated_post_median is not None
        else None
    )
    earliest_closer_to_post = (
        distance_to_post < distance_to_pre
        if distance_to_post is not None and distance_to_pre is not None
        else False
    )
    recovery_like = (
        earliest_closer_to_post
        and net_fraction is not None
        and net_fraction <= maximum_net_fraction
    )

    return {
        "segment_id": segment.get("segment_id"),
        "rgt": segment.get("rgt"),
        "spot": segment.get("spot"),
        "pre_cycle": pre_cycle,
        "post_cycle": post_cycle,
        "earliest_cycle": earliest_cycle,
        "earliest_height_m": earliest_height,
        "reported_step_m": reported_step,
        "pre_median_m": pre_median,
        "post_median_m": calculated_post_median,
        "earliest_to_post_net_change_m": net_change,
        "absolute_net_change_fraction_of_reported_step": net_fraction,
        "earliest_distance_to_pre_m": distance_to_pre,
        "earliest_distance_to_post_m": distance_to_post,
        "earliest_is_closer_to_post_plateau": earliest_closer_to_post,
        "recovery_like": recovery_like,
    }


def build_audit(
    dossier: dict[str, Any],
    *,
    maximum_net_fraction: float = 0.5,
    minimum_recovery_fraction: float = 0.6,
) -> dict[str, Any]:
    if not 0.0 <= maximum_net_fraction <= 1.0:
        raise ValueError("maximum_net_fraction must be between 0 and 1")
    if not 0.0 <= minimum_recovery_fraction <= 1.0:
        raise ValueError("minimum_recovery_fraction must be between 0 and 1")
    values = dossier.get("segments")
    if not isinstance(values, list):
        raise ValueError("candidate dossier has no segments list")
    segments = [dict(value) for value in values if isinstance(value, dict)]
    if not segments:
        raise ValueError("candidate dossier has no usable segments")

    rows = [
        audit_segment(item, maximum_net_fraction=maximum_net_fraction)
        for item in segments
    ]
    recovery_count = sum(bool(item["recovery_like"]) for item in rows)
    recovery_fraction = recovery_count / len(rows)
    net_changes = [
        float(item["earliest_to_post_net_change_m"])
        for item in rows
        if isinstance(item.get("earliest_to_post_net_change_m"), (int, float))
    ]
    net_fractions = [
        float(item["absolute_net_change_fraction_of_reported_step"])
        for item in rows
        if isinstance(
            item.get("absolute_net_change_fraction_of_reported_step"),
            (int, float),
        )
    ]
    recovery_pattern = recovery_fraction >= minimum_recovery_fraction
    status = (
        "temporary_depression_recovery_pattern"
        if recovery_pattern
        else "lasting_rise_not_disproved_by_recovery_audit"
    )

    return {
        "schema": SCHEMA,
        "status": status,
        "candidate_id": dossier.get("candidate_id"),
        "segment_count": len(rows),
        "recovery_like_segment_count": recovery_count,
        "recovery_like_segment_fraction": recovery_fraction,
        "median_earliest_to_post_net_change_m": (
            float(statistics.median(net_changes)) if net_changes else None
        ),
        "median_absolute_net_change_fraction_of_reported_step": (
            float(statistics.median(net_fractions)) if net_fractions else None
        ),
        "segment_audits": rows,
        "audit_parameters": {
            "maximum_net_fraction": maximum_net_fraction,
            "minimum_recovery_fraction": minimum_recovery_fraction,
        },
        "decision": {
            "direct_thickness_anchor_lookup_recommended": not recovery_pattern,
            "candidate_remains_depth_anchor": False,
            "records_research_started": False,
        },
        "interpretation": {
            "recovery_pattern_means": (
                "the oldest observation is closer to the later plateau than "
                "to the immediately pre-event low plateau"
            ),
            "possible_causes_include": [
                "temporary excavation followed by restoration",
                "cycle-specific or seasonal terrain-height bias",
                "temporary surface disturbance",
            ],
            "cause_confirmed": False,
            "placed_thickness_confirmed": False,
        },
        "does_not_prove": [
            "no earthwork occurred",
            "the apparent dip was an instrument error",
            "excavation depth",
            "placed material thickness",
            "buried object depth",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit one ICESat-2 candidate for a recovery pattern."
    )
    parser.add_argument("--dossier", type=Path, default=DEFAULT_DOSSIER)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--maximum-net-fraction", type=float, default=0.5)
    parser.add_argument("--minimum-recovery-fraction", type=float, default=0.6)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    output_path = args.output_json or args.dossier.with_name(
        args.dossier.stem.replace("_dossier", "_temporal_recovery_audit") + ".json"
    )
    try:
        dossier = _load_object(args.dossier)
        result = build_audit(
            dossier,
            maximum_net_fraction=args.maximum_net_fraction,
            minimum_recovery_fraction=args.minimum_recovery_fraction,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "temporal_recovery_audit_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
