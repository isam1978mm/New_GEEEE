from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_depth_s1_site_background_match as matcher


SYNTHETIC_COORDINATE_TEXT = "35.1234"
SYNTHETIC_IMAGE_ID = "S1_SYNTHETIC_PRIVATE_ID"


def _write_geojson(path: Path, *, x_offset: float = 0.0) -> None:
    x0 = 35.1234 + x_offset
    payload = {
        "type": "Feature",
        "properties": {"private_label": "synthetic"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [x0, 44.1234],
                    [x0 + 0.001, 44.1234],
                    [x0 + 0.001, 44.1244],
                    [x0, 44.1234],
                ]
            ],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _ms(value: str) -> int:
    return int(datetime.fromisoformat(value).replace(tzinfo=UTC).timestamp() * 1000)


def _base_kwargs(tmp_path: Path) -> dict[str, object]:
    site = tmp_path / "site.geojson"
    background = tmp_path / "background.geojson"
    _write_geojson(site)
    _write_geojson(background, x_offset=0.01)
    return {
        "site_geojson": site,
        "background_geojson": background,
        "start_date": "2019-01-01",
        "end_date": "2021-01-01",
        "pre_end_exclusive": "2020-02-01",
        "post_start": "2020-04-01",
        "orbit_pass": "ASCENDING",
        "relative_orbit": 107,
        "platform": "A",
    }


def test_repository_local_geometry_is_rejected(tmp_path: Path) -> None:
    background = tmp_path / "background.geojson"
    _write_geojson(background, x_offset=0.01)

    with pytest.raises(matcher.DepthS1BackgroundMatchError, match="outside the repository"):
        matcher.run_site_background_match(
            **{
                **_base_kwargs(tmp_path),
                "site_geojson": ROOT / "site.geojson",
                "background_geojson": background,
            }
        )


def test_identical_site_and_background_geometry_is_rejected(tmp_path: Path) -> None:
    kwargs = _base_kwargs(tmp_path)
    site = Path(kwargs["site_geojson"])
    background = Path(kwargs["background_geojson"])
    _write_geojson(site)
    _write_geojson(background)

    with pytest.raises(matcher.DepthS1BackgroundMatchError, match="must not be identical"):
        matcher.run_site_background_match(**kwargs)


def test_invalid_clean_windows_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(matcher.DepthS1BackgroundMatchError, match="conservative analysis windows"):
        matcher.run_site_background_match(
            **{
                **_base_kwargs(tmp_path),
                "pre_end_exclusive": "2020-05-01",
                "post_start": "2020-04-01",
            }
        )


def test_dry_run_performs_no_query_or_write_and_leaks_nothing(tmp_path: Path) -> None:
    output = tmp_path / "summary.json"
    manifest = tmp_path / "manifest.json"

    def forbidden_query(**_: object) -> list[dict[str, object]]:
        raise AssertionError("dry run must not query Earth Engine")

    result = matcher.run_site_background_match(
        **_base_kwargs(tmp_path),
        execute=False,
        output_path=output,
        private_manifest_path=manifest,
        query_fn=forbidden_query,
    )
    rendered = json.dumps(result)

    assert result["status"] == "site_background_match_dry_run_ready"
    assert result["query_executed"] is False
    assert not output.exists()
    assert not manifest.exists()
    assert result["coordinates_printed"] is False
    assert result["geometry_printed"] is False
    assert result["private_paths_printed"] is False
    assert result["image_ids_printed"] is False
    assert SYNTHETIC_COORDINATE_TEXT not in rendered
    assert str(tmp_path) not in rendered


def test_execute_requires_background_review_confirmation(tmp_path: Path) -> None:
    with pytest.raises(matcher.DepthS1BackgroundMatchError, match="visually reviewed"):
        matcher.run_site_background_match(
            **_base_kwargs(tmp_path),
            execute=True,
            background_reviewed=False,
            query_fn=lambda **_: [],
        )


def test_exact_matches_are_counted_and_private_manifest_isolated(tmp_path: Path) -> None:
    output = tmp_path / "summary.json"
    manifest_path = tmp_path / "private_manifest.json"
    call_count = 0

    def fake_query(**kwargs: object) -> list[dict[str, object]]:
        nonlocal call_count
        call_count += 1
        assert kwargs["orbit_pass"] == "ASCENDING"
        assert kwargs["relative_orbit"] == 107
        assert kwargs["platform"] == "A"
        shared = [
            {"image_id": "PRE_SHARED", "time_start_ms": _ms("2020-01-01")},
            {"image_id": "TRANSITION_SHARED", "time_start_ms": _ms("2020-03-01")},
            {"image_id": "POST_SHARED", "time_start_ms": _ms("2020-05-01")},
        ]
        if call_count == 1:
            return shared + [{"image_id": "SITE_ONLY", "time_start_ms": _ms("2020-06-01")}]
        return shared + [{"image_id": "BACKGROUND_ONLY", "time_start_ms": _ms("2020-07-01")}]

    result = matcher.run_site_background_match(
        **_base_kwargs(tmp_path),
        execute=True,
        background_reviewed=True,
        output_path=output,
        private_manifest_path=manifest_path,
        query_fn=fake_query,
    )
    rendered = json.dumps(result)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    written_summary = json.loads(output.read_text(encoding="utf-8"))

    assert call_count == 2
    assert result["status"] == "site_background_match_completed"
    assert result["match_decision"] == "site_background_acquisition_match_ready"
    assert result["matched_pre_count"] == 1
    assert result["matched_transition_count"] == 1
    assert result["matched_post_count"] == 1
    assert result["site_post_unmatched_count"] == 1
    assert result["background_post_unmatched_count"] == 1
    assert result["site_background_exact_match_support"] is True
    assert result["private_manifest_written"] is True
    assert result["private_manifest_contains_image_ids"] is True
    assert written_summary["image_ids_printed"] is False
    assert manifest["matched_pre"][0]["image_id"] == "PRE_SHARED"
    assert manifest["matched_post"][0]["image_id"] == "POST_SHARED"
    assert "PRE_SHARED" not in rendered
    assert "POST_SHARED" not in rendered
    assert SYNTHETIC_IMAGE_ID not in rendered
    assert SYNTHETIC_COORDINATE_TEXT not in rendered
    assert str(tmp_path) not in rendered


def test_missing_exact_post_match_is_not_ready(tmp_path: Path) -> None:
    call_count = 0

    def fake_query(**_: object) -> list[dict[str, object]]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return [
                {"image_id": "PRE_SHARED", "time_start_ms": _ms("2020-01-01")},
                {"image_id": "SITE_POST", "time_start_ms": _ms("2020-05-01")},
            ]
        return [
            {"image_id": "PRE_SHARED", "time_start_ms": _ms("2020-01-01")},
            {"image_id": "BACKGROUND_POST", "time_start_ms": _ms("2020-05-01")},
        ]

    result = matcher.run_site_background_match(
        **_base_kwargs(tmp_path),
        execute=True,
        background_reviewed=True,
        query_fn=fake_query,
    )

    assert result["matched_pre_count"] == 1
    assert result["matched_post_count"] == 0
    assert result["exact_pre_match_support"] is True
    assert result["exact_post_match_support"] is False
    assert result["site_background_exact_match_support"] is False
    assert result["match_decision"] == "site_background_acquisition_match_not_ready"


def test_duplicate_image_identity_is_rejected(tmp_path: Path) -> None:
    def fake_query(**_: object) -> list[dict[str, object]]:
        return [
            {"image_id": "DUPLICATE", "time_start_ms": _ms("2020-01-01")},
            {"image_id": "DUPLICATE", "time_start_ms": _ms("2020-01-01")},
        ]

    with pytest.raises(matcher.DepthS1BackgroundMatchError, match="duplicate image identity"):
        matcher.run_site_background_match(
            **_base_kwargs(tmp_path),
            execute=True,
            background_reviewed=True,
            query_fn=fake_query,
        )


def test_repository_local_output_and_manifest_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(matcher.DepthS1BackgroundMatchError, match="outside the repository"):
        matcher.run_site_background_match(
            **_base_kwargs(tmp_path),
            output_path=ROOT / "match_summary.json",
        )

    with pytest.raises(matcher.DepthS1BackgroundMatchError, match="outside the repository"):
        matcher.run_site_background_match(
            **_base_kwargs(tmp_path),
            private_manifest_path=ROOT / "match_manifest.json",
        )
