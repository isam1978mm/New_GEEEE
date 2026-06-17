"""Validate private I2 dataset readiness outside Git.

This script reads the private I2 pack from a local folder outside the repository
and prints aggregate-only readiness checks.

It does not write private rows, assemble I2, start model work, run inference,
call Earth Engine, or change app/API/frontend code.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_I2_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\I2_PRIVATE")

I2_ROWS_FILE = "i2_training_examples.private.jsonl"
I2_SUMMARY_FILE = "i2_summary.private.json"
I2_MANIFEST_FILE = "i2_manifest.private.json"
I2_SPLIT_SUMMARY_FILE = "i2_split_summary.private.json"
I2_LEAKAGE_REPORT_FILE = "i2_leakage_report.private.json"
I2_SOURCE_INVENTORY_FILE = "i2_source_inventory.private.json"

EXPECTED_TOTAL_ROWS = 868
EXPECTED_ROWS_BY_SOURCE = {
    "POS-01": 217,
    "C05": 217,
    "C06": 217,
    "C07": 217,
}
EXPECTED_ROWS_BY_LABEL = {
    "Class_A": 217,
    "Class_Background": 217,
    "Class_HardNegative": 434,
}
EXPECTED_ROWS_BY_SPLIT = {
    "train": 608,
    "val": 88,
    "test": 88,
    "holdout": 84,
}
VALID_LABELS = set(EXPECTED_ROWS_BY_LABEL)
VALID_SPLITS = set(EXPECTED_ROWS_BY_SPLIT)

REQUIRED_FIELDS = (
    "schema_version",
    "sample_id",
    "dataset_id",
    "area_id",
    "group_id",
    "chip_id",
    "split",
    "label",
    "label_quality",
    "label_evidence_source",
    "evidence_source_type",
    "evidence_source_version",
    "evidence_review_method",
    "reviewer_or_source_reference",
    "acquisition_window",
    "sensor_sources",
    "grid_version",
    "preprocessing_commit",
    "features_ref",
    "metadata_ref",
    "redaction_class",
    "notes",
    "source_id",
)


class ReadinessError(ValueError):
    """Raised when the private I2 readiness check cannot load inputs."""


def main() -> int:
    args = _parse_args()
    i2_dir = Path(args.i2_dir)
    _validate_private_path_not_inside_repo(i2_dir, "I2 directory")

    paths = {
        "rows": i2_dir / I2_ROWS_FILE,
        "summary": i2_dir / I2_SUMMARY_FILE,
        "manifest": i2_dir / I2_MANIFEST_FILE,
        "split_summary": i2_dir / I2_SPLIT_SUMMARY_FILE,
        "leakage_report": i2_dir / I2_LEAKAGE_REPORT_FILE,
        "source_inventory": i2_dir / I2_SOURCE_INVENTORY_FILE,
    }

    input_errors: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}
    manifest: dict[str, Any] = {}
    split_summary: dict[str, Any] = {}
    leakage_report: dict[str, Any] = {}
    source_inventory: dict[str, Any] = {}

    try:
        rows = _read_jsonl(_require_file(paths["rows"], "I2 rows file"))
    except Exception as exc:  # noqa: BLE001 - aggregate reporting
        input_errors["rows"] = str(exc)

    for key, label in (
        ("summary", "I2 summary file"),
        ("manifest", "I2 manifest file"),
        ("split_summary", "I2 split summary file"),
        ("leakage_report", "I2 leakage report file"),
        ("source_inventory", "I2 source inventory file"),
    ):
        try:
            payload = _read_json(_require_file(paths[key], label))
            if key == "summary":
                summary = payload
            elif key == "manifest":
                manifest = payload
            elif key == "split_summary":
                split_summary = payload
            elif key == "leakage_report":
                leakage_report = payload
            elif key == "source_inventory":
                source_inventory = payload
        except Exception as exc:  # noqa: BLE001 - aggregate reporting
            input_errors[key] = str(exc)

    rows_by_source = _count(rows, "source_id")
    rows_by_label = _count(rows, "label")
    rows_by_split = _count(rows, "split")
    rows_by_source_and_split = _count_by_two_fields(rows, "source_id", "split")
    rows_by_label_and_split = _count_by_two_fields(rows, "label", "split")
    required_field_missing_counts = _missing_required_field_counts(rows)
    duplicate_sample_id_count = _duplicate_count([str(row.get("sample_id", "")) for row in rows])
    duplicate_chip_id_count = _duplicate_count([str(row.get("chip_id", "")) for row in rows])
    group_leakage_detected = _group_leakage_detected(rows)
    unknown_label_count = sum(1 for row in rows if str(row.get("label", "")) not in VALID_LABELS)
    unknown_split_count = sum(1 for row in rows if str(row.get("split", "")) not in VALID_SPLITS)

    count_checks = {
        "total_rows_match": len(rows) == EXPECTED_TOTAL_ROWS,
        "rows_by_source_match": rows_by_source == EXPECTED_ROWS_BY_SOURCE,
        "rows_by_label_match": rows_by_label == EXPECTED_ROWS_BY_LABEL,
        "rows_by_split_match": rows_by_split == EXPECTED_ROWS_BY_SPLIT,
        "summary_status_match": summary.get("status") == "private_i2_pack_assembled",
        "summary_i2_rows_written_match": summary.get("i2_rows_written") == EXPECTED_TOTAL_ROWS,
        "manifest_row_count_match": manifest.get("row_count") == EXPECTED_TOTAL_ROWS,
        "source_inventory_total_match": source_inventory.get("total_rows") == EXPECTED_TOTAL_ROWS,
        "split_summary_present": bool(split_summary),
        "leakage_report_present": bool(leakage_report),
    }

    readiness_decision = _readiness_decision(
        input_errors=input_errors,
        count_checks=count_checks,
        required_field_missing_counts=required_field_missing_counts,
        duplicate_sample_id_count=duplicate_sample_id_count,
        duplicate_chip_id_count=duplicate_chip_id_count,
        group_leakage_detected=group_leakage_detected,
        unknown_label_count=unknown_label_count,
        unknown_split_count=unknown_split_count,
    )

    result = {
        "status": "validation_passed" if readiness_decision == "ready_for_private_training_later" else "validation_failed",
        "readiness_decision": readiness_decision,
        "total_rows": len(rows),
        "expected_total_rows": EXPECTED_TOTAL_ROWS,
        "rows_by_source": rows_by_source,
        "rows_by_label": rows_by_label,
        "rows_by_split": rows_by_split,
        "rows_by_source_and_split": rows_by_source_and_split,
        "rows_by_label_and_split": rows_by_label_and_split,
        "required_field_missing_counts": required_field_missing_counts,
        "duplicate_sample_id_count": duplicate_sample_id_count,
        "duplicate_chip_id_count": duplicate_chip_id_count,
        "group_leakage_detected": group_leakage_detected,
        "unknown_label_count": unknown_label_count,
        "unknown_split_count": unknown_split_count,
        "input_errors": input_errors,
        "count_checks": count_checks,
        "validator_run_on_real_data": True,
        "training_started": False,
        "inference_started": False,
    }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if readiness_decision == "ready_for_private_training_later" else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate private I2 readiness with aggregate-only output.")
    parser.add_argument("--i2-dir", default=str(DEFAULT_I2_DIR))
    return parser.parse_args()


def _readiness_decision(
    *,
    input_errors: dict[str, str],
    count_checks: dict[str, bool],
    required_field_missing_counts: dict[str, int],
    duplicate_sample_id_count: int,
    duplicate_chip_id_count: int,
    group_leakage_detected: bool,
    unknown_label_count: int,
    unknown_split_count: int,
) -> str:
    if input_errors:
        return "not_ready_input_files_missing"
    if required_field_missing_counts:
        return "not_ready_missing_required_fields"
    if not all(count_checks.values()):
        return "not_ready_bad_counts"
    if group_leakage_detected:
        return "not_ready_split_leakage"
    if duplicate_sample_id_count or duplicate_chip_id_count:
        return "not_ready_duplicate_ids"
    if unknown_label_count or unknown_split_count:
        return "not_ready_unknown_labels_or_splits"
    return "ready_for_private_training_later"


def _require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    _validate_private_path_not_inside_repo(path, label)
    return path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except ValueError as exc:
                raise ReadinessError(f"invalid JSON on line {line_number}: {path}") from exc
            if not isinstance(row, dict):
                raise ReadinessError(f"line {line_number} is not a JSON object: {path}")
            rows.append(row)
    if not rows:
        raise ReadinessError(f"empty JSONL file: {path}")
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReadinessError(f"JSON file is not an object: {path}")
    return payload


def _count(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter = Counter(str(row.get(field, "missing")) for row in rows)
    return dict(sorted(counter.items()))


def _count_by_two_fields(rows: list[dict[str, Any]], outer_field: str, inner_field: str) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for row in rows:
        outer = str(row.get(outer_field, "missing"))
        inner = str(row.get(inner_field, "missing"))
        result.setdefault(outer, {})
        result[outer][inner] = result[outer].get(inner, 0) + 1
    return {outer: dict(sorted(inner_counts.items())) for outer, inner_counts in sorted(result.items())}


def _missing_required_field_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for field in REQUIRED_FIELDS:
            if field not in row or row[field] in (None, ""):
                counts[field] += 1
    return dict(sorted(counts.items()))


def _duplicate_count(values: list[str]) -> int:
    counts = Counter(value for value in values if value)
    return sum(count - 1 for count in counts.values() if count > 1)


def _group_leakage_detected(rows: list[dict[str, Any]]) -> bool:
    group_splits: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        group_id = str(row.get("group_id", ""))
        split = str(row.get("split", ""))
        if group_id:
            group_splits[group_id].add(split)
    return any(len(splits) > 1 for splits in group_splits.values())


def _validate_private_path_not_inside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(f"{label} must be outside the repository")


if __name__ == "__main__":
    raise SystemExit(main())
