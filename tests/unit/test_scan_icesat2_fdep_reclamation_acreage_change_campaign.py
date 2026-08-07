from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "scan_icesat2_fdep_reclamation_acreage_change_campaign.py"
)
SPEC = importlib.util.spec_from_file_location("campaign010", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _feature(
    *,
    object_id: int,
    site_id: int,
    unit: str,
    status: str,
    total_reclaimed: float,
    year: int,
    xmin: float = -82.0,
    ymin: float = 27.5,
    xmax: float = -81.9,
    ymax: float = 27.6,
) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "OBJECTID": object_id,
            "MINE_NAME": "Example Mine",
            "MINE_OPERATOR": "Example Operator",
            "SITE_ID": site_id,
            "REC_UNITS": unit,
            "REC_STATUS": status,
            "AR_YEAR": year,
            "RELEASESTATUS": "Not Released",
            "GIS_ACRES": 100.0,
            "MINEDACRES": 80.0,
            "TOTALACRECL": total_reclaimed,
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


def _layer_year(url: str) -> int:
    layer_id = int(url.rstrip("/").split("/")[-2])
    for year, candidate_layer in MODULE.ANNUAL_LAYER_IDS.items():
        if candidate_layer == layer_id:
            return year
    raise AssertionError(f"unexpected layer {layer_id}")


def test_stable_unit_key_normalizes_unit_name():
    feature = _feature(
        object_id=1,
        site_id=77,
        unit="  north   cell  ",
        status="WP",
        total_reclaimed=1.0,
        year=2018,
    )

    assert MODULE._stable_unit_key(feature) == "77|NORTH CELL"


def test_fetch_selects_positive_total_reclaimed_change_across_all_years():
    calls: list[tuple[int, dict[str, str]]] = []

    values = {
        2018: 10.0,
        2019: 10.0,
        2020: 18.5,
        2021: 23.0,
    }
    statuses = {2018: "WS", 2019: "WP", 2020: "WP", 2021: "WC"}

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        year = _layer_year(url)
        calls.append((year, params))
        return _collection(
            _feature(
                object_id=year,
                site_id=123,
                unit="Unit A",
                status=statuses[year],
                total_reclaimed=values[year],
                year=year,
            ),
            _feature(
                object_id=year + 10000,
                site_id=456,
                unit="Flat Unit",
                status="WC",
                total_reclaimed=5.0,
                year=year,
                xmin=-81.8,
                xmax=-81.7,
            ),
        )

    result = MODULE.fetch_reclamation_activity_units(
        west=-82.2,
        south=27.2,
        east=-81.5,
        north=28.2,
        timeout_seconds=12,
        fetch_json=fake_fetch,
    )

    assert [year for year, _ in calls] == [2018, 2019, 2020, 2021]
    assert all(params["where"] == "1=1" for _, params in calls)
    assert all(params["returnGeometry"] == "true" for _, params in calls)
    assert all(params["outSR"] == "4326" for _, params in calls)

    assert len(result["features"]) == 1
    feature = result["features"][0]
    properties = feature["properties"]
    assert properties["ACTIVITY_UNIT_KEY"] == "123|UNIT A"
    assert properties["ACTIVITY_SELECTED_GEOMETRY_YEAR"] == 2021
    assert properties["ACTIVITY_FIRST_YEAR"] == 2019
    assert properties["ACTIVITY_LAST_YEAR"] == 2021
    assert properties["ACTIVITY_TOTAL_POSITIVE_INCREASE_ACRES"] == 13.0
    assert [
        (item["from_year"], item["to_year"])
        for item in properties["ACTIVITY_POSITIVE_TRANSITIONS"]
    ] == [(2019, 2020), (2020, 2021)]


def test_fetch_can_include_activity_not_selected_by_one_2021_status_filter():
    values = {2018: 1.0, 2019: 4.0, 2020: 4.0, 2021: 4.0}
    statuses = {2018: "WF", 2019: "WS", 2020: "WS", 2021: "WS"}

    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        year = _layer_year(url)
        return _collection(
            _feature(
                object_id=year,
                site_id=9,
                unit="Historical Activity",
                status=statuses[year],
                total_reclaimed=values[year],
                year=year,
            )
        )

    result = MODULE.fetch_reclamation_activity_units(
        west=-82.2,
        south=27.2,
        east=-81.5,
        north=28.2,
        timeout_seconds=12,
        fetch_json=fake_fetch,
    )

    assert len(result["features"]) == 1
    props = result["features"][0]["properties"]
    assert props["ACTIVITY_SELECTED_GEOMETRY_YEAR"] == 2019
    assert props["ACTIVITY_POSITIVE_TRANSITIONS"][0]["increase_acres"] == 3.0


def test_ambiguous_duplicate_identity_is_rejected_not_guessed():
    def fake_fetch(url: str, params: dict[str, str], timeout: float) -> dict:
        year = _layer_year(url)
        features = [
            _feature(
                object_id=year,
                site_id=1,
                unit="Ambiguous",
                status="WP",
                total_reclaimed=float(year - 2017),
                year=year,
            ),
            _feature(
                object_id=year + 10000,
                site_id=2,
                unit="Good",
                status="WP",
                total_reclaimed=float(year - 2017),
                year=year,
                xmin=-81.8,
                xmax=-81.7,
            ),
        ]
        if year == 2020:
            features.append(
                _feature(
                    object_id=99999,
                    site_id=1,
                    unit=" ambiguous ",
                    status="WP",
                    total_reclaimed=99.0,
                    year=year,
                    xmin=-81.99,
                    xmax=-81.89,
                )
            )
        return _collection(*features)

    result = MODULE.fetch_reclamation_activity_units(
        west=-82.2,
        south=27.2,
        east=-81.5,
        north=28.2,
        timeout_seconds=12,
        fetch_json=fake_fetch,
    )

    keys = [item["properties"]["ACTIVITY_UNIT_KEY"] for item in result["features"]]
    assert keys == ["2|GOOD"]


def test_activity_metadata_carries_transition_evidence():
    feature = _feature(
        object_id=4,
        site_id=321,
        unit="A",
        status="WC",
        total_reclaimed=25.0,
        year=2021,
    )
    feature["properties"].update(
        {
            "ACTIVITY_UNIT_KEY": "321|A",
            "ACTIVITY_SOURCE_YEARS": [2018, 2019, 2020, 2021],
            "ACTIVITY_SELECTED_GEOMETRY_YEAR": 2021,
            "ACTIVITY_POSITIVE_TRANSITIONS": [
                {
                    "from_year": 2020,
                    "to_year": 2021,
                    "increase_acres": 5.0,
                }
            ],
            "ACTIVITY_STATUS_HISTORY": [],
            "ACTIVITY_TOTAL_POSITIVE_INCREASE_ACRES": 5.0,
            "ACTIVITY_FIRST_YEAR": 2020,
            "ACTIVITY_LAST_YEAR": 2021,
        }
    )

    metadata = MODULE._activity_unit_metadata(feature)

    assert metadata["identity"] == "321|A"
    assert metadata["activity_selected_geometry_year"] == 2021
    assert metadata["activity_total_positive_increase_acres"] == 5.0
    assert metadata["activity_first_year"] == 2020
    assert metadata["activity_last_year"] == 2021
