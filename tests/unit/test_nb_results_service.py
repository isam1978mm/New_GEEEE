from __future__ import annotations

from app.services.nb_results import build_nb_results


def test_nb_results_without_existing_run_outputs_is_not_available(tmp_path) -> None:
    result = build_nb_results(tmp_path)
    assert result["status"] == "not_available"
    assert result["reason"] == "object_results_unavailable"
    assert result["limitations"]["fake_three_meter_fallback_used"] is False
    assert result["unavailable_support"] == []
    assert result["objects"] == []
