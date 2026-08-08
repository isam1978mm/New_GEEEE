from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "scan_icesat2_osmre_recent_phase1_bond_release_campaign_fixed.py"
)
SPEC = importlib.util.spec_from_file_location("campaign012_fixed", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _feature(
    *,
    objectid: int,
    contact: int = 2,
    date_ms: int = 1590969600000,
    west: float = -81.001,
    south: float = 38.000,
    east: float = -81.000,
    north: float = 38.001,
) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "objectid": objectid,
            "permit_id": f"P-{objectid}",
            "national_id": f"N-{objectid}",
            "incremental_area_id": "A",
            "reclamation_bond_status": 1,
            "reclamation_bond_status_date": date_ms,
            "contact": contact,
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [west, south],
                [east, south],
                [east, north],
                [west, north],
                [west, south],
            ]],
        },
    }


def _collection(*features: dict, exceeded: bool = False) -> dict:
    return {
        "type": "FeatureCollection",
        "features": list(features),
        "exceededTransferLimit": exceeded,
    }


def test_source_compat_uses_phase_i_only_server_where_and_local_gates(monkeypatch):
    monkeypatch.setattr(MODULE.campaign012, "PAGE_SIZE", 10)
    calls: list[dict[str, str]] = []

    accepted = _feature(objectid=1, contact=2, date_ms=1590969600000)
    wrong_contact = _feature(objectid=2, contact=8, date_ms=1590969600000)
    old_date = _feature(objectid=3, contact=3, date_ms=1514764800000)
    too_small = _feature(
        objectid=4,
        contact=1,
        date_ms=1590969600000,
        west=-81.0001,
        south=38.0000,
        east=-81.0000,
        north=38.0001,
    )

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        calls.append(dict(params))
        assert timeout == 12
        assert url == MODULE.campaign012.OSMRE_BOND_LAYER_URL
        if int(params["resultOffset"]) == 0:
            return _collection(accepted, wrong_contact, old_date, too_small)
        return _collection()

    result = MODULE.fetch_recent_phase1_bond_release_compat(
        west=-85,
        south=36.45,
        east=-77,
        north=40.65,
        timeout_seconds=12,
        fetch_json=fake_fetch,
    )

    assert calls[0]["where"] == "reclamation_bond_status = 1"
    assert len(result["features"]) == 1
    assert result["features"][0]["properties"]["objectid"] == 1
    diagnostics = result["campaign_source_diagnostics"]
    assert diagnostics["raw_phase1_feature_count"] == 4
    assert diagnostics["retained_approved_feature_count"] == 1
    assert diagnostics["rejection_counts"] == {
        "below_40m_component_envelope_screen": 1,
        "outside_approved_2019_2024_date_window": 1,
        "outside_approved_contacts": 1,
    }


def test_source_compat_zero_result_reports_exact_rejection_counts(monkeypatch):
    monkeypatch.setattr(MODULE.campaign012, "PAGE_SIZE", 10)

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        if int(params["resultOffset"]) == 0:
            return _collection(_feature(objectid=1, contact=8))
        return _collection()

    with pytest.raises(ValueError, match="raw_phase1_feature_count") as exc_info:
        MODULE.fetch_recent_phase1_bond_release_compat(
            west=-85,
            south=36.45,
            east=-77,
            north=40.65,
            timeout_seconds=5,
            fetch_json=fake_fetch,
        )

    assert "outside_approved_contacts" in str(exc_info.value)


def test_install_source_compat_changes_only_source_fetch_hook():
    MODULE.install_campaign_source_compat()

    assert MODULE.campaign012.campaign.fetch_active_mines is (
        MODULE.fetch_recent_phase1_bond_release_compat
    )
    assert MODULE.campaign is MODULE.campaign012.campaign
