"""Build a private H3 smoke-test feature matrix outside Git.

Default behavior is dry-run only and writes nothing.

This script reads the private I2 pack from a local folder outside the repository
and builds a deterministic numeric metadata-derived feature matrix for H3 pipeline
smoke testing. The matrix is useful to verify local training plumbing, but it is
not a scientifically meaningful remote-sensing feature set.

It does not train a model, write model artifacts, run inference, call Earth
Engine, or change app/API/frontend code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_I2_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\I2_PRIVATE")
DEFAULT_OUTPUT_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\H3_TRAINING")
I2_ROWS_FILE = "i2_training_examples.private.jsonl"
EXPECTED_TOTAL_ROWS = 868
VALID_LABELS = {"Class_A", "Class_Background", "Class_HardNegative"}
VALID_SPLITS = {"train", "val", "test", "holdout"}
SOURCE_IDS = ("POS-01", "C05", "C06", "C07")
SPLITS = ("train", "val", "test", "holdout")

# These are metadata-derived smoke-test columns only. They should not be used for
# scientific model claims because source_id can be correlated with label family in
# this early private I2 pack.
FEATURE_COLUMNS = (
    "source_pos01_indicator",
    "source_c05_indicator",
    "source_c06_indicator",
    "source_c07_indicator",
    "stable_hash_feature_01",
    "stable_hash_feature_02",
    "stable_hash_feature_03",
    "stable_hash_feature_04",
)

REQUIRED_I2_FIELDS = (
    "sample_id",
    "dataset_id",
    "group_id",
    "chip_id",
    "split",
    "label",
    "source_id",
)


class FeatureBuildError(ValueError):
    """Raised when the private feature matrix cannot be built safely."""


def main() -> int:
    args = _parse_args()
    i2_dir = Path(args.i2_dir)
    output_dir = Path(args.output_dir)

    _validate_private_path_not_inside_repo(i2_dir, "I2 directory")
    _validate_private_path_not_inside_repo(output_dir, "output directory")

    i2_rows_path = i2_dir / I2_ROWS_FILE
    rows = _read_jsonl(_require_file(i2_rows_path, "private I2 rows file"))

    missing_required_field_counts = _missing_required_field_counts(rows)
    duplicate_sample_id_count = _duplicate_count([str(row.get("sample_id", "")) for row in rows])
    unknown_label_count = sum(1 for row in rows if str(row.get("label", "")) not in VALID_LABELS)
    unknown_split_count = sum(1 for row in rows if str(row.get("split", "")) not in VALID_SPLITS)
    rows_by_label = _count(rows, "label")
    rows_by_split = _count(rows, "split")
    rows_by_source = _count(rows, "source_id")

    matrix_rows = [_matrix_row(row) for row in rows]
    matrix_join_ready = (
        len(matrix_rows) == EXPECTED_TOTAL_ROWS
        and len(rows) == EXPECTED_TOTAL_ROWS
        and not missing_required_field_counts
        and duplicate_sample_id_count == 0
        and unknown_label_count == 0
        and unknown_split_count == 0
    )

    summary = {
        "status": "ready_to_write_feature_matrix" if args.write and matrix_join_ready else ("dry_run_ready" if matrix_join_ready else "dry_run_checks_failed"),
        "feature_set_type": "metadata_smoke_test_only",
        "scientific_training_ready": False,
        "pipeline_smoke_test_ready": matrix_join_ready,
        "i2_rows_loaded": len(rows),
        "expected_i2_rows": EXPECTED_TOTAL_ROWS,
        "planned_matrix_rows": len(matrix_rows),
        "planned_feature_column_count": len(FEATURE_COLUMNS),
        "feature_columns": list(FEATURE_COLUMNS),
        "rows_by_label": rows_by_label,
        "rows_by_split": rows_by_split,
        "rows_by_source": rows_by_source,
        "missing_required_field_counts": missing_required_field_counts,
        "duplicate_sample_id_count": duplicate_sample_id_count,
        "unknown_label_count": unknown_label_count,
        "unknown_split_count": unknown_split_count,
        "feature_matrix_written": False,
        "training_started": False,
        "inference_started": False,
        "model_artifact_written": False,
        "notes": (
            "This feature matrix is metadata-derived and intended for H3 local "
            "pipeline smoke testing only. It is not a final scientific feature set."
        ),
    }

    if args.write:
        if not matrix_join_ready:
            raise SystemExit("H3 feature matrix write refused: dry-run checks did not pass.")
        output_dir.mkdir(parents=True, exist_ok=True)
        matrix_path = output_dir / "training_matrix.private.csv"
        summary_path = output_dir / "training_matrix.private.summary.json"
        lineage_path = output_dir / "feature_matrix_lineage.private.json"
        _write_csv(matrix_path, matrix_rows)
        summary["status"] = "feature_matrix_written"
        summary["feature_matrix_written"] = True
        _write_json(summary_path, summary)
        _write_json(
            lineage_path,
            {
                "feature_set_type": "metadata_smoke_test_only",
                "i2_input_file": str(i2_rows_path),
                "matrix_file": str(matrix_path),
                "row_count": len(matrix_rows),
                "feature_columns": list(FEATURE_COLUMNS),
                "scientific_training_ready": False,
                "training_started": False,
                "inference_started": False,
            },
        )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if matrix_join_ready else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a private H3 smoke-test feature matrix outside Git.")
    parser.add_argument("--i2-dir", default=str(DEFAULT_I2_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--write", action="store_true", help="Write private feature matrix files outside Git. Without this flag, dry-run only.")
    return parser.parse_args()


def _matrix_row(row: dict[str, Any]) -> dict[str, Any]:
    source_id = str(row.get("source_id", ""))
    sample_id = str(row.get("sample_id", ""))
    output = {
        "sample_id": sample_id,
        "split": str(row.get("split", "")),
        "label": str(row.get("label", "")),
        "source_id": source_id,
        "source_pos01_indicator": _indicator(source_id == "POS-01"),
        "source_c05_indicator": _indicator(source_id == "C05"),
        "source_c06_indicator": _indicator(source_id == "C06"),
        "source_c07_indicator": _indicator(source_id == "C07"),
        "stable_hash_feature_01": _hash_float(sample_id, "h3_feature_01"),
        "stable_hash_feature_02": _hash_float(sample_id, "h3_feature_02"),
        "stable_hash_feature_03": _hash_float(sample_id, "h3_feature_03"),
        "stable_hash_feature_04": _hash_float(sample_id, "h3_feature_04"),
    }
    return output


def _indicator(condition: bool) -> str:
    return "1" if condition else "0"


def _hash_float(sample_id: str, salt: str) -> str:
    digest = hashlib.sha256(f"{salt}:{sample_id}".encode("utf-8")).hexdigest()
    integer = int(digest[:12], 16)
    value = integer / float(16**12 - 1)
    return f"{value:.8f}"


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
                raise FeatureBuildError(f"invalid JSON on line {line_number}: {path}") from exc
            if not isinstance(row, dict):
                raise FeatureBuildError(f"line {line_number} is not a JSON object: {path}")
            rows.append(row)
    if not rows:
        raise FeatureBuildError(f"empty JSONL file: {path}")
    return rows


def _missing_required_field_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for field in REQUIRED_I2_FIELDS:
            if field not in row or row[field] in (None, ""):
                counts[field] += 1
    return dict(sorted(counts.items()))


def _count(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field, "missing")) for row in rows).items()))


def _duplicate_count(values: list[str]) -> int:
    counts = Counter(value for value in values if value)
    return sum(count - 1 for count in counts.values() if count > 1)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise FeatureBuildError("cannot write empty feature matrix")
    fieldnames = ["sample_id", "split", "label", "source_id", *FEATURE_COLUMNS]
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp_path, path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp_path, path)


def _require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    _validate_private_path_not_inside_repo(path, label)
    return path


def _validate_private_path_not_inside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(f"{label} must be outside the repository")


if __name__ == "__main__":
    raise SystemExit(main())
