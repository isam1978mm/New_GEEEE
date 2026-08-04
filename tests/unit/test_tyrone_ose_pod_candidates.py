from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts.fetch_tyrone_ose_pod_candidates import (
    BBox,
    PodFetchError,
    build_query_params,
    normalize_feature,
    normalize_features,
    parse_bbox,
    score_candidate,
    write_outputs,
)


def test_parse_bbox_and_arcgis_envelope() -> None:
    bbox = parse_bbox("-108.50,32.55,-108.25,32.75")

    assert bbox == BBox(-108.50, 32.55, -108.25, 32.75)
    assert bbox.as_arcgis_envelope() == "-108.5,32.55,-108.25,32.75"


@pytest.mark.parametrize(
    "raw",
    [
        "-108.5,32.5,-108.2",
        "west,32.5,-108.2,32.8",
        "-108.2,32.5,-108.5,32.8",
        "-108.5,33.0,-108.2,32.8",
    ],
)
def test_parse_bbox_rejects_invalid_values(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_bbox(raw)


def test_build_query_params_uses_published_truncated_quality_fields() -> None:
    params = build_query_params(BBox(-108.5, 32.55, -108.25, 32.75))

    assert params["geometryType"] == "esriGeometryEnvelope"
    assert params["inSR"] == "4326"
    assert params["outSR"] == "4326"
    assert params["returnGeometry"] == "true"
    assert "utm_accura" in params["outFields"]
    assert "xy_accurac" in params["outFields"]
    assert "nmwrrs_wrs" in params["outFields"]
    assert "datum" in params["outFields"]
    assert "utm_accuracy" not in params["outFields"]


def test_score_candidate_prioritizes_map_label_and_coordinate_quality() -> None:
    score, reasons = score_candidate(
        {
            "pod_name": "27-2005-05",
            "own_lname": "Freeport McMoRan Tyrone",
            "easting": 123.0,
            "northing": 456.0,
            "datum": "NAD83",
            "utm_accuracy": "1",
            "xy_accuracy": "1",
        }
    )

    assert score >= 140
    assert "map_label:27-2005-05" in reasons
    assert "owner_or_location:freeport" in reasons
    assert "published_utm_accuracy" in reasons


def test_normalize_feature_maps_hosted_field_names_to_stable_output_names() -> None:
    row = normalize_feature(
        {
            "attributes": {
                "OBJECTID": 7,
                "pod_name": "MVR-2",
                "easting": 123456.7,
                "northing": 3456789.0,
                "utm_zone": "12",
                "datum": "NAD83",
                "utm_accura": "1",
                "xy_accurac": "A",
                "nmwrrs_wrs": "https://example.test/well",
            },
            "geometry": {"x": -108.4, "y": 32.65},
        }
    )

    assert row["OBJECTID"] == 7
    assert row["longitude"] == -108.4
    assert row["latitude"] == 32.65
    assert row["easting"] == 123456.7
    assert row["northing"] == 3456789.0
    assert row["utm_accuracy"] == "1"
    assert row["xy_accuracy"] == "A"
    assert row["nmwrrs_wrsum_url"] == "https://example.test/well"
    assert row["priority_score"] >= 117


def test_normalize_features_sorts_highest_priority_first() -> None:
    rows = normalize_features(
        [
            {
                "attributes": {"OBJECTID": 1, "pod_name": "unrelated"},
                "geometry": {"x": -108.3, "y": 32.6},
            },
            {
                "attributes": {"OBJECTID": 2, "pod_name": "27-2005-04"},
                "geometry": {"x": -108.4, "y": 32.65},
            },
        ]
    )

    assert rows[0]["OBJECTID"] == 2
    assert rows[0]["priority_score"] > rows[1]["priority_score"]


def test_write_outputs_keeps_geometry_blocked(tmp_path: Path) -> None:
    rows = [
        normalize_feature(
            {
                "attributes": {
                    "OBJECTID": 2,
                    "pod_name": "27-2005-04",
                    "datum": "NAD83",
                    "utm_accura": "1",
                },
                "geometry": {"x": -108.4, "y": 32.65},
            }
        )
    ]
    json_path, csv_path = write_outputs(
        output_dir=tmp_path,
        bbox=BBox(-108.5, 32.55, -108.25, 32.75),
        service_url="https://example.test/query",
        payload={"features": [], "exceededTransferLimit": False},
        rows=rows,
    )

    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["status"] == "official_pod_candidates_downloaded"
    assert report["coordinate_geometry_unblocked"] is False
    assert report["numerical_depth_unlocked"] is False
    assert report["feature_count"] == 1

    with csv_path.open(newline="", encoding="utf-8") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert csv_rows[0]["pod_name"] == "27-2005-04"
    assert csv_rows[0]["utm_accuracy"] == "1"
    assert "map_label:27-2005-04" in csv_rows[0]["priority_reasons"]


def test_pod_fetch_error_is_runtime_error() -> None:
    assert issubclass(PodFetchError, RuntimeError)
