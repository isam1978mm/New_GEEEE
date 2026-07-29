from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from app.pipeline.depth.package import load_local_depth_package
from app.pipeline.stages.depth_estimation import write_depth_outputs
from scripts.build_tyrone_local_depth_package import build_tyrone_local_depth_package


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def test_builder_creates_loadable_private_package_and_two_ranges(tmp_path: Path) -> None:
    package_dir = tmp_path / "private" / "tyrone-depth"
    result = build_tyrone_local_depth_package(package_dir)
    package = load_local_depth_package(package_dir)

    assert result["zone_count"] == 2
    assert package.method_version == "tyrone-local-beta-v1"
    assert package.validation_status == "provisional"
    assert package.zone("tyrone_tp5").depth_range.best_m == pytest.approx(0.68072)
    assert package.zone("tyrone_tp6").depth_range.best_m == pytest.approx(0.94996)

    manifest_text = (package_dir / "depth_method_manifest.json").read_text(encoding="utf-8")
    assert "coordinate" not in manifest_text.casefold()
    assert "polygon" not in manifest_text.casefold()
    assert "private source" not in manifest_text.casefold()

    run_dir = tmp_path / "run"
    _write_json(
        run_dir / "QA" / "run_quality" / "run_quality_summary.json",
        {
            "schema": "run_quality_summary_v1",
            "stage": "run_quality",
            "status": "PASS",
            "is_usable": True,
        },
    )
    _write_json(
        run_dir / "depth_inputs" / "candidates.json",
        {
            "schema_version": "local_depth_candidates_v1",
            "candidates": [
                {"candidate_id": "local-plot-5", "zone_id": "tyrone_tp5"},
                {"candidate_id": "local-plot-6", "zone_id": "tyrone_tp6"},
            ],
        },
    )

    paths, summary = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    with paths.estimates_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert summary["status"] == "calibrated_range"
    assert summary["estimated_count"] == 2
    assert [row["estimated_depth_best_m"] for row in rows] == ["0.680720", "0.949960"]
    assert all(row["depth_quality"] == "provisional_local" for row in rows)
    assert all("not_transferable" in row["warnings"] for row in rows)


def test_builder_refuses_nonempty_directory_without_force(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    (package_dir / "unrelated.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="not empty"):
        build_tyrone_local_depth_package(package_dir)

    result = build_tyrone_local_depth_package(package_dir, force=True)
    assert result["status"] == "created"
    assert (package_dir / "unrelated.txt").read_text(encoding="utf-8") == "keep"
