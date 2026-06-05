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


def test_phase_6_and_phase_7_are_complete_and_phase_8_is_complete_and_phase_9_is_next_unchecked_roadmap_phase():
    text = _read(FULL_CHECKLIST)

    phase_5_line = "[x] Phase 5 — QA and intermediate parity — approved —"
    phase_6_line = (
        "[x] Phase 6 — Coordinate/map/private parity outputs — approved — "
        "b17dacbbe07bd40cc40b0e10022d51669e142578 — contract: "
        "`docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md`"
    )
    phase_7_line = (
        "[x] Phase 7 — Classifier/model parity — approved — "
        "383446289214b52012c3ce9d49745cec3bdce376 — contract: "
        "`docs/PHASE_7_CLASSIFIER_MODEL_PARITY_CONTRACT.md`"
    )
    phase_8_line = (
        "[x] Phase 8 — Probability-only ML classifier design — approved — "
        "8abab1a556c9788bc00555c856375c9921c26074 — contract: "
        "`docs/PHASE_8_PROBABILITY_ONLY_CLASSIFIER_DESIGN.md`"
    )
    phase_9_line = (
        "[x] Phase 9 — End-to-end parity harness — approved — "
        "ff5fb2f31abeaa40912e2486de6d5bf17ee8bb6c — contract: "
        "`docs/PHASE_9_END_TO_END_PARITY_HARNESS.md`"
    )
    phase_10_line = "[ ] Phase 10 — Clean app vs parity app decision"

    assert phase_5_line in text
    assert phase_6_line in text
    assert phase_7_line in text
    assert phase_8_line in text
    assert phase_9_line in text
    assert phase_10_line in text
    assert text.index(phase_5_line) < text.index(phase_6_line)
    assert text.index(phase_6_line) < text.index(phase_7_line)
    assert text.index(phase_7_line) < text.index(phase_8_line)
    assert text.index(phase_8_line) < text.index(phase_9_line)
    assert text.index(phase_9_line) < text.index(phase_10_line)
    assert "Phase 4Z" in text
    assert text.index("Phase 4Z") < text.index(phase_5_line)
    assert "[ ] Phase 6 — Coordinate/map/private parity outputs" not in text
    assert "[ ] Phase 7 — Classifier/model parity" not in text
    assert "[ ] Phase 8 — Probability-only ML classifier design" not in text
    assert "[ ] Phase 9 — End-to-end parity harness" not in text


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
    assert "Phase 6A" not in text
    assert "Phase 7A" not in text
    assert "Phase 8A" not in text
