from __future__ import annotations

import json
from pathlib import Path

import pytest
from pyproj import Transformer

from app.config import Settings
from app.services.operator_tyrone_zone_depth_app import (
    CLASSIFIER_ONLY_WARNING,
    REVIEWED_PLOT_IDS,
    ROUTE_A_SOURCE,
    _build_candidate_payload,
    _classifier_only_warning_is_safe,
    _geometry_inside_run_bounds,
    run_operator_tyrone_zone_depth_app,
)
from app.services.roi_contract import ROI_CONTRACT_RELATIVE_PATH


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_tyrone_footprint(run_dir: Path) -> None:
    # Deliberately broad enough to contain all six reviewed Tyrone polygons.
    _write_json(
        run_dir / ROI_CONTRACT_RELATIVE_PATH,
        {
            "grid": {
                "crs": "EPSG:4326",
                "bounds_m": {
                    "xmin": -108.4220,
                    "ymin": 32.7190,
                    "xmax": -108.4160,
                    "ymax": 32.7240,
                },
            }
        },
    )


def _write_classifier_only_warning(run_dir: Path) -> None:
    _write_json(
        run_dir / "QA" / "run_quality" / "run_quality_summary.json",
        {
            "schema": "run_quality_summary_v1",
            "stage": "run_quality",
            "status": "WARNING",
            "is_usable": True,
            "blocking_reasons": [],
            "unknowns": [],
            "warnings": [CLASSIFIER_ONLY_WARNING],
            "checks": [
                {"name": "s2_indices", "status": "PASS", "present": True, "details": {}},
                {"name": "alignment_qa", "status": "PASS", "present": True, "details": {}},
                {
                    "name": "classifier",
                    "status": "WARNING",
                    "present": True,
                    "details": {"object_count": 0},
                },
            ],
        },
    )


def test_reviewed_plot_set_is_exactly_the_approved_six() -> None:
    assert REVIEWED_PLOT_IDS == ("TP1", "TP2", "TP3", "TP5", "TP6", "TP7")


def test_geometry_must_be_fully_inside_run_bounds() -> None:
    geometry = {
        "type": "Polygon",
        "coordinates": [[
            [-108.4190, 32.7210],
            [-108.4180, 32.7210],
            [-108.4180, 32.7220],
            [-108.4190, 32.7220],
            [-108.4190, 32.7210],
        ]],
    }
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:4326", always_xy=True)
    assert _geometry_inside_run_bounds(
        geometry,
        transformer=transformer,
        bounds={"xmin": -108.420, "ymin": 32.720, "xmax": -108.417, "ymax": 32.723},
    )
    assert not _geometry_inside_run_bounds(
        geometry,
        transformer=transformer,
        bounds={"xmin": -108.4185, "ymin": 32.720, "xmax": -108.417, "ymax": 32.723},
    )


def test_candidate_payload_comes_from_reviewed_zones_not_classifier(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_tyrone_footprint(run_dir)

    payload, matched_count = _build_candidate_payload(run_dir)

    assert matched_count == 6
    assert payload["source"] == ROUTE_A_SOURCE
    assert [candidate["zone_id"] for candidate in payload["candidates"]] == [
        "tyrone_tp1",
        "tyrone_tp2",
        "tyrone_tp3",
        "tyrone_tp5",
        "tyrone_tp6",
        "tyrone_tp7",
    ]
    assert not (run_dir / "classifier" / "classifications.csv").exists()


def test_exact_classifier_zero_warning_is_safe_but_other_warning_is_not(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_classifier_only_warning(run_dir)
    assert _classifier_only_warning_is_safe(run_dir)

    payload = json.loads(
        (run_dir / "QA" / "run_quality" / "run_quality_summary.json").read_text(encoding="utf-8")
    )
    payload["warnings"] = ["different_warning"]
    _write_json(run_dir / "QA" / "run_quality" / "run_quality_summary.json", payload)
    assert not _classifier_only_warning_is_safe(run_dir)


def test_route_a_end_to_end_works_with_zero_classifier_objects(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path, database_path=tmp_path / "app.db")
    run_id = "route-a-test"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    _write_tyrone_footprint(run_dir)
    _write_classifier_only_warning(run_dir)

    # This is the decisive regression: there is intentionally no classifier CSV.
    assert not (run_dir / "classifier" / "classifications.csv").exists()

    result = run_operator_tyrone_zone_depth_app(
        settings=settings,
        run_id=run_id,
        operator_confirmed_review=True,
    )

    assert result["status"] == "calibrated_range"
    assert result["candidate_count"] == 6
    assert result["spatial_match_count"] == 6
    assert result["estimated_count"] == 6
    assert result["not_available_count"] == 0
    assert result["insufficient_data_count"] == 0
    assert result["run_quality_status"] == "WARNING"
    assert result["validation_status"] == "provisional"
    assert result["method_kind"] == "operator_zone_lookup_v1"
    assert result["classifier_used"] is False
    assert "classifier_only_warning_irrelevant_to_route_a" in result["warnings"]

    by_zone = {row["zone_id"]: row for row in result["estimates"]}
    assert set(by_zone) == {
        "tyrone_tp1",
        "tyrone_tp2",
        "tyrone_tp3",
        "tyrone_tp5",
        "tyrone_tp6",
        "tyrone_tp7",
    }
    tp6 = by_zone["tyrone_tp6"]
    assert tp6["depth_status"] == "calibrated_range"
    assert tp6["estimated_depth_min_m"] == pytest.approx(0.85090)
    assert tp6["estimated_depth_best_m"] == pytest.approx(0.94996)
    assert tp6["estimated_depth_max_m"] == pytest.approx(1.04902)
    assert tp6["depth_quality"] == "provisional_local"
    assert "run_quality_warning_allowed_by_package" in tp6["warnings"]

    candidate_payload = json.loads(
        (run_dir / "depth_inputs" / "candidates.json").read_text(encoding="utf-8")
    )
    assert candidate_payload["source"] == ROUTE_A_SOURCE
    assert (run_dir / "depth" / "depth_estimates.csv").is_file()
    assert (run_dir / "depth" / "depth_summary.json").is_file()
    assert (run_dir / "depth" / "depth_method_manifest.json").is_file()


def test_other_run_quality_warning_still_blocks_metres(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path, database_path=tmp_path / "app.db")
    run_id = "blocked-route-a-test"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    _write_tyrone_footprint(run_dir)
    _write_json(
        run_dir / "QA" / "run_quality" / "run_quality_summary.json",
        {
            "schema": "run_quality_summary_v1",
            "stage": "run_quality",
            "status": "WARNING",
            "is_usable": True,
            "blocking_reasons": [],
            "unknowns": [],
            "warnings": ["different_warning"],
            "checks": [
                {"name": "s2_indices", "status": "WARNING", "present": True, "details": {}},
                {"name": "classifier", "status": "PASS", "present": True, "details": {"object_count": 4}},
            ],
        },
    )

    result = run_operator_tyrone_zone_depth_app(
        settings=settings,
        run_id=run_id,
        operator_confirmed_review=True,
    )

    assert result["candidate_count"] == 6
    assert result["estimated_count"] == 0
    assert result["insufficient_data_count"] == 6
    assert all(row["estimated_depth_best_m"] is None for row in result["estimates"])
