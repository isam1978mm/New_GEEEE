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
    "Key Downloads",
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
    assert "DELETE" in bundle_text
    assert "GEE Screening Operator Mock V2" not in bundle_text
    assert "Mock Data only" not in bundle_text
    assert "Target reference" not in bundle_text
    assert "Accept SAR residual xfail" not in bundle_text
    assert "demoMode" not in bundle_text
    assert "mockData" not in bundle_text
    assert "coordinates" not in bundle_text.casefold()
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
