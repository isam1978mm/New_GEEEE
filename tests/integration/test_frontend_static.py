from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.main import create_app


REACT_MARKERS = (
    "Dashboard",
    "Run Archive",
    "Exports",
    "Diagnostics",
    "Recent Runs",
    "Candidate Focus",
    "Status History",
)


def _bundle_text(client: TestClient, index_html: str) -> str:
    asset_paths = re.findall(r'src="(/v2/assets/[^"]+\.js)"', index_html)
    assert asset_paths
    return "\n".join(client.get(path).text for path in asset_paths)


def test_react_frontend_is_default_ui_and_v2_alias_uses_same_build() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    root_response = client.get("/")
    v2_response = client.get("/v2")
    ui_deep_response = client.get("/app/runs/anything")
    v2_deep_response = client.get("/v2/runs/anything")

    assert root_response.status_code == 200
    assert "text/html" in root_response.headers["content-type"]
    assert "GEE Screening Dashboard Design" in root_response.text
    assert 'id="root"' in root_response.text
    assert "/v2/assets/" in root_response.text
    assert "GEE Screening Workspace" not in root_response.text
    assert 'src="/app.js"' not in root_response.text
    assert 'href="/style.css"' not in root_response.text

    assert v2_response.status_code == 200
    assert v2_response.text == root_response.text

    assert ui_deep_response.status_code == 200
    assert "GEE Screening Dashboard Design" in ui_deep_response.text

    assert v2_deep_response.status_code == 200
    assert "GEE Screening Dashboard Design" in v2_deep_response.text


def test_api_routes_take_precedence_over_react_spa_fallback() -> None:
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        runs_response = client.get("/runs")
        missing_run_response = client.get("/runs/not-a-real-run-id")
        health_response = client.get("/healthz")
        ready_response = client.get("/readyz")

    assert runs_response.status_code == 200
    assert "application/json" in runs_response.headers["content-type"]
    assert runs_response.text != ""
    assert "GEE Screening Dashboard Design" not in runs_response.text

    assert missing_run_response.status_code == 404
    assert "application/json" in missing_run_response.headers["content-type"]
    assert "GEE Screening Dashboard Design" not in missing_run_response.text

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert "GEE Screening Dashboard Design" not in health_response.text

    assert ready_response.status_code in {200, 503}
    assert "application/json" in ready_response.headers["content-type"]
    assert "GEE Screening Dashboard Design" not in ready_response.text


def test_react_bundle_uses_real_run_apis_without_sensitive_content() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)
    index_response = client.get("/")
    assert index_response.status_code == 200

    bundle_text = _bundle_text(client, index_response.text)
    for marker in REACT_MARKERS:
        assert marker in bundle_text

    assert "Run Workflow" in bundle_text
    assert "Queue a new screening run" in bundle_text
    assert "Queue Run" in bundle_text
    assert "Target Preview" in bundle_text
    assert "Advanced / unavailable outputs" in bundle_text
    assert "Latitude" in bundle_text
    assert "Longitude" in bundle_text
    assert "Run name" in bundle_text
    assert '"/runs"' in bundle_text
    assert "encodeURIComponent" in bundle_text
    assert "/outputs" in bundle_text
    assert "setTimeout" in bundle_text
    assert "2000" in bundle_text
    assert "Status updates paused" in bundle_text
    assert "Delete run?" in bundle_text
    assert "Delete permanently" in bundle_text
    assert "Cannot delete active run" in bundle_text
    assert "This permanently deletes the run record and all files for this run." in bundle_text
    assert "Disk used" in bundle_text
    assert "File count" in bundle_text
    assert "Last scanned" in bundle_text
    assert "Estimated size" in bundle_text
    assert "Unknown size" in bundle_text
    assert "Deleted Runs / Cleanup Summary" in bundle_text
    assert "Total freed" in bundle_text
    assert "Storage Health" in bundle_text
    assert "Cleanup recommended" in bundle_text
    assert "Storage healthy" in bundle_text
    assert "Largest runs" in bundle_text
    assert "Oldest runs" in bundle_text
    assert "Stale failed runs" in bundle_text
    assert "No runs yet." in bundle_text
    assert "No archived runs yet. Queue a run from Dashboard to populate this local archive." in bundle_text
    assert "No runs match this filter. Clear search or set Status filter to All statuses." in bundle_text
    assert "No terminal runs are ready for cleanup suggestions yet." in bundle_text
    assert "No stale failed runs need cleanup attention." in bundle_text
    assert "No deleted run audit records yet. Deleted terminal runs will appear here with freed storage totals." in bundle_text
    assert "Run disk usage is still being scanned." in bundle_text
    assert "Search runs" in bundle_text
    assert "Status filter" in bundle_text
    assert "Sort runs" in bundle_text
    assert "Newest first" in bundle_text
    assert "Oldest first" in bundle_text
    assert "Largest first" in bundle_text
    assert "Smallest first" in bundle_text
    assert "Most files" in bundle_text
    assert "Name A-Z" in bundle_text
    assert "DELETE" in bundle_text
    assert "External map tiles" in bundle_text
    assert "Disabled by default" in bundle_text
    assert "Tile URL template" in bundle_text
    assert "Privacy warning" in bundle_text
    assert "Status polling interval" in bundle_text
    assert "read-only" in bundle_text
    assert "Show advanced / unavailable outputs" in bundle_text
    assert "Private overlay must show coordinate-free summaries only" in bundle_text
    assert "verify existing UI safety tests before changing this panel" in bundle_text
    assert "Start a local operator session to request operator-only coordinate-free summaries." in bundle_text
    assert "Pick or enter a target, preview safe grid metadata, optionally dry-run Earth Engine planning, then queue the local run." in bundle_text
    assert "Queue Run stays disabled until both target fields are valid." in bundle_text
    assert "Earth Engine planning is a dry run only; it checks backend readiness before execution." in bundle_text
    assert "exports may appear after completion" in bundle_text
    assert "Classifier Results" in bundle_text
    assert "Final area findings summary" in bundle_text
    assert "App score" in bundle_text
    assert "about a 30% signal" not in bundle_text
    assert "tied for the highest app score" in bundle_text
    assert "Depth estimate: not available." in bundle_text
    assert "Full export tree and unavailable-output status are available" in bundle_text
    assert "No status history events are available yet. Queued runs may not record detailed stage events until processing starts." in bundle_text
    assert "H5 operator aggregate summary" in bundle_text
    assert "Aggregate prediction summary" in bundle_text
    assert "No row-level output" in bundle_text
    assert "/operator/h5/aggregate-summary" in bundle_text
    assert "Run QA summaries" in bundle_text
    assert "DEM / Grid QA" in bundle_text
    assert "SAR QA" in bundle_text
    assert "Stack / S2 / Thermal QA" in bundle_text
    assert "Alignment QA" in bundle_text
    assert "Accepted exceptions" in bundle_text
    assert "PCA variance capture: 94.2%" not in bundle_text
    assert "S2 cloud coverage: 18%" not in bundle_text
    assert "nearest-clear S2 composite" not in bundle_text
    assert "SAR backscatter exceeds threshold" not in bundle_text
    assert "Check SAR source data for corrupted scenes" not in bundle_text
    assert "Failed at SAR" not in bundle_text
    assert "Run is stale_failed." in bundle_text
    assert "No terminal failure message was recorded." in bundle_text
    assert "GEE Screening Operator Mock V2" not in bundle_text
    assert "Mock Data only" not in bundle_text
    assert "Target reference" not in bundle_text
    assert "Accept SAR residual xfail" not in bundle_text
    assert "demoMode" not in bundle_text
    assert "mockData" not in bundle_text
    assert "exact coordinates" not in bundle_text.casefold()
    assert "private coordinates" not in bundle_text.casefold()
    assert "37.7749" not in bundle_text
    assert "-122.4194" not in bundle_text
    assert "C:\\" not in bundle_text
    assert "/Users/" not in bundle_text
    assert "/home/" not in bundle_text
    assert "data/runs/" not in bundle_text
    assert ".env" not in bundle_text
    assert "service-account" not in bundle_text
    assert "fonts.googleapis" not in bundle_text
    assert "googletagmanager" not in bundle_text
    assert "cdn." not in bundle_text.casefold()
