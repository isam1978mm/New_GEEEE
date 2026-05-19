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
    assert "Blank Basemap" in response.text
    assert "External tiles disabled" in response.text
    assert "latitude" not in response.text.casefold()
    assert "longitude" not in response.text.casefold()
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
    assert '/artifacts/' in js_response.text
    assert 'FILESYSTEM_ONLY' in js_response.text
    assert 'experimental/' in js_response.text
    assert 'https://' not in js_response.text
    assert 'http://' not in js_response.text

    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert "@import" not in css_response.text
    assert "fonts.googleapis" not in css_response.text
