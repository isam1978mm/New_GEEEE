from __future__ import annotations

import importlib.util
import json
import pickle
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "run_icesat2_pa_aml_campaign_011_with_tile_watchdog.py"
)
SPEC = importlib.util.spec_from_file_location("campaign011_watchdog", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _polygon() -> list[dict[str, float]]:
    return [
        {"lon": -79.1, "lat": 40.0},
        {"lon": -79.0, "lat": 40.0},
        {"lon": -79.0, "lat": 40.1},
        {"lon": -79.1, "lat": 40.1},
        {"lon": -79.1, "lat": 40.0},
    ]


def test_watchdog_success_reads_child_result(monkeypatch):
    expected = {"rows": 123}

    def fake_run(command, *, check, timeout):
        assert check is False
        assert timeout == MODULE.DEFAULT_ATL08_TILE_TIMEOUT_SECONDS
        assert command[2] == MODULE.WORKER_FLAG
        request_path = Path(command[3])
        result_path = Path(command[4])
        request = json.loads(request_path.read_text(encoding="utf-8"))
        assert request["start"] == "2018-10-13T00:00:00Z"
        assert request["end"] == "2026-08-03T00:00:00Z"
        with result_path.open("wb") as stream:
            pickle.dump(expected, stream)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)

    result = MODULE._query_atl08_with_timeout(
        polygon=_polygon(),
        start="2018-10-13T00:00:00Z",
        end="2026-08-03T00:00:00Z",
    )

    assert result == expected


def test_watchdog_converts_subprocess_timeout_to_tile_failure(monkeypatch):
    def fake_run(command, *, check, timeout):
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)

    with pytest.raises(MODULE.Campaign011TileTimeoutError, match="300 seconds"):
        MODULE._query_atl08_with_timeout(
            polygon=_polygon(),
            start="2018-10-13T00:00:00Z",
            end="2026-08-03T00:00:00Z",
        )


def test_watchdog_surfaces_child_error(monkeypatch):
    def fake_run(command, *, check, timeout):
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
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="Icesat2AuditError: remote failure"):
        MODULE._query_atl08_with_timeout(
            polygon=_polygon(),
            start="2018-10-13T00:00:00Z",
            end="2026-08-03T00:00:00Z",
        )


def test_install_timeout_hook_changes_only_query_hook():
    original = MODULE.campaign011.campaign._query_atl08
    original_region_result = MODULE.campaign011.campaign._region_result
    original_summary = MODULE.campaign011.campaign._summary
    try:
        MODULE.install_timeout_hook()
        assert MODULE.campaign011.campaign._query_atl08 is MODULE._query_atl08_with_timeout
        assert MODULE.campaign011.campaign._region_result is original_region_result
        assert MODULE.campaign011.campaign._summary is original_summary
    finally:
        MODULE.campaign011.campaign._query_atl08 = original
