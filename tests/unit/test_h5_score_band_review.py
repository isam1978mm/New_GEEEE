from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.h5_review_score_bands import build_h5_score_band_review


EXPECTED_ROWS = 868


def _write_predictions(path: Path) -> None:
    scores = [0.05, 0.15, 0.35, 0.60, 0.90]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["sample_id", "split", "label", "source_id", "positive_score"],
        )
        writer.writeheader()
        for index in range(EXPECTED_ROWS):
            writer.writerow(
                {
                    "sample_id": f"sample_{index:04d}",
                    "split": "train" if index < 608 else "val",
                    "label": "Class_A" if index % 4 == 0 else "Class_Background",
                    "source_id": ["POS-01", "C05", "C06", "C07"][index % 4],
                    "positive_score": f"{scores[index % len(scores)]:.8f}",
                }
            )


def _write_h4_summary(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "h4_private_offline_inference_completed",
                "score_rows_written": EXPECTED_ROWS,
                "prediction_files_written": True,
            }
        ),
        encoding="utf-8",
    )


def test_score_band_review_is_aggregate_only_and_ready() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        predictions_path = root / "h4_predictions.private.csv"
        h4_summary_path = root / "h4_prediction_summary.private.json"
        _write_predictions(predictions_path)
        _write_h4_summary(h4_summary_path)

        review = build_h5_score_band_review(
            predictions_path=predictions_path,
            h4_summary_path=h4_summary_path,
        )

    assert review["status"] == "dry_run_ready"
    assert review["score_rows_loaded"] == EXPECTED_ROWS
    assert sum(review["score_band_counts"].values()) == EXPECTED_ROWS
    assert review["score_band_counts"] == {
        "score_0_00_to_0_10": 174,
        "score_0_10_to_0_25": 174,
        "score_0_25_to_0_50": 174,
        "score_0_50_to_0_75": 173,
        "score_0_75_to_1_00": 173,
    }
    assert review["row_level_output_included"] is False
    assert review["private_paths_included"] is False
    assert review["raw_prediction_file_served"] is False
    assert review["api_frontend_changed"] is False
    assert review["overlays_created"] is False

    text = json.dumps(review, sort_keys=True)
    assert "sample_" not in text
    assert "sample_id" not in text
    assert "positive_score" not in text
    assert "h4_predictions.private.csv" not in text


def test_score_band_review_refuses_out_of_range_scores() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        predictions_path = root / "h4_predictions.private.csv"
        h4_summary_path = root / "h4_prediction_summary.private.json"
        _write_predictions(predictions_path)
        _write_h4_summary(h4_summary_path)

        rows = predictions_path.read_text(encoding="utf-8").splitlines()
        rows[1] = rows[1].rsplit(",", maxsplit=1)[0] + ",1.50000000"
        predictions_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

        review = build_h5_score_band_review(
            predictions_path=predictions_path,
            h4_summary_path=h4_summary_path,
        )

    assert review["status"] == "dry_run_checks_failed"
    assert review["out_of_range_score_count"] == 1
    assert review["review_written"] is False
