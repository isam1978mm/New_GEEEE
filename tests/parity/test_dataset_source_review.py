from __future__ import annotations

import inspect
import json
from pathlib import Path
import re

import pytest

from app.pipeline.parity.dataset_source_candidate_register import (
    CANDIDATE_RECORD_FIELDS,
    CANDIDATE_REVIEW_GATE_NAMES,
)
from app.services.redaction import verify_redacted


REQUIRED_REVIEW_FIELDS = set(CANDIDATE_RECORD_FIELDS)
EXPECTED_GATE_STATUS_VALUES = {
    "pass",
    "reject",
    "needs_human_review",
    "insufficient_information",
    "weak_signal_only",
    "not_applicable",
}


def _base_statuses() -> dict[str, str]:
    return {
        "sensitivity_status": "pass",
        "independence_status": "pass",
        "provenance_status": "pass",
        "license_status": "pass",
        "storage_status": "pass",
        "i2_compatibility_status": "pass",
    }


def _review_with_statuses(**overrides: str) -> dict[str, str]:
    from app.pipeline.parity.dataset_source_review import (
        build_candidate_source_review_record,
    )

    statuses = _base_statuses()
    statuses.update(overrides)
    return build_candidate_source_review_record(
        candidate_id="test-lead",
        source_name="Test public metadata lead",
        source_reference="test-reference",
        source_url_or_doi="doi:10.0000/test",
        source_type="public_metadata_lead",
        reviewer="pytest",
        review_date="2026-06-07",
        notes="Metadata-only gate exercise. No payload content is included.",
        **statuses,
    )


def test_review_record_contains_slice_13_candidate_register_fields() -> None:
    from app.pipeline.parity.dataset_source_review import (
        get_first_candidate_source_review_record,
    )

    record = get_first_candidate_source_review_record(
        reviewer="pytest",
        review_date="2026-06-07",
    )

    assert set(record) == REQUIRED_REVIEW_FIELDS


def test_candidate_starts_as_unverified_lead() -> None:
    from app.pipeline.parity.dataset_source_review import (
        get_first_candidate_source_review_record,
    )

    record = get_first_candidate_source_review_record(
        reviewer="pytest",
        review_date="2026-06-07",
    )

    assert record["lead_status"] == "unverified_lead"
    assert record["review_status"] == "under_review"


def test_all_six_gates_are_represented() -> None:
    from app.pipeline.parity.dataset_source_review import summarize_gate_statuses

    record = _review_with_statuses()
    gate_summary = summarize_gate_statuses(record)

    assert tuple(gate_summary) == CANDIDATE_REVIEW_GATE_NAMES
    assert set(gate_summary.values()) <= EXPECTED_GATE_STATUS_VALUES


def test_conditionally_approved_for_i2_requires_all_six_gates_to_pass() -> None:
    approved = _review_with_statuses()

    assert approved["final_decision"] == "conditionally_approved_for_I2"

    blocked_cases = [
        {"sensitivity_status": "reject"},
        {"sensitivity_status": "needs_human_review"},
        {"independence_status": "weak_signal_only"},
        {"independence_status": "reject"},
        {"independence_status": "insufficient_information"},
        {"provenance_status": "insufficient_information"},
        {"provenance_status": "reject"},
        {"license_status": "insufficient_information"},
        {"license_status": "reject"},
        {"storage_status": "reject"},
        {"i2_compatibility_status": "reject"},
        {"i2_compatibility_status": "insufficient_information"},
    ]
    for overrides in blocked_cases:
        record = _review_with_statuses(**overrides)
        assert record["final_decision"] != "conditionally_approved_for_I2"


def test_explicit_approval_is_rejected_when_any_gate_is_not_passed() -> None:
    from app.pipeline.parity.dataset_source_review import (
        build_candidate_source_review_record,
    )

    statuses = _base_statuses()
    statuses["sensitivity_status"] = "needs_human_review"

    with pytest.raises(ValueError, match="six gates"):
        build_candidate_source_review_record(
            candidate_id="test-lead",
            source_name="Test public metadata lead",
            source_reference="test-reference",
            source_url_or_doi="doi:10.0000/test",
            source_type="public_metadata_lead",
            reviewer="pytest",
            review_date="2026-06-07",
            final_decision="conditionally_approved_for_I2",
            notes="Metadata-only gate exercise.",
            **statuses,
        )


def test_dafa_ls_review_records_sensitivity_concern_and_blocks_h3_h4(
    tmp_path: Path,
) -> None:
    from app.pipeline.parity.dataset_source_review import (
        get_first_candidate_source_review_record,
        write_first_source_review_report,
    )

    record = get_first_candidate_source_review_record(
        reviewer="pytest",
        review_date="2026-06-07",
    )
    report_path = write_first_source_review_report(
        run_dir=tmp_path / "run",
        run_id="run-13b",
        candidate_review=record,
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert record["candidate_id"] == "dafa_ls_arxiv_2409_09432"
    assert record["final_decision"] != "conditionally_approved_for_I2"
    assert record["sensitivity_status"] == "needs_human_review"
    assert record["sensitivity_blocker"]
    assert payload["h3_training_allowed"] is False
    assert payload["h4_inference_allowed"] is False


def test_report_writes_parses_and_stays_under_run_dir(tmp_path: Path) -> None:
    from app.pipeline.parity.dataset_source_review import (
        get_first_candidate_source_review_record,
        write_first_source_review_report,
    )

    run_dir = tmp_path / "run"
    report_path = write_first_source_review_report(
        run_dir=run_dir,
        run_id="run-13b",
        candidate_review=get_first_candidate_source_review_record(
            reviewer="pytest",
            review_date="2026-06-07",
        ),
    )

    assert report_path.resolve().is_relative_to(run_dir.resolve())
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "future_slice_13b_first_source_review_v1"
    assert payload["run_id"] == "run-13b"
    assert payload["gates_reviewed"] == list(CANDIDATE_REVIEW_GATE_NAMES)
    assert payload["dataset_downloaded"] is False
    assert payload["dataset_created"] is False
    assert payload["i2_pack_created"] is False
    assert payload["training_added"] is False
    assert payload["inference_added"] is False
    assert payload["ml_dependencies_added"] is False
    assert payload["earth_engine_calls_added"] is False
    assert payload["public_exposure_changes"] is False


def test_report_contains_no_coordinates_geometry_paths_hashes_or_payload(
    tmp_path: Path,
) -> None:
    from app.pipeline.parity.dataset_source_review import (
        get_first_candidate_source_review_record,
        write_first_source_review_report,
    )

    report_path = write_first_source_review_report(
        run_dir=tmp_path / "run",
        run_id="run-13b",
        candidate_review=get_first_candidate_source_review_record(
            reviewer="pytest",
            review_date="2026-06-07",
        ),
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
    from app.pipeline.parity.dataset_source_review import (
        get_first_candidate_source_review_record,
        write_first_source_review_report,
    )

    run_dir = tmp_path / "run"
    write_first_source_review_report(
        run_dir=run_dir,
        run_id="run-13b",
        candidate_review=get_first_candidate_source_review_record(
            reviewer="pytest",
            review_date="2026-06-07",
        ),
    )

    created_files = [path for path in run_dir.rglob("*") if path.is_file()]
    assert [path.name for path in created_files] == [
        "future_slice_13b_first_source_review.json"
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


def test_no_web_earth_engine_ml_training_or_inference_logic_exists() -> None:
    import app.pipeline.parity.dataset_source_review as module

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
    ]
    for term in blocked_terms:
        assert term not in source


def test_no_forbidden_certainty_wording_is_present() -> None:
    import app.pipeline.parity.dataset_source_review as module

    sources = [
        inspect.getsource(module).lower(),
        Path("docs/FUTURE_SLICE_13B_FIRST_SOURCE_REVIEW.md").read_text(
            encoding="utf-8"
        ).lower()
        if Path("docs/FUTURE_SLICE_13B_FIRST_SOURCE_REVIEW.md").exists()
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
