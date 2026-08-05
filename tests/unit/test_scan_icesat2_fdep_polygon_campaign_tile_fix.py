from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import pytest

import scan_icesat2_fdep_polygon_campaign as campaign
from scan_icesat2_fdep_polygon_campaign_fixed import (
    install_fix,
    tile_bbox_wgs84,
)
from scan_icesat2_regional_expansion import QueryTile


def _dictionary_tile() -> QueryTile:
    return QueryTile(
        tile_id="r000_c000",
        xmin=0.0,
        ymin=0.0,
        xmax=1.0,
        ymax=1.0,
        polygon_wgs84=(
            {"lon": -82.0, "lat": 27.0},
            {"lon": -81.5, "lat": 27.0},
            {"lon": -81.5, "lat": 27.5},
            {"lon": -82.0, "lat": 27.5},
            {"lon": -82.0, "lat": 27.0},
        ),
    )


def test_real_query_tile_dictionary_vertices_are_supported() -> None:
    assert tile_bbox_wgs84(_dictionary_tile()) == (-82.0, 27.0, -81.5, 27.5)


def test_sequence_vertices_remain_supported() -> None:
    class SequenceTile:
        polygon_wgs84 = (
            (-82.0, 27.0),
            (-81.5, 27.0),
            (-81.5, 27.5),
            (-82.0, 27.5),
        )

    assert tile_bbox_wgs84(SequenceTile()) == (-82.0, 27.0, -81.5, 27.5)


def test_invalid_dictionary_vertex_fails_clearly() -> None:
    class InvalidTile:
        polygon_wgs84 = ({"lon": -82.0},)

    with pytest.raises(ValueError, match="numeric"):
        tile_bbox_wgs84(InvalidTile())


def test_install_fix_repairs_original_tile_selection() -> None:
    install_fix()
    polygon = [
        [
            (-81.9, 27.1),
            (-81.6, 27.1),
            (-81.6, 27.4),
            (-81.9, 27.4),
            (-81.9, 27.1),
        ]
    ]

    assert campaign.select_polygon_tiles([_dictionary_tile()], [polygon]) == [
        _dictionary_tile()
    ]
