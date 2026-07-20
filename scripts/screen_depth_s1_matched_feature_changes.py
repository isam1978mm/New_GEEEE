"""Screen pre/post changes in private matched Sentinel-1 site/background features.

The input and numeric output must remain outside Git. Rows with zero valid pixels
are excluded without imputation. Console output is aggregate-only and contains no
image identities, coordinates, geometry, private paths, or exact feature values.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

import extract_depth_s1_matched_features as extractor


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_SCHEMA = "depth_s1_matched_descriptive_screen_v1"
PERIODS = ("pre", "post")
SIDES = ("site", "background")
ZERO_TOLERANCE = 1e-12


class DepthS1DescriptiveScreenError(ValueError):
    """Raised when the private descriptive screen cannot proceed safely."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise DepthS1DescriptiveScreenError(f"{label} must remain outside the repository")


def _read_private_payload(path: Path) -> dict[str, Any]:
    path = Path(path)
    _require_outside_repo(path, "private matched feature input")
    if not path.is_file():
        raise DepthS1DescriptiveScreenError("private matched feature input is missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DepthS1DescriptiveScreenError(
            "private matched feature input is unreadable or invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise DepthS1DescriptiveScreenError("private matched feature input must be a JSON object")
    if payload.get("schema_version") != extractor.PRIVATE_OUTPUT_SCHEMA:
        raise DepthS1DescriptiveScreenError("private matched feature schema is unsupported")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise DepthS1DescriptiveScreenError("private matched feature rows must not be empty")
    return payload


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        raise DepthS1DescriptiveScreenError("descriptive screen requires non-empty values")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return ordered[lower_index]
    fraction = position - lower_index
    return ordered[lower_index] + fraction * (ordered[upper_index] - ordered[lower_index])


def _cliffs_delta(post_values: list[float], pre_values: list[float]) -> float:
    if not post_values or not pre_values:
        raise DepthS1DescriptiveScreenError("Cliff's delta requires non-empty periods")
    greater = 0
    lower = 0
    for post_value in post_values:
        for pre_value in pre_values:
            if post_value > pre_value:
                greater += 1
            elif post_value < pre_value:
                lower += 1
    return (greater - lower) / (len(post_values) * len(pre_values))


def _direction(value: float) -> str:
    if value > ZERO_TOLERANCE:
        return "positive"
    if value < -ZERO_TOLERANCE:
        return "negative"
    return "zero"


def _validate_row_and_extract_deltas(row: Any) -> tuple[str, dict[str, float] | None, str | None]:
    if not isinstance(row, dict):
        raise DepthS1DescriptiveScreenError("private matched feature output contains an invalid row")
    period = str(row.get("period") or "")
    if period not in PERIODS:
        raise DepthS1DescriptiveScreenError("private matched feature output contains an invalid period")

    image_id = str(row.get("image_id") or "").strip()
    if not image_id:
        raise DepthS1DescriptiveScreenError("private matched feature output contains a missing image identity")

    zero_valid_found = False
    unexplained_missing_found = False
    side_stats: dict[str, dict[str, Any]] = {}

    for side in SIDES:
        stats = row.get(side)
        if not isinstance(stats, dict):
            raise DepthS1DescriptiveScreenError(
                "private matched feature output contains invalid feature statistics"
            )
        side_stats[side] = stats
        for feature in extractor.FEATURE_NAMES:
            count_key = f"{feature}_count"
            count_value = _finite_number(stats.get(count_key))
            if count_value is None or count_value < 0:
                unexplained_missing_found = True
                continue
            if count_value == 0:
                zero_valid_found = True
                continue
            for statistic in extractor.STATISTIC_NAMES:
                key = f"{feature}_{statistic}"
                if _finite_number(stats.get(key)) is None:
                    unexplained_missing_found = True

    if unexplained_missing_found:
        raise DepthS1DescriptiveScreenError(
            "private matched feature output contains missing statistics not explained by zero valid pixels"
        )
    if zero_valid_found:
        return period, None, "zero_valid_pixels"

    deltas: dict[str, float] = {}
    stored_deltas = row.get("site_minus_background")
    if not isinstance(stored_deltas, dict):
        raise DepthS1DescriptiveScreenError(
            "private matched feature output contains invalid site-background differences"
        )

    for feature in extractor.FEATURE_NAMES:
        key = f"{feature}_median"
        site_value = _finite_number(side_stats["site"].get(key))
        background_value = _finite_number(side_stats["background"].get(key))
        stored_value = _finite_number(stored_deltas.get(key))
        if site_value is None or background_value is None or stored_value is None:
            raise DepthS1DescriptiveScreenError(
                "usable private matched feature row contains an invalid median"
            )
        calculated = site_value - background_value
        if not math.isclose(calculated, stored_value, rel_tol=1e-9, abs_tol=1e-9):
            raise DepthS1DescriptiveScreenError(
                "stored site-background median does not match source feature statistics"
            )
        deltas[feature] = calculated

    return period, deltas, None


def _period_summary(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "p25": _quantile(values, 0.25),
        "median": _quantile(values, 0.5),
        "p75": _quantile(values, 0.75),
        "site_higher_fraction": sum(value > 0 for value in values) / len(values),
    }


def build_descriptive_screen(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise DepthS1DescriptiveScreenError("private matched feature rows must not be empty")

    seen_ids: set[str] = set()
    values_by_period = {
        period: {feature: [] for feature in extractor.FEATURE_NAMES}
        for period in PERIODS
    }
    input_by_period = {period: 0 for period in PERIODS}
    excluded_by_period = {period: 0 for period in PERIODS}
    exclusion_reason_counts = {"zero_valid_pixels": 0}

    for row in rows:
        if not isinstance(row, dict):
            raise DepthS1DescriptiveScreenError("private matched feature output contains an invalid row")
        image_id = str(row.get("image_id") or "").strip()
        if not image_id:
            raise DepthS1DescriptiveScreenError("private matched feature output contains a missing image identity")
        if image_id in seen_ids:
            raise DepthS1DescriptiveScreenError("private matched feature output contains a duplicate image identity")
        seen_ids.add(image_id)

        period, deltas, exclusion_reason = _validate_row_and_extract_deltas(row)
        input_by_period[period] += 1
        if exclusion_reason is not None:
            excluded_by_period[period] += 1
            exclusion_reason_counts[exclusion_reason] += 1
            continue
        assert deltas is not None
        for feature, value in deltas.items():
            values_by_period[period][feature].append(value)

    usable_by_period = {
        period: input_by_period[period] - excluded_by_period[period]
        for period in PERIODS
    }
    if usable_by_period["pre"] < 1 or usable_by_period["post"] < 1:
        raise DepthS1DescriptiveScreenError(
            "descriptive screen requires at least one usable pre and post row"
        )

    feature_results: dict[str, Any] = {}
    direction_by_feature: dict[str, str] = {}
    for feature in extractor.FEATURE_NAMES:
        pre_values = values_by_period["pre"][feature]
        post_values = values_by_period["post"][feature]
        if len(pre_values) != usable_by_period["pre"] or len(post_values) != usable_by_period["post"]:
            raise DepthS1DescriptiveScreenError("usable feature counts are inconsistent")
        pre_summary = _period_summary(pre_values)
        post_summary = _period_summary(post_values)
        median_shift = float(post_summary["median"]) - float(pre_summary["median"])
        shift_direction = _direction(median_shift)
        direction_by_feature[feature] = shift_direction
        feature_results[feature] = {
            "pre": pre_summary,
            "post": post_summary,
            "post_minus_pre_median_shift": median_shift,
            "shift_direction": shift_direction,
            "cliffs_delta_post_vs_pre": _cliffs_delta(post_values, pre_values),
        }

    positive_count = sum(direction == "positive" for direction in direction_by_feature.values())
    negative_count = sum(direction == "negative" for direction in direction_by_feature.values())
    zero_count = sum(direction == "zero" for direction in direction_by_feature.values())

    private_output = {
        "schema_version": OUTPUT_SCHEMA,
        "status": "matched_s1_descriptive_screen_complete",
        "source_schema_version": payload.get("schema_version"),
        "selection_contract": payload.get("selection_contract"),
        "input_row_count": len(rows),
        "input_by_period": input_by_period,
        "excluded_row_count": sum(excluded_by_period.values()),
        "excluded_by_period": excluded_by_period,
        "exclusion_reason_counts": exclusion_reason_counts,
        "usable_row_count": sum(usable_by_period.values()),
        "usable_by_period": usable_by_period,
        "feature_results": feature_results,
        "image_ids_included": False,
        "coordinates_included": False,
        "geometry_included": False,
        "causal_test_run": False,
        "significance_test_run": False,
        "scientific_validation_run": False,
        "training_started": False,
        "app_depth_enabled": False,
    }
    console_result = {
        "status": "matched_s1_descriptive_screen_complete",
        "input_row_count": len(rows),
        "input_pre_count": input_by_period["pre"],
        "input_post_count": input_by_period["post"],
        "excluded_row_count": sum(excluded_by_period.values()),
        "excluded_pre_count": excluded_by_period["pre"],
        "excluded_post_count": excluded_by_period["post"],
        "zero_valid_row_count": exclusion_reason_counts["zero_valid_pixels"],
        "usable_row_count": sum(usable_by_period.values()),
        "usable_pre_count": usable_by_period["pre"],
        "usable_post_count": usable_by_period["post"],
        "feature_count": len(extractor.FEATURE_NAMES),
        "positive_shift_feature_count": positive_count,
        "negative_shift_feature_count": negative_count,
        "zero_shift_feature_count": zero_count,
        "shift_direction_by_feature": direction_by_feature,
        "private_output_written": False,
        "image_ids_printed": False,
        "coordinates_printed": False,
        "geometry_printed": False,
        "private_paths_printed": False,
        "feature_values_printed": False,
        "causal_test_run": False,
        "significance_test_run": False,
        "scientific_validation_run": False,
        "depth_claim_made": False,
        "training_started": False,
        "app_depth_enabled": False,
    }
    return private_output, console_result


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        raise DepthS1DescriptiveScreenError("private descriptive screen output could not be written") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def run_descriptive_screen(*, input_path: Path, output_path: Path) -> dict[str, Any]:
    _require_outside_repo(output_path, "private descriptive screen output")
    if Path(input_path).expanduser().resolve(strict=False) == Path(output_path).expanduser().resolve(strict=False):
        raise DepthS1DescriptiveScreenError("input and output must use different files")
    payload = _read_private_payload(input_path)
    private_output, console_result = build_descriptive_screen(payload)
    _atomic_write_json(Path(output_path), private_output)
    console_result["private_output_written"] = True
    return console_result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Exclude zero-valid matched rows and run a private descriptive Sentinel-1 pre/post screen."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_descriptive_screen(input_path=args.input, output_path=args.output)
    except DepthS1DescriptiveScreenError as exc:
        print(
            json.dumps(
                {
                    "status": "matched_s1_descriptive_screen_failed",
                    "error": str(exc),
                    "image_ids_printed": False,
                    "coordinates_printed": False,
                    "geometry_printed": False,
                    "private_paths_printed": False,
                    "feature_values_printed": False,
                    "depth_claim_made": False,
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
