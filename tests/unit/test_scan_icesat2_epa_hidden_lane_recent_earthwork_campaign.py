from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "scan_icesat2_epa_hidden_lane_recent_earthwork_campaign.py"
)
SPEC = importlib.util.spec_from_file_location("campaign014", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _geometry(
    *,
    west: float = -77.451,
    south: float = 38.990,
    east: float = -77.450,
    north: float = 38.991,
) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [west, south],
                [east, south],
                [east, north],
                [west, north],
                [west, south],
            ]
        ],
    }


def _feature(
    *,
    epa_id: str = "VAD980829030",
    name: str = "Hidden Lane Landfill",
    geometry: dict | None = None,
) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "OBJECTID": 1,
            "EPA_ID": epa_id,
            "Site_Name": name,
            "City": "STERLING",
            "State": "VA",
        },
        "geometry": geometry or _geometry(),
    }


def _collection(*features: dict) -> dict:
    return {"type": "FeatureCollection", "features": list(features)}


def _cluster(*, start: str, end: str, step: float = 0.8) -> dict:
    return {
        "event_start": start,
        "event_end": end,
        "centroid_longitude": -77.45,
        "centroid_latitude": 38.99,
        "median_step_m": step,
        "segment_count": 3,
        "segments": [
            {"longitude": -77.4505, "latitude": 38.9905},
            {"longitude": -77.4504, "latitude": 38.9905},
            {"longitude": -77.4503, "latitude": 38.9905},
        ],
    }


def test_epa_identity_and_name_normalization():
    feature = _feature(epa_id=" vad980829030 ", name=" hidden   lane landfill ")

    assert MODULE._epa_id(feature) == "VAD980829030"
    assert MODULE._site_name(feature) == "HIDDEN LANE LANDFILL"


def test_geometry_screen_rejects_too_small_component():
    small = _geometry(
        west=-77.45005,
        south=38.99000,
        east=-77.45000,
        north=38.99005,
    )
    large = _geometry()

    assert MODULE._filtered_geometry(small) is None
    assert MODULE._filtered_geometry(large) is not None


def test_fetch_requires_exact_hidden_lane_epa_id_and_wgs84():
    calls: list[dict[str, str]] = []

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        assert url == MODULE.EPA_SUPERFUND_LAYER_URL
        assert timeout == 12
        calls.append(dict(params))
        return _collection(_feature())

    result = MODULE.fetch_hidden_lane_polygon(
        west=-77.7,
        south=38.8,
        east=-77.1,
        north=39.2,
        timeout_seconds=12,
        fetch_json=fake_fetch,
    )

    assert len(result["features"]) == 1
    assert result["features"][0]["properties"]["CAMPAIGN_EPA_ID"] == MODULE.TARGET_EPA_ID
    assert result["campaign_source_diagnostics"]["retained_feature_count"] == 1
    assert calls[0]["where"] == "EPA_ID = 'VAD980829030'"
    assert calls[0]["outSR"] == "4326"
    assert calls[0]["f"] == "geojson"


def test_fetch_rejects_wrong_id_or_small_geometry():
    wrong = _feature(epa_id="PAD000000000")
    small = _feature(
        geometry=_geometry(
            west=-77.45005,
            south=38.99000,
            east=-77.45000,
            north=38.99005,
        )
    )

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        return _collection(wrong, small)

    with pytest.raises(ValueError, match="no usable official EPA Hidden Lane"):
        MODULE.fetch_hidden_lane_polygon(
            west=-77.7,
            south=38.8,
            east=-77.1,
            north=39.2,
            timeout_seconds=5,
            fetch_json=fake_fetch,
        )


def test_event_overlap_accepts_transition_crossing_window_start():
    cluster = _cluster(
        start="2023-08-01T00:00:00+00:00",
        end="2023-10-01T00:00:00+00:00",
    )

    assert MODULE.cluster_overlaps_earthwork_window(cluster) is True


def test_event_overlap_rejects_transition_entirely_before_or_after_window():
    before = _cluster(
        start="2022-01-01T00:00:00+00:00",
        end="2023-01-01T00:00:00+00:00",
    )
    after = _cluster(
        start="2026-01-01T00:00:00+00:00",
        end="2026-02-01T00:00:00+00:00",
    )

    assert MODULE.cluster_overlaps_earthwork_window(before) is False
    assert MODULE.cluster_overlaps_earthwork_window(after) is False


def test_event_filter_attaches_epa_metadata_and_records_rejection():
    accepted = _cluster(
        start="2024-08-01T00:00:00+00:00",
        end="2024-12-01T00:00:00+00:00",
    )
    rejected = _cluster(
        start="2022-08-01T00:00:00+00:00",
        end="2022-12-01T00:00:00+00:00",
    )

    survivors, rejections = MODULE.filter_clusters_to_earthwork_window(
        [accepted, rejected]
    )

    assert len(survivors) == 1
    metadata = survivors[0]["official_epa_hidden_lane_event"]
    assert metadata["epa_id"] == "VAD980829030"
    assert metadata["remedial_action_start"] == "2023-09-11"
    assert metadata["remedial_action_end"] == "2025-11-06"
    assert len(rejections) == 1
    assert rejections[0]["reason"] == "transition_outside_epa_ou3_earthwork_window"


def test_install_campaign_changes_only_campaign_runtime_hooks():
    original_id = MODULE.campaign.CAMPAIGN_ID
    original_fetch = MODULE.campaign.fetch_active_mines
    original_region_result = MODULE.campaign._region_result
    original_summary = MODULE.campaign._summary
    try:
        MODULE.install_campaign()
        assert MODULE.campaign.CAMPAIGN_ID == MODULE.CAMPAIGN_ID
        assert MODULE.campaign.REGION_ID == MODULE.REGION_ID
        assert MODULE.campaign.DEFAULT_BOUNDS == MODULE.DEFAULT_BOUNDS
        assert MODULE.campaign.fetch_active_mines is MODULE.fetch_hidden_lane_polygon
        assert MODULE.campaign._region_result is MODULE._region_result
        assert MODULE.campaign._summary is MODULE._summary
    finally:
        MODULE.campaign.CAMPAIGN_ID = original_id
        MODULE.campaign.fetch_active_mines = original_fetch
        MODULE.campaign._region_result = original_region_result
        MODULE.campaign._summary = original_summary
