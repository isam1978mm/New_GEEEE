from __future__ import annotations

import json
from pathlib import Path


DECISION_PATH = Path("config/tyrone_3x_route_b_geometry_decision.json")


def _decision() -> dict:
    return json.loads(DECISION_PATH.read_text(encoding="utf-8"))


def test_route_b_geometry_decision_keeps_all_unlocks_closed() -> None:
    payload = _decision()
    assert payload["status"] == "route_b_rejected_insufficient_homologous_controls"
    decision = payload["decision"]
    assert decision["route_b_geometry_recovery_succeeded"] is False
    assert decision["coordinate_geometry_unblocked"] is False
    assert decision["earth_engine_plot_query_allowed"] is False
    assert decision["calibration_record_allowed"] is False
    assert decision["plot_specific_stability_proven"] is False
    assert decision["numerical_depth_unlocked"] is False


def test_route_b_decision_preserves_strict_control_gate() -> None:
    gate = _decision()["strict_gate"]
    assert gate == {
        "minimum_fit_points": 6,
        "minimum_independent_check_points": 2,
        "maximum_check_rmse_m": 5.0,
        "maximum_check_residual_m": 7.5,
    }


def test_route_b_does_not_claim_an_audit_from_invented_controls() -> None:
    review = _decision()["manual_review"]
    assert review["tp5_tp6_plot_boundaries_unambiguously_visible_in_imagery"] is False
    assert review["six_well_distributed_fit_controls_available_without_guessing"] is False
    assert review["two_independent_check_controls_available_without_reusing_fit_evidence"] is False
    assert review["strict_affine_audit_run"] is False
    assert "invented or circular" in review["strict_affine_audit_not_run_reason"]


def test_verified_geotiff_metadata_is_recorded() -> None:
    imagery = _decision()["verified_imagery"]
    assert imagery["years"] == [2009, 2011]
    assert imagery["pixel_size_m"] == 1.0
    assert imagery["width"] == 2207
    assert imagery["height"] == 2118
    assert imagery["affine_transform"] == [1.0, 0.0, 179023.0, 0.0, -1.0, 3623489.0]
