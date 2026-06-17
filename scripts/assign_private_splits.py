"""Dry-run or write private split assignments outside Git.

Default behavior is dry-run only and writes nothing.

This script reads private I1 rows from local folders outside the repository,
assigns deterministic group_id-based splits, and optionally writes private split
assignment files outside Git when --write is provided.

It does not assemble I2, run a validator, train a model, run inference, call
Earth Engine, or change app/API/frontend code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\SPLITS")
DEFAULT_SEED = 20260616

SOURCE_CONFIGS = {
    "POS-01": {
        "path": Path(r"C:\Dev\New_GEE_PRIVATE\I1_POS01\training_examples.pos01.private.jsonl"),
        "expected_rows": 217,
        "targets": {"train": 152, "val": 22, "test": 22, "holdout": 21},
    },
    "C05": {
        "path": Path(r"C:\Dev\New_GEE_PRIVATE\I1_C05\training_examples.c05.private.jsonl"),
        "expected_rows": 217,
        "targets": {"train": 152, "val": 22, "test": 22, "holdout": 21},
    },
    "C06": {
        "path": Path(r"C:\Dev\New_GEE_PRIVATE\I1_C06\training_examples.c06.private.jsonl"),
        "expected_rows": 217,
        "targets": {"train": 152, "val": 22, "test": 22, "holdout": 21},
    },
    "C07": {
        "path": Path(r"C:\Dev\New_GEE_PRIVATE\I1_C07\training_examples.c07.private.jsonl"),
        "expected_rows": 217,
        "targets": {"train": 152, "val": 22, "test": 22, "holdout": 21},
    },
}

SPLITS = ("train", "val", "test", "holdout")

REQUIRED_FIELDS = (
    "sample_id",
    "dataset_id",
    "group_id",
    "chip_id",
    "split",
    "label",
    "label_quality",
    "evidence_source_type",
    "evidence_source_version",
    "features_ref",
    "metadata_ref",
    "redaction_class",
)


class SplitAssignmentError(ValueError):
    """Raised when private split assignment cannot proceed safely."""


def main() -> int:
    args = _parse_args()
    output_dir = Path(args.output_dir)
    _validate_private_path_not_inside_repo(output_dir, "output directory")

    source_rows: dict[str, list[dict[str, Any]]] = {}
    load_errors: dict[str, str] = {}
    missing_required_field_counts: dict[str, dict[str, int]] = {}
    row_count_errors: dict[str, str] = {}

    for source_id, config in SOURCE_CONFIGS.items():
        path = Path(config["path"])
        try:
            _validate_private_existing_file(path, f"{source_id} private I1 file")
            rows = _read_jsonl(path)
            source_rows[source_id] = rows
            missing_required_field_counts[source_id] = _missing_required_field_counts(rows)
            expected = int(config["expected_rows"])
            if len(rows) != expected:
                row_count_errors[source_id] = f"expected {expected}, found {len(rows)}"
        except Exception as exc:  # noqa: BLE001 - aggregate dry-run reporting
            source_rows[source_id] = []
            load_errors[source_id] = str(exc)
            missing_required_field_counts[source_id] = {}

    assignments, assignment_errors = _assign_all_sources(source_rows, args.seed)
    leakage_report = _build_leakage_report(assignments, source_rows)

    rows_by_source = {source_id: len(rows) for source_id, rows in source_rows.items()}
    rows_by_label = _rows_by_label(source_rows)
    planned_rows_by_split = _count_assignments_by_split(assignments)
    planned_rows_by_source_and_split = _count_assignments_by_source_and_split(assignments)
    planned_rows_by_label_and_split = _count_assignments_by_label_and_split(assignments)

    ready_to_write = (
        not load_errors
        and not row_count_errors
        and not assignment_errors
        and not any(counts for counts in missing_required_field_counts.values())
        and not leakage_report["group_leakage_detected"]
        and not leakage_report["duplicate_sample_id_count"]
    )

    summary = {
        "status": _status(write=args.write, ready_to_write=ready_to_write),
        "seed": args.seed,
        "total_rows": sum(rows_by_source.values()),
        "expected_total_rows": 868,
        "rows_by_source": rows_by_source,
        "rows_by_label": dict(sorted(rows_by_label.items())),
        "planned_rows_by_split": planned_rows_by_split,
        "planned_rows_by_source_and_split": planned_rows_by_source_and_split,
        "planned_rows_by_label_and_split": planned_rows_by_label_and_split,
        "missing_required_field_counts": missing_required_field_counts,
        "load_errors": load_errors,
        "row_count_errors": row_count_errors,
        "assignment_errors": assignment_errors,
        "duplicate_sample_id_count": leakage_report["duplicate_sample_id_count"],
        "duplicate_chip_id_count": leakage_report["duplicate_chip_id_count"],
        "group_leakage_detected": leakage_report["group_leakage_detected"],
        "real_split_assignments_written": 0,
        "i2_pack_assembled": False,
        "validator_run_on_real_data": False,
    }

    if args.write:
        if not ready_to_write:
            raise SystemExit("Private split assignment write refused: dry-run checks did not pass.")
        output_dir.mkdir(parents=True, exist_ok=True)
        _write_jsonl(output_dir / "split_assignments.private.jsonl", assignments)
        summary["real_split_assignments_written"] = len(assignments)
        summary["status"] = "private_split_assignments_written"
        _write_json(output_dir / "split_assignments.private.summary.json", summary)
        _write_json(output_dir / "split_leakage_report.private.json", leakage_report)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or write private split assignments outside Git."
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write private split assignment files outside Git. Without this flag, dry-run only.",
    )
    return parser.parse_args()


def _status(*, write: bool, ready_to_write: bool) -> str:
    if write and ready_to_write:
        return "ready_to_write_private_split_assignments"
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
                raise SplitAssignmentError(f"invalid JSON on line {line_number}: {path}") from exc
            if not isinstance(row, dict):
                raise SplitAssignmentError(f"line {line_number} is not a JSON object: {path}")
            rows.append(row)
    if not rows:
        raise SplitAssignmentError(f"empty JSONL file: {path}")
    return rows


def _missing_required_field_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for field in REQUIRED_FIELDS:
            if field not in row or row[field] in (None, ""):
                counts[field] += 1
    return dict(sorted(counts.items()))


def _assign_all_sources(
    source_rows: dict[str, list[dict[str, Any]]],
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    all_assignments: list[dict[str, Any]] = []
    errors: dict[str, str] = {}

    for source_id, rows in source_rows.items():
        if not rows:
            errors[source_id] = "no rows loaded"
            continue
        targets = SOURCE_CONFIGS[source_id]["targets"]
        try:
            all_assignments.extend(
                _assign_source_by_group(
                    source_id=source_id,
                    rows=rows,
                    targets=targets,
                    seed=seed,
                )
            )
        except SplitAssignmentError as exc:
            errors[source_id] = str(exc)

    return all_assignments, errors


def _assign_source_by_group(
    *,
    source_id: str,
    rows: list[dict[str, Any]],
    targets: dict[str, int],
    seed: int,
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        group_id = str(row.get("group_id", "")).strip()
        if not group_id:
            raise SplitAssignmentError(f"{source_id} has row without group_id")
        groups[group_id].append(row)

    ordered_groups = sorted(
        groups.items(),
        key=lambda item: _stable_hash({"seed": seed, "source_id": source_id, "group_id": item[0]}),
    )

    split_counts = {split: 0 for split in SPLITS}
    group_to_split: dict[str, str] = {}

    for split in SPLITS:
        target = targets[split]
        for group_id, group_rows in ordered_groups:
            if group_id in group_to_split:
                continue
            if split_counts[split] >= target:
                break
            group_to_split[group_id] = split
            split_counts[split] += len(group_rows)

    unassigned_groups = [group_id for group_id, _ in ordered_groups if group_id not in group_to_split]
    if unassigned_groups:
        raise SplitAssignmentError(
            f"{source_id} has {len(unassigned_groups)} unassigned groups after split assignment"
        )

    for split, target in targets.items():
        if split_counts[split] != target:
            raise SplitAssignmentError(
                f"{source_id} split {split} expected {target}, assigned {split_counts[split]}"
            )

    assignments: list[dict[str, Any]] = []
    for row in rows:
        group_id = str(row["group_id"])
        split = group_to_split[group_id]
        assignments.append(
            {
                "source_id": source_id,
                "dataset_id": row.get("dataset_id"),
                "sample_id": row.get("sample_id"),
                "group_id": group_id,
                "chip_id": row.get("chip_id"),
                "label": row.get("label"),
                "assigned_split": split,
            }
        )
    return assignments


def _build_leakage_report(
    assignments: list[dict[str, Any]],
    source_rows: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    group_splits: dict[str, set[str]] = defaultdict(set)
    sample_ids: list[str] = []
    chip_ids: list[str] = []

    for assignment in assignments:
        group_splits[str(assignment.get("group_id", ""))].add(str(assignment.get("assigned_split", "")))
        sample_ids.append(str(assignment.get("sample_id", "")))
        chip_ids.append(str(assignment.get("chip_id", "")))

    duplicate_sample_id_count = _duplicate_count(sample_ids)
    duplicate_chip_id_count = _duplicate_count(chip_ids)
    leaking_group_count = sum(1 for splits in group_splits.values() if len(splits) > 1)

    return {
        "total_assignments_checked": len(assignments),
        "source_files_checked": sorted(source_rows.keys()),
        "duplicate_sample_id_count": duplicate_sample_id_count,
        "duplicate_chip_id_count": duplicate_chip_id_count,
        "leaking_group_count": leaking_group_count,
        "group_leakage_detected": leaking_group_count > 0,
        "i2_pack_assembled": False,
        "validator_run_on_real_data": False,
    }


def _duplicate_count(values: list[str]) -> int:
    counts = Counter(value for value in values if value)
    return sum(count - 1 for count in counts.values() if count > 1)


def _rows_by_label(source_rows: dict[str, list[dict[str, Any]]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for rows in source_rows.values():
        for row in rows:
            counter[str(row.get("label", "missing"))] += 1
    return counter


def _count_assignments_by_split(assignments: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(str(row.get("assigned_split", "missing")) for row in assignments)
    return {split: counter.get(split, 0) for split in SPLITS}


def _count_assignments_by_source_and_split(assignments: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    result = {source_id: {split: 0 for split in SPLITS} for source_id in SOURCE_CONFIGS}
    for row in assignments:
        source_id = str(row.get("source_id", "missing"))
        split = str(row.get("assigned_split", "missing"))
        if source_id not in result:
            result[source_id] = {name: 0 for name in SPLITS}
        if split in result[source_id]:
            result[source_id][split] += 1
    return result


def _count_assignments_by_label_and_split(assignments: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for row in assignments:
        label = str(row.get("label", "missing"))
        split = str(row.get("assigned_split", "missing"))
        result.setdefault(label, {name: 0 for name in SPLITS})
        if split in result[label]:
            result[label][split] += 1
    return dict(sorted(result.items()))


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


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
