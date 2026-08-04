"""Finalize broad-track ICESat-2 candidates through temporal and context gates.

The first-stage broad scanner intentionally preserves every spatially supported
terrain-step cluster. This local finalizer reads that immutable scan output,
builds each candidate dossier, then applies:

1. the temporal-recovery audit, which rejects recovery from an older high
   surface;
2. the terminal-stability audit, which rejects rises that reverse at the first
   or latest available independent follow-up epoch; and
3. the context-priority audit, which defers extreme magnitudes, weak spatial
   support, and event windows too broad for efficient attribution.

The final output contains a ``context_review_priority`` list only. Records
research remains paused, and ``record_lookup_priority`` is intentionally empty,
until land/water/parcel context identifies a matching project footprint and
activity window.

This tool does not query SlideRule, modify tile caches, research records, create
a depth anchor, invoke the radar engine, or change app artifacts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    import sys

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_icesat2_candidate_context_priority import (
    build_audit as build_context_priority_audit,
)
from audit_icesat2_candidate_temporal_recovery import (
    build_audit as build_recovery_audit,
)
from audit_icesat2_candidate_terminal_stability import (
    build_audit as build_terminal_stability_audit,
)
from extract_icesat2_broad_candidate_dossier import build_dossier

DEFAULT_CAMPAIGN_DIR = Path(
    "./data/research/icesat2_broad_track_scan/southwest_us_earthwork_pilot_v1"
)
INPUT_SUMMARY_FILENAME = "campaign_summary.json"
OUTPUT_SUMMARY_FILENAME = "campaign_finalized_summary.json"
SCHEMA = "icesat2_broad_track_campaign_finalized_v3"


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _candidate_rank(row: dict[str, Any]) -> int:
    value = row.get("campaign_rank", row.get("global_rank"))
    if not isinstance(value, int) or value <= 0:
        raise ValueError("candidate is missing a positive campaign rank")
    return value


def _compact_recovery_audit(audit: dict[str, Any]) -> dict[str, Any]:
    decision = audit.get("decision")
    decision = decision if isinstance(decision, dict) else {}
    return {
        "status": audit.get("status"),
        "segment_count": audit.get("segment_count"),
        "recovery_like_segment_count": audit.get("recovery_like_segment_count"),
        "recovery_like_segment_fraction": audit.get(
            "recovery_like_segment_fraction"
        ),
        "median_earliest_to_post_net_change_m": audit.get(
            "median_earliest_to_post_net_change_m"
        ),
        "median_absolute_net_change_fraction_of_reported_step": audit.get(
            "median_absolute_net_change_fraction_of_reported_step"
        ),
        "direct_thickness_anchor_lookup_recommended": bool(
            decision.get("direct_thickness_anchor_lookup_recommended")
        ),
    }


def _compact_terminal_audit(audit: dict[str, Any]) -> dict[str, Any]:
    decision = audit.get("decision")
    decision = decision if isinstance(decision, dict) else {}
    return {
        "status": audit.get("status"),
        "segment_count": audit.get("segment_count"),
        "segment_with_followup_count": audit.get("segment_with_followup_count"),
        "segment_with_followup_fraction": audit.get(
            "segment_with_followup_fraction"
        ),
        "immediate_reversal_like_segment_count": audit.get(
            "immediate_reversal_like_segment_count"
        ),
        "immediate_reversal_like_segment_fraction": audit.get(
            "immediate_reversal_like_segment_fraction"
        ),
        "terminal_reversal_like_segment_count": audit.get(
            "terminal_reversal_like_segment_count"
        ),
        "terminal_reversal_like_segment_fraction": audit.get(
            "terminal_reversal_like_segment_fraction"
        ),
        "median_immediate_retention_fraction": audit.get(
            "median_immediate_retention_fraction"
        ),
        "median_terminal_retention_fraction": audit.get(
            "median_terminal_retention_fraction"
        ),
        "direct_thickness_anchor_lookup_recommended": bool(
            decision.get("direct_thickness_anchor_lookup_recommended")
        ),
    }


def _compact_context_audit(audit: dict[str, Any]) -> dict[str, Any]:
    decision = audit.get("decision")
    decision = decision if isinstance(decision, dict) else {}
    return {
        "status": audit.get("status"),
        "median_step_m": audit.get("median_step_m"),
        "segment_count": audit.get("segment_count"),
        "event_start": audit.get("event_start"),
        "event_end": audit.get("event_end"),
        "event_window_days": audit.get("event_window_days"),
        "context_review_recommended": bool(
            decision.get("context_review_recommended")
        ),
        "records_research_recommended": bool(
            decision.get("records_research_recommended")
        ),
    }


def finalize_campaign(
    *,
    campaign_dir: Path,
    maximum_net_fraction: float = 0.5,
    minimum_recovery_fraction: float = 0.6,
    minimum_retention_fraction: float = 0.5,
    minimum_reversal_fraction: float = 0.6,
    minimum_followup_fraction: float = 0.6,
    maximum_context_step_m: float = 5.0,
    minimum_context_segment_count: int = 4,
    maximum_context_event_window_days: float = 730.0,
) -> dict[str, Any]:
    source_path = campaign_dir / INPUT_SUMMARY_FILENAME
    source = _load_object(source_path, label="campaign summary")
    rows = source.get("record_lookup_priority")
    if not isinstance(rows, list):
        raise ValueError("campaign summary has no record_lookup_priority list")

    context_priority: list[dict[str, Any]] = []
    recovery_rejected: list[dict[str, Any]] = []
    terminal_rejected: list[dict[str, Any]] = []
    context_deferred: list[dict[str, Any]] = []
    candidate_audits: list[dict[str, Any]] = []
    region_cache: dict[str, dict[str, Any]] = {}

    for raw in rows:
        if not isinstance(raw, dict):
            continue
        candidate = dict(raw)
        rank = _candidate_rank(candidate)
        region_id = candidate.get("region_id")
        if not isinstance(region_id, str) or not region_id:
            raise ValueError(f"candidate rank {rank} is missing region_id")
        if region_id not in region_cache:
            region_cache[region_id] = _load_object(
                campaign_dir / region_id / "region_scan.json",
                label=f"region result {region_id}",
            )

        dossier = build_dossier(
            campaign_summary=source,
            region_result=region_cache[region_id],
            candidate_rank=rank,
        )
        recovery_audit = build_recovery_audit(
            dossier,
            maximum_net_fraction=maximum_net_fraction,
            minimum_recovery_fraction=minimum_recovery_fraction,
        )
        terminal_audit = build_terminal_stability_audit(
            dossier,
            minimum_retention_fraction=minimum_retention_fraction,
            minimum_reversal_fraction=minimum_reversal_fraction,
            minimum_followup_fraction=minimum_followup_fraction,
        )
        context_audit = build_context_priority_audit(
            dossier,
            maximum_context_step_m=maximum_context_step_m,
            minimum_segment_count=minimum_context_segment_count,
            maximum_event_window_days=maximum_context_event_window_days,
        )

        recovery_path = (
            campaign_dir / f"candidate_{rank:03d}_temporal_recovery_audit.json"
        )
        terminal_path = (
            campaign_dir / f"candidate_{rank:03d}_terminal_stability_audit.json"
        )
        context_path = (
            campaign_dir / f"candidate_{rank:03d}_context_priority_audit.json"
        )
        recovery_path.write_text(
            json.dumps(recovery_audit, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        terminal_path.write_text(
            json.dumps(terminal_audit, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        context_path.write_text(
            json.dumps(context_audit, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        compact_recovery = _compact_recovery_audit(recovery_audit)
        compact_terminal = _compact_terminal_audit(terminal_audit)
        compact_context = _compact_context_audit(context_audit)
        reviewed = {
            **candidate,
            "source_campaign_rank": rank,
            "temporal_recovery_audit": compact_recovery,
            "temporal_recovery_audit_json": str(recovery_path),
            "terminal_stability_audit": compact_terminal,
            "terminal_stability_audit_json": str(terminal_path),
            "context_priority_audit": compact_context,
            "context_priority_audit_json": str(context_path),
        }
        candidate_audits.append(reviewed)

        recovery_pass = compact_recovery[
            "direct_thickness_anchor_lookup_recommended"
        ]
        terminal_pass = compact_terminal[
            "direct_thickness_anchor_lookup_recommended"
        ]
        context_pass = compact_context["context_review_recommended"]
        if not recovery_pass:
            recovery_rejected.append(reviewed)
        elif not terminal_pass:
            terminal_rejected.append(reviewed)
        elif not context_pass:
            context_deferred.append(reviewed)
        else:
            context_priority.append(reviewed)

    for final_rank, item in enumerate(context_priority, start=1):
        item["context_priority_rank"] = final_rank

    failed_tiles = int(source.get("failed_tile_count", 0) or 0)
    if context_priority:
        status = "finalized_context_review_candidates_found"
    elif rows and context_deferred:
        status = "all_temporal_survivors_deferred_by_context_priority"
    elif rows and terminal_rejected:
        status = "all_spatial_candidates_rejected_by_temporal_or_terminal_stability"
    elif rows:
        status = "all_spatial_candidates_rejected_by_temporal_recovery"
    elif failed_tiles:
        status = "finalized_scan_incomplete_no_candidates_yet"
    else:
        status = "finalized_no_context_candidates"

    result = {
        "schema": SCHEMA,
        "status": status,
        "campaign_id": source.get("campaign_id"),
        "source_campaign_summary": str(source_path),
        "source_spatial_candidate_count": len(
            [item for item in rows if isinstance(item, dict)]
        ),
        "temporal_recovery_rejected_count": len(recovery_rejected),
        "terminal_stability_rejected_count": len(terminal_rejected),
        "context_priority_deferred_count": len(context_deferred),
        "context_review_candidate_count": len(context_priority),
        "surviving_candidate_count": len(context_priority),
        "context_review_priority": context_priority,
        "record_lookup_priority": [],
        "records_research_ready": False,
        "temporal_recovery_rejections": recovery_rejected,
        "terminal_stability_rejections": terminal_rejected,
        "context_priority_deferrals": context_deferred,
        "candidate_audits": candidate_audits,
        "failed_tile_count": failed_tiles,
        "audit_parameters": {
            "maximum_net_fraction": maximum_net_fraction,
            "minimum_recovery_fraction": minimum_recovery_fraction,
            "minimum_retention_fraction": minimum_retention_fraction,
            "minimum_reversal_fraction": minimum_reversal_fraction,
            "minimum_followup_fraction": minimum_followup_fraction,
            "maximum_context_step_m": maximum_context_step_m,
            "minimum_context_segment_count": minimum_context_segment_count,
            "maximum_context_event_window_days": (
                maximum_context_event_window_days
            ),
        },
        "interpretation": {
            "use_this_summary_for_context_review_decisions": True,
            "do_not_start_records_research_from_this_summary": True,
            "original_scan_summary_preserved": True,
            "spatial_support_alone_is_not_enough": True,
            "oldest_epoch_recovery_and_later_epoch_reversal_are_screened": True,
            "large_magnitude_deferral_does_not_mean_impossible": True,
            "candidate_cause_confirmed": False,
            "candidate_is_depth_anchor": False,
            "app_behavior_changed": False,
        },
        "does_not_prove": [
            "engineered fill",
            "placed material thickness",
            "depth to a buried object",
            "radar depth prediction",
        ],
    }
    output_path = campaign_dir / OUTPUT_SUMMARY_FILENAME
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Apply temporal and context-priority gates to broad-track "
            "candidates."
        )
    )
    parser.add_argument("--campaign-dir", type=Path, default=DEFAULT_CAMPAIGN_DIR)
    parser.add_argument("--maximum-net-fraction", type=float, default=0.5)
    parser.add_argument("--minimum-recovery-fraction", type=float, default=0.6)
    parser.add_argument("--minimum-retention-fraction", type=float, default=0.5)
    parser.add_argument("--minimum-reversal-fraction", type=float, default=0.6)
    parser.add_argument("--minimum-followup-fraction", type=float, default=0.6)
    parser.add_argument("--maximum-context-step-m", type=float, default=5.0)
    parser.add_argument("--minimum-context-segment-count", type=int, default=4)
    parser.add_argument(
        "--maximum-context-event-window-days",
        type=float,
        default=730.0,
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        result = finalize_campaign(
            campaign_dir=args.campaign_dir,
            maximum_net_fraction=args.maximum_net_fraction,
            minimum_recovery_fraction=args.minimum_recovery_fraction,
            minimum_retention_fraction=args.minimum_retention_fraction,
            minimum_reversal_fraction=args.minimum_reversal_fraction,
            minimum_followup_fraction=args.minimum_followup_fraction,
            maximum_context_step_m=args.maximum_context_step_m,
            minimum_context_segment_count=args.minimum_context_segment_count,
            maximum_context_event_window_days=(
                args.maximum_context_event_window_days
            ),
        )
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "broad_track_finalization_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
