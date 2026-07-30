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


def test_site_calibration_is_a_settings_workflow() -> None:
    settings_source = _read("frontend-v2/src/app/components/SettingsPage.tsx")
    private_overlay_source = _read(
        "frontend-v2/src/app/components/OperatorPrivateOverlayPanel.tsx"
    )
    panel_source = _read(
        "frontend-v2/src/app/components/OperatorLocalDepthPanel.tsx"
    )

    assert "<OperatorLocalDepthPanel" in settings_source
    assert "readSelectedRunId" in settings_source
    assert "<OperatorLocalDepthPanel" not in private_overlay_source
    assert "Site depth calibration — one-time setup" in panel_source
    assert "Known-depth reference zones (surveyed)" in panel_source
    assert "Calibration only — not a new AOI analysis" in panel_source
    assert "No finding or candidate AOI is uploaded" in panel_source
    assert "Dashboard → Classifier Results" in panel_source


def test_saved_calibration_hides_setup_and_points_to_classifier_results() -> None:
    source = _read("frontend-v2/src/app/components/OperatorLocalDepthPanel.tsx")

    assert "fetchOperatorLocalDepthResult" in source
    assert "hasCompletedCalibration && !editing" in source
    assert "Replace saved calibration" in source
    assert "setup form is hidden because this run is already calibrated" in source
    assert "Save calibration and estimate every finding" in source
    assert "<Header>Finding</Header>" not in source


def test_classifier_table_surfaces_depth_for_each_object() -> None:
    source = _read("frontend-v2/src/app/components/ClassifierResultsPanel.tsx")

    assert "Depth range" in source
    assert "Best depth" in source
    assert "Depth status" in source
    assert "finding-object-" in source
    assert "fetchOperatorLocalDepthResult" in source


def test_selected_run_is_remembered_without_storing_credentials() -> None:
    selected_run_source = _read("frontend-v2/src/app/selectedRun.ts")
    status_source = _read("frontend-v2/src/app/components/StatusStrip.tsx")

    assert "gs_selected_run_id_v1" in selected_run_source
    assert "rememberSelectedRunId(runId)" in status_source
    assert "accessToken" not in selected_run_source
    assert "Authorization" not in selected_run_source


def test_env_example_keeps_operator_local_depth_default_off() -> None:
    source = _read(".env.example")

    assert "OPERATOR_LOCAL_DEPTH_APP_ENABLED=false" in source
