from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import extract_depth_s1_matched_features as extractor
import screen_depth_s1_matched_feature_changes as screen


PRIVATE_ID = "S1A_PRIVATE_DO_NOT_PRINT"
PRIVATE_COORDINATE_TEXT = "-97.1234"


def _stats(value: float, *, count: int = 25) -> dict[str, float | int | None]:
    result: dict[str, float | int | None] = {}
    for feature_index, feature in enumerate(extractor.FEATURE_NAMES):
        base = value + feature_index
        result[f"{feature}_p25"] = base - 0.25 if count else None
        result[f"{feature}_median"] = base if count else None
        result[f"{feature}_p75"] = base + 0.25 if count else None
        result[f"{feature}_count"] = count
    return result


def _row(image_id: str, period: str, site_value: float, background_value: float, *, count: int = 25) -> dict[str, object]:
    site = _stats(site_value, count=count)
    background = _stats(background_value, count=count)
    deltas: dict[str, float | None] = {}
    for feature in extractor.FEATURE_NAMES:
        site_median = site[f"{feature}_median"]
        background_median = background[f"{feature}_median"]
        if site_median is None or background_median is None:
            deltas[f"{feature}_median"] = None
        else:
            deltas[f"{feature}_median"] = float(site_median) - float(background_median)
    return {
        "period": period,
        "image_id": image_id,
        "timestamp": "2021-01-01T00:00:00+00:00",
        "site": site,
        "background": background,
        "site_minus_background": deltas,
    }


def _payload() -> dict[str, object]:
    return {
        "schema_version": extractor.PRIVATE_OUTPUT_SCHEMA,
        "status": "matched_s1_feature_extraction_incomplete",
        "selection_contract": {
            "collection_id": extractor.S1_COLLECTION_ID,
            "selected_relative_orbit": 107,
        },
        "coordinates_included": False,
        "geometry_included": False,
        "rows": [
            _row("PRE_1", "pre", 2.0, 1.0),
            _row("PRE_2", "pre", 3.0, 1.0),
            _row("POST_1", "post", 4.0, 1.0),
            _row("POST_2", "post", 6.0, 1.0),
            _row(PRIVATE_ID, "post", 0.0, 0.0, count=0),
        ],
    }


def _write_payload(path: Path, payload: dict[str, object] | None = None) -> None:
    path.write_text(json.dumps(payload or _payload()), encoding="utf-8")


def test_repository_local_input_and_output_are_rejected(tmp_path: Path) -> None:
    private_input = tmp_path / "input.json"
    _write_payload(private_input)

    with pytest.raises(screen.DepthS1DescriptiveScreenError, match="outside the repository"):
        screen.run_descriptive_screen(
            input_path=ROOT / "private-input.json",
            output_path=tmp_path / "output.json",
        )

    with pytest.raises(screen.DepthS1DescriptiveScreenError, match="outside the repository"):
        screen.run_descriptive_screen(
            input_path=private_input,
            output_path=ROOT / "private-output.json",
        )


def test_zero_valid_row_is_excluded_and_remaining_rows_are_compared(tmp_path: Path) -> None:
    private_input = tmp_path / "input.json"
    private_output = tmp_path / "output.json"
    _write_payload(private_input)

    result = screen.run_descriptive_screen(input_path=private_input, output_path=private_output)
    payload = json.loads(private_output.read_text(encoding="utf-8"))

    assert result["status"] == "matched_s1_descriptive_screen_complete"
    assert result["input_row_count"] == 5
    assert result["excluded_row_count"] == 1
    assert result["excluded_pre_count"] == 0
    assert result["excluded_post_count"] == 1
    assert result["usable_pre_count"] == 2
    assert result["usable_post_count"] == 2
    assert result["usable_row_count"] == 4
    assert result["private_output_written"] is True
    assert payload["image_ids_included"] is False
    assert payload["excluded_by_period"] == {"pre": 0, "post": 1}
    assert payload["usable_by_period"] == {"pre": 2, "post": 2}


def test_descriptive_numeric_contract_is_correct(tmp_path: Path) -> None:
    private_input = tmp_path / "input.json"
    private_output = tmp_path / "output.json"
    _write_payload(private_input)

    screen.run_descriptive_screen(input_path=private_input, output_path=private_output)
    payload = json.loads(private_output.read_text(encoding="utf-8"))
    vv = payload["feature_results"]["vv_db"]

    assert vv["pre"]["count"] == 2
    assert vv["pre"]["median"] == pytest.approx(1.5)
    assert vv["post"]["median"] == pytest.approx(4.0)
    assert vv["post_minus_pre_median_shift"] == pytest.approx(2.5)
    assert vv["shift_direction"] == "positive"
    assert vv["cliffs_delta_post_vs_pre"] == pytest.approx(1.0)
    assert vv["pre"]["site_higher_fraction"] == pytest.approx(1.0)
    assert vv["post"]["site_higher_fraction"] == pytest.approx(1.0)


def test_positive_count_missing_statistic_stops_instead_of_excluding(tmp_path: Path) -> None:
    payload = _payload()
    rows = payload["rows"]
    assert isinstance(rows, list)
    first = rows[0]
    assert isinstance(first, dict)
    site = first["site"]
    assert isinstance(site, dict)
    site["vv_db_median"] = None

    private_input = tmp_path / "input.json"
    private_output = tmp_path / "output.json"
    _write_payload(private_input, payload)

    with pytest.raises(screen.DepthS1DescriptiveScreenError, match="not explained"):
        screen.run_descriptive_screen(input_path=private_input, output_path=private_output)
    assert not private_output.exists()


def test_duplicate_image_identity_is_rejected(tmp_path: Path) -> None:
    payload = _payload()
    rows = payload["rows"]
    assert isinstance(rows, list)
    duplicate = dict(rows[0])
    rows.append(duplicate)

    private_input = tmp_path / "input.json"
    private_output = tmp_path / "output.json"
    _write_payload(private_input, payload)

    with pytest.raises(screen.DepthS1DescriptiveScreenError, match="duplicate image identity"):
        screen.run_descriptive_screen(input_path=private_input, output_path=private_output)


def test_console_result_leaks_no_private_ids_coordinates_values_or_paths(tmp_path: Path) -> None:
    private_input = tmp_path / "input.json"
    private_output = tmp_path / "output.json"
    _write_payload(private_input)

    result = screen.run_descriptive_screen(input_path=private_input, output_path=private_output)
    rendered = json.dumps(result)

    assert PRIVATE_ID not in rendered
    assert PRIVATE_COORDINATE_TEXT not in rendered
    assert str(tmp_path) not in rendered
    assert "post_minus_pre_median_shift" not in rendered
    assert "cliffs_delta_post_vs_pre" not in rendered
    assert result["feature_values_printed"] is False
    assert result["image_ids_printed"] is False
    assert result["coordinates_printed"] is False
    assert result["depth_claim_made"] is False
    assert result["shift_direction_by_feature"] == {
        feature: "positive" for feature in extractor.FEATURE_NAMES
    }
