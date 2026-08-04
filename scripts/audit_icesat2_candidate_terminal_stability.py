"""Audit whether an ICESat-2 step remains stable in later independent epochs.

The temporal-recovery audit checks whether the oldest observation already
resembles the later plateau.  That is necessary but not sufficient: a candidate
can still rise for one or more cycles and later return to the pre-event level.
This audit adds two conservative gates before records research:

* immediate follow-up retention after the detected post cycle;
* terminal retention at the latest available independent cycle.

It does not query SlideRule, research records, create a depth anchor, invoke the
radar engine, or modify app artifacts.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

DEFAULT_DOSSIER = Path(
    "./data/research/icesat2_broad_track_scan/"
    "southwest_us_earthwork_pilot_v3_imperial_valley/"
    "candidate_001_dossier.json"
)
SCHEMA = "icesat2_candidate_terminal_stability_audit_v1"


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
    rows = [
        dict(value)
        for value in values
        if isinstance(value, dict)
        and isinstance(value.get("cycle"), int)
        and _number(value.get("height_m")) is not None
    ]
    rows.sort(
        key=lambda item: (
            int(item["cycle"]),
            str(item.get("observed_at", "")),
        )
    )
    return rows


def _row_for_cycle(
    rows: list[dict[str, Any]],
    cycle: int | None,
) -> dict[str, Any] | None:
    if not isinstance(cycle, int):
        return None
    matches = [item for item in rows if int(item["cycle"]) == cycle]
    return matches[-1] if matches else None


def audit_segment(
    segment: dict[str, Any],
    *,
    minimum_retention_fraction: float,
) -> dict[str, Any]:
    rows = _timeline_rows(segment)
    pre_cycle = segment.get("pre_cycle")
    post_cycle = segment.get("post_cycle")
    pre_row = _row_for_cycle(rows, pre_cycle if isinstance(pre_cycle, int) else None)
    post_row = _row_for_cycle(
        rows, post_cycle if isinstance(post_cycle, int) else None
    )

    pre_height = (
        _number(pre_row.get("height_m"))
        if pre_row
        else _number(segment.get("pre_median_m"))
    )
    post_height = (
        _number(post_row.get("height_m"))
        if post_row
        else _number(segment.get("post_median_m"))
    )
    observed_step = (
        post_height - pre_height
        if pre_height is not None and post_height is not None
        else None
    )
    reported_step = _number(segment.get("step_m"))
    reference_step = (
        observed_step
        if observed_step is not None and observed_step > 0.0
        else reported_step
    )

    followups = [
        item
        for item in rows
        if isinstance(post_cycle, int) and int(item["cycle"]) > post_cycle
    ]
    immediate = followups[0] if followups else None
    terminal = followups[-1] if followups else None

    def retention(item: dict[str, Any] | None) -> float | None:
        height = _number(item.get("height_m")) if item else None
        if (
            height is None
            or pre_height is None
            or reference_step is None
            or reference_step <= 0.0
        ):
            return None
        return (height - pre_height) / reference_step

    immediate_retention = retention(immediate)
    terminal_retention = retention(terminal)
    immediate_reversal = (
        immediate_retention is not None
        and immediate_retention < minimum_retention_fraction
    )
    terminal_reversal = (
        terminal_retention is not None
        and terminal_retention < minimum_retention_fraction
    )

    return {
        "segment_id": segment.get("segment_id"),
        "rgt": segment.get("rgt"),
        "spot": segment.get("spot"),
        "pre_cycle": pre_cycle,
        "post_cycle": post_cycle,
        "pre_height_m": pre_height,
        "post_height_m": post_height,
        "observed_event_step_m": observed_step,
        "reported_step_m": reported_step,
        "reference_step_m": reference_step,
        "followup_observation_count": len(followups),
        "immediate_followup_cycle": immediate.get("cycle") if immediate else None,
        "immediate_followup_height_m": (
            _number(immediate.get("height_m")) if immediate else None
        ),
        "immediate_retention_fraction": immediate_retention,
        "immediate_reversal_like": immediate_reversal,
        "terminal_cycle": terminal.get("cycle") if terminal else None,
        "terminal_height_m": _number(terminal.get("height_m")) if terminal else None,
        "terminal_retention_fraction": terminal_retention,
        "terminal_reversal_like": terminal_reversal,
    }


def build_audit(
    dossier: dict[str, Any],
    *,
    minimum_retention_fraction: float = 0.5,
    minimum_reversal_fraction: float = 0.6,
    minimum_followup_fraction: float = 0.6,
) -> dict[str, Any]:
    for name, value in (
        ("minimum_retention_fraction", minimum_retention_fraction),
        ("minimum_reversal_fraction", minimum_reversal_fraction),
        ("minimum_followup_fraction", minimum_followup_fraction),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be between 0 and 1")

    values = dossier.get("segments")
    if not isinstance(values, list):
        raise ValueError("candidate dossier has no segments list")
    segments = [dict(value) for value in values if isinstance(value, dict)]
    if not segments:
        raise ValueError("candidate dossier has no usable segments")

    rows = [
        audit_segment(
            item,
            minimum_retention_fraction=minimum_retention_fraction,
        )
        for item in segments
    ]
    followup_rows = [
        item for item in rows if int(item["followup_observation_count"]) > 0
    ]
    followup_fraction = len(followup_rows) / len(rows)
    immediate_rows = [
        item
        for item in rows
        if isinstance(item.get("immediate_retention_fraction"), (int, float))
    ]
    terminal_rows = [
        item
        for item in rows
        if isinstance(item.get("terminal_retention_fraction"), (int, float))
    ]
    immediate_reversal_count = sum(
        bool(item["immediate_reversal_like"]) for item in immediate_rows
    )
    terminal_reversal_count = sum(
        bool(item["terminal_reversal_like"]) for item in terminal_rows
    )
    immediate_reversal_fraction = (
        immediate_reversal_count / len(immediate_rows) if immediate_rows else None
    )
    terminal_reversal_fraction = (
        terminal_reversal_count / len(terminal_rows) if terminal_rows else None
    )
    immediate_retentions = [
        float(item["immediate_retention_fraction"]) for item in immediate_rows
    ]
    terminal_retentions = [
        float(item["terminal_retention_fraction"]) for item in terminal_rows
    ]

    insufficient_followup = followup_fraction < minimum_followup_fraction
    immediate_reversal_pattern = (
        immediate_reversal_fraction is not None
        and immediate_reversal_fraction >= minimum_reversal_fraction
    )
    terminal_reversal_pattern = (
        terminal_reversal_fraction is not None
        and terminal_reversal_fraction >= minimum_reversal_fraction
    )

    if insufficient_followup:
        status = "insufficient_followup_for_terminal_stability"
        recommended = False
    elif immediate_reversal_pattern:
        status = "immediate_post_step_reversal_pattern"
        recommended = False
    elif terminal_reversal_pattern:
        status = "late_epoch_reversal_pattern"
        recommended = False
    else:
        status = "terminal_stability_not_disproved"
        recommended = True

    return {
        "schema": SCHEMA,
        "status": status,
        "candidate_id": dossier.get("candidate_id"),
        "segment_count": len(rows),
        "segment_with_followup_count": len(followup_rows),
        "segment_with_followup_fraction": followup_fraction,
        "immediate_reversal_like_segment_count": immediate_reversal_count,
        "immediate_reversal_like_segment_fraction": immediate_reversal_fraction,
        "terminal_reversal_like_segment_count": terminal_reversal_count,
        "terminal_reversal_like_segment_fraction": terminal_reversal_fraction,
        "median_immediate_retention_fraction": (
            float(statistics.median(immediate_retentions))
            if immediate_retentions
            else None
        ),
        "median_terminal_retention_fraction": (
            float(statistics.median(terminal_retentions))
            if terminal_retentions
            else None
        ),
        "segment_audits": rows,
        "audit_parameters": {
            "minimum_retention_fraction": minimum_retention_fraction,
            "minimum_reversal_fraction": minimum_reversal_fraction,
            "minimum_followup_fraction": minimum_followup_fraction,
        },
        "decision": {
            "direct_thickness_anchor_lookup_recommended": recommended,
            "candidate_remains_depth_anchor": False,
            "records_research_started": False,
        },
        "interpretation": {
            "retention_fraction_means": (
                "fraction of the detected post-cycle rise still present relative "
                "to the exact pre-cycle height"
            ),
            "immediate_reversal_pattern_means": (
                "most supporting segments lost more than half of the rise at "
                "their first later independent epoch"
            ),
            "late_epoch_reversal_pattern_means": (
                "most supporting segments lost more than half of the rise by "
                "their latest available independent epoch"
            ),
            "cause_confirmed": False,
            "placed_thickness_confirmed": False,
        },
        "does_not_prove": [
            "the candidate is instrument error",
            "no earthwork occurred",
            "excavation depth",
            "placed material thickness",
            "buried object depth",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit one ICESat-2 candidate for later-epoch stability."
    )
    parser.add_argument("--dossier", type=Path, default=DEFAULT_DOSSIER)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--minimum-retention-fraction", type=float, default=0.5)
    parser.add_argument("--minimum-reversal-fraction", type=float, default=0.6)
    parser.add_argument("--minimum-followup-fraction", type=float, default=0.6)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    output_path = args.output_json or args.dossier.with_name(
        args.dossier.stem.replace("_dossier", "_terminal_stability_audit") + ".json"
    )
    try:
        dossier = _load_object(args.dossier)
        result = build_audit(
            dossier,
            minimum_retention_fraction=args.minimum_retention_fraction,
            minimum_reversal_fraction=args.minimum_reversal_fraction,
            minimum_followup_fraction=args.minimum_followup_fraction,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "terminal_stability_audit_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
