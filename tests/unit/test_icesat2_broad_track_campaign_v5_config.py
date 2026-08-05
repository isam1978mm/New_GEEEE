from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "scan_icesat2_broad_track_campaign.py"
CONFIG_PATH = ROOT / "config" / "icesat2_broad_track_campaign_v5_tucson_marana.json"
SPEC = importlib.util.spec_from_file_location(
    "scan_icesat2_broad_track_campaign_v5_config", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_campaign_005_config_loads_with_expected_identity_and_bounds():
    campaign = MODULE.load_campaign(CONFIG_PATH)

    assert campaign.campaign_id == "southwest_us_earthwork_pilot_v5_tucson_marana"
    assert len(campaign.regions) == 1
    region = campaign.regions[0]
    assert region.region_id == "tucson_marana_santa_cruz_valley_pilot"
    assert region.west == -111.30
    assert region.south == 31.90
    assert region.east == -110.80
    assert region.north == 32.75


def test_campaign_005_region_builds_multiple_valid_tiles_in_utm_zone_12():
    campaign = MODULE.load_campaign(CONFIG_PATH)
    epsg, tiles = MODULE.build_tiles(
        campaign.regions[0],
        tile_size_m=25_000.0,
        overlap_m=100.0,
    )

    assert epsg == 32612
    assert len(tiles) >= 8
    assert len({tile.tile_id for tile in tiles}) == len(tiles)
    assert all(tile.xmax > tile.xmin for tile in tiles)
    assert all(tile.ymax > tile.ymin for tile in tiles)
    assert all(len(tile.polygon_wgs84) == 5 for tile in tiles)


def test_campaign_005_is_distinct_from_prior_campaign_ids_and_campaign_004_bounds():
    campaign = MODULE.load_campaign(CONFIG_PATH)
    region = campaign.regions[0]

    assert campaign.campaign_id not in {
        "southwest_us_earthwork_pilot_v1",
        "southwest_us_earthwork_pilot_v2_phoenix",
        "southwest_us_earthwork_pilot_v3_imperial_valley",
        "southwest_us_earthwork_pilot_v4_el_paso_las_cruces",
    }
    assert region.east < -107.25
