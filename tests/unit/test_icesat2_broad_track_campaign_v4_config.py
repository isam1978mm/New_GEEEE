from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "scan_icesat2_broad_track_campaign.py"
CONFIG_PATH = (
    ROOT / "config" / "icesat2_broad_track_campaign_v4_el_paso_las_cruces.json"
)
SPEC = importlib.util.spec_from_file_location(
    "scan_icesat2_broad_track_campaign_v4_config", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_campaign_004_config_loads_with_expected_identity_and_bounds():
    campaign = MODULE.load_campaign(CONFIG_PATH)

    assert campaign.campaign_id == (
        "southwest_us_earthwork_pilot_v4_el_paso_las_cruces"
    )
    assert len(campaign.regions) == 1
    region = campaign.regions[0]
    assert region.region_id == "el_paso_las_cruces_lower_rio_grande_pilot"
    assert region.west == -107.25
    assert region.south == 31.76
    assert region.east == -106.05
    assert region.north == 32.76


def test_campaign_004_region_builds_multiple_valid_tiles():
    campaign = MODULE.load_campaign(CONFIG_PATH)
    epsg, tiles = MODULE.build_tiles(
        campaign.regions[0],
        tile_size_m=25_000.0,
        overlap_m=100.0,
    )

    assert epsg == 32613
    assert len(tiles) >= 16
    assert len({tile.tile_id for tile in tiles}) == len(tiles)
    assert all(tile.xmax > tile.xmin for tile in tiles)
    assert all(tile.ymax > tile.ymin for tile in tiles)
    assert all(len(tile.polygon_wgs84) == 5 for tile in tiles)


def test_campaign_004_is_distinct_from_prior_campaign_ids():
    campaign = MODULE.load_campaign(CONFIG_PATH)

    assert campaign.campaign_id not in {
        "southwest_us_earthwork_pilot_v1",
        "southwest_us_earthwork_pilot_v2_phoenix",
        "southwest_us_earthwork_pilot_v3_imperial_valley",
    }
