from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "scan_all_icesat2_terrain_steps.py"
)
SPEC = importlib.util.spec_from_file_location("scan_all_icesat2_terrain_steps", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _make_run(root: Path, name: str, *, completed: bool = True) -> Path:
    run_dir = root / name
    run_dir.mkdir(parents=True)
    (run_dir / "grid_manifest.json").write_text("{}", encoding="utf-8")
    if completed:
        (run_dir / "logRatio_dB.tif").write_bytes(b"marker")
    return run_dir


def _result(run: str, *, clusters: list[dict[str, object]] | None = None):
    clusters = clusters or []
    return {
        "schema": "icesat2_terrain_step_scan_v1",
        "status": (
            "spatially_supported_step_candidates_found"
            if clusters
            else "no_persistent_upward_steps"
        ),
        "run": run,
        "quality_segment_count": 100,
        "exact_segment_series_count": 25,
        "classification_counts": {"stable": 25},
        "raw_step_up_segment_count": len(clusters),
        "surviving_step_cluster_count": len(clusters),
        "surviving_step_clusters": clusters,
    }


def test_discovery_requires_grid_and_completed_marker(tmp_path: Path) -> None:
    completed = _make_run(tmp_path, "completed")
    _make_run(tmp_path, "grid_only", completed=False)
    no_grid = tmp_path / "no_grid"
    no_grid.mkdir()
    (no_grid / "logRatio_dB.tif").write_bytes(b"marker")

    selected, skipped = MODULE.discover_completed_runs(tmp_path)

    assert [item.run_dir for item in selected] == [completed]
    assert {item["reason"] for item in skipped} == {
        "no_completed_run_marker",
        "missing_grid_manifest",
    }


def test_include_grid_only_explicitly_includes_older_layout(tmp_path: Path) -> None:
    old = _make_run(tmp_path, "old", completed=False)

    selected, _ = MODULE.discover_completed_runs(
        tmp_path,
        include_grid_only=True,
    )

    assert [item.run_dir for item in selected] == [old]


def test_rank_candidates_prefers_cross_spot_then_support_and_low_spread() -> None:
    rows = [
        {
            "run": "a",
            "run_local_rank": 1,
            "cross_spot_supported": False,
            "segment_count": 10,
            "step_nmad_m": 0.02,
            "median_step_m": 1.0,
        },
        {
            "run": "b",
            "run_local_rank": 1,
            "cross_spot_supported": True,
            "segment_count": 4,
            "step_nmad_m": 0.10,
            "median_step_m": 0.5,
        },
        {
            "run": "c",
            "run_local_rank": 1,
            "cross_spot_supported": True,
            "segment_count": 7,
            "step_nmad_m": 0.20,
            "median_step_m": 0.6,
        },
    ]

    ranked = MODULE.rank_candidates(rows)

    assert [item["run"] for item in ranked] == ["c", "b", "a"]
    assert [item["global_rank"] for item in ranked] == [1, 2, 3]


def test_batch_continues_after_one_failed_run(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    _make_run(runs_dir, "bad")
    _make_run(runs_dir, "good")
    summary_path = runs_dir / "summary.json"

    def fake_audit(*, run_dir: Path, **_: object):
        if run_dir.name == "bad":
            raise RuntimeError("remote read failed")
        return _result(
            "good",
            clusters=[
                {
                    "centroid_longitude": 1.0,
                    "centroid_latitude": 2.0,
                    "event_start": "2021-01-01T00:00:00+00:00",
                    "event_end": "2022-01-01T00:00:00+00:00",
                    "median_step_m": 0.8,
                    "step_nmad_m": 0.05,
                    "segment_count": 4,
                    "cross_spot_supported": True,
                    "rgt": 1,
                    "spot": 5,
                    "pre_cycle": 1,
                    "post_cycle": 2,
                }
            ],
        )

    result = MODULE.scan_all_runs(
        runs_dir=runs_dir,
        summary_path=summary_path,
        start="2018-01-01T00:00:00Z",
        end="2026-01-01T00:00:00Z",
        include_grid_only=False,
        force=True,
        continue_on_error=True,
        audit_callable=fake_audit,
    )

    assert result["completed_run_count_scanned"] == 1
    assert result["failed_run_count"] == 1
    assert result["surviving_candidate_count"] == 1
    assert result["record_lookup_priority"][0]["run"] == "good"
    assert summary_path.is_file()
    assert (runs_dir / "good" / MODULE.RUN_RESULT_FILENAME).is_file()
    assert (runs_dir / "good" / MODULE.RUN_GEOJSON_FILENAME).is_file()


def test_valid_cached_result_avoids_live_query(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    run_dir = _make_run(runs_dir, "cached")
    cached = _result("cached")
    (run_dir / MODULE.RUN_RESULT_FILENAME).write_text(
        json.dumps(cached),
        encoding="utf-8",
    )

    def should_not_run(**_: object):
        raise AssertionError("live audit should not run")

    result = MODULE.scan_all_runs(
        runs_dir=runs_dir,
        summary_path=runs_dir / "summary.json",
        start="2018-01-01T00:00:00Z",
        end="2026-01-01T00:00:00Z",
        include_grid_only=False,
        force=False,
        continue_on_error=True,
        audit_callable=should_not_run,
    )

    assert result["failed_run_count"] == 0
    assert result["run_summaries"][0]["result_source"] == "cached"


def test_zero_candidates_means_no_record_lookup(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    _make_run(runs_dir, "one")

    result = MODULE.scan_all_runs(
        runs_dir=runs_dir,
        summary_path=runs_dir / "summary.json",
        start="2018-01-01T00:00:00Z",
        end="2026-01-01T00:00:00Z",
        include_grid_only=False,
        force=True,
        continue_on_error=True,
        audit_callable=lambda run_dir, **_: _result(run_dir.name),
    )

    assert result["status"] == "no_surviving_candidates_in_scanned_runs"
    assert result["record_lookup_priority"] == []
    assert result["interpretation"]["zero_candidates_means_no_record_lookup"] is True
