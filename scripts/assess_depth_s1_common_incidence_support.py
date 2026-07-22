"""Offline common-incidence-support assessment for TAMUCC Sentinel-1 effects.

Restricts usable pre and post acquisitions to the shared range of the per-image
site-minus-background incidence-angle median. It then repeats the pre-period
incidence adjustment for the four radar-feature medians.

This is the final whole-site TAMUCC feasibility screen. It performs no network
access, hypothesis testing, causal inference, target classification, or depth
estimation. Detailed numeric results remain in a private output outside the
repository.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from statistics import median
from typing import Any

import assess_depth_s1_incidence_adjusted_effect as adjustment

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA = adjustment.INPUT_SCHEMA
OUTPUT_SCHEMA = "depth_s1_common_incidence_support_v1"
MIN_ROWS_PER_PERIOD = 8


class DepthS1CommonSupportError(ValueError):
    """Raised when common-incidence-support assessment cannot proceed safely."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise DepthS1CommonSupportError(f"{label} must remain outside the repository")


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DepthS1CommonSupportError(f"{label} is unreadable or invalid JSON") from exc


def _finite_float(value: Any, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise DepthS1CommonSupportError(f"{label} is missing or not numeric") from exc
    if not math.isfinite(numeric):
        raise DepthS1CommonSupportError(f"{label} is not finite")
    return numeric


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    except OSError as exc:
        raise DepthS1CommonSupportError(
            "private common-support output could not be written"
        ) from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def _retention_bucket(fraction: float) -> str:
    if fraction >= 0.9:
        return "at_least_90_percent_retained"
    if fraction >= 0.75:
        return "at_least_75_percent_retained"
    if fraction >= 0.5:
        return "at_least_50_percent_retained"
    return "under_50_percent_retained"


def _load_rows(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    _require_outside_repo(path, "private matched feature input")
    if not path.is_file():
        raise DepthS1CommonSupportError("private matched feature input is missing")

    payload = _read_json(path, "private matched feature input")
    if not isinstance(payload, dict):
        raise DepthS1CommonSupportError(
            "private matched feature input must be a JSON object"
        )
    if payload.get("schema_version") != INPUT_SCHEMA:
        raise DepthS1CommonSupportError(
            "private matched feature input schema is unsupported"
        )
    if payload.get("status") != "matched_s1_feature_extraction_complete":
        raise DepthS1CommonSupportError(
            "private matched feature input is not complete"
        )
    if payload.get("coordinates_included") is True or payload.get("geometry_included") is True:
        raise DepthS1CommonSupportError(
            "private matched feature input must not embed coordinates or geometry"
        )

    raw_rows = payload.get("rows")
    if not isinstance(raw_rows, list):
        raise DepthS1CommonSupportError(
            "private matched feature input rows are invalid"
        )

    rows: list[dict[str, Any]] = []
    excluded_count = 0
    for item in raw_rows:
        if not isinstance(item, dict):
            raise DepthS1CommonSupportError(
                "private matched feature input contains an invalid row"
            )
        if item.get("analysis_included") is not True:
            excluded_count += 1
            continue

        period = str(item.get("period") or "")
        if period not in {"pre", "post"}:
            raise DepthS1CommonSupportError(
                "included row has an unsupported period"
            )

        deltas = item.get("site_minus_background")
        if not isinstance(deltas, dict):
            raise DepthS1CommonSupportError(
                "included row has invalid site-minus-background values"
            )

        normalized: dict[str, Any] = {
            "period": period,
            "incidence": _finite_float(
                deltas.get(adjustment.INCIDENCE_KEY),
                adjustment.INCIDENCE_KEY,
            ),
            "radar": {},
        }
        for feature in adjustment.RADAR_FEATURES:
            key = f"{feature}_median"
            normalized["radar"][feature] = _finite_float(deltas.get(key), key)
        rows.append(normalized)

    return payload, rows, excluded_count


def _common_support(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pre = [row for row in rows if row["period"] == "pre"]
    post = [row for row in rows if row["period"] == "post"]
    if len(pre) < MIN_ROWS_PER_PERIOD or len(post) < MIN_ROWS_PER_PERIOD:
        raise DepthS1CommonSupportError(
            "common-support assessment requires at least eight usable rows in each period"
        )

    pre_min = min(row["incidence"] for row in pre)
    pre_max = max(row["incidence"] for row in pre)
    post_min = min(row["incidence"] for row in post)
    post_max = max(row["incidence"] for row in post)

    lower = max(pre_min, post_min)
    upper = min(pre_max, post_max)
    if lower >= upper:
        raise DepthS1CommonSupportError(
            "pre and post periods have no usable common incidence range"
        )

    restricted = [
        row for row in rows
        if lower <= row["incidence"] <= upper
    ]
    restricted_pre = [row for row in restricted if row["period"] == "pre"]
    restricted_post = [row for row in restricted if row["period"] == "post"]

    if (
        len(restricted_pre) < MIN_ROWS_PER_PERIOD
        or len(restricted_post) < MIN_ROWS_PER_PERIOD
    ):
        raise DepthS1CommonSupportError(
            "too few rows remain inside the common incidence range"
        )

    pre_fraction = len(restricted_pre) / len(pre)
    post_fraction = len(restricted_post) / len(post)
    support = {
        "full_pre_count": len(pre),
        "full_post_count": len(post),
        "restricted_pre_count": len(restricted_pre),
        "restricted_post_count": len(restricted_post),
        "pre_retained_fraction": pre_fraction,
        "post_retained_fraction": post_fraction,
        "pre_retention_bucket": _retention_bucket(pre_fraction),
        "post_retention_bucket": _retention_bucket(post_fraction),
        "pre_incidence_min": pre_min,
        "pre_incidence_max": pre_max,
        "post_incidence_min": post_min,
        "post_incidence_max": post_max,
        "common_incidence_lower": lower,
        "common_incidence_upper": upper,
    }
    return restricted, support


def _assess_feature(
    full_rows: list[dict[str, Any]],
    restricted_rows: list[dict[str, Any]],
    feature: str,
) -> dict[str, Any]:
    try:
        full = adjustment._assess_feature(full_rows, feature)
        restricted = adjustment._assess_feature(restricted_rows, feature)
    except adjustment.DepthS1IncidenceAdjustmentError as exc:
        raise DepthS1CommonSupportError(str(exc)) from exc

    return {
        "feature": feature,
        "full_period_adjusted": full["adjusted"],
        "common_support_adjusted": restricted["adjusted"],
        "full_period_incidence_overlap": full["incidence_overlap"],
        "direction_changed_on_common_support": (
            full["adjusted"]["direction"]
            != restricted["adjusted"]["direction"]
        ),
    }


def run_common_support_assessment(
    *,
    input_path: Path,
    output_path: Path | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    source, rows, excluded_count = _load_rows(input_path)
    if output_path is not None:
        _require_outside_repo(output_path, "private common-support output")
    if execute and output_path is None:
        raise DepthS1CommonSupportError(
            "execute requires a private output path outside the repository"
        )

    restricted_rows, support = _common_support(rows)
    features = [
        _assess_feature(rows, restricted_rows, feature)
        for feature in adjustment.RADAR_FEATURES
    ]

    feature_screen = {
        item["feature"]: {
            "full_adjusted_direction": item["full_period_adjusted"]["direction"],
            "common_support_direction": item["common_support_adjusted"]["direction"],
            "common_support_magnitude_bucket": (
                item["common_support_adjusted"]["magnitude_bucket"]
            ),
            "direction_changed_on_common_support": (
                item["direction_changed_on_common_support"]
            ),
        }
        for item in features
    }

    result: dict[str, Any] = {
        "status": "common_incidence_support_dry_run_ready",
        "query_executed": False,
        "private_output_written": False,
        "input_schema": source["schema_version"],
        "included_pre_count": support["full_pre_count"],
        "included_post_count": support["full_post_count"],
        "common_support_pre_count": support["restricted_pre_count"],
        "common_support_post_count": support["restricted_post_count"],
        "pre_retention_bucket": support["pre_retention_bucket"],
        "post_retention_bucket": support["post_retention_bucket"],
        "input_rows_excluded_from_analysis": excluded_count,
        "assessed_feature_count": len(adjustment.RADAR_FEATURES),
        "direction_change_count": sum(
            item["direction_changed_on_common_support"] for item in features
        ),
        "feature_screen": feature_screen,
        "effect_values_printed": False,
        "incidence_values_printed": False,
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
            "status": "common_incidence_support_complete",
            "source_schema_version": source["schema_version"],
            "input_rows_excluded_from_analysis": excluded_count,
            "support": support,
            "method": {
                "restriction": "inclusive shared pre/post incidence range",
                "model": "pre-period ordinary least squares feature ~ incidence difference",
                "comparison": "post minus pre median residual shift",
                "minimum_rows_per_period": MIN_ROWS_PER_PERIOD,
                "hypothesis_testing": False,
                "causal_interpretation": False,
                "depth_interpretation": False,
            },
            "features": features,
            "image_ids_included": False,
            "coordinates_included": False,
            "geometry_included": False,
        }
        _atomic_write_json(Path(output_path), private_payload)
        result["status"] = "common_incidence_support_complete"
        result["private_output_written"] = True

    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or execute an offline common-incidence-support assessment."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        help="Required private JSON output with --execute.",
    )
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_common_support_assessment(
            input_path=args.input,
            output_path=args.output,
            execute=args.execute,
        )
    except DepthS1CommonSupportError as exc:
        print(
            json.dumps(
                {
                    "status": "common_incidence_support_failed",
                    "error": str(exc),
                    "effect_values_printed": False,
                    "incidence_values_printed": False,
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
