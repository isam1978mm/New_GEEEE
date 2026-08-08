from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "run_icesat2_epa_hidden_lane_campaign_014_with_saved_relevance_evidence.py"
)
SPEC = importlib.util.spec_from_file_location("campaign014_saved_evidence", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

RESOURCE = "ATL08_20210504235905_06291102_007_01.h5"


def _write(path: Path, payload) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _control_row(**overrides):
    row = {
        "resource": RESOURCE,
        "date": "2021-05-04",
        "target_track_id": 629,
        "returned_track_ids": [629],
        "target_track_present": True,
        "decision": "target_track_intersects_campaign_bounds",
    }
    row.update(overrides)
    return row


def _epa_row(**overrides):
    row = {
        "resource": RESOURCE,
        "date": "2021-05-04",
        "target_track_id": 629,
        "returned_track_ids": [],
        "target_track_present": False,
        "decision": "target_track_absent_from_exact_epa_envelope",
    }
    row.update(overrides)
    return row


def test_saved_evidence_proves_off_site_with_exact_matching_rows(tmp_path):
    control_path = _write(tmp_path / "control.json", [_control_row()])
    epa_path = _write(tmp_path / "epa.json", [_epa_row()])

    proven, proof = MODULE._saved_relevance_proof(
        RESOURCE,
        control_summary_path=control_path,
        epa_summary_path=epa_path,
    )

    assert proven is True
    assert proof["rgt"] == 629
    assert proof["control_track_present"] is True
    assert proof["epa_envelope_track_present"] is False


def test_missing_saved_summary_fails_closed(tmp_path):
    epa_path = _write(tmp_path / "epa.json", [_epa_row()])

    with pytest.raises(MODULE.Campaign014SavedEvidenceError, match="missing saved"):
        MODULE._saved_relevance_proof(
            RESOURCE,
            control_summary_path=tmp_path / "missing.json",
            epa_summary_path=epa_path,
        )


def test_wrong_rgt_has_no_exact_match(tmp_path):
    control_path = _write(tmp_path / "control.json", [_control_row(target_track_id=187)])
    epa_path = _write(tmp_path / "epa.json", [_epa_row()])

    with pytest.raises(MODULE.Campaign014SavedEvidenceError, match="0 exact matches"):
        MODULE._saved_relevance_proof(
            RESOURCE,
            control_summary_path=control_path,
            epa_summary_path=epa_path,
        )


def test_missing_positive_control_does_not_prove_off_site(tmp_path):
    control_path = _write(
        tmp_path / "control.json",
        [_control_row(target_track_present=False, returned_track_ids=[])],
    )
    epa_path = _write(tmp_path / "epa.json", [_epa_row()])

    proven, _proof = MODULE._saved_relevance_proof(
        RESOURCE,
        control_summary_path=control_path,
        epa_summary_path=epa_path,
    )

    assert proven is False


def test_epa_presence_does_not_prove_off_site(tmp_path):
    control_path = _write(tmp_path / "control.json", [_control_row()])
    epa_path = _write(
        tmp_path / "epa.json",
        [
            _epa_row(
                target_track_present=True,
                returned_track_ids=[629],
                decision="target_track_crosses_exact_epa_envelope_but_atl08_unavailable",
            )
        ],
    )

    proven, _proof = MODULE._saved_relevance_proof(
        RESOURCE,
        control_summary_path=control_path,
        epa_summary_path=epa_path,
    )

    assert proven is False


def test_install_saved_evidence_recovery_changes_only_relevance_hook():
    original = MODULE.control.site._failed_resource_is_proven_off_site
    try:
        MODULE.install_saved_evidence_recovery()
        assert (
            MODULE.control.site._failed_resource_is_proven_off_site
            is MODULE._failed_resource_is_proven_off_site_from_saved_evidence
        )
    finally:
        MODULE.control.site._failed_resource_is_proven_off_site = original
