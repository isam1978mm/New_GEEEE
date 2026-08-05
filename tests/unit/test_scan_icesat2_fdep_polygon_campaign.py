from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "scan_icesat2_fdep_polygon_campaign.py"
SPEC = importlib.util.spec_from_file_location(
    "scan_icesat2_fdep_polygon_campaign", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _feature_collection():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"MINE_NAME": "Test Mine"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-82.0, 27.0],
                            [-81.0, 27.0],
                            [-81.0, 28.0],
                            [-82.0, 28.0],
                            [-82.0, 27.0],
                        ],
                        [
                            [-81.8, 27.2],
                            [-81.2, 27.2],
                            [-81.2, 27.8],
                            [-81.8, 27.8],
                            [-81.8, 27.2],
                        ],
                    ],
                },
            }
        ],
    }


def test_point_in_polygon_respects_exterior_boundary_and_hole():
    polygons = MODULE._feature_polygons(_feature_collection())

    assert MODULE._point_in_polygons(-81.9, 27.5, polygons) is True
    assert MODULE._point_in_polygons(-82.0, 27.5, polygons) is True
    assert MODULE._point_in_polygons(-81.5, 27.5, polygons) is False
    assert MODULE._point_in_polygons(-80.5, 27.5, polygons) is False


def test_fetch_active_mines_uses_envelope_and_keeps_polygon_features():
    calls = []

    def fake_fetch(url, params, timeout):
        calls.append((url, params, timeout))
        return {
            "type": "FeatureCollection",
            "features": [
                _feature_collection()["features"][0],
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {"type": "Point", "coordinates": [-81.5, 27.5]},
                },
            ],
        }

    result = MODULE.fetch_active_mines(
        west=-82.2,
        south=27.2,
        east=-81.55,
        north=28.2,
        timeout_seconds=12.0,
        fetch_json=fake_fetch,
    )

    assert len(result["features"]) == 1
    assert calls[0][0] == MODULE.FDEP_LAYER_URL
    assert calls[0][1]["geometryType"] == "esriGeometryEnvelope"
    assert calls[0][1]["outSR"] == "4326"
    assert json.loads(calls[0][1]["geometry"])["xmin"] == -82.2


def test_select_polygon_tiles_rejects_nonintersecting_tile_bounds():
    polygons = MODULE._feature_polygons(_feature_collection())
    inside = SimpleNamespace(
        tile_id="inside",
        polygon_wgs84=[
            (-82.1, 26.9),
            (-81.9, 26.9),
            (-81.9, 27.1),
            (-82.1, 27.1),
            (-82.1, 26.9),
        ],
    )
    outside = SimpleNamespace(
        tile_id="outside",
        polygon_wgs84=[
            (-80.5, 26.0),
            (-80.0, 26.0),
            (-80.0, 26.5),
            (-80.5, 26.5),
            (-80.5, 26.0),
        ],
    )

    selected = MODULE.select_polygon_tiles([inside, outside], polygons)

    assert [tile.tile_id for tile in selected] == ["inside"]


def test_summary_keeps_records_and_depth_closed(tmp_path):
    campaign_dir = tmp_path / MODULE.CAMPAIGN_ID
    campaign_dir.mkdir()
    region_result = {
        "status": "no_persistent_upward_steps_inside_official_mines",
        "bounding_box_tile_count": 10,
        "tile_count": 3,
        "cached_tile_count": 0,
        "completed_tile_count": 3,
        "failed_tile_count": 0,
        "quality_segment_count_before_polygon_filter": 100,
        "quality_segment_count_after_deduplication": 30,
        "segments_rejected_outside_official_mines": 70,
        "exact_segment_series_count": 8,
        "classification_counts": {"stable": 8},
        "raw_step_up_segment_count": 0,
        "surviving_step_cluster_count": 0,
        "surviving_step_clusters": [],
    }

    result = MODULE._summary(
        campaign_dir=campaign_dir,
        region_result=region_result,
    )

    assert result["record_lookup_priority"] == []
    assert result["records_research_ready"] is False
    assert result["numerical_depth_unlocked"] is False
    assert result["interpretation"][
        "every_retained_segment_inside_official_active_mine_polygon"
    ] is True


def test_cache_signature_identifies_polygon_filter():
    signature = MODULE._cache_signature(
        tile_id="r000_c000",
        start="2018-01-01",
        end="2026-01-01",
        epsg=32617,
        minimum_ground_photons=3,
        maximum_uncertainty_m=None,
    )

    assert signature["campaign_id"] == MODULE.CAMPAIGN_ID
    assert signature["fdep_layer_url"] == MODULE.FDEP_LAYER_URL
    assert signature["segment_filter"] == "inside_official_active_mine_polygon"
