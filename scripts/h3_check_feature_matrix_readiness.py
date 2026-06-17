"""Check H3 feature matrix readiness for private training.

This script reads the private I2 pack from a local folder outside Git and checks
whether the rows are linked to usable training features.

Default behavior is check-only. It writes nothing, trains nothing, runs no
inference, and does not change app/API/frontend code.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_I2_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\I2_PRIVATE")
DEFAULT_H3_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\H3_TRAINING")
DEFAULT_FEATURE_MATRIX_CSV = DEFAULT_H3_DIR / "training_matrix.private.csv"
DEFAULT_FEATURE_MATRIX_JSONL = DEFAULT_H3_DIR / "training_matrix.private.jsonl"

I2_ROWS_FILE = "i2_training_examples.private.jsonl"
EXPECTED_TOTAL_ROWS = 868
VALID_LABELS = {"Class_A", "Class_Background", "Class_HardNegative"}
VALID_SPLITS = {"train", "val", "test", "holdout"}
PENDING_MARKERS = {
    "pending_feature_build",
    "pending_features",
    "pending_metadata",
    "pending_chip",
    "pending",
}
NON_FEATURE_COLUMNS = {
    "sample_id",
    "dataset_id",
    "area_id",
    "group_id",
    "chip_id",
    "split",
    "label",
    "label_quality",
    "source_id",
}


class FeatureReadinessError(ValueError):
    """Raised when H3 readiness inputs cannot be loaded."""


def main() -> int:
    args = _parse_args()
    i2_dir = Path(args.i2_dir)
    feature_matrix = Path(args.feature_matrix) if args.feature_matrix else _default_feature_matrix()

    _validate_private_path_not_inside_repo(i2_dir, "I2 directory")
    _validate_private_path_not_inside_repo(feature_matrix, "feature matrix")

    rows_path = i2_dir / I2_ROWS_FILE
    input_errors: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    matrix_rows: list[dict[str, Any]] = []
    feature_columns: list[str] = []

    try:
        rows = _read_jsonl(_require_file(rows_path, "private I2 rows file"))
    except Exception as exc:  # noqa: BLE001 - aggregate reporting
        input_errors["i2_rows"] = str(exc)

    matrix_status = "missing"
    if feature_matrix.is_file():
        try:
            matrix_rows, feature_columns = _read_feature_matrix(feature_matrix)
            matrix_status = "loaded"
        except Exception as exc:  # noqa: BLE001 - aggregate reporting
            matrix_status = "invalid"
            input_errors["feature_matrix"] = str(exc)

    feature_ref_counts = _feature_ref_counts(rows)
    metadata_ref_counts = _metadata_ref_counts(rows)
    pending_feature_ref_count = _pending_ref_count(rows, "features_ref")
    pending_metadata_ref_count = _pending_ref_count(rows, "metadata_ref")
    rows_by_label = _count(rows, "label")
    rows_by_split = _count(rows, "split")
    unknown_label_count = sum(1 for row in rows if str(row.get("label", "")) not in VALID_LABELS)
    unknown_split_count = sum(1 for row in rows if str(row.get("split", "")) not in VALID_SPLITS)

    matrix_summary = _matrix_summary(matrix_rows, feature_columns)
    join_summary = _join_summary(rows, matrix_rows)

    readiness_decision = _readiness_decision(
        input_errors=input_errors,
        rows=rows,
        matrix_status=matrix_status,
        matrix_summary=matrix_summary,
        join_summary=join_summary,
        pending_feature_ref_count=pending_feature_ref_count,
        pending_metadata_ref_count=pending_metadata_ref_count,
        unknown_label_count=unknown_label_count,
        unknown_split_count=unknown_split_count,
    )

    result = {
        "status": "feature_matrix_ready" if readiness_decision == "ready_for_h3_training_design" else "feature_matrix_not_ready",
        "readiness_decision": readiness_decision,
        "i2_rows_loaded": len(rows),
        "expected_i2_rows": EXPECTED_TOTAL_ROWS,
        "rows_by_label": rows_by_label,
        "rows_by_split": rows_by_split,
        "unknown_label_count": unknown_label_count,
        "unknown_split_count": unknown_split_count,
        "feature_ref_counts": feature_ref_counts,
        "metadata_ref_counts": metadata_ref_counts,
        "pending_feature_ref_count": pending_feature_ref_count,
        "pending_metadata_ref_count": pending_metadata_ref_count,
        "feature_matrix_path_checked": str(feature_matrix),
        "feature_matrix_status": matrix_status,
        "feature_matrix_rows": len(matrix_rows),
        "feature_column_count": len(feature_columns),
        "numeric_feature_column_count": matrix_summary["numeric_feature_column_count"],
        "non_numeric_feature_column_count": matrix_summary["non_numeric_feature_column_count"],
        "non_finite_value_count": matrix_summary["non_finite_value_count"],
        "matrix_duplicate_sample_id_count": matrix_summary["duplicate_sample_id_count"],
        "matrix_missing_sample_id_count": matrix_summary["missing_sample_id_count"],
        "join_matched_rows": join_summary["matched_rows"],
        "join_missing_feature_rows": join_summary["missing_feature_rows"],
        "join_extra_feature_rows": join_summary["extra_feature_rows"],
        "input_errors": input_errors,
        "training_started": False,
        "inference_started": False,
        "model_artifact_written": False,
    }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if readiness_decision == "ready_for_h3_training_design" else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether private I2 has usable H3 training features.")
    parser.add_argument("--i2-dir", default=str(DEFAULT_I2_DIR))
    parser.add_argument(
        "--feature-matrix",
        default=None,
        help="Optional private feature matrix path. Supported: CSV or JSONL. Default checks H3_TRAINING training_matrix.private.csv/jsonl.",
    )
    return parser.parse_args()


def _default_feature_matrix() -> Path:
    if DEFAULT_FEATURE_MATRIX_CSV.is_file():
        return DEFAULT_FEATURE_MATRIX_CSV
    return DEFAULT_FEATURE_MATRIX_JSONL


def _readiness_decision(
    *,
    input_errors: dict[str, str],
    rows: list[dict[str, Any]],
    matrix_status: str,
    matrix_summary: dict[str, int],
    join_summary: dict[str, int],
    pending_feature_ref_count: int,
    pending_metadata_ref_count: int,
    unknown_label_count: int,
    unknown_split_count: int,
) -> str:
    if input_errors and "i2_rows" in input_errors:
        return "not_ready_i2_missing_or_invalid"
    if len(rows) != EXPECTED_TOTAL_ROWS:
        return "not_ready_i2_row_count_mismatch"
    if unknown_label_count or unknown_split_count:
        return "not_ready_unknown_labels_or_splits"
    if pending_feature_ref_count or pending_metadata_ref_count:
        return "not_ready_pending_feature_references"
    if matrix_status == "missing":
        return "not_ready_feature_matrix_missing"
    if matrix_status == "invalid":
        return "not_ready_feature_matrix_invalid"
    if matrix_summary["missing_sample_id_count"] or matrix_summary["duplicate_sample_id_count"]:
        return "not_ready_feature_matrix_bad_ids"
    if join_summary["missing_feature_rows"] or join_summary["extra_feature_rows"]:
        return "not_ready_feature_join_incomplete"
    if matrix_summary["numeric_feature_column_count"] == 0:
        return "not_ready_no_numeric_features"
    if matrix_summary["non_finite_value_count"]:
        return "not_ready_non_finite_features"
    return "ready_for_h3_training_design"


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
                raise FeatureReadinessError(f"invalid JSON on line {line_number}: {path}") from exc
            if not isinstance(row, dict):
                raise FeatureReadinessError(f"line {line_number} is not a JSON object: {path}")
            rows.append(row)
    if not rows:
        raise FeatureReadinessError(f"empty JSONL file: {path}")
    return rows


def _read_feature_matrix(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _read_feature_matrix_csv(path)
    if suffix == ".jsonl":
        rows = _read_jsonl(path)
        columns = sorted({key for row in rows for key in row.keys()})
        return rows, _feature_columns(columns)
    raise FeatureReadinessError(f"unsupported feature matrix extension: {suffix}; use .csv or .jsonl")


def _read_feature_matrix_csv(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise FeatureReadinessError("feature matrix CSV has no header")
        for row in reader:
            rows.append(dict(row))
    if not rows:
        raise FeatureReadinessError("feature matrix CSV is empty")
    return rows, _feature_columns(reader.fieldnames or [])


def _feature_columns(columns: list[str]) -> list[str]:
    return [column for column in columns if column not in NON_FEATURE_COLUMNS]


def _matrix_summary(rows: list[dict[str, Any]], feature_columns: list[str]) -> dict[str, int]:
    if not rows:
        return {
            "numeric_feature_column_count": 0,
            "non_numeric_feature_column_count": 0,
            "non_finite_value_count": 0,
            "duplicate_sample_id_count": 0,
            "missing_sample_id_count": 0,
        }

    missing_sample_id_count = sum(1 for row in rows if not str(row.get("sample_id", "")).strip())
    duplicate_sample_id_count = _duplicate_count([str(row.get("sample_id", "")) for row in rows])
    numeric_columns = 0
    non_numeric_columns = 0
    non_finite_values = 0

    for column in feature_columns:
        column_is_numeric = True
        for row in rows:
            value = row.get(column)
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                column_is_numeric = False
                break
            if not math.isfinite(numeric_value):
                non_finite_values += 1
        if column_is_numeric:
            numeric_columns += 1
        else:
            non_numeric_columns += 1

    return {
        "numeric_feature_column_count": numeric_columns,
        "non_numeric_feature_column_count": non_numeric_columns,
        "non_finite_value_count": non_finite_values,
        "duplicate_sample_id_count": duplicate_sample_id_count,
        "missing_sample_id_count": missing_sample_id_count,
    }


def _join_summary(i2_rows: list[dict[str, Any]], matrix_rows: list[dict[str, Any]]) -> dict[str, int]:
    i2_ids = {str(row.get("sample_id", "")) for row in i2_rows if str(row.get("sample_id", ""))}
    matrix_ids = {str(row.get("sample_id", "")) for row in matrix_rows if str(row.get("sample_id", ""))}
    return {
        "matched_rows": len(i2_ids & matrix_ids),
        "missing_feature_rows": len(i2_ids - matrix_ids),
        "extra_feature_rows": len(matrix_ids - i2_ids),
    }


def _feature_ref_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(_ref_family(row.get("features_ref")) for row in rows))


def _metadata_ref_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(_ref_family(row.get("metadata_ref")) for row in rows))


def _pending_ref_count(rows: list[dict[str, Any]], field: str) -> int:
    return sum(1 for row in rows if _is_pending_ref(row.get(field)))


def _ref_family(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "missing"
    if _is_pending_ref(text):
        return "pending"
    if ":" in text:
        return text.split(":", 1)[0]
    if "_" in text:
        return text.split("_", 1)[0]
    return "other"


def _is_pending_ref(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return True
    return any(marker in text for marker in PENDING_MARKERS)


def _count(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field, "missing")) for row in rows).items()))


def _duplicate_count(values: list[str]) -> int:
    counts = Counter(value for value in values if value)
    return sum(count - 1 for count in counts.values() if count > 1)


def _validate_private_path_not_inside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(f"{label} must be outside the repository")


if __name__ == "__main__":
    raise SystemExit(main())
