from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "audit_icesat2_candidate_gee_context.py"
)
SPEC = importlib.util.spec_from_file_location("gee_context", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _dossier() -> dict:
    return {
        "candidate_id": "candidate_009",
        "campaign_id": "campaign_v3",
        "campaign_rank": 9,
        "segment_count": 5,
        "candidate_summary": {
            "campaign_rank": 9,
            "longitude": -115.413375,
            "latitude": 32.769190,
            "median_step_m": 0.808,
            "segment_count": 5,
            "event_start": "2021-05-23T00:00:00+00:00",
            "event_end": "2022-05-21T00:00:00+00:00",
        },
        "segments": [
            {"longitude": -115.4135, "latitude": 32.7683},
            {"longitude": -115.4134, "latitude": 32.7692},
            {"longitude": -115.4133, "latitude": 32.7701},
        ],
    }


def test_agricultural_context_blocks_records_research():
    result = MODULE.build_context_decision(
        _dossier(),
        cdl_years=[
            {
                "year": 2021,
                "point_cropland_name": "Alfalfa",
                "point_cultivated_name": "Cultivated",
                "buffer_cultivated_fraction": 0.94,
            }
        ],
        dynamic_world_windows=[
            {
                "mean_probabilities": {
                    "crops": 0.72,
                    "built": 0.03,
                    "bare": 0.10,
                }
            }
        ],
    )

    assert result["status"] == "agricultural_context_detected"
    assert result["context_indicators"]["cultivated_years"] == [2021]
    assert result["decision"]["records_research_recommended"] is False
    assert result["decision"]["candidate_is_depth_anchor"] is False


def test_built_context_stays_manual_review_only():
    result = MODULE.build_context_decision(
        _dossier(),
        cdl_years=[
            {
                "year": 2021,
                "point_cultivated_name": "Non-Cultivated",
                "buffer_cultivated_fraction": 0.02,
            }
        ],
        dynamic_world_windows=[
            {
                "mean_probabilities": {
                    "crops": 0.04,
                    "built": 0.61,
                    "bare": 0.20,
                }
            }
        ],
    )

    assert result["status"] == "engineered_or_built_context_possible"
    assert result["context_indicators"]["built_context_detected"] is True
    assert result["decision"]["records_research_recommended"] is False


def test_context_can_remain_inconclusive():
    result = MODULE.build_context_decision(
        _dossier(),
        cdl_years=[],
        dynamic_world_windows=[
            {
                "mean_probabilities": {
                    "crops": 0.12,
                    "built": 0.08,
                    "bare": 0.18,
                }
            }
        ],
    )

    assert result["status"] == "context_inconclusive"
    assert (
        result["decision"]["manual_imagery_and_parcel_review_recommended"]
        is True
    )


def test_named_histogram_maps_classes_and_fractions():
    rows = MODULE._named_histogram(
        {"1": 75, "2": 25},
        {1: "Cultivated", 2: "Non-Cultivated"},
    )

    assert rows[0]["name"] == "Cultivated"
    assert rows[0]["fraction"] == pytest.approx(0.75)
    assert MODULE._cultivated_fraction(rows) == pytest.approx(0.75)
