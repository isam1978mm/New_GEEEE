from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.pipeline.elevation_change.icesat2_repeat import Icesat2Segment


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "scan_icesat2_broad_track_campaign.py"
)
SPEC = importlib.util.spec_from_file_location(
    "scan_icesat2_broad_track_campaign", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _write_campaign(path: Path, regions: list[dict[str, object]]) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": MODULE.CONFIG_SCHEMA,
                "campaign_id": "campaign_a",
                "description": "test",
                "regions": regions,
            }
        ),
        encoding="utf-8",
    )
    return path


def _segment() -> Icesat2Segment:
    return Icesat2Segment(
        segment_id="123",
        observed_at=datetime(2022, 1, 1, tzinfo=UTC),
        longitude=-115.2,
        latitude=36.0,
        x_m=660_000.0,
        y_m=3_985_000.0,
        height_m=100.4,
        height_uncertainty_m=2.0,
        terrain_slope=0.01,
        ground_photon_count=50,
        rgt=45,
        cycle=16,
        spot=5,
        gt="gt1l",
    )


def test_load_campaign_skips_disabled_regions(tmp_path: Path):
    path = _write_campaign(
        tmp_path / "campaign.json",
        [
            {
                "region_id": "enabled",
                "west": -116.0,
                "south": 35.0,
                "east": -115.0,
                "north": 36.0,
            },
            {
                "region_id": "disabled",
                "west": -115.0,
                "south": 35.0,
                "east": -114.0,
                "north": 36.0,
                "enabled": False,
            },
        ],
    )

    campaign = MODULE.load_campaign(path)

    assert campaign.campaign_id == "campaign_a"
    assert [item.region_id for item in campaign.regions] == ["enabled"]


def test_load_campaign_rejects_unordered_bounds(tmp_path: Path):
    path = _write_campaign(
        tmp_path / "campaign.json",
        [
            {
                "region_id": "bad",
                "west": -114.0,
                "south": 35.0,
                "east": -115.0,
                "north": 36.0,
            }
        ],
    )

    try:
        MODULE.load_campaign(path)
    except ValueError as exc:
        assert "longitude bounds" in str(exc)
    else:
        raise AssertionError("unordered bounds should fail")


def test_utm_epsg_handles_northern_and_southern_hemispheres():
    assert MODULE.utm_epsg(-115.0, 36.0) == 32611
    assert MODULE.utm_epsg(18.0, -33.0) == 32734


def test_build_tiles_covers_region_with_unique_closed_polygons():
    region = MODULE.RegionSpec(
        region_id="region",
        description="",
        west=-115.75,
        south=35.55,
        east=-114.65,
        north=36.45,
    )

    epsg, tiles = MODULE.build_tiles(
        region,
        tile_size_m=25_000.0,
        overlap_m=100.0,
    )

    assert epsg == 32611
    assert len(tiles) >= 16
    assert len({item.tile_id for item in tiles}) == len(tiles)
    assert all(len(item.polygon_wgs84) == 5 for item in tiles)
    assert all(
        item.polygon_wgs84[0] == item.polygon_wgs84[-1]
        for item in tiles
    )


def test_cache_round_trip(tmp_path: Path):
    path = tmp_path / "tile.json"
    signature = MODULE._signature(
        "region",
        "r000_c000",
        "2018-10-13T00:00:00Z",
        "2026-08-03T00:00:00Z",
        32611,
        3,
        None,
    )

    MODULE.write_cache(path, signature, [_segment()])
    restored = MODULE.read_cache(path, signature)

    assert restored is not None
    assert len(restored) == 1
    assert restored[0].segment_id == "123"
    assert restored[0].observed_at == datetime(2022, 1, 1, tzinfo=UTC)


def test_cache_rejects_changed_query_signature(tmp_path: Path):
    path = tmp_path / "tile.json"
    signature = MODULE._signature(
        "region",
        "r000_c000",
        "2018-10-13T00:00:00Z",
        "2026-08-03T00:00:00Z",
        32611,
        3,
        None,
    )
    MODULE.write_cache(path, signature, [_segment()])
    changed = dict(signature, query_end="2027-01-01T00:00:00Z")

    assert MODULE.read_cache(path, changed) is None


def test_scan_campaign_ranks_survivors_and_reports_failed_tiles(
    tmp_path: Path,
    monkeypatch,
):
    campaign = MODULE.CampaignSpec(
        campaign_id="campaign_a",
        description="test",
        regions=(
            MODULE.RegionSpec("region_a", "", -116.0, 35.0, -115.0, 36.0),
        ),
    )

    def fake_scan_region(**kwargs):
        return {
            "status": "spatially_supported_step_candidates_found",
            "tile_count": 4,
            "cached_tile_count": 2,
            "completed_tile_count": 3,
            "failed_tile_count": 1,
            "quality_segment_count_after_deduplication": 100,
            "exact_segment_series_count": 40,
            "classification_counts": {"step_up_candidate": 3},
            "raw_step_up_segment_count": 3,
            "surviving_step_cluster_count": 1,
            "surviving_step_clusters": [
                {
                    "centroid_longitude": -115.2,
                    "centroid_latitude": 35.8,
                    "event_start": "2021-01-01T00:00:00+00:00",
                    "event_end": "2022-01-01T00:00:00+00:00",
                    "median_step_m": 0.8,
                    "step_nmad_m": 0.05,
                    "segment_count": 4,
                    "cross_spot_supported": True,
                    "rgt": 45,
                    "spot": 5,
                    "pre_cycle": 11,
                    "post_cycle": 16,
                }
            ],
        }

    monkeypatch.setattr(MODULE, "scan_region", fake_scan_region)
    result = MODULE.scan_campaign(
        campaign=campaign,
        output_root=tmp_path,
        selected_region_ids=[],
        start="2018-10-13T00:00:00Z",
        end="2026-08-03T00:00:00Z",
        tile_size_m=25_000.0,
        tile_overlap_m=100.0,
        force=False,
        continue_on_error=True,
    )

    assert result["status"] == "broad_track_candidates_found"
    assert result["failed_tile_count"] == 1
    assert result["surviving_candidate_count"] == 1
    assert result["record_lookup_priority"][0]["campaign_rank"] == 1
    assert (tmp_path / "campaign_a" / "campaign_summary.json").is_file()
