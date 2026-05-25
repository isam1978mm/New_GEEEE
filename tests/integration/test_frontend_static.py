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
    assert "Manual Pin Workspace" in response.text
    assert "External tiles disabled" in response.text
    assert "Queue local run" in response.text
    assert "Stage a local point" in response.text
    assert "Run lookup" in response.text
    assert "Refresh runs" in response.text
    assert "Load run" in response.text
    assert "latitude" not in response.text.casefold()
    assert "longitude" not in response.text.casefold()
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
