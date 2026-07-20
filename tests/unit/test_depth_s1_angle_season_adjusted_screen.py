from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import extract_depth_s1_matched_features as extractor
import screen_depth_s1_angle_season_adjusted as adjusted


PRIVATE_ID = "S1A_PRIVATE_CONTROLLED_SCREEN_ID"
PRIVATE_COORDINATE_TEXT = "-97.1234"


def _feature_stats(
    median_by_feature: dict[str, float],
    *,
    count: int = 25,
) -> dict[str, float | int | None]:
    stats: dict[str, float | int | None] = {}
    for feature in extractor.FEATURE_NAMES:
        median = median_by_feature[feature]
        stats[f"{feature}_p25"] = median - 0.1
        stats[f"{feature}_median"] = median
        stats[f"{feature}_p75"] = median + 0.1
        stats[f"{feature}_count"] = count
    return stats


def _usable_row(
    image_id: str,
    *,
    period: str,
    timestamp: str,
    deltas: dict[str, float],
) -> dict[str, object]:
    background_medians = {
        "vv_db": -12.0,
        "vh_db": -18.0,
        "incidence_deg": 35.0,
        "vv_minus_vh_db": 6.0,
        "vh_to_vv_linear_ratio": 0.25,
    }
    site_medians = {
        feature: background_medians[feature] + deltas[feature]
        for feature in extractor.FEATURE_NAMES
    }
    site = _feature_stats(site_medians)
    background = _feature_stats(background_medians)
    stored: dict[str, float] = {}
    for feature in extractor.FEATURE_NAMES:
        for statistic in ("p25", "median", "p75"):
            stored[f"{feature}_{statistic}"] = deltas[feature]
    return {
        "period": period,
        "image_id": image_id,
        "timestamp": timestamp,
        "site": site,
        "background": background,
        "site_minus_background": stored,
    }


def _zero_valid_row(image_id: str, *, period: str, timestamp: str) -> dict[str, object]:
    empty: dict[str, float | int | None] = {}
    for feature in extractor.FEATURE_NAMES:
        empty[f"{feature}_p25"] = None
        empty[f"{feature}_median"] = None
        empty[f"{feature}_p75"] = None
        empty[f"{feature}_count"] = 0
    return {
        "period": period,
        "image_id": image_id,
        "timestamp": timestamp,
        "site": dict(empty),
        "background": dict(empty),
        "site_minus_background": {
            f"{feature}_{statistic}": None
            for feature in extractor.FEATURE_NAMES
            for statistic in ("p25", "median", "p75")
        },
    }


def _payload(*, strong_shift: bool = False, angle_only_shift: bool = False) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    counter = 0
    for month in range(1, 13):
        radians = 2.0 * math.pi * (month - 1) / 12.0
        seasonal = math.sin(radians)
        # Keep a small deterministic second harmonic outside the fitted sine/cosine
        # basis. This prevents the synthetic fixture from collapsing to only two
        # tied residual values, while remaining balanced between pre and post.
        second_harmonic = 0.2 * math.sin(2.0 * radians)
        if angle_only_shift:
            pre_angles = (-1.0, -0.5)
            post_angles = (0.5, 1.0)
        else:
            pre_angles = (-0.5, 0.5)
            post_angles = (-0.5, 0.5)

        for period, year, angles in (
            ("pre", 2018, pre_angles),
            ("post", 2021, post_angles),
        ):
            for day, incidence in enumerate(angles, start=1):
                counter += 1
                post_shift = 5.0 if strong_shift and period == "post" else 0.0
                deltas = {
                    "incidence_deg": incidence,
                    "vv_db": 2.0 * incidence + seasonal + second_harmonic + post_shift,
                    "vh_db": -1.5 * incidence + 0.5 * seasonal,
                    "vv_minus_vh_db": 0.75 * incidence - seasonal,
                    "vh_to_vv_linear_ratio": 0.1 * incidence + 0.05 * seasonal,
                }
                rows.append(
                    _usable_row(
                        f"S1A_SYNTH_{counter:03d}",
                        period=period,
                        timestamp=f"{year}-{month:02d}-{day:02d}T00:00:00+00:00",
                        deltas=deltas,
                    )
                )
    return {
        "schema_version": extractor.PRIVATE_OUTPUT_SCHEMA,
        "status": "matched_s1_feature_extraction_incomplete",
        "selection_contract": {"selected_relative_orbit": 107},
        "rows": rows,
    }


def _write_payload(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_repository_local_input_and_output_are_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "adjusted.json"
    _write_payload(private_input, _payload())

    with pytest.raises(adjusted.DepthS1AdjustedScreenError, match="outside the repository"):
        adjusted.run_adjusted_screen(
            input_path=ROOT / "private.json",
            output_path=private_output,
            permutations=100,
        )
    with pytest.raises(adjusted.DepthS1AdjustedScreenError, match="outside the repository"):
        adjusted.run_adjusted_screen(
            input_path=private_input,
            output_path=ROOT / "adjusted.json",
            permutations=100,
        )


def test_zero_valid_row_is_excluded_without_imputation() -> None:
    payload = _payload()
    rows = payload["rows"]
    assert isinstance(rows, list)
    rows.append(
        _zero_valid_row(
            PRIVATE_ID,
            period="post",
            timestamp="2022-01-01T00:00:00+00:00",
        )
    )

    private_result, console = adjusted.build_adjusted_screen(
        payload,
        permutations=100,
        seed=11,
    )

    assert console["input_row_count"] == 49
    assert console["excluded_row_count"] == 1
    assert console["usable_row_count"] == 48
    assert console["usable_pre_count"] == 24
    assert console["usable_post_count"] == 24
    assert private_result["feature_results"]


def test_strong_post_shift_survives_angle_season_and_holm_controls(tmp_path: Path) -> None:
    input_path = tmp_path / "features.json"
    output_path = tmp_path / "controlled.json"
    _write_payload(input_path, _payload(strong_shift=True))

    result = adjusted.run_adjusted_screen(
        input_path=input_path,
        output_path=output_path,
        permutations=300,
        seed=7,
    )
    private_result = json.loads(output_path.read_text(encoding="utf-8"))

    assert result["decision"] == "angle_season_adjusted_shift_support"
    assert result["support_by_feature"]["vv_db"] is True
    assert result["supported_shift_feature_count"] >= 1
    assert private_result["feature_results"]["vv_db"]["holm_adjusted_p_value"] <= 0.05
    assert private_result["depth_claim_made"] is False


def test_angle_only_raw_shift_disappears_after_adjustment() -> None:
    payload = _payload(angle_only_shift=True)
    private_result, console = adjusted.build_adjusted_screen(
        payload,
        permutations=200,
        seed=19,
    )

    assert console["decision"] == "no_angle_season_adjusted_shift_support"
    assert console["supported_shift_feature_count"] == 0
    assert not any(console["support_by_feature"].values())
    assert all(
        feature_result["holm_adjusted_p_value"] > 0.05
        for feature_result in private_result["feature_results"].values()
    )


def test_holm_adjustment_is_monotone_and_bounded() -> None:
    adjusted_values = adjusted._holm_adjust(
        {"a": 0.01, "b": 0.02, "c": 0.20, "d": 0.90}
    )
    assert adjusted_values["a"] == pytest.approx(0.04)
    assert adjusted_values["b"] == pytest.approx(0.06)
    assert adjusted_values["c"] == pytest.approx(0.40)
    assert adjusted_values["d"] == pytest.approx(0.90)
    assert all(0.0 <= value <= 1.0 for value in adjusted_values.values())


def test_duplicate_identity_is_rejected() -> None:
    payload = _payload()
    rows = payload["rows"]
    assert isinstance(rows, list)
    duplicate = dict(rows[0])
    rows.append(duplicate)

    with pytest.raises(adjusted.DepthS1AdjustedScreenError, match="duplicate"):
        adjusted.build_adjusted_screen(payload, permutations=100)


def test_console_result_leaks_no_private_ids_values_or_paths(tmp_path: Path) -> None:
    payload = _payload()
    rows = payload["rows"]
    assert isinstance(rows, list)
    rows[0]["image_id"] = PRIVATE_ID
    input_path = tmp_path / "private_features.json"
    output_path = tmp_path / "private_controlled.json"
    _write_payload(input_path, payload)

    result = adjusted.run_adjusted_screen(
        input_path=input_path,
        output_path=output_path,
        permutations=100,
        seed=3,
    )
    rendered = json.dumps(result)

    assert PRIVATE_ID not in rendered
    assert PRIVATE_COORDINATE_TEXT not in rendered
    assert str(tmp_path) not in rendered
    assert result["image_ids_printed"] is False
    assert result["feature_values_printed"] is False
    assert result["p_values_printed"] is False
    assert result["depth_claim_made"] is False
