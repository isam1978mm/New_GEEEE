from __future__ import annotations

import asyncio
import csv
import hashlib
import json
from pathlib import Path

import pytest

from app.config import Settings
from app.db.models.enums import ArtifactClass
from app.pipeline._base import StageContext
from app.pipeline.depth.package import LocalDepthPackageError, load_local_depth_package
from app.pipeline.stages.depth_estimation import DepthEstimationStage, write_depth_outputs


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


def _write_candidates(run_dir: Path, candidates: list[dict[str, str]]) -> None:
    _write_json(
        run_dir / "depth_inputs" / "candidates.json",
        {
            "schema_version": "local_depth_candidates_v1",
            "candidates": candidates,
        },
    )


def _write_package(package_dir: Path) -> Path:
    package_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "local_depth_package_v1",
        "method_kind": "operator_zone_lookup_v1",
        "method_version": "tyrone-local-beta-v1",
        "calibration_dataset_version": "tyrone-3x-2026-07-29",
        "site_id": "tyrone_3x",
        "validation_status": "provisional",
        "allow_run_quality_warning": False,
        "warnings": ["provisional_geometry"],
        "zones": [
            {
                "zone_id": "tyrone_tp5",
                "depth_min_m": 0.65532,
                "depth_best_m": 0.68072,
                "depth_max_m": 0.70612,
                "warnings": ["measured_anchor"],
            },
            {
                "zone_id": "tyrone_tp6",
                "depth_min_m": 0.8509,
                "depth_best_m": 0.94996,
                "depth_max_m": 1.04902,
                "warnings": ["measured_anchor"],
            },
        ],
    }
    manifest_path = package_dir / "depth_method_manifest.json"
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True)
    manifest_path.write_text(manifest_text, encoding="utf-8")
    digest = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()
    (package_dir / "checksums.sha256").write_text(
        f"{digest}  depth_method_manifest.json\n",
        encoding="utf-8",
    )
    return package_dir


def _read_first_csv_row(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return next(csv.DictReader(handle))


def test_depth_stage_is_disabled_without_outputs_by_default(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    settings = Settings(
        data_dir=tmp_path,
        database_path=tmp_path / "app.db",
        local_depth_mode="off",
    )
    result = asyncio.run(
        DepthEstimationStage().run(
            StageContext(run_id="run-1", settings=settings, run_dir=run_dir)
        )
    )

    assert result.artifacts == []
    assert result.metadata["status"] == "not_available"
    assert not (run_dir / "depth").exists()


def test_local_supported_zone_writes_provisional_metre_range(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    package_dir = _write_package(tmp_path / "package")
    _write_run_quality(run_dir)
    _write_candidates(
        run_dir,
        [{"candidate_id": "candidate-1", "zone_id": "tyrone_tp5"}],
    )

    paths, summary = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    row = _read_first_csv_row(paths.estimates_csv)
    method_manifest = json.loads(paths.method_manifest_json.read_text(encoding="utf-8"))

    assert summary["status"] == "calibrated_range"
    assert summary["estimated_count"] == 1
    assert row["depth_status"] == "calibrated_range"
    assert row["estimated_depth_min_m"] == "0.655320"
    assert row["estimated_depth_best_m"] == "0.680720"
    assert row["estimated_depth_max_m"] == "0.706120"
    assert row["depth_quality"] == "provisional_local"
    assert "not_transferable" in row["warnings"]
    assert method_manifest["site_id"] == "tyrone_3x"
    assert "root" not in method_manifest


def test_candidate_outside_package_support_has_no_metre_values(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    package_dir = _write_package(tmp_path / "package")
    _write_run_quality(run_dir)
    _write_candidates(
        run_dir,
        [{"candidate_id": "candidate-2", "zone_id": "unknown-zone"}],
    )

    paths, summary = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    row = _read_first_csv_row(paths.estimates_csv)

    assert summary["status"] == "insufficient_data"
    assert summary["estimated_count"] == 0
    assert row["depth_status"] == "insufficient_data"
    assert row["estimated_depth_min_m"] == ""
    assert row["estimated_depth_best_m"] == ""
    assert row["estimated_depth_max_m"] == ""
    assert "candidate_outside_local_calibration_support" in row["warnings"]


def test_blocked_run_quality_has_no_metre_values(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    package_dir = _write_package(tmp_path / "package")
    _write_run_quality(run_dir, status="BLOCKED", is_usable=False)
    _write_candidates(
        run_dir,
        [{"candidate_id": "candidate-3", "zone_id": "tyrone_tp6"}],
    )

    paths, summary = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    row = _read_first_csv_row(paths.estimates_csv)

    assert summary["status"] == "insufficient_data"
    assert summary["run_quality_status"] == "BLOCKED"
    assert row["depth_status"] == "insufficient_data"
    assert row["estimated_depth_best_m"] == ""
    assert "run_quality_not_supported" in row["warnings"]


def test_package_checksum_mismatch_is_rejected(tmp_path: Path) -> None:
    package_dir = _write_package(tmp_path / "package")
    manifest_path = package_dir / "depth_method_manifest.json"
    manifest_path.write_text(manifest_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(LocalDepthPackageError, match="checksum mismatch"):
        load_local_depth_package(package_dir)


def test_enabled_stage_outputs_private_non_http_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    package_dir = _write_package(tmp_path / "package")
    _write_run_quality(run_dir)
    _write_candidates(
        run_dir,
        [{"candidate_id": "candidate-4", "zone_id": "tyrone_tp6"}],
    )
    settings = Settings(
        data_dir=tmp_path,
        database_path=tmp_path / "app.db",
        local_depth_mode="local_calibrated",
        local_depth_package_dir=package_dir,
    )

    result = asyncio.run(
        DepthEstimationStage().run(
            StageContext(run_id="run-2", settings=settings, run_dir=run_dir)
        )
    )

    assert result.metadata["status"] == "calibrated_range"
    assert len(result.artifacts) == 3
    assert all(artifact.artifact_class is ArtifactClass.FILESYSTEM_ONLY for artifact in result.artifacts)
    assert all(artifact.http_servable is False for artifact in result.artifacts)
