from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import extract_depth_s1_matched_features as extractor


PRIVATE_ID = "S1A_SYNTHETIC_PRIVATE_ID"
PRIVATE_COORDINATE_TEXT = "-97.1234"


def _write_rectangle(path: Path, *, offset: float = 0.0) -> None:
    west = -97.1234 + offset
    south = 27.1234
    east = west + 0.0005
    north = south + 0.0005
    payload = {
        "type": "Feature",
        "properties": {"private_label": "remove-me"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [west, south],
                    [east, south],
                    [east, north],
                    [west, north],
                    [west, south],
                ]
            ],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _manifest_payload() -> dict[str, object]:
    return {
        "schema_version": extractor.MATCH_MANIFEST_SCHEMA,
        "status": "site_background_acquisition_match_ready",
        "collection_id": extractor.S1_COLLECTION_ID,
        "instrument_mode": "IW",
        "required_polarisations": ["VV", "VH"],
        "resolution_meters": 10,
        "start_date": "2017-01-01",
        "end_date_exclusive": "2023-01-01",
        "pre_end_exclusive": "2020-02-01",
        "post_start": "2020-04-01",
        "selected_orbit_pass": "ASCENDING",
        "selected_relative_orbit": 107,
        "selected_platform": "A",
        "coordinates_included": False,
        "geometry_included": False,
        "matched_pre": [
            {
                "image_id": "S1A_PRE_001",
                "timestamp": "2019-01-01T00:00:00+00:00",
            }
        ],
        "matched_transition_excluded": [
            {
                "image_id": "S1A_TRANSITION_001",
                "timestamp": "2020-03-01T00:00:00+00:00",
            }
        ],
        "matched_post": [
            {
                "image_id": "S1A_POST_001",
                "timestamp": "2021-01-01T00:00:00+00:00",
            }
        ],
    }


def _write_manifest(path: Path, payload: dict[str, object] | None = None) -> None:
    path.write_text(json.dumps(payload or _manifest_payload()), encoding="utf-8")


def _all_stats(base: float) -> dict[str, float | int]:
    stats: dict[str, float | int] = {}
    for index, key in enumerate(extractor.STATISTIC_KEYS):
        if key.endswith("_count"):
            stats[key] = 25
        else:
            stats[key] = base + index / 100.0
    return stats


def _complete_query_items() -> list[dict[str, object]]:
    return [
        {
            "image_id": "S1A_PRE_001",
            "timestamp": "2019-01-01T00:00:00+00:00",
            "site": _all_stats(1.0),
            "background": _all_stats(0.5),
        },
        {
            "image_id": "S1A_POST_001",
            "timestamp": "2021-01-01T00:00:00+00:00",
            "site": _all_stats(2.0),
            "background": _all_stats(1.5),
        },
    ]


def _base_paths(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    site = tmp_path / "site.geojson"
    background = tmp_path / "background.geojson"
    manifest = tmp_path / "match_manifest.json"
    output = tmp_path / "matched_features.json"
    _write_rectangle(site)
    _write_rectangle(background, offset=0.01)
    _write_manifest(manifest)
    return site, background, manifest, output


def test_repository_local_geometry_is_rejected(tmp_path: Path) -> None:
    _, background, manifest, output = _base_paths(tmp_path)
    with pytest.raises(extractor.DepthS1MatchedFeatureError, match="outside the repository"):
        extractor.run_matched_feature_extraction(
            site_geojson=ROOT / "site.geojson",
            background_geojson=background,
            match_manifest=manifest,
            output_path=output,
        )


def test_repository_local_manifest_and_output_are_rejected(tmp_path: Path) -> None:
    site, background, _, output = _base_paths(tmp_path)
    with pytest.raises(extractor.DepthS1MatchedFeatureError, match="outside the repository"):
        extractor.run_matched_feature_extraction(
            site_geojson=site,
            background_geojson=background,
            match_manifest=ROOT / "manifest.json",
            output_path=output,
        )

    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest)
    with pytest.raises(extractor.DepthS1MatchedFeatureError, match="outside the repository"):
        extractor.run_matched_feature_extraction(
            site_geojson=site,
            background_geojson=background,
            match_manifest=manifest,
            output_path=ROOT / "features.json",
        )


def test_identical_site_and_background_are_rejected(tmp_path: Path) -> None:
    site, background, manifest, output = _base_paths(tmp_path)
    _write_rectangle(background)
    with pytest.raises(extractor.DepthS1MatchedFeatureError, match="must not be identical"):
        extractor.run_matched_feature_extraction(
            site_geojson=site,
            background_geojson=background,
            match_manifest=manifest,
            output_path=output,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", "wrong", "schema"),
        ("status", "not_ready", "not ready"),
        ("matched_pre", [], "must not be empty"),
        ("matched_post", [], "must not be empty"),
    ],
)
def test_invalid_manifest_contract_is_rejected(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    site, background, manifest, output = _base_paths(tmp_path)
    payload = _manifest_payload()
    payload[field] = value
    _write_manifest(manifest, payload)
    with pytest.raises(extractor.DepthS1MatchedFeatureError, match=message):
        extractor.run_matched_feature_extraction(
            site_geojson=site,
            background_geojson=background,
            match_manifest=manifest,
            output_path=output,
        )


def test_duplicate_and_overlapping_manifest_ids_are_rejected(tmp_path: Path) -> None:
    _, _, manifest, _ = _base_paths(tmp_path)
    payload = _manifest_payload()
    payload["matched_pre"] = [
        {"image_id": "DUPLICATE", "timestamp": "2019-01-01T00:00:00+00:00"},
        {"image_id": "DUPLICATE", "timestamp": "2019-01-02T00:00:00+00:00"},
    ]
    _write_manifest(manifest, payload)
    with pytest.raises(extractor.DepthS1MatchedFeatureError, match="duplicate"):
        extractor.load_private_match_manifest(manifest)

    payload = _manifest_payload()
    payload["matched_post"] = [
        {"image_id": "S1A_PRE_001", "timestamp": "2021-01-01T00:00:00+00:00"}
    ]
    _write_manifest(manifest, payload)
    with pytest.raises(extractor.DepthS1MatchedFeatureError, match="overlapping"):
        extractor.load_private_match_manifest(manifest)


def test_dry_run_performs_no_query_or_write_and_leaks_nothing(tmp_path: Path) -> None:
    site, background, manifest, output = _base_paths(tmp_path)
    called = False

    def query_fn(**_: object) -> list[dict[str, object]]:
        nonlocal called
        called = True
        return []

    result = extractor.run_matched_feature_extraction(
        site_geojson=site,
        background_geojson=background,
        match_manifest=manifest,
        output_path=output,
        execute=False,
        query_fn=query_fn,
    )
    rendered = json.dumps(result)

    assert result["status"] == "matched_s1_feature_extraction_dry_run_ready"
    assert result["query_executed"] is False
    assert result["private_output_written"] is False
    assert result["manifest_pre_count"] == 1
    assert result["manifest_post_count"] == 1
    assert result["transition_rows_excluded"] == 1
    assert called is False
    assert not output.exists()
    assert PRIVATE_ID not in rendered
    assert PRIVATE_COORDINATE_TEXT not in rendered
    assert str(tmp_path) not in rendered


def test_execute_requires_private_output_path(tmp_path: Path) -> None:
    site, background, manifest, _ = _base_paths(tmp_path)
    with pytest.raises(extractor.DepthS1MatchedFeatureError, match="requires a private output"):
        extractor.run_matched_feature_extraction(
            site_geojson=site,
            background_geojson=background,
            match_manifest=manifest,
            execute=True,
            query_fn=lambda **_: _complete_query_items(),
        )


def test_complete_extraction_writes_private_rows_and_aggregate_console_only(tmp_path: Path) -> None:
    site, background, manifest, output = _base_paths(tmp_path)
    queried_ids: list[str] = []

    def query_fn(**kwargs: object) -> list[dict[str, object]]:
        rows = kwargs["manifest_rows"]
        assert isinstance(rows, list)
        queried_ids.extend(str(row["image_id"]) for row in rows)
        assert kwargs["resolution_meters"] == 10
        return _complete_query_items()

    result = extractor.run_matched_feature_extraction(
        site_geojson=site,
        background_geojson=background,
        match_manifest=manifest,
        output_path=output,
        execute=True,
        query_fn=query_fn,
    )
    rendered = json.dumps(result)
    private_payload = json.loads(output.read_text(encoding="utf-8"))

    assert result["status"] == "matched_s1_feature_extraction_complete"
    assert result["query_executed"] is True
    assert result["private_output_written"] is True
    assert result["extracted_pre_count"] == 1
    assert result["extracted_post_count"] == 1
    assert result["transition_rows_excluded"] == 1
    assert result["missing_image_count"] == 0
    assert result["missing_statistic_count"] == 0
    assert result["all_rows_complete"] is True
    assert queried_ids == ["S1A_PRE_001", "S1A_POST_001"]
    assert "S1A_TRANSITION_001" not in queried_ids
    assert private_payload["schema_version"] == extractor.PRIVATE_OUTPUT_SCHEMA
    assert private_payload["coordinates_included"] is False
    assert private_payload["geometry_included"] is False
    assert len(private_payload["rows"]) == 2
    first_row = private_payload["rows"][0]
    assert first_row["period"] == "pre"
    assert first_row["image_id"] == "S1A_PRE_001"
    assert first_row["site_minus_background"]["vv_db_median"] == pytest.approx(0.5)
    assert "S1A_PRE_001" not in rendered
    assert PRIVATE_COORDINATE_TEXT not in rendered
    assert str(tmp_path) not in rendered
    assert result["feature_values_printed"] is False
    assert result["image_ids_printed"] is False


def test_missing_statistics_produce_incomplete_decision(tmp_path: Path) -> None:
    site, background, manifest, output = _base_paths(tmp_path)
    items = _complete_query_items()
    assert isinstance(items[0]["site"], dict)
    items[0]["site"]["vv_db_median"] = None

    result = extractor.run_matched_feature_extraction(
        site_geojson=site,
        background_geojson=background,
        match_manifest=manifest,
        output_path=output,
        execute=True,
        query_fn=lambda **_: items,
    )

    assert result["status"] == "matched_s1_feature_extraction_incomplete"
    assert result["missing_statistic_count"] == 1
    assert result["all_rows_complete"] is False
    assert output.exists()


def test_missing_image_and_unexpected_image_are_handled_safely(tmp_path: Path) -> None:
    site, background, manifest, output = _base_paths(tmp_path)
    result = extractor.run_matched_feature_extraction(
        site_geojson=site,
        background_geojson=background,
        match_manifest=manifest,
        output_path=output,
        execute=True,
        query_fn=lambda **_: _complete_query_items()[:1],
    )
    assert result["status"] == "matched_s1_feature_extraction_incomplete"
    assert result["missing_image_count"] == 1
    assert result["extracted_post_count"] == 0

    unexpected = _complete_query_items()
    unexpected.append(
        {
            "image_id": "S1A_UNEXPECTED",
            "timestamp": "2022-01-01T00:00:00+00:00",
            "site": _all_stats(1.0),
            "background": _all_stats(1.0),
        }
    )
    with pytest.raises(extractor.DepthS1MatchedFeatureError, match="outside the private manifest"):
        extractor.run_matched_feature_extraction(
            site_geojson=site,
            background_geojson=background,
            match_manifest=manifest,
            output_path=tmp_path / "second.json",
            execute=True,
            query_fn=lambda **_: unexpected,
        )
