from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_depth_s1_coverage as coverage


SYNTHETIC_COORDINATE_TEXT = "35.1234"


def _write_geojson(path: Path, geometry_type: str = "Polygon") -> None:
    if geometry_type == "Polygon":
        coordinates = [[[35.1234, 44.1234], [35.1244, 44.1234], [35.1244, 44.1244], [35.1234, 44.1234]]]
    elif geometry_type == "MultiPolygon":
        coordinates = [[[[35.1234, 44.1234], [35.1244, 44.1234], [35.1244, 44.1244], [35.1234, 44.1234]]]]
    else:
        coordinates = [35.1234, 44.1234]
    payload = {
        "type": "Feature",
        "properties": {"private_site_name": "synthetic_private_site"},
        "geometry": {"type": geometry_type, "coordinates": coordinates},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _ms(value: str) -> int:
    return int(datetime.fromisoformat(value).replace(tzinfo=UTC).timestamp() * 1000)


def test_repository_local_geometry_is_rejected() -> None:
    with pytest.raises(coverage.DepthS1CoverageError, match="outside the repository"):
        coverage.load_private_geometry(ROOT / "private_site.geojson")


@pytest.mark.parametrize("geometry_type", ["Point", "LineString"])
def test_non_polygon_geometry_is_rejected(tmp_path: Path, geometry_type: str) -> None:
    path = tmp_path / "site.geojson"
    _write_geojson(path, geometry_type=geometry_type)

    with pytest.raises(coverage.DepthS1CoverageError, match="Polygon or MultiPolygon"):
        coverage.load_private_geometry(path)


@pytest.mark.parametrize("geometry_type", ["Polygon", "MultiPolygon"])
def test_polygon_geometry_is_accepted_and_properties_are_removed(tmp_path: Path, geometry_type: str) -> None:
    path = tmp_path / "site.geojson"
    _write_geojson(path, geometry_type=geometry_type)

    result = coverage.load_private_geometry(path)

    assert result["type"] == "Feature"
    assert result["properties"] == {}
    assert result["geometry"]["type"] == geometry_type
    assert "private_site_name" not in json.dumps(result)


def test_invalid_or_reversed_date_windows_are_rejected() -> None:
    with pytest.raises(coverage.DepthS1CoverageError, match="YYYY-MM-DD"):
        coverage.validate_date_window("2020/01/01", "2021-01-01")
    with pytest.raises(coverage.DepthS1CoverageError, match="later"):
        coverage.validate_date_window("2021-01-01", "2020-01-01")
    with pytest.raises(coverage.DepthS1CoverageError, match="inside"):
        coverage.validate_date_window("2020-01-01", "2021-01-01", "2021-01-01")


def test_dry_run_performs_no_query_and_prints_no_private_values(tmp_path: Path) -> None:
    path = tmp_path / "site.geojson"
    _write_geojson(path)

    def forbidden_query(**_: object) -> list[dict[str, object]]:
        raise AssertionError("dry run must not call Earth Engine")

    result = coverage.run_coverage_check(
        site_geojson=path,
        start_date="2019-01-01",
        end_date="2021-01-01",
        event_date="2020-02-01",
        execute=False,
        query_fn=forbidden_query,
    )
    rendered = json.dumps(result)

    assert result["status"] == "coverage_query_dry_run_ready"
    assert result["query_executed"] is False
    assert result["coordinates_printed"] is False
    assert result["image_ids_printed"] is False
    assert SYNTHETIC_COORDINATE_TEXT not in rendered
    assert str(path) not in rendered
    assert "synthetic_private_site" not in rendered


def test_execute_returns_aggregate_orbit_and_pre_post_counts(tmp_path: Path) -> None:
    path = tmp_path / "site.geojson"
    _write_geojson(path)
    query_called = False

    def fake_query(**kwargs: object) -> list[dict[str, object]]:
        nonlocal query_called
        query_called = True
        assert kwargs["start_date"] == "2019-01-01"
        assert kwargs["end_date"] == "2021-01-01"
        assert kwargs["resolution_meters"] == 10
        return [
            {"time_start_ms": _ms("2020-01-01"), "orbit_pass": "ASCENDING", "relative_orbit": 10, "platform": "A"},
            {"time_start_ms": _ms("2020-02-01"), "orbit_pass": "DESCENDING", "relative_orbit": 20, "platform": "B"},
            {"time_start_ms": _ms("2020-03-01"), "orbit_pass": "ASCENDING", "relative_orbit": 10, "platform": "A"},
        ]

    result = coverage.run_coverage_check(
        site_geojson=path,
        start_date="2019-01-01",
        end_date="2021-01-01",
        event_date="2020-02-01",
        execute=True,
        query_fn=fake_query,
    )

    assert query_called is True
    assert result["status"] == "coverage_query_completed"
    assert result["query_executed"] is True
    assert result["acquisition_count"] == 3
    assert result["first_acquisition_date"] == "2020-01-01"
    assert result["last_acquisition_date"] == "2020-03-01"
    assert result["orbit_pass_counts"] == {"ASCENDING": 2, "DESCENDING": 1}
    assert result["relative_orbit_counts"] == {"10": 2, "20": 1}
    assert result["platform_counts"] == {"A": 2, "B": 1}
    assert result["pre_event_count"] == 1
    assert result["on_event_date_count"] == 1
    assert result["post_event_count"] == 1
    assert SYNTHETIC_COORDINATE_TEXT not in json.dumps(result)


def test_output_path_inside_repository_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "site.geojson"
    _write_geojson(path)

    with pytest.raises(coverage.DepthS1CoverageError, match="outside the repository"):
        coverage.run_coverage_check(
            site_geojson=path,
            start_date="2019-01-01",
            end_date="2021-01-01",
            output_path=ROOT / "coverage_summary.json",
        )


def test_aggregate_output_can_be_written_outside_repository(tmp_path: Path) -> None:
    geometry_path = tmp_path / "site.geojson"
    output_path = tmp_path / "coverage_summary.json"
    _write_geojson(geometry_path)

    result = coverage.run_coverage_check(
        site_geojson=geometry_path,
        start_date="2019-01-01",
        end_date="2021-01-01",
        output_path=output_path,
    )

    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["output_written"] is True
    assert written["status"] == "coverage_query_dry_run_ready"
    assert SYNTHETIC_COORDINATE_TEXT not in json.dumps(written)
    assert str(geometry_path) not in json.dumps(written)
