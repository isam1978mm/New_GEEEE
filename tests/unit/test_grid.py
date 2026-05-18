from __future__ import annotations

from app.services.grid import build_grid_manifest


def test_grid_manifest_is_deterministic_for_same_input() -> None:
    first = build_grid_manifest(43.6532, -79.3832)
    second = build_grid_manifest(43.6532, -79.3832)
    assert first == second


def test_grid_manifest_changes_utm_zone_with_longitude() -> None:
    western = build_grid_manifest(43.6532, -79.3832)
    eastern = build_grid_manifest(43.6532, 31.2357)
    assert western.utm_zone != eastern.utm_zone
    assert western.epsg != eastern.epsg


def test_grid_manifest_uses_hemisphere_and_fixed_extent() -> None:
    north = build_grid_manifest(43.6532, -79.3832)
    south = build_grid_manifest(-33.8688, 151.2093)
    assert north.hemisphere == "north"
    assert south.hemisphere == "south"
    assert north.scale_m == 10
    assert north.size_px == 640
    assert north.bounds_m["xmin"] == -3200.0
    assert north.bounds_m["xmax"] == 3200.0
