"""Validate a private depth-calibration pack with aggregate-only output.

The validator reads files from a local folder outside the repository. It never
prints record IDs, site IDs, coordinates, source paths, depth values, or rows.
It does not fit a model or enable app depth output.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\DEPTH_CALIBRATION\dataset_v001")

REQUIRED_FILES = (
    "calibration_records.csv",
    "calibration_manifest.json",
    "feature_manifest.json",
    "source_index.csv",
    "exclusions.csv",
    "DATASET_CARD.md",
)
REQUIRED_COLUMNS = (
    "schema_version", "record_id", "site_id", "feature_id", "group_id",
    "reference_status", "finding_family", "known_depth_top_m", "known_depth_bottom_m",
    "depth_reference_uncertainty_m", "depth_reference_method", "evidence_source_type",
    "evidence_source_reference", "evidence_source_version", "evidence_review_method",
    "label_quality", "target_size_length_m", "target_size_width_m", "target_size_height_m",
    "target_material_or_structure", "soil_or_surface_type", "moisture_or_season",
    "terrain_class", "observation_start", "observation_end", "sensor_sources",
    "sensor_acquisition_ids", "pipeline_commit", "feature_manifest_version", "split",
    "split_policy_version", "include_for_relative_depth", "include_for_numerical_depth",
    "exclusion_reason", "quality_notes", "created_at", "reviewed_at", "reviewer_reference",
)
SOURCE_COLUMNS = (
    "source_reference", "source_type", "source_version", "private_location", "review_status", "review_notes"
)
EXCLUSION_COLUMNS = (
    "record_id", "site_id", "feature_id", "exclusion_reason", "decision_date", "reviewer_reference", "notes"
)
REFERENCE_STATUSES = {"known_depth_positive", "confirmed_no_target", "uncertain_reference", "excluded"}
LABEL_QUALITIES = {
    "measured_independent", "reviewed_independent", "reviewed_adjudicated",
    "weak_or_proxy", "uncertain", "excluded",
}
FIT_LABEL_QUALITIES = {"measured_independent", "reviewed_independent", "reviewed_adjudicated"}
SPLITS = {"train", "validation", "holdout", "excluded"}
ACTIVE_SPLIT_ORDER = ("train", "validation", "holdout")
ACTIVE_SPLITS = set(ACTIVE_SPLIT_ORDER)
REQUIRED_EVIDENCE_FIELDS = (
    "depth_reference_method", "evidence_source_type", "evidence_source_reference",
    "evidence_source_version", "evidence_review_method", "reviewer_reference",
)
REQUIRED_INCLUDED_CONTEXT = (
    "finding_family", "soil_or_surface_type", "moisture_or_season", "terrain_class",
    "observation_start", "observation_end", "sensor_sources", "sensor_acquisition_ids",
    "pipeline_commit", "feature_manifest_version", "split_policy_version",
)
REQUIRED_PROHIBITED_INPUTS = {
    "classifier_class", "classifier_score", "classifier_probability",
    "classifier_final_finding_summary", "pca_target_decision",
    "target_mask_or_geometry_from_same_decision_pipeline", "app_generated_depth_label",
    "notebook_generated_depth_label", "unknown_provenance_depth_array",
}
FEATURE_REQUIRED_FIELDS = (
    "name", "role", "source", "source_fields", "formula_or_definition", "unit",
    "spatial_resolution", "nodata_behavior", "preprocessing", "known_confounders",
    "allowed_for_depth_research", "limitation", "order",
)
FEATURE_ROLES = {"candidate_depth_signal", "context", "confounder_control", "quality_gate"}
PROHIBITED_FEATURE_TOKENS = ("classifier", "pca", "target_mask", "generated_depth", "finding_summary")
COORDINATE_PATTERN = re.compile(r"(?i)(POINT\s*\(|-?\d{1,2}\.\d+\s*[,;/_ ]\s*-?\d{1,3}\.\d+)")


class PackValidationError(ValueError):
    """Raised when the private pack cannot be read safely."""


def validate_pack(dataset_dir: Path) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    _require_outside_repo(dataset_dir, "dataset directory")
    issues: Counter[str] = Counter()
    input_errors: dict[str, str] = {}

    paths = {name: dataset_dir / name for name in REQUIRED_FILES}
    for name, path in paths.items():
        if not path.is_file():
            input_errors[name] = "missing"

    rows: list[dict[str, str]] = []
    sources: list[dict[str, str]] = []
    exclusions: list[dict[str, str]] = []
    manifest: dict[str, Any] = {}
    feature_manifest: dict[str, Any] = {}

    if not input_errors:
        try:
            rows = _read_csv(paths["calibration_records.csv"], REQUIRED_COLUMNS, issues, "records")
            sources = _read_csv(paths["source_index.csv"], SOURCE_COLUMNS, issues, "source_index")
            exclusions = _read_csv(paths["exclusions.csv"], EXCLUSION_COLUMNS, issues, "exclusions")
            manifest = _read_json(paths["calibration_manifest.json"])
            feature_manifest = _read_json(paths["feature_manifest.json"])
        except (OSError, PackValidationError, json.JSONDecodeError, csv.Error) as exc:
            input_errors["read_error"] = str(exc)

    if not input_errors:
        _validate_rows(rows, sources, exclusions, issues)
        _validate_feature_manifest(feature_manifest, rows, issues)
        _validate_manifest(manifest, rows, sources, exclusions, paths, issues)

    counts = _aggregate_counts(rows)
    readiness = _readiness_decision(input_errors, issues, counts, feature_manifest)
    return {
        "status": "validation_passed" if readiness == "ready_for_relative_depth_research" else "validation_failed",
        "readiness_decision": readiness,
        "record_count": len(rows),
        "positive_count": counts["positive_count"],
        "negative_count": counts["negative_count"],
        "eligible_positive_count": counts["eligible_positive_count"],
        "eligible_confirmed_negative_count": counts["eligible_confirmed_negative_count"],
        "eligible_positive_by_split": counts["eligible_positive_by_split"],
        "eligible_confirmed_negative_by_split": counts["eligible_confirmed_negative_by_split"],
        "excluded_or_uncertain_count": counts["excluded_or_uncertain_count"],
        "included_relative_count": counts["included_relative_count"],
        "included_numerical_count": counts["included_numerical_count"],
        "split_counts": counts["split_counts"],
        "reference_status_counts": counts["reference_status_counts"],
        "label_quality_counts": counts["label_quality_counts"],
        "issue_counts": dict(sorted(issues.items())),
        "input_errors": input_errors,
        "dataset_path_outside_repository": True,
        "private_rows_printed": False,
        "scientific_validation_run": False,
        "training_started": False,
        "app_depth_enabled": False,
    }


def _validate_rows(
    rows: list[dict[str, str]],
    sources: list[dict[str, str]],
    exclusions: list[dict[str, str]],
    issues: Counter[str],
) -> None:
    source_refs = [row.get("source_reference", "").strip() for row in sources]
    source_ref_set = {value for value in source_refs if value}
    issues["duplicate_source_reference"] += _duplicate_count(source_refs)

    exclusion_ids = {row.get("record_id", "").strip() for row in exclusions if row.get("record_id", "").strip()}
    record_ids = [row.get("record_id", "").strip() for row in rows]
    issues["duplicate_record_id"] += _duplicate_count(record_ids)

    group_splits: dict[str, set[str]] = defaultdict(set)
    site_splits: dict[str, set[str]] = defaultdict(set)
    feature_splits: dict[tuple[str, str], set[str]] = defaultdict(set)

    for row in rows:
        status = row.get("reference_status", "").strip()
        quality = row.get("label_quality", "").strip()
        split = row.get("split", "").strip()
        relative = _parse_bool(row.get("include_for_relative_depth", ""), issues)
        numerical = _parse_bool(row.get("include_for_numerical_depth", ""), issues)
        included = relative is True or numerical is True

        if status not in REFERENCE_STATUSES:
            issues["invalid_reference_status"] += 1
        if quality not in LABEL_QUALITIES:
            issues["invalid_label_quality"] += 1
        if split not in SPLITS:
            issues["invalid_split"] += 1
        if numerical is True and relative is not True:
            issues["numerical_without_relative_inclusion"] += 1
        if included and quality not in FIT_LABEL_QUALITIES:
            issues["included_row_has_ineligible_label_quality"] += 1
        if status in {"uncertain_reference", "excluded"} and included:
            issues["uncertain_or_excluded_row_included"] += 1
        if included and split not in ACTIVE_SPLITS:
            issues["included_row_not_in_active_split"] += 1

        for key in ("record_id", "site_id", "feature_id", "group_id"):
            value = row.get(key, "").strip()
            if not value:
                issues[f"missing_{key}"] += 1
            elif COORDINATE_PATTERN.search(value):
                issues["identifier_looks_coordinate_bearing"] += 1

        if status == "known_depth_positive":
            top = _parse_nonnegative_float(row.get("known_depth_top_m", ""), issues, "invalid_positive_top_depth")
            bottom = _parse_optional_nonnegative_float(
                row.get("known_depth_bottom_m", ""), issues, "invalid_positive_bottom_depth"
            )
            uncertainty = _parse_nonnegative_float(
                row.get("depth_reference_uncertainty_m", ""), issues, "invalid_or_missing_depth_uncertainty"
            )
            if top is not None and bottom is not None and bottom < top:
                issues["bottom_depth_less_than_top_depth"] += 1
            del uncertainty
        elif status == "confirmed_no_target":
            if any(
                row.get(key, "").strip()
                for key in ("known_depth_top_m", "known_depth_bottom_m", "depth_reference_uncertainty_m")
            ):
                issues["negative_row_contains_depth_value"] += 1

        if status in {"known_depth_positive", "confirmed_no_target"}:
            for key in REQUIRED_EVIDENCE_FIELDS:
                if not row.get(key, "").strip():
                    issues[f"missing_evidence_field_{key}"] += 1
            source_ref = row.get("evidence_source_reference", "").strip()
            if source_ref and source_ref not in source_ref_set:
                issues["evidence_reference_missing_from_source_index"] += 1

        if included:
            for key in REQUIRED_INCLUDED_CONTEXT:
                if not row.get(key, "").strip():
                    issues[f"missing_included_context_{key}"] += 1
            _validate_date_range(row, issues)

        if status == "excluded" and row.get("record_id", "").strip() not in exclusion_ids:
            issues["excluded_record_missing_from_exclusion_ledger"] += 1

        if split in ACTIVE_SPLITS:
            group_id = row.get("group_id", "").strip()
            site_id = row.get("site_id", "").strip()
            feature_id = row.get("feature_id", "").strip()
            if group_id:
                group_splits[group_id].add(split)
            if site_id:
                site_splits[site_id].add(split)
            if site_id and feature_id:
                feature_splits[(site_id, feature_id)].add(split)

    issues["group_split_leakage"] += sum(1 for values in group_splits.values() if len(values) > 1)
    issues["site_split_leakage"] += sum(1 for values in site_splits.values() if len(values) > 1)
    issues["feature_split_leakage"] += sum(1 for values in feature_splits.values() if len(values) > 1)
    _remove_zero_issues(issues)


def _validate_feature_manifest(feature_manifest: dict[str, Any], rows: list[dict[str, str]], issues: Counter[str]) -> None:
    if feature_manifest.get("schema_version") != "depth_feature_manifest_v1":
        issues["feature_manifest_schema_mismatch"] += 1
    prohibited = set(feature_manifest.get("prohibited_inputs", []))
    if not REQUIRED_PROHIBITED_INPUTS.issubset(prohibited):
        issues["feature_manifest_missing_prohibited_inputs"] += 1

    included_rows = [row for row in rows if _bool_without_issue(row.get("include_for_relative_depth", ""))]
    if included_rows:
        if feature_manifest.get("status") != "frozen":
            issues["feature_manifest_not_frozen"] += 1
        version = str(feature_manifest.get("feature_manifest_version") or "").strip()
        features = feature_manifest.get("features")
        if not version:
            issues["feature_manifest_version_missing"] += 1
        if not isinstance(features, list) or not features:
            issues["feature_manifest_features_empty"] += 1
        else:
            names: list[str] = []
            orders: list[int] = []
            for feature in features:
                if not isinstance(feature, dict):
                    issues["feature_manifest_entry_not_object"] += 1
                    continue
                for key in FEATURE_REQUIRED_FIELDS:
                    if feature.get(key) in (None, "", []):
                        issues[f"feature_manifest_entry_missing_{key}"] += 1
                name = str(feature.get("name") or "").strip()
                role = str(feature.get("role") or "").strip()
                if name:
                    names.append(name)
                    lowered = name.casefold()
                    if any(token in lowered for token in PROHIBITED_FEATURE_TOKENS):
                        issues["feature_manifest_contains_prohibited_feature_name"] += 1
                if role and role not in FEATURE_ROLES:
                    issues["feature_manifest_invalid_role"] += 1
                if feature.get("allowed_for_depth_research") is not True:
                    issues["feature_manifest_entry_not_approved_for_research"] += 1
                order = feature.get("order")
                if isinstance(order, int) and order > 0:
                    orders.append(order)
                else:
                    issues["feature_manifest_invalid_order"] += 1
            issues["feature_manifest_duplicate_name"] += _duplicate_count(names)
            issues["feature_manifest_duplicate_order"] += _duplicate_count([str(value) for value in orders])
        if version and any(row.get("feature_manifest_version", "").strip() != version for row in included_rows):
            issues["row_feature_manifest_version_mismatch"] += 1
    _remove_zero_issues(issues)


def _validate_manifest(
    manifest: dict[str, Any],
    rows: list[dict[str, str]],
    sources: list[dict[str, str]],
    exclusions: list[dict[str, str]],
    paths: dict[str, Path],
    issues: Counter[str],
) -> None:
    if manifest.get("schema_version") != "depth_calibration_manifest_v1":
        issues["calibration_manifest_schema_mismatch"] += 1
    privacy = manifest.get("privacy") if isinstance(manifest.get("privacy"), dict) else manifest
    expected_privacy = {
        "filesystem_only": True,
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
    }
    for key, expected in expected_privacy.items():
        if privacy.get(key) is not expected:
            issues[f"manifest_privacy_{key}_mismatch"] += 1

    counts = _aggregate_counts(rows)
    count_mapping = {
        "record_count": len(rows),
        "positive_count": counts["positive_count"],
        "negative_count": counts["negative_count"],
        "excluded_count": counts["excluded_or_uncertain_count"],
        "included_relative_count": counts["included_relative_count"],
        "included_numerical_count": counts["included_numerical_count"],
    }
    for key, expected in count_mapping.items():
        value = manifest.get(key)
        if value is not None and value != expected:
            issues[f"manifest_{key}_mismatch"] += 1

    expected_hashes = {
        "records_sha256": _sha256(paths["calibration_records.csv"]),
        "source_index_sha256": _sha256(paths["source_index.csv"]),
        "exclusions_sha256": _sha256(paths["exclusions.csv"]),
    }
    for key, expected in expected_hashes.items():
        value = manifest.get(key)
        if value is not None and value != expected:
            issues[f"manifest_{key}_mismatch"] += 1

    content_hash = manifest.get("content_hash")
    if content_hash is not None and content_hash != _combined_hash(expected_hashes.values()):
        issues["manifest_content_hash_mismatch"] += 1

    if rows:
        required_manifest_values = (
            "dataset_id", "dataset_version", "created_at", "updated_at", "build_commit",
            "build_procedure", "feature_manifest_version", "records_sha256",
            "source_index_sha256", "exclusions_sha256", "content_hash", "manifest_hash",
            "storage_location_reference", "redaction_policy",
        )
        for key in required_manifest_values:
            if manifest.get(key) in (None, ""):
                issues[f"manifest_required_value_missing_{key}"] += 1
        if manifest.get("status") != "populated_private_dataset":
            issues["populated_rows_with_invalid_manifest_status"] += 1
        if manifest.get("artifact_class") not in {"LOCAL_SENSITIVE", "FILESYSTEM_ONLY"}:
            issues["manifest_artifact_class_invalid"] += 1
        if not isinstance(manifest.get("known_limitations"), list):
            issues["manifest_known_limitations_not_list"] += 1
        manifest_hash = manifest.get("manifest_hash")
        if manifest_hash:
            canonical = dict(manifest)
            canonical["manifest_hash"] = None
            if manifest_hash != _manifest_hash(canonical):
                issues["manifest_manifest_hash_mismatch"] += 1
    if sources and _duplicate_count([row.get("source_reference", "").strip() for row in sources]):
        issues["source_index_not_unique"] += 1
    if exclusions and _duplicate_count([row.get("record_id", "").strip() for row in exclusions]):
        issues["exclusion_ledger_duplicate_record_id"] += 1
    _remove_zero_issues(issues)


def _readiness_decision(
    input_errors: dict[str, str], issues: Counter[str], counts: dict[str, Any], feature_manifest: dict[str, Any]
) -> str:
    if input_errors:
        return "not_ready_input_files_missing_or_invalid"
    if counts["record_count"] == 0:
        return "not_ready_no_records"
    if issues:
        return "not_ready_contract_errors"
    if counts["positive_count"] == 0:
        return "not_ready_no_positive_records"
    if counts["negative_count"] == 0:
        return "not_ready_no_confirmed_negative_records"
    if any(counts["split_counts"].get(split, 0) == 0 for split in ACTIVE_SPLIT_ORDER):
        return "not_ready_missing_group_separated_split"
    eligibility_failure = _eligible_readiness_failure(counts)
    if eligibility_failure is not None:
        return eligibility_failure
    if feature_manifest.get("status") != "frozen":
        return "not_ready_feature_manifest_not_frozen"
    return "ready_for_relative_depth_research"


def _is_eligible_row(row: dict[str, str]) -> bool:
    return (
        row.get("reference_status", "").strip() in {"known_depth_positive", "confirmed_no_target"}
        and row.get("label_quality", "").strip() in FIT_LABEL_QUALITIES
        and _bool_without_issue(row.get("include_for_relative_depth", ""))
        and row.get("split", "").strip() in ACTIVE_SPLITS
    )


def _eligible_readiness_failure(counts: dict[str, Any]) -> str | None:
    if counts["eligible_positive_count"] == 0:
        return "not_ready_no_eligible_positive_records"
    if counts["eligible_confirmed_negative_count"] == 0:
        return "not_ready_no_eligible_confirmed_negative_records"
    for split in ACTIVE_SPLIT_ORDER:
        if counts["eligible_positive_by_split"].get(split, 0) == 0:
            return "not_ready_missing_eligible_split_coverage"
        if counts["eligible_confirmed_negative_by_split"].get(split, 0) == 0:
            return "not_ready_missing_eligible_split_coverage"
    return None


def _aggregate_counts(rows: list[dict[str, str]]) -> dict[str, Any]:
    status_counts = Counter(row.get("reference_status", "").strip() or "missing" for row in rows)
    split_counts = Counter(row.get("split", "").strip() or "missing" for row in rows)
    quality_counts = Counter(row.get("label_quality", "").strip() or "missing" for row in rows)
    eligible_positive_by_split = {split: 0 for split in ACTIVE_SPLIT_ORDER}
    eligible_confirmed_negative_by_split = {split: 0 for split in ACTIVE_SPLIT_ORDER}

    for row in rows:
        if not _is_eligible_row(row):
            continue
        split = row.get("split", "").strip()
        status = row.get("reference_status", "").strip()
        if status == "known_depth_positive":
            eligible_positive_by_split[split] += 1
        elif status == "confirmed_no_target":
            eligible_confirmed_negative_by_split[split] += 1

    return {
        "record_count": len(rows),
        "positive_count": status_counts.get("known_depth_positive", 0),
        "negative_count": status_counts.get("confirmed_no_target", 0),
        "eligible_positive_count": sum(eligible_positive_by_split.values()),
        "eligible_confirmed_negative_count": sum(eligible_confirmed_negative_by_split.values()),
        "eligible_positive_by_split": eligible_positive_by_split,
        "eligible_confirmed_negative_by_split": eligible_confirmed_negative_by_split,
        "excluded_or_uncertain_count": status_counts.get("excluded", 0) + status_counts.get("uncertain_reference", 0),
        "included_relative_count": sum(_bool_without_issue(row.get("include_for_relative_depth", "")) for row in rows),
        "included_numerical_count": sum(_bool_without_issue(row.get("include_for_numerical_depth", "")) for row in rows),
        "split_counts": dict(sorted(split_counts.items())),
        "reference_status_counts": dict(sorted(status_counts.items())),
        "label_quality_counts": dict(sorted(quality_counts.items())),
    }


def _read_csv(path: Path, required: tuple[str, ...], issues: Counter[str], prefix: str) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        missing = [name for name in required if name not in header]
        if missing:
            raise PackValidationError(f"{prefix} CSV is missing required columns: {', '.join(missing)}")
        extra = [name for name in header if name not in required]
        if extra:
            issues[f"{prefix}_extra_column_count"] += len(extra)
        return [{key: (value or "").strip() for key, value in row.items() if key is not None} for row in reader]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PackValidationError(f"JSON file is not an object: {path.name}")
    return payload


def _parse_bool(value: str, issues: Counter[str]) -> bool | None:
    normalized = str(value).strip().casefold()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    issues["invalid_boolean_value"] += 1
    return None


def _bool_without_issue(value: str) -> bool:
    return str(value).strip().casefold() in {"true", "1", "yes"}


def _parse_nonnegative_float(value: str, issues: Counter[str], issue: str) -> float | None:
    if not str(value).strip():
        issues[issue] += 1
        return None
    return _parse_optional_nonnegative_float(value, issues, issue)


def _parse_optional_nonnegative_float(value: str, issues: Counter[str], issue: str) -> float | None:
    if not str(value).strip():
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        issues[issue] += 1
        return None
    if not math.isfinite(number) or number < 0:
        issues[issue] += 1
        return None
    return number


def _validate_date_range(row: dict[str, str], issues: Counter[str]) -> None:
    try:
        start = date.fromisoformat(row.get("observation_start", ""))
        end = date.fromisoformat(row.get("observation_end", ""))
    except ValueError:
        issues["invalid_observation_date"] += 1
        return
    if end < start:
        issues["observation_end_before_start"] += 1


def _duplicate_count(values: list[str]) -> int:
    counts = Counter(value for value in values if value)
    return sum(count - 1 for count in counts.values() if count > 1)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_hash(manifest: dict[str, Any]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _combined_hash(values: Any) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(str(value).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _remove_zero_issues(issues: Counter[str]) -> None:
    for key in list(issues):
        if issues[key] <= 0:
            del issues[key]


def _require_outside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise PackValidationError(f"{label} must be outside the repository")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a private depth-calibration pack with aggregate-only output.")
    parser.add_argument("--dataset-dir", default=str(DEFAULT_DATASET_DIR))
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = validate_pack(Path(args.dataset_dir))
    except (OSError, PackValidationError) as exc:
        result = {
            "status": "validation_failed",
            "readiness_decision": "not_ready_validator_error",
            "error": str(exc),
            "private_rows_printed": False,
            "scientific_validation_run": False,
            "training_started": False,
            "app_depth_enabled": False,
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "validation_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
