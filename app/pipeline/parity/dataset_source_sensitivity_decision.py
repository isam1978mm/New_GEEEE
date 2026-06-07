from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Mapping

from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.dataset_source_review import (
    get_first_candidate_source_review_record,
)
from app.services.redaction import verify_redacted


FUTURE_SLICE_13C_SCHEMA_VERSION = "future_slice_13c_dafa_ls_sensitivity_v1"
FUTURE_SLICE_13C_REPORT_RELATIVE_PATH = (
    "manifests/future_slice_13c_dafa_ls_sensitivity_decision.json"
)

ALLOWED_SENSITIVITY_DECISIONS = (
    "sensitivity_reject",
    "sensitivity_needs_restricted_human_governance",
    "sensitivity_pass_with_restrictions",
)

_DECISION_RULES = {
    "sensitivity_reject": {
        "sensitivity_status": "reject",
        "final_decision": "rejected",
        "allowed_next_state": "rejected",
        "i2_routing_allowed": False,
        "public_summary": (
            "DAFA-LS Gate 1 rejects I2 routing for this lead. H3 and H4 remain "
            "blocked."
        ),
    },
    "sensitivity_needs_restricted_human_governance": {
        "sensitivity_status": "needs_human_review",
        "final_decision": "under_review",
        "allowed_next_state": "under_review",
        "i2_routing_allowed": False,
        "public_summary": (
            "DAFA-LS Gate 1 remains under restricted human governance. I2, H3, "
            "and H4 remain blocked."
        ),
    },
    "sensitivity_pass_with_restrictions": {
        "sensitivity_status": "pass",
        "final_decision": "under_review",
        "allowed_next_state": "gate_2_to_6_review_required",
        "i2_routing_allowed": False,
        "public_summary": (
            "DAFA-LS Gate 1 would require restrictions, but Gates 2 through 6 "
            "still block I2 routing."
        ),
    },
}


def get_default_dafa_ls_sensitivity_decision_record() -> dict[str, object]:
    return build_dafa_ls_sensitivity_decision_record(
        prior_review=get_first_candidate_source_review_record(),
        sensitivity_decision="sensitivity_reject",
    )


def build_dafa_ls_sensitivity_decision_record(
    *,
    prior_review: Mapping[str, str],
    sensitivity_decision: str,
) -> dict[str, object]:
    if sensitivity_decision not in ALLOWED_SENSITIVITY_DECISIONS:
        raise ValueError(f"unsupported sensitivity decision: {sensitivity_decision}")
    if prior_review.get("candidate_id") != "dafa_ls_arxiv_2409_09432":
        raise ValueError("Slice 13C only records the DAFA-LS candidate decision")

    rule = _DECISION_RULES[sensitivity_decision]
    record: dict[str, object] = {
        "candidate_id": str(prior_review["candidate_id"]),
        "source_name": str(prior_review["source_name"]),
        "prior_review_reference": "future_slice_13b_first_source_review",
        "gate_name": "sensitivity_misuse",
        "sensitivity_decision": sensitivity_decision,
        "sensitivity_status": rule["sensitivity_status"],
        "misuse_risk_level": "high",
        "sensitive_data_categories": [
            "heritage_place_imagery",
            "vulnerable_place_context",
            "misuse_sensitive_training_lead",
        ],
        "public_summary": rule["public_summary"],
        "decision_rationale_redacted": (
            "DAFA-LS is associated with looting and preserved archaeological-place "
            "imagery. This committed record keeps only source-level metadata and "
            "does not include source payload details."
        ),
        "allowed_next_state": rule["allowed_next_state"],
        "final_decision": rule["final_decision"],
        "h3_training_allowed": False,
        "h4_inference_allowed": False,
        "i2_routing_allowed": rule["i2_routing_allowed"],
        "dataset_downloaded": False,
        "dataset_created": False,
        "i2_pack_created": False,
        "training_added": False,
        "inference_added": False,
        "public_exposure_changes": False,
        "notes": (
            "Slice 13C records Gate 1 only. Gates 2 through 6 are not changed "
            "by this decision record."
        ),
    }
    _validate_decision_record(record)
    return record


def write_dafa_ls_sensitivity_decision_report(
    *,
    run_dir: str | Path,
    run_id: str,
    decision_record: Mapping[str, object] | None = None,
    report_relative_path: str | Path = FUTURE_SLICE_13C_REPORT_RELATIVE_PATH,
) -> Path:
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    record = dict(decision_record or get_default_dafa_ls_sensitivity_decision_record())
    _validate_decision_record(record)
    payload: dict[str, Any] = {
        "schema_version": FUTURE_SLICE_13C_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "sensitivity_decision_record": record,
        "final_decision": record["final_decision"],
        "h3_training_allowed": False,
        "h4_inference_allowed": False,
        "i2_routing_allowed": record["i2_routing_allowed"],
        "dataset_downloaded": False,
        "dataset_created": False,
        "i2_pack_created": False,
        "training_added": False,
        "inference_added": False,
        "ml_dependencies_added": False,
        "earth_engine_calls_added": False,
        "public_exposure_changes": False,
        "notes": (
            "Slice 13C is a redacted Gate 1 decision record only. It does not "
            "create candidate data, an I2 pack, training, inference, or public "
            "exposure."
        ),
    }
    verify_redacted(payload)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _validate_decision_record(record: Mapping[str, object]) -> None:
    required_fields = {
        "candidate_id",
        "source_name",
        "prior_review_reference",
        "gate_name",
        "sensitivity_decision",
        "sensitivity_status",
        "misuse_risk_level",
        "sensitive_data_categories",
        "public_summary",
        "decision_rationale_redacted",
        "allowed_next_state",
        "final_decision",
        "h3_training_allowed",
        "h4_inference_allowed",
        "i2_routing_allowed",
        "dataset_downloaded",
        "dataset_created",
        "i2_pack_created",
        "training_added",
        "inference_added",
        "public_exposure_changes",
        "notes",
    }
    if set(record) != required_fields:
        raise ValueError("Slice 13C decision record fields do not match schema")
    decision = str(record["sensitivity_decision"])
    if decision not in ALLOWED_SENSITIVITY_DECISIONS:
        raise ValueError("unsupported sensitivity decision")
    rule = _DECISION_RULES[decision]
    if record["sensitivity_status"] != rule["sensitivity_status"]:
        raise ValueError("sensitivity status does not match decision rule")
    if record["final_decision"] != rule["final_decision"]:
        raise ValueError("final decision does not match sensitivity rule")
    if record["i2_routing_allowed"] is not False:
        raise ValueError("Slice 13C does not allow I2 routing")
    if record["h3_training_allowed"] is not False:
        raise ValueError("Slice 13C does not allow H3")
    if record["h4_inference_allowed"] is not False:
        raise ValueError("Slice 13C does not allow H4")
    if record["public_exposure_changes"] is not False:
        raise ValueError("Slice 13C does not allow public exposure")
    verify_redacted(record)
