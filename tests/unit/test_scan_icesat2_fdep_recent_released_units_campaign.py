from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "scan_icesat2_fdep_recent_released_units_campaign.py"
)
SPEC = importlib.util.spec_from_file_location("campaign008", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _feature(
    *,
    object_id: int,
    unit: str,
    release_year: int | str,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "OBJECTID": object_id,
            "MINE_NAME": "Example Mine",
            "MINE_OPERATOR": "Example Operator",
            "SITE_ID": 12345,
            "REC_UNITS": unit,
            "REC_STATUS": "WC",
            "RELEASESTATUS": "Released",
            "RELEASE_YEAR": release_year,
            "GIS_ACRES": 100.0,
            "MINEDACRES": 80.0,
            "TOTALACRECL": 80.0,
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [xmin, ymin],
                    [xmax, ymin],
                    [xmax, ymax],
                    [xmin, ymax],
                    [xmin, ymin],
                ]
            ],
        },
    }


def _collection(*features: dict) -> dict:
    return {"type": "FeatureCollection", "features": list(features)}


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


def test_fetch_filters_to_release_year_window_and_requests_geometry():
    captured: dict = {}

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        captured.update({"url": url, "params": params, "timeout": timeout})
        return _collection(
            _feature(
                object_id=1,
                unit="OLD",
                release_year=2018,
                xmin=-82.1,
                ymin=27.5,
                xmax=-82.0,
                ymax=27.6,
            ),
            _feature(
                object_id=2,
                unit="A",
                release_year=2019,
                xmin=-82.0,
                ymin=27.5,
                xmax=-81.9,
                ymax=27.6,
            ),
            _feature(
                object_id=3,
                unit="B",
                release_year="2024",
                xmin=-81.9,
                ymin=27.5,
                xmax=-81.8,
                ymax=27.6,
            ),
            _feature(
                object_id=4,
                unit="FUTURE",
                release_year=2025,
                xmin=-81.8,
                ymin=27.5,
                xmax=-81.7,
                ymax=27.6,
            ),
        )

    result = MODULE.fetch_recent_released_units(
        west=-82.2,
        south=27.2,
        east=-81.5,
        north=28.2,
        timeout_seconds=12,
        fetch_json=fake_fetch,
    )

    assert [item["properties"]["REC_UNITS"] for item in result["features"]] == [
        "A",
        "B",
    ]
    assert captured["url"] == MODULE.FDEP_RELEASED_UNITS_LAYER_URL
    assert "RELEASE_YEAR >= 2019" in captured["params"]["where"]
    assert captured["params"]["returnGeometry"] == "true"
    assert captured["params"]["outSR"] == "4326"


def test_shared_released_unit_requires_every_segment_inside_one_unit():
    units = _collection(
        _feature(
            object_id=2,
            unit="A",
            release_year=2023,
            xmin=-82.0,
            ymin=27.5,
            xmax=-81.9,
            ymax=27.6,
        )
    )
    cluster = _cluster(
        (-81.98, 27.52),
        (-81.97, 27.53),
        (-81.96, 27.54),
        (-81.95, 27.55),
    )

    result = MODULE.shared_released_unit(cluster, units)

    assert result is not None
    assert result["reclamation_unit"] == "A"
    assert result["release_year"] == 2023
    assert result["site_id"] == 12345


def test_shared_released_unit_rejects_cluster_split_between_units():
    units = _collection(
        _feature(
            object_id=2,
            unit="A",
            release_year=2023,
            xmin=-82.0,
            ymin=27.5,
            xmax=-81.95,
            ymax=27.6,
        ),
        _feature(
            object_id=3,
            unit="B",
            release_year=2024,
            xmin=-81.95,
            ymin=27.5,
            xmax=-81.9,
            ymax=27.6,
        ),
    )
    cluster = _cluster((-81.98, 27.52), (-81.92, 27.52))

    assert MODULE.shared_released_unit(cluster, units) is None


def test_filter_clusters_attaches_unit_metadata_and_records_rejection():
    units = _collection(
        _feature(
            object_id=2,
            unit="A",
            release_year=2022,
            xmin=-82.0,
            ymin=27.5,
            xmax=-81.9,
            ymax=27.6,
        )
    )
    accepted = _cluster((-81.98, 27.52), (-81.97, 27.53))
    rejected = _cluster((-81.80, 27.52), (-81.79, 27.53))

    survivors, rejections = MODULE.filter_clusters_to_single_unit(
        [accepted, rejected], units
    )

    assert len(survivors) == 1
    assert survivors[0]["official_released_unit"]["reclamation_unit"] == "A"
    assert len(rejections) == 1
    assert (
        rejections[0]["reason"]
        == "supporting_segments_do_not_share_one_released_unit"
    )


def test_release_year_rejects_non_numeric_values():
    feature = _feature(
        object_id=5,
        unit="A",
        release_year="unknown",
        xmin=-82.0,
        ymin=27.5,
        xmax=-81.9,
        ymax=27.6,
    )

    assert MODULE._release_year(feature) is None
