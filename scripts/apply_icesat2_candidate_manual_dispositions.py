"""Apply evidence-backed manual context dispositions to ICESat-2 candidates.

The automated broad-track finalizer stops at a context-review queue. This tool
applies explicit manual decisions made after parcel, imagery, land-use, or
project-footprint review. It never creates a depth anchor and never promotes a
candidate into records research.

The automated ``campaign_finalized_summary.json`` is preserved. The output is a
separate, authoritative campaign decision file:
``campaign_decision_summary.json``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_CAMPAIGN_DIR = Path(
    "./data/research/icesat2_broad_track_scan/southwest_us_earthwork_pilot_v1"
)
FINALIZED_SUMMARY_FILENAME = "campaign_finalized_summary.json"
MANUAL_DISPOSITIONS_FILENAME = "candidate_manual_dispositions.json"
OUTPUT_SUMMARY_FILENAME = "campaign_decision_summary.json"
SCHEMA = "icesat2_broad_track_campaign_decision_v1"
ALLOWED_CLOSED_STATUSES = {
    "closed_after_parcel_context",
    "closed_after_imagery_context",
    "closed_after_project_footprint_mismatch",
    "closed_after_manual_context_review",
}


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _campaign_rank(value: object, *, label: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must contain a positive campaign_rank")
    return value


def _load_dispositions(path: Path) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    payload = _load_object(path, label="manual dispositions")
    rows = payload.get("dispositions")
    if not isinstance(rows, list):
        raise ValueError("manual dispositions must contain a dispositions list")

    result: dict[int, dict[str, Any]] = {}
    for index, raw in enumerate(rows, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"manual disposition {index} must be an object")
        rank = _campaign_rank(
            raw.get("campaign_rank"), label=f"manual disposition {index}"
        )
        if rank in result:
            raise ValueError(f"duplicate manual disposition for campaign rank {rank}")
        status = raw.get("status")
        if status not in ALLOWED_CLOSED_STATUSES:
            raise ValueError(
                f"manual disposition rank {rank} has unsupported status: {status!r}"
            )
        reason = raw.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(
                f"manual disposition rank {rank} must contain a non-empty reason"
            )
        decision = raw.get("decision")
        if not isinstance(decision, dict):
            raise ValueError(
                f"manual disposition rank {rank} must contain a decision object"
            )
        if decision.get("context_review_recommended") is not False:
            raise ValueError(
                f"manual disposition rank {rank} must set "
                "context_review_recommended to false"
            )
        if decision.get("candidate_is_depth_anchor") is not False:
            raise ValueError(
                f"manual disposition rank {rank} must set "
                "candidate_is_depth_anchor to false"
            )
        result[rank] = dict(raw)
    return result, payload


def apply_manual_dispositions(
    *,
    campaign_dir: Path,
    dispositions_path: Path | None = None,
) -> dict[str, Any]:
    finalized_path = campaign_dir / FINALIZED_SUMMARY_FILENAME
    finalized = _load_object(finalized_path, label="finalized campaign summary")
    context_rows = finalized.get("context_review_priority")
    if not isinstance(context_rows, list):
        raise ValueError(
            "finalized campaign summary has no context_review_priority list"
        )

    manual_path = dispositions_path or campaign_dir / MANUAL_DISPOSITIONS_FILENAME
    dispositions, disposition_payload = _load_dispositions(manual_path)

    finalized_campaign_id = finalized.get("campaign_id")
    disposition_campaign_id = disposition_payload.get("campaign_id")
    if (
        isinstance(finalized_campaign_id, str)
        and isinstance(disposition_campaign_id, str)
        and disposition_campaign_id != finalized_campaign_id
    ):
        raise ValueError(
            "manual disposition campaign_id does not match finalized campaign"
        )

    remaining: list[dict[str, Any]] = []
    closures: list[dict[str, Any]] = []
    context_ranks: set[int] = set()

    for raw in context_rows:
        if not isinstance(raw, dict):
            continue
        candidate = dict(raw)
        rank = _campaign_rank(
            candidate.get("campaign_rank", candidate.get("source_campaign_rank")),
            label="context candidate",
        )
        context_ranks.add(rank)
        disposition = dispositions.get(rank)
        if disposition is None:
            remaining.append(candidate)
            continue
        candidate["manual_context_disposition"] = disposition
        closures.append(candidate)

    unknown_ranks = sorted(set(dispositions) - context_ranks)
    if unknown_ranks:
        joined = ", ".join(str(item) for item in unknown_ranks)
        raise ValueError(
            "manual dispositions reference candidates that are not in the "
            f"context-review queue: {joined}"
        )

    for index, candidate in enumerate(remaining, start=1):
        candidate["context_priority_rank"] = index

    if remaining:
        status = "manual_review_context_candidates_remaining"
    elif closures:
        status = "all_context_review_candidates_closed_by_manual_review"
    else:
        status = "no_context_review_candidates"

    result = {
        **finalized,
        "schema": SCHEMA,
        "status": status,
        "source_finalized_summary": str(finalized_path),
        "manual_dispositions_source": str(manual_path),
        "automated_context_review_candidate_count": len(
            [item for item in context_rows if isinstance(item, dict)]
        ),
        "manual_context_closed_count": len(closures),
        "manual_context_closures": closures,
        "context_review_candidate_count": len(remaining),
        "surviving_candidate_count": len(remaining),
        "context_review_priority": remaining,
        "record_lookup_priority": [],
        "records_research_ready": False,
        "interpretation": {
            **(
                finalized.get("interpretation")
                if isinstance(finalized.get("interpretation"), dict)
                else {}
            ),
            "manual_context_review_applied": True,
            "manual_closure_does_not_create_depth_anchor": True,
            "candidate_cause_confirmed": False,
            "candidate_is_depth_anchor": False,
            "app_behavior_changed": False,
        },
    }

    output_path = campaign_dir / OUTPUT_SUMMARY_FILENAME
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply manual context closures to a finalized campaign."
    )
    parser.add_argument("--campaign-dir", type=Path, default=DEFAULT_CAMPAIGN_DIR)
    parser.add_argument("--dispositions", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        result = apply_manual_dispositions(
            campaign_dir=args.campaign_dir,
            dispositions_path=args.dispositions,
        )
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "manual_disposition_application_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
