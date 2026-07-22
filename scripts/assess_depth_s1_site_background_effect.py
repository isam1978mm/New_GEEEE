"""Offline descriptive pre/post site-background effect assessment.

Reads the private matched Sentinel-1 feature output and compares the
site-minus-background distributions before and after the construction window.
This utility performs no network access, no target classification, and no depth
estimation. Detailed numeric results are written only to a private output outside
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
OUTPUT_SCHEMA = "depth_s1_site_background_effect_v1"
FEATURE_NAMES = (
    "vv_db",
    "vh_db",
    "incidence_deg",
    "vv_minus_vh_db",
    "vh_to_vv_linear_ratio",
)
QUANTILE_STATS = ("p25", "median", "p75")


class DepthS1EffectAssessmentError(ValueError):
    """Raised when a private descriptive effect assessment cannot proceed safely."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise DepthS1EffectAssessmentError(f"{label} must remain outside the repository")


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DepthS1EffectAssessmentError(f"{label} is unreadable or invalid JSON") from exc


def _finite_float(value: Any, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise DepthS1EffectAssessmentError(f"{label} is missing or not numeric") from exc
    if not math.isfinite(numeric):
        raise DepthS1EffectAssessmentError(f"{label} is not finite")
    return numeric


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        raise DepthS1EffectAssessmentError("cannot summarize an empty value set")
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


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        raise DepthS1EffectAssessmentError("private effect-assessment output could not be written") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def _load_included_rows(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    _require_outside_repo(path, "private matched feature input")
    if not path.is_file():
        raise DepthS1EffectAssessmentError("private matched feature input is missing")

    payload = _read_json(path, "private matched feature input")
    if not isinstance(payload, dict):
        raise DepthS1EffectAssessmentError("private matched feature input must be a JSON object")
    if payload.get("schema_version") != INPUT_SCHEMA:
        raise DepthS1EffectAssessmentError("private matched feature input schema is unsupported")
    if payload.get("status") != "matched_s1_feature_extraction_complete":
        raise DepthS1EffectAssessmentError("private matched feature input is not complete")
    if payload.get("coordinates_included") is True or payload.get("geometry_included") is True:
        raise DepthS1EffectAssessmentError("private matched feature input must not embed coordinates or geometry")

    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise DepthS1EffectAssessmentError("private matched feature input rows are invalid")

    included: list[dict[str, Any]] = []
    excluded_count = 0
    for row in rows:
        if not isinstance(row, dict):
            raise DepthS1EffectAssessmentError("private matched feature input contains an invalid row")
        if row.get("analysis_included") is not True:
            excluded_count += 1
            continue
        period = str(row.get("period") or "")
        if period not in {"pre", "post"}:
            raise DepthS1EffectAssessmentError("included row has an unsupported period")
        deltas = row.get("site_minus_background")
        if not isinstance(deltas, dict):
            raise DepthS1EffectAssessmentError("included row has invalid site-minus-background values")

        normalized: dict[str, Any] = {"period": period, "site_minus_background": {}}
        for feature in FEATURE_NAMES:
            for statistic in QUANTILE_STATS:
                key = f"{feature}_{statistic}"
                normalized["site_minus_background"][key] = _finite_float(
                    deltas.get(key),
                    f"included row {key}",
                )
        included.append(normalized)

    pre_count = sum(1 for row in included if row["period"] == "pre")
    post_count = sum(1 for row in included if row["period"] == "post")
    if pre_count < 2 or post_count < 2:
        raise DepthS1EffectAssessmentError("effect assessment requires at least two usable rows in each period")

    return payload, included, excluded_count


def _summarize_feature(rows: list[dict[str, Any]], feature: str) -> dict[str, Any]:
    statistics: dict[str, Any] = {}
    directions: list[str] = []

    for statistic in QUANTILE_STATS:
        key = f"{feature}_{statistic}"
        pre = [row["site_minus_background"][key] for row in rows if row["period"] == "pre"]
        post = [row["site_minus_background"][key] for row in rows if row["period"] == "post"]

        pre_location = median(pre)
        post_location = median(post)
        shift = post_location - pre_location
        pre_iqr = _iqr(pre)
        post_iqr = _iqr(post)
        pooled_iqr = median([pre_iqr, post_iqr])
        bucket, normalized_shift = _magnitude_bucket(shift, pooled_iqr)
        direction = _direction(shift, max(abs(pre_location), abs(post_location), pooled_iqr))
        directions.append(direction)

        statistics[statistic] = {
            "pre_count": len(pre),
            "post_count": len(post),
            "pre_median": pre_location,
            "post_median": post_location,
            "post_minus_pre_median_shift": shift,
            "pre_iqr": pre_iqr,
            "post_iqr": post_iqr,
            "pooled_iqr": pooled_iqr,
            "normalized_shift_iqr_units": normalized_shift,
            "direction": direction,
            "magnitude_bucket": bucket,
            "post_above_pre_median_fraction": sum(value > pre_location for value in post) / len(post),
        }

    nonzero_directions = {value for value in directions if value != "no_material_numeric_change"}
    quantile_direction_agreement = (
        len(nonzero_directions) == 1
        and all(value != "no_material_numeric_change" for value in directions)
    )

    primary = statistics["median"]
    return {
        "feature": feature,
        "primary_statistic": "median",
        "primary_direction": primary["direction"],
        "primary_magnitude_bucket": primary["magnitude_bucket"],
        "quantile_direction_agreement": quantile_direction_agreement,
        "statistics": statistics,
    }


def run_effect_assessment(
    *,
    input_path: Path,
    output_path: Path | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    source, rows, excluded_count = _load_included_rows(input_path)
    if output_path is not None:
        _require_outside_repo(output_path, "private effect-assessment output")
    if execute and output_path is None:
        raise DepthS1EffectAssessmentError("execute requires a private output path outside the repository")

    pre_count = sum(1 for row in rows if row["period"] == "pre")
    post_count = sum(1 for row in rows if row["period"] == "post")
    feature_results = [_summarize_feature(rows, feature) for feature in FEATURE_NAMES]

    feature_screen = {
        item["feature"]: {
            "primary_direction": item["primary_direction"],
            "primary_magnitude_bucket": item["primary_magnitude_bucket"],
            "quantile_direction_agreement": item["quantile_direction_agreement"],
        }
        for item in feature_results
    }

    result: dict[str, Any] = {
        "status": "descriptive_effect_assessment_dry_run_ready",
        "query_executed": False,
        "private_output_written": False,
        "input_schema": source["schema_version"],
        "included_pre_count": pre_count,
        "included_post_count": post_count,
        "input_rows_excluded_from_analysis": excluded_count,
        "assessed_feature_count": len(FEATURE_NAMES),
        "feature_screen": feature_screen,
        "quantile_direction_agreement_count": sum(
            bool(item["quantile_direction_agreement"]) for item in feature_results
        ),
        "effect_values_printed": False,
        "image_ids_printed": False,
        "coordinates_printed": False,
        "geometry_printed": False,
        "private_paths_printed": False,
        "scientific_validation_run": False,
        "causal_inference_run": False,
        "depth_estimation_run": False,
        "training_started": False,
        "app_depth_enabled": False,
    }

    if execute:
        private_payload = {
            "schema_version": OUTPUT_SCHEMA,
            "status": "descriptive_effect_assessment_complete",
            "source_schema_version": source["schema_version"],
            "included_pre_count": pre_count,
            "included_post_count": post_count,
            "input_rows_excluded_from_analysis": excluded_count,
            "method": {
                "comparison": "post minus pre change in per-image site-minus-background distributions",
                "primary_statistic": "median",
                "scale": "median of pre and post interquartile ranges",
                "magnitude_buckets": [
                    "under_0_25_iqr",
                    "0_25_to_0_5_iqr",
                    "0_5_to_1_iqr",
                    "at_least_1_iqr",
                ],
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
        result["status"] = "descriptive_effect_assessment_complete"
        result["private_output_written"] = True

    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or execute an offline descriptive Sentinel-1 site-background effect assessment."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Required private aggregate JSON output when --execute is used.")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_effect_assessment(
            input_path=args.input,
            output_path=args.output,
            execute=args.execute,
        )
    except DepthS1EffectAssessmentError as exc:
        print(
            json.dumps(
                {
                    "status": "descriptive_effect_assessment_failed",
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
