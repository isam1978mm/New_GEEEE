from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import create_depth_background_candidates as candidates


SYNTHETIC_COORDINATE_TEXT = "35.1234"


def _write_rectangle(path: Path) -> None:
    payload = {
        "type": "Feature",
        "properties": {"private_label": "synthetic"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [35.1234, 44.1234],
                    [35.1244, 44.1234],
                    [35.1244, 44.1244],
                    [35.1234, 44.1244],
                    [35.1234, 44.1234],
                ]
            ],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_triangle(path: Path) -> None:
    payload = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [35.1234, 44.1234],
                    [35.1244, 44.1234],
                    [35.1239, 44.1244],
                    [35.1234, 44.1234],
                ]
            ],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _bbox(payload: dict[str, object]) -> tuple[float, float, float, float]:
    geometry = payload["geometry"]
    assert isinstance(geometry, dict)
    coordinates = geometry["coordinates"]
    assert isinstance(coordinates, list)
    ring = coordinates[0]
    assert isinstance(ring, list)
    xs = [float(point[0]) for point in ring[:-1]]
    ys = [float(point[1]) for point in ring[:-1]]
    return min(xs), min(ys), max(xs), max(ys)


def test_repository_local_site_geometry_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(candidates.DepthBackgroundCandidateError, match="outside the repository"):
        candidates.create_private_background_candidates(
            site_geojson=ROOT / "site.geojson",
            output_directory=tmp_path / "backgrounds",
            edge_gap_meters=100.0,
        )


def test_repository_local_output_directory_is_rejected(tmp_path: Path) -> None:
    site = tmp_path / "site.geojson"
    _write_rectangle(site)

    with pytest.raises(candidates.DepthBackgroundCandidateError, match="outside the repository"):
        candidates.create_private_background_candidates(
            site_geojson=site,
            output_directory=ROOT / "backgrounds",
            edge_gap_meters=100.0,
        )


def test_non_rectangular_site_geometry_is_rejected(tmp_path: Path) -> None:
    site = tmp_path / "site.geojson"
    _write_triangle(site)

    with pytest.raises(candidates.DepthBackgroundCandidateError, match="rectangle"):
        candidates.create_private_background_candidates(
            site_geojson=site,
            output_directory=tmp_path / "backgrounds",
            edge_gap_meters=100.0,
        )


@pytest.mark.parametrize("edge_gap", [0.0, -1.0, float("nan")])
def test_invalid_edge_gap_is_rejected(tmp_path: Path, edge_gap: float) -> None:
    site = tmp_path / "site.geojson"
    _write_rectangle(site)

    with pytest.raises(candidates.DepthBackgroundCandidateError, match="finite positive"):
        candidates.create_private_background_candidates(
            site_geojson=site,
            output_directory=tmp_path / "backgrounds",
            edge_gap_meters=edge_gap,
        )


def test_dry_run_writes_nothing_and_leaks_no_private_values(tmp_path: Path) -> None:
    site = tmp_path / "site.geojson"
    output_directory = tmp_path / "backgrounds"
    _write_rectangle(site)

    result = candidates.create_private_background_candidates(
        site_geojson=site,
        output_directory=output_directory,
        edge_gap_meters=100.0,
        write=False,
    )
    rendered = json.dumps(result)

    assert result["status"] == "private_background_candidates_dry_run_ready"
    assert result["candidate_count"] == 4
    assert result["output_written"] is False
    assert not output_directory.exists()
    assert result["coordinates_printed"] is False
    assert result["geometry_printed"] is False
    assert result["private_paths_printed"] is False
    assert result["network_request_made"] is False
    assert SYNTHETIC_COORDINATE_TEXT not in rendered
    assert str(tmp_path) not in rendered


def test_write_creates_four_closed_private_polygon_files(tmp_path: Path) -> None:
    site = tmp_path / "site.geojson"
    output_directory = tmp_path / "backgrounds"
    _write_rectangle(site)

    result = candidates.create_private_background_candidates(
        site_geojson=site,
        output_directory=output_directory,
        edge_gap_meters=100.0,
        write=True,
    )

    assert result["status"] == "private_background_candidates_written"
    assert result["candidate_count"] == 4
    assert result["output_written"] is True
    assert result["visual_review_required"] is True

    for direction in candidates.CANDIDATE_NAMES:
        path = output_directory / f"background_{direction}.geojson"
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["type"] == "Feature"
        assert payload["properties"] == {}
        assert payload["geometry"]["type"] == "Polygon"
        ring = payload["geometry"]["coordinates"][0]
        assert len(ring) == 5
        assert ring[0] == ring[-1]


def test_candidates_preserve_dimensions_and_do_not_overlap_site(tmp_path: Path) -> None:
    site = tmp_path / "site.geojson"
    output_directory = tmp_path / "backgrounds"
    _write_rectangle(site)
    site_rectangle = candidates.load_private_site_rectangle(site)

    candidates.create_private_background_candidates(
        site_geojson=site,
        output_directory=output_directory,
        edge_gap_meters=100.0,
        write=True,
    )

    site_bbox = tuple(site_rectangle["bbox"])
    for direction in candidates.CANDIDATE_NAMES:
        payload = json.loads(
            (output_directory / f"background_{direction}.geojson").read_text(encoding="utf-8")
        )
        candidate_bbox = _bbox(payload)
        assert candidates._bboxes_overlap(site_bbox, candidate_bbox) is False
        extracted = candidates._extract_polygon(payload)
        assert math.isclose(
            float(extracted["width_meters"]),
            float(site_rectangle["width_meters"]),
            rel_tol=1e-6,
        )
        assert math.isclose(
            float(extracted["height_meters"]),
            float(site_rectangle["height_meters"]),
            rel_tol=1e-6,
        )


def test_existing_candidate_output_is_not_overwritten(tmp_path: Path) -> None:
    site = tmp_path / "site.geojson"
    output_directory = tmp_path / "backgrounds"
    output_directory.mkdir()
    existing = output_directory / "background_north.geojson"
    existing.write_text("keep", encoding="utf-8")
    _write_rectangle(site)

    with pytest.raises(candidates.DepthBackgroundCandidateError, match="already exists"):
        candidates.create_private_background_candidates(
            site_geojson=site,
            output_directory=output_directory,
            edge_gap_meters=100.0,
            write=True,
        )

    assert existing.read_text(encoding="utf-8") == "keep"
    assert not (output_directory / "background_east.geojson").exists()


def test_result_never_contains_coordinates_geometry_or_private_path(tmp_path: Path) -> None:
    site = tmp_path / "site.geojson"
    _write_rectangle(site)

    result = candidates.create_private_background_candidates(
        site_geojson=site,
        output_directory=tmp_path / "backgrounds",
        edge_gap_meters=100.0,
        write=False,
    )
    rendered = json.dumps(result)

    assert result["coordinates_printed"] is False
    assert result["geometry_printed"] is False
    assert result["private_paths_printed"] is False
    assert SYNTHETIC_COORDINATE_TEXT not in rendered
    assert str(tmp_path) not in rendered
