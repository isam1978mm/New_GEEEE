"""Prioritize finalized ICESat-2 candidates for land/parcel context review.

Passing the temporal gates only shows that an apparent rise is spatially
supported and not disproved by available time-series reversals. It still does
not make every survivor a sensible direct placed-thickness records target.

This conservative audit defers candidates with an extreme reported rise, too
few supporting segments, or an event window too broad for efficient attribution.
A passing candidate is eligible only for land/water/parcel context review.
Records research remains paused until that context review identifies a matching
project footprint and activity window.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_DOSSIER = Path(
    "./data/research/icesat2_broad_track_scan/"
    "southwest_us_earthwork_pilot_v3_imperial_valley/"
    "candidate_009_dossier.json"
)
SCHEMA = "icesat2_candidate_context_priority_audit_v1"


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


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def build_audit(
    dossier: dict[str, Any],
    *,
    maximum_context_step_m: float = 5.0,
    minimum_segment_count: int = 4,
    maximum_event_window_days: float = 730.0,
) -> dict[str, Any]:
    if maximum_context_step_m <= 0.0:
        raise ValueError("maximum_context_step_m must be positive")
    if minimum_segment_count <= 0:
        raise ValueError("minimum_segment_count must be positive")
    if maximum_event_window_days <= 0.0:
        raise ValueError("maximum_event_window_days must be positive")

    summary = dossier.get("candidate_summary")
    if not isinstance(summary, dict):
        summary = {}
    cluster = dossier.get("cluster")
    if not isinstance(cluster, dict):
        cluster = {}

    step_m = _number(summary.get("median_step_m", cluster.get("median_step_m")))
    segment_count_value = summary.get(
        "segment_count",
        dossier.get("segment_count", cluster.get("segment_count")),
    )
    segment_count = (
        int(segment_count_value) if isinstance(segment_count_value, int) else None
    )
    event_start = _parse_time(summary.get("event_start", cluster.get("event_start")))
    event_end = _parse_time(summary.get("event_end", cluster.get("event_end")))
    event_window_days = (
        (event_end - event_start).total_seconds() / 86400.0
        if event_start is not None and event_end is not None
        else None
    )

    magnitude_deferred = step_m is None or step_m > maximum_context_step_m
    support_deferred = segment_count is None or segment_count < minimum_segment_count
    window_deferred = (
        event_window_days is None or event_window_days > maximum_event_window_days
    )

    if magnitude_deferred:
        status = "deferred_direct_thickness_magnitude"
        context_review_recommended = False
    elif support_deferred:
        status = "deferred_insufficient_spatial_support"
        context_review_recommended = False
    elif window_deferred:
        status = "deferred_event_window_too_broad"
        context_review_recommended = False
    else:
        status = "context_review_priority"
        context_review_recommended = True

    return {
        "schema": SCHEMA,
        "status": status,
        "candidate_id": dossier.get("candidate_id"),
        "median_step_m": step_m,
        "segment_count": segment_count,
        "event_start": event_start.isoformat() if event_start is not None else None,
        "event_end": event_end.isoformat() if event_end is not None else None,
        "event_window_days": event_window_days,
        "audit_parameters": {
            "maximum_context_step_m": maximum_context_step_m,
            "minimum_segment_count": minimum_segment_count,
            "maximum_event_window_days": maximum_event_window_days,
        },
        "decision": {
            "context_review_recommended": context_review_recommended,
            "records_research_recommended": False,
            "candidate_remains_depth_anchor": False,
        },
        "interpretation": {
            "context_review_means": (
                "check exact land, water, parcel, surface, and activity context "
                "before any permit or as-built records search"
            ),
            "large_magnitude_is_not_declared_impossible": True,
            "cause_confirmed": False,
            "placed_thickness_confirmed": False,
        },
        "does_not_prove": [
            "the apparent rise is earthwork",
            "the apparent rise is placed thickness",
            "the candidate is invalid",
            "buried object depth",
            "radar transferability",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prioritize one ICESat-2 candidate for context review."
    )
    parser.add_argument("--dossier", type=Path, default=DEFAULT_DOSSIER)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--maximum-context-step-m", type=float, default=5.0)
    parser.add_argument("--minimum-segment-count", type=int, default=4)
    parser.add_argument("--maximum-event-window-days", type=float, default=730.0)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    output_path = args.output_json or args.dossier.with_name(
        args.dossier.stem.replace("_dossier", "_context_priority_audit") + ".json"
    )
    try:
        dossier = _load_object(args.dossier)
        result = build_audit(
            dossier,
            maximum_context_step_m=args.maximum_context_step_m,
            minimum_segment_count=args.minimum_segment_count,
            maximum_event_window_days=args.maximum_event_window_days,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "context_priority_audit_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
