from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import create_depth_site_polygon as polygon


def test_repository_local_output_is_rejected() -> None:
    with pytest.raises(polygon.DepthSitePolygonError, match="outside"):
        polygon.create_private_site_polygon(
            output_path=ROOT / "candidate.geojson",
            center_latitude=10.0,
            center_longitude=20.0,
            width_meters=50.0,
            height_meters=50.0,
            write=False,
        )


@pytest.mark.parametrize(
    ("latitude", "longitude", "width", "height"),
    [
        (86.0, 20.0, 50.0, 50.0),
        (10.0, 181.0, 50.0, 50.0),
        (10.0, 20.0, 0.0, 50.0),
        (10.0, 20.0, 50.0, -1.0),
        (math.nan, 20.0, 50.0, 50.0),
    ],
)
def test_invalid_polygon_inputs_are_rejected(
    latitude: float,
    longitude: float,
    width: float,
    height: float,
) -> None:
    with pytest.raises(polygon.DepthSitePolygonError):
        polygon.build_rectangle_geojson(
            center_latitude=latitude,
            center_longitude=longitude,
            width_meters=width,
            height_meters=height,
        )


def test_dry_run_writes_nothing_and_returns_aggregate_only(tmp_path: Path) -> None:
    output = tmp_path / "site.geojson"

    result = polygon.create_private_site_polygon(
        output_path=output,
        center_latitude=27.0,
        center_longitude=-97.0,
        width_meters=50.0,
        height_meters=50.0,
        write=False,
    )
    rendered = json.dumps(result)

    assert result["status"] == "private_site_polygon_dry_run_ready"
    assert result["output_written"] is False
    assert not output.exists()
    assert "27.0" not in rendered
    assert "-97.0" not in rendered
    assert str(output) not in rendered


def test_write_creates_closed_private_geojson_polygon(tmp_path: Path) -> None:
    output = tmp_path / "site.geojson"

    result = polygon.create_private_site_polygon(
        output_path=output,
        center_latitude=27.0,
        center_longitude=-97.0,
        width_meters=50.0,
        height_meters=50.0,
        write=True,
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    ring = payload["geometry"]["coordinates"][0]

    assert result["status"] == "private_site_polygon_written"
    assert result["output_written"] is True
    assert payload["type"] == "Feature"
    assert payload["properties"] == {}
    assert payload["geometry"]["type"] == "Polygon"
    assert len(ring) == 5
    assert ring[0] == ring[-1]
    assert min(point[0] for point in ring) < -97.0 < max(point[0] for point in ring)
    assert min(point[1] for point in ring) < 27.0 < max(point[1] for point in ring)


def test_existing_private_output_is_not_overwritten(tmp_path: Path) -> None:
    output = tmp_path / "site.geojson"
    output.write_text("original", encoding="utf-8")

    with pytest.raises(polygon.DepthSitePolygonError, match="already exists"):
        polygon.create_private_site_polygon(
            output_path=output,
            center_latitude=27.0,
            center_longitude=-97.0,
            width_meters=50.0,
            height_meters=50.0,
            write=True,
        )

    assert output.read_text(encoding="utf-8") == "original"


def test_result_never_contains_coordinates_or_private_path(tmp_path: Path) -> None:
    output = tmp_path / "private_site.geojson"
    result = polygon.create_private_site_polygon(
        output_path=output,
        center_latitude=12.345678,
        center_longitude=-45.678901,
        width_meters=70.0,
        height_meters=80.0,
        write=True,
    )
    rendered = json.dumps(result)

    assert result["coordinates_printed"] is False
    assert result["private_path_printed"] is False
    assert result["network_request_made"] is False
    assert "12.345678" not in rendered
    assert "-45.678901" not in rendered
    assert str(output) not in rendered
