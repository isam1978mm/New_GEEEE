from __future__ import annotations

import inspect
import json
from pathlib import Path
import re

from app.services.redaction import verify_redacted


def test_closeout_includes_current_known_rejected_leads() -> None:
    from app.pipeline.parity.dataset_source_approval_closeout import (
        get_slice_13_source_approval_closeout,
    )

    closeout = get_slice_13_source_approval_closeout()

    assert closeout["known_leads_reviewed"] == [
        "dafa_ls_arxiv_2409_09432",
        "arxiv_2602_19608_looted_sites",
    ]
    assert closeout["rejected_leads"] == [
        "dafa_ls_arxiv_2409_09432",
        "arxiv_2602_19608_looted_sites",
    ]
    assert closeout["deferred_leads"] == []
    assert closeout["conditionally_approved_for_i2"] == []


def test_closeout_blocks_i2_h3_h4_for_current_known_leads() -> None:
    from app.pipeline.parity.dataset_source_approval_closeout import (
        get_slice_13_source_approval_closeout,
    )

    closeout = get_slice_13_source_approval_closeout()

    assert closeout["i2_routing_allowed"] is False
    assert closeout["h3_training_allowed"] is False
    assert closeout["h4_inference_allowed"] is False
    assert closeout["slice_13_current_known_leads_complete"] is True


def test_current_known_lead_decisions_are_redacted_and_gate_1_rejected() -> None:
    from app.pipeline.parity.dataset_source_approval_closeout import (
        get_slice_13_source_approval_closeout,
    )

    closeout = get_slice_13_source_approval_closeout()
    decisions = closeout["current_known_lead_decisions"]

    assert decisions == [
        {
            "candidate_id": "dafa_ls_arxiv_2409_09432",
            "source_name": "DAFA-LS public metadata lead",
            "final_decision": "rejected",
            "blocking_gate": "sensitivity_misuse",
            "i2_routing_allowed": False,
        },
        {
            "candidate_id": "arxiv_2602_19608_looted_sites",
            "source_name": "arXiv 2602.19608 public metadata lead",
            "final_decision": "rejected",
            "blocking_gate": "sensitivity_misuse",
            "i2_routing_allowed": False,
        },
    ]
    verify_redacted(closeout)


def test_future_unknown_candidates_are_not_rejected_by_closeout() -> None:
    from app.pipeline.parity.dataset_source_approval_closeout import (
        get_slice_13_source_approval_closeout,
    )

    closeout = get_slice_13_source_approval_closeout()

    assert closeout["future_unknown_candidates_rejected"] is False
    assert "future_unknown" not in json.dumps(closeout["rejected_leads"])
    assert any(
        "new_candidate" in path
        for path in closeout["next_allowed_paths"]
    )


def test_next_allowed_paths_include_new_candidate_and_operator_evidence() -> None:
    from app.pipeline.parity.dataset_source_approval_closeout import (
        get_slice_13_source_approval_closeout,
    )

    closeout = get_slice_13_source_approval_closeout()

    assert closeout["next_allowed_paths"] == [
        "new_candidate_source_review_under_new_scoped_goal",
        "operator_provided_independent_evidence_under_new_scoped_goal",
        "future_i2_assembly_only_after_a_candidate_passes_all_slice_13_gates",
    ]


def test_report_writes_parses_and_stays_under_run_dir(tmp_path: Path) -> None:
    from app.pipeline.parity.dataset_source_approval_closeout import (
        write_slice_13_source_approval_closeout_report,
    )

    run_dir = tmp_path / "run"
    report_path = write_slice_13_source_approval_closeout_report(
        run_dir=run_dir,
        run_id="run-13e",
    )

    assert report_path.resolve().is_relative_to(run_dir.resolve())
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "future_slice_13e_source_approval_closeout_v1"
    assert payload["run_id"] == "run-13e"
    assert payload["closeout_id"] == "future_slice_13e_current_known_leads"
    assert payload["conditionally_approved_for_i2"] == []
    assert payload["i2_routing_allowed"] is False
    assert payload["h3_training_allowed"] is False
    assert payload["h4_inference_allowed"] is False
    assert payload["slice_13_current_known_leads_complete"] is True
    assert payload["dataset_downloaded"] is False
    assert payload["dataset_created"] is False
    assert payload["i2_pack_created"] is False
    assert payload["training_added"] is False
    assert payload["inference_added"] is False
    assert payload["ml_dependencies_added"] is False
    assert payload["earth_engine_calls_added"] is False
    assert payload["public_exposure_changes"] is False


def test_report_contains_no_sensitive_payload(tmp_path: Path) -> None:
    from app.pipeline.parity.dataset_source_approval_closeout import (
        write_slice_13_source_approval_closeout_report,
    )

    report_path = write_slice_13_source_approval_closeout_report(
        run_dir=tmp_path / "run",
        run_id="run-13e",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    verify_redacted(payload)
    serialized = json.dumps(payload, sort_keys=True).lower()

    forbidden_fragments = (
        "latitude",
        "longitude",
        "coordinate",
        "raw geometry",
        "geometry",
        "site list",
        "site_list",
        "local path",
        "local_path",
        "private hash",
        "private_hash",
        "payload content",
        "archive content",
        str(tmp_path).lower(),
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized


def test_report_creates_no_dataset_or_i2_files(tmp_path: Path) -> None:
    from app.pipeline.parity.dataset_source_approval_closeout import (
        write_slice_13_source_approval_closeout_report,
    )

    run_dir = tmp_path / "run"
    write_slice_13_source_approval_closeout_report(
        run_dir=run_dir,
        run_id="run-13e",
    )

    created_files = [path for path in run_dir.rglob("*") if path.is_file()]
    assert [path.name for path in created_files] == [
        "future_slice_13e_source_approval_closeout.json"
    ]
    blocked_fragments = (
        "dataset_pack",
        "training_examples",
        "label",
        "chip",
        "mask",
        "imagery",
        "site_list",
    )
    for path in created_files:
        lowered = path.name.lower()
        assert not any(fragment in lowered for fragment in blocked_fragments)


def test_no_web_earth_engine_ml_training_or_api_logic_exists() -> None:
    import app.pipeline.parity.dataset_source_approval_closeout as module

    source = inspect.getsource(module).lower()
    blocked_terms = [
        "req" + "uests",
        "url" + "lib",
        "htt" + "px",
        "beautiful" + "soup",
        "scr" + "ape",
        "def down" + "load",
        "down" + "load_file",
        "down" + "load_dataset",
        "ee.authenticate",
        "import " + "ee",
        "earth" + "engine",
        "tor" + "ch",
        "tensor" + "flow",
        "cu" + "da",
        "sk" + "learn",
        "fast" + "api",
        "api" + "router",
        "serve_" + "artifact_response",
        "fi" + "t(",
        "pre" + "dict(",
        "inf" + "er(",
        "train_" + "model",
        "run_" + "inference",
    ]
    for term in blocked_terms:
        assert term not in source


def test_no_forbidden_certainty_wording_is_present() -> None:
    import app.pipeline.parity.dataset_source_approval_closeout as module

    sources = [
        inspect.getsource(module).lower(),
        Path("docs/FUTURE_SLICE_13E_SOURCE_APPROVAL_CLOSEOUT.md").read_text(
            encoding="utf-8"
        ).lower()
        if Path("docs/FUTURE_SLICE_13E_SOURCE_APPROVAL_CLOSEOUT.md").exists()
        else "",
    ]
    forbidden_patterns = [
        "con" + "firmed",
        "fo" + "und",
        r"\b" + "pro" + "ven" + r"\b",
        "dig " + "target",
        "def" + "initely",
        "dis" + "covery",
        "burial " + "pro" + "ven",
        "tomb " + "con" + "firmed",
        "target " + "con" + "firmed",
    ]
    for source in sources:
        for pattern in forbidden_patterns:
            assert re.search(pattern, source) is None
