from __future__ import annotations

from typing import Any

import numpy as np

SPATIAL_QA_MODE = "shadow"
LOCAL_RADIUS_PX = 6
BOUNDARY_GROUP_THRESHOLD = 0.50
OVERSIZED_AREA_PX = 1024
OVERSIZED_SPAN_PX = 64

_LAYER_GROUPS = {
    "radar": ("vv", "vh", "logratio", "incidence", "ascdesc"),
    "thermal": ("thermal_day", "thermal_inertia", "thermal_delta"),
    "terrain": ("rough", "tpi", "curv"),
    "report": ("mass", "pottery"),
}


def _as_int(row: dict[str, str], name: str) -> int | None:
    try:
        return int(round(float(row[name])))
    except (KeyError, TypeError, ValueError):
        return None


def _side_median(array: np.ndarray) -> float | None:
    valid = array[np.isfinite(array)]
    if valid.size < 5:
        return None
    return float(np.nanmedian(valid))


def directional_boundary_score(
    array: np.ndarray,
    *,
    row: int,
    col: int,
    radius: int = LOCAL_RADIUS_PX,
) -> float | None:
    """Return a scale-free local split score for a broad surface boundary.

    The score compares opposite halves of a local window and normalizes the
    difference by the local 10th-to-90th percentile range. It is intentionally
    diagnostic only: this module runs in shadow mode and never removes a target.
    """
    source = np.asarray(array, dtype=np.float32)
    if source.ndim != 2:
        return None

    row0 = max(0, row - radius)
    row1 = min(source.shape[0], row + radius + 1)
    col0 = max(0, col - radius)
    col1 = min(source.shape[1], col + radius + 1)
    patch = source[row0:row1, col0:col1]
    valid = patch[np.isfinite(patch)]
    if valid.size < 20:
        return None

    p10, p90 = np.nanpercentile(valid, [10.0, 90.0])
    local_range = float(p90 - p10)
    if not np.isfinite(local_range) or local_range < 1e-6:
        return 0.0

    local_row = row - row0
    local_col = col - col0
    split_scores: list[float] = []
    for first, second in (
        (patch[:local_row, :], patch[local_row + 1 :, :]),
        (patch[:, :local_col], patch[:, local_col + 1 :]),
    ):
        first_median = _side_median(first)
        second_median = _side_median(second)
        if first_median is None or second_median is None:
            continue
        split_scores.append(abs(first_median - second_median) / local_range)

    if not split_scores:
        return 0.0
    return float(np.clip(max(split_scores), 0.0, 2.0))


def assess_nb_spatial_validity(
    *,
    object_row: dict[str, str],
    shape: tuple[int, int],
    row: int,
    col: int,
    layers: dict[str, np.ndarray | None],
) -> dict[str, Any]:
    """Compute additive NB spatial QA without changing any NB result.

    PASS/MIXED/FAIL is diagnostic metadata only while ``mode == shadow``.
    No candidate, interpretation, score, or depth is suppressed by this function.
    """
    row_min = _as_int(object_row, "row_min")
    row_max = _as_int(object_row, "row_max")
    col_min = _as_int(object_row, "col_min")
    col_max = _as_int(object_row, "col_max")
    area_px = _as_int(object_row, "area_px")

    edge_touch = False
    bbox_height_px = None
    bbox_width_px = None
    if None not in (row_min, row_max, col_min, col_max):
        assert row_min is not None and row_max is not None and col_min is not None and col_max is not None
        edge_touch = row_min <= 0 or col_min <= 0 or row_max >= shape[0] - 1 or col_max >= shape[1] - 1
        bbox_height_px = max(0, row_max - row_min + 1)
        bbox_width_px = max(0, col_max - col_min + 1)

    oversized = False
    if area_px is not None and area_px >= OVERSIZED_AREA_PX:
        oversized = True
    if bbox_height_px is not None and bbox_height_px >= OVERSIZED_SPAN_PX:
        oversized = True
    if bbox_width_px is not None and bbox_width_px >= OVERSIZED_SPAN_PX:
        oversized = True

    layer_scores: dict[str, float] = {}
    for name, array in layers.items():
        if array is None:
            continue
        score = directional_boundary_score(array, row=row, col=col)
        if score is not None:
            layer_scores[name] = round(float(score), 4)

    group_scores: dict[str, float] = {}
    for group_name, names in _LAYER_GROUPS.items():
        scores = [layer_scores[name] for name in names if name in layer_scores]
        if scores:
            group_scores[group_name] = round(max(scores), 4)

    boundary_groups = sorted(
        group_name
        for group_name, score in group_scores.items()
        if score >= BOUNDARY_GROUP_THRESHOLD
    )
    multigroup_boundary = len(boundary_groups) >= 2

    reasons: list[str] = []
    if oversized:
        reasons.append("oversized_region")
    if edge_touch:
        reasons.append("grid_edge_touch")
    if multigroup_boundary:
        reasons.append("multigroup_surface_boundary")

    if oversized or (edge_touch and multigroup_boundary):
        status = "FAIL"
    elif edge_touch or multigroup_boundary:
        status = "MIXED"
    else:
        status = "PASS"

    return {
        "mode": SPATIAL_QA_MODE,
        "status": status,
        "reasons": reasons,
        "candidate_suppressed": False,
        "interpretation_suppressed": False,
        "depth_suppressed": False,
        "edge_touch": edge_touch,
        "oversized_region": oversized,
        "area_px": area_px,
        "bbox_height_px": bbox_height_px,
        "bbox_width_px": bbox_width_px,
        "boundary_group_count": len(boundary_groups),
        "boundary_groups": boundary_groups,
        "boundary_group_scores": group_scores,
        "boundary_layer_scores": layer_scores,
    }
