from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_frontend_spa_shell_is_served_locally_without_external_assets() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "GEE Screening Workspace" in response.text
    assert 'src="/app.js"' in response.text
    assert 'href="/style.css"' in response.text
    assert "Target Input" in response.text
    assert "External tiles disabled" in response.text
    assert "Queue run" in response.text
    assert 'id="target-lat"' in response.text
    assert 'id="target-lon"' in response.text
    assert "Current stage" in response.text
    assert "stage-progress-list" in response.text
    assert "Status history" in response.text
    assert "status-history-list" in response.text
    assert "What outputs will I get?" in response.text
    assert "public-safe artifacts" in response.text
    assert "data/runs/&lt;run_id&gt;/" in response.text
    assert "guarded links" in response.text
    assert "FILESYSTEM_ONLY" in response.text
    assert "GRID/DEM" in response.text
    assert "SAR" in response.text
    assert "Sentinel-2 indices" in response.text
    assert "DEM derivatives" in response.text
    assert "thermal" in response.text
    assert "hypercube/PCA" in response.text
    assert "object extraction" in response.text
    assert "alignment QA" in response.text
    assert "docs/RUN_OUTPUTS.md" in response.text
    assert 'href="docs/RUN_OUTPUTS.md"' not in response.text
    assert "Run lookup" in response.text
    assert "Refresh runs" in response.text
    assert "Load run" in response.text
    assert "Manual Pin Workspace" not in response.text
    assert "Stage a local point" not in response.text
    assert "pin-map" not in response.text
    assert "geojson" not in response.text.casefold()
    assert "wkt" not in response.text.casefold()
    assert "cdn" not in response.text.casefold()
    assert "fonts.googleapis" not in response.text.casefold()
    assert "googletagmanager" not in response.text.casefold()
    assert "experimental/" not in response.text


def test_frontend_assets_are_served_and_guarded_artifact_path_is_used() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    js_response = client.get("/app.js")
    css_response = client.get("/style.css")

    assert js_response.status_code == 200
    assert "application/javascript" in js_response.headers["content-type"] or "text/javascript" in js_response.headers["content-type"]
    assert 'externalTilesEnabled: false' in js_response.text
    assert 'fetch("/runs"' in js_response.text
    assert 'fetch("/runs")' in js_response.text
    assert "fetch(`/runs/${encodeURIComponent(runId)}`)" in js_response.text
    assert 'method: "POST"' in js_response.text
    assert "loadRecentRuns" in js_response.text
    assert "selectRun" in js_response.text
    assert "run-lookup-form" in js_response.text
    assert "run-history-list" in js_response.text
    assert "target-lat" in js_response.text
    assert "target-lon" in js_response.text
    assert "renderStageProgress" in js_response.text
    assert "renderStatusHistory" in js_response.text
    assert "current_stage" in js_response.text
    assert "history" in js_response.text
    assert "Completed" in js_response.text
    assert "Waiting for first stage" in js_response.text
    assert "Historical run; detailed stage progress is unavailable." in js_response.text
    assert "Detailed stage progress is unavailable for this failed run." in js_response.text
    assert "Waiting for first stage update." in js_response.text
    assert "No detailed status history is available for this run." in js_response.text
    assert "Stage progress is not available yet." not in js_response.text
    assert "Status history is not available yet." not in js_response.text
    assert "stage-progress-list" in js_response.text
    assert "status-history-list" in js_response.text
    assert "selectedPoint" not in js_response.text
    assert "pin-map" not in js_response.text
    assert "stagePointFromNormalized" not in js_response.text
    assert '/artifacts/' in js_response.text
    assert 'FILESYSTEM_ONLY' in js_response.text
    assert "experimental_" in js_response.text
    assert "sampleArtifacts" not in js_response.text
    assert "demo-run" not in js_response.text
    assert "Artifacts will appear after a run completes." in js_response.text
    assert "Run completed with no public artifacts." in js_response.text
    assert 'GeoJSON' not in js_response.text
    assert 'WKT' not in js_response.text
    assert "relative_path" not in js_response.text
    assert "display_label" not in js_response.text
    assert "run_id" not in js_response.text
    assert 'https://' not in js_response.text
    assert 'http://' not in js_response.text

    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert "@import" not in css_response.text
    assert "fonts.googleapis" not in css_response.text
