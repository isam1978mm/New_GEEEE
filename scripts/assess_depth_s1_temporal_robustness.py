"""Offline temporal-block robustness screen for TAMUCC Sentinel-1 effects.

Splits usable pre and post acquisitions into chronological blocks. For each radar
feature and each pre/post block pair, refits the pre-block incidence relationship
and compares adjusted residual medians.

This is a descriptive robustness screen only. It performs no network access,
hypothesis testing, causal inference, target classification, or depth estimation.
Detailed numeric results remain in a private output outside the repository.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any

import assess_depth_s1_incidence_adjusted_effect as incidence

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA = incidence.INPUT_SCHEMA
OUTPUT_SCHEMA = "depth_s1_temporal_block_robustness_v1"
BLOCK_COUNT = 4
MIN_BLOCK_ROWS = 8


class DepthS1TemporalRobustnessError(ValueError):
    """Raised when temporal robustness screening cannot proceed safely."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise DepthS1TemporalRobustnessError(f"{label} must remain outside the repository")


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DepthS1TemporalRobustnessError(f"{label} is unreadable or invalid JSON") from exc


def _parse_timestamp(value: Any) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise DepthS1TemporalRobustnessError("included row has a missing timestamp")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DepthS1TemporalRobustnessError("included row has an invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise DepthS1TemporalRobustnessError("included row timestamp must include a timezone")
    return parsed.astimezone(UTC)


def _finite_float(value: Any, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise DepthS1TemporalRobustnessError(f"{label} is missing or not numeric") from exc
    if not math.isfinite(numeric):
        raise DepthS1TemporalRobustnessError(f"{label} is not finite")
    return numeric


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        raise DepthS1TemporalRobustnessError("private temporal robustness output could not be written") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def _split_blocks(rows: list[dict[str, Any]], block_count: int) -> list[list[dict[str, Any]]]:
    ordered = sorted(rows, key=lambda row: row["timestamp"])
    if len(ordered) < block_count * MIN_BLOCK_ROWS:
        raise DepthS1TemporalRobustnessError(
            "not enough usable rows for four temporal blocks"
        )

    blocks: list[list[dict[str, Any]]] = []
    for index in range(block_count):
        start = round(index * len(ordered) / block_count)
        end = round((index + 1) * len(ordered) / block_count)
        block = ordered[start:end]
        if len(block) < MIN_BLOCK_ROWS:
            raise DepthS1TemporalRobustnessError(
                "a temporal block has too few usable rows"
            )
        blocks.append(block)
    return blocks


def _load_rows(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    _require_outside_repo(path, "private matched feature input")
    if not path.is_file():
        raise DepthS1TemporalRobustnessError("private matched feature input is missing")

    payload = _read_json(path, "private matched feature input")
    if not isinstance(payload, dict):
        raise DepthS1TemporalRobustnessError("private matched feature input must be a JSON object")
    if payload.get("schema_version") != INPUT_SCHEMA:
        raise DepthS1TemporalRobustnessError("private matched feature input schema is unsupported")
    if payload.get("status") != "matched_s1_feature_extraction_complete":
        raise DepthS1TemporalRobustnessError("private matched feature input is not complete")
    if payload.get("coordinates_included") is True or payload.get("geometry_included") is True:
        raise DepthS1TemporalRobustnessError("private matched feature input must not embed coordinates or geometry")

    raw_rows = payload.get("rows")
    if not isinstance(raw_rows, list):
        raise DepthS1TemporalRobustnessError("private matched feature input rows are invalid")

    rows: list[dict[str, Any]] = []
    excluded_count = 0
    for item in raw_rows:
        if not isinstance(item, dict):
            raise DepthS1TemporalRobustnessError("private matched feature input contains an invalid row")
        if item.get("analysis_included") is not True:
            excluded_count += 1
            continue

        period = str(item.get("period") or "")
        if period not in {"pre", "post"}:
            raise DepthS1TemporalRobustnessError("included row has an unsupported period")

        deltas = item.get("site_minus_background")
        if not isinstance(deltas, dict):
            raise DepthS1TemporalRobustnessError("included row has invalid site-minus-background values")

        normalized: dict[str, Any] = {
            "period": period,
            "timestamp": _parse_timestamp(item.get("timestamp")),
            "incidence": _finite_float(
                deltas.get(incidence.INCIDENCE_KEY),
                incidence.INCIDENCE_KEY,
            ),
            "radar": {},
        }
        for feature in incidence.RADAR_FEATURES:
            key = f"{feature}_median"
            normalized["radar"][feature] = _finite_float(deltas.get(key), key)
        rows.append(normalized)

    return payload, rows, excluded_count


def _sign(value: float, scale: float) -> str:
    tolerance = max(1e-12, abs(scale) * 1e-12)
    if value > tolerance:
        return "increase"
    if value < -tolerance:
        return "decrease"
    return "no_material_numeric_change"


def _consistency_bucket(fraction: float) -> str:
    if fraction >= 1.0:
        return "all_blocks_consistent"
    if fraction >= 0.75:
        return "at_least_75_percent_consistent"
    if fraction >= 0.5:
        return "at_least_50_percent_consistent"
    return "under_50_percent_consistent"


def _overlap_bucket(fraction: float) -> str:
    if fraction >= 0.75:
        return "at_least_75_percent_qualified"
    if fraction >= 0.5:
        return "at_least_50_percent_qualified"
    return "under_50_percent_qualified"


def _assess_pair(
    pre_rows: list[dict[str, Any]],
    post_rows: list[dict[str, Any]],
    feature: str,
) -> dict[str, Any]:
    pre_x = [row["incidence"] for row in pre_rows]
    post_x = [row["incidence"] for row in post_rows]
    pre_y = [row["radar"][feature] for row in pre_rows]
    post_y = [row["radar"][feature] for row in post_rows]

    try:
        intercept, slope = incidence._fit_pre_linear(pre_x, pre_y)
    except incidence.DepthS1IncidenceAdjustmentError as exc:
        raise DepthS1TemporalRobustnessError(str(exc)) from exc

    pre_residuals = [
        y_value - (intercept + slope * x_value)
        for x_value, y_value in zip(pre_x, pre_y, strict=True)
    ]
    post_residuals = [
        y_value - (intercept + slope * x_value)
        for x_value, y_value in zip(post_x, post_y, strict=True)
    ]

    shift = median(post_residuals) - median(pre_residuals)
    pre_iqr = incidence._iqr(pre_residuals)
    post_iqr = incidence._iqr(post_residuals)
    pooled_iqr = median([pre_iqr, post_iqr])
    magnitude_bucket, normalized_shift = incidence._magnitude_bucket(shift, pooled_iqr)
    direction = _sign(
        shift,
        max(abs(median(pre_residuals)), abs(median(post_residuals)), pooled_iqr),
    )

    pre_min = min(pre_x)
    pre_max = max(pre_x)
    overlap_fraction = sum(pre_min <= value <= pre_max for value in post_x) / len(post_x)

    return {
        "pre_count": len(pre_rows),
        "post_count": len(post_rows),
        "pre_start": pre_rows[0]["timestamp"].isoformat(),
        "pre_end": pre_rows[-1]["timestamp"].isoformat(),
        "post_start": post_rows[0]["timestamp"].isoformat(),
        "post_end": post_rows[-1]["timestamp"].isoformat(),
        "incidence_slope": slope,
        "adjusted_shift": shift,
        "normalized_shift_iqr_units": normalized_shift,
        "direction": direction,
        "magnitude_bucket": magnitude_bucket,
        "post_within_pre_incidence_range_fraction": overlap_fraction,
        "overlap_qualified": overlap_fraction >= 0.75,
    }


def _assess_feature(
    pre_blocks: list[list[dict[str, Any]]],
    post_blocks: list[list[dict[str, Any]]],
    feature: str,
) -> dict[str, Any]:
    comparisons: list[dict[str, Any]] = []
    for pre_index, pre_block in enumerate(pre_blocks, start=1):
        for post_index, post_block in enumerate(post_blocks, start=1):
            result = _assess_pair(pre_block, post_block, feature)
            result["pre_block"] = pre_index
            result["post_block"] = post_index
            comparisons.append(result)

    nonzero = [
        item for item in comparisons
        if item["direction"] != "no_material_numeric_change"
    ]
    increase_count = sum(item["direction"] == "increase" for item in comparisons)
    decrease_count = sum(item["direction"] == "decrease" for item in comparisons)
    dominant_direction = (
        "increase"
        if increase_count > decrease_count
        else "decrease"
        if decrease_count > increase_count
        else "mixed"
    )
    dominant_count = max(increase_count, decrease_count)
    consistency_fraction = dominant_count / len(comparisons)
    qualified = [item for item in comparisons if item["overlap_qualified"]]
    qualified_fraction = len(qualified) / len(comparisons)

    qualified_dominant_count = 0
    if dominant_direction in {"increase", "decrease"}:
        qualified_dominant_count = sum(
            item["direction"] == dominant_direction for item in qualified
        )
    qualified_consistency_fraction = (
        qualified_dominant_count / len(qualified)
        if qualified
        else 0.0
    )

    return {
        "feature": feature,
        "comparison_count": len(comparisons),
        "nonzero_comparison_count": len(nonzero),
        "increase_count": increase_count,
        "decrease_count": decrease_count,
        "dominant_direction": dominant_direction,
        "dominant_direction_fraction": consistency_fraction,
        "consistency_bucket": _consistency_bucket(consistency_fraction),
        "overlap_qualified_count": len(qualified),
        "overlap_qualified_fraction": qualified_fraction,
        "overlap_qualification_bucket": _overlap_bucket(qualified_fraction),
        "qualified_dominant_direction_fraction": qualified_consistency_fraction,
        "qualified_consistency_bucket": _consistency_bucket(
            qualified_consistency_fraction
        ),
        "comparisons": comparisons,
    }


def run_temporal_robustness(
    *,
    input_path: Path,
    output_path: Path | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    source, rows, excluded_count = _load_rows(input_path)
    if output_path is not None:
        _require_outside_repo(output_path, "private temporal robustness output")
    if execute and output_path is None:
        raise DepthS1TemporalRobustnessError(
            "execute requires a private output path outside the repository"
        )

    pre_rows = [row for row in rows if row["period"] == "pre"]
    post_rows = [row for row in rows if row["period"] == "post"]
    pre_blocks = _split_blocks(pre_rows, BLOCK_COUNT)
    post_blocks = _split_blocks(post_rows, BLOCK_COUNT)

    feature_results = [
        _assess_feature(pre_blocks, post_blocks, feature)
        for feature in incidence.RADAR_FEATURES
    ]

    feature_screen = {
        item["feature"]: {
            "dominant_direction": item["dominant_direction"],
            "consistency_bucket": item["consistency_bucket"],
            "overlap_qualification_bucket": item["overlap_qualification_bucket"],
            "qualified_consistency_bucket": item["qualified_consistency_bucket"],
        }
        for item in feature_results
    }

    result: dict[str, Any] = {
        "status": "temporal_block_robustness_dry_run_ready",
        "query_executed": False,
        "private_output_written": False,
        "input_schema": source["schema_version"],
        "included_pre_count": len(pre_rows),
        "included_post_count": len(post_rows),
        "input_rows_excluded_from_analysis": excluded_count,
        "pre_block_count": len(pre_blocks),
        "post_block_count": len(post_blocks),
        "comparisons_per_feature": len(pre_blocks) * len(post_blocks),
        "assessed_feature_count": len(incidence.RADAR_FEATURES),
        "feature_screen": feature_screen,
        "effect_values_printed": False,
        "timestamps_printed": False,
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
            "status": "temporal_block_robustness_complete",
            "source_schema_version": source["schema_version"],
            "included_pre_count": len(pre_rows),
            "included_post_count": len(post_rows),
            "input_rows_excluded_from_analysis": excluded_count,
            "block_count_per_period": BLOCK_COUNT,
            "comparisons_per_feature": len(pre_blocks) * len(post_blocks),
            "method": {
                "temporal_split": "four chronological blocks per period",
                "model": "pre-block ordinary least squares feature ~ incidence difference",
                "comparison": "post-block minus pre-block median residual shift",
                "incidence_overlap_qualified_threshold": 0.75,
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
        result["status"] = "temporal_block_robustness_complete"
        result["private_output_written"] = True

    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or execute an offline temporal-block robustness screen."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Required private JSON output with --execute.")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_temporal_robustness(
            input_path=args.input,
            output_path=args.output,
            execute=args.execute,
        )
    except DepthS1TemporalRobustnessError as exc:
        print(
            json.dumps(
                {
                    "status": "temporal_block_robustness_failed",
                    "error": str(exc),
                    "effect_values_printed": False,
                    "timestamps_printed": False,
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
