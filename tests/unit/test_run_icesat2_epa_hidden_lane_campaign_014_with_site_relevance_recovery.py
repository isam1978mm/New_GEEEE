from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "run_icesat2_epa_hidden_lane_campaign_014_with_site_relevance_recovery.py"
)
SPEC = importlib.util.spec_from_file_location("campaign014_site_relevance", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _polygon() -> list[dict[str, float]]:
    return [
        {"lon": -77.50, "lat": 39.00},
        {"lon": -77.20, "lat": 39.00},
        {"lon": -77.20, "lat": 39.20},
        {"lon": -77.50, "lat": 39.20},
        {"lon": -77.50, "lat": 39.00},
    ]


def test_resource_date_rgt_parses_campaign_resources():
    assert MODULE._resource_date_rgt(
        "ATL08_20210504235905_06291102_007_01.h5"
    ) == ("2021-05-04", 629)
    assert MODULE._resource_date_rgt(
        "ATL08_20251226145703_01873002_007_01.h5"
    ) == ("2025-12-26", 187)


def test_off_site_proof_requires_tile_presence_and_epa_absence():
    resource = "ATL08_20251226145703_01873002_007_01.h5"

    def fake_lookup(*, date, bounds, timeout_seconds):
        assert date == "2025-12-26"
        assert timeout_seconds == 60
        if bounds == MODULE.EPA_ENVELOPE:
            return []
        return [187]

    proven, proof = MODULE._failed_resource_is_proven_off_site(
        resource,
        tile_polygon=_polygon(),
        timeout_seconds=60,
        track_lookup=fake_lookup,
    )

    assert proven is True
    assert proof["tile_track_present"] is True
    assert proof["epa_envelope_track_present"] is False


def test_epa_envelope_presence_keeps_failed_resource_blocking(monkeypatch):
    resource = "ATL08_20210504235905_06291102_007_01.h5"

    def fake_worker(request, *, timeout_seconds):
        if request["operation"] == "cmr":
            return [resource], []
        return pd.DataFrame({"value": [1]}), ["Failure on resource test"]

    monkeypatch.setattr(MODULE.watchdog, "_run_worker_request", fake_worker)
    monkeypatch.setattr(
        MODULE,
        "_failed_resource_is_proven_off_site",
        lambda *args, **kwargs: (
            False,
            {
                "resource": resource,
                "tile_track_present": True,
                "epa_envelope_track_present": True,
            },
        ),
    )

    with pytest.raises(
        MODULE.watchdog.Campaign014ResourceRecoveryError,
        match="unresolved relevant/ambiguous resources",
    ):
        MODULE._recover_by_explicit_resources_with_site_relevance(
            polygon=_polygon(),
            start="2018-10-13T00:00:00Z",
            end="2026-08-03T00:00:00Z",
            timeout_seconds=60,
        )


def test_proven_off_site_failed_resource_does_not_block_clean_resources(monkeypatch):
    failed = "ATL08_20251226145703_01873002_007_01.h5"
    clean = "ATL08_20240101000000_00010101_007_01.h5"

    def fake_worker(request, *, timeout_seconds):
        if request["operation"] == "cmr":
            return [clean, failed], []
        resource = request["resource"]
        if resource == clean:
            return pd.DataFrame({"value": [7]}), []
        return pd.DataFrame({"value": [9]}), ["Failure on resource test"]

    monkeypatch.setattr(MODULE.watchdog, "_run_worker_request", fake_worker)
    monkeypatch.setattr(
        MODULE,
        "_failed_resource_is_proven_off_site",
        lambda *args, **kwargs: (
            True,
            {
                "resource": failed,
                "tile_track_present": True,
                "epa_envelope_track_present": False,
            },
        ),
    )

    result = MODULE._recover_by_explicit_resources_with_site_relevance(
        polygon=_polygon(),
        start="2018-10-13T00:00:00Z",
        end="2026-08-03T00:00:00Z",
        timeout_seconds=60,
    )

    assert result["value"].tolist() == [7]
    assert result.attrs["campaign014_excluded_failed_off_site_resources"] == [failed]
