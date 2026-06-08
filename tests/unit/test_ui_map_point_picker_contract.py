"""Static contract tests for UI-MAP-1 real point picker."""
from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
_RUN_WORKFLOW_CARD = _ROOT / "frontend-v2" / "src" / "app" / "components" / "RunWorkflowCard.tsx"
_PACKAGE_JSON = _ROOT / "frontend-v2" / "package.json"
_DOC = _ROOT / "docs" / "UI_MAP_1_REAL_POINT_PICKER.md"


def _read(path: Path) -> str:
    assert path.exists(), f"missing expected file: {path}"
    return path.read_text(encoding="utf-8")


def test_ui_map_doc_exists_and_states_problem() -> None:
    text = _read(_DOC)
    assert "blank local grid" in text
    assert "real map-style point picker" in text
    assert "External map tiles are disabled by default" in text


def test_fake_point_grid_removed() -> None:
    text = _read(_RUN_WORKFLOW_CARD)
    assert "Point picker" not in text
    assert "Click to seed point" not in text
    assert "linear-gradient" not in text


def test_real_map_picker_present() -> None:
    text = _read(_RUN_WORKFLOW_CARD)
    assert "Map point picker" in text
    assert "real map tiles" in text
    assert "Click map to place target pin" in text
    assert "Target map center tile" in text


def test_map_click_updates_target_from_web_mercator_math() -> None:
    text = _read(_RUN_WORKFLOW_CARD)
    assert "function handleMapClick" in text
    assert "pixelToLatLon" in text
    assert "setLatitude(point.lat.toFixed(8))" in text
    assert "setLongitude(point.lon.toFixed(8))" in text
    assert "latLonToPixel" in text


def test_map_uses_existing_external_tile_setting_boundary() -> None:
    text = _read(_RUN_WORKFLOW_CARD)
    assert "externalTilesEnabled" in text
    assert "tileUrlTemplate" in text
    assert "Map picker disabled" in text
    assert "Enable External map tiles in Settings" in text


def test_no_new_frontend_dependency_added_for_map() -> None:
    package = json.loads(_read(_PACKAGE_JSON))
    deps = package.get("dependencies", {})
    for package_name in ("leaflet", "react-leaflet", "mapbox-gl", "ol"):
        assert package_name not in deps
