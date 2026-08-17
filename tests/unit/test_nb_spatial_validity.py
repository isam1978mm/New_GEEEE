from __future__ import annotations

import numpy as np

from app.services.nb_spatial_validity import assess_nb_spatial_validity, directional_boundary_score


def _row(*, area_px: int = 5, row_min: int = 20, row_max: int = 22, col_min: int = 20, col_max: int = 22):
    return {
        "area_px": str(area_px),
        "row_min": str(row_min),
        "row_max": str(row_max),
        "col_min": str(col_min),
        "col_max": str(col_max),
    }


def _boundary(axis: str) -> np.ndarray:
    array = np.zeros((64, 64), dtype=np.float32)
    if axis == "vertical":
        array[:, 32:] = 10.0
    else:
        array[32:, :] = 10.0
    return array


def test_directional_boundary_score_detects_broad_split() -> None:
    score = directional_boundary_score(_boundary("vertical"), row=32, col=32)
    assert score is not None
    assert score >= 0.9


def test_shadow_qa_fails_oversized_region_without_suppressing_results() -> None:
    result = assess_nb_spatial_validity(
        object_row=_row(area_px=3943, row_min=10, row_max=112, col_min=20, col_max=102),
        shape=(640, 640),
        row=60,
        col=60,
        layers={},
    )

    assert result["mode"] == "shadow"
    assert result["status"] == "FAIL"
    assert "oversized_region" in result["reasons"]
    assert result["candidate_suppressed"] is False
    assert result["interpretation_suppressed"] is False
    assert result["depth_suppressed"] is False


def test_shadow_qa_fails_edge_candidate_with_multigroup_boundary() -> None:
    result = assess_nb_spatial_validity(
        object_row=_row(area_px=5, row_min=30, row_max=32, col_min=0, col_max=1),
        shape=(64, 64),
        row=32,
        col=0,
        layers={
            "vv": _boundary("horizontal"),
            "thermal_day": _boundary("horizontal"),
        },
    )

    assert result["edge_touch"] is True
    assert result["boundary_group_count"] == 2
    assert result["status"] == "FAIL"
    assert "grid_edge_touch" in result["reasons"]
    assert "multigroup_surface_boundary" in result["reasons"]


def test_shadow_qa_marks_multigroup_boundary_mixed_away_from_edge() -> None:
    result = assess_nb_spatial_validity(
        object_row=_row(),
        shape=(64, 64),
        row=32,
        col=32,
        layers={
            "vh": _boundary("vertical"),
            "mass": _boundary("horizontal"),
        },
    )

    assert result["edge_touch"] is False
    assert result["oversized_region"] is False
    assert result["boundary_group_count"] == 2
    assert result["status"] == "MIXED"


def test_shadow_qa_passes_compact_candidate_without_surface_flags() -> None:
    flat = np.ones((64, 64), dtype=np.float32)
    result = assess_nb_spatial_validity(
        object_row=_row(),
        shape=(64, 64),
        row=21,
        col=21,
        layers={"vv": flat, "thermal_day": flat, "rough": flat},
    )

    assert result["status"] == "PASS"
    assert result["reasons"] == []
