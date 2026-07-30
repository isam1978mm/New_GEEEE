from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def test_measured_anchor_template_is_safe_and_intentionally_incomplete() -> None:
    payload = json.loads(
        _read("docs/examples/operator_local_depth_first_aoi_template.geojson")
    )

    assert payload["type"] == "FeatureCollection"
    assert payload["template_only"] is True
    assert len(payload["features"]) == 2
    assert [feature["properties"]["role"] for feature in payload["features"]] == [
        "anchor",
        "anchor",
    ]
    assert all(
        coordinate is None
        for feature in payload["features"]
        for position in feature["geometry"]["coordinates"][0]
        for coordinate in position
    )
    assert any(
        "app uses every classifier finding automatically" in instruction.lower()
        for instruction in payload["instructions"]
    )


def test_local_depth_preflight_rejects_common_operator_input_errors() -> None:
    source = _read("frontend-v2/src/app/localDepthPreflight.ts")

    assert "still marked template_only" in source
    assert "Duplicate feature_id" in source
    assert "Do not upload candidate polygons" in source
    assert "Polygon or MultiPolygon" in source
    assert "must be closed" in source
    assert "finite numeric coordinates" in source
    assert "depth_min_m <= depth_best_m <= depth_max_m" in source
    assert "at least two distinct best-depth values" in source
    assert "replace-with" in source


def test_local_depth_panel_uses_anchors_and_automatic_findings() -> None:
    source = _read("frontend-v2/src/app/components/OperatorLocalDepthPanel.tsx")

    assert "Download measured-anchor template" in source
    assert "operator-local-depth-measured-anchors-template.geojson" in source
    assert "Preflight failed" in source
    assert "Preflight passed" in source
    assert "Every classifier finding will be used automatically" in source
    assert "Calibrate and estimate all findings" in source
    assert "No candidate AOI is uploaded" in source


def test_classifier_table_surfaces_depth_for_each_object() -> None:
    source = _read("frontend-v2/src/app/components/ClassifierResultsPanel.tsx")

    assert "Depth range" in source
    assert "Best depth" in source
    assert "Depth status" in source
    assert "finding-object-" in source
    assert "fetchOperatorLocalDepthResult" in source


def test_env_example_keeps_operator_local_depth_default_off() -> None:
    source = _read(".env.example")
    assert "OPERATOR_LOCAL_DEPTH_APP_ENABLED=false" in source
