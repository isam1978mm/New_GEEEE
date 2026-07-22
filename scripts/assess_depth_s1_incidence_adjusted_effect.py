"""Offline incidence-adjusted TAMUCC Sentinel-1 effect assessment.

For each radar feature, fit the pre-period relationship between the per-image
site-minus-background feature median and the corresponding incidence-angle
difference. Compare pre and post residual distributions after removing that
baseline relationship.

This is a descriptive nuisance-adjustment screen only. It performs no network
access, hypothesis testing, causal inference, target classification, or depth
estimation. Detailed numeric values are written only to a private output outside
the repository.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from statistics import median
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA = "depth_s1_matched_feature_extract_v2"
OUTPUT_SCHEMA = "depth_s1_incidence_adjusted_effect_v1"
INCIDENCE_KEY = "incidence_deg_median"
RADAR_FEATURES = (
    "vv_db",
    "vh_db",
    "vv_minus_vh_db",
    "vh_to_vv_linear_ratio",
)


class DepthS1IncidenceAdjustmentError(ValueError):
    """Raised when the private incidence-adjusted assessment cannot proceed."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise DepthS1IncidenceAdjustmentError(f"{label} must remain outside the repository")


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DepthS1IncidenceAdjustmentError(f"{label} is unreadable or invalid JSON") from exc


def _finite_float(value: Any, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise DepthS1IncidenceAdjustmentError(f"{label} is missing or not numeric") from exc
    if not math.isfinite(numeric):
        raise DepthS1IncidenceAdjustmentError(f"{label} is not finite")
    return numeric


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        raise DepthS1IncidenceAdjustmentError("cannot summarize an empty value set")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _iqr(values: list[float]) -> float:
    return _quantile(values, 0.75) - _quantile(values, 0.25)


def _direction(value: float, reference_scale: float) -> str:
    tolerance = max(1e-12, abs(reference_scale) * 1e-12)
    if value > tolerance:
        return "increase"
    if value < -tolerance:
        return "decrease"
    return "no_material_numeric_change"


def _magnitude_bucket(shift: float, pooled_iqr: float) -> tuple[str, float | None]:
    if pooled_iqr <= 0.0:
        if abs(shift) <= 1e-12:
            return "zero_shift_zero_iqr", None
        return "nonzero_shift_zero_iqr", None
    normalized = shift / pooled_iqr
    absolute = abs(normalized)
    if absolute < 0.25:
        bucket = "under_0_25_iqr"
    elif absolute < 0.5:
        bucket = "0_25_to_0_5_iqr"
    elif absolute < 1.0:
        bucket = "0_5_to_1_iqr"
    else:
        bucket = "at_least_1_iqr"
    return bucket, normalized


def _overlap_bucket(fraction: float) -> str:
    if fraction >= 1.0:
        return "all_post_within_pre_range"
    if fraction >= 0.75:
        return "at_least_75_percent_within_pre_range"
    if fraction >= 0.5:
        return "at_least_50_percent_within_pre_range"
    return "under_50_percent_within_pre_range"


def _fit_pre_linear(x: list[float], y: list[float]) -> tuple[float, float]:
    if len(x) != len(y) or len(x) < 3:
        raise DepthS1IncidenceAdjustmentError("pre-period linear adjustment requires at least three rows")
    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)
    denominator = sum((value - x_mean) ** 2 for value in x)
    if denominator <= 1e-18:
        raise DepthS1IncidenceAdjustmentError("pre-period incidence values have no usable variation")
    slope = sum(
        (x_value - x_mean) * (y_value - y_mean)
        for x_value, y_value in zip(x, y, strict=True)
    ) / denominator
    intercept = y_mean - slope * x_mean
    return intercept, slope


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        raise DepthS1IncidenceAdjustmentError("private incidence-adjusted output could not be written") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def _load_rows(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    _require_outside_repo(path, "private matched feature input")
    if not path.is_file():
        raise DepthS1IncidenceAdjustmentError("private matched feature input is missing")

    payload = _read_json(path, "private matched feature input")
    if not isinstance(payload, dict):
        raise DepthS1IncidenceAdjustmentError("private matched feature input must be a JSON object")
    if payload.get("schema_version") != INPUT_SCHEMA:
        raise DepthS1IncidenceAdjustmentError("private matched feature input schema is unsupported")
    if payload.get("status") != "matched_s1_feature_extraction_complete":
        raise DepthS1IncidenceAdjustmentError("private matched feature input is not complete")
    if payload.get("coordinates_included") is True or payload.get("geometry_included") is True:
        raise DepthS1IncidenceAdjustmentError("private matched feature input must not embed coordinates or geometry")

    raw_rows = payload.get("rows")
    if not isinstance(raw_rows, list):
        raise DepthS1IncidenceAdjustmentError("private matched feature input rows are invalid")

    rows: list[dict[str, Any]] = []
    excluded_count = 0
    for item in raw_rows:
        if not isinstance(item, dict):
            raise DepthS1IncidenceAdjustmentError("private matched feature input contains an invalid row")
        if item.get("analysis_included") is not True:
            excluded_count += 1
            continue
        period = str(item.get("period") or "")
        if period not in {"pre", "post"}:
            raise DepthS1IncidenceAdjustmentError("included row has an unsupported period")
        deltas = item.get("site_minus_background")
        if not isinstance(deltas, dict):
            raise DepthS1IncidenceAdjustmentError("included row has invalid site-minus-background values")

        normalized: dict[str, Any] = {
            "period": period,
            "incidence": _finite_float(deltas.get(INCIDENCE_KEY), INCIDENCE_KEY),
            "radar": {},
        }
        for feature in RADAR_FEATURES:
            key = f"{feature}_median"
            normalized["radar"][feature] = _finite_float(deltas.get(key), key)
        rows.append(normalized)

    pre_count = sum(row["period"] == "pre" for row in rows)
    post_count = sum(row["period"] == "post" for row in rows)
    if pre_count < 3 or post_count < 2:
        raise DepthS1IncidenceAdjustmentError(
            "incidence-adjusted assessment requires at least three pre rows and two post rows"
        )
    return payload, rows, excluded_count


def _assess_feature(rows: list[dict[str, Any]], feature: str) -> dict[str, Any]:
    pre_rows = [row for row in rows if row["period"] == "pre"]
    post_rows = [row for row in rows if row["period"] == "post"]

    pre_x = [row["incidence"] for row in pre_rows]
    post_x = [row["incidence"] for row in post_rows]
    pre_y = [row["radar"][feature] for row in pre_rows]
    post_y = [row["radar"][feature] for row in post_rows]

    intercept, slope = _fit_pre_linear(pre_x, pre_y)
    pre_residuals = [
        y_value - (intercept + slope * x_value)
        for x_value, y_value in zip(pre_x, pre_y, strict=True)
    ]
    post_residuals = [
        y_value - (intercept + slope * x_value)
        for x_value, y_value in zip(post_x, post_y, strict=True)
    ]

    unadjusted_shift = median(post_y) - median(pre_y)
    adjusted_shift = median(post_residuals) - median(pre_residuals)

    pre_residual_iqr = _iqr(pre_residuals)
    post_residual_iqr = _iqr(post_residuals)
    pooled_residual_iqr = median([pre_residual_iqr, post_residual_iqr])
    magnitude_bucket, normalized_shift = _magnitude_bucket(
        adjusted_shift,
        pooled_residual_iqr,
    )

    unadjusted_direction = _direction(
        unadjusted_shift,
        max(abs(median(pre_y)), abs(median(post_y)), _iqr(pre_y), _iqr(post_y)),
    )
    adjusted_direction = _direction(
        adjusted_shift,
        max(
            abs(median(pre_residuals)),
            abs(median(post_residuals)),
            pooled_residual_iqr,
        ),
    )

    pre_min = min(pre_x)
    pre_max = max(pre_x)
    within_count = sum(pre_min <= value <= pre_max for value in post_x)
    overlap_fraction = within_count / len(post_x)

    return {
        "feature": feature,
        "pre_model": {
            "intercept": intercept,
            "incidence_slope": slope,
            "pre_incidence_min": pre_min,
            "pre_incidence_max": pre_max,
        },
        "incidence_overlap": {
            "post_count": len(post_x),
            "post_within_pre_range_count": within_count,
            "post_within_pre_range_fraction": overlap_fraction,
            "bucket": _overlap_bucket(overlap_fraction),
        },
        "unadjusted": {
            "pre_median": median(pre_y),
            "post_median": median(post_y),
            "post_minus_pre_median_shift": unadjusted_shift,
            "direction": unadjusted_direction,
        },
        "adjusted": {
            "pre_residual_median": median(pre_residuals),
            "post_residual_median": median(post_residuals),
            "post_minus_pre_residual_median_shift": adjusted_shift,
            "pre_residual_iqr": pre_residual_iqr,
            "post_residual_iqr": post_residual_iqr,
            "pooled_residual_iqr": pooled_residual_iqr,
            "normalized_shift_iqr_units": normalized_shift,
            "direction": adjusted_direction,
            "magnitude_bucket": magnitude_bucket,
        },
        "direction_changed_after_adjustment": unadjusted_direction != adjusted_direction,
    }


def run_incidence_adjusted_assessment(
    *,
    input_path: Path,
    output_path: Path | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    source, rows, excluded_count = _load_rows(input_path)
    if output_path is not None:
        _require_outside_repo(output_path, "private incidence-adjusted output")
    if execute and output_path is None:
        raise DepthS1IncidenceAdjustmentError("execute requires a private output path outside the repository")

    pre_count = sum(row["period"] == "pre" for row in rows)
    post_count = sum(row["period"] == "post" for row in rows)
    feature_results = [_assess_feature(rows, feature) for feature in RADAR_FEATURES]

    feature_screen = {
        item["feature"]: {
            "unadjusted_direction": item["unadjusted"]["direction"],
            "adjusted_direction": item["adjusted"]["direction"],
            "adjusted_magnitude_bucket": item["adjusted"]["magnitude_bucket"],
            "direction_changed_after_adjustment": item["direction_changed_after_adjustment"],
            "incidence_overlap_bucket": item["incidence_overlap"]["bucket"],
        }
        for item in feature_results
    }

    result: dict[str, Any] = {
        "status": "incidence_adjusted_effect_dry_run_ready",
        "query_executed": False,
        "private_output_written": False,
        "input_schema": source["schema_version"],
        "included_pre_count": pre_count,
        "included_post_count": post_count,
        "input_rows_excluded_from_analysis": excluded_count,
        "adjusted_feature_count": len(RADAR_FEATURES),
        "feature_screen": feature_screen,
        "direction_change_count": sum(
            item["direction_changed_after_adjustment"] for item in feature_results
        ),
        "effect_values_printed": False,
        "image_ids_printed": False,
        "coordinates_printed": False,
        "geometry_printed": False,
        "private_paths_printed": False,
        "scientific_validation_run": False,
        "hypothesis_testing_run": False,
        "causal_inference_run": False,
        "depth_estimation_run": False,
        "training_started": False,
        "app_depth_enabled": False,
    }

    if execute:
        private_payload = {
            "schema_version": OUTPUT_SCHEMA,
            "status": "incidence_adjusted_effect_complete",
            "source_schema_version": source["schema_version"],
            "included_pre_count": pre_count,
            "included_post_count": post_count,
            "input_rows_excluded_from_analysis": excluded_count,
            "method": {
                "model": "pre-period ordinary least squares feature ~ incidence difference",
                "comparison": "post minus pre median residual shift",
                "hypothesis_testing": False,
                "causal_interpretation": False,
                "depth_interpretation": False,
            },
            "features": feature_results,
            "image_ids_included": False,
            "coordinates_included": False,
            "geometry_included": False,
        }
        _atomic_write_json(Path(output_path), private_payload)
        result["status"] = "incidence_adjusted_effect_complete"
        result["private_output_written"] = True

    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or execute an offline incidence-adjusted Sentinel-1 effect assessment."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Required private JSON output with --execute.")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_incidence_adjusted_assessment(
            input_path=args.input,
            output_path=args.output,
            execute=args.execute,
        )
    except DepthS1IncidenceAdjustmentError as exc:
        print(
            json.dumps(
                {
                    "status": "incidence_adjusted_effect_failed",
                    "error": str(exc),
                    "effect_values_printed": False,
                    "image_ids_printed": False,
                    "coordinates_printed": False,
                    "geometry_printed": False,
                    "private_paths_printed": False,
                    "scientific_validation_run": False,
                    "depth_estimation_run": False,
                    "app_depth_enabled": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
