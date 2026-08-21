from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def test_first_aoi_template_is_safe_and_intentionally_incomplete() -> None:
    payload = json.loads(
        _read("docs/examples/operator_local_depth_first_aoi_template.geojson")
    )

    assert payload["type"] == "FeatureCollection"
    assert payload["template_only"] is True
    assert len(payload["features"]) == 3
    assert [feature["properties"]["role"] for feature in payload["features"]] == [
        "anchor",
        "anchor",
        "candidate",
    ]
    assert all(
        coordinate is None
        for feature in payload["features"]
        for position in feature["geometry"]["coordinates"][0]
        for coordinate in position
    )


def test_local_depth_preflight_rejects_common_operator_input_errors() -> None:
    source = _read("frontend-v2/src/app/localDepthPreflight.ts")

    assert "still marked template_only" in source
    assert "Duplicate feature_id" in source
    assert "use anchor or candidate" in source
    assert "Polygon or MultiPolygon" in source
    assert "must be closed" in source
    assert "finite numeric coordinates" in source
    assert "depth_min_m <= depth_best_m <= depth_max_m" in source
    assert "at least two distinct best-depth values" in source
    assert "replace-with" in source


def test_local_depth_panel_exposes_recorded_lookup_without_calibration_ui() -> None:
    source = _read("frontend-v2/src/app/components/OperatorLocalDepthPanel.tsx")

    assert "Recorded measured depth" in source
    assert "Load reviewed recorded measurements" in source
    assert "not predicted from this run" in source
    assert "return null" not in source
    assert "Local depth calibration" not in source
    assert "Run local depth calibration" not in source
    assert "Download blank GeoJSON template" not in source
    assert "GeoJSON" not in source
    assert "calibration_dataset_version" not in source
    assert "anchor" not in source.lower()


def test_env_example_keeps_operator_local_depth_default_off() -> None:
    source = _read(".env.example")

    assert "OPERATOR_LOCAL_DEPTH_APP_ENABLED=false" in source
