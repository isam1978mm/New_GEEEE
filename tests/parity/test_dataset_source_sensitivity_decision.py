from __future__ import annotations

import inspect
import json
from pathlib import Path
import re

from app.services.redaction import verify_redacted


REQUIRED_DECISION_FIELDS = {
    "candidate_id",
    "source_name",
    "prior_review_reference",
    "gate_name",
    "sensitivity_decision",
    "sensitivity_status",
    "misuse_risk_level",
    "sensitive_data_categories",
    "public_summary",
    "decision_rationale_redacted",
    "allowed_next_state",
    "final_decision",
    "h3_training_allowed",
    "h4_inference_allowed",
    "i2_routing_allowed",
    "dataset_downloaded",
    "dataset_created",
    "i2_pack_created",
    "training_added",
    "inference_added",
    "public_exposure_changes",
    "notes",
}


def _decision_record(sensitivity_decision: str) -> dict[str, object]:
    from app.pipeline.parity.dataset_source_review import (
        get_first_candidate_source_review_record,
    )
    from app.pipeline.parity.dataset_source_sensitivity_decision import (
        build_dafa_ls_sensitivity_decision_record,
    )

    return build_dafa_ls_sensitivity_decision_record(
        prior_review=get_first_candidate_source_review_record(
            reviewer="pytest",
            review_date="2026-06-07",
        ),
        sensitivity_decision=sensitivity_decision,
    )


def test_sensitivity_reject_blocks_i2_and_marks_rejected() -> None:
    record = _decision_record("sensitivity_reject")

    assert set(record) == REQUIRED_DECISION_FIELDS
    assert record["candidate_id"] == "dafa_ls_arxiv_2409_09432"
    assert record["gate_name"] == "sensitivity_misuse"
    assert record["sensitivity_status"] == "reject"
    assert record["i2_routing_allowed"] is False
    assert record["final_decision"] == "rejected"
    assert record["allowed_next_state"] == "rejected"


def test_sensitivity_needs_restricted_human_governance_blocks_i2_and_keeps_under_review() -> None:
    record = _decision_record("sensitivity_needs_restricted_human_governance")

    assert record["sensitivity_status"] == "needs_human_review"
    assert record["i2_routing_allowed"] is False
    assert record["final_decision"] == "under_review"
    assert record["allowed_next_state"] == "under_review"


def test_sensitivity_pass_with_restrictions_does_not_allow_h3_h4_or_i2_yet() -> None:
    record = _decision_record("sensitivity_pass_with_restrictions")

    assert record["sensitivity_status"] == "pass"
    assert record["i2_routing_allowed"] is False
    assert record["final_decision"] == "under_review"
    assert record["allowed_next_state"] == "gate_2_to_6_review_required"
    assert record["h3_training_allowed"] is False
    assert record["h4_inference_allowed"] is False


def test_no_sensitivity_decision_allows_h3_h4_or_public_exposure() -> None:
    for decision in (
        "sensitivity_reject",
        "sensitivity_needs_restricted_human_governance",
        "sensitivity_pass_with_restrictions",
    ):
        record = _decision_record(decision)

        assert record["h3_training_allowed"] is False
        assert record["h4_inference_allowed"] is False
        assert record["public_exposure_changes"] is False


def test_default_dafa_ls_decision_is_rejected_and_redacted() -> None:
    from app.pipeline.parity.dataset_source_sensitivity_decision import (
        get_default_dafa_ls_sensitivity_decision_record,
    )

    record = get_default_dafa_ls_sensitivity_decision_record()

    assert record["candidate_id"] == "dafa_ls_arxiv_2409_09432"
    assert record["sensitivity_decision"] == "sensitivity_reject"
    assert record["final_decision"] == "rejected"
    assert record["h3_training_allowed"] is False
    assert record["h4_inference_allowed"] is False
    verify_redacted(record)


def test_report_writes_parses_and_stays_under_run_dir(tmp_path: Path) -> None:
    from app.pipeline.parity.dataset_source_sensitivity_decision import (
        write_dafa_ls_sensitivity_decision_report,
    )

    run_dir = tmp_path / "run"
    report_path = write_dafa_ls_sensitivity_decision_report(
        run_dir=run_dir,
        run_id="run-13c",
    )

    assert report_path.resolve().is_relative_to(run_dir.resolve())
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "future_slice_13c_dafa_ls_sensitivity_v1"
    assert payload["run_id"] == "run-13c"
    assert payload["sensitivity_decision_record"]["final_decision"] == "rejected"
    assert payload["h3_training_allowed"] is False
    assert payload["h4_inference_allowed"] is False
    assert payload["i2_routing_allowed"] is False
    assert payload["dataset_downloaded"] is False
    assert payload["dataset_created"] is False
    assert payload["i2_pack_created"] is False
    assert payload["training_added"] is False
    assert payload["inference_added"] is False
    assert payload["public_exposure_changes"] is False


def test_report_contains_no_sensitive_payload(tmp_path: Path) -> None:
    from app.pipeline.parity.dataset_source_sensitivity_decision import (
        write_dafa_ls_sensitivity_decision_report,
    )

    report_path = write_dafa_ls_sensitivity_decision_report(
        run_dir=tmp_path / "run",
        run_id="run-13c",
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


def test_report_does_not_create_dataset_or_i2_pack_files(tmp_path: Path) -> None:
    from app.pipeline.parity.dataset_source_sensitivity_decision import (
        write_dafa_ls_sensitivity_decision_report,
    )

    run_dir = tmp_path / "run"
    write_dafa_ls_sensitivity_decision_report(
        run_dir=run_dir,
        run_id="run-13c",
    )

    created_files = [path for path in run_dir.rglob("*") if path.is_file()]
    assert [path.name for path in created_files] == [
        "future_slice_13c_dafa_ls_sensitivity_decision.json"
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


def test_no_web_earth_engine_ml_training_inference_api_or_frontend_logic_exists() -> None:
    import app.pipeline.parity.dataset_source_sensitivity_decision as module

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
        "fi" + "t(",
        "pre" + "dict(",
        "inf" + "er(",
        "train_" + "model",
        "run_" + "inference",
        "fast" + "api",
        "apirouter",
        "react",
        "jsx",
        "tsx",
        "serve_" + "artifact_response",
    ]
    for term in blocked_terms:
        assert term not in source


def test_no_forbidden_certainty_wording_is_present() -> None:
    import app.pipeline.parity.dataset_source_sensitivity_decision as module

    sources = [
        inspect.getsource(module).lower(),
        Path("docs/FUTURE_SLICE_13C_DAFA_LS_SENSITIVITY_DECISION.md").read_text(
            encoding="utf-8"
        ).lower()
        if Path("docs/FUTURE_SLICE_13C_DAFA_LS_SENSITIVITY_DECISION.md").exists()
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
