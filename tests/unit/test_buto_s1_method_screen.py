from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import run_buto_s1_method_screen as buto

SYNTHETIC_COORDINATE_TEXT = "31.1234"


def _write_geojson(path: Path, shift: float = 0.0) -> None:
    payload = {
        "type": "Feature",
        "properties": {"site_name": "synthetic_private_test"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [31.1234 + shift, 30.1234],
                    [31.1244 + shift, 30.1234],
                    [31.1244 + shift, 30.1244],
                    [31.1234 + shift, 30.1234],
                ]
            ],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _row(
    acquired_date: str,
    relative_orbit: int,
    delta: float,
    pixels: int = 12,
) -> dict[str, object]:
    return {
        "acquired_date": acquired_date,
        "orbit_pass": "ASCENDING",
        "relative_orbit": relative_orbit,
        "platform": "A",
        "target_valid_pixels": pixels,
        "background_valid_pixels": pixels,
        "features": {
            feature: {
                "target_median": 10.0 + delta,
                "background_median": 10.0,
            }
            for feature in buto.FEATURE_NAMES
        },
    }


def test_dry_run_is_private_and_does_not_query(tmp_path: Path) -> None:
    target = tmp_path / "target.geojson"
    background = tmp_path / "background.geojson"
    _write_geojson(target)
    _write_geojson(background, shift=0.01)

    def forbidden_query(**_: object) -> list[dict[str, object]]:
        raise AssertionError("dry run must not query")

    result = buto.run_method_screen(
        target_geojson=target,
        background_geojson=background,
        execute=False,
        query_fn=forbidden_query,
    )
    console = buto.redacted_console_summary(result)
    rendered = json.dumps(console)

    assert result["status"] == "method_screen_dry_run_ready"
    assert result["query_executed"] is False
    assert result["comparison_area_is_confirmed_negative"] is False
    assert SYNTHETIC_COORDINATE_TEXT not in rendered
    assert str(target) not in rendered
    assert "synthetic_private_test" not in rendered


def test_same_geometry_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target.geojson"
    background = tmp_path / "background.geojson"
    _write_geojson(target)
    _write_geojson(background)

    with pytest.raises(buto.ButoMethodScreenError, match="must be different"):
        buto.run_method_screen(
            target_geojson=target,
            background_geojson=background,
        )


def test_exact_date_and_same_orbit_support_can_support_spatial_agreement() -> None:
    rows = [
        _row("2018-05-05", 42, 2.0),
        _row("2018-04-23", 42, 1.0),
        _row("2018-05-17", 42, 0.5),
        _row("2018-05-17", 99, -5.0),
    ]

    result = buto.summarize_rows(rows, image_date="2018-05-05")

    assert result["status"] == "method_screen_complete_spatial_comparison_only"
    assert result["same_orbit_support_count"] == 2
    assert result["stable_feature_count"] == 4
    assert result["signal_feature_count"] == 4
    assert result["spatial_agreement_decision"] == "spatial_agreement_supported"
    assert result["depth_measured"] is False


def test_incidence_control_does_not_count_as_signal_support() -> None:
    exact = _row("2018-05-05", 42, 0.0)
    support_one = _row("2018-04-23", 42, 0.0)
    support_two = _row("2018-05-17", 42, 0.0)
    for row in (exact, support_one, support_two):
        features = row["features"]
        assert isinstance(features, dict)
        features["incidence_angle"] = {
            "target_median": 31.0,
            "background_median": 30.0,
        }

    result = buto.summarize_rows(
        [exact, support_one, support_two],
        image_date="2018-05-05",
    )

    assert result["exact_feature_summary"]["incidence_angle"]["stable_direction"] is True
    assert result["stable_feature_count"] == 0
    assert result["spatial_agreement_decision"] == "spatial_agreement_not_supported"


def test_missing_exact_date_is_inconclusive() -> None:
    result = buto.summarize_rows(
        [_row("2018-05-17", 42, 1.0)],
        image_date="2018-05-05",
    )

    assert result["status"] == "method_screen_not_ready_no_exact_date_acquisition"
    assert result["spatial_agreement_decision"] == "method_screen_inconclusive"


def test_too_few_valid_pixels_is_inconclusive() -> None:
    result = buto.summarize_rows(
        [_row("2018-05-05", 42, 1.0, pixels=3)],
        image_date="2018-05-05",
    )

    assert result["status"] == "method_screen_not_ready_insufficient_valid_pixels"
    assert result["spatial_agreement_decision"] == "method_screen_inconclusive"


def test_output_inside_repository_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target.geojson"
    background = tmp_path / "background.geojson"
    _write_geojson(target)
    _write_geojson(background, shift=0.01)

    with pytest.raises(buto.ButoMethodScreenError, match="outside the repository"):
        buto.run_method_screen(
            target_geojson=target,
            background_geojson=background,
            output_path=ROOT / "buto_result.json",
        )


def test_detailed_output_is_written_only_to_external_file(tmp_path: Path) -> None:
    target = tmp_path / "target.geojson"
    background = tmp_path / "background.geojson"
    output = tmp_path / "result.json"
    _write_geojson(target)
    _write_geojson(background, shift=0.01)

    result = buto.run_method_screen(
        target_geojson=target,
        background_geojson=background,
        execute=True,
        output_path=output,
        query_fn=lambda **_: [
            _row("2018-05-05", 42, 1.0),
            _row("2018-04-23", 42, 0.5),
            _row("2018-05-17", 42, 0.5),
        ],
    )
    written = json.loads(output.read_text(encoding="utf-8"))
    console = buto.redacted_console_summary(result)

    assert written["output_written"] is True
    assert "exact_feature_summary" in written
    assert "exact_feature_summary" not in console
    assert SYNTHETIC_COORDINATE_TEXT not in json.dumps(console)
