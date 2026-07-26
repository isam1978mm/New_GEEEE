from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import run_buto_s1_method_screen as buto
import run_depth_radar_linkage_feasibility_screen as screen

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


def _write_manifest(
    path: Path,
    *,
    site_id: str = "river_road",
    dates: tuple[str, ...] = ("2018-05-05", "2018-06-10"),
    controls_pass: bool = True,
) -> None:
    payload = {
        "site_id": site_id,
        "anchors": [
            {
                "image_date": image_date,
                "support_days": 36,
                "accepted": True,
                "weather_screened": controls_pass,
                "vegetation_screened": controls_pass,
                "construction_inactive": controls_pass,
                "geometry_reviewed": controls_pass,
            }
            for image_date in dates
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _row(
    acquired_date: str,
    *,
    relative_orbit: int = 42,
    signal_delta: float = 1.0,
    incidence_delta: float = 0.1,
    pixels: int = 12,
) -> dict[str, object]:
    features: dict[str, dict[str, float]] = {}
    for feature in buto.FEATURE_NAMES:
        delta = incidence_delta if feature == "incidence_angle" else signal_delta
        features[feature] = {
            "target_median": 10.0 + delta,
            "background_median": 10.0,
        }
    return {
        "acquired_date": acquired_date,
        "orbit_pass": "ASCENDING",
        "relative_orbit": relative_orbit,
        "platform": "A",
        "target_valid_pixels": pixels,
        "background_valid_pixels": pixels,
        "features": features,
    }


def _positive_query(**kwargs: object) -> list[dict[str, object]]:
    image_date = str(kwargs["image_date"])
    if image_date == "2018-05-05":
        support = ("2018-04-11", "2018-04-23", "2018-05-17")
    else:
        support = ("2018-05-17", "2018-05-29", "2018-06-22")
    return [_row(image_date)] + [_row(value) for value in support]


def _private_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    target = tmp_path / "target.geojson"
    comparison = tmp_path / "comparison.geojson"
    manifest = tmp_path / "manifest.json"
    _write_geojson(target)
    _write_geojson(comparison, shift=0.01)
    _write_manifest(manifest)
    return target, comparison, manifest


def test_dry_run_is_private_and_does_not_query(tmp_path: Path) -> None:
    target, comparison, manifest = _private_inputs(tmp_path)

    def forbidden_query(**_: object) -> list[dict[str, object]]:
        raise AssertionError("dry run must not query")

    result = screen.run_site_screen(
        site_id="river_road",
        site_role="known_cover_surface_response",
        target_geojson=target,
        comparison_geojson=comparison,
        manifest_path=manifest,
        execute=False,
        query_fn=forbidden_query,
    )
    console = screen.redacted_console_summary(result)
    rendered = json.dumps(console)

    assert result["status"] == "site_screen_dry_run_ready"
    assert result["query_executed"] is False
    assert result["comparison_area_is_confirmed_negative"] is False
    assert SYNTHETIC_COORDINATE_TEXT not in rendered
    assert str(target) not in rendered
    assert "synthetic_private_test" not in rendered


def test_accepted_anchor_requires_all_confounder_controls(tmp_path: Path) -> None:
    target, comparison, manifest = _private_inputs(tmp_path)
    _write_manifest(manifest, controls_pass=False)

    with pytest.raises(
        screen.RadarLinkageScreenError,
        match="must pass all confounder controls",
    ):
        screen.run_site_screen(
            site_id="river_road",
            site_role="known_cover_surface_response",
            target_geojson=target,
            comparison_geojson=comparison,
            manifest_path=manifest,
        )


def test_two_anchor_series_can_support_site_surface_response(tmp_path: Path) -> None:
    target, comparison, manifest = _private_inputs(tmp_path)

    result = screen.run_site_screen(
        site_id="river_road",
        site_role="known_cover_surface_response",
        target_geojson=target,
        comparison_geojson=comparison,
        manifest_path=manifest,
        execute=True,
        query_fn=_positive_query,
    )

    assert result["status"] == "site_screen_complete"
    assert result["supported_anchor_count"] == 2
    assert result["total_same_orbit_support_count"] == 6
    assert result["stable_signal_feature_count"] == 4
    assert result["site_surface_response_decision"] == "site_surface_response_supported"
    assert result["site_depth_ordering_decision"] == (
        "depth_ordering_not_available_at_this_site_stage"
    )
    assert result["cross_site_depth_linkage_decision"] == (
        "not_evaluated_single_site_result"
    )
    assert result["depth_measured"] is False
    assert result["calibration_record_created"] is False
    assert result["app_depth_enabled"] is False


def test_incidence_angle_alone_cannot_support_site_signal(tmp_path: Path) -> None:
    target, comparison, manifest = _private_inputs(tmp_path)

    def incidence_only_query(**kwargs: object) -> list[dict[str, object]]:
        image_date = str(kwargs["image_date"])
        return [
            _row(image_date, signal_delta=0.0, incidence_delta=1.0),
            _row("2018-04-11", signal_delta=0.0, incidence_delta=1.0),
            _row("2018-04-23", signal_delta=0.0, incidence_delta=1.0),
            _row("2018-05-17", signal_delta=0.0, incidence_delta=1.0),
        ]

    result = screen.run_site_screen(
        site_id="river_road",
        site_role="known_cover_surface_response",
        target_geojson=target,
        comparison_geojson=comparison,
        manifest_path=manifest,
        execute=True,
        query_fn=incidence_only_query,
    )

    assert result["stable_signal_feature_count"] == 0
    assert result["site_surface_response_decision"] == (
        "site_surface_response_not_supported"
    )


def test_execute_with_one_anchor_is_inconclusive(tmp_path: Path) -> None:
    target, comparison, manifest = _private_inputs(tmp_path)
    _write_manifest(manifest, dates=("2018-05-05",))

    result = screen.run_site_screen(
        site_id="river_road",
        site_role="known_cover_surface_response",
        target_geojson=target,
        comparison_geojson=comparison,
        manifest_path=manifest,
        execute=True,
        query_fn=_positive_query,
    )

    assert result["status"] == "site_screen_not_ready_insufficient_accepted_anchors"
    assert result["query_executed"] is False
    assert result["site_surface_response_decision"] == "site_screen_inconclusive"


def test_detailed_output_stays_outside_git_and_console_is_redacted(
    tmp_path: Path,
) -> None:
    target, comparison, manifest = _private_inputs(tmp_path)
    output = tmp_path / "river_road_result.json"

    result = screen.run_site_screen(
        site_id="river_road",
        site_role="known_cover_surface_response",
        target_geojson=target,
        comparison_geojson=comparison,
        manifest_path=manifest,
        execute=True,
        output_path=output,
        query_fn=_positive_query,
    )
    written = json.loads(output.read_text(encoding="utf-8"))
    console = screen.redacted_console_summary(result)

    assert written["output_written"] is True
    assert "anchor_results" in written
    assert "feature_direction_summary" in written
    assert "anchor_results" not in console
    assert "feature_direction_summary" not in console
    assert SYNTHETIC_COORDINATE_TEXT not in json.dumps(console)

    with pytest.raises(screen.RadarLinkageScreenError, match="outside the repository"):
        screen.run_site_screen(
            site_id="river_road",
            site_role="known_cover_surface_response",
            target_geojson=target,
            comparison_geojson=comparison,
            manifest_path=manifest,
            output_path=ROOT / "river_road_result.json",
        )
