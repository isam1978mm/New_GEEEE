"""Build an aggregate-only H5 score-band review outside Git.

Default behavior is dry-run only and writes nothing.

Write mode requires --write and writes only aggregate JSON outside the repo. The
script reads private H4 prediction rows locally, but it never writes row-level
scores, sample IDs, private paths, raw CSV content, map overlays, API changes,
or frontend changes.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = Path(r"C:\Dev\New_GEE_PRIVATE")
DEFAULT_H4_DIR = PRIVATE_ROOT / "H4_INFERENCE"
DEFAULT_PREDICTIONS = DEFAULT_H4_DIR / "h4_predictions.private.csv"
DEFAULT_H4_SUMMARY = DEFAULT_H4_DIR / "h4_prediction_summary.private.json"
DEFAULT_OUTPUT_DIR = PRIVATE_ROOT / "H5_AGGREGATE_REVIEW"
DEFAULT_OUTPUT_SUMMARY = DEFAULT_OUTPUT_DIR / "h5_score_band_summary.private.json"
DEFAULT_OUTPUT_LINEAGE = DEFAULT_OUTPUT_DIR / "h5_score_band_lineage.private.json"

EXPECTED_SCORE_ROWS = 868
EXPECTED_SCORE_MIN = 0.0
EXPECTED_SCORE_MAX = 1.0
SCORE_COLUMN = "positive_score"
REQUIRED_COLUMNS = {"sample_id", "split", "label", "source_id", SCORE_COLUMN}
BANDS: tuple[tuple[str, float, float, bool], ...] = (
    ("score_0_00_to_0_10", 0.00, 0.10, False),
    ("score_0_10_to_0_25", 0.10, 0.25, False),
    ("score_0_25_to_0_50", 0.25, 0.50, False),
    ("score_0_50_to_0_75", 0.50, 0.75, False),
    ("score_0_75_to_1_00", 0.75, 1.00, True),
)


class H5ScoreBandReviewError(ValueError):
    """Raised when score-band review inputs are not safe or ready."""


def main() -> int:
    args = _parse_args()
    predictions_path = Path(args.predictions)
    h4_summary_path = Path(args.h4_summary)
    output_summary_path = Path(args.output_summary)
    output_lineage_path = Path(args.output_lineage)

    for label, path in (
        ("predictions", predictions_path),
        ("H4 summary", h4_summary_path),
        ("output summary", output_summary_path),
        ("output lineage", output_lineage_path),
    ):
        _validate_private_path_not_inside_repo(path, label)

    review = build_h5_score_band_review(
        predictions_path=predictions_path,
        h4_summary_path=h4_summary_path,
        write=args.write,
    )

    if args.write:
        if review["status"] != "h5_score_band_review_ready_to_write":
            raise SystemExit("H5 score-band write refused: dry-run checks did not pass.")
        review = dict(review)
        review.update(
            {
                "status": "h5_score_band_review_written",
                "mode": "write",
                "review_written": True,
            }
        )
        output_summary_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(output_summary_path, review)
        _write_json(
            output_lineage_path,
            {
                "source_stage": "h4_private_offline_inference",
                "review_stage": "h5_score_band_aggregate_review",
                "score_rows_loaded": review["score_rows_loaded"],
                "score_band_counts_status": review["score_band_counts_status"],
                "row_level_output_included": False,
                "private_paths_included": False,
                "api_frontend_changed": False,
                "overlays_created": False,
            },
        )

    print(json.dumps(review, indent=2, sort_keys=True))
    return 0 if not review["input_errors"] else 1


def build_h5_score_band_review(
    *,
    predictions_path: Path,
    h4_summary_path: Path,
    write: bool = False,
) -> dict[str, Any]:
    input_errors: dict[str, str] = {}
    rows: list[dict[str, str]] = []
    h4_summary: dict[str, Any] = {}

    try:
        rows = _read_prediction_rows(_require_file(predictions_path, "predictions"))
    except Exception as exc:  # noqa: BLE001
        input_errors["predictions"] = str(exc)
    try:
        h4_summary = _read_json(_require_file(h4_summary_path, "H4 summary"))
    except Exception as exc:  # noqa: BLE001
        input_errors["h4_summary"] = str(exc)

    scores = _score_values(rows)
    non_finite_score_count = sum(1 for score in scores if not math.isfinite(score))
    out_of_range_score_count = sum(
        1 for score in scores if score < EXPECTED_SCORE_MIN or score > EXPECTED_SCORE_MAX
    )
    duplicate_private_id_count = _duplicate_count([row.get("sample_id", "") for row in rows])
    score_band_counts = _score_band_counts(scores)
    rows_by_source = _count(rows, "source_id")
    rows_by_split = _count(rows, "split")

    h4_score_rows = _safe_int(h4_summary.get("score_rows_written"))
    h4_prediction_files_written = bool(h4_summary.get("prediction_files_written", False))
    ready = (
        not input_errors
        and len(rows) == EXPECTED_SCORE_ROWS
        and h4_score_rows == EXPECTED_SCORE_ROWS
        and h4_prediction_files_written is True
        and duplicate_private_id_count == 0
        and non_finite_score_count == 0
        and out_of_range_score_count == 0
        and sum(score_band_counts.values()) == len(rows)
    )

    return {
        "status": _status(write=write, ready=ready),
        "mode": "write" if write else "dry_run",
        "source_stage": "h4_private_offline_inference",
        "review_stage": "h5_score_band_aggregate_review",
        "expected_score_rows": EXPECTED_SCORE_ROWS,
        "score_rows_loaded": len(rows),
        "h4_score_rows_written": h4_score_rows,
        "score_min": min(scores) if scores else None,
        "score_max": max(scores) if scores else None,
        "score_mean": sum(scores) / len(scores) if scores else None,
        "score_band_edges": _score_band_edges(),
        "score_band_counts": score_band_counts,
        "score_band_counts_status": "available_from_private_aggregate_review" if ready else "not_ready",
        "rows_by_source": rows_by_source,
        "rows_by_split": rows_by_split,
        "duplicate_private_id_count": duplicate_private_id_count,
        "non_finite_score_count": non_finite_score_count,
        "out_of_range_score_count": out_of_range_score_count,
        "input_errors": input_errors,
        "review_written": False,
        "row_level_output_included": False,
        "private_paths_included": False,
        "raw_prediction_file_served": False,
        "api_frontend_changed": False,
        "overlays_created": False,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build H5 aggregate score-band review outside Git.")
    parser.add_argument("--predictions", default=str(DEFAULT_PREDICTIONS))
    parser.add_argument("--h4-summary", default=str(DEFAULT_H4_SUMMARY))
    parser.add_argument("--output-summary", default=str(DEFAULT_OUTPUT_SUMMARY))
    parser.add_argument("--output-lineage", default=str(DEFAULT_OUTPUT_LINEAGE))
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def _read_prediction_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise H5ScoreBandReviewError("prediction CSV has no header")
        missing_columns = sorted(REQUIRED_COLUMNS - set(reader.fieldnames))
        if missing_columns:
            raise H5ScoreBandReviewError(f"prediction CSV missing required columns: {missing_columns}")
        rows = [dict(row) for row in reader]
    if not rows:
        raise H5ScoreBandReviewError("prediction CSV is empty")
    return rows


def _score_values(rows: list[dict[str, str]]) -> list[float]:
    scores: list[float] = []
    for index, row in enumerate(rows, start=1):
        try:
            scores.append(float(row[SCORE_COLUMN]))
        except (KeyError, TypeError, ValueError) as exc:
            raise H5ScoreBandReviewError(f"invalid score at row {index}") from exc
    return scores


def _score_band_counts(scores: list[float]) -> dict[str, int]:
    counts = {label: 0 for label, _low, _high, _inclusive_high in BANDS}
    for score in scores:
        for label, low, high, inclusive_high in BANDS:
            if score >= low and (score <= high if inclusive_high else score < high):
                counts[label] += 1
                break
    return counts


def _score_band_edges() -> list[dict[str, object]]:
    return [
        {
            "label": label,
            "lower": low,
            "upper": high,
            "upper_inclusive": inclusive_high,
        }
        for label, low, high, inclusive_high in BANDS
    ]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise H5ScoreBandReviewError(f"JSON payload is not an object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
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


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _validate_private_path_not_inside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(f"{label} must be outside the repository")


def _status(*, write: bool, ready: bool) -> str:
    if write and ready:
        return "h5_score_band_review_ready_to_write"
    if write:
        return "write_refused"
    return "dry_run_ready" if ready else "dry_run_checks_failed"


if __name__ == "__main__":
    raise SystemExit(main())
