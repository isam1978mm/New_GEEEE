from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import assess_depth_s1_common_incidence_support as common


def _row(
    period: str,
    incidence_value: float,
    period_effect: float,
    *,
    included: bool = True,
) -> dict[str, object]:
    deltas: dict[str, float] = {
        common.adjustment.INCIDENCE_KEY: incidence_value,
    }
    for index, feature in enumerate(common.adjustment.RADAR_FEATURES):
        deltas[f"{feature}_median"] = (
            (index + 1.0) * incidence_value + period_effect
        )
    return {
        "period": period,
        "analysis_included": included,
        "site_minus_background": deltas,
    }


def _payload(
    *,
    post_effect: float = 1.0,
    pre_values: tuple[float, ...] = tuple(float(value) for value in range(12)),
    post_values: tuple[float, ...] = tuple(float(value) for value in range(4, 16)),
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    rows.extend(_row("pre", value, 0.0) for value in pre_values)
    rows.extend(_row("post", value, post_effect) for value in post_values)
    rows.append(_row("post", 999.0, 999.0, included=False))
    return {
        "schema_version": common.INPUT_SCHEMA,
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

    with pytest.raises(common.DepthS1CommonSupportError, match="outside the repository"):
        common.run_common_support_assessment(input_path=ROOT / "features.json")

    with pytest.raises(common.DepthS1CommonSupportError, match="outside the repository"):
        common.run_common_support_assessment(
            input_path=private_input,
            output_path=ROOT / "support.json",
        )


def test_dry_run_reports_common_support_without_writing(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "support.json"
    _write(private_input)

    result = common.run_common_support_assessment(
        input_path=private_input,
        output_path=private_output,
        execute=False,
    )
    rendered = json.dumps(result)

    assert result["status"] == "common_incidence_support_dry_run_ready"
    assert result["included_pre_count"] == 12
    assert result["included_post_count"] == 12
    assert result["common_support_pre_count"] == 8
    assert result["common_support_post_count"] == 8
    assert result["input_rows_excluded_from_analysis"] == 1
    assert result["private_output_written"] is False
    assert result["effect_values_printed"] is False
    assert "4.0" not in rendered
    assert str(tmp_path) not in rendered
    assert not private_output.exists()


def test_execute_writes_private_support_results(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "support.json"
    _write(private_input)

    result = common.run_common_support_assessment(
        input_path=private_input,
        output_path=private_output,
        execute=True,
    )
    payload = json.loads(private_output.read_text(encoding="utf-8"))

    assert result["status"] == "common_incidence_support_complete"
    assert result["private_output_written"] is True
    assert payload["schema_version"] == common.OUTPUT_SCHEMA
    assert payload["image_ids_included"] is False
    assert payload["coordinates_included"] is False
    assert payload["geometry_included"] is False
    assert len(payload["features"]) == 4
    for feature in payload["features"]:
        assert feature["common_support_adjusted"]["direction"] == "increase"


def test_pure_incidence_difference_disappears_on_common_support(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "support.json"
    _write(private_input, _payload(post_effect=0.0))

    common.run_common_support_assessment(
        input_path=private_input,
        output_path=private_output,
        execute=True,
    )
    payload = json.loads(private_output.read_text(encoding="utf-8"))

    for feature in payload["features"]:
        assert (
            feature["common_support_adjusted"]["direction"]
            == "no_material_numeric_change"
        )


def test_no_common_range_is_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    payload = _payload(
        pre_values=tuple(float(value) for value in range(12)),
        post_values=tuple(float(value) for value in range(20, 32)),
    )
    _write(private_input, payload)

    with pytest.raises(common.DepthS1CommonSupportError, match="no usable common incidence range"):
        common.run_common_support_assessment(input_path=private_input)


def test_too_few_rows_inside_support_are_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    payload = _payload(
        pre_values=tuple(float(value) for value in range(12)),
        post_values=tuple(float(value) for value in range(9, 21)),
    )
    _write(private_input, payload)

    with pytest.raises(common.DepthS1CommonSupportError, match="too few rows remain"):
        common.run_common_support_assessment(input_path=private_input)
