from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FULL_CHECKLIST = REPO_ROOT / "docs" / "NOTEBOOK_PARITY_FULL_CHECKLIST.md"
PHASE_4_CHECKLIST = REPO_ROOT / "docs" / "PHASE_4_COVERAGE_CHECKLIST.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_roadmap_checklist_marks_phase_4z_and_phase_5_complete():
    text = _read(FULL_CHECKLIST)

    assert (
        "[x] Phase 4Z — Phase 4 final coverage summary / naming cleanup — approved — "
        "ddb362ed7175bda4d65446f6278a3d54fe130e05"
    ) in text
    assert (
        "[x] Phase 5 — QA and intermediate parity — approved — "
        "8ec135c68957cc92f3d62b91dd445896b8d4eb85 — contract: "
        "`docs/PHASE_5_QA_INTERMEDIATE_PARITY_CONTRACT.md`"
    ) in text


def test_phase_six_is_next_unchecked_roadmap_phase():
    text = _read(FULL_CHECKLIST)

    phase_5_line = "[x] Phase 5 — QA and intermediate parity — approved —"
    phase_6_line = "[ ] Phase 6 — Coordinate/map/private parity outputs"

    assert phase_5_line in text
    assert phase_6_line in text
    assert text.index(phase_5_line) < text.index(phase_6_line)
    assert "Phase 4Z" in text
    assert text.index("Phase 4Z") < text.index(phase_5_line)


def test_phase_4_checklist_marks_phase_4z_complete():
    text = _read(PHASE_4_CHECKLIST)

    assert (
        "[x] Phase 4Z — Phase 4 final coverage summary / naming cleanup — approved — "
        "ddb362ed7175bda4d65446f6278a3d54fe130e05"
    ) in text


def test_no_competing_roadmap_list_is_introduced():
    text = _read(FULL_CHECKLIST)

    assert text.count("```text") == 1
    assert text.count("Phase 0 — Output inventory lock") == 1
    assert text.count("Phase 10 — Clean app vs parity app decision") == 1
    assert "Phase 4H12" not in text
