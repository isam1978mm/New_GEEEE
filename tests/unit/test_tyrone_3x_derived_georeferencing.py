from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "audit_tyrone_3x_derived_georeferencing.py"
SPEC = importlib.util.spec_from_file_location(
    "audit_tyrone_3x_derived_georeferencing", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _point(point_id: str, role: str, x: float, y: float, *, error_x=0.0, error_y=0.0):
    # Exact affine transform used by the fixture:
    # target_x = 2*x + 0.5*y + 500000
    # target_y = -0.25*x + 3*y + 3600000
    return {
        "point_id": point_id,
        "role": role,
        "drawing_x": x,
        "drawing_y": y,
        "target_x_m": 2.0 * x + 0.5 * y + 500000.0 + error_x,
        "target_y_m": -0.25 * x + 3.0 * y + 3600000.0 + error_y,
    }


def _payload(*, bad_checks: bool = False):
    fit_xy = [(0, 0), (100, 0), (0, 100), (100, 100), (50, 20), (20, 70)]
    check_xy = [(80, 40), (30, 90)]
    points = [
        _point(f"fit_{index}", "fit", x, y)
        for index, (x, y) in enumerate(fit_xy, start=1)
    ]
    for index, (x, y) in enumerate(check_xy, start=1):
        points.append(
            _point(
                f"check_{index}",
                "check",
                x,
                y,
                error_x=20.0 if bad_checks else 1.0,
                error_y=20.0 if bad_checks else -1.0,
            )
        )
    return {
        "schema": "tyrone_3x_georeference_control_points_v1",
        "target_crs": "EPSG:32612",
        "points": points,
    }


def test_low_independent_checkpoint_error_is_feasible_but_never_unlocks_depth():
    result = MODULE.build_audit(_payload())

    assert result["status"] == "derived_georeferencing_feasible_for_manual_review"
    assert result["fit_point_count"] == 6
    assert result["check_point_count"] == 2
    assert result["check_residual_summary"]["rmse_m"] < 5.0
    assert result["decision"]["derived_geometry_feasible_for_manual_review"] is True
    assert result["decision"]["official_survey_geometry_recovered"] is False
    assert result["decision"]["plot_specific_stability_proven"] is False
    assert result["decision"]["earth_engine_query_allowed"] is False
    assert result["decision"]["calibration_record_allowed"] is False
    assert result["decision"]["numerical_depth_ready"] is False


def test_large_independent_checkpoint_error_rejects_georeference():
    result = MODULE.build_audit(_payload(bad_checks=True))

    assert result["status"] == "derived_georeferencing_rejected"
    assert result["decision"]["derived_geometry_feasible_for_manual_review"] is False
    assert result["check_residual_summary"]["maximum_m"] > 7.5


def test_requires_six_fit_points():
    payload = _payload()
    payload["points"] = [
        point
        for point in payload["points"]
        if point["point_id"] != "fit_6"
    ]

    with pytest.raises(ValueError, match="at least 6 fit points"):
        MODULE.build_audit(payload)


def test_requires_two_independent_check_points():
    payload = _payload()
    payload["points"] = [
        point
        for point in payload["points"]
        if point["point_id"] != "check_2"
    ]

    with pytest.raises(ValueError, match="at least 2 independent check points"):
        MODULE.build_audit(payload)


def test_rejects_collinear_fit_points():
    points = [
        _point(f"fit_{index}", "fit", float(index), float(index))
        for index in range(6)
    ]
    points.extend(
        [
            _point("check_1", "check", 10.0, 10.0),
            _point("check_2", "check", 11.0, 11.0),
        ]
    )
    payload = {
        "schema": "tyrone_3x_georeference_control_points_v1",
        "target_crs": "EPSG:32612",
        "points": points,
    }

    with pytest.raises(ValueError, match="rank deficient"):
        MODULE.build_audit(payload)
