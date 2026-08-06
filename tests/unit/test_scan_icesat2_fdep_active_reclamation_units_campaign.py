from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "scan_icesat2_fdep_active_reclamation_units_campaign.py"
)
SPEC = importlib.util.spec_from_file_location("campaign009", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _feature(
    *,
    object_id: int,
    unit: str,
    status: str,
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
            "REC_STATUS": status,
            "AR_YEAR": 2021,
            "RELEASESTATUS": "Not Released",
            "GIS_ACRES": 100.0,
            "MINEDACRES": 80.0,
            "TOTALACRECL": 40.0,
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


def test_fetch_filters_to_work_in_progress_and_complete_units():
    captured: dict = {}

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        captured.update({"url": url, "params": params, "timeout": timeout})
        return _collection(
            _feature(
                object_id=1,
                unit="FUTURE",
                status="WF",
                xmin=-82.1,
                ymin=27.5,
                xmax=-82.0,
                ymax=27.6,
            ),
            _feature(
                object_id=2,
                unit="PROGRESS",
                status="WP",
                xmin=-82.0,
                ymin=27.5,
                xmax=-81.9,
                ymax=27.6,
            ),
            _feature(
                object_id=3,
                unit="COMPLETE",
                status=" wc ",
                xmin=-81.9,
                ymin=27.5,
                xmax=-81.8,
                ymax=27.6,
            ),
            _feature(
                object_id=4,
                unit="SCHEDULED",
                status="WS",
                xmin=-81.8,
                ymin=27.5,
                xmax=-81.7,
                ymax=27.6,
            ),
        )

    result = MODULE.fetch_active_reclamation_units(
        west=-82.2,
        south=27.2,
        east=-81.5,
        north=28.2,
        timeout_seconds=12,
        fetch_json=fake_fetch,
    )

    assert [item["properties"]["REC_UNITS"] for item in result["features"]] == [
        "PROGRESS",
        "COMPLETE",
    ]
    assert captured["url"] == MODULE.FDEP_ACTIVE_RECLAMATION_UNITS_LAYER_URL
    assert captured["params"]["where"] == "REC_STATUS IN ('WP','WC')"
    assert captured["params"]["returnGeometry"] == "true"
    assert captured["params"]["outSR"] == "4326"


def test_shared_unit_requires_every_segment_inside_one_named_unit():
    units = _collection(
        _feature(
            object_id=2,
            unit="A",
            status="WP",
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

    result = MODULE.shared_active_reclamation_unit(cluster, units)

    assert result is not None
    assert result["reclamation_unit"] == "A"
    assert result["reclamation_status"] == "WP"
    assert result["site_id"] == 12345


def test_shared_unit_rejects_cluster_split_between_units():
    units = _collection(
        _feature(
            object_id=2,
            unit="A",
            status="WP",
            xmin=-82.0,
            ymin=27.5,
            xmax=-81.95,
            ymax=27.6,
        ),
        _feature(
            object_id=3,
            unit="B",
            status="WC",
            xmin=-81.95,
            ymin=27.5,
            xmax=-81.9,
            ymax=27.6,
        ),
    )
    cluster = _cluster((-81.98, 27.52), (-81.92, 27.52))

    assert MODULE.shared_active_reclamation_unit(cluster, units) is None


def test_filter_clusters_attaches_unit_metadata_and_records_rejection():
    units = _collection(
        _feature(
            object_id=2,
            unit="A",
            status="WC",
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
    assert (
        survivors[0]["official_active_reclamation_unit"]["reclamation_unit"]
        == "A"
    )
    assert len(rejections) == 1
    assert (
        rejections[0]["reason"]
        == "supporting_segments_do_not_share_one_active_reclamation_unit"
    )


def test_status_code_rejects_non_string_and_normalizes_text():
    valid = _feature(
        object_id=5,
        unit="A",
        status=" wc ",
        xmin=-82.0,
        ymin=27.5,
        xmax=-81.9,
        ymax=27.6,
    )
    invalid = _feature(
        object_id=6,
        unit="B",
        status="WP",
        xmin=-81.9,
        ymin=27.5,
        xmax=-81.8,
        ymax=27.6,
    )
    invalid["properties"]["REC_STATUS"] = 123

    assert MODULE._status_code(valid) == "WC"
    assert MODULE._status_code(invalid) is None
