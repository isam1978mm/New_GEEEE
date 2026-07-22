from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import assess_depth_s1_site_background_effect as assessment


def _row(period: str, base: float, *, included: bool = True) -> dict[str, object]:
    deltas: dict[str, float] = {}
    for feature_index, feature in enumerate(assessment.FEATURE_NAMES):
        for statistic_index, statistic in enumerate(assessment.QUANTILE_STATS):
            deltas[f"{feature}_{statistic}"] = base + feature_index + statistic_index / 10.0
    return {
        "period": period,
        "analysis_included": included,
        "site_minus_background": deltas,
    }


def _payload() -> dict[str, object]:
    return {
        "schema_version": assessment.INPUT_SCHEMA,
        "status": "matched_s1_feature_extraction_complete",
        "coordinates_included": False,
        "geometry_included": False,
        "rows": [
            _row("pre", 0.0),
            _row("pre", 0.5),
            _row("pre", 1.0),
            _row("post", 2.0),
            _row("post", 2.5),
            _row("post", 3.0),
            _row("post", 999.0, included=False),
        ],
    }


def _write_input(path: Path, payload: dict[str, object] | None = None) -> None:
    path.write_text(json.dumps(payload or _payload()), encoding="utf-8")


def test_repository_local_paths_are_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    _write_input(private_input)

    with pytest.raises(assessment.DepthS1EffectAssessmentError, match="outside the repository"):
        assessment.run_effect_assessment(input_path=ROOT / "features.json")

    with pytest.raises(assessment.DepthS1EffectAssessmentError, match="outside the repository"):
        assessment.run_effect_assessment(
            input_path=private_input,
            output_path=ROOT / "effect.json",
        )


def test_invalid_schema_and_status_are_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    payload = _payload()
    payload["schema_version"] = "wrong"
    _write_input(private_input, payload)
    with pytest.raises(assessment.DepthS1EffectAssessmentError, match="schema"):
        assessment.run_effect_assessment(input_path=private_input)

    payload = _payload()
    payload["status"] = "matched_s1_feature_extraction_incomplete"
    _write_input(private_input, payload)
    with pytest.raises(assessment.DepthS1EffectAssessmentError, match="not complete"):
        assessment.run_effect_assessment(input_path=private_input)


def test_dry_run_writes_nothing_and_prints_no_numeric_effect_values(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "effect.json"
    _write_input(private_input)

    result = assessment.run_effect_assessment(
        input_path=private_input,
        output_path=private_output,
        execute=False,
    )
    rendered = json.dumps(result)

    assert result["status"] == "descriptive_effect_assessment_dry_run_ready"
    assert result["included_pre_count"] == 3
    assert result["included_post_count"] == 3
    assert result["input_rows_excluded_from_analysis"] == 1
    assert result["private_output_written"] is False
    assert result["effect_values_printed"] is False
    assert "2.5" not in rendered
    assert not private_output.exists()


def test_execute_writes_private_numeric_results_and_safe_console_summary(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "effect.json"
    _write_input(private_input)

    result = assessment.run_effect_assessment(
        input_path=private_input,
        output_path=private_output,
        execute=True,
    )
    private_payload = json.loads(private_output.read_text(encoding="utf-8"))
    rendered = json.dumps(result)

    assert result["status"] == "descriptive_effect_assessment_complete"
    assert result["private_output_written"] is True
    assert result["assessed_feature_count"] == 5
    assert result["quantile_direction_agreement_count"] == 5
    assert private_payload["schema_version"] == assessment.OUTPUT_SCHEMA
    assert private_payload["coordinates_included"] is False
    assert private_payload["geometry_included"] is False
    assert private_payload["image_ids_included"] is False
    assert len(private_payload["features"]) == 5
    assert private_payload["features"][0]["statistics"]["median"]["post_minus_pre_median_shift"] == pytest.approx(2.0)
    assert "2.0" not in rendered
    assert str(tmp_path) not in rendered


def test_missing_included_effect_value_is_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    payload = _payload()
    rows = payload["rows"]
    assert isinstance(rows, list)
    first = rows[0]
    assert isinstance(first, dict)
    deltas = first["site_minus_background"]
    assert isinstance(deltas, dict)
    deltas["vv_db_median"] = None
    _write_input(private_input, payload)

    with pytest.raises(assessment.DepthS1EffectAssessmentError, match="missing or not numeric"):
        assessment.run_effect_assessment(input_path=private_input)


def test_excluded_rows_do_not_influence_effect(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "effect.json"
    _write_input(private_input)

    assessment.run_effect_assessment(
        input_path=private_input,
        output_path=private_output,
        execute=True,
    )
    private_payload = json.loads(private_output.read_text(encoding="utf-8"))

    first_feature = private_payload["features"][0]
    assert first_feature["statistics"]["median"]["post_count"] == 3
    assert first_feature["statistics"]["median"]["post_median"] == pytest.approx(2.6)
