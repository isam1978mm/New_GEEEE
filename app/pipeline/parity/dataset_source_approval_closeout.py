from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Mapping

from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.dataset_source_review import (
    get_arxiv_2602_19608_source_review_record,
)
from app.pipeline.parity.dataset_source_sensitivity_decision import (
    get_default_dafa_ls_sensitivity_decision_record,
)
from app.services.redaction import verify_redacted


FUTURE_SLICE_13E_SCHEMA_VERSION = "future_slice_13e_source_approval_closeout_v1"
FUTURE_SLICE_13E_REPORT_RELATIVE_PATH = (
    "manifests/future_slice_13e_source_approval_closeout.json"
)

_NEXT_ALLOWED_PATHS = (
    "new_candidate_source_review_under_new_scoped_goal",
    "operator_provided_independent_evidence_under_new_scoped_goal",
    "future_i2_assembly_only_after_a_candidate_passes_all_slice_13_gates",
)


def get_slice_13_source_approval_closeout() -> dict[str, Any]:
    """Return the redacted Slice 13E closeout for current known public leads."""

    dafa_decision = get_default_dafa_ls_sensitivity_decision_record()
    arxiv_review = get_arxiv_2602_19608_source_review_record()
    current_decisions = [
        {
            "candidate_id": str(dafa_decision["candidate_id"]),
            "source_name": str(dafa_decision["source_name"]),
            "final_decision": str(dafa_decision["final_decision"]),
            "blocking_gate": "sensitivity_misuse",
            "i2_routing_allowed": False,
        },
        {
            "candidate_id": arxiv_review["candidate_id"],
            "source_name": arxiv_review["source_name"],
            "final_decision": arxiv_review["final_decision"],
            "blocking_gate": "sensitivity_misuse",
            "i2_routing_allowed": False,
        },
    ]
    _validate_current_decisions(current_decisions)

    rejected_leads = [
        decision["candidate_id"]
        for decision in current_decisions
        if decision["final_decision"] == "rejected"
    ]
    closeout: dict[str, Any] = {
        "closeout_id": "future_slice_13e_current_known_leads",
        "known_leads_reviewed": [decision["candidate_id"] for decision in current_decisions],
        "rejected_leads": rejected_leads,
        "deferred_leads": [],
        "conditionally_approved_for_i2": [],
        "i2_routing_allowed": False,
        "h3_training_allowed": False,
        "h4_inference_allowed": False,
        "slice_13_current_known_leads_complete": True,
        "current_known_lead_decisions": current_decisions,
        "blockers_summary": (
            "Both current known public leads are rejected at Gate 1. No candidate "
            "passes all Slice 13 gates, no I2 routing is allowed, and H3/H4 "
            "remain blocked."
        ),
        "next_allowed_paths": list(_NEXT_ALLOWED_PATHS),
        "future_unknown_candidates_rejected": False,
        "dataset_downloaded": False,
        "dataset_created": False,
        "i2_pack_created": False,
        "training_added": False,
        "inference_added": False,
        "ml_dependencies_added": False,
        "earth_engine_calls_added": False,
        "public_exposure_changes": False,
        "notes": (
            "Slice 13E closes only the current known public-lead set. Future "
            "unknown candidates require a new scoped Slice 13-style review goal."
        ),
    }
    _validate_closeout(closeout)
    return closeout


def write_slice_13_source_approval_closeout_report(
    *,
    run_dir: str | Path,
    run_id: str,
    closeout: Mapping[str, Any] | None = None,
    report_relative_path: str | Path = FUTURE_SLICE_13E_REPORT_RELATIVE_PATH,
) -> Path:
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    closeout_payload = dict(closeout or get_slice_13_source_approval_closeout())
    _validate_closeout(closeout_payload)
    payload: dict[str, Any] = {
        "schema_version": FUTURE_SLICE_13E_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        **closeout_payload,
    }
    verify_redacted(payload)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _validate_current_decisions(decisions: list[dict[str, Any]]) -> None:
    expected_ids = (
        "dafa_ls_arxiv_2409_09432",
        "arxiv_2602_19608_looted_sites",
    )
    if tuple(decision.get("candidate_id") for decision in decisions) != expected_ids:
        raise ValueError("Slice 13E closeout must include the current known leads")
    for decision in decisions:
        if decision.get("final_decision") != "rejected":
            raise ValueError("current known lead must be rejected for closeout")
        if decision.get("blocking_gate") != "sensitivity_misuse":
            raise ValueError("current known lead closeout expects Gate 1 blocker")
        if decision.get("i2_routing_allowed") is not False:
            raise ValueError("current known lead closeout cannot allow I2 routing")


def _validate_closeout(closeout: Mapping[str, Any]) -> None:
    required_fields = {
        "closeout_id",
        "known_leads_reviewed",
        "rejected_leads",
        "deferred_leads",
        "conditionally_approved_for_i2",
        "i2_routing_allowed",
        "h3_training_allowed",
        "h4_inference_allowed",
        "slice_13_current_known_leads_complete",
        "current_known_lead_decisions",
        "blockers_summary",
        "next_allowed_paths",
        "future_unknown_candidates_rejected",
        "dataset_downloaded",
        "dataset_created",
        "i2_pack_created",
        "training_added",
        "inference_added",
        "ml_dependencies_added",
        "earth_engine_calls_added",
        "public_exposure_changes",
        "notes",
    }
    if set(closeout) != required_fields:
        raise ValueError("Slice 13E closeout fields do not match schema")
    _validate_current_decisions(list(closeout["current_known_lead_decisions"]))

    if closeout["conditionally_approved_for_i2"] != []:
        raise ValueError("Slice 13E has no candidate approved for I2")
    for field in (
        "i2_routing_allowed",
        "h3_training_allowed",
        "h4_inference_allowed",
        "dataset_downloaded",
        "dataset_created",
        "i2_pack_created",
        "training_added",
        "inference_added",
        "ml_dependencies_added",
        "earth_engine_calls_added",
        "public_exposure_changes",
        "future_unknown_candidates_rejected",
    ):
        if closeout[field] is not False:
            raise ValueError(f"Slice 13E requires {field}=false")
    if closeout["slice_13_current_known_leads_complete"] is not True:
        raise ValueError("Slice 13E must close the current known-lead set")
    if tuple(closeout["next_allowed_paths"]) != _NEXT_ALLOWED_PATHS:
        raise ValueError("Slice 13E next allowed paths changed")
    verify_redacted(closeout)
