from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_H4_SUMMARY_PATH = Path(r"C:\Dev\New_GEE_PRIVATE\H4_INFERENCE\h4_prediction_summary.private.json")

FORBIDDEN_RESPONSE_KEYS = {
    "sample_id",
    "predictions_path",
    "feature_matrix_path",
    "model_artifact_path",
    "evaluation_report_path",
    "private_path",
    "raw_file",
    "positive_score",
    "feature_values",
    "features",
    "model_pickle",
}


class H5OperatorSummaryError(ValueError):
    """Raised when H5 aggregate summary cannot be loaded safely."""


def load_h5_operator_aggregate_summary(
    summary_path: Path | str = DEFAULT_H4_SUMMARY_PATH,
) -> dict[str, Any]:
    """Load a private H4 summary and return only redacted aggregate fields.

    This function does not read row-level output files and does not expose local
    private paths. It is intended for a future operator-only route.
    """

    path = Path(summary_path)
    _validate_private_path_not_inside_repo(path, "H4 summary path")
    if not path.is_file():
        raise FileNotFoundError(f"H4 summary does not exist: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise H5OperatorSummaryError("H4 summary JSON must be an object")

    safe_summary = {
        "status": str(payload.get("status", "unknown")),
        "pipeline_stage": "h5_operator_aggregate_summary",
        "feature_set_type": str(payload.get("feature_set_type", "unknown")),
        "training_type": str(payload.get("training_type", "unknown")),
        "total_row_count": _safe_int(payload.get("score_rows_written")),
        "feature_matrix_rows": _safe_int(payload.get("feature_matrix_rows")),
        "feature_column_count": _safe_int(payload.get("feature_column_count")),
        "score_min": _safe_float(payload.get("score_min")),
        "score_max": _safe_float(payload.get("score_max")),
        "score_mean": _safe_float(payload.get("score_mean")),
        "rows_by_source": _safe_count_mapping(payload.get("rows_by_source")),
        "rows_by_split": _safe_count_mapping(payload.get("rows_by_split")),
        "score_band_counts": {},
        "score_band_counts_status": "not_available_from_aggregate_summary",
        "prediction_files_written": bool(payload.get("prediction_files_written", False)),
        "api_frontend_changed": bool(payload.get("api_frontend_changed", False)),
        "overlays_created": bool(payload.get("overlays_created", False)),
        "row_level_output_included": False,
        "private_paths_included": False,
    }
    assert_h5_operator_summary_is_redacted(safe_summary)
    return safe_summary


def assert_h5_operator_summary_is_redacted(payload: Mapping[str, Any]) -> None:
    """Guard future operator responses from leaking private fields."""

    leaked = _find_forbidden_keys(payload)
    if leaked:
        raise H5OperatorSummaryError(f"unsafe H5 operator summary fields: {sorted(leaked)}")


def _find_forbidden_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            if normalized in FORBIDDEN_RESPONSE_KEYS:
                found.add(normalized)
            found.update(_find_forbidden_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_find_forbidden_keys(child))
    return found


def _safe_count_mapping(value: Any) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    safe: dict[str, int] = {}
    for key, count in value.items():
        safe[str(key)] = _safe_int(count)
    return dict(sorted(safe.items()))


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _validate_private_path_not_inside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(f"{label} must be outside the repository")


__all__ = (
    "DEFAULT_H4_SUMMARY_PATH",
    "H5OperatorSummaryError",
    "assert_h5_operator_summary_is_redacted",
    "load_h5_operator_aggregate_summary",
)
