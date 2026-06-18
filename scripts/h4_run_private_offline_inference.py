"""Dry-run or run private H4 offline inference outside Git.

Default behavior is dry-run only and writes nothing.

Write mode requires --write and writes private outputs only outside the repo.
This script does not call Earth Engine, change API/frontend code, create map
overlays, or serve model outputs.
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
H3_DIR = PRIVATE_ROOT / "H3_REAL_FEATURES"
DEFAULT_MATRIX = H3_DIR / "real_feature_matrix.private.csv"
DEFAULT_MATRIX_SUMMARY = H3_DIR / "real_feature_matrix.private.summary.json"
DEFAULT_MODEL = H3_DIR / "h3_scientific_model.private.pkl"
DEFAULT_TRAINING_SUMMARY = H3_DIR / "h3_scientific_training_summary.private.json"
DEFAULT_OUTPUT_DIR = PRIVATE_ROOT / "H4_INFERENCE"

EXPECTED_ROWS = 868
EXPECTED_FEATURE_COLUMNS = 8
EXPECTED_FEATURE_SET_TYPE = "real_i2_source_context_v1"
EXPECTED_TRAINING_TYPE = "h3_scientific_real_feature_baseline"
EXPECTED_ROWS_BY_SOURCE = {"POS-01": 217, "C05": 217, "C06": 217, "C07": 217}
EXPECTED_ROWS_BY_LABEL = {"Class_A": 217, "Class_Background": 217, "Class_HardNegative": 434}
EXPECTED_ROWS_BY_SPLIT = {"train": 608, "val": 88, "test": 88, "holdout": 84}
IDENTITY_COLUMNS = {"sample_id", "split", "label", "source_id"}


class H4InputError(ValueError):
    """Raised when private H4 inference inputs are not safe or ready."""


def main() -> int:
    args = _parse_args()
    matrix_path = Path(args.feature_matrix)
    matrix_summary_path = Path(args.feature_matrix_summary)
    model_path = Path(args.model_artifact)
    training_summary_path = Path(args.training_summary)
    output_dir = Path(args.output_dir)

    for label, path in (
        ("feature matrix", matrix_path),
        ("feature matrix summary", matrix_summary_path),
        ("model artifact", model_path),
        ("training summary", training_summary_path),
        ("output directory", output_dir),
    ):
        _validate_private_path_not_inside_repo(path, label)

    input_errors: dict[str, str] = {}
    rows: list[dict[str, str]] = []
    matrix_summary: dict[str, Any] = {}
    training_summary: dict[str, Any] = {}

    try:
        rows = _read_matrix(_require_file(matrix_path, "feature matrix"))
    except Exception as exc:  # noqa: BLE001
        input_errors["feature_matrix"] = str(exc)
    try:
        matrix_summary = _read_json(_require_file(matrix_summary_path, "feature matrix summary"))
    except Exception as exc:  # noqa: BLE001
        input_errors["feature_matrix_summary"] = str(exc)
    try:
        _require_file(model_path, "model artifact")
    except Exception as exc:  # noqa: BLE001
        input_errors["model_artifact"] = str(exc)
    try:
        training_summary = _read_json(_require_file(training_summary_path, "training summary"))
    except Exception as exc:  # noqa: BLE001
        input_errors["training_summary"] = str(exc)

    feature_columns = _feature_columns(rows) if rows else []
    rows_by_source = _count(rows, "source_id")
    rows_by_label = _count(rows, "label")
    rows_by_split = _count(rows, "split")
    duplicate_sample_id_count = _duplicate_count([row.get("sample_id", "") for row in rows])
    non_numeric_feature_column_count, non_finite_value_count = _feature_value_errors(rows, feature_columns)

    contract_ready = (
        not input_errors
        and len(rows) == EXPECTED_ROWS
        and len(feature_columns) == EXPECTED_FEATURE_COLUMNS
        and rows_by_source == EXPECTED_ROWS_BY_SOURCE
        and rows_by_label == EXPECTED_ROWS_BY_LABEL
        and rows_by_split == EXPECTED_ROWS_BY_SPLIT
        and duplicate_sample_id_count == 0
        and non_numeric_feature_column_count == 0
        and non_finite_value_count == 0
        and matrix_summary.get("feature_set_type") == EXPECTED_FEATURE_SET_TYPE
        and matrix_summary.get("feature_matrix_written") is True
        and training_summary.get("training_type") == EXPECTED_TRAINING_TYPE
        and training_summary.get("feature_set_type") == EXPECTED_FEATURE_SET_TYPE
        and training_summary.get("model_artifact_written") is True
        and training_summary.get("inference_started") is False
    )

    summary: dict[str, Any] = {
        "status": _status(write=args.write, ready=contract_ready),
        "mode": "write" if args.write else "dry_run",
        "feature_set_type": EXPECTED_FEATURE_SET_TYPE,
        "training_type": EXPECTED_TRAINING_TYPE,
        "feature_matrix_rows": len(rows),
        "expected_rows": EXPECTED_ROWS,
        "feature_column_count": len(feature_columns),
        "expected_feature_column_count": EXPECTED_FEATURE_COLUMNS,
        "planned_score_rows": len(rows) if contract_ready else 0,
        "score_rows_written": 0,
        "rows_by_source": rows_by_source,
        "rows_by_label": rows_by_label,
        "rows_by_split": rows_by_split,
        "duplicate_sample_id_count": duplicate_sample_id_count,
        "non_numeric_feature_column_count": non_numeric_feature_column_count,
        "non_finite_value_count": non_finite_value_count,
        "model_artifact_present": model_path.is_file(),
        "training_summary_present": training_summary_path.is_file(),
        "matrix_summary_present": matrix_summary_path.is_file(),
        "input_errors": input_errors,
        "inference_started": False,
        "prediction_files_written": False,
        "api_frontend_changed": False,
        "overlays_created": False,
    }

    if args.write:
        if not contract_ready:
            raise SystemExit("H4 inference write refused: dry-run checks did not pass.")
        score_rows = _score_rows(model_path=model_path, rows=rows, feature_columns=feature_columns)
        output_dir.mkdir(parents=True, exist_ok=True)
        predictions_path = output_dir / "h4_predictions.private.csv"
        summary_path = output_dir / "h4_prediction_summary.private.json"
        lineage_path = output_dir / "h4_prediction_lineage.private.json"
        _write_csv(predictions_path, score_rows)
        score_values = [float(row["positive_score"]) for row in score_rows]
        summary.update(
            {
                "status": "h4_private_offline_inference_completed",
                "score_rows_written": len(score_rows),
                "score_min": min(score_values) if score_values else None,
                "score_max": max(score_values) if score_values else None,
                "score_mean": sum(score_values) / len(score_values) if score_values else None,
                "inference_started": True,
                "prediction_files_written": True,
                "predictions_path": str(predictions_path),
            }
        )
        _write_json(summary_path, summary)
        _write_json(
            lineage_path,
            {
                "feature_set_type": EXPECTED_FEATURE_SET_TYPE,
                "training_type": EXPECTED_TRAINING_TYPE,
                "score_rows_written": len(score_rows),
                "api_frontend_changed": False,
                "overlays_created": False,
            },
        )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if contract_ready else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run or run private H4 offline inference outside Git.")
    parser.add_argument("--feature-matrix", default=str(DEFAULT_MATRIX))
    parser.add_argument("--feature-matrix-summary", default=str(DEFAULT_MATRIX_SUMMARY))
    parser.add_argument("--model-artifact", default=str(DEFAULT_MODEL))
    parser.add_argument("--training-summary", default=str(DEFAULT_TRAINING_SUMMARY))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def _read_matrix(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise H4InputError("feature matrix has no header")
        rows = [dict(row) for row in reader]
    if not rows:
        raise H4InputError("feature matrix is empty")
    return rows


def _score_rows(*, model_path: Path, rows: list[dict[str, str]], feature_columns: list[str]) -> list[dict[str, str]]:
    with model_path.open("rb") as handle:
        model = pickle.load(handle)
    x_values = [[float(row[column]) for column in feature_columns] for row in rows]
    try:
        scores = list(model.predict_proba(x_values)[:, 1])
    except Exception:
        scores = [float(value) for value in model.predict(x_values)]
    scored: list[dict[str, str]] = []
    for row, score in zip(rows, scores, strict=True):
        scored.append(
            {
                "sample_id": row["sample_id"],
                "split": row["split"],
                "label": row["label"],
                "source_id": row["source_id"],
                "positive_score": f"{float(score):.8f}",
            }
        )
    return scored


def _feature_columns(rows: list[dict[str, str]]) -> list[str]:
    return [column for column in rows[0].keys() if column not in IDENTITY_COLUMNS]


def _feature_value_errors(rows: list[dict[str, str]], feature_columns: list[str]) -> tuple[int, int]:
    non_numeric_columns = 0
    non_finite_values = 0
    for column in feature_columns:
        numeric = True
        for row in rows:
            try:
                value = float(row[column])
            except (KeyError, TypeError, ValueError):
                numeric = False
                break
            if not math.isfinite(value):
                non_finite_values += 1
        if not numeric:
            non_numeric_columns += 1
    return non_numeric_columns, non_finite_values


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise H4InputError(f"JSON payload is not an object: {path}")
    return payload


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample_id", "split", "label", "source_id", "positive_score"])
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
    return path


def _count(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field, "missing") for row in rows).items()))


def _duplicate_count(values: list[str]) -> int:
    counts = Counter(value for value in values if value)
    return sum(count - 1 for count in counts.values() if count > 1)


def _validate_private_path_not_inside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(f"{label} must be outside the repository")


def _status(*, write: bool, ready: bool) -> str:
    if write and ready:
        return "ready_to_write_h4_private_offline_inference"
    if write:
        return "write_refused"
    return "dry_run_ready" if ready else "dry_run_checks_failed"


if __name__ == "__main__":
    raise SystemExit(main())
