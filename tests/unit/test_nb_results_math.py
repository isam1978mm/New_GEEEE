from __future__ import annotations

import pytest

from app.services.nb_math import compute_point


def test_nb_point_formulas_and_depth_use_notebook_weights() -> None:
    result = compute_point(
        {
            "gold": 0.8,
            "silver": 0.6,
            "mass": 0.7,
            "sar_comp": 0.5,
            "tunnel": 0.4,
            "door": 0.3,
            "tpi": 0.2,
            "rough": 0.5,
            "pottery": 0.6,
            "lime": 0.2,
            "curv": 0.3,
            "risk": 0.2,
            "quartz": 0.3,
            "moist": 0.4,
            "oxid": 0.2,
            "ascdesc": 0.0,
            "thermal": 0.5,
            "delta": 0.0,
            "nano_depth_penetration": 2.25,
        }
    )

    assert result["nb_metal_signature"] == pytest.approx(0.695, abs=1e-4)
    assert result["nb_void_signature"] == pytest.approx(0.36, abs=1e-4)
    assert result["nb_ceramic_signature"] == pytest.approx(0.46, abs=1e-4)
    assert result["nb_mass_signature"] == pytest.approx(0.7, abs=1e-4)
    assert result["nano_depth_penetration"] == pytest.approx(2.25)
    assert result["nb_depth_m"] == pytest.approx(2.03, abs=0.01)
    assert result["nb_depth_available"] is True


def test_nb_depth_abstains_when_required_input_is_missing() -> None:
    result = compute_point(
        {
            "tunnel": 0.4,
            "door": 0.3,
            "tpi": 0.2,
            "rough": 0.5,
            "sar_comp": 0.5,
            "thermal": 0.5,
            # thermal delta deliberately absent
        }
    )
    assert result["nb_void_signature"] == pytest.approx(0.36, abs=1e-4)
    assert result["nb_depth_m"] is None
    assert result["nb_depth_available"] is False


def test_nb_missing_inputs_do_not_turn_into_fake_values() -> None:
    result = compute_point({})
    assert result["nb_metal_signature"] is None
    assert result["nb_void_signature"] is None
    assert result["nb_depth_m"] is None
    assert result["nb_depth_available"] is False
