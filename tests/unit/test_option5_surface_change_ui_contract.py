from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "frontend-v2" / "src" / "app" / "components" / "ClassifierResultsPanel.tsx"
ADAPTER = ROOT / "frontend-v2" / "src" / "app" / "api" / "surfaceChangeResults.ts"


def test_surface_change_panel_keeps_radar_only_boundary() -> None:
    source = PANEL.read_text(encoding="utf-8")
    lower = source.lower()

    assert "Dual-window radar surface-change review" in source
    assert "RADAR BACKSCATTER ONLY" in source
    assert "NOT DEPTH OR SETTLEMENT" in source
    assert "moisture, vegetation and surface roughness may contribute" in lower
    assert "not measured displacement, settlement, physical confirmation, or depth" in lower
    assert "review_pixel_fraction" in source
    assert "review_threshold_db" in source


def test_surface_change_adapter_uses_public_summary_only() -> None:
    source = ADAPTER.read_text(encoding="utf-8")

    assert 'ARTIFACT_NAME = "option5_surface_change_summary"' in source
    assert 'FILENAME = "option5_surface_change_summary.json"' in source
    assert 'status: "available" | "not_available"' in source
    assert "coordinates" not in source.lower()
    assert "geometry" not in source.lower()


def test_surface_change_panel_has_clear_abstention_reasons() -> None:
    source = PANEL.read_text(encoding="utf-8")

    assert "insufficient_compatible_pixels" in source
    assert "insufficient_after_pairs" in source
    assert "insufficient_before_pairs" in source
    assert "orbit_signature_mismatch" in source
    assert "Older runs must be rerun after this stage is enabled" in source
