"""Dry-run or assemble the private I2 dataset pack outside Git.

Default behavior is dry-run only and writes nothing.

This script reads private I1 rows and private split assignments from local folders
outside the repository, validates one-to-one split coverage, applies split labels,
and optionally writes a private I2 pack outside Git when --write is provided.

It does not run a validator, train a model, run inference, call Earth Engine, or
change app/API/frontend code.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\I2_PRIVATE")

SOURCE_CONFIGS = {
    "POS-01": {
        "path": Path(r"C:\Dev\New_GEE_PRIVATE\I1_POS01\training_examples.pos01.private.jsonl"),
        "expected_rows": 217,
    },
    "C05": {
        "path": Path(r"C:\Dev\New_GEE_PRIVATE\I1_C05\training_examples.c05.private.jsonl"),
        "expected_rows": 217,
    },
    "C06": {
        "path": Path(r"C:\Dev\New_GEE_PRIVATE\I1_C06\training_examples.c06.private.jsonl"),
        "expected_rows": 217,
    },
    "C07": {
        "path": Path(r"C:\Dev\New_GEE_PRIVATE\I1_C07\training_examples.c07.private.jsonl"),
        "expected_rows": 217,
    },
}

DEFAULT_SPLIT_ASSIGNMENTS = Path(r"C:\Dev\New_GEE_PRIVATE\SPLITS\split_assignments.private.jsonl")
DEFAULT_SPLIT_SUMMARY = Path(r"C:\Dev\New_GEE_PRIVATE\SPLITS\split_assignments.private.summary.json")
DEFAULT_SPLIT_LEAKAGE_REPORT = Path(r"C:\Dev\New_GEE_PRIVATE\SPLITS\split_leakage_report.private.json")

EXPECTED_TOTAL_ROWS = 868
VALID_SPLITS = {"train", "val", "test", "holdout"}

REQUIRED_I2_FIELDS = (
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
)


class I2AssemblyError(ValueError):
    """Raised when private I2 assembly cannot proceed safely."""


def main() -> int:
    args = _parse_args()
    output_dir = Path(args.output_dir)
    split_assignments_path = Path(args.split_assignments)
    split_summary_path = Path(args.split_summary)
    split_leakage_report_path = Path(args.split_leakage_report)

    _validate_private_path_not_inside_repo(output_dir, "output directory")
    _validate_private_existing_file(split_assignments_path, "split assignments")
    _validate_private_existing_file(split_summary_path, "split summary")
    _validate_private_existing_file(split_leakage_report_path, "split leakage report")

    source_rows: dict[str, list[dict[str, Any]]] = {}
    load_errors: dict[str, str] = {}
    row_count_errors: dict[str, str] = {}

    for source_id, config in SOURCE_CONFIGS.items():
        path = Path(config["path"])
        try:
            _validate_private_existing_file(path, f"{source_id} private I1 file")
            rows = _read_jsonl(path)
            source_rows[source_id] = rows
            expected = int(config["expected_rows"])
            if len(rows) != expected:
                row_count_errors[source_id] = f"expected {expected}, found {len(rows)}"
        except Exception as exc:  # noqa: BLE001 - aggregate dry-run reporting
            source_rows[source_id] = []
            load_errors[source_id] = str(exc)

    split_assignments = _read_jsonl(split_assignments_path)
    split_summary = _read_json(split_summary_path)
    split_leakage_report = _read_json(split_leakage_report_path)

    i1_rows = _flatten_source_rows(source_rows)
    assembly_result = _assemble_rows(i1_rows=i1_rows, split_assignments=split_assignments)
    i2_rows = assembly_result["rows"]
    assembly_errors = assembly_result["errors"]

    leakage_report = _build_i2_leakage_report(i2_rows)
    missing_required_field_counts = _missing_required_field_counts(i2_rows)
    rows_by_source = _rows_by_source(i2_rows)
    rows_by_label = _rows_by_label(i2_rows)
    rows_by_split = _rows_by_split(i2_rows)
    rows_by_source_and_split = _rows_by_source_and_split(i2_rows)
    rows_by_label_and_split = _rows_by_label_and_split(i2_rows)

    ready_to_write = (
        not load_errors
        and not row_count_errors
        and not assembly_errors
        and len(i1_rows) == EXPECTED_TOTAL_ROWS
        and len(split_assignments) == EXPECTED_TOTAL_ROWS
        and len(i2_rows) == EXPECTED_TOTAL_ROWS
        and not any(missing_required_field_counts.values())
        and not leakage_report["group_leakage_detected"]
        and leakage_report["duplicate_sample_id_count"] == 0
        and _split_inputs_passed(split_summary, split_leakage_report)
    )

    summary = {
        "status": _status(write=args.write, ready_to_write=ready_to_write),
        "total_i1_rows_loaded": len(i1_rows),
        "expected_total_i1_rows": EXPECTED_TOTAL_ROWS,
        "total_split_assignments_loaded": len(split_assignments),
        "matched_assignment_count": assembly_result["matched_assignment_count"],
        "missing_assignment_count": assembly_result["missing_assignment_count"],
        "extra_assignment_count": assembly_result["extra_assignment_count"],
        "rows_by_source": rows_by_source,
        "rows_by_label": rows_by_label,
        "rows_by_split": rows_by_split,
        "rows_by_source_and_split": rows_by_source_and_split,
        "rows_by_label_and_split": rows_by_label_and_split,
        "missing_required_field_counts": missing_required_field_counts,
        "load_errors": load_errors,
        "row_count_errors": row_count_errors,
        "assembly_errors": assembly_errors,
        "leakage_check_passed": not leakage_report["group_leakage_detected"],
        "duplicate_sample_id_count": leakage_report["duplicate_sample_id_count"],
        "duplicate_chip_id_count": leakage_report["duplicate_chip_id_count"],
        "group_leakage_detected": leakage_report["group_leakage_detected"],
        "split_inputs_passed": _split_inputs_passed(split_summary, split_leakage_report),
        "i2_rows_written": 0,
        "validator_run_on_real_data": False,
        "training_started": False,
        "inference_started": False,
    }

    if args.write:
        if not ready_to_write:
            raise SystemExit("Private I2 assembly refused: dry-run checks did not pass.")
        output_dir.mkdir(parents=True, exist_ok=True)
        _write_jsonl(output_dir / "i2_training_examples.private.jsonl", i2_rows)
        summary["i2_rows_written"] = len(i2_rows)
        summary["status"] = "private_i2_pack_assembled"
        _write_json(output_dir / "i2_summary.private.json", summary)
        _write_json(output_dir / "i2_manifest.private.json", _manifest(summary))
        _write_json(output_dir / "i2_source_inventory.private.json", _source_inventory(rows_by_source))
        _write_json(output_dir / "i2_split_summary.private.json", {"rows_by_split": rows_by_split, "rows_by_source_and_split": rows_by_source_and_split, "rows_by_label_and_split": rows_by_label_and_split})
        _write_json(output_dir / "i2_leakage_report.private.json", leakage_report)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run or assemble private I2 pack outside Git.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--split-assignments", default=str(DEFAULT_SPLIT_ASSIGNMENTS))
    parser.add_argument("--split-summary", default=str(DEFAULT_SPLIT_SUMMARY))
    parser.add_argument("--split-leakage-report", default=str(DEFAULT_SPLIT_LEAKAGE_REPORT))
    parser.add_argument("--write", action="store_true", help="Write private I2 files outside Git. Without this flag, dry-run only.")
    return parser.parse_args()


def _status(*, write: bool, ready_to_write: bool) -> str:
    if write and ready_to_write:
        return "ready_to_write_private_i2_pack"
    if write:
        return "write_refused"
    if ready_to_write:
        return "dry_run_ready"
    return "dry_run_checks_failed"


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
                raise I2AssemblyError(f"invalid JSON on line {line_number}: {path}") from exc
            if not isinstance(row, dict):
                raise I2AssemblyError(f"line {line_number} is not a JSON object: {path}")
            rows.append(row)
    if not rows:
        raise I2AssemblyError(f"empty JSONL file: {path}")
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise I2AssemblyError(f"JSON file is not an object: {path}")
    return payload


def _flatten_source_rows(source_rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, source_specific_rows in source_rows.items():
        for row in source_specific_rows:
            enriched = dict(row)
            enriched["source_id"] = source_id
            rows.append(enriched)
    return rows


def _assemble_rows(*, i1_rows: list[dict[str, Any]], split_assignments: list[dict[str, Any]]) -> dict[str, Any]:
    errors: dict[str, str] = {}
    split_by_sample_id: dict[str, dict[str, Any]] = {}

    for assignment in split_assignments:
        sample_id = str(assignment.get("sample_id", "")).strip()
        assigned_split = str(assignment.get("assigned_split", "")).strip()
        if not sample_id:
            errors["blank_assignment_sample_id"] = "one or more split assignments lack sample_id"
            continue
        if assigned_split not in VALID_SPLITS:
            errors["invalid_assignment_split"] = "one or more split assignments have invalid split"
            continue
        if sample_id in split_by_sample_id:
            errors["duplicate_assignment_sample_id"] = "one or more sample_id values appear in multiple split assignments"
            continue
        split_by_sample_id[sample_id] = assignment

    i1_by_sample_id: dict[str, dict[str, Any]] = {}
    for row in i1_rows:
        sample_id = str(row.get("sample_id", "")).strip()
        if not sample_id:
            errors["blank_i1_sample_id"] = "one or more I1 rows lack sample_id"
            continue
        if sample_id in i1_by_sample_id:
            errors["duplicate_i1_sample_id"] = "one or more sample_id values appear in multiple I1 rows"
            continue
        i1_by_sample_id[sample_id] = row

    rows: list[dict[str, Any]] = []
    missing_assignment_count = 0
    for sample_id, row in i1_by_sample_id.items():
        assignment = split_by_sample_id.get(sample_id)
        if assignment is None:
            missing_assignment_count += 1
            continue
        assembled = dict(row)
        assembled["split"] = assignment["assigned_split"]
        rows.append(assembled)

    extra_assignment_count = sum(1 for sample_id in split_by_sample_id if sample_id not in i1_by_sample_id)
    if missing_assignment_count:
        errors["missing_assignments"] = f"{missing_assignment_count} I1 rows lack split assignments"
    if extra_assignment_count:
        errors["extra_assignments"] = f"{extra_assignment_count} split assignments lack matching I1 rows"

    return {
        "rows": rows,
        "errors": errors,
        "matched_assignment_count": len(rows),
        "missing_assignment_count": missing_assignment_count,
        "extra_assignment_count": extra_assignment_count,
    }


def _missing_required_field_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for field in REQUIRED_I2_FIELDS:
            if field not in row or row[field] in (None, ""):
                counts[field] += 1
    return dict(sorted(counts.items()))


def _build_i2_leakage_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    group_splits: dict[str, set[str]] = defaultdict(set)
    sample_ids: list[str] = []
    chip_ids: list[str] = []

    for row in rows:
        group_splits[str(row.get("group_id", ""))].add(str(row.get("split", "")))
        sample_ids.append(str(row.get("sample_id", "")))
        chip_ids.append(str(row.get("chip_id", "")))

    leaking_group_count = sum(1 for splits in group_splits.values() if len(splits) > 1)
    return {
        "total_rows_checked": len(rows),
        "duplicate_sample_id_count": _duplicate_count(sample_ids),
        "duplicate_chip_id_count": _duplicate_count(chip_ids),
        "leaking_group_count": leaking_group_count,
        "group_leakage_detected": leaking_group_count > 0,
        "validator_run_on_real_data": False,
    }


def _duplicate_count(values: list[str]) -> int:
    counts = Counter(value for value in values if value)
    return sum(count - 1 for count in counts.values() if count > 1)


def _rows_by_source(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(str(row.get("source_id", "missing")) for row in rows)
    return dict(sorted(counter.items()))


def _rows_by_label(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(str(row.get("label", "missing")) for row in rows)
    return dict(sorted(counter.items()))


def _rows_by_split(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(str(row.get("split", "missing")) for row in rows)
    return {split: counter.get(split, 0) for split in ("train", "val", "test", "holdout")}


def _rows_by_source_and_split(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    result = {source_id: {split: 0 for split in ("train", "val", "test", "holdout")} for source_id in SOURCE_CONFIGS}
    for row in rows:
        source_id = str(row.get("source_id", "missing"))
        split = str(row.get("split", "missing"))
        result.setdefault(source_id, {name: 0 for name in ("train", "val", "test", "holdout")})
        if split in result[source_id]:
            result[source_id][split] += 1
    return result


def _rows_by_label_and_split(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for row in rows:
        label = str(row.get("label", "missing"))
        split = str(row.get("split", "missing"))
        result.setdefault(label, {name: 0 for name in ("train", "val", "test", "holdout")})
        if split in result[label]:
            result[label][split] += 1
    return dict(sorted(result.items()))


def _split_inputs_passed(split_summary: dict[str, Any], split_leakage_report: dict[str, Any]) -> bool:
    return (
        split_summary.get("status") == "private_split_assignments_written"
        and split_summary.get("total_rows") == EXPECTED_TOTAL_ROWS
        and split_summary.get("real_split_assignments_written") == EXPECTED_TOTAL_ROWS
        and split_summary.get("group_leakage_detected") is False
        and split_summary.get("duplicate_sample_id_count") == 0
        and split_leakage_report.get("group_leakage_detected") is False
        and split_leakage_report.get("duplicate_sample_id_count") == 0
    )


def _manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset_id": "i2_private_stronger_v1",
        "status": summary["status"],
        "row_count": summary["i2_rows_written"],
        "source_count": len(SOURCE_CONFIGS),
        "validator_run_on_real_data": False,
        "training_started": False,
        "inference_started": False,
    }


def _source_inventory(rows_by_source: dict[str, int]) -> dict[str, Any]:
    return {
        "sources": rows_by_source,
        "expected_sources": sorted(SOURCE_CONFIGS.keys()),
        "total_rows": sum(rows_by_source.values()),
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temp_path, path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temp_path, path)


def _validate_private_existing_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    _validate_private_path_not_inside_repo(path, label)


def _validate_private_path_not_inside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(f"{label} must be outside the repository")


if __name__ == "__main__":
    raise SystemExit(main())
