from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts.build_tyrone_local_depth_package import build_tyrone_local_depth_package
from scripts.run_local_depth_for_existing_run import run_local_depth_for_existing_run


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_run_quality(run_dir: Path, *, status: str = "PASS", is_usable: bool = True) -> None:
    _write_json(
        run_dir / "QA" / "run_quality" / "run_quality_summary.json",
        {
            "schema": "run_quality_summary_v1",
            "stage": "run_quality",
            "status": status,
            "is_usable": is_usable,
        },
    )


def _write_candidates(path: Path) -> None:
    _write_json(
        path,
        {
            "schema_version": "local_depth_candidates_v1",
            "candidates": [
                {"candidate_id": "reviewed-local-plot-5", "zone_id": "tyrone_tp5"},
                {"candidate_id": "reviewed-local-plot-6", "zone_id": "tyrone_tp6"},
            ],
        },
    )


def test_existing_run_command_writes_two_private_ranges(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    package_dir = tmp_path / "private-package"
    candidate_input = tmp_path / "reviewed-candidates.json"
    build_tyrone_local_depth_package(package_dir)
    _write_run_quality(run_dir)
    _write_candidates(candidate_input)

    result = run_local_depth_for_existing_run(
        run_dir=run_dir,
        package_dir=package_dir,
        candidate_input=candidate_input,
    )

    assert result["status"] == "calibrated_range"
    assert result["candidate_count"] == 2
    assert result["estimated_count"] == 2
    assert result["run_quality_status"] == "PASS"
    assert result["outputs"] == [
        "depth/depth_estimates.csv",
        "depth/depth_summary.json",
        "depth/depth_method_manifest.json",
    ]

    with (run_dir / "depth" / "depth_estimates.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert [row["estimated_depth_best_m"] for row in rows] == ["0.680720", "0.949960"]
    assert all(row["depth_status"] == "calibrated_range" for row in rows)
    assert all("not_global_model" in row["warnings"] for row in rows)

    copied = json.loads(
        (run_dir / "depth_inputs" / "candidates.json").read_text(encoding="utf-8")
    )
    assert copied["candidates"][0] == {
        "candidate_id": "reviewed-local-plot-5",
        "zone_id": "tyrone_tp5",
    }


def test_existing_run_command_abstains_when_run_quality_is_blocked(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    package_dir = tmp_path / "private-package"
    candidate_input = tmp_path / "reviewed-candidates.json"
    build_tyrone_local_depth_package(package_dir)
    _write_run_quality(run_dir, status="BLOCKED", is_usable=False)
    _write_candidates(candidate_input)

    result = run_local_depth_for_existing_run(
        run_dir=run_dir,
        package_dir=package_dir,
        candidate_input=candidate_input,
    )

    assert result["status"] == "insufficient_data"
    assert result["estimated_count"] == 0
    assert result["insufficient_data_count"] == 2

    with (run_dir / "depth" / "depth_estimates.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert all(row["estimated_depth_best_m"] == "" for row in rows)


def test_existing_run_command_protects_reviewed_input_without_force(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    package_dir = tmp_path / "private-package"
    candidate_input = tmp_path / "reviewed-candidates.json"
    build_tyrone_local_depth_package(package_dir)
    _write_run_quality(run_dir)
    _write_candidates(candidate_input)

    run_local_depth_for_existing_run(
        run_dir=run_dir,
        package_dir=package_dir,
        candidate_input=candidate_input,
    )

    with pytest.raises(FileExistsError, match="already has"):
        run_local_depth_for_existing_run(
            run_dir=run_dir,
            package_dir=package_dir,
            candidate_input=candidate_input,
        )

    result = run_local_depth_for_existing_run(
        run_dir=run_dir,
        package_dir=package_dir,
        candidate_input=candidate_input,
        force=True,
    )
    assert result["estimated_count"] == 2


def test_existing_run_command_rejects_duplicate_candidate_ids(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    package_dir = tmp_path / "private-package"
    candidate_input = tmp_path / "bad-candidates.json"
    build_tyrone_local_depth_package(package_dir)
    _write_run_quality(run_dir)
    _write_json(
        candidate_input,
        {
            "schema_version": "local_depth_candidates_v1",
            "candidates": [
                {"candidate_id": "duplicate", "zone_id": "tyrone_tp5"},
                {"candidate_id": "duplicate", "zone_id": "tyrone_tp6"},
            ],
        },
    )

    with pytest.raises(ValueError, match="duplicate candidate_id"):
        run_local_depth_for_existing_run(
            run_dir=run_dir,
            package_dir=package_dir,
            candidate_input=candidate_input,
        )

    assert not (run_dir / "depth_inputs" / "candidates.json").exists()
    assert not (run_dir / "depth").exists()
