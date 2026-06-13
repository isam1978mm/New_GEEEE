from __future__ import annotations

import json

import pytest

from app.services.v6_real_scoring import (
    V6ScoringThresholds,
    score_v6_candidates,
    validate_v6_scoring_input_row,
)


def _row(cell_id: str, **overrides):
    row = {
        "cell_id": cell_id,
        "visibility_score": 0.70,
        "spectral_contrast": 0.60,
        "sar_contrast": 0.50,
        "terrain_score": 0.80,
        "s2_count": 8,
        "builtup_frac": 0.0,
        "builtup_near_frac": 0.0,
        "cropland_frac": 0.0,
        "water_edge_frac": 0.0,
        "v6_strong_built_frac": 0.0,
        "v6_building_near_frac": 0.0,
        "v6_road_like_edge_frac": 0.0,
        "v6_modern_corridor_frac": 0.0,
        "confidence_score_all": 0.8,
        "stability_score_norm": 0.7,
        "season_stability_norm": 0.6,
        "score_gap_from_median": 0.1,
        "top10_count": 2,
        "top25_count": 4,
        "season_top10_count": 1,
        "season_top25_count": 3,
    }
    row.update(overrides)
    return row


def test_score_v6_candidates_ranks_clean_candidates_before_warned_candidates() -> None:
    scored = score_v6_candidates(
        [
            _row("WARNED", v6_strong_built_frac=0.5, v6_road_like_edge_frac=0.5, candidate_score=0.99),
            _row("CLEAN", visibility_score=0.75, spectral_contrast=0.65, terrain_score=0.85),
        ]
    )

    assert [candidate.cell_id for candidate in scored] == ["CLEAN", "WARNED"]
    assert scored[0].final_priority_rank_v6 == 1
    assert scored[0].v6_false_positive_warning_count == 0
    assert scored[1].v6_false_positive_warning_count == 2
    assert scored[1].v6_false_positive_penalty == 0.14


def test_score_v6_candidates_uses_notebook_candidate_score_formula_components() -> None:
    scored = score_v6_candidates([
        _row(
            "A",
            visibility_score=1.0,
            spectral_contrast=1.0,
            sar_contrast=1.0,
            terrain_score=1.0,
            s2_count=8,
        )
    ])

    assert scored[0].candidate_score == 1.0
    assert scored[0].remote_sensing_contrast == 1.0
    assert scored[0].s2_confidence == 1.0


def test_score_v6_candidates_caps_warning_penalty() -> None:
    thresholds = V6ScoringThresholds(
        builtup_warning_frac=0.01,
        builtup_near_warning_frac=0.01,
        cropland_heavy_frac=0.01,
        water_edge_warning_frac=0.01,
        v6_strong_built_frac=0.01,
        v6_building_near_frac=0.01,
        v6_road_like_edge_frac=0.01,
        v6_modern_corridor_frac=0.01,
    )

    scored = score_v6_candidates(
        [_row("A", builtup_frac=1, cropland_frac=1, water_edge_frac=1, v6_strong_built_frac=1, v6_road_like_edge_frac=1)],
        thresholds=thresholds,
    )

    assert scored[0].v6_false_positive_warning_count == 4
    assert scored[0].v6_false_positive_penalty == 0.28
    assert scored[0].v6_no_warning_bonus == 0.0


def test_validate_v6_scoring_input_row_reports_missing_and_invalid_features() -> None:
    row = _row("A")
    row.pop("visibility_score")
    row["terrain_score"] = float("nan")

    issues = validate_v6_scoring_input_row(row)

    assert "missing_score_feature:visibility_score" in issues
    assert "invalid_score_feature:terrain_score" in issues


def test_scored_candidate_safe_summary_has_no_geometry_or_feature_values() -> None:
    scored = score_v6_candidates([_row("A")])[0]

    summary = scored.safe_summary()
    serialized = json.dumps(summary, sort_keys=True)

    assert summary["contains_geometry"] is False
    assert summary["cell_id"] == "A"
    assert "visibility_score" not in serialized
    assert "spectral_contrast" not in serialized
    assert "bounds" not in serialized


def test_score_v6_candidates_is_deterministic_for_ties() -> None:
    scored = score_v6_candidates([_row("B"), _row("A")])

    assert [candidate.cell_id for candidate in scored] == ["A", "B"]
