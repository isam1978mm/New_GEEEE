"""Run a private incidence-angle and season adjusted Sentinel-1 pre/post screen.

The input and numeric output must remain outside Git. Rows with zero valid pixels
are excluded without imputation. Exact coefficients, shifts, and p-values are
written only to the private output. Console output is aggregate-only.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

import extract_depth_s1_matched_features as extractor
import screen_depth_s1_matched_feature_changes as descriptive


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_SCHEMA = "depth_s1_angle_season_adjusted_screen_v1"
SIGNAL_FEATURES = tuple(
    feature for feature in extractor.FEATURE_NAMES if feature != "incidence_deg"
)
DEFAULT_PERMUTATIONS = 5000
DEFAULT_SEED = 20260720
DEFAULT_ALPHA = 0.05
ZERO_TOLERANCE = 1e-12


class DepthS1AdjustedScreenError(ValueError):
    """Raised when the private controlled screen cannot proceed safely."""


def _require_outside_repo(path: Path, label: str) -> None:
    candidate = Path(path).expanduser().resolve(strict=False)
    repository = REPO_ROOT.resolve()
    if candidate == repository or repository in candidate.parents:
        raise DepthS1AdjustedScreenError(f"{label} must remain outside the repository")


def _read_private_payload(path: Path) -> dict[str, Any]:
    path = Path(path)
    _require_outside_repo(path, "private matched feature input")
    if not path.is_file():
        raise DepthS1AdjustedScreenError("private matched feature input is missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DepthS1AdjustedScreenError(
            "private matched feature input is unreadable or invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise DepthS1AdjustedScreenError("private matched feature input must be a JSON object")
    if payload.get("schema_version") != extractor.PRIVATE_OUTPUT_SCHEMA:
        raise DepthS1AdjustedScreenError("private matched feature schema is unsupported")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise DepthS1AdjustedScreenError("private matched feature rows must not be empty")
    return payload


def _parse_month(value: Any) -> int:
    text = str(value or "").strip()
    if not text:
        raise DepthS1AdjustedScreenError("private matched feature row contains a missing timestamp")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DepthS1AdjustedScreenError(
            "private matched feature row contains an invalid timestamp"
        ) from exc
    return parsed.month


def _collect_usable_rows(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise DepthS1AdjustedScreenError("private matched feature rows must not be empty")

    seen_ids: set[str] = set()
    usable: list[dict[str, Any]] = []
    counts = {
        "input_pre": 0,
        "input_post": 0,
        "excluded_pre": 0,
        "excluded_post": 0,
    }

    for row in rows:
        if not isinstance(row, dict):
            raise DepthS1AdjustedScreenError("private matched feature output contains an invalid row")
        image_id = str(row.get("image_id") or "").strip()
        if not image_id:
            raise DepthS1AdjustedScreenError(
                "private matched feature output contains a missing image identity"
            )
        if image_id in seen_ids:
            raise DepthS1AdjustedScreenError(
                "private matched feature output contains a duplicate image identity"
            )
        seen_ids.add(image_id)

        try:
            period, deltas, exclusion_reason = descriptive._validate_row_and_extract_deltas(row)
        except descriptive.DepthS1DescriptiveScreenError as exc:
            raise DepthS1AdjustedScreenError(str(exc)) from exc
        counts[f"input_{period}"] += 1
        if exclusion_reason is not None:
            if exclusion_reason != "zero_valid_pixels":
                raise DepthS1AdjustedScreenError("unsupported controlled-screen exclusion reason")
            counts[f"excluded_{period}"] += 1
            continue
        if deltas is None:
            raise DepthS1AdjustedScreenError("usable controlled-screen row is missing differences")

        usable.append(
            {
                "period": period,
                "month": _parse_month(row.get("timestamp")),
                "deltas": deltas,
            }
        )

    usable_pre = counts["input_pre"] - counts["excluded_pre"]
    usable_post = counts["input_post"] - counts["excluded_post"]
    if usable_pre < 2 or usable_post < 2:
        raise DepthS1AdjustedScreenError(
            "controlled screen requires at least two usable pre and post rows"
        )
    return usable, counts


def _design_matrix(rows: list[dict[str, Any]]) -> np.ndarray:
    incidence = np.asarray(
        [float(row["deltas"]["incidence_deg"]) for row in rows],
        dtype=np.float64,
    )
    months = np.asarray([int(row["month"]) for row in rows], dtype=np.float64)
    radians = 2.0 * math.pi * (months - 1.0) / 12.0
    return np.column_stack(
        [
            np.ones(len(rows), dtype=np.float64),
            incidence,
            np.sin(radians),
            np.cos(radians),
        ]
    )


def _residualize(values: np.ndarray, design: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    coefficients, _, rank, _ = np.linalg.lstsq(design, values, rcond=None)
    residuals = values - design @ coefficients
    if not np.all(np.isfinite(residuals)):
        raise DepthS1AdjustedScreenError("controlled screen produced non-finite residuals")
    return residuals, coefficients, int(rank)


def _direction(value: float) -> str:
    if value > ZERO_TOLERANCE:
        return "positive"
    if value < -ZERO_TOLERANCE:
        return "negative"
    return "zero"


def _build_permuted_labels(
    labels: np.ndarray,
    months: np.ndarray,
    *,
    permutations: int,
    seed: int,
) -> tuple[np.ndarray, int]:
    if permutations < 100:
        raise DepthS1AdjustedScreenError("permutations must be at least 100")
    rng = np.random.default_rng(seed)
    unique_months = sorted({int(value) for value in months.tolist()})
    groups = [np.flatnonzero(months == month) for month in unique_months]
    mixed_groups = [
        indices
        for indices in groups
        if np.any(labels[indices]) and np.any(~labels[indices])
    ]
    if not mixed_groups:
        raise DepthS1AdjustedScreenError(
            "controlled screen requires at least one month containing both pre and post rows"
        )

    permuted = np.empty((permutations, len(labels)), dtype=bool)
    for permutation_index in range(permutations):
        shuffled = labels.copy()
        for indices in groups:
            group_labels = shuffled[indices].copy()
            rng.shuffle(group_labels)
            shuffled[indices] = group_labels
        permuted[permutation_index] = shuffled
    return permuted, len(mixed_groups)


def _permutation_p_value(
    residuals: np.ndarray,
    labels: np.ndarray,
    permuted_labels: np.ndarray,
) -> tuple[float, float]:
    observed = float(np.median(residuals[labels]) - np.median(residuals[~labels]))
    exceedances = 0
    for permuted in permuted_labels:
        statistic = float(
            np.median(residuals[permuted]) - np.median(residuals[~permuted])
        )
        if abs(statistic) >= abs(observed) - ZERO_TOLERANCE:
            exceedances += 1
    p_value = (exceedances + 1.0) / (len(permuted_labels) + 1.0)
    return observed, float(p_value)


def _holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values, key=lambda feature: (p_values[feature], feature))
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for index, feature in enumerate(ordered):
        candidate = min(1.0, (total - index) * p_values[feature])
        running = max(running, candidate)
        adjusted[feature] = min(1.0, running)
    return adjusted


def build_adjusted_screen(
    payload: dict[str, Any],
    *,
    permutations: int = DEFAULT_PERMUTATIONS,
    seed: int = DEFAULT_SEED,
    alpha: float = DEFAULT_ALPHA,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not (0.0 < alpha < 1.0):
        raise DepthS1AdjustedScreenError("alpha must be between zero and one")

    rows, counts = _collect_usable_rows(payload)
    labels = np.asarray([row["period"] == "post" for row in rows], dtype=bool)
    months = np.asarray([int(row["month"]) for row in rows], dtype=np.int16)
    design = _design_matrix(rows)
    permuted_labels, mixed_month_count = _build_permuted_labels(
        labels,
        months,
        permutations=permutations,
        seed=seed,
    )

    raw_results: dict[str, dict[str, Any]] = {}
    p_values: dict[str, float] = {}
    for feature in SIGNAL_FEATURES:
        values = np.asarray(
            [float(row["deltas"][feature]) for row in rows],
            dtype=np.float64,
        )
        residuals, coefficients, design_rank = _residualize(values, design)
        shift, p_value = _permutation_p_value(residuals, labels, permuted_labels)
        p_values[feature] = p_value
        raw_results[feature] = {
            "adjusted_post_minus_pre_median_shift": shift,
            "shift_direction": _direction(shift),
            "permutation_p_value": p_value,
            "design_rank": design_rank,
            "control_coefficients": {
                "intercept": float(coefficients[0]),
                "incidence_delta": float(coefficients[1]),
                "season_sine": float(coefficients[2]),
                "season_cosine": float(coefficients[3]),
            },
        }

    adjusted_p_values = _holm_adjust(p_values)
    support_by_feature: dict[str, bool] = {}
    direction_by_feature: dict[str, str] = {}
    for feature in SIGNAL_FEATURES:
        adjusted_p = adjusted_p_values[feature]
        supported = adjusted_p <= alpha
        raw_results[feature]["holm_adjusted_p_value"] = adjusted_p
        raw_results[feature]["supported_at_alpha"] = supported
        support_by_feature[feature] = supported
        direction_by_feature[feature] = raw_results[feature]["shift_direction"]

    supported_count = sum(support_by_feature.values())
    decision = (
        "angle_season_adjusted_shift_support"
        if supported_count > 0
        else "no_angle_season_adjusted_shift_support"
    )
    usable_pre = counts["input_pre"] - counts["excluded_pre"]
    usable_post = counts["input_post"] - counts["excluded_post"]

    private_output = {
        "schema_version": OUTPUT_SCHEMA,
        "status": "matched_s1_angle_season_adjusted_screen_complete",
        "decision": decision,
        "source_schema_version": payload.get("schema_version"),
        "selection_contract": payload.get("selection_contract"),
        "input_row_count": counts["input_pre"] + counts["input_post"],
        "excluded_row_count": counts["excluded_pre"] + counts["excluded_post"],
        "usable_row_count": len(rows),
        "usable_pre_count": usable_pre,
        "usable_post_count": usable_post,
        "control_contract": {
            "incidence_controlled": True,
            "season_controlled": True,
            "season_basis": "month_of_year_sine_cosine",
            "test": "month_stratified_permutation_of_adjusted_median_shift",
            "permutations": permutations,
            "seed": seed,
            "alpha": alpha,
            "multiple_testing": "Holm",
            "mixed_month_count": mixed_month_count,
        },
        "feature_results": raw_results,
        "image_ids_included": False,
        "coordinates_included": False,
        "geometry_included": False,
        "causal_test_run": False,
        "significance_test_run": True,
        "scientific_validation_run": False,
        "depth_claim_made": False,
        "training_started": False,
        "app_depth_enabled": False,
    }
    console_result = {
        "status": "matched_s1_angle_season_adjusted_screen_complete",
        "decision": decision,
        "input_row_count": counts["input_pre"] + counts["input_post"],
        "excluded_row_count": counts["excluded_pre"] + counts["excluded_post"],
        "usable_row_count": len(rows),
        "usable_pre_count": usable_pre,
        "usable_post_count": usable_post,
        "tested_feature_count": len(SIGNAL_FEATURES),
        "incidence_controlled": True,
        "season_controlled": True,
        "mixed_month_count": mixed_month_count,
        "supported_shift_feature_count": supported_count,
        "support_by_feature": support_by_feature,
        "adjusted_shift_direction_by_feature": direction_by_feature,
        "private_output_written": False,
        "image_ids_printed": False,
        "coordinates_printed": False,
        "geometry_printed": False,
        "private_paths_printed": False,
        "feature_values_printed": False,
        "p_values_printed": False,
        "causal_test_run": False,
        "significance_test_run": True,
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
        raise DepthS1AdjustedScreenError("private controlled-screen output could not be written") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def run_adjusted_screen(
    *,
    input_path: Path,
    output_path: Path,
    permutations: int = DEFAULT_PERMUTATIONS,
    seed: int = DEFAULT_SEED,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, Any]:
    _require_outside_repo(output_path, "private controlled-screen output")
    if Path(input_path).expanduser().resolve(strict=False) == Path(output_path).expanduser().resolve(strict=False):
        raise DepthS1AdjustedScreenError("input and output must use different files")
    payload = _read_private_payload(input_path)
    private_output, console_result = build_adjusted_screen(
        payload,
        permutations=permutations,
        seed=seed,
        alpha=alpha,
    )
    _atomic_write_json(output_path, private_output)
    console_result["private_output_written"] = True
    return console_result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a private incidence-angle and season adjusted Sentinel-1 screen."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--permutations", type=int, default=DEFAULT_PERMUTATIONS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_adjusted_screen(
            input_path=args.input,
            output_path=args.output,
            permutations=args.permutations,
            seed=args.seed,
            alpha=args.alpha,
        )
    except DepthS1AdjustedScreenError as exc:
        print(
            json.dumps(
                {
                    "status": "matched_s1_angle_season_adjusted_screen_failed",
                    "error": str(exc),
                    "image_ids_printed": False,
                    "coordinates_printed": False,
                    "geometry_printed": False,
                    "private_paths_printed": False,
                    "feature_values_printed": False,
                    "p_values_printed": False,
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
