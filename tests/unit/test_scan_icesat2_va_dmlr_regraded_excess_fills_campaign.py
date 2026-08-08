from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "scan_icesat2_va_dmlr_regraded_excess_fills_campaign.py"
)
SPEC = importlib.util.spec_from_file_location("campaign013", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _geometry(
    *,
    west: float = -82.001,
    south: float = 37.000,
    east: float = -82.000,
    north: float = 37.001,
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


def _regraded(
    *,
    object_id: int,
    permit: str,
    global_id: str,
    status: str = "reg",
    west: float = -82.001,
    south: float = 37.000,
    east: float = -82.000,
    north: float = 37.001,
) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "OBJECTID": object_id,
            "Permit": permit,
            "Rec_Stat": status,
            "GlobalID": global_id,
        },
        "geometry": _geometry(west=west, south=south, east=east, north=north),
    }


def _fill(
    *,
    object_id: int,
    permit: str,
    global_id: str,
    component: str,
    west: float = -82.001,
    south: float = 37.000,
    east: float = -82.000,
    north: float = 37.001,
) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "OBJECTID": object_id,
            "Permit": permit,
            "Comp_ID": component,
            "Descrip": "Excess fill",
            "CFCertNo": "CF-1",
            "GlobalID": global_id,
        },
        "geometry": _geometry(west=west, south=south, east=east, north=north),
    }


def _collection(*features: dict, exceeded: bool = False) -> dict:
    return {
        "type": "FeatureCollection",
        "features": list(features),
        "exceededTransferLimit": exceeded,
    }


def _cluster(*coordinates: tuple[float, float]) -> dict:
    return {
        "centroid_longitude": sum(item[0] for item in coordinates) / len(coordinates),
        "centroid_latitude": sum(item[1] for item in coordinates) / len(coordinates),
        "median_step_m": 0.8,
        "segment_count": len(coordinates),
        "segments": [
            {"longitude": longitude, "latitude": latitude}
            for longitude, latitude in coordinates
        ],
    }


def _campaign_collection(fill: dict, regraded: dict) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [fill],
        "campaign_regraded_status_features": [regraded],
    }


def test_status_permit_and_identities_are_normalized():
    regraded = _regraded(
        object_id=1,
        permit=" 1101234 ",
        global_id="{REG-1}",
        status=" reg ",
    )
    fill = _fill(
        object_id=2,
        permit="1101234",
        global_id="{FILL-1}",
        component="VF-1",
    )

    assert MODULE._permit(regraded) == "1101234"
    assert MODULE._reclamation_status(regraded) == "REG"
    assert MODULE._regraded_identity(regraded) == "GLOBALID:{REG-1}"
    assert MODULE._fill_identity(fill) == "GLOBALID:{FILL-1}"


def test_geometry_screen_rejects_too_small_component():
    small = _geometry(
        west=-82.0001,
        south=37.0000,
        east=-82.0000,
        north=37.0001,
    )
    large = _geometry()

    assert MODULE._filtered_geometry(small) is None
    assert MODULE._filtered_geometry(large) is not None


def test_fetch_joins_fills_to_regraded_permits_and_reports_source_counts(monkeypatch):
    monkeypatch.setattr(MODULE, "PAGE_SIZE", 2)
    regraded = _regraded(
        object_id=1,
        permit="1100001",
        global_id="{REG-A}",
    )
    eligible_fill = _fill(
        object_id=10,
        permit="1100001",
        global_id="{FILL-A}",
        component="F1",
    )
    wrong_permit_fill = _fill(
        object_id=11,
        permit="1100002",
        global_id="{FILL-B}",
        component="F2",
    )
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        assert timeout == 9
        calls.append((url, dict(params)))
        offset = int(params["resultOffset"])
        if url == MODULE.VA_DMLR_RECLAMATION_STATUS_URL:
            assert params["where"] == "Rec_Stat = 'reg'"
            return _collection(regraded) if offset == 0 else _collection()
        if url == MODULE.VA_DMLR_EXCESS_FILLS_URL:
            assert params["where"] == "1=1"
            if offset == 0:
                return _collection(eligible_fill, wrong_permit_fill)
            return _collection()
        raise AssertionError(url)

    result = MODULE.fetch_regraded_excess_fills(
        west=-83.0,
        south=36.5,
        east=-81.0,
        north=37.5,
        timeout_seconds=9,
        fetch_json=fake_fetch,
    )

    assert len(result["features"]) == 1
    assert result["features"][0]["properties"]["Permit"] == "1100001"
    assert len(result["campaign_regraded_status_features"]) == 1
    diagnostics = result["campaign_source_diagnostics"]
    assert diagnostics["raw_regraded_feature_count"] == 1
    assert diagnostics["raw_fill_feature_count"] == 2
    assert diagnostics["fill_rejected_without_regraded_permit"] == 1
    assert diagnostics["retained_fill_feature_count"] == 1
    assert all(params["outSR"] == "4326" for _, params in calls)


def test_fetch_rejects_when_no_fill_survives_approved_target(monkeypatch):
    regraded = _regraded(
        object_id=1,
        permit="1100001",
        global_id="{REG-A}",
    )
    unrelated_fill = _fill(
        object_id=2,
        permit="1109999",
        global_id="{FILL-X}",
        component="X",
    )

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        if url == MODULE.VA_DMLR_RECLAMATION_STATUS_URL:
            return _collection(regraded)
        return _collection(unrelated_fill)

    with pytest.raises(ValueError, match="no eligible Virginia DMLR excess-material fills"):
        MODULE.fetch_regraded_excess_fills(
            west=-83.0,
            south=36.5,
            east=-81.0,
            north=37.5,
            timeout_seconds=5,
            fetch_json=fake_fetch,
        )


def test_shared_gate_accepts_one_fill_and_one_same_permit_regraded_polygon():
    fill = _fill(
        object_id=1,
        permit="1100001",
        global_id="{FILL-A}",
        component="F1",
        west=-82.10,
        south=37.00,
        east=-82.00,
        north=37.10,
    )
    regraded = _regraded(
        object_id=2,
        permit="1100001",
        global_id="{REG-A}",
        west=-82.09,
        south=37.01,
        east=-82.01,
        north=37.09,
    )
    cluster = _cluster(
        (-82.08, 37.02),
        (-82.06, 37.04),
        (-82.04, 37.06),
    )

    result = MODULE.shared_fill_and_regraded_polygon(
        cluster, _campaign_collection(fill, regraded)
    )

    assert result is not None
    assert result["permit"] == "1100001"
    assert result["fill"]["component_id"] == "F1"
    assert result["regraded_polygon"]["status"] == "Regraded"


def test_shared_gate_rejects_segment_outside_regraded_polygon():
    fill = _fill(
        object_id=1,
        permit="1100001",
        global_id="{FILL-A}",
        component="F1",
        west=-82.10,
        south=37.00,
        east=-82.00,
        north=37.10,
    )
    regraded = _regraded(
        object_id=2,
        permit="1100001",
        global_id="{REG-A}",
        west=-82.09,
        south=37.01,
        east=-82.05,
        north=37.09,
    )
    cluster = _cluster((-82.08, 37.02), (-82.02, 37.04))

    assert (
        MODULE.shared_fill_and_regraded_polygon(
            cluster, _campaign_collection(fill, regraded)
        )
        is None
    )


def test_shared_gate_rejects_overlapping_polygons_from_different_permits():
    fill = _fill(
        object_id=1,
        permit="1100001",
        global_id="{FILL-A}",
        component="F1",
        west=-82.10,
        south=37.00,
        east=-82.00,
        north=37.10,
    )
    regraded = _regraded(
        object_id=2,
        permit="1100002",
        global_id="{REG-B}",
        west=-82.10,
        south=37.00,
        east=-82.00,
        north=37.10,
    )
    cluster = _cluster((-82.08, 37.02), (-82.06, 37.04), (-82.04, 37.06))

    assert (
        MODULE.shared_fill_and_regraded_polygon(
            cluster, _campaign_collection(fill, regraded)
        )
        is None
    )


def test_cluster_filter_attaches_metadata_and_records_rejection():
    fill = _fill(
        object_id=1,
        permit="1100001",
        global_id="{FILL-A}",
        component="F1",
        west=-82.10,
        south=37.00,
        east=-82.00,
        north=37.10,
    )
    regraded = _regraded(
        object_id=2,
        permit="1100001",
        global_id="{REG-A}",
        west=-82.10,
        south=37.00,
        east=-82.00,
        north=37.10,
    )
    accepted = _cluster((-82.08, 37.02), (-82.06, 37.04), (-82.04, 37.06))
    rejected = _cluster((-81.80, 37.02), (-81.78, 37.04), (-81.76, 37.06))

    survivors, rejections = MODULE.filter_clusters_to_fill_and_regraded_polygon(
        [accepted, rejected], _campaign_collection(fill, regraded)
    )

    assert len(survivors) == 1
    assert survivors[0]["official_va_dmlr_regraded_fill"]["permit"] == "1100001"
    assert len(rejections) == 1
    assert "same_permit_regraded_polygon" in rejections[0]["reason"]


def test_install_campaign_changes_only_campaign_runtime_hooks():
    original = {
        "CAMPAIGN_ID": MODULE.campaign.CAMPAIGN_ID,
        "REGION_ID": MODULE.campaign.REGION_ID,
        "DEFAULT_BOUNDS": MODULE.campaign.DEFAULT_BOUNDS,
        "fetch_active_mines": MODULE.campaign.fetch_active_mines,
        "region_result": MODULE.campaign._region_result,
        "summary": MODULE.campaign._summary,
    }
    try:
        MODULE.install_campaign()
        assert MODULE.campaign.CAMPAIGN_ID == MODULE.CAMPAIGN_ID
        assert MODULE.campaign.REGION_ID == MODULE.REGION_ID
        assert MODULE.campaign.DEFAULT_BOUNDS == MODULE.DEFAULT_BOUNDS
        assert MODULE.campaign.fetch_active_mines is MODULE.fetch_regraded_excess_fills
        assert MODULE.campaign._region_result is MODULE._region_result
        assert MODULE.campaign._summary is MODULE._summary
    finally:
        MODULE.campaign.CAMPAIGN_ID = original["CAMPAIGN_ID"]
        MODULE.campaign.REGION_ID = original["REGION_ID"]
        MODULE.campaign.DEFAULT_BOUNDS = original["DEFAULT_BOUNDS"]
        MODULE.campaign.fetch_active_mines = original["fetch_active_mines"]
        MODULE.campaign._region_result = original["region_result"]
        MODULE.campaign._summary = original["summary"]
