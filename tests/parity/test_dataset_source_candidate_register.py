from __future__ import annotations

import inspect
import json
from pathlib import Path
import re
import tempfile
from uuid import uuid4

import pytest

from app.pipeline.parity import ParityPathError
from app.pipeline.parity.dataset_source_candidate_register import (
    CANDIDATE_RECORD_FIELDS,
    CANDIDATE_REVIEW_GATE_NAMES,
    CANDIDATE_STATUS_VALUES,
    initialize_private_candidate_register,
    get_candidate_record_schema,
    write_candidate_register_scaffold_report,
)
from app.services.redaction import verify_redacted


REQUIRED_CANDIDATE_FIELDS = {
    "candidate_id",
    "source_name",
    "source_reference",
    "source_url_or_doi",
    "source_type",
    "lead_status",
    "review_status",
    "sensitivity_status",
    "sensitivity_decision",
    "sensitivity_blocker",
    "independence_status",
    "independence_decision",
    "independence_blocker",
    "provenance_status",
    "provenance_decision",
    "provenance_blocker",
    "license_status",
    "license_decision",
    "license_blocker",
    "storage_status",
    "storage_decision",
    "storage_blocker",
    "i2_compatibility_status",
    "i2_compatibility_decision",
    "i2_compatibility_blocker",
    "final_decision",
    "final_blocker",
    "reviewer",
    "review_date",
    "notes",
}

EXPECTED_PRIVATE_REGISTER_ENTRIES = {
    Path("candidate_register"),
    Path("candidate_register/candidates.jsonl"),
    Path("candidate_register/reviews"),
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _outside_private_root() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(
        prefix=f"new_gee_slice_13a_{uuid4().hex}_",
    )


def _relative_entries(root: Path) -> set[Path]:
    return {path.relative_to(root) for path in root.rglob("*")}


def test_private_root_inside_repo_is_rejected(tmp_path: Path) -> None:
    private_root = _repo_root() / "private_candidate_register_test"

    with pytest.raises(ValueError, match="outside"):
        initialize_private_candidate_register(
            private_root=private_root,
            repo_root=_repo_root(),
        )


def test_private_root_outside_repo_is_accepted() -> None:
    with _outside_private_root() as private_root_text:
        result = initialize_private_candidate_register(
            private_root=Path(private_root_text),
            repo_root=_repo_root(),
        )

        assert result.private_root_status == "outside_repo"
        assert result.register_dir.is_dir()
        assert result.candidates_file.is_file()
        assert result.reviews_dir.is_dir()


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ParityPathError):
        initialize_private_candidate_register(
            private_root=Path("..") / "private_dataset_root",
            repo_root=_repo_root(),
        )


def test_scaffold_creates_only_expected_empty_structure() -> None:
    with _outside_private_root() as private_root_text:
        private_root = Path(private_root_text)

        result = initialize_private_candidate_register(
            private_root=private_root,
            repo_root=_repo_root(),
        )

        assert _relative_entries(private_root) == EXPECTED_PRIVATE_REGISTER_ENTRIES
        assert result.candidates_file.read_text(encoding="utf-8") == ""


def test_scaffold_creates_no_dataset_label_chip_mask_imagery_or_coordinate_files() -> None:
    blocked_name_fragments = (
        "dataset",
        "label",
        "chip",
        "mask",
        "imagery",
        "coordinate",
        "site_list",
    )
    blocked_suffixes = {".tif", ".tiff", ".npy", ".png", ".jpg", ".jpeg", ".csv"}

    with _outside_private_root() as private_root_text:
        private_root = Path(private_root_text)
        initialize_private_candidate_register(
            private_root=private_root,
            repo_root=_repo_root(),
        )

        created_files = [path for path in private_root.rglob("*") if path.is_file()]
        assert created_files == [private_root / "candidate_register" / "candidates.jsonl"]
        for path in created_files:
            lowered_name = path.name.lower()
            assert path.suffix.lower() not in blocked_suffixes
            assert not any(fragment in lowered_name for fragment in blocked_name_fragments)


def test_candidate_schema_includes_slice_13_checklist_fields() -> None:
    schema = get_candidate_record_schema()

    assert set(CANDIDATE_RECORD_FIELDS) == REQUIRED_CANDIDATE_FIELDS
    assert set(schema["fields"]) == REQUIRED_CANDIDATE_FIELDS
    assert schema["no_real_candidate_data"] is True
    assert schema["storage_boundary"] == "outside_git_private_root"


def test_lifecycle_values_are_exactly_approved_values() -> None:
    assert CANDIDATE_STATUS_VALUES == (
        "unverified_lead",
        "under_review",
        "rejected",
        "conditionally_approved_for_I2",
    )


def test_six_gate_names_are_present() -> None:
    assert CANDIDATE_REVIEW_GATE_NAMES == (
        "sensitivity_misuse",
        "independent_evidence",
        "provenance_labeling_method",
        "license_access_terms",
        "storage_redaction",
        "i2_validator_compatibility",
    )


def test_redacted_summary_contains_no_paths_coordinates_or_private_hashes() -> None:
    with _outside_private_root() as private_root_text:
        result = initialize_private_candidate_register(
            private_root=Path(private_root_text),
            repo_root=_repo_root(),
        )

        summary = result.redacted_summary
        verify_redacted(summary)
        serialized = json.dumps(summary, sort_keys=True).lower()
        assert str(private_root_text).lower() not in serialized
        assert "private_root" not in serialized
        assert "local_path" not in serialized
        assert "coordinate" not in serialized
        assert "latitude" not in serialized
        assert "longitude" not in serialized
        assert "hash" not in serialized
        assert "candidate_contents" not in serialized


def test_report_writes_and_parses(tmp_path: Path) -> None:
    with _outside_private_root() as private_root_text:
        result = initialize_private_candidate_register(
            private_root=Path(private_root_text),
            repo_root=_repo_root(),
        )

        report_path = write_candidate_register_scaffold_report(
            run_dir=tmp_path / "run",
            run_id="run-13a",
            scaffold_result=result,
        )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "future_slice_13a_candidate_register_scaffold_v1"
    assert payload["run_id"] == "run-13a"
    assert payload["candidate_register_scaffold_only"] is True
    assert payload["dataset_created"] is False
    assert payload["candidate_data_created"] is False
    assert payload["public_exposure_changes"] is False


def test_report_path_stays_under_run_dir(tmp_path: Path) -> None:
    with _outside_private_root() as private_root_text:
        result = initialize_private_candidate_register(
            private_root=Path(private_root_text),
            repo_root=_repo_root(),
        )
        run_dir = tmp_path / "run"

        report_path = write_candidate_register_scaffold_report(
            run_dir=run_dir,
            run_id="run-13a",
            scaffold_result=result,
        )

    assert report_path.resolve().is_relative_to(run_dir.resolve())


def test_no_web_earth_engine_ml_training_or_inference_logic_exists() -> None:
    import app.pipeline.parity.dataset_source_candidate_register as module

    source = inspect.getsource(module)
    lowered = source.lower()

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
        assert term not in lowered


def test_no_forbidden_certainty_wording_is_present() -> None:
    import app.pipeline.parity.dataset_source_candidate_register as module

    source = inspect.getsource(module).lower()
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
    for pattern in forbidden_patterns:
        assert re.search(pattern, source) is None
