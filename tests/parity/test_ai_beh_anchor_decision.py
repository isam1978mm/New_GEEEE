from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.pipeline.parity.ai_beh_anchor_decision import (
    ALLOWED_DECISIONS,
    ALLOWED_IMPLEMENTATION_STATUSES,
    ALLOWED_SOURCE_STATUSES,
    AIBehAnchorDecisionItem,
    get_ai_beh_anchor_pattern_decisions,
    write_ai_beh_anchor_pattern_decision_report,
)


EXPECTED_PATTERNS = {
    "AI_BEH_VegRoot_Anomaly",
    "AI_BEH_IronOxide_Hardness",
    "AI_BEH_GoldAlloy_Signal",
    "AI_BEH_MassVolume_Shadow",
}


def test_decision_checklist_covers_all_anchor_patterns() -> None:
    items = get_ai_beh_anchor_pattern_decisions()

    assert len(items) == 4
    assert {item.notebook_pattern for item in items} == EXPECTED_PATTERNS


def test_decision_items_use_valid_enums_and_nonblank_evidence() -> None:
    items = get_ai_beh_anchor_pattern_decisions()

    for item in items:
        assert item.source_status in ALLOWED_SOURCE_STATUSES
        assert item.decision in ALLOWED_DECISIONS
        assert item.implementation_status in ALLOWED_IMPLEMENTATION_STATUSES
        assert item.source_reference.strip()
        assert item.standalone_export_evidence.strip()
        assert item.report_640_internal_evidence.strip()


def test_decision_items_stay_private_and_unverified() -> None:
    items = get_ai_beh_anchor_pattern_decisions()

    for item in items:
        assert item.runtime_output_verified is False
        assert item.notebook_value_parity_verified is False
        assert item.target_mode != "public_shared"
        assert item.http_servable is False


def test_decision_report_writes_and_parses(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    report_path = write_ai_beh_anchor_pattern_decision_report(run_dir, "run-4h11")

    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == run_dir / "manifests" / "ai_beh_anchor_pattern_decision_report.json"
    assert payload["run_id"] == "run-4h11"
    assert payload["phase_4h11_formula_changes"] is False
    assert len(payload["items"]) == 4


def test_decision_report_stays_under_run_dir(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_ai_beh_anchor_pattern_decision_report(
            tmp_path / "run",
            "run-4h11",
            report_relative_path="../escape.json",
        )


def test_decision_report_creates_no_tif_tiff_or_npy(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    write_ai_beh_anchor_pattern_decision_report(run_dir, "run-4h11")

    assert not list(run_dir.rglob("*.tif"))
    assert not list(run_dir.rglob("*.tiff"))
    assert not list(run_dir.rglob("*.npy"))


def test_allowed_enums_are_enforced() -> None:
    with pytest.raises(ValueError):
        AIBehAnchorDecisionItem(
            id="bad-source",
            notebook_pattern="AI_BEH_VegRoot_Anomaly",
            family="AI_BEH semantic rasters",
            source_status="bad",
            authoritative_source_available=True,
            source_reference="ref",
            standalone_export_evidence="evidence",
            report_640_internal_evidence="evidence",
            existing_contract_reference=None,
            expected_formula_summary="formula",
            expected_input_outputs=(),
            decision="internal_report_precursor_only",
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="notebook-parity semantic item",
            http_servable=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="no_action_needed_internal_precursor",
            blocker="blocker",
            recommended_next_action="next",
            notes="notes",
        )

    with pytest.raises(ValueError):
        AIBehAnchorDecisionItem(
            id="bad-decision",
            notebook_pattern="AI_BEH_VegRoot_Anomaly",
            family="AI_BEH semantic rasters",
            source_status="exact_source_available",
            authoritative_source_available=True,
            source_reference="ref",
            standalone_export_evidence="evidence",
            report_640_internal_evidence="evidence",
            existing_contract_reference=None,
            expected_formula_summary="formula",
            expected_input_outputs=(),
            decision="bad",
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="notebook-parity semantic item",
            http_servable=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="no_action_needed_internal_precursor",
            blocker="blocker",
            recommended_next_action="next",
            notes="notes",
        )

    with pytest.raises(ValueError):
        AIBehAnchorDecisionItem(
            id="bad-impl",
            notebook_pattern="AI_BEH_VegRoot_Anomaly",
            family="AI_BEH semantic rasters",
            source_status="exact_source_available",
            authoritative_source_available=True,
            source_reference="ref",
            standalone_export_evidence="evidence",
            report_640_internal_evidence="evidence",
            existing_contract_reference=None,
            expected_formula_summary="formula",
            expected_input_outputs=(),
            decision="internal_report_precursor_only",
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="notebook-parity semantic item",
            http_servable=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="bad",
            blocker="blocker",
            recommended_next_action="next",
            notes="notes",
        )


def test_docs_and_code_avoid_certainty_wording() -> None:
    doc_text = Path("docs/AI_BEH_ANCHOR_PATTERN_DECISION.md").read_text(
        encoding="utf-8"
    ).lower()
    code_text = Path("app/pipeline/parity/ai_beh_anchor_decision.py").read_text(
        encoding="utf-8"
    ).lower()

    for forbidden in ("confirmed", "proven", "dig target", "definitely"):
        assert forbidden not in doc_text
        assert forbidden not in code_text
