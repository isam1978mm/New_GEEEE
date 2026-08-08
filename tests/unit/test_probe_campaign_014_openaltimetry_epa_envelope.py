from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "probe_campaign_014_openaltimetry_epa_envelope.py"
)
SPEC = importlib.util.spec_from_file_location("campaign014_epa_envelope_probe", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_epa_envelope_reads_polygon_coordinates(tmp_path):
    path = tmp_path / "epa.geojson"
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"EPA_ID": "VAD980829030"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [-77.50, 38.95],
                                    [-77.40, 38.95],
                                    [-77.40, 39.05],
                                    [-77.50, 39.05],
                                    [-77.50, 38.95],
                                ]
                            ],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert MODULE.epa_envelope(path) == (-77.5, 38.95, -77.4, 39.05)


def test_track_id_extraction_is_tolerant():
    payload = {"tracks": [{"track": 187}, {"trackId": "629"}, {"rgt": -1}]}
    assert MODULE._track_ids(payload) == [187, 629]


def test_probe_classifies_missing_target_track(tmp_path):
    responses = [
        (200, "application/json", json.dumps([{"track": 629}]).encode()),
        (
            200,
            "application/json",
            json.dumps({"product": "ATL08", "trackId": -1, "series": []}).encode(),
        ),
    ]

    def fake_fetch(url, *, timeout_seconds):
        assert timeout_seconds == 12
        return responses.pop(0)

    result = MODULE.probe_target(
        {"resource": "x.h5", "date": "2025-12-26", "track_id": 187},
        bounds=(-77.5, 38.9, -77.4, 39.0),
        output_dir=tmp_path,
        timeout_seconds=12,
        fetch=fake_fetch,
    )

    assert result["target_track_present"] is False
    assert result["decision"] == "target_track_absent_from_exact_epa_envelope"


def test_probe_classifies_crossing_track_with_no_atl08(tmp_path):
    responses = [
        (200, "application/json", json.dumps([{"track": 187}]).encode()),
        (
            200,
            "application/json",
            json.dumps({"product": "ATL08", "trackId": -1, "series": []}).encode(),
        ),
    ]

    def fake_fetch(url, *, timeout_seconds):
        return responses.pop(0)

    result = MODULE.probe_target(
        {"resource": "x.h5", "date": "2025-12-26", "track_id": 187},
        bounds=(-77.5, 38.9, -77.4, 39.0),
        output_dir=tmp_path,
        timeout_seconds=12,
        fetch=fake_fetch,
    )

    assert result["target_track_present"] is True
    assert result["atl08_point_count"] == 0
    assert (
        result["decision"]
        == "target_track_crosses_exact_epa_envelope_but_atl08_unavailable"
    )


def test_probe_classifies_available_atl08_points(tmp_path):
    responses = [
        (200, "application/json", json.dumps([{"track": 629}]).encode()),
        (
            200,
            "application/json",
            json.dumps(
                {
                    "product": "ATL08",
                    "trackId": 629,
                    "series": [
                        {
                            "beam": "gt1l",
                            "lat_lon_elev_canopy": [
                                [38.98, -77.45, 80.0, 12.0],
                                [38.981, -77.451, 80.1, 12.5],
                            ],
                        }
                    ],
                }
            ).encode(),
        ),
    ]

    def fake_fetch(url, *, timeout_seconds):
        return responses.pop(0)

    result = MODULE.probe_target(
        {"resource": "x.h5", "date": "2021-05-04", "track_id": 629},
        bounds=(-77.5, 38.9, -77.4, 39.0),
        output_dir=tmp_path,
        timeout_seconds=12,
        fetch=fake_fetch,
    )

    assert result["target_track_present"] is True
    assert result["atl08_series_count"] == 1
    assert result["atl08_point_count"] == 2
    assert (
        result["decision"]
        == "target_track_and_atl08_present_in_exact_epa_envelope"
    )
