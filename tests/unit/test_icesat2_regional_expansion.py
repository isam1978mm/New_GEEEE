from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from app.pipeline.elevation_change.icesat2_repeat import Icesat2Segment


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "scan_icesat2_regional_expansion.py"
)
SPEC = importlib.util.spec_from_file_location(
    "scan_icesat2_regional_expansion", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _manifest(
    *,
    epsg: int = 32637,
    xmin: float = 300_000.0,
    ymin: float = 3_700_000.0,
    xmax: float = 306_000.0,
    ymax: float = 3_706_000.0,
):
    return SimpleNamespace(
        epsg=epsg,
        bounds_m={
            "xmin": xmin,
            "ymin": ymin,
            "xmax": xmax,
            "ymax": ymax,
        },
    )


def _selection(tmp_path: Path, name: str):
    run_dir = tmp_path / name
    run_dir.mkdir()
    return MODULE.RunSelection(
        run_dir=run_dir,
        completion_markers=("logRatio_dB.tif",),
    )


def _segment(
    *,
    segment_id: str,
    cycle: int,
    observed_at: datetime,
    height_m: float,
):
    return Icesat2Segment(
        segment_id=segment_id,
        observed_at=observed_at,
        longitude=37.0,
        latitude=33.5,
        x_m=300_000.0,
        y_m=3_700_000.0,
        height_m=height_m,
        height_uncertainty_m=2.0,
        terrain_slope=0.0,
        ground_photon_count=50,
        rgt=45,
        cycle=cycle,
        spot=5,
        gt="gt1l",
    )


def test_manifest_bounds_rejects_unordered_values():
    manifest = _manifest(xmin=10.0, xmax=9.0)
    try:
        MODULE._manifest_bounds(manifest)
    except ValueError as exc:
        assert "not ordered" in str(exc)
    else:
        raise AssertionError("unordered bounds should fail")


def test_build_query_tiles_covers_buffered_square():
    manifest = _manifest(xmin=0.0, ymin=0.0, xmax=6_000.0, ymax=6_000.0)
    tiles = MODULE.build_query_tiles(
        manifest,
        buffer_m=10_000.0,
        tile_size_m=10_000.0,
    )

    assert len(tiles) == 9
    assert tiles[0].xmin == -10_000.0
    assert tiles[0].ymin == -10_000.0
    assert tiles[-1].xmax == 16_000.0
    assert tiles[-1].ymax == 16_000.0
    assert all(len(tile.polygon_wgs84) == 5 for tile in tiles)


def test_deduplicate_geographies_collapses_matching_runs(tmp_path: Path):
    first = _selection(tmp_path, "run_a")
    second = _selection(tmp_path, "run_b")
    third = _selection(tmp_path, "run_c")
    manifests = {
        "run_a": _manifest(),
        "run_b": _manifest(xmin=300_050.0, xmax=306_050.0),
        "run_c": _manifest(xmin=500_000.0, xmax=506_000.0),
    }

    seeds, rejected = MODULE.deduplicate_geographies(
        [first, second, third],
        center_tolerance_m=250.0,
        size_tolerance_m=250.0,
        manifest_loader=lambda path: manifests[path.name],
    )

    assert rejected == []
    assert len(seeds) == 2
    members = sorted(seed.member_runs for seed in seeds)
    assert ("run_a", "run_b") in members
    assert ("run_c",) in members


def test_deduplicate_geographies_reports_bad_manifest(tmp_path: Path):
    good = _selection(tmp_path, "good")
    bad = _selection(tmp_path, "bad")

    def loader(path: Path):
        if path.name == "bad":
            raise ValueError("broken")
        return _manifest()

    seeds, rejected = MODULE.deduplicate_geographies(
        [good, bad],
        manifest_loader=loader,
    )

    assert len(seeds) == 1
    assert rejected == [
        {
            "run": "bad",
            "reason": "unreadable_grid_manifest",
            "error": "broken",
        }
    ]


def test_deduplicate_segments_removes_tile_overlap():
    observed = datetime(2022, 1, 1, tzinfo=UTC)
    first = _segment(
        segment_id="100",
        cycle=16,
        observed_at=observed,
        height_m=10.0,
    )
    duplicate = _segment(
        segment_id="100",
        cycle=16,
        observed_at=observed,
        height_m=10.0,
    )
    other = _segment(
        segment_id="101",
        cycle=16,
        observed_at=observed,
        height_m=11.0,
    )

    result = MODULE.deduplicate_segments([first, duplicate, other])

    assert len(result) == 2
    assert [item.segment_id for item in result] == ["100", "101"]


def test_candidate_rows_preserve_regional_boundary():
    rows = MODULE._candidate_rows(
        [
            {
                "centroid_longitude": 37.1,
                "centroid_latitude": 33.6,
                "event_start": "2021-01-01T00:00:00+00:00",
                "event_end": "2022-01-01T00:00:00+00:00",
                "median_step_m": 0.8,
                "step_nmad_m": 0.1,
                "segment_count": 5,
                "cross_spot_supported": True,
                "rgt": 45,
                "spot": 5,
                "pre_cycle": 11,
                "post_cycle": 16,
                "inside_existing_run_aoi": False,
            }
        ],
        geography_id="run_a",
        member_runs=("run_a", "run_b"),
    )

    assert rows == [
        {
            "geography_id": "run_a",
            "member_runs": ["run_a", "run_b"],
            "run_local_rank": 1,
            "longitude": 37.1,
            "latitude": 33.6,
            "event_start": "2021-01-01T00:00:00+00:00",
            "event_end": "2022-01-01T00:00:00+00:00",
            "median_step_m": 0.8,
            "step_nmad_m": 0.1,
            "segment_count": 5,
            "cross_spot_supported": True,
            "rgt": 45,
            "spot": 5,
            "pre_cycle": 11,
            "post_cycle": 16,
            "inside_existing_run_aoi": False,
        }
    ]
