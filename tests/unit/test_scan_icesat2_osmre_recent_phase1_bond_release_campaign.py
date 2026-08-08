from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "scan_icesat2_osmre_recent_phase1_bond_release_campaign.py"
)
SPEC = importlib.util.spec_from_file_location("campaign012", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _feature(
    *,
    object_id: int,
    permit_id: str,
    contact: int = 2,
    status: int = 1,
    bond_date: object = "2021-06-15T00:00:00Z",
    west: float = -81.001,
    south: float = 38.000,
    east: float = -81.000,
    north: float = 38.001,
) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "objectid": object_id,
            "permittee": "Example Permittee",
            "company": "Example Company",
            "permit_id": permit_id,
            "national_id": f"N-{object_id}",
            "incremental_area_id": f"INC-{object_id}",
            "reclamation_bond_status": status,
            "reclamation_bond_status_date": bond_date,
            "bond_amount": 100000.0,
            "calculated_area": 20.0,
            "reported_area": 19.5,
            "contact": contact,
            "information_link": "https://example.invalid/permit",
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


def test_date_parser_accepts_arcgis_milliseconds_and_iso_text():
    assert MODULE._date_from_value(1577836800000) == date(2020, 1, 1)
    assert MODULE._date_from_value("2024-12-31T15:00:00Z") == date(2024, 12, 31)
    assert MODULE._date_from_value(None) is None


def test_status_contact_and_identity_use_osmre_fields():
    feature = _feature(object_id=10, permit_id="P-10", contact=3)

    assert MODULE._status_code(feature) == 1
    assert MODULE._contact_code(feature) == 3
    assert MODULE._identity(feature) == "OBJECTID:10"


def test_geometry_screen_rejects_small_polygon_and_keeps_large_component():
    small = _feature(
        object_id=1,
        permit_id="SMALL",
        west=-81.0001,
        south=38.0000,
        east=-81.0000,
        north=38.0001,
    )["geometry"]
    assert MODULE._filtered_geometry(small) is None

    large = _feature(object_id=2, permit_id="LARGE")["geometry"]
    multipolygon = {
        "type": "MultiPolygon",
        "coordinates": [small["coordinates"], large["coordinates"]],
    }
    result = MODULE._filtered_geometry(multipolygon)

    assert result is not None
    assert result["type"] == "Polygon"
    assert result["coordinates"] == large["coordinates"]


def test_fetch_paginates_and_preserves_only_recent_phase1_target_features(monkeypatch):
    monkeypatch.setattr(MODULE, "PAGE_SIZE", 2)
    calls: list[dict[str, str]] = []

    eligible_a = _feature(object_id=1, permit_id="A", contact=1)
    wrong_contact = _feature(object_id=2, permit_id="B", contact=8)
    eligible_c = _feature(object_id=3, permit_id="C", contact=2, bond_date=1704067200000)

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        assert url == MODULE.OSMRE_BOND_LAYER_URL
        assert timeout == 12
        calls.append(dict(params))
        offset = int(params["resultOffset"])
        if offset == 0:
            return _collection(eligible_a, wrong_contact, exceeded=True)
        if offset == 2:
            return _collection(eligible_c)
        return _collection()

    result = MODULE.fetch_recent_phase1_bond_release(
        west=-85.0,
        south=36.5,
        east=-77.0,
        north=40.6,
        timeout_seconds=12,
        fetch_json=fake_fetch,
    )

    assert [item["properties"]["permit_id"] for item in result["features"]] == [
        "A",
        "C",
    ]
    assert [item["resultOffset"] for item in calls] == ["0", "2"]
    assert "reclamation_bond_status = 1" in calls[0]["where"]
    assert "contact IN (1,2,3)" in calls[0]["where"]
    assert "2019-01-01" in calls[0]["where"]
    assert "2025-01-01" in calls[0]["where"]
    assert calls[0]["outSR"] == "4326"
    assert calls[0]["f"] == "geojson"


def test_fetch_rejects_wrong_status_and_dates_outside_window(monkeypatch):
    monkeypatch.setattr(MODULE, "PAGE_SIZE", 10)
    eligible = _feature(object_id=1, permit_id="OK")
    wrong_status = _feature(object_id=2, permit_id="STATUS", status=2)
    too_old = _feature(object_id=3, permit_id="OLD", bond_date="2018-12-31T00:00:00Z")
    too_new = _feature(object_id=4, permit_id="NEW", bond_date="2025-01-01T00:00:00Z")

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        return _collection(eligible, wrong_status, too_old, too_new)

    result = MODULE.fetch_recent_phase1_bond_release(
        west=-85.0,
        south=36.5,
        east=-77.0,
        north=40.6,
        timeout_seconds=5,
        fetch_json=fake_fetch,
    )

    assert len(result["features"]) == 1
    assert result["features"][0]["properties"]["permit_id"] == "OK"


def test_metadata_retains_release_date_and_regulatory_authority():
    feature = _feature(
        object_id=22,
        permit_id="WV-22",
        contact=2,
        bond_date="2022-07-04T00:00:00Z",
    )

    metadata = MODULE._metadata(feature)

    assert metadata["identity"] == "OBJECTID:22"
    assert metadata["reclamation_bond_status"] == "Phase I Release"
    assert metadata["reclamation_bond_status_date"] == "2022-07-04"
    assert metadata["contact_name"] == "West Virginia"
    assert metadata["permit_id"] == "WV-22"


def test_shared_polygon_requires_every_segment_inside_one_official_polygon():
    polygons = _collection(
        _feature(
            object_id=31,
            permit_id="ONE",
            west=-81.10,
            south=38.00,
            east=-81.00,
            north=38.10,
        )
    )
    cluster = _cluster(
        (-81.08, 38.02),
        (-81.06, 38.04),
        (-81.04, 38.06),
    )

    result = MODULE.shared_phase1_polygon(cluster, polygons)

    assert result is not None
    assert result["identity"] == "OBJECTID:31"
    assert result["reclamation_bond_status"] == "Phase I Release"


def test_shared_polygon_rejects_cluster_split_between_two_polygons():
    polygons = _collection(
        _feature(
            object_id=41,
            permit_id="WEST",
            west=-81.10,
            south=38.00,
            east=-81.05,
            north=38.10,
        ),
        _feature(
            object_id=42,
            permit_id="EAST",
            west=-81.05,
            south=38.00,
            east=-81.00,
            north=38.10,
        ),
    )
    cluster = _cluster((-81.08, 38.04), (-81.02, 38.04))

    assert MODULE.shared_phase1_polygon(cluster, polygons) is None


def test_cluster_filter_attaches_metadata_and_records_rejection():
    polygons = _collection(
        _feature(
            object_id=51,
            permit_id="ACCEPT",
            west=-81.10,
            south=38.00,
            east=-81.00,
            north=38.10,
        )
    )
    accepted = _cluster((-81.08, 38.02), (-81.06, 38.04), (-81.04, 38.06))
    rejected = _cluster((-80.80, 38.02), (-80.78, 38.04), (-80.76, 38.06))

    survivors, rejections = MODULE.filter_clusters_to_single_phase1_polygon(
        [accepted, rejected], polygons
    )

    assert len(survivors) == 1
    assert (
        survivors[0]["official_osmre_phase1_bond_release_polygon"]["identity"]
        == "OBJECTID:51"
    )
    assert len(rejections) == 1
    assert rejections[0]["reason"] == (
        "supporting_segments_do_not_share_exactly_one_osmre_"
        "recent_phase1_bond_release_polygon"
    )


def test_install_campaign_changes_only_campaign_runtime_hooks():
    MODULE.install_campaign()

    assert MODULE.campaign.CAMPAIGN_ID == MODULE.CAMPAIGN_ID
    assert MODULE.campaign.REGION_ID == MODULE.REGION_ID
    assert MODULE.campaign.DEFAULT_BOUNDS == MODULE.DEFAULT_BOUNDS
    assert MODULE.campaign.fetch_active_mines is MODULE.fetch_recent_phase1_bond_release
    assert MODULE.campaign._region_result is MODULE._region_result
    assert MODULE.campaign._summary is MODULE._summary
