from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "run_icesat2_epa_hidden_lane_campaign_014_with_nsidc_fallback.py"
)
SPEC = importlib.util.spec_from_file_location("campaign014_nsidc_launcher", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _polygon() -> list[dict[str, float]]:
    return [
        {"lon": -77.50, "lat": 38.90},
        {"lon": -77.40, "lat": 38.90},
        {"lon": -77.40, "lat": 39.10},
        {"lon": -77.50, "lat": 39.10},
        {"lon": -77.50, "lat": 38.90},
    ]


def _frame(value: float) -> pd.DataFrame:
    return pd.DataFrame(
        {"h_te_median": [value]},
        index=pd.Index([1_600_000_000_000_000_000 + int(value)], name="time_ns"),
    )


def test_resource_recovery_uses_direct_copy_only_for_known_unresolved_granule(monkeypatch):
    critical = MODULE.direct.UNRESOLVED_RESOURCES[0]
    clean = "ATL08_20200101000000_00010101_007_01.h5"

    def fake_worker(request, *, timeout_seconds):
        assert timeout_seconds == 30
        if request["operation"] == "cmr":
            return [clean, critical], []
        if request["operation"] == "resource" and request["resource"] == clean:
            return _frame(10.0), []
        if request["operation"] == "resource" and request["resource"] == critical:
            return _frame(20.0), ["H5Coro::Future read failure"]
        raise AssertionError(request)

    direct_calls: list[str] = []

    def fake_direct(resource, *, polygon):
        direct_calls.append(resource)
        assert polygon == _polygon()
        return _frame(30.0)

    monkeypatch.setattr(MODULE.base, "_run_worker_request", fake_worker)
    monkeypatch.setattr(MODULE.direct, "load_cached_resource", fake_direct)

    result = MODULE._recover_by_explicit_resources_with_nsidc(
        polygon=_polygon(),
        start="2018-10-13T00:00:00Z",
        end="2026-08-03T00:00:00Z",
        timeout_seconds=30,
        attempts=2,
    )

    assert len(result) == 2
    assert direct_calls == [critical]
    assert result.attrs["campaign014_nsidc_direct_resources"] == [critical]
    assert result.attrs["campaign014_all_cmr_resources_represented"] is True


def test_unknown_failed_resource_is_not_silently_replaced(monkeypatch):
    unknown = "ATL08_20200101000000_00010101_007_01.h5"

    def fake_worker(request, *, timeout_seconds):
        if request["operation"] == "cmr":
            return [unknown], []
        if request["operation"] == "resource":
            return _frame(10.0), ["Failure on resource unknown"]
        raise AssertionError(request)

    monkeypatch.setattr(MODULE.base, "_run_worker_request", fake_worker)

    with pytest.raises(
        MODULE.Campaign014NsidcFallbackError,
        match="unresolved 1/1 resources",
    ):
        MODULE._recover_by_explicit_resources_with_nsidc(
            polygon=_polygon(),
            start="2018-10-13T00:00:00Z",
            end="2026-08-03T00:00:00Z",
            timeout_seconds=30,
            attempts=2,
        )


def test_install_recovery_hook_changes_only_campaign_query_hook():
    original_query = MODULE.base.campaign014.campaign._query_atl08
    original_region_result = MODULE.base.campaign014.campaign._region_result
    original_summary = MODULE.base.campaign014.campaign._summary
    try:
        MODULE.install_recovery_hook()
        assert (
            MODULE.base.campaign014.campaign._query_atl08
            is MODULE._query_atl08_with_nsidc_fallback
        )
        assert (
            MODULE.base.campaign014.campaign._region_result
            is MODULE.base.campaign014._region_result
        )
        assert MODULE.base.campaign014.campaign._summary is MODULE.base.campaign014._summary
    finally:
        MODULE.base.campaign014.campaign._query_atl08 = original_query
        MODULE.base.campaign014.campaign._region_result = original_region_result
        MODULE.base.campaign014.campaign._summary = original_summary
