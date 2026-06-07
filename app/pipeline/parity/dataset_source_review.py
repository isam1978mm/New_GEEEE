from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Mapping

from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.dataset_source_candidate_register import (
    CANDIDATE_RECORD_FIELDS,
    CANDIDATE_REVIEW_GATE_NAMES,
    CANDIDATE_STATUS_VALUES,
)
from app.services.redaction import verify_redacted


FUTURE_SLICE_13B_SCHEMA_VERSION = "future_slice_13b_first_source_review_v1"
FUTURE_SLICE_13B_REPORT_RELATIVE_PATH = (
    "manifests/future_slice_13b_first_source_review.json"
)
FUTURE_SLICE_13D_SCHEMA_VERSION = "future_slice_13d_arxiv_2602_19608_source_review_v1"
FUTURE_SLICE_13D_REPORT_RELATIVE_PATH = (
    "manifests/future_slice_13d_arxiv_2602_19608_source_review.json"
)

GATE_STATUS_VALUES = (
    "pass",
    "reject",
    "needs_human_review",
    "insufficient_information",
    "weak_signal_only",
    "not_applicable",
)
FINAL_DECISION_VALUES = (
    "rejected",
    "under_review",
    "conditionally_approved_for_I2",
)

_GATE_STATUS_FIELDS = {
    "sensitivity_misuse": "sensitivity_status",
    "independent_evidence": "independence_status",
    "provenance_labeling_method": "provenance_status",
    "license_access_terms": "license_status",
    "storage_redaction": "storage_status",
    "i2_validator_compatibility": "i2_compatibility_status",
}

_GATE_BLOCKER_FIELDS = {
    "sensitivity_misuse": "sensitivity_blocker",
    "independent_evidence": "independence_blocker",
    "provenance_labeling_method": "provenance_blocker",
    "license_access_terms": "license_blocker",
    "storage_redaction": "storage_blocker",
    "i2_validator_compatibility": "i2_compatibility_blocker",
}

_DEFAULT_DECISIONS = {
    "sensitivity_status": {
        "pass": "sensitivity_gate_passed_for_i2_routing",
        "reject": "reject_before_i2",
        "needs_human_review": "block_i2_until_human_sensitivity_review",
        "insufficient_information": "block_i2_until_sensitivity_review_is_complete",
        "weak_signal_only": "block_i2_until_sensitivity_review_is_complete",
        "not_applicable": "block_i2_until_sensitivity_review_is_complete",
    },
    "independence_status": {
        "pass": "independent_evidence_gate_passed_for_i2_routing",
        "reject": "reject_before_i2",
        "needs_human_review": "block_i2_until_independent_evidence_is_reviewed",
        "insufficient_information": "block_i2_until_independent_evidence_is_documented",
        "weak_signal_only": "block_i2_until_independent_evidence_is_documented",
        "not_applicable": "block_i2_until_independent_evidence_is_documented",
    },
    "provenance_status": {
        "pass": "labeling_method_gate_passed_for_i2_routing",
        "reject": "reject_before_i2",
        "needs_human_review": "block_i2_until_labeling_method_is_reviewed",
        "insufficient_information": "block_i2_until_labeling_method_is_reviewed",
        "weak_signal_only": "block_i2_until_labeling_method_is_reviewed",
        "not_applicable": "block_i2_until_labeling_method_is_reviewed",
    },
    "license_status": {
        "pass": "license_gate_passed_for_i2_routing",
        "reject": "reject_before_i2",
        "needs_human_review": "block_i2_until_license_terms_are_reviewed",
        "insufficient_information": "block_i2_until_license_terms_are_reviewed",
        "weak_signal_only": "block_i2_until_license_terms_are_reviewed",
        "not_applicable": "block_i2_until_license_terms_are_reviewed",
    },
    "storage_status": {
        "pass": "private_storage_gate_passed_for_i2_routing",
        "reject": "reject_before_i2",
        "needs_human_review": "block_i2_until_storage_redaction_plan_is_reviewed",
        "insufficient_information": "block_i2_until_storage_redaction_plan_is_reviewed",
        "weak_signal_only": "block_i2_until_storage_redaction_plan_is_reviewed",
        "not_applicable": "block_i2_until_storage_redaction_plan_is_reviewed",
    },
    "i2_compatibility_status": {
        "pass": "i2_schema_gate_passed_for_i2_routing",
        "reject": "reject_before_i2",
        "needs_human_review": "block_i2_until_schema_fit_is_reviewed",
        "insufficient_information": "block_i2_until_schema_fit_is_reviewed",
        "weak_signal_only": "block_i2_until_schema_fit_is_reviewed",
        "not_applicable": "block_i2_until_schema_fit_is_reviewed",
    },
}

_DEFAULT_BLOCKERS = {
    "sensitivity_status": {
        "pass": "",
        "reject": "sensitivity_or_misuse_gate_rejected_the_candidate",
        "needs_human_review": "sensitive_heritage_location_risk_needs_human_review",
        "insufficient_information": "sensitivity_or_misuse_details_are_incomplete",
        "weak_signal_only": "sensitivity_or_misuse_details_are_incomplete",
        "not_applicable": "sensitivity_or_misuse_gate_must_be_reviewed",
    },
    "independence_status": {
        "pass": "",
        "reject": "independent_evidence_gate_rejected_the_candidate",
        "needs_human_review": "independent_evidence_needs_human_review",
        "insufficient_information": "independent_evidence_is_not_documented",
        "weak_signal_only": "labels_are_weak_signal_only_for_training",
        "not_applicable": "independent_evidence_gate_must_be_reviewed",
    },
    "provenance_status": {
        "pass": "",
        "reject": "labeling_method_gate_rejected_the_candidate",
        "needs_human_review": "labeling_method_needs_human_review",
        "insufficient_information": "labeling_method_details_are_incomplete",
        "weak_signal_only": "labeling_method_supports_weak_signal_only",
        "not_applicable": "labeling_method_gate_must_be_reviewed",
    },
    "license_status": {
        "pass": "",
        "reject": "license_or_access_terms_rejected_the_candidate",
        "needs_human_review": "license_or_access_terms_need_human_review",
        "insufficient_information": "license_or_access_terms_are_incomplete",
        "weak_signal_only": "license_or_access_terms_are_incomplete",
        "not_applicable": "license_or_access_terms_must_be_reviewed",
    },
    "storage_status": {
        "pass": "",
        "reject": "private_storage_or_redaction_gate_rejected_the_candidate",
        "needs_human_review": "private_storage_redaction_plan_needs_human_review",
        "insufficient_information": "private_storage_redaction_plan_is_incomplete",
        "weak_signal_only": "private_storage_redaction_plan_is_incomplete",
        "not_applicable": "private_storage_redaction_gate_must_be_reviewed",
    },
    "i2_compatibility_status": {
        "pass": "",
        "reject": "i2_schema_gate_rejected_the_candidate",
        "needs_human_review": "i2_schema_fit_needs_human_review",
        "insufficient_information": "i2_schema_fit_is_incomplete",
        "weak_signal_only": "i2_schema_fit_is_incomplete",
        "not_applicable": "i2_schema_gate_must_be_reviewed",
    },
}


def get_first_candidate_source_review_record(
    *,
    reviewer: str = "codex_slice_13b",
    review_date: str | None = None,
) -> dict[str, str]:
    """Return the redacted metadata-only review for the first Slice 13B lead."""

    return build_candidate_source_review_record(
        candidate_id="dafa_ls_arxiv_2409_09432",
        source_name="DAFA-LS public metadata lead",
        source_reference="arXiv:2409.09432; ElliotVincent/DAFA-LS public repository",
        source_url_or_doi="https://arxiv.org/abs/2409.09432",
        source_type="public_paper_and_repository_metadata",
        reviewer=reviewer,
        review_date=review_date or datetime.now(UTC).date().isoformat(),
        sensitivity_status="needs_human_review",
        sensitivity_decision="block_i2_until_human_sensitivity_review",
        sensitivity_blocker=(
            "Sensitive heritage-site and vulnerable-place risk cannot pass from "
            "metadata-only review."
        ),
        independence_status="weak_signal_only",
        independence_decision="block_i2_until_independent_evidence_is_documented",
        independence_blocker=(
            "Public metadata does not establish labels independent of modeled imagery "
            "signals."
        ),
        provenance_status="insufficient_information",
        provenance_decision="block_i2_until_labeling_method_is_reviewed",
        provenance_blocker=(
            "Metadata-only review does not establish reproducible label production, "
            "review, and adjudication details."
        ),
        license_status="insufficient_information",
        license_decision="block_i2_until_license_terms_are_reviewed",
        license_blocker=(
            "Public metadata was not enough to review dataset access, reuse, and "
            "redistribution terms for a private I2 pack."
        ),
        storage_status="needs_human_review",
        storage_decision="block_i2_until_storage_redaction_plan_is_reviewed",
        storage_blocker=(
            "Location-bearing source material would need LOCAL_SENSITIVE or "
            "FILESYSTEM_ONLY handling plus public-summary redaction review."
        ),
        i2_compatibility_status="insufficient_information",
        i2_compatibility_decision="block_i2_until_schema_fit_is_reviewed",
        i2_compatibility_blocker=(
            "No private pack was assembled, so I1/I2 schema fit cannot be evaluated."
        ),
        final_decision="under_review",
        final_blocker=(
            "Gate 1 human sensitivity review and evidence, method, license, storage, "
            "and I2-fit reviews remain open."
        ),
        notes=(
            "Metadata-only review of public paper and repository lead. No source "
            "payload, imagery, masks, labels, site records, archives, private "
            "register, I2 pack, training, or inference were created."
        ),
    )


def get_arxiv_2602_19608_source_review_record(
    *,
    reviewer: str = "codex_slice_13d",
    review_date: str | None = None,
) -> dict[str, str]:
    """Return the redacted metadata-only review for the Slice 13D lead."""

    return build_candidate_source_review_record(
        candidate_id="arxiv_2602_19608_looted_sites",
        source_name="arXiv 2602.19608 public metadata lead",
        source_reference=(
            "arXiv:2602.19608; microsoft/looted_site_detection public "
            "repository metadata"
        ),
        source_url_or_doi="https://doi.org/10.48550/arXiv.2602.19608",
        source_type="public_paper_and_repository_metadata",
        reviewer=reviewer,
        review_date=review_date or datetime.now(UTC).date().isoformat(),
        sensitivity_status="reject",
        sensitivity_decision="reject_before_i2",
        sensitivity_blocker=(
            "Gate 1 rejects I2 routing because public metadata describes "
            "looting-related heritage-place imagery, preserved-place examples, "
            "and footprint-mask material."
        ),
        independence_status="weak_signal_only",
        independence_decision="block_i2_until_independent_evidence_is_documented",
        independence_blocker=(
            "Public metadata does not establish reviewed-tier labels independent "
            "of modeled imagery signals."
        ),
        provenance_status="insufficient_information",
        provenance_decision="block_i2_until_labeling_method_is_reviewed",
        provenance_blocker=(
            "Metadata-only review does not establish a reviewed-tier label "
            "production, review, and adjudication method acceptable for I2."
        ),
        license_status="insufficient_information",
        license_decision="block_i2_until_license_terms_are_reviewed",
        license_blocker=(
            "Paper and code metadata do not establish acceptable dataset-payload "
            "access, reuse, and redistribution terms for a private I2 pack."
        ),
        storage_status="needs_human_review",
        storage_decision="block_i2_until_storage_redaction_plan_is_reviewed",
        storage_blocker=(
            "Footprint masks, place identifiers, and related source material "
            "would need restricted LOCAL_SENSITIVE or FILESYSTEM_ONLY handling "
            "and redaction review."
        ),
        i2_compatibility_status="insufficient_information",
        i2_compatibility_decision="block_i2_until_schema_fit_is_reviewed",
        i2_compatibility_blocker=(
            "No private pack was assembled, so I1/I2 schema fit cannot be "
            "evaluated."
        ),
        final_decision="rejected",
        final_blocker=(
            "Gate 1 sensitivity/misuse rejection blocks I2 routing. Independent "
            "evidence, method, license/access, storage/redaction, and I2-fit "
            "reviews also do not pass from metadata-only review."
        ),
        notes=(
            "Metadata-only review of public paper and repository metadata. No "
            "source payload, imagery, masks, labels, place records, archives, "
            "private register, I2 pack, training, or inference were created."
        ),
    )


def build_candidate_source_review_record(
    *,
    candidate_id: str,
    source_name: str,
    source_reference: str,
    source_url_or_doi: str,
    source_type: str,
    reviewer: str,
    review_date: str,
    sensitivity_status: str,
    independence_status: str,
    provenance_status: str,
    license_status: str,
    storage_status: str,
    i2_compatibility_status: str,
    sensitivity_decision: str | None = None,
    sensitivity_blocker: str | None = None,
    independence_decision: str | None = None,
    independence_blocker: str | None = None,
    provenance_decision: str | None = None,
    provenance_blocker: str | None = None,
    license_decision: str | None = None,
    license_blocker: str | None = None,
    storage_decision: str | None = None,
    storage_blocker: str | None = None,
    i2_compatibility_decision: str | None = None,
    i2_compatibility_blocker: str | None = None,
    final_decision: str | None = None,
    final_blocker: str | None = None,
    notes: str = "",
) -> dict[str, str]:
    statuses = {
        "sensitivity_status": sensitivity_status,
        "independence_status": independence_status,
        "provenance_status": provenance_status,
        "license_status": license_status,
        "storage_status": storage_status,
        "i2_compatibility_status": i2_compatibility_status,
    }
    for field, status in statuses.items():
        _validate_status(field, status)

    computed_final = decide_final_review_status(statuses)
    if final_decision is not None and final_decision != computed_final:
        if final_decision == "conditionally_approved_for_I2":
            raise ValueError(
                "conditionally_approved_for_I2 requires all six gates to pass"
            )
        raise ValueError(f"final_decision must be {computed_final!r}")

    record = {
        "candidate_id": candidate_id,
        "source_name": source_name,
        "source_reference": source_reference,
        "source_url_or_doi": source_url_or_doi,
        "source_type": source_type,
        "lead_status": "unverified_lead",
        "review_status": computed_final,
        "sensitivity_status": sensitivity_status,
        "sensitivity_decision": sensitivity_decision
        or _DEFAULT_DECISIONS["sensitivity_status"][sensitivity_status],
        "sensitivity_blocker": sensitivity_blocker
        if sensitivity_blocker is not None
        else _DEFAULT_BLOCKERS["sensitivity_status"][sensitivity_status],
        "independence_status": independence_status,
        "independence_decision": independence_decision
        or _DEFAULT_DECISIONS["independence_status"][independence_status],
        "independence_blocker": independence_blocker
        if independence_blocker is not None
        else _DEFAULT_BLOCKERS["independence_status"][independence_status],
        "provenance_status": provenance_status,
        "provenance_decision": provenance_decision
        or _DEFAULT_DECISIONS["provenance_status"][provenance_status],
        "provenance_blocker": provenance_blocker
        if provenance_blocker is not None
        else _DEFAULT_BLOCKERS["provenance_status"][provenance_status],
        "license_status": license_status,
        "license_decision": license_decision
        or _DEFAULT_DECISIONS["license_status"][license_status],
        "license_blocker": license_blocker
        if license_blocker is not None
        else _DEFAULT_BLOCKERS["license_status"][license_status],
        "storage_status": storage_status,
        "storage_decision": storage_decision
        or _DEFAULT_DECISIONS["storage_status"][storage_status],
        "storage_blocker": storage_blocker
        if storage_blocker is not None
        else _DEFAULT_BLOCKERS["storage_status"][storage_status],
        "i2_compatibility_status": i2_compatibility_status,
        "i2_compatibility_decision": i2_compatibility_decision
        or _DEFAULT_DECISIONS["i2_compatibility_status"][i2_compatibility_status],
        "i2_compatibility_blocker": i2_compatibility_blocker
        if i2_compatibility_blocker is not None
        else _DEFAULT_BLOCKERS["i2_compatibility_status"][i2_compatibility_status],
        "final_decision": computed_final,
        "final_blocker": final_blocker
        if final_blocker is not None
        else _default_final_blocker(statuses),
        "reviewer": reviewer,
        "review_date": review_date,
        "notes": notes,
    }
    _validate_record(record)
    return record


def summarize_gate_statuses(candidate_review: Mapping[str, str]) -> dict[str, str]:
    return {
        gate_name: str(candidate_review[_GATE_STATUS_FIELDS[gate_name]])
        for gate_name in CANDIDATE_REVIEW_GATE_NAMES
    }


def decide_final_review_status(statuses: Mapping[str, str]) -> str:
    normalized = _normalize_gate_statuses(statuses)
    if all(status == "pass" for status in normalized.values()):
        return "conditionally_approved_for_I2"
    if any(status == "reject" for status in normalized.values()):
        return "rejected"
    return "under_review"


def write_first_source_review_report(
    *,
    run_dir: str | Path,
    run_id: str,
    candidate_review: Mapping[str, str] | None = None,
    report_relative_path: str | Path = FUTURE_SLICE_13B_REPORT_RELATIVE_PATH,
) -> Path:
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    review = dict(candidate_review or get_first_candidate_source_review_record())
    _validate_record(review)
    payload: dict[str, Any] = {
        "schema_version": FUTURE_SLICE_13B_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "candidate_review": review,
        "gates_reviewed": list(CANDIDATE_REVIEW_GATE_NAMES),
        "final_decision": review["final_decision"],
        "h3_training_allowed": False,
        "h4_inference_allowed": False,
        "dataset_downloaded": False,
        "dataset_created": False,
        "i2_pack_created": False,
        "training_added": False,
        "inference_added": False,
        "ml_dependencies_added": False,
        "earth_engine_calls_added": False,
        "public_exposure_changes": False,
        "notes": (
            "Slice 13B writes a redacted, metadata-only first source review. It "
            "does not create candidate data, an I2 pack, training, inference, or "
            "public exposure."
        ),
    }
    verify_redacted(payload)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def write_arxiv_2602_19608_source_review_report(
    *,
    run_dir: str | Path,
    run_id: str,
    candidate_review: Mapping[str, str] | None = None,
    report_relative_path: str | Path = FUTURE_SLICE_13D_REPORT_RELATIVE_PATH,
) -> Path:
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    review = dict(candidate_review or get_arxiv_2602_19608_source_review_record())
    _validate_record(review)
    if review["candidate_id"] != "arxiv_2602_19608_looted_sites":
        raise ValueError("Slice 13D report requires the arXiv 2602.19608 candidate")

    payload: dict[str, Any] = {
        "schema_version": FUTURE_SLICE_13D_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "candidate_review": review,
        "gates_reviewed": list(CANDIDATE_REVIEW_GATE_NAMES),
        "final_decision": review["final_decision"],
        "h3_training_allowed": False,
        "h4_inference_allowed": False,
        "dataset_downloaded": False,
        "dataset_created": False,
        "i2_pack_created": False,
        "training_added": False,
        "inference_added": False,
        "ml_dependencies_added": False,
        "earth_engine_calls_added": False,
        "public_exposure_changes": False,
        "notes": (
            "Slice 13D writes a redacted, metadata-only source review. It does "
            "not create candidate data, an I2 pack, training, inference, or "
            "public exposure."
        ),
    }
    verify_redacted(payload)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _validate_status(field: str, status: str) -> None:
    if status not in GATE_STATUS_VALUES:
        raise ValueError(f"{field} has unsupported status: {status}")


def _validate_record(record: Mapping[str, str]) -> None:
    missing = [field for field in CANDIDATE_RECORD_FIELDS if field not in record]
    extra = [field for field in record if field not in CANDIDATE_RECORD_FIELDS]
    if missing or extra:
        raise ValueError(
            "candidate review record fields do not match Slice 13 schema"
        )
    if record["lead_status"] not in CANDIDATE_STATUS_VALUES:
        raise ValueError("unsupported lead_status")
    if record["lead_status"] != "unverified_lead":
        raise ValueError("Slice 13B candidate must start as unverified_lead")
    if record["review_status"] not in CANDIDATE_STATUS_VALUES:
        raise ValueError("unsupported review_status")
    if record["final_decision"] not in FINAL_DECISION_VALUES:
        raise ValueError("unsupported final_decision")

    gate_statuses = summarize_gate_statuses(record)
    computed_final = decide_final_review_status(gate_statuses)
    if record["final_decision"] != computed_final:
        raise ValueError("final_decision does not match gate rules")
    if record["review_status"] != computed_final:
        raise ValueError("review_status does not match gate rules")
    for gate_name, status in gate_statuses.items():
        _validate_status(_GATE_STATUS_FIELDS[gate_name], status)
        blocker_field = _GATE_BLOCKER_FIELDS[gate_name]
        if status != "pass" and not str(record[blocker_field]).strip():
            raise ValueError(f"{blocker_field} is required when gate does not pass")


def _default_final_blocker(statuses: Mapping[str, str]) -> str:
    normalized = _normalize_gate_statuses(statuses)
    if all(status == "pass" for status in normalized.values()):
        return ""
    return "one_or_more_slice_13_gates_did_not_pass"


def _normalize_gate_statuses(statuses: Mapping[str, str]) -> dict[str, str]:
    if all(field in statuses for field in _GATE_STATUS_FIELDS.values()):
        return {
            field: str(statuses[field])
            for field in _GATE_STATUS_FIELDS.values()
        }
    if all(gate_name in statuses for gate_name in CANDIDATE_REVIEW_GATE_NAMES):
        return {
            _GATE_STATUS_FIELDS[gate_name]: str(statuses[gate_name])
            for gate_name in CANDIDATE_REVIEW_GATE_NAMES
        }
    raise KeyError("missing one or more Slice 13 gate statuses")
