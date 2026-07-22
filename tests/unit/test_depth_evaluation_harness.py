from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import depth_evaluation_harness as harness


def _row(
    index: int,
    *,
    split: str,
    truth: str,
    prediction: str,
    group_id: str | None = None,
    supported: bool = True,
    soil: str = "soil_a",
) -> dict[str, object]:
    return {
        "fixture_kind": "synthetic",
        "record_id": f"fake_record_{index}",
        "site_id": f"fake_site_{index}",
        "group_id": group_id or f"fake_group_{index}",
        "split": split,
        "truth_class": truth,
        "prediction_class": prediction,
        "supported_condition": supported,
        "finding_family": "reference_structure",
        "soil_or_surface_type": soil,
        "moisture_or_season": "dry",
        "terrain_class": "flat",
    }


def _rows() -> list[dict[str, object]]:
    return [
        _row(1, split="train", truth="shallow", prediction="shallow", soil="soil_a"),
        _row(2, split="train", truth="medium", prediction="medium", soil="soil_a"),
        _row(3, split="validation", truth="deep", prediction="deep", soil="soil_b"),
        _row(4, split="validation", truth="shallow", prediction="medium", soil="soil_b"),
        _row(5, split="holdout", truth="deep", prediction=harness.ABSTAIN_LABEL, supported=False),
        _row(6, split="holdout", truth="medium", prediction="medium"),
    ]


def test_rejects_non_synthetic_rows() -> None:
    rows = _rows()
    rows[0]["fixture_kind"] = "private"

    with pytest.raises(harness.DepthHarnessError, match="synthetic fixtures only"):
        harness.evaluate_synthetic_fixture(rows)


def test_rejects_group_leakage() -> None:
    rows = _rows()
    rows[0]["group_id"] = "shared"
    rows[2]["group_id"] = "shared"

    with pytest.raises(harness.DepthHarnessError, match="group leakage"):
        harness.evaluate_synthetic_fixture(rows)


def test_unsupported_conditions_must_abstain() -> None:
    rows = _rows()
    rows[4]["prediction_class"] = "deep"

    with pytest.raises(harness.DepthHarnessError, match="must abstain"):
        harness.evaluate_synthetic_fixture(rows)


def test_classification_metrics_and_abstention() -> None:
    result = harness.evaluate_synthetic_fixture(_rows())
    metrics = result["classification"]

    assert metrics["record_count"] == 6
    assert metrics["non_abstained_count"] == 5
    assert metrics["abstention_count"] == 1
    assert metrics["coverage"] == pytest.approx(5 / 6)
    assert metrics["one_class_off_rate"] == pytest.approx(1 / 5)
    assert metrics["two_class_off_rate"] == 0.0
    assert metrics["confusion_matrix"]["shallow"]["medium"] == 1


def test_interval_metrics() -> None:
    rows = _rows()
    rows[0].update({"truth_depth_m": 1.0, "interval_low_m": 0.5, "interval_high_m": 1.5})
    rows[1].update({"truth_depth_m": 3.0, "interval_low_m": 1.0, "interval_high_m": 2.0})

    intervals = harness.evaluate_synthetic_fixture(rows)["intervals"]

    assert intervals["eligible_interval_count"] == 2
    assert intervals["interval_coverage"] == 0.5
    assert intervals["mean_interval_width_m"] == 1.0
    assert intervals["median_interval_width_m"] == 1.0


def test_subgroups_suppress_small_categories() -> None:
    rows = _rows()
    rows[-1]["soil_or_surface_type"] = "rare_soil"

    report = harness.evaluate_synthetic_fixture(rows)["subgroups"]["soil_or_surface_type"]

    assert "rare_soil" not in report["groups"]
    assert report["suppressed_record_count"] == 1


def test_aggregate_output_contains_no_identity_fields() -> None:
    result = harness.evaluate_synthetic_fixture(_rows())
    serialized = json.dumps(result)

    for field in harness.IDENTITY_FIELDS:
        assert field not in serialized
    assert result["private_rows_printed"] is False
    assert result["scientific_validation_run"] is False


def test_majority_baseline_uses_deterministic_class_order_for_ties() -> None:
    train = [
        _row(1, split="train", truth="shallow", prediction="shallow"),
        _row(2, split="train", truth="medium", prediction="medium"),
    ]

    assert harness.majority_class_baseline(train, _rows()[:2]) == ["shallow", "shallow"]


def test_stratified_random_baseline_is_deterministic() -> None:
    train = _rows()[:4]

    first = harness.stratified_random_baseline(train, _rows(), seed=17)
    second = harness.stratified_random_baseline(train, _rows(), seed=17)

    assert first == second


def test_one_feature_threshold_baseline() -> None:
    rows = [{"signal": 1.0}, {"signal": 2.0}, {"signal": 3.0}]

    assert harness.one_feature_threshold_baseline(
        rows,
        feature_name="signal",
        lower_threshold=1.5,
        upper_threshold=2.5,
    ) == ["shallow", "medium", "deep"]


def test_median_and_relative_midpoint_baselines() -> None:
    train = [{"truth_depth_m": 1.0}, {"truth_depth_m": 3.0}, {"truth_depth_m": 8.0}]
    eval_rows = [{}, {}]
    classified = [
        {"prediction_class": "shallow"},
        {"prediction_class": "deep"},
    ]

    assert harness.median_depth_baseline(train, eval_rows) == [3.0, 3.0]
    assert harness.relative_midpoint_baseline(
        classified,
        midpoints_m={"shallow": 1.0, "medium": 3.0, "deep": 6.0},
    ) == [1.0, 6.0]
