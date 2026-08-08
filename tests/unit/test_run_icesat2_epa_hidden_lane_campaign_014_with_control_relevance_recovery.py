from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "run_icesat2_epa_hidden_lane_campaign_014_with_control_relevance_recovery.py"
)
SPEC = importlib.util.spec_from_file_location("campaign014_control_relevance", MODULE_PATH)
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


def test_positive_control_plus_epa_absence_proves_off_site():
    resource = "ATL08_20251226145703_01873002_007_01.h5"

    def fake_lookup(*, date, bounds, timeout_seconds):
        assert date == "2025-12-26"
        assert timeout_seconds == 60
        if bounds == MODULE.CONTROL_BOUNDS:
            return [187]
        if bounds == MODULE.site.EPA_ENVELOPE:
            return []
        raise AssertionError(bounds)

    proven, proof = MODULE._failed_resource_is_proven_off_site_with_control(
        resource,
        tile_polygon=_polygon(),
        timeout_seconds=60,
        track_lookup=fake_lookup,
    )

    assert proven is True
    assert proof["control_track_present"] is True
    assert proof["epa_envelope_track_present"] is False


def test_missing_positive_control_keeps_resource_blocking():
    resource = "ATL08_20251226145703_01873002_007_01.h5"

    def fake_lookup(*, date, bounds, timeout_seconds):
        return []

    proven, proof = MODULE._failed_resource_is_proven_off_site_with_control(
        resource,
        tile_polygon=_polygon(),
        timeout_seconds=60,
        track_lookup=fake_lookup,
    )

    assert proven is False
    assert proof["control_track_present"] is False
    assert proof["epa_envelope_track_present"] is False


def test_epa_presence_keeps_resource_blocking():
    resource = "ATL08_20210504235905_06291102_007_01.h5"

    def fake_lookup(*, date, bounds, timeout_seconds):
        return [629]

    proven, proof = MODULE._failed_resource_is_proven_off_site_with_control(
        resource,
        tile_polygon=_polygon(),
        timeout_seconds=60,
        track_lookup=fake_lookup,
    )

    assert proven is False
    assert proof["control_track_present"] is True
    assert proof["epa_envelope_track_present"] is True


def test_install_replaces_only_site_relevance_proof_function():
    original = MODULE.site._failed_resource_is_proven_off_site
    original_recover = MODULE.site._recover_by_explicit_resources_with_site_relevance
    try:
        MODULE.install_control_relevance_recovery()
        assert (
            MODULE.site._failed_resource_is_proven_off_site
            is MODULE._failed_resource_is_proven_off_site_with_control
        )
        assert (
            MODULE.site._recover_by_explicit_resources_with_site_relevance
            is original_recover
        )
    finally:
        MODULE.site._failed_resource_is_proven_off_site = original
