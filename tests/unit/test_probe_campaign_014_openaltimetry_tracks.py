from __future__ import annotations

import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "probe_campaign_014_openaltimetry_tracks.py"
SPEC = importlib.util.spec_from_file_location("campaign014_openaltimetry_tracks", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_track_ids_extracts_common_openaltimetry_shapes():
    payload = {
        "tracks": [
            {"track": 629},
            {"trackId": "187"},
            {"rgt": 812},
        ]
    }
    assert MODULE._track_ids(payload) == [187, 629, 812]


def test_probe_marks_target_present(tmp_path):
    target = {"resource": "x.h5", "date": "2021-05-04", "track_id": 629}

    def fake_fetch(url, *, timeout_seconds):
        assert "getTracks" in url
        assert "date=2021-05-04" in url
        return 200, "application/json", json.dumps([{"track": 629}, {"track": 812}]).encode()

    result = MODULE.probe_target(target, output_dir=tmp_path, timeout_seconds=10, fetch=fake_fetch)
    assert result["target_track_present"] is True
    assert result["decision"] == "target_track_intersects_campaign_bounds"


def test_probe_marks_target_absent_when_other_tracks_exist(tmp_path):
    target = {"resource": "x.h5", "date": "2025-12-26", "track_id": 187}

    def fake_fetch(url, *, timeout_seconds):
        return 200, "application/json", json.dumps([{"track": 45}, {"track": 812}]).encode()

    result = MODULE.probe_target(target, output_dir=tmp_path, timeout_seconds=10, fetch=fake_fetch)
    assert result["target_track_present"] is False
    assert result["returned_track_count"] == 2
    assert result["decision"] == "target_track_absent_while_other_tracks_intersect"


def test_probe_keeps_empty_track_day_unresolved(tmp_path):
    target = {"resource": "x.h5", "date": "2025-12-26", "track_id": 187}

    def fake_fetch(url, *, timeout_seconds):
        return 200, "application/json", b"[]"

    result = MODULE.probe_target(target, output_dir=tmp_path, timeout_seconds=10, fetch=fake_fetch)
    assert result["target_track_present"] is False
    assert result["decision"] == "no_tracks_returned_date_or_service_unresolved"
