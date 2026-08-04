from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "extract_tyrone_3x_route_b_map_pages.py"
SPEC = importlib.util.spec_from_file_location(
    "extract_tyrone_3x_route_b_map_pages", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_score_page_text_prioritizes_coordinate_and_3x_terms():
    score, hits = MODULE.score_page_text(
        "Reclaimed 3X Mangas Valley coordinate grid NAD83 northing easting"
    )

    assert score >= 40
    assert "reclaimed 3x" in hits
    assert "mangas valley" in hits
    assert "coordinate" in hits
    assert "nad83" in hits
    assert "northing" in hits
    assert "easting" in hits


def test_score_page_text_is_case_and_whitespace_insensitive():
    score, hits = MODULE.score_page_text("TEST   PLOT 5\nTest Plot 6")

    assert score == 20
    assert hits == ("test plot 5", "test plot 6")


def test_select_candidates_preserves_forced_pages_before_scored_limit():
    candidates = [
        MODULE.PageCandidate(
            pdf_name="a.pdf",
            page_number=39,
            score=0,
            hits=(),
            text_preview="",
            forced_reason="known drawing",
        ),
        MODULE.PageCandidate(
            pdf_name="a.pdf",
            page_number=3,
            score=50,
            hits=("3x",),
            text_preview="",
        ),
        MODULE.PageCandidate(
            pdf_name="a.pdf",
            page_number=4,
            score=40,
            hits=("grid",),
            text_preview="",
        ),
    ]

    selected = MODULE.select_candidates(
        candidates,
        maximum_scored_pages_per_pdf=1,
    )

    assert [item.page_number for item in selected] == [39, 3]


def test_select_candidates_removes_duplicate_page_numbers():
    candidates = [
        MODULE.PageCandidate(
            pdf_name="a.pdf",
            page_number=1,
            score=0,
            hits=(),
            text_preview="",
            forced_reason="complete plate",
        ),
        MODULE.PageCandidate(
            pdf_name="a.pdf",
            page_number=1,
            score=20,
            hits=("3x",),
            text_preview="",
        ),
    ]

    selected = MODULE.select_candidates(
        candidates,
        maximum_scored_pages_per_pdf=12,
    )

    assert len(selected) == 1
    assert selected[0].forced_reason == "complete plate"


def test_known_as_built_pages_are_the_forensic_drawing_pages():
    assert MODULE.KNOWN_AS_BUILT_PAGES_1_BASED == (39, 40, 45)
