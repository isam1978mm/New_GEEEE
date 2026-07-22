from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import assess_depth_s1_temporal_robustness as robustness


def _row(
    period: str,
    timestamp: datetime,
    incidence_value: float,
    period_effect: float,
    *,
    included: bool = True,
) -> dict[str, object]:
    deltas: dict[str, float] = {
        robustness.incidence.INCIDENCE_KEY: incidence_value,
    }
    for index, feature in enumerate(robustness.incidence.RADAR_FEATURES):
        deltas[f"{feature}_median"] = (
            (index + 1.0) * incidence_value
            + period_effect
            + ((timestamp.day % 3) - 1) * 0.01
        )
    return {
        "period": period,
        "timestamp": timestamp.isoformat(),
        "analysis_included": included,
        "site_minus_background": deltas,
    }


def _payload(*, post_effect: float = 1.0) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    pre_start = datetime(2018, 1, 1, tzinfo=UTC)
    post_start = datetime(2021, 1, 1, tzinfo=UTC)

    for index in range(40):
        rows.append(
            _row(
                "pre",
                pre_start + timedelta(days=index * 12),
                incidence_value=float(index % 10),
                period_effect=0.0,
            )
        )
    for index in range(40):
        rows.append(
            _row(
                "post",
                post_start + timedelta(days=index * 12),
                incidence_value=float(index % 10),
                period_effect=post_effect,
            )
        )
    rows.append(
        _row(
            "post",
            post_start,
            incidence_value=999.0,
            period_effect=999.0,
            included=False,
        )
    )

    return {
        "schema_version": robustness.INPUT_SCHEMA,
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

    with pytest.raises(robustness.DepthS1TemporalRobustnessError, match="outside the repository"):
        robustness.run_temporal_robustness(input_path=ROOT / "features.json")

    with pytest.raises(robustness.DepthS1TemporalRobustnessError, match="outside the repository"):
        robustness.run_temporal_robustness(
            input_path=private_input,
            output_path=ROOT / "robustness.json",
        )


def test_dry_run_writes_nothing_and_uses_four_by_four_blocks(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "robustness.json"
    _write(private_input)

    result = robustness.run_temporal_robustness(
        input_path=private_input,
        output_path=private_output,
        execute=False,
    )
    rendered = json.dumps(result)

    assert result["status"] == "temporal_block_robustness_dry_run_ready"
    assert result["included_pre_count"] == 40
    assert result["included_post_count"] == 40
    assert result["input_rows_excluded_from_analysis"] == 1
    assert result["pre_block_count"] == 4
    assert result["post_block_count"] == 4
    assert result["comparisons_per_feature"] == 16
    assert result["private_output_written"] is False
    assert result["effect_values_printed"] is False
    assert "1.0" not in rendered
    assert str(tmp_path) not in rendered
    assert not private_output.exists()


def test_execute_writes_private_comparisons(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "robustness.json"
    _write(private_input)

    result = robustness.run_temporal_robustness(
        input_path=private_input,
        output_path=private_output,
        execute=True,
    )
    payload = json.loads(private_output.read_text(encoding="utf-8"))

    assert result["status"] == "temporal_block_robustness_complete"
    assert result["private_output_written"] is True
    assert payload["schema_version"] == robustness.OUTPUT_SCHEMA
    assert payload["image_ids_included"] is False
    assert payload["coordinates_included"] is False
    assert payload["geometry_included"] is False
    assert len(payload["features"]) == 4
    assert len(payload["features"][0]["comparisons"]) == 16


def test_consistent_post_effect_is_detected_across_all_blocks(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    private_output = tmp_path / "robustness.json"
    _write(private_input, _payload(post_effect=1.0))

    robustness.run_temporal_robustness(
        input_path=private_input,
        output_path=private_output,
        execute=True,
    )
    payload = json.loads(private_output.read_text(encoding="utf-8"))

    for feature in payload["features"]:
        assert feature["dominant_direction"] == "increase"
        assert feature["consistency_bucket"] == "all_blocks_consistent"
        assert feature["overlap_qualification_bucket"] == "at_least_75_percent_qualified"


def test_too_few_rows_are_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    payload = _payload()
    rows = payload["rows"]
    assert isinstance(rows, list)
    payload["rows"] = rows[:20]
    _write(private_input, payload)

    with pytest.raises(robustness.DepthS1TemporalRobustnessError, match="not enough usable rows"):
        robustness.run_temporal_robustness(input_path=private_input)


def test_missing_timestamp_is_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "features.json"
    payload = _payload()
    rows = payload["rows"]
    assert isinstance(rows, list)
    first = rows[0]
    assert isinstance(first, dict)
    first["timestamp"] = None
    _write(private_input, payload)

    with pytest.raises(robustness.DepthS1TemporalRobustnessError, match="missing timestamp"):
        robustness.run_temporal_robustness(input_path=private_input)
