from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from app.config import Settings
from app.services.operator_tyrone_zone_depth_app import (
    OUTSIDE_ZONE_ID,
    REVIEWED_PLOT_IDS,
    ROUTE_A_SOURCE,
    _assign_zone,
    _candidate_rectangle,
    _rectangle_fully_inside_ring,
    run_operator_tyrone_zone_depth_app,
)
from app.services.roi_contract import ROI_CONTRACT_RELATIVE_PATH


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _square(xmin: float, ymin: float, xmax: float, ymax: float) -> list[tuple[float, float]]:
    return [
        (xmin, ymin),
        (xmax, ymin),
        (xmax, ymax),
        (xmin, ymax),
        (xmin, ymin),
    ]


def test_reviewed_plot_set_is_exactly_the_approved_six() -> None:
    assert REVIEWED_PLOT_IDS == ("TP1", "TP2", "TP3", "TP5", "TP6", "TP7")


def test_candidate_rectangle_uses_full_pixel_bbox_edges() -> None:
    row = {
        "object_id": "7",
        "row_min": "2",
        "row_max": "3",
        "col_min": "4",
        "col_max": "5",
    }
    transform = [10.0, 0.0, 100.0, 0.0, -10.0, 200.0]
    assert _candidate_rectangle(row, transform) == pytest.approx((140.0, 160.0, 160.0, 180.0))


def test_rectangle_containment_is_conservative() -> None:
    square = _square(0.0, 0.0, 10.0, 10.0)
    assert _rectangle_fully_inside_ring((2.0, 2.0, 4.0, 4.0), square)
    assert not _rectangle_fully_inside_ring((0.0, 2.0, 2.0, 4.0), square)
    assert not _rectangle_fully_inside_ring((9.0, 9.0, 11.0, 11.0), square)

    concave = [
        (0.0, 0.0),
        (10.0, 0.0),
        (10.0, 10.0),
        (6.0, 10.0),
        (6.0, 4.0),
        (4.0, 4.0),
        (4.0, 10.0),
        (0.0, 10.0),
        (0.0, 0.0),
    ]
    assert not _rectangle_fully_inside_ring((3.0, 3.0, 7.0, 7.0), concave)


def test_assign_zone_requires_exactly_one_full_containment() -> None:
    rings = {
        "TP1": _square(0, 0, 10, 10),
        "TP2": _square(20, 0, 30, 10),
        "TP3": _square(40, 0, 50, 10),
        "TP5": _square(60, 0, 70, 10),
        "TP6": _square(80, 0, 90, 10),
        "TP7": _square(100, 0, 110, 10),
    }
    assert _assign_zone((82, 2, 84, 4), rings) == "tyrone_tp6"
    assert _assign_zone((12, 2, 14, 4), rings) == OUTSIDE_ZONE_ID

    ambiguous = dict(rings)
    ambiguous["TP5"] = _square(80, 0, 90, 10)
    assert _assign_zone((82, 2, 84, 4), ambiguous) == OUTSIDE_ZONE_ID


def test_route_a_end_to_end_assigns_tp6_and_abstains_outside(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path, database_path=tmp_path / "app.db")
    run_id = "route-a-test"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)

    # Match the real run contract: UTM Zone 12N with 10 m north-up pixels.
    # Pixel (0, 0) is centered safely inside the reviewed TP6 polygon.
    _write_json(
        run_dir / ROI_CONTRACT_RELATIVE_PATH,
        {
            "grid": {
                "crs": "EPSG:32612",
                "crs_transform": [10.0, 0.0, 741958.2482431115, 0.0, -10.0, 3623404.398004249],
            }
        },
    )
    _write_json(
        run_dir / "QA" / "run_quality" / "run_quality_summary.json",
        {
            "schema": "run_quality_summary_v1",
            "stage": "run_quality",
            "status": "PASS",
            "is_usable": True,
        },
    )

    classifier_path = run_dir / "classifier" / "classifications.csv"
    classifier_path.parent.mkdir(parents=True)
    with classifier_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["object_id", "row_min", "row_max", "col_min", "col_max"],
        )
        writer.writeheader()
        writer.writerow({"object_id": 1, "row_min": 0, "row_max": 0, "col_min": 0, "col_max": 0})
        writer.writerow({"object_id": 2, "row_min": 0, "row_max": 0, "col_min": 500, "col_max": 500})

    result = run_operator_tyrone_zone_depth_app(
        settings=settings,
        run_id=run_id,
        operator_confirmed_review=True,
    )

    assert result["status"] == "calibrated_range"
    assert result["candidate_count"] == 2
    assert result["spatial_match_count"] == 1
    assert result["estimated_count"] == 1
    assert result["not_available_count"] == 1
    assert result["validation_status"] == "provisional"
    assert result["method_kind"] == "operator_zone_lookup_v1"

    by_id = {row["candidate_id"]: row for row in result["estimates"]}
    tp6 = by_id["object-1"]
    assert tp6["zone_id"] == "tyrone_tp6"
    assert tp6["depth_status"] == "calibrated_range"
    assert tp6["estimated_depth_min_m"] == pytest.approx(0.85090)
    assert tp6["estimated_depth_best_m"] == pytest.approx(0.94996)
    assert tp6["estimated_depth_max_m"] == pytest.approx(1.04902)
    assert tp6["depth_quality"] == "provisional_local"

    outside = by_id["object-2"]
    assert outside["zone_id"] == OUTSIDE_ZONE_ID
    assert outside["depth_status"] == "not_available"
    assert outside["estimated_depth_best_m"] is None

    candidate_payload = json.loads(
        (run_dir / "depth_inputs" / "candidates.json").read_text(encoding="utf-8")
    )
    assert candidate_payload["source"] == ROUTE_A_SOURCE
    assert (run_dir / "depth" / "depth_estimates.csv").is_file()
    assert (run_dir / "depth" / "depth_summary.json").is_file()
    assert (run_dir / "depth" / "depth_method_manifest.json").is_file()
