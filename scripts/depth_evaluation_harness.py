from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

CLASS_ORDER = ("shallow", "medium", "deep")
ABSTAIN_LABEL = "insufficient_data"
ACTIVE_SPLITS = ("train", "validation", "holdout")
ALLOWED_SUBGROUP_FIELDS = (
    "finding_family",
    "soil_or_surface_type",
    "moisture_or_season",
    "terrain_class",
)
IDENTITY_FIELDS = {
    "record_id",
    "site_id",
    "feature_id",
    "group_id",
    "source_reference",
    "coordinates",
    "latitude",
    "longitude",
}


class DepthHarnessError(ValueError):
    """Raised when a synthetic evaluation fixture violates the frozen contract."""


def _as_float(value: Any, *, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise DepthHarnessError(f"{field} must be numeric") from exc
    if not math.isfinite(result):
        raise DepthHarnessError(f"{field} must be finite")
    return result


def _require_synthetic_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise DepthHarnessError("at least one synthetic row is required")
    for row in rows:
        if row.get("fixture_kind") != "synthetic":
            raise DepthHarnessError("repository harness accepts synthetic fixtures only")


def validate_group_separation(rows: Sequence[Mapping[str, Any]]) -> None:
    """Reject any physical group assigned to more than one active split."""

    group_splits: dict[str, set[str]] = {}
    for row in rows:
        split = str(row.get("split", ""))
        if split not in ACTIVE_SPLITS:
            continue
        group_id = str(row.get("group_id", "")).strip()
        if not group_id:
            raise DepthHarnessError("active rows require group_id")
        group_splits.setdefault(group_id, set()).add(split)

    leaked = sorted(group_id for group_id, splits in group_splits.items() if len(splits) > 1)
    if leaked:
        raise DepthHarnessError(f"group leakage across active splits: {len(leaked)} group(s)")


def _truth_counts(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        truth = str(row.get("truth_class", ""))
        if truth not in CLASS_ORDER:
            raise DepthHarnessError(f"truth_class must be one of {CLASS_ORDER}")
        counts[truth] += 1
    return counts


def majority_class_baseline(
    train_rows: Sequence[Mapping[str, Any]],
    eval_rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    """Predict the most common training class with deterministic tie breaking."""

    counts = _truth_counts(train_rows)
    winner = max(CLASS_ORDER, key=lambda label: (counts[label], -CLASS_ORDER.index(label)))
    return [winner for _ in eval_rows]


def stratified_random_baseline(
    train_rows: Sequence[Mapping[str, Any]],
    eval_rows: Sequence[Mapping[str, Any]],
    *,
    seed: int,
) -> list[str]:
    """Sample classes from frozen training prevalence using a local deterministic RNG."""

    counts = _truth_counts(train_rows)
    total = sum(counts.values())
    if total == 0:
        raise DepthHarnessError("training rows are required")
    weights = [counts[label] / total for label in CLASS_ORDER]
    rng = random.Random(seed)
    return rng.choices(CLASS_ORDER, weights=weights, k=len(eval_rows))


def one_feature_threshold_baseline(
    rows: Sequence[Mapping[str, Any]],
    *,
    feature_name: str,
    lower_threshold: float,
    upper_threshold: float,
) -> list[str]:
    """Apply two already-frozen thresholds; threshold selection is outside this helper."""

    if lower_threshold >= upper_threshold:
        raise DepthHarnessError("lower_threshold must be less than upper_threshold")
    predictions: list[str] = []
    for row in rows:
        value = _as_float(row.get(feature_name), field=feature_name)
        if value <= lower_threshold:
            predictions.append("shallow")
        elif value <= upper_threshold:
            predictions.append("medium")
        else:
            predictions.append("deep")
    return predictions


def median_depth_baseline(
    train_rows: Sequence[Mapping[str, Any]],
    eval_rows: Sequence[Mapping[str, Any]],
) -> list[float]:
    depths = [_as_float(row.get("truth_depth_m"), field="truth_depth_m") for row in train_rows]
    if not depths:
        raise DepthHarnessError("training depths are required")
    value = float(statistics.median(depths))
    return [value for _ in eval_rows]


def relative_midpoint_baseline(
    rows: Sequence[Mapping[str, Any]],
    *,
    midpoints_m: Mapping[str, float],
) -> list[float]:
    missing = [label for label in CLASS_ORDER if label not in midpoints_m]
    if missing:
        raise DepthHarnessError("midpoints_m must define every relative class")
    return [
        _as_float(midpoints_m[str(row.get("prediction_class"))], field="midpoint")
        for row in rows
    ]


def _confusion_matrix(
    pairs: Sequence[tuple[str, str]],
) -> dict[str, dict[str, int]]:
    matrix = {truth: {pred: 0 for pred in CLASS_ORDER} for truth in CLASS_ORDER}
    for truth, prediction in pairs:
        matrix[truth][prediction] += 1
    return matrix


def _classification_metrics(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    pairs: list[tuple[str, str]] = []
    abstained = 0
    for row in rows:
        truth = str(row.get("truth_class", ""))
        prediction = str(row.get("prediction_class", ""))
        if truth not in CLASS_ORDER:
            raise DepthHarnessError(f"truth_class must be one of {CLASS_ORDER}")
        if prediction == ABSTAIN_LABEL:
            abstained += 1
            continue
        if prediction not in CLASS_ORDER:
            raise DepthHarnessError(f"prediction_class must be one of {CLASS_ORDER} or abstain")
        pairs.append((truth, prediction))

    matrix = _confusion_matrix(pairs)
    per_class: dict[str, dict[str, float | int]] = {}
    recalls: list[float] = []
    f1_values: list[float] = []
    for label in CLASS_ORDER:
        tp = matrix[label][label]
        support = sum(matrix[label].values())
        predicted = sum(matrix[truth][label] for truth in CLASS_ORDER)
        recall = tp / support if support else 0.0
        precision = tp / predicted if predicted else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        per_class[label] = {
            "support": support,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
        recalls.append(recall)
        f1_values.append(f1)

    one_class_off = 0
    two_class_off = 0
    shallow_deep = 0
    for truth, prediction in pairs:
        distance = abs(CLASS_ORDER.index(truth) - CLASS_ORDER.index(prediction))
        if distance == 1:
            one_class_off += 1
        elif distance >= 2:
            two_class_off += 1
            shallow_deep += 1

    non_abstained = len(pairs)
    total = len(rows)
    return {
        "record_count": total,
        "non_abstained_count": non_abstained,
        "abstention_count": abstained,
        "abstention_rate": abstained / total if total else 0.0,
        "coverage": non_abstained / total if total else 0.0,
        "balanced_accuracy": statistics.fmean(recalls),
        "macro_f1": statistics.fmean(f1_values),
        "one_class_off_rate": one_class_off / non_abstained if non_abstained else 0.0,
        "two_class_off_rate": two_class_off / non_abstained if non_abstained else 0.0,
        "shallow_deep_confusion_rate": shallow_deep / non_abstained if non_abstained else 0.0,
        "per_class": per_class,
        "confusion_matrix": matrix,
    }


def _interval_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    widths: list[float] = []
    covered = 0
    eligible = 0
    for row in rows:
        fields = (row.get("truth_depth_m"), row.get("interval_low_m"), row.get("interval_high_m"))
        if all(value in (None, "") for value in fields):
            continue
        if any(value in (None, "") for value in fields):
            raise DepthHarnessError("numerical interval rows require truth, low, and high values")
        truth = _as_float(fields[0], field="truth_depth_m")
        low = _as_float(fields[1], field="interval_low_m")
        high = _as_float(fields[2], field="interval_high_m")
        if low < 0 or high < low:
            raise DepthHarnessError("interval bounds must be nonnegative and ordered")
        eligible += 1
        widths.append(high - low)
        if low <= truth <= high:
            covered += 1

    if not eligible:
        return {
            "eligible_interval_count": 0,
            "interval_coverage": None,
            "mean_interval_width_m": None,
            "median_interval_width_m": None,
        }
    return {
        "eligible_interval_count": eligible,
        "interval_coverage": covered / eligible,
        "mean_interval_width_m": statistics.fmean(widths),
        "median_interval_width_m": statistics.median(widths),
    }


def _validate_refusal_contract(rows: Sequence[Mapping[str, Any]]) -> None:
    for row in rows:
        supported = row.get("supported_condition", True)
        if supported is False and row.get("prediction_class") != ABSTAIN_LABEL:
            raise DepthHarnessError("unsupported conditions must abstain")


def _subgroup_report(
    rows: Sequence[Mapping[str, Any]],
    *,
    subgroup_fields: Iterable[str],
    minimum_count: int,
) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for field in subgroup_fields:
        if field not in ALLOWED_SUBGROUP_FIELDS:
            raise DepthHarnessError(f"unsupported subgroup field: {field}")
        grouped: dict[str, list[Mapping[str, Any]]] = {}
        for row in rows:
            value = str(row.get(field, "unknown") or "unknown")
            grouped.setdefault(value, []).append(row)
        visible: dict[str, Any] = {}
        suppressed = 0
        for value in sorted(grouped):
            group_rows = grouped[value]
            if len(group_rows) < minimum_count:
                suppressed += len(group_rows)
                continue
            visible[value] = _classification_metrics(group_rows)
        report[field] = {
            "groups": visible,
            "suppressed_record_count": suppressed,
            "minimum_count": minimum_count,
        }
    return report


def evaluate_synthetic_fixture(
    rows: Sequence[Mapping[str, Any]],
    *,
    subgroup_fields: Sequence[str] = ALLOWED_SUBGROUP_FIELDS,
    minimum_subgroup_count: int = 2,
) -> dict[str, Any]:
    """Evaluate fake rows while returning aggregate-only software-test output."""

    _require_synthetic_rows(rows)
    validate_group_separation(rows)
    _validate_refusal_contract(rows)
    if minimum_subgroup_count < 2:
        raise DepthHarnessError("minimum_subgroup_count must be at least 2")

    classification = _classification_metrics(rows)
    intervals = _interval_metrics(rows)
    subgroups = _subgroup_report(
        rows,
        subgroup_fields=subgroup_fields,
        minimum_count=minimum_subgroup_count,
    )
    result = {
        "status": "software_fixture_passed",
        "fixture_kind": "synthetic",
        "scientific_validation_run": False,
        "training_started": False,
        "private_rows_printed": False,
        "classification": classification,
        "intervals": intervals,
        "subgroups": subgroups,
    }
    serialized = json.dumps(result, sort_keys=True)
    if any(field in serialized for field in IDENTITY_FIELDS):
        raise DepthHarnessError("aggregate output contains an identity field")
    return result


def _load_rows(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise DepthHarnessError("input must be a JSON list of objects")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Run synthetic-only depth evaluation harness")
    parser.add_argument("input_json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = evaluate_synthetic_fixture(_load_rows(args.input_json))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
