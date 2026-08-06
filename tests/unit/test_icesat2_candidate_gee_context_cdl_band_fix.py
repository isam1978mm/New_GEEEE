from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "audit_icesat2_candidate_gee_context_fixed.py"
)
SPEC = importlib.util.spec_from_file_location("gee_context_cdl_fix", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_2024_cropland_only_band_is_supported():
    selected, cultivated_available = MODULE._selected_cdl_bands(["cropland"])

    assert selected == ["cropland"]
    assert cultivated_available is False


def test_legacy_cropland_and_cultivated_bands_are_preserved():
    selected, cultivated_available = MODULE._selected_cdl_bands(
        ["cropland", "cultivated", "confidence"]
    )

    assert selected == ["cropland", "cultivated"]
    assert cultivated_available is True


def test_missing_required_cropland_band_is_rejected():
    with pytest.raises(ValueError, match="missing required cropland band"):
        MODULE._selected_cdl_bands(["confidence"])


def test_non_list_band_names_response_is_rejected():
    with pytest.raises(ValueError, match="bandNames response must be a list"):
        MODULE._selected_cdl_bands({"cropland": True})
