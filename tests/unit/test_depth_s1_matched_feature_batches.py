from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import extract_depth_s1_matched_features as extractor
import extract_depth_s1_matched_features_batched as batched


PRIVATE_ID = "S1A_PRIVATE_DO_NOT_PRINT"
PRIVATE_COORDINATE = "-97.1234"


def _write_rectangle(path: Path, *, offset: float = 0.0) -> None:
    west = -97.1234 + offset
    south = 27.1234
    payload = {
        "type": "Feature",
        "properties": {"private": True},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [west, south],
                    [west + 0.0005, south],
                    [west + 0.0005, south + 0.0005],
                    [west, south + 0.0005],
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
            {"image_id": "S1A_PRE_001", "timestamp": "2019-01-01T00:00:00+00:00"},
            {"image_id": "S1A_PRE_002", "timestamp": "2019-01-13T00:00:00+00:00"},
        ],
        "matched_transition_excluded": [
            {"image_id": "S1A_TRANSITION_001", "timestamp": "2020-03-01T00:00:00+00:00"}
        ],
        "matched_post": [
            {"image_id": "S1A_POST_001", "timestamp": "2021-01-01T00:00:00+00:00"},
        ],
    }


def _base_paths(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    site = tmp_path / "site.geojson"
    background = tmp_path / "background.geojson"
    manifest = tmp_path / "match_manifest.json"
    output = tmp_path / "matched_features.json"
    _write_rectangle(site)
    _write_rectangle(background, offset=0.01)
    manifest.write_text(json.dumps(_manifest_payload()), encoding="utf-8")
    return site, background, manifest, output


def _all_stats(base: float) -> dict[str, float | int]:
    values: dict[str, float | int] = {}
    for index, key in enumerate(extractor.STATISTIC_KEYS):
        values[key] = 25 if key.endswith("_count") else base + index / 100.0
    return values


def _query_rows(manifest_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "image_id": row["image_id"],
            "timestamp": row["timestamp"],
            "site": _all_stats(1.0),
            "background": _all_stats(0.5),
        }
        for row in manifest_rows
    ]


@pytest.mark.parametrize("value", [0, 51, "bad"])
def test_invalid_batch_size_is_rejected(value: object) -> None:
    with pytest.raises(extractor.DepthS1MatchedFeatureError, match="batch size"):
        batched.validate_batch_size(value)  # type: ignore[arg-type]


def test_batched_query_splits_and_preserves_order() -> None:
    manifest_rows = [
        {"image_id": f"S1A_{index:03d}", "timestamp": "2020-01-01T00:00:00+00:00"}
        for index in range(23)
    ]
    observed_sizes: list[int] = []

    def single_batch_query_fn(**kwargs: object) -> list[dict[str, object]]:
        rows = kwargs["manifest_rows"]
        assert isinstance(rows, list)
        observed_sizes.append(len(rows))
        return _query_rows(rows)

    result = batched.query_exact_s1_feature_summaries_batched(
        manifest_rows=manifest_rows,
        site_geometry_payload={"type": "Polygon"},
        background_geometry_payload={"type": "Polygon"},
        resolution_meters=10,
        batch_size=10,
        single_batch_query_fn=single_batch_query_fn,
    )

    assert observed_sizes == [10, 10, 3]
    assert [row["image_id"] for row in result] == [row["image_id"] for row in manifest_rows]


def test_batched_query_failure_message_leaks_no_private_values() -> None:
    manifest_rows = [
        {"image_id": f"S1A_{index:03d}", "timestamp": "2020-01-01T00:00:00+00:00"}
        for index in range(12)
    ]
    calls = 0

    def failing_query(**kwargs: object) -> list[dict[str, object]]:
        nonlocal calls
        calls += 1
        rows = kwargs["manifest_rows"]
        assert isinstance(rows, list)
        if calls == 2:
            raise RuntimeError(f"server failed for {PRIVATE_ID} at {PRIVATE_COORDINATE}")
        return _query_rows(rows)

    with pytest.raises(extractor.DepthS1MatchedFeatureError) as captured:
        batched.query_exact_s1_feature_summaries_batched(
            manifest_rows=manifest_rows,
            site_geometry_payload={"type": "Polygon"},
            background_geometry_payload={"type": "Polygon"},
            resolution_meters=10,
            batch_size=10,
            single_batch_query_fn=failing_query,
        )

    message = str(captured.value)
    assert "batch 2 of 2" in message
    assert "batch_size=2" in message
    assert PRIVATE_ID not in message
    assert PRIVATE_COORDINATE not in message


def test_batched_dry_run_performs_no_query(tmp_path: Path) -> None:
    site, background, manifest, output = _base_paths(tmp_path)
    called = False

    def query_fn(**_: object) -> list[dict[str, object]]:
        nonlocal called
        called = True
        return []

    result = batched.run_batched_matched_feature_extraction(
        site_geojson=site,
        background_geojson=background,
        match_manifest=manifest,
        output_path=output,
        execute=False,
        batch_size=2,
        single_batch_query_fn=query_fn,
    )

    assert result["status"] == "matched_s1_feature_extraction_dry_run_ready"
    assert result["batching_enabled"] is True
    assert result["batch_size"] == 2
    assert result["planned_batch_count"] == 2
    assert result["executed_batch_count"] == 0
    assert called is False
    assert not output.exists()


def test_batched_execute_writes_complete_private_output(tmp_path: Path) -> None:
    site, background, manifest, output = _base_paths(tmp_path)
    observed_sizes: list[int] = []

    def query_fn(**kwargs: object) -> list[dict[str, object]]:
        rows = kwargs["manifest_rows"]
        assert isinstance(rows, list)
        observed_sizes.append(len(rows))
        return _query_rows(rows)

    result = batched.run_batched_matched_feature_extraction(
        site_geojson=site,
        background_geojson=background,
        match_manifest=manifest,
        output_path=output,
        execute=True,
        batch_size=2,
        single_batch_query_fn=query_fn,
    )
    private_payload = json.loads(output.read_text(encoding="utf-8"))
    rendered = json.dumps(result)

    assert observed_sizes == [2, 1]
    assert result["status"] == "matched_s1_feature_extraction_complete"
    assert result["all_rows_complete"] is True
    assert result["executed_batch_count"] == 2
    assert result["missing_image_count"] == 0
    assert result["missing_statistic_count"] == 0
    assert len(private_payload["rows"]) == 3
    assert PRIVATE_COORDINATE not in rendered
    assert str(tmp_path) not in rendered
    assert result["image_ids_printed"] is False
    assert result["feature_values_printed"] is False
