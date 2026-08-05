#!/usr/bin/env python3
"""Audit Tyrone OSE spatial-pattern hypotheses with independent checkpoints.

Each seven-point discovery hypothesis is re-fit repeatedly using five points and
validated on the two withheld points. This is a discovery credibility screen;
it does not itself establish final TP5/TP6 geometry or unlock numerical depth.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from pyproj import Transformer

DEFAULT_CHECK_RMSE_M = 5.0
DEFAULT_CHECK_MAX_M = 7.5
OUTPUT_NAME = "tyrone_ose_spatial_pattern_audit.json"


def _fit_similarity(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray, bool]:
    """Return the best 2-D similarity transform, considering reflection."""
    if source.shape != target.shape or source.ndim != 2 or source.shape[1] != 2:
        raise ValueError("source and target must be matching Nx2 arrays")
    if len(source) < 2:
        raise ValueError("at least two points are required")

    best: tuple[float, np.ndarray, np.ndarray, bool] | None = None
    for reflected in (False, True):
        work = source.copy()
        if reflected:
            work[:, 0] *= -1.0
        src_mean = work.mean(axis=0)
        dst_mean = target.mean(axis=0)
        src_centered = work - src_mean
        dst_centered = target - dst_mean
        covariance = src_centered.T @ dst_centered
        u, _, vt = np.linalg.svd(covariance)
        rotation = u @ vt
        if np.linalg.det(rotation) < 0:
            u[:, -1] *= -1
            rotation = u @ vt
        denominator = float(np.sum(src_centered**2))
        if denominator <= 0:
            raise ValueError("source points are degenerate")
        scale = float(np.sum((src_centered @ rotation) * dst_centered) / denominator)
        matrix = scale * rotation
        if reflected:
            reflection = np.array([[-1.0, 0.0], [0.0, 1.0]])
            matrix = reflection @ matrix
        offset = dst_mean - source.mean(axis=0) @ matrix
        predicted = source @ matrix + offset
        rmse = float(np.sqrt(np.mean(np.sum((predicted - target) ** 2, axis=1))))
        candidate = (rmse, matrix, offset, reflected)
        if best is None or candidate[0] < best[0]:
            best = candidate
    assert best is not None
    return best[1], best[2], best[3]


def _errors(source: np.ndarray, target: np.ndarray, matrix: np.ndarray, offset: np.ndarray) -> np.ndarray:
    predicted = source @ matrix + offset
    return np.sqrt(np.sum((predicted - target) ** 2, axis=1))


def _map_lookup(report: dict[str, Any]) -> dict[str, tuple[float, float]]:
    points = report.get("map_config", {}).get("points")
    if not isinstance(points, list):
        raise ValueError("report lacks map_config.points")
    lookup: dict[str, tuple[float, float]] = {}
    for row in points:
        point_id = str(row["id"])
        lookup[point_id] = (float(row["x"]), -float(row["y"]))
    return lookup


def _hypothesis_arrays(
    hypothesis: dict[str, Any],
    map_lookup: dict[str, tuple[float, float]],
    transformer: Transformer,
) -> tuple[list[str], np.ndarray, np.ndarray]:
    ids: list[str] = []
    source: list[tuple[float, float]] = []
    lon: list[float] = []
    lat: list[float] = []
    for row in hypothesis.get("matches", []):
        if not row.get("matched"):
            continue
        point_id = str(row["map_point_id"])
        if point_id not in map_lookup:
            continue
        longitude = row.get("candidate_longitude")
        latitude = row.get("candidate_latitude")
        if longitude is None or latitude is None:
            continue
        ids.append(point_id)
        source.append(map_lookup[point_id])
        lon.append(float(longitude))
        lat.append(float(latitude))
    east, north = transformer.transform(lon, lat)
    target = np.column_stack((east, north)).astype(float)
    return ids, np.asarray(source, dtype=float), target


def audit_hypothesis(
    hypothesis: dict[str, Any],
    map_lookup: dict[str, tuple[float, float]],
    transformer: Transformer,
    *,
    check_rmse_m: float,
    check_max_m: float,
) -> dict[str, Any]:
    ids, source, target = _hypothesis_arrays(hypothesis, map_lookup, transformer)
    if len(ids) < 7:
        return {
            "matched_count": len(ids),
            "status": "insufficient_points_for_leave_two_out",
            "strict_passing_split_count": 0,
            "best_split": None,
        }

    splits: list[dict[str, Any]] = []
    all_indices = tuple(range(len(ids)))
    for check_indices_tuple in itertools.combinations(all_indices, 2):
        check_indices = set(check_indices_tuple)
        fit_indices = [index for index in all_indices if index not in check_indices]
        matrix, offset, reflected = _fit_similarity(source[fit_indices], target[fit_indices])
        fit_errors = _errors(source[fit_indices], target[fit_indices], matrix, offset)
        check_errors = _errors(source[list(check_indices_tuple)], target[list(check_indices_tuple)], matrix, offset)
        fit_rmse = float(np.sqrt(np.mean(fit_errors**2)))
        check_rmse = float(np.sqrt(np.mean(check_errors**2)))
        check_max = float(np.max(check_errors))
        strict_pass = check_rmse <= check_rmse_m and check_max <= check_max_m
        splits.append(
            {
                "fit_point_ids": [ids[index] for index in fit_indices],
                "check_point_ids": [ids[index] for index in check_indices_tuple],
                "fit_rmse_m": fit_rmse,
                "fit_max_m": float(np.max(fit_errors)),
                "check_rmse_m": check_rmse,
                "check_max_m": check_max,
                "check_residuals_m": {
                    ids[index]: float(error)
                    for index, error in zip(check_indices_tuple, check_errors, strict=True)
                },
                "reflected": reflected,
                "strict_pass": strict_pass,
            }
        )
    splits.sort(key=lambda row: (not row["strict_pass"], row["check_rmse_m"], row["check_max_m"], row["fit_rmse_m"]))
    passing = [row for row in splits if row["strict_pass"]]
    return {
        "matched_count": len(ids),
        "status": "credible_discovery_pattern" if passing else "discovery_pattern_failed_independent_accuracy",
        "strict_passing_split_count": len(passing),
        "best_split": splits[0] if splits else None,
        "split_count": len(splits),
    }


def audit_report(
    report: dict[str, Any],
    *,
    check_rmse_m: float = DEFAULT_CHECK_RMSE_M,
    check_max_m: float = DEFAULT_CHECK_MAX_M,
) -> dict[str, Any]:
    hypotheses = report.get("hypotheses")
    if not isinstance(hypotheses, list):
        raise ValueError("input report lacks hypotheses list")
    map_lookup = _map_lookup(report)
    transformer = Transformer.from_crs(4326, 32612, always_xy=True)
    audited = [
        {
            "hypothesis_index": index,
            **audit_hypothesis(
                hypothesis,
                map_lookup,
                transformer,
                check_rmse_m=check_rmse_m,
                check_max_m=check_max_m,
            ),
        }
        for index, hypothesis in enumerate(hypotheses)
    ]
    audited.sort(
        key=lambda row: (
            row["status"] != "credible_discovery_pattern",
            -row.get("strict_passing_split_count", 0),
            (row.get("best_split") or {}).get("check_rmse_m", math.inf),
        )
    )
    credible = [row for row in audited if row["status"] == "credible_discovery_pattern"]
    return {
        "schema": "tyrone_ose_spatial_pattern_audit_v1",
        "status": "credible_discovery_pattern_found" if credible else "all_discovery_patterns_failed_independent_accuracy",
        "thresholds": {
            "check_rmse_m_max": check_rmse_m,
            "check_max_residual_m_max": check_max_m,
            "fit_points_per_split": 5,
            "independent_check_points_per_split": 2,
        },
        "input_hypothesis_count": len(hypotheses),
        "credible_hypothesis_count": len(credible),
        "hypotheses": audited,
        "warning": (
            "Even a credible seven-well discovery pattern is not the final geometry gate. "
            "The final route still requires at least six well-distributed controls, two independent "
            "checks, TP5/TP6 digitization, exclusion masks, and post-2014 stability proof."
        ),
        "coordinate_geometry_unblocked": False,
        "numerical_depth_unlocked": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hypotheses-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--check-rmse-m", type=float, default=DEFAULT_CHECK_RMSE_M)
    parser.add_argument("--check-max-m", type=float, default=DEFAULT_CHECK_MAX_M)
    args = parser.parse_args()
    try:
        if args.check_rmse_m <= 0 or args.check_max_m <= 0:
            raise ValueError("accuracy thresholds must be positive")
        report = json.loads(args.hypotheses_json.read_text(encoding="utf-8-sig"))
        audit = audit_report(
            report,
            check_rmse_m=args.check_rmse_m,
            check_max_m=args.check_max_m,
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        output = args.output_dir / OUTPUT_NAME
        output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({
            "status": "spatial_hypothesis_audit_failed",
            "error": str(exc),
            "coordinate_geometry_unblocked": False,
            "numerical_depth_unlocked": False,
        }, indent=2), file=sys.stderr)
        return 1

    best = audit["hypotheses"][0] if audit["hypotheses"] else None
    print(json.dumps({
        "status": audit["status"],
        "input_hypothesis_count": audit["input_hypothesis_count"],
        "credible_hypothesis_count": audit["credible_hypothesis_count"],
        "best_hypothesis_index": best.get("hypothesis_index") if best else None,
        "best_status": best.get("status") if best else None,
        "best_split": best.get("best_split") if best else None,
        "json": str(output.resolve()),
        "coordinate_geometry_unblocked": False,
        "numerical_depth_unlocked": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
