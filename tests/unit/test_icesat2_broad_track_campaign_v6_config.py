from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "scan_icesat2_broad_track_campaign.py"
CONFIG_PATH = (
    ROOT
    / "config"
    / "icesat2_broad_track_campaign_v6_central_florida_phosphate.json"
)
SPEC = importlib.util.spec_from_file_location(
    "scan_icesat2_broad_track_campaign_v6_config", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_campaign_006_config_loads_with_expected_identity_and_bounds():
    campaign = MODULE.load_campaign(CONFIG_PATH)

    assert campaign.campaign_id == (
        "southeast_us_earthwork_pilot_v6_central_florida_phosphate"
    )
    assert len(campaign.regions) == 1
    region = campaign.regions[0]
    assert region.region_id == "central_florida_bone_valley_phosphate_pilot"
    assert region.west == -82.20
    assert region.south == 27.20
    assert region.east == -81.55
    assert region.north == 28.20


def test_campaign_006_region_builds_multiple_valid_tiles():
    campaign = MODULE.load_campaign(CONFIG_PATH)
    epsg, tiles = MODULE.build_tiles(
        campaign.regions[0],
        tile_size_m=25_000.0,
        overlap_m=100.0,
    )

    assert epsg == 32617
    assert len(tiles) >= 8
    assert len({tile.tile_id for tile in tiles}) == len(tiles)
    assert all(tile.xmax > tile.xmin for tile in tiles)
    assert all(tile.ymax > tile.ymin for tile in tiles)
    assert all(len(tile.polygon_wgs84) == 5 for tile in tiles)


def test_campaign_006_is_distinct_from_prior_campaign_ids():
    campaign = MODULE.load_campaign(CONFIG_PATH)

    assert campaign.campaign_id not in {
        "southwest_us_earthwork_pilot_v1",
        "southwest_us_earthwork_pilot_v2_phoenix",
        "southwest_us_earthwork_pilot_v3_imperial_valley",
        "southwest_us_earthwork_pilot_v4_el_paso_las_cruces",
        "southwest_us_earthwork_pilot_v5_tucson_marana",
    }
