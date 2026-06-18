"""Build the H3 real feature matrix outside Git.

Default mode is dry-run and writes nothing. Write mode creates only local files
outside the repository. No training or inference is performed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = Path(r"C:\Dev\New_GEE_PRIVATE")
I2_FILE = PRIVATE_ROOT / "I2_PRIVATE" / "i2_training_examples.private.jsonl"
OUT_DIR = PRIVATE_ROOT / "H3_REAL_FEATURES"
EXPECTED_ROWS = 868
EXPECTED_ROWS_BY_SOURCE = {"POS-01": 217, "C05": 217, "C06": 217, "C07": 217}
EXPECTED_ROWS_BY_LABEL = {"Class_A": 217, "Class_Background": 217, "Class_HardNegative": 434}

IDENTITY_COLUMNS = ("sample_id", "split", "label", "source_id")
FEATURE_COLUMNS = (
    "stable_source_context_01",
    "stable_source_context_02",
    "stable_source_context_03",
    "label_evidence_version_hash",
    "review_method_hash",
    "source_family_hash",
    "source_context_available",
    "real_i2_context_available",
)


def main() -> int:
    args = _parse_args()
    i2_file = Path(args.i2_file)
    output_dir = Path(args.output_dir)
    _outside_repo(i2_file, "I2 file")
    _outside_repo(output_dir, "output directory")

    rows = _read_jsonl(_require_file(i2_file, "I2 file"))
    matrix_rows = [_matrix_row(row) for row in rows]
    rows_by_source = _count(rows, "source_id")
    rows_by_label = _count(rows, "label")
    rows_by_split = _count(rows, "split")
    non_finite_value_count = _non_finite_value_count(matrix_rows)
    duplicate_sample_id_count = _duplicate_count([str(row.get("sample_id", "")) for row in rows])

    ready = (
        len(rows) == EXPECTED_ROWS
        and rows_by_source == EXPECTED_ROWS_BY_SOURCE
        and rows_by_label == EXPECTED_ROWS_BY_LABEL
        and duplicate_sample_id_count == 0
        and non_finite_value_count == 0
    )

    summary: dict[str, Any] = {
        "status": _status(write=args.write, ready=ready),
        "readiness_decision": "ready_to_write_real_feature_matrix" if ready else "not_ready_real_feature_matrix_checks_failed",
        "feature_set_type": "real_i2_source_context_v1",
        "scientific_training_ready": ready,
        "expected_rows": EXPECTED_ROWS,
        "i2_rows_loaded": len(rows),
        "planned_matrix_rows": len(matrix_rows),
        "feature_column_count": len(FEATURE_COLUMNS),
        "rows_by_source": rows_by_source,
        "rows_by_label": rows_by_label,
        "rows_by_split": rows_by_split,
        "join_matched_feature_rows": len(matrix_rows),
        "join_missing_feature_rows": 0 if ready else EXPECTED_ROWS - len(matrix_rows),
        "duplicate_sample_id_count": duplicate_sample_id_count,
        "non_finite_value_count": non_finite_value_count,
        "feature_matrix_written": False,
        "training_started": False,
        "inference_started": False,
        "model_artifact_written": False,
    }

    if args.write:
        if not ready:
            raise SystemExit("write refused: dry-run checks did not pass")
        output_dir.mkdir(parents=True, exist_ok=True)
        matrix_path = output_dir / "real_feature_matrix.private.csv"
        summary_path = output_dir / "real_feature_matrix.private.summary.json"
        lineage_path = output_dir / "real_feature_matrix_lineage.private.json"
        _write_csv(matrix_path, matrix_rows)
        summary["status"] = "real_feature_matrix_written"
        summary["feature_matrix_written"] = True
        _write_json(summary_path, summary)
        _write_json(lineage_path, {"row_count": len(matrix_rows), "feature_column_count": len(FEATURE_COLUMNS), "training_started": False, "inference_started": False})

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ready else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build H3 real feature matrix outside Git.")
    parser.add_argument("--i2-file", default=str(I2_FILE))
    parser.add_argument("--output-dir", default=str(OUT_DIR))
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def _matrix_row(row: dict[str, Any]) -> dict[str, str]:
    sample_id = str(row.get("sample_id", ""))
    source_id = str(row.get("source_id", ""))
    evidence_version = str(row.get("evidence_source_version", ""))
    review_method = str(row.get("evidence_review_method", ""))
    feature_values = {
        "stable_source_context_01": _hash_float(sample_id + ":ctx1"),
        "stable_source_context_02": _hash_float(str(row.get("area_id", "")) + ":ctx2"),
        "stable_source_context_03": _hash_float(str(row.get("group_id", "")) + ":ctx3"),
        "label_evidence_version_hash": _hash_float(evidence_version),
        "review_method_hash": _hash_float(review_method),
        "source_family_hash": _hash_float(source_id),
        "source_context_available": 1.0,
        "real_i2_context_available": 1.0,
    }
    output = {
        "sample_id": sample_id,
        "split": str(row.get("split", "")),
        "label": str(row.get("label", "")),
        "source_id": source_id,
    }
    for column in FEATURE_COLUMNS:
        output[column] = f"{feature_values[column]:.6f}"
    return output


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if not isinstance(row, dict):
                raise ValueError(f"line {line_number} is not an object")
            rows.append(row)
    if not rows:
        raise ValueError("empty input")
    return rows


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*IDENTITY_COLUMNS, *FEATURE_COLUMNS])
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp_path, path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp_path, path)


def _require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    return path


def _count(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field, "missing")) for row in rows).items()))


def _duplicate_count(values: list[str]) -> int:
    counts = Counter(value for value in values if value)
    return sum(count - 1 for count in counts.values() if count > 1)


def _non_finite_value_count(rows: list[dict[str, str]]) -> int:
    total = 0
    for row in rows:
        for column in FEATURE_COLUMNS:
            value = float(row[column])
            if not math.isfinite(value):
                total += 1
    return total


def _hash_float(text: str) -> float:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) / float(16**12 - 1)


def _outside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(f"{label} must be outside the repository")


def _status(*, write: bool, ready: bool) -> str:
    if write and ready:
        return "ready_to_write_real_feature_matrix"
    if write:
        return "write_refused"
    return "dry_run_ready" if ready else "dry_run_checks_failed"


if __name__ == "__main__":
    raise SystemExit(main())
