from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from app.pipeline.depth.interpolation import (
    OPERATOR_CANDIDATES_SCHEMA,
    OperatorDepthPackageError,
    load_operator_interpolation_package,
)
from app.pipeline.stages.depth_estimation import write_depth_outputs
from scripts.build_operator_local_depth_package import build_operator_local_depth_package
from scripts.run_operator_local_depth_for_existing_run import (
    run_operator_depth_for_existing_run,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _config(*, nonmonotonic: bool = False) -> dict:
    second_min = 0.4 if nonmonotonic else 1.4
    second_best = 0.5 if nonmonotonic else 1.5
    second_max = 0.6 if nonmonotonic else 1.6
    return {
        "method_version": "operator-local-beta-v1",
        "calibration_dataset_version": "operator-test-v1",
        "site_id": "local_test_site",
        "validation_status": "provisional",
        "signal_name": "vv_minus_vh_db",
        "signal_units": "dB",
        "default_signal_uncertainty": 0.0,
        "warnings": ["operator_review_required"],
        "anchors": [
            {
                "anchor_id": "shallow",
                "signal_value": 1.0,
                "depth_min_m": 0.4,
                "depth_best_m": 0.5,
                "depth_max_m": 0.6,
            },
            {
                "anchor_id": "deep",
                "signal_value": 3.0,
                "depth_min_m": second_min,
                "depth_best_m": second_best,
                "depth_max_m": second_max,
            },
        ],
    }


def _build_package(tmp_path: Path, *, nonmonotonic: bool = False) -> Path:
    config_path = tmp_path / "operator_config.json"
    _write_json(config_path, _config(nonmonotonic=nonmonotonic))
    package_dir = tmp_path / "operator_package"
    build_operator_local_depth_package(
        config_path=config_path,
        output_dir=package_dir,
    )
    return package_dir


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


def _write_candidates(path: Path, candidates: list[dict]) -> None:
    _write_json(
        path,
        {
            "schema_version": OPERATOR_CANDIDATES_SCHEMA,
            "candidates": candidates,
        },
    )


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_operator_midpoint_interpolates_local_metre_range(tmp_path: Path) -> None:
    package_dir = _build_package(tmp_path)
    run_dir = tmp_path / "run"
    _write_run_quality(run_dir)
    _write_candidates(
        run_dir / "depth_inputs" / "candidates.json",
        [
            {
                "candidate_id": "candidate-mid",
                "signal_name": "vv_minus_vh_db",
                "signal_value": 2.0,
                "signal_uncertainty": 0.0,
            }
        ],
    )

    paths, summary = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    row = _read_rows(paths.estimates_csv)[0]

    assert summary["status"] == "calibrated_range"
    assert summary["method_kind"] == "operator_scalar_interpolation_v1"
    assert summary["candidate_schema_version"] == OPERATOR_CANDIDATES_SCHEMA
    assert row["estimated_depth_min_m"] == "0.900000"
    assert row["estimated_depth_best_m"] == "1.000000"
    assert row["estimated_depth_max_m"] == "1.100000"
    assert row["zone_id"] == "interval:shallow:deep"
    assert "no_extrapolation" in row["warnings"]


def test_candidate_signal_uncertainty_widens_range(tmp_path: Path) -> None:
    package_dir = _build_package(tmp_path)
    run_dir = tmp_path / "run"
    _write_run_quality(run_dir)
    _write_candidates(
        run_dir / "depth_inputs" / "candidates.json",
        [
            {
                "candidate_id": "candidate-uncertain",
                "signal_name": "vv_minus_vh_db",
                "signal_value": 2.0,
                "signal_uncertainty": 0.2,
            }
        ],
    )

    paths, _ = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    row = _read_rows(paths.estimates_csv)[0]

    assert row["estimated_depth_min_m"] == "0.800000"
    assert row["estimated_depth_best_m"] == "1.000000"
    assert row["estimated_depth_max_m"] == "1.200000"
    assert "signal_uncertainty_applied" in row["warnings"]


def test_operator_interpolation_abstains_outside_signal_support(tmp_path: Path) -> None:
    package_dir = _build_package(tmp_path)
    run_dir = tmp_path / "run"
    _write_run_quality(run_dir)
    _write_candidates(
        run_dir / "depth_inputs" / "candidates.json",
        [
            {
                "candidate_id": "outside",
                "signal_name": "vv_minus_vh_db",
                "signal_value": 0.5,
                "signal_uncertainty": 0.0,
            }
        ],
    )

    paths, summary = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    row = _read_rows(paths.estimates_csv)[0]

    assert summary["status"] == "insufficient_data"
    assert row["estimated_depth_best_m"] == ""
    assert "candidate_outside_local_calibration_signal_support" in row["warnings"]


def test_operator_interpolation_rejects_signal_name_mismatch(tmp_path: Path) -> None:
    package_dir = _build_package(tmp_path)
    run_dir = tmp_path / "run"
    _write_run_quality(run_dir)
    _write_candidates(
        run_dir / "depth_inputs" / "candidates.json",
        [
            {
                "candidate_id": "wrong-signal",
                "signal_name": "different_signal",
                "signal_value": 2.0,
            }
        ],
    )

    paths, _ = write_depth_outputs(run_dir=run_dir, package_dir=package_dir)
    row = _read_rows(paths.estimates_csv)[0]
    assert row["depth_status"] == "insufficient_data"
    assert "candidate_signal_name_mismatch" in row["warnings"]


def test_nonmonotonic_anchor_depths_are_rejected(tmp_path: Path) -> None:
    config_path = tmp_path / "bad_config.json"
    _write_json(config_path, _config(nonmonotonic=True))
    package_dir = tmp_path / "bad_package"

    with pytest.raises(OperatorDepthPackageError, match="strictly monotonic"):
        build_operator_local_depth_package(
            config_path=config_path,
            output_dir=package_dir,
        )


def test_operator_existing_run_command_is_end_to_end(tmp_path: Path) -> None:
    package_dir = _build_package(tmp_path)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_run_quality(run_dir)
    candidates_path = tmp_path / "operator_candidates.json"
    _write_candidates(
        candidates_path,
        [
            {
                "candidate_id": "candidate-mid",
                "signal_name": "vv_minus_vh_db",
                "signal_value": 2.0,
                "signal_uncertainty": 0.1,
            }
        ],
    )

    result = run_operator_depth_for_existing_run(
        run_dir=run_dir,
        package_dir=package_dir,
        candidate_input=candidates_path,
    )

    assert result["status"] == "calibrated_range"
    assert result["estimated_count"] == 1
    assert result["method_kind"] == "operator_scalar_interpolation_v1"
    copied = json.loads(
        (run_dir / "depth_inputs" / "candidates.json").read_text(encoding="utf-8")
    )
    assert copied["schema_version"] == OPERATOR_CANDIDATES_SCHEMA
    assert copied["candidates"][0]["signal_uncertainty"] == 0.1


def test_operator_package_checksum_is_enforced(tmp_path: Path) -> None:
    package_dir = _build_package(tmp_path)
    manifest_path = package_dir / "depth_method_manifest.json"
    manifest_path.write_text(manifest_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(OperatorDepthPackageError, match="checksum mismatch"):
        load_operator_interpolation_package(package_dir)
