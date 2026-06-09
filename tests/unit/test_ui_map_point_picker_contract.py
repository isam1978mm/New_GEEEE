"""Static contract tests for the target map picker wiring."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
WORKFLOW = ROOT / "frontend-v2" / "src" / "app" / "components" / "RunWorkflowCard.tsx"
TARGET_MAP = ROOT / "frontend-v2" / "src" / "app" / "components" / "TargetLeafletMap.tsx"
PACKAGE_JSON = ROOT / "frontend-v2" / "package.json"


def read(path: Path) -> str:
    assert path.exists(), f"missing expected file: {path}"
    return path.read_text(encoding="utf-8")


def test_workflow_uses_target_map_component() -> None:
    text = read(WORKFLOW)
    assert "TargetLeafletMap" in text
    assert "Large map target picker" in text
    assert "mouse drag + scroll zoom" in text
    assert "BigMapPicker" not in text
    assert "buildTiles" not in text


def test_target_map_component_exists() -> None:
    text = read(TARGET_MAP)
    assert "MapContainer" in text
    assert "scrollWheelZoom" in text
    assert "doubleClickZoom" in text
    assert "dragging" in text
    assert "Marker" in text


def test_target_map_dependencies_declared() -> None:
    package = json.loads(read(PACKAGE_JSON))
    assert "leaflet" in package.get("dependencies", {})
    assert "react-leaflet" in package.get("dependencies", {})
    assert "@types/leaflet" in package.get("devDependencies", {})
