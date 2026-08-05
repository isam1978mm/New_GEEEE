from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from scripts.fetch_tyrone_usgs_imagery_review_pack import (
    TileSpec,
    build_contact_sheet,
    build_export_url,
    build_tile_specs,
    center_to_web_mercator,
    validate_grid_size,
    write_manifest,
)


@pytest.mark.parametrize("value", [1, 3, 5, 9])
def test_validate_grid_size_accepts_positive_odd_values(value: int) -> None:
    assert validate_grid_size(value) == value


@pytest.mark.parametrize("value", [0, 2, 10, -1])
def test_validate_grid_size_rejects_invalid_values(value: int) -> None:
    with pytest.raises(ValueError):
        validate_grid_size(value)


def test_build_tile_specs_has_expected_order_and_extent() -> None:
    specs = build_tile_specs(
        center_x=1000.0,
        center_y=2000.0,
        grid_size=3,
        tile_span_m=100.0,
    )

    assert len(specs) == 9
    assert specs[0].tile_id == "R1C1"
    assert specs[0].center_easting_3857 == 900.0
    assert specs[0].center_northing_3857 == 2100.0
    assert specs[4].tile_id == "R2C2"
    assert specs[4].bbox == "950.000,1950.000,1050.000,2050.000"
    assert specs[-1].tile_id == "R3C3"


def test_center_to_web_mercator_returns_finite_values() -> None:
    x, y = center_to_web_mercator(-108.36, 32.658333)

    assert -12_100_000 < x < -12_000_000
    assert 3_800_000 < y < 3_900_000


def test_build_export_url_contains_coordinate_parameters() -> None:
    spec = TileSpec(
        tile_id="R1C1",
        row=1,
        column=1,
        xmin=1.0,
        ymin=2.0,
        xmax=3.0,
        ymax=4.0,
        center_easting_3857=2.0,
        center_northing_3857=3.0,
    )

    url = build_export_url(
        service_url="https://example.test/export",
        spec=spec,
        tile_pixels=1024,
    )

    assert "bbox=1.000%2C2.000%2C3.000%2C4.000" in url
    assert "bboxSR=3857" in url
    assert "imageSR=3857" in url
    assert "size=1024%2C1024" in url
    assert "f=image" in url


def test_contact_sheet_and_manifest_keep_geometry_closed(tmp_path: Path) -> None:
    spec = TileSpec(
        tile_id="R1C1",
        row=1,
        column=1,
        xmin=1.0,
        ymin=2.0,
        xmax=3.0,
        ymax=4.0,
        center_easting_3857=2.0,
        center_northing_3857=3.0,
    )
    contact = tmp_path / "contact.jpg"
    manifest = tmp_path / "manifest.json"
    build_contact_sheet(
        tiles=[(spec, Image.new("RGB", (100, 100), "white"), None)],
        grid_size=1,
        output_path=contact,
        thumbnail_px=80,
    )
    write_manifest(
        output_path=manifest,
        service_url="https://example.test/export",
        center_lon=-108.36,
        center_lat=32.658333,
        center_x=1.0,
        center_y=2.0,
        grid_size=1,
        tile_span_m=3000.0,
        tile_pixels=1536,
        tiles=[
            {
                "tile_id": "R1C1",
                "status": "downloaded",
                "image": "R1C1.jpg",
            }
        ],
        contact_sheet=contact,
    )

    assert contact.exists()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["status"] == "usgs_imagery_review_pack_created"
    assert payload["successful_tile_count"] == 1
    assert payload["coordinate_geometry_unblocked"] is False
    assert payload["numerical_depth_unlocked"] is False
