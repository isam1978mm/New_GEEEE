"""Finalize broad-track ICESat-2 candidates through the recovery gate.

The first-stage broad scanner intentionally preserves every spatially supported
terrain-step cluster. This local second-stage tool reads that immutable scan
output, builds each candidate dossier, runs the temporal-recovery audit, and
writes a finalized campaign summary whose ``record_lookup_priority`` contains
only candidates that were not rejected as recovery from an older high surface.

It does not query SlideRule, modify tile caches, research records, create a
depth anchor, invoke the radar engine, or change app artifacts.
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

from audit_icesat2_candidate_temporal_recovery import build_audit
from extract_icesat2_broad_candidate_dossier import build_dossier

DEFAULT_CAMPAIGN_DIR = Path(
    "./data/research/icesat2_broad_track_scan/southwest_us_earthwork_pilot_v1"
)
INPUT_SUMMARY_FILENAME = "campaign_summary.json"
OUTPUT_SUMMARY_FILENAME = "campaign_finalized_summary.json"
SCHEMA = "icesat2_broad_track_campaign_finalized_v1"


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


def _compact_audit(audit: dict[str, Any]) -> dict[str, Any]:
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


def finalize_campaign(
    *,
    campaign_dir: Path,
    maximum_net_fraction: float = 0.5,
    minimum_recovery_fraction: float = 0.6,
) -> dict[str, Any]:
    source_path = campaign_dir / INPUT_SUMMARY_FILENAME
    source = _load_object(source_path, label="campaign summary")
    rows = source.get("record_lookup_priority")
    if not isinstance(rows, list):
        raise ValueError("campaign summary has no record_lookup_priority list")

    eligible: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
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
        audit = build_audit(
            dossier,
            maximum_net_fraction=maximum_net_fraction,
            minimum_recovery_fraction=minimum_recovery_fraction,
        )
        audit_path = campaign_dir / f"candidate_{rank:03d}_temporal_recovery_audit.json"
        audit_path.write_text(
            json.dumps(audit, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        compact = _compact_audit(audit)
        reviewed = {
            **candidate,
            "source_campaign_rank": rank,
            "temporal_recovery_audit": compact,
            "temporal_recovery_audit_json": str(audit_path),
        }
        candidate_audits.append(reviewed)
        if compact["direct_thickness_anchor_lookup_recommended"]:
            eligible.append(reviewed)
        else:
            rejected.append(reviewed)

    for final_rank, item in enumerate(eligible, start=1):
        item["finalized_campaign_rank"] = final_rank

    failed_tiles = int(source.get("failed_tile_count", 0) or 0)
    if eligible:
        status = "finalized_record_candidates_found"
    elif rows:
        status = "all_spatial_candidates_rejected_by_temporal_recovery"
    elif failed_tiles:
        status = "finalized_scan_incomplete_no_candidates_yet"
    else:
        status = "finalized_no_record_candidates"

    result = {
        "schema": SCHEMA,
        "status": status,
        "campaign_id": source.get("campaign_id"),
        "source_campaign_summary": str(source_path),
        "source_spatial_candidate_count": len(
            [item for item in rows if isinstance(item, dict)]
        ),
        "temporal_recovery_rejected_count": len(rejected),
        "surviving_candidate_count": len(eligible),
        "record_lookup_priority": eligible,
        "temporal_recovery_rejections": rejected,
        "candidate_audits": candidate_audits,
        "failed_tile_count": failed_tiles,
        "audit_parameters": {
            "maximum_net_fraction": maximum_net_fraction,
            "minimum_recovery_fraction": minimum_recovery_fraction,
        },
        "interpretation": {
            "use_this_summary_for_records_decisions": True,
            "original_scan_summary_preserved": True,
            "spatial_support_alone_is_not_enough": True,
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
        description="Apply the temporal-recovery gate to broad-track candidates."
    )
    parser.add_argument("--campaign-dir", type=Path, default=DEFAULT_CAMPAIGN_DIR)
    parser.add_argument("--maximum-net-fraction", type=float, default=0.5)
    parser.add_argument("--minimum-recovery-fraction", type=float, default=0.6)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        result = finalize_campaign(
            campaign_dir=args.campaign_dir,
            maximum_net_fraction=args.maximum_net_fraction,
            minimum_recovery_fraction=args.minimum_recovery_fraction,
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
