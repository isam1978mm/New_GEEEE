"""Validate repository-safe public depth-evidence candidates.

The validator checks provenance and aggregate consistency without printing target
labels, depths, source locations, or site details. Passing this validator does not
approve private-pack import, model fitting, or app depth output.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE_PATH = (
    REPO_ROOT / "docs" / "depth_public_evidence" / "controlled_site_depths_v1.json"
)
EXPECTED_SCHEMA = "depth_public_evidence_candidate_v1"
EXPECTED_STATUS = "candidate_evidence_not_approved_for_private_pack_import"
ALLOWED_EVIDENCE_METHODS = {
    "controlled_site_installed_known_depth",
    "controlled_site_independently_surveyed_depth",
}
REQUIRED_RULES = {
    "truth_source": "installed_or_independently_recorded_physical_depth_only",
    "geophysical_estimates_as_labels": False,
    "classifier_or_notebook_labels_allowed": False,
    "physical_site_group_must_remain_unsplit": True,
    "app_depth_enabled": False,
}
PROHIBITED_RECORD_KEYS = {
    "estimated_depth_m",
    "gpr_estimated_depth_m",
    "ert_estimated_depth_m",
    "vlf_estimated_depth_m",
    "magnetic_estimated_depth_m",
    "classifier_score",
    "classifier_probability",
    "notebook_depth_m",
    "pca_score",
    "target_mask",
}


class PublicEvidenceValidationError(ValueError):
    """Raised when a public candidate file cannot be read safely."""


def validate_candidate_file(path: Path) -> dict[str, Any]:
    path = Path(path)
    payload = _read_json(path)
    issues: Counter[str] = Counter()

    if payload.get("schema_version") != EXPECTED_SCHEMA:
        issues["schema_version_mismatch"] += 1
    if payload.get("status") != EXPECTED_STATUS:
        issues["status_mismatch"] += 1

    rules = payload.get("rules")
    if not isinstance(rules, dict):
        issues["rules_not_object"] += 1
        rules = {}
    for key, expected in REQUIRED_RULES.items():
        if rules.get(key) is not expected and rules.get(key) != expected:
            issues[f"rule_{key}_mismatch"] += 1

    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        issues["sources_missing_or_empty"] += 1
        sources = []

    candidate_ids: list[str] = []
    site_groups: set[str] = set()
    record_count = 0
    explicit_depth_to_top_count = 0
    uncertainty_record_count = 0
    approved_record_count = 0

    for source in sources:
        if not isinstance(source, dict):
            issues["source_not_object"] += 1
            continue

        candidate_id = str(source.get("candidate_id") or "").strip()
        site_group = str(source.get("physical_site_group") or "").strip()
        source_doi = str(source.get("source_doi") or "").strip()
        evidence_method = str(source.get("evidence_method") or "").strip()
        depth_reference = str(source.get("depth_reference") or "").strip()
        uncertainty = source.get("reference_uncertainty_m")
        satellite_status = str(source.get("satellite_feature_compatibility") or "").strip()
        import_approved = source.get("private_pack_import_approved")

        if not candidate_id:
            issues["candidate_id_missing"] += 1
        else:
            candidate_ids.append(candidate_id)
        if not site_group:
            issues["physical_site_group_missing"] += 1
        else:
            site_groups.add(site_group)
        if not source_doi:
            issues["source_doi_missing"] += 1
        if evidence_method not in ALLOWED_EVIDENCE_METHODS:
            issues["evidence_method_not_independent"] += 1
        if not depth_reference:
            issues["depth_reference_missing"] += 1

        uncertainty_valid = _valid_optional_nonnegative_number(uncertainty)
        if uncertainty is not None and not uncertainty_valid:
            issues["reference_uncertainty_invalid"] += 1

        if import_approved is not False:
            issues["private_pack_import_must_remain_unapproved"] += 1
        if import_approved is True and uncertainty is None:
            issues["import_approved_without_uncertainty"] += 1
        if import_approved is True and satellite_status != "approved":
            issues["import_approved_without_satellite_support"] += 1

        records = source.get("records")
        if not isinstance(records, list) or not records:
            issues["source_records_missing_or_empty"] += 1
            continue

        labels: list[str] = []
        for record in records:
            if not isinstance(record, dict):
                issues["record_not_object"] += 1
                continue
            prohibited = sorted(set(record) & PROHIBITED_RECORD_KEYS)
            prohibited.extend(
                key for key in record if "estimated_depth" in str(key).casefold()
            )
            if prohibited:
                issues["record_contains_derived_depth_or_prohibited_input"] += 1

            label = str(record.get("public_target_label") or "").strip()
            if not label:
                issues["public_target_label_missing"] += 1
            else:
                labels.append(label)

            depth = record.get("known_depth_top_m")
            if not _valid_nonnegative_number(depth):
                issues["known_depth_top_invalid"] += 1

        issues["duplicate_public_target_label"] += _duplicate_count(labels)
        valid_record_total = sum(1 for record in records if isinstance(record, dict))
        record_count += valid_record_total
        if depth_reference == "explicit_depth_to_top":
            explicit_depth_to_top_count += valid_record_total
        if uncertainty is not None and uncertainty_valid:
            uncertainty_record_count += valid_record_total
        if import_approved is True:
            approved_record_count += valid_record_total

    issues["duplicate_candidate_id"] += _duplicate_count(candidate_ids)
    _remove_zero_issues(issues)

    expected_aggregate = {
        "physical_site_group_count": len(site_groups),
        "candidate_record_count": record_count,
        "record_count_with_explicit_depth_to_top_source_wording": explicit_depth_to_top_count,
        "record_count_with_reported_reference_uncertainty": uncertainty_record_count,
        "private_pack_import_approved_count": approved_record_count,
    }
    aggregate = payload.get("aggregate")
    if not isinstance(aggregate, dict):
        issues["aggregate_not_object"] += 1
    else:
        for key, expected in expected_aggregate.items():
            if aggregate.get(key) != expected:
                issues[f"aggregate_{key}_mismatch"] += 1

    _remove_zero_issues(issues)
    return {
        "status": "validation_passed" if not issues else "validation_failed",
        "readiness_decision": (
            "candidate_evidence_structurally_valid_not_import_approved"
            if not issues
            else "candidate_evidence_contract_errors"
        ),
        "source_count": len(sources),
        "physical_site_group_count": len(site_groups),
        "candidate_record_count": record_count,
        "reference_uncertainty_record_count": uncertainty_record_count,
        "private_pack_import_approved_count": approved_record_count,
        "issue_counts": dict(sorted(issues.items())),
        "private_values_printed": False,
        "scientific_validation_run": False,
        "training_started": False,
        "app_depth_enabled": False,
    }


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PublicEvidenceValidationError("candidate JSON is not an object")
    return payload


def _valid_nonnegative_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number >= 0


def _valid_optional_nonnegative_number(value: Any) -> bool:
    return value is None or _valid_nonnegative_number(value)


def _duplicate_count(values: list[str]) -> int:
    counts = Counter(value for value in values if value)
    return sum(count - 1 for count in counts.values() if count > 1)


def _remove_zero_issues(issues: Counter[str]) -> None:
    for key in list(issues):
        if issues[key] <= 0:
            del issues[key]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate public controlled-site depth candidates with aggregate-only output."
    )
    parser.add_argument("--candidate-file", default=str(DEFAULT_CANDIDATE_PATH))
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = validate_candidate_file(Path(args.candidate_file))
    except (OSError, json.JSONDecodeError, PublicEvidenceValidationError) as exc:
        result = {
            "status": "validation_failed",
            "readiness_decision": "candidate_evidence_input_error",
            "error": str(exc),
            "private_values_printed": False,
            "scientific_validation_run": False,
            "training_started": False,
            "app_depth_enabled": False,
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "validation_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
