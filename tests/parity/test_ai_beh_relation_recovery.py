from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.pipeline.parity.ai_beh_relation_recovery import (
    ALLOWED_IMPLEMENTATION_STATUSES,
    ALLOWED_SOURCE_STATUSES,
    AIBehRelationRecoveryItem,
    get_ai_beh_relation_recovery_checklist,
    write_ai_beh_relation_recovery_report,
)


EXPECTED_OUTPUTS = {
    "AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif": "normalizedDifference(B8, B4)",
    "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif": "B4 / B3",
    "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif": "B11 / B12",
}


def test_recovery_checklist_covers_all_ai_beh_relation_outputs() -> None:
    checklist = get_ai_beh_relation_recovery_checklist()

    assert len(checklist) == 3
    assert {item.notebook_output for item in checklist} == set(EXPECTED_OUTPUTS)


def test_recovery_checklist_is_conservative_and_evidence_backed() -> None:
    checklist = get_ai_beh_relation_recovery_checklist()

    for item in checklist:
        assert item.source_status == "exact_source_found"
        assert item.authoritative_source_available is True
        assert item.expected_formula_summary == (
            f"{item.notebook_output[:-4]} = {EXPECTED_OUTPUTS[item.notebook_output]}."
        )
        assert item.runtime_output_verified is False
        assert item.notebook_value_parity_verified is False
        assert item.target_mode != "public_shared"
        assert item.http_servable is False


def test_recovery_formula_fields_are_locked_to_expected_inputs() -> None:
    checklist = get_ai_beh_relation_recovery_checklist()

    for item in checklist:
        assert item.expected_input_outputs == (
            "S2:B3",
            "S2:B4",
            "S2:B8",
            "S2:B11",
            "S2:B12",
        )
        assert item.expected_dtype == "unknown"
        assert item.implementation_status == "requires_reference_output"


def test_recovery_report_writes_and_parses(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    report_path = write_ai_beh_relation_recovery_report(run_dir, "run-4h5")

    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == run_dir / "manifests" / "ai_beh_relation_recovery_report.json"
    assert payload["run_id"] == "run-4h5"
    assert payload["phase_4h5_formula_changes"] is False
    assert len(payload["items"]) == 3


def test_recovery_report_stays_under_run_dir(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"

    with pytest.raises(ValueError):
        write_ai_beh_relation_recovery_report(
            run_dir,
            "run-4h5",
            report_relative_path="../escape.json",
        )


def test_recovery_report_does_not_create_tif_or_npy(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    write_ai_beh_relation_recovery_report(run_dir, "run-4h5")

    assert not list(run_dir.rglob("*.tif"))
    assert not list(run_dir.rglob("*.npy"))


def test_allowed_enums_are_enforced() -> None:
    with pytest.raises(ValueError):
        AIBehRelationRecoveryItem(
            id="bad-source",
            notebook_output="AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif",
            family="AI_BEH semantic rasters",
            current_app_status="missing",
            source_status="bad",
            authoritative_source_available=True,
            source_reference="ref",
            expected_input_outputs=(),
            expected_formula_summary="formula",
            expected_dtype="unknown",
            expected_units="unknown",
            expected_nodata_policy="unknown",
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="notebook-parity semantic raster stage",
            http_servable=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="requires_reference_output",
            blocker="blocker",
            recommended_next_action="next",
            notes="notes",
        )

    with pytest.raises(ValueError):
        AIBehRelationRecoveryItem(
            id="bad-impl",
            notebook_output="AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif",
            family="AI_BEH semantic rasters",
            current_app_status="missing",
            source_status="exact_source_found",
            authoritative_source_available=True,
            source_reference="ref",
            expected_input_outputs=(),
            expected_formula_summary="formula",
            expected_dtype="unknown",
            expected_units="unknown",
            expected_nodata_policy="unknown",
            required_reference_outputs=(),
            required_metadata=(),
            target_mode="notebook_parity",
            classification="notebook-parity semantic raster stage",
            http_servable=False,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            implementation_status="bad",
            blocker="blocker",
            recommended_next_action="next",
            notes="notes",
        )

    assert "exact_source_found" in ALLOWED_SOURCE_STATUSES
    assert "requires_reference_output" in ALLOWED_IMPLEMENTATION_STATUSES
