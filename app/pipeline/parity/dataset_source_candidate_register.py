from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Mapping

from app.pipeline.parity import ParityPathError, resolve_run_output_path


FUTURE_SLICE_13A_SCHEMA_VERSION = "future_slice_13a_candidate_register_scaffold_v1"
FUTURE_SLICE_13A_REPORT_RELATIVE_PATH = (
    "manifests/future_slice_13a_candidate_register_scaffold.json"
)

CANDIDATE_REGISTER_DIR_NAME = "candidate_register"
CANDIDATE_REGISTER_FILE_NAME = "candidates.jsonl"
CANDIDATE_REVIEWS_DIR_NAME = "reviews"

CANDIDATE_STATUS_VALUES = (
    "unverified_lead",
    "under_review",
    "rejected",
    "conditionally_approved_for_I2",
)

CANDIDATE_REVIEW_GATE_NAMES = (
    "sensitivity_misuse",
    "independent_evidence",
    "provenance_labeling_method",
    "license_access_terms",
    "storage_redaction",
    "i2_validator_compatibility",
)

CANDIDATE_RECORD_FIELDS = (
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
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class CandidateRegisterScaffoldResult:
    private_root_status: str
    register_dir: Path
    candidates_file: Path
    reviews_dir: Path
    created_entries: tuple[str, ...]
    redacted_summary: dict[str, object]


def get_candidate_record_schema() -> dict[str, object]:
    return {
        "schema_version": FUTURE_SLICE_13A_SCHEMA_VERSION,
        "fields": list(CANDIDATE_RECORD_FIELDS),
        "lifecycle_values": list(CANDIDATE_STATUS_VALUES),
        "gate_names": list(CANDIDATE_REVIEW_GATE_NAMES),
        "storage_boundary": "outside_git_private_root",
        "artifact_class": "LOCAL_SENSITIVE_OR_FILESYSTEM_ONLY",
        "no_real_candidate_data": True,
    }


def initialize_private_candidate_register(
    *,
    private_root: str | Path,
    repo_root: str | Path | None = None,
) -> CandidateRegisterScaffoldResult:
    root = _validate_private_root(private_root=private_root, repo_root=repo_root)
    register_dir = root / CANDIDATE_REGISTER_DIR_NAME
    candidates_file = register_dir / CANDIDATE_REGISTER_FILE_NAME
    reviews_dir = register_dir / CANDIDATE_REVIEWS_DIR_NAME

    root.mkdir(parents=True, exist_ok=True)
    register_dir.mkdir(exist_ok=True)
    reviews_dir.mkdir(exist_ok=True)
    if candidates_file.exists() and candidates_file.read_text(encoding="utf-8") != "":
        raise ValueError("candidate register scaffold requires an empty candidates file")
    candidates_file.touch(exist_ok=True)

    redacted_summary: dict[str, object] = {
        "schema_version": FUTURE_SLICE_13A_SCHEMA_VERSION,
        "storage_location_status": "outside_repo",
        "candidate_register_scaffold_created": True,
        "candidate_record_count": 0,
        "candidate_data_created": False,
        "dataset_created": False,
        "filesystem_only": True,
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
        "public_exposure_changes": False,
    }
    return CandidateRegisterScaffoldResult(
        private_root_status="outside_repo",
        register_dir=register_dir,
        candidates_file=candidates_file,
        reviews_dir=reviews_dir,
        created_entries=(
            CANDIDATE_REGISTER_DIR_NAME,
            f"{CANDIDATE_REGISTER_DIR_NAME}/{CANDIDATE_REGISTER_FILE_NAME}",
            f"{CANDIDATE_REGISTER_DIR_NAME}/{CANDIDATE_REVIEWS_DIR_NAME}",
        ),
        redacted_summary=redacted_summary,
    )


def write_candidate_register_scaffold_report(
    *,
    run_dir: str | Path,
    run_id: str,
    scaffold_result: CandidateRegisterScaffoldResult,
    report_relative_path: str | Path = FUTURE_SLICE_13A_REPORT_RELATIVE_PATH,
) -> Path:
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "schema_version": FUTURE_SLICE_13A_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "candidate_schema": get_candidate_record_schema(),
        "lifecycle_values": list(CANDIDATE_STATUS_VALUES),
        "gate_names": list(CANDIDATE_REVIEW_GATE_NAMES),
        "scaffold_summary": dict(scaffold_result.redacted_summary),
        "created_entries": list(scaffold_result.created_entries),
        "candidate_register_scaffold_only": True,
        "candidate_data_created": False,
        "dataset_created": False,
        "labels_created": False,
        "chips_created": False,
        "masks_created": False,
        "imagery_created": False,
        "weights_created": False,
        "ml_dependencies_added": False,
        "earth_engine_calls_added": False,
        "public_exposure_changes": False,
        "notes": (
            "Slice 13A creates only an empty private candidate-register scaffold "
            "outside git and records schema metadata for later source review."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _validate_private_root(
    *,
    private_root: str | Path,
    repo_root: str | Path | None,
) -> Path:
    candidate = Path(private_root)
    if ".." in candidate.parts:
        raise ParityPathError("private_root must not contain path traversal")
    if "://" in str(private_root):
        raise ParityPathError("private_root must be a local filesystem path")

    resolved_root = candidate.resolve()
    resolved_repo = Path(repo_root).resolve() if repo_root is not None else _REPO_ROOT
    if _is_relative_to(resolved_root, resolved_repo):
        raise ValueError("private_root must be outside the repository")
    return resolved_root


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
