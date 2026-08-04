"""Evaluate a research-only affine georeference for Tyrone 3X drawings.

This tool fits a 2D affine transformation from drawing coordinates to a
projected map coordinate system using designated fit points, then evaluates the
transformation on independent check points.  It is deliberately conservative:
it does not digitize plot polygons, create calibration rows, invoke Earth
Engine, or enable numerical depth.

Input JSON schema::

    {
      "schema": "tyrone_3x_georeference_control_points_v1",
      "target_crs": "EPSG:32612",
      "points": [
        {
          "point_id": "control_01",
          "role": "fit",
          "drawing_x": 123.4,
          "drawing_y": 456.7,
          "target_x_m": 765432.1,
          "target_y_m": 3623456.7
        }
      ]
    }

Drawing coordinates may be pixels or another internally consistent planar
coordinate system. Target coordinates must be projected metres in one stated
CRS. At least six well-distributed fit points and two independent check points
are required.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

SCHEMA = "tyrone_3x_georeference_audit_v1"
INPUT_SCHEMA = "tyrone_3x_georeference_control_points_v1"


def _load_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read control points: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("control-point input must be a JSON object")
    return payload


def _finite_number(value: object, name: str) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _normalized_points(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError("control-point schema is not supported")
    target_crs = payload.get("target_crs")
    if not isinstance(target_crs, str) or not target_crs.strip():
        raise ValueError("target_crs is required")
    if not target_crs.upper().startswith("EPSG:"):
        raise ValueError("target_crs must be an explicit projected EPSG code")

    raw_points = payload.get("points")
    if not isinstance(raw_points, list):
        raise ValueError("points must be a list")

    points: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_points, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"point {index} must be an object")
        point_id = raw.get("point_id")
        if not isinstance(point_id, str) or not point_id.strip():
            raise ValueError(f"point {index} has no point_id")
        if point_id in seen:
            raise ValueError(f"duplicate point_id: {point_id}")
        seen.add(point_id)
        role = raw.get("role")
        if role not in {"fit", "check"}:
            raise ValueError(f"{point_id}.role must be fit or check")
        points.append(
            {
                "point_id": point_id,
                "role": role,
                "drawing_x": _finite_number(raw.get("drawing_x"), f"{point_id}.drawing_x"),
                "drawing_y": _finite_number(raw.get("drawing_y"), f"{point_id}.drawing_y"),
                "target_x_m": _finite_number(raw.get("target_x_m"), f"{point_id}.target_x_m"),
                "target_y_m": _finite_number(raw.get("target_y_m"), f"{point_id}.target_y_m"),
            }
        )
    return points


def _design_matrix(points: list[dict[str, Any]]) -> np.ndarray:
    return np.asarray(
        [[point["drawing_x"], point["drawing_y"], 1.0] for point in points],
        dtype=np.float64,
    )


def _target_matrix(points: list[dict[str, Any]]) -> np.ndarray:
    return np.asarray(
        [[point["target_x_m"], point["target_y_m"]] for point in points],
        dtype=np.float64,
    )


def _residual_rows(
    points: list[dict[str, Any]],
    coefficients: np.ndarray,
) -> list[dict[str, Any]]:
    predicted = _design_matrix(points) @ coefficients
    rows: list[dict[str, Any]] = []
    for point, estimate in zip(points, predicted, strict=True):
        dx = float(estimate[0] - point["target_x_m"])
        dy = float(estimate[1] - point["target_y_m"])
        rows.append(
            {
                "point_id": point["point_id"],
                "role": point["role"],
                "predicted_x_m": float(estimate[0]),
                "predicted_y_m": float(estimate[1]),
                "residual_x_m": dx,
                "residual_y_m": dy,
                "residual_distance_m": float(math.hypot(dx, dy)),
            }
        )
    return rows


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    distances = np.asarray(
        [float(row["residual_distance_m"]) for row in rows], dtype=np.float64
    )
    return {
        "point_count": len(rows),
        "rmse_m": float(math.sqrt(float(np.mean(distances**2)))) if len(rows) else None,
        "median_m": float(np.median(distances)) if len(rows) else None,
        "maximum_m": float(np.max(distances)) if len(rows) else None,
    }


def _drawing_spread(points: list[dict[str, Any]]) -> dict[str, float]:
    xs = np.asarray([float(point["drawing_x"]) for point in points], dtype=np.float64)
    ys = np.asarray([float(point["drawing_y"]) for point in points], dtype=np.float64)
    return {
        "x_span": float(np.max(xs) - np.min(xs)),
        "y_span": float(np.max(ys) - np.min(ys)),
    }


def build_audit(
    payload: dict[str, Any],
    *,
    maximum_check_rmse_m: float = 5.0,
    maximum_check_residual_m: float = 7.5,
    minimum_fit_points: int = 6,
    minimum_check_points: int = 2,
) -> dict[str, Any]:
    if maximum_check_rmse_m <= 0 or maximum_check_residual_m <= 0:
        raise ValueError("residual thresholds must be positive")
    if minimum_fit_points < 3:
        raise ValueError("minimum_fit_points must be at least 3")
    if minimum_check_points < 1:
        raise ValueError("minimum_check_points must be at least 1")

    points = _normalized_points(payload)
    fit_points = [point for point in points if point["role"] == "fit"]
    check_points = [point for point in points if point["role"] == "check"]
    if len(fit_points) < minimum_fit_points:
        raise ValueError(
            f"at least {minimum_fit_points} fit points are required; got {len(fit_points)}"
        )
    if len(check_points) < minimum_check_points:
        raise ValueError(
            f"at least {minimum_check_points} independent check points are required; got {len(check_points)}"
        )

    design = _design_matrix(fit_points)
    target = _target_matrix(fit_points)
    coefficients, _, rank, singular_values = np.linalg.lstsq(design, target, rcond=None)
    if int(rank) < 3:
        raise ValueError("fit points are collinear or otherwise rank deficient")

    fit_rows = _residual_rows(fit_points, coefficients)
    check_rows = _residual_rows(check_points, coefficients)
    fit_summary = _summary(fit_rows)
    check_summary = _summary(check_rows)
    spread = _drawing_spread(fit_points)
    distributed = spread["x_span"] > 0.0 and spread["y_span"] > 0.0
    check_rmse_pass = (
        isinstance(check_summary["rmse_m"], (int, float))
        and float(check_summary["rmse_m"]) <= maximum_check_rmse_m
    )
    check_max_pass = (
        isinstance(check_summary["maximum_m"], (int, float))
        and float(check_summary["maximum_m"]) <= maximum_check_residual_m
    )
    feasible = bool(distributed and check_rmse_pass and check_max_pass)

    coefficient_rows = {
        "target_x_m": {
            "drawing_x": float(coefficients[0, 0]),
            "drawing_y": float(coefficients[1, 0]),
            "intercept": float(coefficients[2, 0]),
        },
        "target_y_m": {
            "drawing_x": float(coefficients[0, 1]),
            "drawing_y": float(coefficients[1, 1]),
            "intercept": float(coefficients[2, 1]),
        },
    }

    return {
        "schema": SCHEMA,
        "status": (
            "derived_georeferencing_feasible_for_manual_review"
            if feasible
            else "derived_georeferencing_rejected"
        ),
        "target_crs": payload.get("target_crs"),
        "fit_point_count": len(fit_points),
        "check_point_count": len(check_points),
        "fit_point_spread": spread,
        "affine_coefficients": coefficient_rows,
        "matrix_rank": int(rank),
        "singular_values": [float(value) for value in singular_values],
        "fit_residual_summary": fit_summary,
        "check_residual_summary": check_summary,
        "fit_point_residuals": fit_rows,
        "check_point_residuals": check_rows,
        "audit_parameters": {
            "maximum_check_rmse_m": maximum_check_rmse_m,
            "maximum_check_residual_m": maximum_check_residual_m,
            "minimum_fit_points": minimum_fit_points,
            "minimum_check_points": minimum_check_points,
        },
        "decision": {
            "derived_geometry_feasible_for_manual_review": feasible,
            "official_survey_geometry_recovered": False,
            "plot_specific_stability_proven": False,
            "earth_engine_query_allowed": False,
            "calibration_record_allowed": False,
            "numerical_depth_ready": False,
        },
        "interpretation": {
            "independent_check_points_used": True,
            "derived_geometry_is_not_official_survey_geometry": True,
            "successful_fit_still_requires_manual_control_feature_review": True,
            "successful_fit_still_requires_post_2014_stability_evidence": True,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit a research-only affine georeference for Tyrone 3X drawings."
    )
    parser.add_argument("--control-points", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--maximum-check-rmse-m", type=float, default=5.0)
    parser.add_argument("--maximum-check-residual-m", type=float, default=7.5)
    return parser


def main() -> int:
    args = _parser().parse_args()
    output_path = args.output_json or args.control_points.with_name(
        args.control_points.stem + "_audit.json"
    )
    try:
        payload = _load_object(args.control_points)
        result = build_audit(
            payload,
            maximum_check_rmse_m=args.maximum_check_rmse_m,
            maximum_check_residual_m=args.maximum_check_residual_m,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "derived_georeferencing_audit_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
