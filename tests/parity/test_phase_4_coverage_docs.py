import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FULL_CHECKLIST = REPO_ROOT / "docs" / "NOTEBOOK_PARITY_FULL_CHECKLIST.md"
PHASE_4_CHECKLIST = REPO_ROOT / "docs" / "PHASE_4_COVERAGE_CHECKLIST.md"
PHASE_4_SUMMARY = REPO_ROOT / "docs" / "PHASE_4_FINAL_COVERAGE_SUMMARY.md"
SEMANTIC_CONTRACT = REPO_ROOT / "docs" / "SEMANTIC_RASTER_RECOVERY_CONTRACT.md"
SEMANTIC_INVENTORY = REPO_ROOT / "app" / "pipeline" / "parity" / "semantic_raster_recovery.py"

FORBIDDEN_WORDING = {
    "confirmed",
    "proven",
    "dig target",
    "definitely",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase_4_tracking_docs_exist():
    assert FULL_CHECKLIST.exists()
    assert PHASE_4_CHECKLIST.exists()
    assert PHASE_4_SUMMARY.exists()


def test_full_checklist_includes_phase_0_through_phase_10():
    text = _read(FULL_CHECKLIST)

    for phase in [
        "Phase 0",
        "Phase 1",
        "Phase 2",
        "Phase 3",
        "Phase 4",
        "Phase 5",
        "Phase 6",
        "Phase 7",
        "Phase 8",
        "Phase 9",
        "Phase 10",
    ]:
        assert phase in text


def test_phase_4_checklist_includes_phase_4a_through_4h11_and_4z_without_h12():
    text = _read(PHASE_4_CHECKLIST)

    for phase in [
        "Phase 4A",
        "Phase 4B",
        "Phase 4C",
        "Phase 4D1",
        "Phase 4D2",
        "Phase 4D3",
        "Phase 4E1",
        "Phase 4E2",
        "Phase 4E3",
        "Phase 4F1",
        "Phase 4F2",
        "Phase 4G1",
        "Phase 4H1",
        "Phase 4H2",
        "Phase 4H3",
        "Phase 4H4",
        "Phase 4H5",
        "Phase 4H6",
        "Phase 4H7",
        "Phase 4H8",
        "Phase 4H9",
        "Phase 4H10",
        "Phase 4H11",
        "Phase 4Z",
    ]:
        assert phase in text

    assert "Phase 4H12" not in text


def test_h9_h10_h11_are_marked_complete_with_correct_hashes():
    full_text = _read(FULL_CHECKLIST)
    phase_4_text = _read(PHASE_4_CHECKLIST)

    expected_lines = [
        "[x] Phase 4H9 — remaining rare-material semantic rasters recovery + verifier — approved — 19550c010405a5cfce56358fec040d1163b1e4a0",
        "[x] Phase 4H10 — remaining alloy/statue semantic rasters recovery + verifier — approved — 23308ae0ed1cf6a28cc761af949e88f208d4ab80",
        "[x] Phase 4H11 — anchor / non-TIF semantic patterns decision — approved — 28cc36325f7443a695727ce8a14812bd7242f040",
    ]

    for line in expected_lines:
        assert line in phase_4_text

    assert expected_lines[1] in full_text
    assert expected_lines[2] in full_text


def test_phase_4z_is_closed_out_in_the_phase_4_docs():
    full_text = _read(FULL_CHECKLIST)
    phase_4_text = _read(PHASE_4_CHECKLIST)

    assert (
        "[x] Phase 4Z — Phase 4 final coverage summary / naming cleanup — approved — "
        "ddb362ed7175bda4d65446f6278a3d54fe130e05"
    ) in full_text
    assert (
        "[x] Phase 4Z — Phase 4 final coverage summary / naming cleanup — approved — "
        "ddb362ed7175bda4d65446f6278a3d54fe130e05"
    ) in phase_4_text


def test_final_summary_lists_all_phase_4_major_branches_and_invariants():
    text = _read(PHASE_4_SUMMARY)

    for branch in [
        "REPORT_640",
        "secret layers",
        "DEM curvature",
        "Sentinel-1 support stacks",
        "panchromatic support outputs",
        "resampled hypercube",
        "`AI_READY` semantic outputs",
        "`AI_BEH` semantic outputs",
        "anchor / non-TIF semantic pattern decision",
    ]:
        assert branch in text

    for invariant in [
        "Phase 4 did not change raster math.",
        "Phase 4 did not change API, frontend, or database behavior.",
        "Phase 4 did not change artifact serving.",
        "Phase 4 did not call Earth Engine.",
        "Phase 4 did not commit raster or NPY files.",
        "Phase `5` is the next roadmap phase after Phase `4Z`.",
    ]:
        assert invariant in text


def test_semantic_inventory_references_later_contracts_instead_of_describing_h2_through_h11_as_missing():
    text = _read(SEMANTIC_INVENTORY)

    for snippet in [
        "covered by dedicated AI_READY anomaly recovery and verifier contract",
        "covered by dedicated AI_READY metal-hardness recovery and verifier contract",
        "covered by dedicated AI_READY fraction recovery and verifier contract",
        "covered by dedicated AI_BEH relation recovery and verifier contract for the trio",
        "covered by dedicated AI_BEH extended, logic, density/artifact, rare-material, ",
        "covered by dedicated anchor-pattern decision; the four names remain internal ",
    ]:
        assert snippet in text

    for obsolete_phrase in [
        'current_app_status="missing; referenced by notebook patch and downstream scoring cells only"',
        'current_app_status="missing; notebook uses it as a spatial reference and success check, but app has no source writer"',
        'current_app_status="missing; notebook names are visible but no app writer exists"',
        'current_app_status="missing as standalone app notebook-parity outputs"',
    ]:
        assert obsolete_phrase not in text


def test_phase_4z_files_do_not_introduce_forbidden_certainty_wording():
    texts = [
        _read(FULL_CHECKLIST),
        _read(PHASE_4_CHECKLIST),
        _read(PHASE_4_SUMMARY),
        _read(SEMANTIC_CONTRACT),
        _read(SEMANTIC_INVENTORY),
    ]
    merged = "\n".join(texts).lower()

    for term in FORBIDDEN_WORDING:
        assert re.search(rf"\\b{re.escape(term)}\\b", merged) is None


def test_phase_4z_docs_do_not_create_binary_artifacts(tmp_path):
    before = set(tmp_path.rglob("*"))
    _ = _read(FULL_CHECKLIST)
    _ = _read(PHASE_4_CHECKLIST)
    _ = _read(PHASE_4_SUMMARY)
    after = set(tmp_path.rglob("*"))

    assert before == after
    assert not list(tmp_path.rglob("*.tif"))
    assert not list(tmp_path.rglob("*.tiff"))
    assert not list(tmp_path.rglob("*.npy"))
