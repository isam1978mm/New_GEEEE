"""Safely append one private depth-calibration record outside Git.

The default action is a dry run. Use --create-template to create a blank private
JSON payload, or --write to append a validated record. The command never prints
record values, identifiers, coordinates, depth values, source references, or
private paths.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

import validate_depth_calibration_pack as validator


DEFAULT_DATASET_DIR = validator.DEFAULT_DATASET_DIR
DEFAULT_PAYLOAD_NAME = "record_intake.json"
ALLOWED_INTAKE_STATUSES = {"known_depth_positive", "confirmed_no_target"}
MANIFEST_INVALIDATED_STATUS = "private_dataset_modified_requires_refinalization"
MANIFEST_FIELDS_TO_CLEAR: dict[str, Any] = {
    "updated_at": None,
    "build_commit": None,
    "build_procedure": None,
    "record_count": None,
    "positive_count": None,
    "negative_count": None,
    "excluded_count": None,
    "included_relative_count": None,
    "included_numerical_count": None,
    "label_quality_counts": {},
    "evidence_source_counts": {},
    "finding_family_counts": {},
    "soil_surface_counts": {},
    "season_moisture_counts": {},
    "terrain_counts": {},
    "depth_min_m": None,
    "depth_max_m": None,
    "depth_uncertainty_summary": None,
    "split_policy_version": None,
    "split_counts": {},
    "site_counts_by_split": {},
    "feature_manifest_version": None,
    "data_source_list": [],
    "records_sha256": None,
    "source_index_sha256": None,
    "exclusions_sha256": None,
    "content_hash": None,
    "manifest_hash": None,
}


class DepthRecordIntakeError(ValueError):
    """Raised when a private intake payload cannot be accepted safely."""


def create_blank_payload(payload_path: Path) -> dict[str, Any]:
    payload_path = Path(payload_path)
    validator._require_outside_repo(payload_path, "payload path")
    if payload_path.exists():
        raise DepthRecordIntakeError("private intake payload already exists")
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "record": {field: "" for field in validator.REQUIRED_COLUMNS},
        "source": {field: "" for field in validator.SOURCE_COLUMNS},
    }
    _atomic_write_json(payload_path, payload)
    return {
        "status": "blank_private_intake_payload_created",
        "template_written": True,
        "record_written": False,
        "source_written": False,
        "private_values_printed": False,
        "app_depth_enabled": False,
    }


def intake_record(dataset_dir: Path, payload_path: Path, *, write: bool = False) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    payload_path = Path(payload_path)
    validator._require_outside_repo(dataset_dir, "dataset directory")
    validator._require_outside_repo(payload_path, "payload path")

    paths = {name: dataset_dir / name for name in validator.REQUIRED_FILES}
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise DepthRecordIntakeError(f"required private pack files are missing: {', '.join(sorted(missing))}")
    if not payload_path.is_file():
        raise DepthRecordIntakeError("private intake payload is missing")

    issues: Counter[str] = Counter()
    rows = validator._read_csv(paths["calibration_records.csv"], validator.REQUIRED_COLUMNS, issues, "records")
    sources = validator._read_csv(paths["source_index.csv"], validator.SOURCE_COLUMNS, issues, "source_index")
    exclusions = validator._read_csv(paths["exclusions.csv"], validator.EXCLUSION_COLUMNS, issues, "exclusions")
    manifest = validator._read_json(paths["calibration_manifest.json"])
    payload = validator._read_json(payload_path)

    extra_top_level = sorted(set(payload) - {"record", "source"})
    if extra_top_level:
        raise DepthRecordIntakeError("intake payload contains unsupported top-level fields")
    if "record" not in payload:
        raise DepthRecordIntakeError("intake payload is missing the record object")

    record = _normalize_exact_object(payload["record"], validator.REQUIRED_COLUMNS, "record")
    if record["reference_status"] not in ALLOWED_INTAKE_STATUSES:
        raise DepthRecordIntakeError("intake supports only known-depth positives and confirmed negatives")

    record_id = record["record_id"]
    if record_id and any(existing.get("record_id", "").strip() == record_id for existing in rows):
        raise DepthRecordIntakeError("record identifier already exists")

    source_payload = payload.get("source")
    source = None if source_payload is None else _normalize_exact_object(
        source_payload, validator.SOURCE_COLUMNS, "source"
    )
    source_ref = record["evidence_source_reference"]
    existing_source = next(
        (item for item in sources if item.get("source_reference", "").strip() == source_ref),
        None,
    )
    source_to_append: dict[str, str] | None = None

    if source is None:
        if existing_source is None:
            raise DepthRecordIntakeError("record evidence source is not present in the source index")
    else:
        if source["source_reference"] != source_ref:
            raise DepthRecordIntakeError("record and source reference fields do not match")
        if existing_source is None:
            source_to_append = source
        elif existing_source != source:
            raise DepthRecordIntakeError("source reference already exists with different metadata")

    candidate_rows = [*rows, record]
    candidate_sources = [*sources, *([source_to_append] if source_to_append is not None else [])]
    validator._validate_rows(candidate_rows, candidate_sources, exclusions, issues)
    validator._remove_zero_issues(issues)
    if issues:
        raise DepthRecordIntakeError(
            f"private intake has contract issues: {json.dumps(dict(sorted(issues.items())), sort_keys=True)}"
        )

    if write:
        _atomic_write_csv(paths["calibration_records.csv"], validator.REQUIRED_COLUMNS, candidate_rows)
        if source_to_append is not None:
            _atomic_write_csv(paths["source_index.csv"], validator.SOURCE_COLUMNS, candidate_sources)
        invalidated_manifest = dict(manifest)
        invalidated_manifest["status"] = MANIFEST_INVALIDATED_STATUS
        invalidated_manifest.update(MANIFEST_FIELDS_TO_CLEAR)
        _atomic_write_json(paths["calibration_manifest.json"], invalidated_manifest)

    return {
        "status": "private_depth_record_written" if write else "private_depth_record_dry_run_ready",
        "record_count_before": len(rows),
        "record_count_after": len(candidate_rows),
        "source_count_before": len(sources),
        "source_count_after": len(candidate_sources),
        "record_written": write,
        "source_written": write and source_to_append is not None,
        "manifest_invalidated_for_refinalization": write,
        "private_values_printed": False,
        "scientific_validation_run": False,
        "training_started": False,
        "app_depth_enabled": False,
    }


def _normalize_exact_object(value: Any, fields: tuple[str, ...], label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise DepthRecordIntakeError(f"intake {label} must be a JSON object")
    missing = [field for field in fields if field not in value]
    extra = [field for field in value if field not in fields]
    if missing:
        raise DepthRecordIntakeError(f"intake {label} is missing required fields: {', '.join(missing)}")
    if extra:
        raise DepthRecordIntakeError(f"intake {label} contains unsupported fields: {', '.join(sorted(extra))}")
    return {field: str(value.get(field) or "").strip() for field in fields}


def _atomic_write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(fields))
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or validate one private depth-calibration intake payload.")
    parser.add_argument("--dataset-dir", default=str(DEFAULT_DATASET_DIR))
    parser.add_argument("--payload")
    parser.add_argument(
        "--create-template",
        action="store_true",
        help="Create a blank private JSON intake payload and exit.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Append the validated record and invalidate the manifest. Without this flag, run dry-only validation.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    dataset_dir = Path(args.dataset_dir)
    payload_path = Path(args.payload) if args.payload else dataset_dir / DEFAULT_PAYLOAD_NAME
    try:
        if args.create_template:
            if args.write:
                raise DepthRecordIntakeError("--create-template and --write cannot be used together")
            result = create_blank_payload(payload_path)
        else:
            result = intake_record(dataset_dir, payload_path, write=args.write)
    except (OSError, json.JSONDecodeError, csv.Error, validator.PackValidationError, DepthRecordIntakeError) as exc:
        print(
            json.dumps(
                {
                    "status": "private_depth_record_intake_failed",
                    "error": str(exc),
                    "private_values_printed": False,
                    "app_depth_enabled": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
