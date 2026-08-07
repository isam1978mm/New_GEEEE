from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "scan_icesat2_pa_aml_reclamation_complete_campaign.py"
)
SPEC = importlib.util.spec_from_file_location("campaign011", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _feature(
    *,
    object_id: int,
    sf_id: int | None,
    name: str,
    status: str = "Reclamation Complete",
    west: float = -79.001,
    south: float = 40.000,
    east: float = -79.000,
    north: float = 40.001,
) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "OBJECTID": object_id,
            "SF_ID": sf_id,
            "SF_NAME": name,
            "SF_TYPE_CD": "AML",
            "SF_TYPE": "AML Polygon Feature",
            "SF_STATUS_CD": "RC",
            "SF_STATUS": status,
            "SF_PRIORITY_CD": "2",
            "SF_PRIORITY": "Priority 2",
            "SF_PROBLEM_CODE": "P",
            "SF_PROBLEM_CODE_DESCRIPTION": "Spoil Area",
            "HEIGHT_FT": 12,
            "VOLUME_CY": 1000,
        },
        "geometry": {
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
        },
    }


def _collection(*features: dict, exceeded: bool = False) -> dict:
    return {
        "type": "FeatureCollection",
        "features": list(features),
        "exceededTransferLimit": exceeded,
    }


def _cluster(*coordinates: tuple[float, float]) -> dict:
    return {
        "centroid_longitude": sum(item[0] for item in coordinates)
        / len(coordinates),
        "centroid_latitude": sum(item[1] for item in coordinates)
        / len(coordinates),
        "median_step_m": 0.8,
        "segment_count": len(coordinates),
        "segments": [
            {"longitude": longitude, "latitude": latitude}
            for longitude, latitude in coordinates
        ],
    }


def test_status_normalizes_text_and_identity_prefers_sf_id():
    feature = _feature(object_id=10, sf_id=22, name="Example", status=" reclamation   complete ")

    assert MODULE._status(feature) == "RECLAMATION COMPLETE"
    assert MODULE._identity(feature) == "SF_ID:22"

    feature["properties"]["SF_ID"] = None
    assert MODULE._identity(feature) == "OBJECTID:10"


def test_geometry_screen_rejects_small_polygon_and_keeps_large_component():
    small = _feature(
        object_id=1,
        sf_id=1,
        name="Small",
        west=-79.0001,
        south=40.0000,
        east=-79.0000,
        north=40.0001,
    )["geometry"]
    assert MODULE._filtered_geometry(small) is None

    large = _feature(object_id=2, sf_id=2, name="Large")["geometry"]
    multipolygon = {
        "type": "MultiPolygon",
        "coordinates": [small["coordinates"], large["coordinates"]],
    }
    result = MODULE._filtered_geometry(multipolygon)

    assert result is not None
    assert result["type"] == "Polygon"
    assert result["coordinates"] == large["coordinates"]


def test_fetch_paginates_filters_status_and_preserves_only_eligible_geometry(monkeypatch):
    monkeypatch.setattr(MODULE, "PAGE_SIZE", 2)
    calls: list[dict[str, str]] = []

    eligible_a = _feature(object_id=1, sf_id=101, name="A")
    wrong_status = _feature(
        object_id=2, sf_id=102, name="B", status="Abandoned"
    )
    eligible_c = _feature(object_id=3, sf_id=103, name="C")

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        assert url == MODULE.PA_DEP_AML_LAYER_URL
        assert timeout == 12
        calls.append(dict(params))
        offset = int(params["resultOffset"])
        if offset == 0:
            return _collection(eligible_a, wrong_status, exceeded=True)
        if offset == 2:
            return _collection(eligible_c)
        return _collection()

    result = MODULE.fetch_reclamation_complete_aml(
        west=-80.0,
        south=39.8,
        east=-78.0,
        north=41.0,
        timeout_seconds=12,
        fetch_json=fake_fetch,
    )

    assert [item["properties"]["SF_NAME"] for item in result["features"]] == [
        "A",
        "C",
    ]
    assert [item["resultOffset"] for item in calls] == ["0", "2"]
    assert calls[0]["where"] == "SF_STATUS = 'Reclamation Complete'"
    assert calls[0]["outSR"] == "4326"
    assert calls[0]["f"] == "geojson"


def test_fetch_deduplicates_repeated_official_identity(monkeypatch):
    monkeypatch.setattr(MODULE, "PAGE_SIZE", 2)
    first = _feature(object_id=1, sf_id=500, name="First")
    duplicate = _feature(object_id=2, sf_id=500, name="Duplicate")

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        if int(params["resultOffset"]) == 0:
            return _collection(first, duplicate)
        return _collection()

    result = MODULE.fetch_reclamation_complete_aml(
        west=-80.0,
        south=39.8,
        east=-78.0,
        north=41.0,
        timeout_seconds=5,
        fetch_json=fake_fetch,
    )

    assert len(result["features"]) == 1
    assert result["features"][0]["properties"]["SF_NAME"] == "First"


def test_shared_polygon_requires_every_segment_in_one_official_polygon():
    polygons = _collection(
        _feature(
            object_id=1,
            sf_id=701,
            name="One",
            west=-79.10,
            south=40.00,
            east=-79.00,
            north=40.10,
        )
    )
    cluster = _cluster(
        (-79.08, 40.02),
        (-79.06, 40.04),
        (-79.04, 40.06),
    )

    result = MODULE.shared_reclamation_complete_polygon(cluster, polygons)

    assert result is not None
    assert result["identity"] == "SF_ID:701"
    assert result["name"] == "One"
    assert result["status"] == "RECLAMATION COMPLETE"


def test_shared_polygon_rejects_cluster_split_between_two_polygons():
    polygons = _collection(
        _feature(
            object_id=1,
            sf_id=801,
            name="West",
            west=-79.10,
            south=40.00,
            east=-79.05,
            north=40.10,
        ),
        _feature(
            object_id=2,
            sf_id=802,
            name="East",
            west=-79.05,
            south=40.00,
            east=-79.00,
            north=40.10,
        ),
    )
    cluster = _cluster((-79.08, 40.04), (-79.02, 40.04))

    assert MODULE.shared_reclamation_complete_polygon(cluster, polygons) is None


def test_cluster_filter_attaches_metadata_and_records_rejection():
    polygons = _collection(
        _feature(
            object_id=1,
            sf_id=901,
            name="Accepted",
            west=-79.10,
            south=40.00,
            east=-79.00,
            north=40.10,
        )
    )
    accepted = _cluster((-79.08, 40.02), (-79.06, 40.04), (-79.04, 40.06))
    rejected = _cluster((-78.80, 40.02), (-78.78, 40.04), (-78.76, 40.06))

    survivors, rejections = MODULE.filter_clusters_to_single_polygon(
        [accepted, rejected], polygons
    )

    assert len(survivors) == 1
    assert survivors[0]["official_pa_dep_aml_polygon"]["identity"] == "SF_ID:901"
    assert len(rejections) == 1
    assert rejections[0]["reason"] == (
        "supporting_segments_do_not_share_exactly_one_pa_dep_"
        "reclamation_complete_aml_polygon"
    )


def test_install_campaign_changes_only_campaign_runtime_hooks():
    MODULE.install_campaign()

    assert MODULE.campaign.CAMPAIGN_ID == MODULE.CAMPAIGN_ID
    assert MODULE.campaign.REGION_ID == MODULE.REGION_ID
    assert MODULE.campaign.DEFAULT_BOUNDS == MODULE.DEFAULT_BOUNDS
    assert MODULE.campaign.fetch_active_mines is MODULE.fetch_reclamation_complete_aml
    assert MODULE.campaign._region_result is MODULE._region_result
    assert MODULE.campaign._summary is MODULE._summary
