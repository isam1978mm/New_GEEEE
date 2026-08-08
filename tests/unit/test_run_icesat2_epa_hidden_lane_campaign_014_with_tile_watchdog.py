from __future__ import annotations

import importlib.util
import json
import pickle
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "run_icesat2_epa_hidden_lane_campaign_014_with_tile_watchdog.py"
)
SPEC = importlib.util.spec_from_file_location("campaign014_watchdog", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _polygon() -> list[dict[str, float]]:
    return [
        {"lon": -77.46, "lat": 38.98},
        {"lon": -77.44, "lat": 38.98},
        {"lon": -77.44, "lat": 39.00},
        {"lon": -77.46, "lat": 39.00},
        {"lon": -77.46, "lat": 38.98},
    ]


def _partial_alert(resource: str) -> str:
    return (
        "Alert <-7>: Failure on resource "
        f"{resource} beam gt3r: H5Coro::Future read failure on "
        "gt3r/land_segments/latitude"
    )


def test_watchdog_success_reads_child_result(monkeypatch):
    expected = {"rows": 14}

    def fake_run(command, *, check, timeout, capture_output, text):
        assert check is False
        assert timeout == MODULE.DEFAULT_ATL08_TILE_TIMEOUT_SECONDS
        assert capture_output is True
        assert text is True
        assert command[2] == MODULE.WORKER_FLAG
        request_path = Path(command[3])
        result_path = Path(command[4])
        request = json.loads(request_path.read_text(encoding="utf-8"))
        assert request["operation"] == "broad"
        assert request["start"] == "2018-10-13T00:00:00Z"
        assert request["end"] == "2026-08-03T00:00:00Z"
        with result_path.open("wb") as stream:
            pickle.dump(expected, stream)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)

    result = MODULE._query_atl08_with_timeout(
        polygon=_polygon(),
        start="2018-10-13T00:00:00Z",
        end="2026-08-03T00:00:00Z",
    )

    assert result == expected


def test_watchdog_converts_timeout_to_tile_failure(monkeypatch):
    def fake_run(command, *, check, timeout, capture_output, text):
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)

    with pytest.raises(MODULE.Campaign014TileTimeoutError, match="300 seconds"):
        MODULE._query_atl08_with_timeout(
            polygon=_polygon(),
            start="2018-10-13T00:00:00Z",
            end="2026-08-03T00:00:00Z",
        )


def test_watchdog_surfaces_child_error(monkeypatch):
    def fake_run(command, *, check, timeout, capture_output, text):
        error_path = Path(command[5])
        error_path.write_text(
            json.dumps(
                {
                    "error_type": "Icesat2AuditError",
                    "error": "remote failure",
                }
            ),
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="Icesat2AuditError: remote failure"):
        MODULE._query_atl08_with_timeout(
            polygon=_polygon(),
            start="2018-10-13T00:00:00Z",
            end="2026-08-03T00:00:00Z",
        )


def test_watchdog_retries_partial_read_then_accepts_clean_attempt(monkeypatch):
    expected = {"rows": 31}
    calls = 0

    def fake_run(command, *, check, timeout, capture_output, text):
        nonlocal calls
        calls += 1
        result_path = Path(command[4])
        with result_path.open("wb") as stream:
            pickle.dump(expected, stream)
        if calls == 1:
            return SimpleNamespace(
                returncode=0,
                stdout=_partial_alert("ATL08_20210504235905_06291102_007_01.h5"),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)

    result = MODULE._query_atl08_with_timeout(
        polygon=_polygon(),
        start="2018-10-13T00:00:00Z",
        end="2026-08-03T00:00:00Z",
    )

    assert calls == 2
    assert result == expected


def test_broad_partial_falls_back_to_all_cmr_resources(monkeypatch):
    resource_a = "ATL08_20210504235905_06291102_007_01.h5"
    resource_b = "ATL08_20220228215041_10481406_007_01.h5"
    broad_calls = 0
    resource_calls: list[str] = []

    def fake_worker(request, *, timeout_seconds):
        nonlocal broad_calls
        assert timeout_seconds == MODULE.DEFAULT_ATL08_TILE_TIMEOUT_SECONDS
        operation = request["operation"]
        if operation == "broad":
            broad_calls += 1
            return pd.DataFrame({"value": [0]}), [_partial_alert(resource_a)]
        if operation == "cmr":
            return [resource_a, resource_b], []
        if operation == "resource":
            resource = request["resource"]
            resource_calls.append(resource)
            value = 1 if resource == resource_a else 2
            return pd.DataFrame({"value": [value]}), []
        raise AssertionError(operation)

    monkeypatch.setattr(MODULE, "_run_worker_request", fake_worker)

    result = MODULE._query_atl08_with_timeout(
        polygon=_polygon(),
        start="2018-10-13T00:00:00Z",
        end="2026-08-03T00:00:00Z",
    )

    assert broad_calls == MODULE.DEFAULT_ATL08_TILE_ATTEMPTS
    assert resource_calls == [resource_a, resource_b]
    assert result["value"].tolist() == [1, 2]


def test_explicit_resource_retries_partial_then_accepts_clean(monkeypatch):
    resource = "ATL08_20210504235905_06291102_007_01.h5"
    resource_attempts = 0

    def fake_worker(request, *, timeout_seconds):
        nonlocal resource_attempts
        if request["operation"] == "cmr":
            return [resource], []
        assert request["operation"] == "resource"
        resource_attempts += 1
        frame = pd.DataFrame({"value": [8]})
        if resource_attempts < 3:
            return frame, [_partial_alert(resource)]
        return frame, []

    monkeypatch.setattr(MODULE, "_run_worker_request", fake_worker)

    result = MODULE._recover_by_explicit_resources(
        polygon=_polygon(),
        start="2018-10-13T00:00:00Z",
        end="2026-08-03T00:00:00Z",
        timeout_seconds=300,
    )

    assert resource_attempts == 3
    assert result["value"].tolist() == [8]


def test_explicit_resource_failure_keeps_tile_incomplete(monkeypatch):
    resource = "ATL08_20210504235905_06291102_007_01.h5"
    calls = 0

    def fake_worker(request, *, timeout_seconds):
        nonlocal calls
        if request["operation"] == "cmr":
            return [resource], []
        calls += 1
        return pd.DataFrame({"value": [9]}), [_partial_alert(resource)]

    monkeypatch.setattr(MODULE, "_run_worker_request", fake_worker)

    with pytest.raises(
        MODULE.Campaign014ResourceRecoveryError,
        match="failed 1/1 CMR-listed resources",
    ):
        MODULE._recover_by_explicit_resources(
            polygon=_polygon(),
            start="2018-10-13T00:00:00Z",
            end="2026-08-03T00:00:00Z",
            timeout_seconds=300,
        )

    assert calls == MODULE.DEFAULT_ATL08_RESOURCE_ATTEMPTS


def test_unique_resource_names_deduplicates_without_dropping_order():
    assert MODULE._unique_resource_names(["A.h5", "B.h5", "A.h5", " "]) == [
        "A.h5",
        "B.h5",
    ]


def test_partial_read_detector_ignores_harmless_worker_output():
    assert MODULE._partial_read_lines("normal progress\n", "") == []
    assert MODULE._partial_read_lines(None, "warning without resource failure") == []


def test_install_timeout_hook_changes_only_query_hook():
    original_query = MODULE.campaign014.campaign._query_atl08
    original_region_result = MODULE.campaign014.campaign._region_result
    original_summary = MODULE.campaign014.campaign._summary
    try:
        MODULE.install_timeout_hook()
        assert MODULE.campaign014.campaign._query_atl08 is MODULE._query_atl08_with_timeout
        assert MODULE.campaign014.campaign._region_result is MODULE.campaign014._region_result
        assert MODULE.campaign014.campaign._summary is MODULE.campaign014._summary
    finally:
        MODULE.campaign014.campaign._query_atl08 = original_query
        MODULE.campaign014.campaign._region_result = original_region_result
        MODULE.campaign014.campaign._summary = original_summary
