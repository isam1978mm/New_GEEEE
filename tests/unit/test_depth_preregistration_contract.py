from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "DEPTH_PREREGISTRATION_FRAMEWORK_V1.md"


def test_preregistration_keeps_holdout_closed_until_final_freeze() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "holdout_opened = false" in text
    assert "Any missing field keeps `holdout_opened=false`." in text
    assert "Opening the holdout before the final freeze record exists invalidates the run." in text


def test_preregistration_separates_relative_and_numerical_gates() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "Passing the relative experiment does not approve metre output." in text
    assert "Relative depth has passed" in text
    assert "A single exact depth without an interval is prohibited." in text


def test_preregistration_preserves_software_science_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "synthetic-fixture results prove software behavior only" in text
    assert "depth_mode = off" in text
    assert "visible_depth_result = not_available" in text
