from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "scan_icesat2_broad_track_campaign.py"
CONFIG_PATH = ROOT / "config" / "icesat2_broad_track_campaign_v2_phoenix.json"

SPEC = importlib.util.spec_from_file_location(
    "scan_icesat2_broad_track_campaign_v2_config", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_campaign_v2_configuration_loads_with_expected_region():
    campaign = MODULE.load_campaign(CONFIG_PATH)

    assert campaign.campaign_id == "southwest_us_earthwork_pilot_v2_phoenix"
    assert len(campaign.regions) == 1
    region = campaign.regions[0]
    assert region.region_id == "west_phoenix_lower_gila_pilot"
    assert region.west == -113.35
    assert region.south == 33.10
    assert region.east == -112.20
    assert region.north == 34.00


def test_campaign_v2_region_uses_one_utm_zone():
    campaign = MODULE.load_campaign(CONFIG_PATH)
    region = campaign.regions[0]
    center_lon = (region.west + region.east) / 2.0
    center_lat = (region.south + region.north) / 2.0

    assert MODULE.utm_epsg(center_lon, center_lat) == 32612


def test_campaign_v2_builds_projected_tiles():
    campaign = MODULE.load_campaign(CONFIG_PATH)
    epsg, tiles = MODULE.build_tiles(
        campaign.regions[0],
        tile_size_m=25_000.0,
        overlap_m=100.0,
    )

    assert epsg == 32612
    assert len(tiles) >= 20
    assert all(tile.xmax > tile.xmin for tile in tiles)
    assert all(tile.ymax > tile.ymin for tile in tiles)
