from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import assess_depth_s1_incidence_adjusted_effect as adjustment


def _row(
    period: str,
    incidence: float,
    *,
    period_effect: float,
    included: bool = True,
    include_alternating_noise: bool = True,
) -> dict[str, object]:
    deltas: dict[str, float] = {
        adjustment.INCIDENCE_KEY: incidence,
    }
    noise = (
        (0.1 if incidence % 2 else -0.1)
        if include_alternating_noise
        else 0.0
    )
    for index, feature in enumerate(adjustment.RADAR_FEATURES):
        deltas[f"{feature}_median"] = (
            (index + 1.0) * incidence
            + period_effect
            + noise
        )
    return {
        "period": period,
        "analysis_included": included,
        "site_minus_background": deltas,
    }


def _payload(
    *,
    post_effect: float = 2.0,
    include_alternating_noise: bool = True,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for incidence in (0.0, 1.0, 2.0, 3.0):
        rows.append(
            _row(
                "pre",
                incidence,
                period_effect=0.0,
                include_alternating_noise=include_alternating_noise,
            )
        )
    for incidence in (1.0, 2.0, 3.0, 4.0):
        rows.append(
            _row(
                "post",
                incidence,
                period_effect=post_effect,
                include_alternating_noise=include_alternating_noise,
            )
        )
    rows.append(_row("post", 999.0, period_effect=999.0, included=False))
    return {
        "schema_version": adjustment.INPUT_SCHEMA,
        "status": "matched_s1_feature_extraction_complete",
        "coordinates_included": False,
        "geometry_included": False,
        "rows": rows,
    }


def _write(path: Path, payload: dict[str, object] | None = None) -> None:
    path.write_text(json.dumps(payload or _payload()), encoding="utf-8")


def test_repository_local_paths_are_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    _write(private_input)

    with pytest.raises(adjustment.DepthS1IncidenceAdjustmentError, match="outside the repository"):
        adjustment.run_incidence_adjusted_assessment(input_path=ROOT / "features.json")

    with pytest.raises(adjustment.DepthS1IncidenceAdjustmentError, match="outside the repository"):
        adjustment.run_incidence_adjusted_assessment(
            input_path=private_input,
            output_path=ROOT / "adjusted.json",
        )


def test_invalid_schema_and_status_are_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    payload = _payload()
    payload["schema_version"] = "wrong"
    _write(private_input, payload)
    with pytest.raises(adjustment.DepthS1IncidenceAdjustmentError, match="schema"):
        adjustment.run_incidence_adjusted_assessment(input_path=private_input)

    payload = _payload()
    payload["status"] = "matched_s1_feature_extraction_incomplete"
    _write(private_input, payload)
    with pytest.raises(adjustment.DepthS1IncidenceAdjustmentError, match="not complete"):
        adjustment.run_incidence_adjusted_assessment(input_path=private_input)


def test_dry_run_is_private_and_writes_nothing(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "adjusted.json"
    _write(private_input)

    result = adjustment.run_incidence_adjusted_assessment(
        input_path=private_input,
        output_path=private_output,
        execute=False,
    )
    rendered = json.dumps(result)

    assert result["status"] == "incidence_adjusted_effect_dry_run_ready"
    assert result["included_pre_count"] == 4
    assert result["included_post_count"] == 4
    assert result["input_rows_excluded_from_analysis"] == 1
    assert result["private_output_written"] is False
    assert result["effect_values_printed"] is False
    assert "2.0" not in rendered
    assert str(tmp_path) not in rendered
    assert not private_output.exists()


def test_execute_writes_adjusted_private_results(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "adjusted.json"
    _write(private_input)

    result = adjustment.run_incidence_adjusted_assessment(
        input_path=private_input,
        output_path=private_output,
        execute=True,
    )
    payload = json.loads(private_output.read_text(encoding="utf-8"))

    assert result["status"] == "incidence_adjusted_effect_complete"
    assert result["private_output_written"] is True
    assert result["adjusted_feature_count"] == 4
    assert payload["schema_version"] == adjustment.OUTPUT_SCHEMA
    assert payload["image_ids_included"] is False
    assert payload["coordinates_included"] is False
    assert payload["geometry_included"] is False
    assert len(payload["features"]) == 4
    assert payload["features"][0]["adjusted"]["direction"] == "increase"


def test_adjustment_removes_pure_incidence_shift(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "adjusted.json"
    payload = _payload(
        post_effect=0.0,
        include_alternating_noise=False,
    )
    _write(private_input, payload)

    adjustment.run_incidence_adjusted_assessment(
        input_path=private_input,
        output_path=private_output,
        execute=True,
    )
    result = json.loads(private_output.read_text(encoding="utf-8"))

    for feature in result["features"]:
        assert feature["unadjusted"]["direction"] == "increase"
        assert feature["adjusted"]["direction"] == "no_material_numeric_change"
        assert feature["direction_changed_after_adjustment"] is True


def test_missing_included_value_is_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    payload = _payload()
    rows = payload["rows"]
    assert isinstance(rows, list)
    first = rows[0]
    assert isinstance(first, dict)
    deltas = first["site_minus_background"]
    assert isinstance(deltas, dict)
    deltas["vv_db_median"] = None
    _write(private_input, payload)

    with pytest.raises(adjustment.DepthS1IncidenceAdjustmentError, match="missing or not numeric"):
        adjustment.run_incidence_adjusted_assessment(input_path=private_input)


def test_zero_pre_incidence_variation_is_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    payload = _payload()
    rows = payload["rows"]
    assert isinstance(rows, list)
    for row in rows:
        assert isinstance(row, dict)
        if row["period"] == "pre":
            deltas = row["site_minus_background"]
            assert isinstance(deltas, dict)
            deltas[adjustment.INCIDENCE_KEY] = 1.0
    _write(private_input, payload)

    with pytest.raises(adjustment.DepthS1IncidenceAdjustmentError, match="no usable variation"):
        adjustment.run_incidence_adjusted_assessment(input_path=private_input)
