"""Dry-run or run H3 scientific training outside Git.

Default behavior is dry-run only and writes nothing.

This script reads the private H3 real feature matrix outside the repository,
validates row/split/label/feature readiness, and optionally trains a local
scikit-learn binary classifier when --write is provided.

It does not run H4 inference, create prediction files, call Earth Engine, change
app/API/frontend code, or write private artifacts inside Git.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import pickle
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = Path(r"C:\Dev\New_GEE_PRIVATE")
DEFAULT_H3_DIR = PRIVATE_ROOT / "H3_REAL_FEATURES"
DEFAULT_MATRIX = DEFAULT_H3_DIR / "real_feature_matrix.private.csv"

EXPECTED_ROWS = 868
EXPECTED_ROWS_BY_SOURCE = {"POS-01": 217, "C05": 217, "C06": 217, "C07": 217}
EXPECTED_ROWS_BY_LABEL = {"Class_A": 217, "Class_Background": 217, "Class_HardNegative": 434}
EXPECTED_ROWS_BY_SPLIT = {"train": 608, "val": 88, "test": 88, "holdout": 84}
VALID_SPLITS = ("train", "val", "test", "holdout")
TARGET_POSITIVE_LABEL = "Class_A"
NON_FEATURE_COLUMNS = {"sample_id", "split", "label", "source_id"}


class H3ScientificTrainingError(ValueError):
    """Raised when H3 scientific training cannot proceed safely."""


def main() -> int:
    args = _parse_args()
    matrix_path = Path(args.feature_matrix)
    output_dir = Path(args.output_dir)

    _validate_private_path_not_inside_repo(matrix_path, "feature matrix")
    _validate_private_path_not_inside_repo(output_dir, "output directory")

    rows = _read_matrix(_require_file(matrix_path, "real feature matrix"))
    feature_columns = _feature_columns(rows)
    checks = _build_checks(rows, feature_columns)
    dependency_status = _dependency_status()
    ready = _ready_for_training(checks, dependency_status)

    summary: dict[str, Any] = {
        "status": "dry_run_ready" if ready else "dry_run_checks_failed",
        "mode": "dry_run" if not args.write else "write",
        "training_type": "h3_scientific_real_feature_baseline",
        "feature_set_type": "real_i2_source_context_v1",
        "scientific_training_ready": ready,
        "target_policy": "binary_class_a_vs_other",
        "feature_matrix_path": str(matrix_path),
        "rows_loaded": len(rows),
        "expected_rows": EXPECTED_ROWS,
        "feature_column_count": len(feature_columns),
        "rows_by_source": checks["rows_by_source"],
        "rows_by_label": checks["rows_by_label"],
        "rows_by_split": checks["rows_by_split"],
        "positive_rows_by_split": checks["positive_rows_by_split"],
        "numeric_feature_column_count": checks["numeric_feature_column_count"],
        "non_numeric_feature_column_count": checks["non_numeric_feature_column_count"],
        "non_finite_value_count": checks["non_finite_value_count"],
        "duplicate_sample_id_count": checks["duplicate_sample_id_count"],
        "missing_required_column_count": checks["missing_required_column_count"],
        "unknown_label_count": checks["unknown_label_count"],
        "unknown_split_count": checks["unknown_split_count"],
        "sklearn_available": dependency_status["sklearn_available"],
        "sklearn_error": dependency_status["sklearn_error"],
        "training_started": False,
        "model_artifact_written": False,
        "evaluation_report_written": False,
        "inference_started": False,
    }

    if args.write:
        if not ready:
            raise SystemExit("H3 scientific training refused: dry-run checks did not pass.")
        result = _train_and_evaluate(rows=rows, feature_columns=feature_columns)
        output_dir.mkdir(parents=True, exist_ok=True)
        model_path = output_dir / "h3_scientific_model.private.pkl"
        report_path = output_dir / "h3_scientific_evaluation_report.private.json"
        summary_path = output_dir / "h3_scientific_training_summary.private.json"

        with model_path.open("wb") as handle:
            pickle.dump(result["model"], handle)
        _write_json(report_path, result["report"])

        summary.update(
            {
                "status": "h3_scientific_training_completed",
                "training_started": True,
                "model_artifact_written": True,
                "evaluation_report_written": True,
                "model_artifact_path": str(model_path),
                "evaluation_report_path": str(report_path),
                "train_accuracy": result["report"]["train"]["accuracy"],
                "val_accuracy": result["report"]["val"]["accuracy"],
                "test_accuracy": result["report"]["test"]["accuracy"],
                "holdout_accuracy": result["report"]["holdout"]["accuracy"],
                "inference_started": False,
            }
        )
        _write_json(summary_path, summary)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ready else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run or run H3 scientific training outside Git.")
    parser.add_argument("--feature-matrix", default=str(DEFAULT_MATRIX))
    parser.add_argument("--output-dir", default=str(DEFAULT_H3_DIR))
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def _dependency_status() -> dict[str, Any]:
    try:
        import sklearn  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        return {"sklearn_available": False, "sklearn_error": str(exc)}
    return {"sklearn_available": True, "sklearn_error": None}


def _read_matrix(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise H3ScientificTrainingError("feature matrix has no header")
        rows = [dict(row) for row in reader]
    if not rows:
        raise H3ScientificTrainingError("feature matrix is empty")
    return rows


def _feature_columns(rows: list[dict[str, str]]) -> list[str]:
    return [column for column in rows[0].keys() if column not in NON_FEATURE_COLUMNS]


def _build_checks(rows: list[dict[str, str]], feature_columns: list[str]) -> dict[str, Any]:
    rows_by_source = dict(sorted(Counter(row.get("source_id", "missing") for row in rows).items()))
    rows_by_label = dict(sorted(Counter(row.get("label", "missing") for row in rows).items()))
    rows_by_split = dict(sorted(Counter(row.get("split", "missing") for row in rows).items()))
    positive_rows_by_split = {split: 0 for split in VALID_SPLITS}
    for row in rows:
        if row.get("label") == TARGET_POSITIVE_LABEL and row.get("split") in positive_rows_by_split:
            positive_rows_by_split[row["split"]] += 1

    numeric_feature_column_count = 0
    non_numeric_feature_column_count = 0
    non_finite_value_count = 0
    for column in feature_columns:
        column_numeric = True
        for row in rows:
            try:
                value = float(row[column])
            except (KeyError, TypeError, ValueError):
                column_numeric = False
                break
            if not math.isfinite(value):
                non_finite_value_count += 1
        if column_numeric:
            numeric_feature_column_count += 1
        else:
            non_numeric_feature_column_count += 1

    required_columns = {"sample_id", "split", "label", "source_id", *feature_columns}
    return {
        "row_count_match": len(rows) == EXPECTED_ROWS,
        "source_counts_match": rows_by_source == EXPECTED_ROWS_BY_SOURCE,
        "label_counts_match": rows_by_label == EXPECTED_ROWS_BY_LABEL,
        "split_counts_match": rows_by_split == EXPECTED_ROWS_BY_SPLIT,
        "rows_by_source": rows_by_source,
        "rows_by_label": rows_by_label,
        "rows_by_split": rows_by_split,
        "positive_rows_by_split": positive_rows_by_split,
        "numeric_feature_column_count": numeric_feature_column_count,
        "non_numeric_feature_column_count": non_numeric_feature_column_count,
        "non_finite_value_count": non_finite_value_count,
        "duplicate_sample_id_count": _duplicate_count([row.get("sample_id", "") for row in rows]),
        "missing_required_column_count": sum(1 for column in required_columns if column not in rows[0]),
        "unknown_label_count": sum(1 for row in rows if row.get("label") not in EXPECTED_ROWS_BY_LABEL),
        "unknown_split_count": sum(1 for row in rows if row.get("split") not in VALID_SPLITS),
    }


def _ready_for_training(checks: dict[str, Any], dependency_status: dict[str, Any]) -> bool:
    return (
        checks["row_count_match"]
        and checks["source_counts_match"]
        and checks["label_counts_match"]
        and checks["split_counts_match"]
        and checks["numeric_feature_column_count"] > 0
        and checks["non_numeric_feature_column_count"] == 0
        and checks["non_finite_value_count"] == 0
        and checks["duplicate_sample_id_count"] == 0
        and checks["missing_required_column_count"] == 0
        and checks["unknown_label_count"] == 0
        and checks["unknown_split_count"] == 0
        and dependency_status["sklearn_available"]
    )


def _train_and_evaluate(*, rows: list[dict[str, str]], feature_columns: list[str]) -> dict[str, Any]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    train_rows = [row for row in rows if row["split"] == "train"]
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000, random_state=20260616)),
        ]
    )
    model.fit(_x(train_rows, feature_columns), _y(train_rows))

    report: dict[str, Any] = {
        "model_name": "logistic_regression",
        "target_policy": "binary_class_a_vs_other",
        "feature_set_type": "real_i2_source_context_v1",
        "h4_inference_started": False,
    }
    for split in VALID_SPLITS:
        split_rows = [row for row in rows if row["split"] == split]
        report[split] = _metrics(model=model, rows=split_rows, feature_columns=feature_columns)
    return {"model": model, "report": report}


def _x(rows: list[dict[str, str]], feature_columns: list[str]) -> list[list[float]]:
    return [[float(row[column]) for column in feature_columns] for row in rows]


def _y(rows: list[dict[str, str]]) -> list[int]:
    return [1 if row["label"] == TARGET_POSITIVE_LABEL else 0 for row in rows]


def _metrics(*, model: Any, rows: list[dict[str, str]], feature_columns: list[str]) -> dict[str, Any]:
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

    y_true = _y(rows)
    x_values = _x(rows, feature_columns)
    y_pred = list(model.predict(x_values))
    try:
        y_score = list(model.predict_proba(x_values)[:, 1])
        roc_auc = float(roc_auc_score(y_true, y_score)) if len(set(y_true)) > 1 else None
    except Exception:
        roc_auc = None
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "rows": len(rows),
        "positive_rows": int(sum(y_true)),
        "negative_rows": int(len(y_true) - sum(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": roc_auc,
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }


def _duplicate_count(values: list[str]) -> int:
    counts = Counter(value for value in values if value)
    return sum(count - 1 for count in counts.values() if count > 1)


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
