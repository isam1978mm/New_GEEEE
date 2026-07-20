"""Audit completeness of the private matched Sentinel-1 feature table.

The input must remain outside Git. Console output is aggregate-only and never
includes image identities, coordinates, geometry, private paths, or feature values.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import extract_depth_s1_matched_features as extractor


REPO_ROOT = Path(__file__).resolve().parents[1]
PERIODS = ("pre", "post")
SIDES = ("site", "background")


class DepthS1FeatureCompletenessError(ValueError):
    """Raised when a private feature table cannot be audited safely."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise DepthS1FeatureCompletenessError(f"{label} must remain outside the repository")


def _read_private_payload(path: Path) -> dict[str, Any]:
    path = Path(path)
    _require_outside_repo(path, "private matched feature input")
    if not path.is_file():
        raise DepthS1FeatureCompletenessError("private matched feature input is missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DepthS1FeatureCompletenessError(
            "private matched feature input is unreadable or invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise DepthS1FeatureCompletenessError("private matched feature input must be a JSON object")
    if payload.get("schema_version") != extractor.PRIVATE_OUTPUT_SCHEMA:
        raise DepthS1FeatureCompletenessError("private matched feature schema is unsupported")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise DepthS1FeatureCompletenessError("private matched feature rows must not be empty")
    return payload


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return not math.isfinite(float(value))
    return True


def audit_private_feature_completeness(path: Path) -> dict[str, Any]:
    payload = _read_private_payload(path)
    rows = payload["rows"]

    missing_by_period = {period: 0 for period in PERIODS}
    missing_by_side = {side: 0 for side in SIDES}
    missing_by_feature = {feature: 0 for feature in extractor.FEATURE_NAMES}
    missing_by_statistic = {statistic: 0 for statistic in extractor.STATISTIC_NAMES}
    zero_count_by_period = {period: 0 for period in PERIODS}
    zero_count_by_side = {side: 0 for side in SIDES}
    zero_count_by_feature = {feature: 0 for feature in extractor.FEATURE_NAMES}

    affected_row_count = 0
    affected_pre_row_count = 0
    affected_post_row_count = 0
    rows_with_zero_valid_pixels = 0
    missing_statistic_count = 0
    missing_explained_by_zero_count = 0

    for row in rows:
        if not isinstance(row, dict):
            raise DepthS1FeatureCompletenessError("private matched feature output contains an invalid row")
        period = str(row.get("period") or "")
        if period not in PERIODS:
            raise DepthS1FeatureCompletenessError("private matched feature output contains an invalid period")

        row_missing = 0
        row_has_zero_count = False
        for side in SIDES:
            stats = row.get(side)
            if not isinstance(stats, dict):
                raise DepthS1FeatureCompletenessError(
                    "private matched feature output contains invalid feature statistics"
                )

            zero_count_features: set[str] = set()
            for feature in extractor.FEATURE_NAMES:
                count_key = f"{feature}_count"
                count_value = stats.get(count_key)
                if isinstance(count_value, (int, float)) and not isinstance(count_value, bool):
                    if math.isfinite(float(count_value)) and float(count_value) == 0.0:
                        zero_count_features.add(feature)
                        row_has_zero_count = True
                        zero_count_by_period[period] += 1
                        zero_count_by_side[side] += 1
                        zero_count_by_feature[feature] += 1

            for feature in extractor.FEATURE_NAMES:
                for statistic in extractor.STATISTIC_NAMES:
                    key = f"{feature}_{statistic}"
                    if _is_missing(stats.get(key)):
                        row_missing += 1
                        missing_statistic_count += 1
                        missing_by_period[period] += 1
                        missing_by_side[side] += 1
                        missing_by_feature[feature] += 1
                        missing_by_statistic[statistic] += 1
                        if feature in zero_count_features and statistic != "count":
                            missing_explained_by_zero_count += 1

        if row_missing:
            affected_row_count += 1
            if period == "pre":
                affected_pre_row_count += 1
            else:
                affected_post_row_count += 1
        if row_has_zero_count:
            rows_with_zero_valid_pixels += 1

    all_missing_explained_by_zero_count = (
        missing_statistic_count > 0
        and missing_statistic_count == missing_explained_by_zero_count
    )
    if missing_statistic_count == 0:
        status = "matched_s1_feature_completeness_complete"
    elif all_missing_explained_by_zero_count:
        status = "matched_s1_feature_completeness_missing_due_to_zero_valid_pixels"
    else:
        status = "matched_s1_feature_completeness_missing_unexplained"

    return {
        "status": status,
        "row_count": len(rows),
        "feature_count": len(extractor.FEATURE_NAMES),
        "statistics_per_feature_count": len(extractor.STATISTIC_NAMES),
        "expected_statistic_count": len(rows)
        * len(SIDES)
        * len(extractor.FEATURE_NAMES)
        * len(extractor.STATISTIC_NAMES),
        "missing_statistic_count": missing_statistic_count,
        "missing_explained_by_zero_count": missing_explained_by_zero_count,
        "all_missing_explained_by_zero_count": all_missing_explained_by_zero_count,
        "affected_row_count": affected_row_count,
        "affected_pre_row_count": affected_pre_row_count,
        "affected_post_row_count": affected_post_row_count,
        "rows_with_zero_valid_pixels": rows_with_zero_valid_pixels,
        "missing_by_period": missing_by_period,
        "missing_by_side": missing_by_side,
        "missing_by_feature": missing_by_feature,
        "missing_by_statistic": missing_by_statistic,
        "zero_count_by_period": zero_count_by_period,
        "zero_count_by_side": zero_count_by_side,
        "zero_count_by_feature": zero_count_by_feature,
        "image_ids_printed": False,
        "coordinates_printed": False,
        "geometry_printed": False,
        "private_paths_printed": False,
        "feature_values_printed": False,
        "scientific_validation_run": False,
        "training_started": False,
        "app_depth_enabled": False,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit private matched Sentinel-1 feature completeness using aggregate-only output."
    )
    parser.add_argument("--input", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = audit_private_feature_completeness(args.input)
    except DepthS1FeatureCompletenessError as exc:
        print(
            json.dumps(
                {
                    "status": "matched_s1_feature_completeness_audit_failed",
                    "error": str(exc),
                    "image_ids_printed": False,
                    "coordinates_printed": False,
                    "geometry_printed": False,
                    "private_paths_printed": False,
                    "feature_values_printed": False,
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
