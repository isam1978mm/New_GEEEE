from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.dataset_pack_readiness import ALLOWED_READINESS_STATUSES


FUTURE_SLICE_09_H2_SCHEMA_VERSION = "future_slice_09_h2_ml_dependency_sandbox_v1"
FUTURE_SLICE_09_H2_REPORT_RELATIVE_PATH = (
    "manifests/future_slice_09_h2_ml_dependency_sandbox.json"
)
FUTURE_SLICE_09_SANDBOX_ID = "future_slice_09_h2_ml_dependency_sandbox"

# A ready I2 dataset pack is the gate that must pass before training can be
# considered. The literal is validated against the I2 readiness status set so the
# two slices stay in sync.
READY_DATASET_STATUS = "ready_for_private_training_later"
assert READY_DATASET_STATUS in ALLOWED_READINESS_STATUSES

ALLOWED_SANDBOX_STATUSES = {
    "sandbox_design_only",
    "allowed_later_optional_extra",
    "blocked_no_ready_dataset",
    "blocked_base_dependency_change",
    "blocked_api_frontend_dependency",
    "blocked_eager_import",
    "blocked_missing_weights_policy",
    "blocked_training_gate",
    "blocked_inference_gate",
}

ALLOWED_SANDBOX_INTENTS = {
    "design_only",
    "optional_extra_dependency",
    "training",
    "inference",
    "weights_download",
}

OPTIONAL_DEPENDENCY_GROUP = "optional_extra"
REQUIRED_WEIGHTS_POLICY_FIELDS = ("source", "license", "sha256", "model_card")

# Informational only. These are recorded as packages that must not become required
# base-app dependencies. This module does not import any of them.
FORBIDDEN_BASE_PACKAGES = (
    "torch",
    "tensorflow",
    "cuda",
    "keras",
    "ultralytics",
    "segmentation_models_pytorch",
)


@dataclass(frozen=True)
class MlDependencySandboxResult:
    report_path: Path
    proposed_sandbox_status: str
    results: tuple[dict[str, Any], ...]
    payload: dict[str, Any]


def get_h2_sandbox_rules() -> dict[str, Any]:
    """Return the H2 optional ML dependency sandbox policy rules."""

    return {
        "base_app_must_remain_ml_free": True,
        "optional_ml_dependency_group_allowed_later_only": True,
        "optional_dependency_group_name": OPTIONAL_DEPENDENCY_GROUP,
        "eager_import_at_startup_forbidden": True,
        "api_frontend_ml_dependency_forbidden": True,
        "cli_private_first": True,
        "training_requires_ready_i2_dataset": True,
        "ready_dataset_status_required": READY_DATASET_STATUS,
        "inference_requires_training_evaluation_or_approved_weight_validation": True,
        "weights_download_requires_policy": list(REQUIRED_WEIGHTS_POLICY_FIELDS),
        "training_remains_blocked_in_h2": True,
        "inference_remains_blocked_in_h2": True,
        "weights_download_remains_blocked_in_h2": True,
        "forbidden_base_packages": list(FORBIDDEN_BASE_PACKAGES),
        "h3_training_blocked": True,
        "h4_private_inference_blocked": True,
    }


def check_ml_dependency_sandbox(
    proposed_sandbox: Mapping[str, Any],
    *,
    dataset_readiness_status: str | None = None,
) -> tuple[str, list[str]]:
    """Return the H2 status and blockers for one proposed sandbox.

    This is a pure policy check. It does not add dependencies, import ML packages,
    train, run inference, or download weights.
    """

    blockers: list[str] = []
    intent = str(proposed_sandbox.get("intent", "design_only"))
    if intent not in ALLOWED_SANDBOX_INTENTS:
        blockers.append("unsupported_intent")
        return "blocked_base_dependency_change", blockers

    # Structural gates apply to every intent and take precedence.
    if _changes_base_dependencies(proposed_sandbox):
        blockers.append("base_app_dependency_change_is_forbidden")
        return "blocked_base_dependency_change", blockers
    if _imports_at_startup(proposed_sandbox):
        blockers.append("eager_import_at_app_startup_is_forbidden")
        return "blocked_eager_import", blockers
    if _has_api_frontend_dependency(proposed_sandbox):
        blockers.append("api_or_frontend_dependency_on_ml_packages_is_forbidden")
        return "blocked_api_frontend_dependency", blockers

    if intent == "weights_download":
        if not _weights_policy_complete(proposed_sandbox.get("weights_policy")):
            blockers.append("weights_policy_incomplete_source_license_hash_model_card_required")
            return "blocked_missing_weights_policy", blockers
        # Even with a complete policy, downloading weights is a later approved slice.
        return "allowed_later_optional_extra", blockers

    if intent == "training":
        if dataset_readiness_status != READY_DATASET_STATUS:
            blockers.append("training_requires_a_ready_i2_dataset_pack")
            return "blocked_no_ready_dataset", blockers
        blockers.append("training_is_blocked_in_h2_and_deferred_to_a_later_h3_slice")
        return "blocked_training_gate", blockers

    if intent == "inference":
        blockers.append(
            "inference_requires_a_trained_evaluated_model_or_approved_weight_validation"
        )
        return "blocked_inference_gate", blockers

    if intent == "optional_extra_dependency":
        return "allowed_later_optional_extra", blockers

    return "sandbox_design_only", blockers


def evaluate_ml_dependency_sandbox(
    *,
    run_dir: str | Path,
    run_id: str,
    proposed_sandboxes: Iterable[Mapping[str, Any]] | None = None,
    dataset_readiness_status: str | None = None,
    report_relative_path: str | Path = FUTURE_SLICE_09_H2_REPORT_RELATIVE_PATH,
) -> MlDependencySandboxResult:
    """Evaluate proposed ML dependency sandboxes and write a private H2 report.

    This is sandbox readiness/policy only. It does not add ML dependencies, train,
    run inference, download weights, create datasets, call Earth Engine, or expose
    anything publicly.
    """

    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    proposals = tuple(proposed_sandboxes or ())
    results: list[dict[str, Any]] = []
    for index, proposal in enumerate(proposals):
        status, blockers = check_ml_dependency_sandbox(
            proposal, dataset_readiness_status=dataset_readiness_status
        )
        results.append(
            {
                "index": index,
                "label": str(proposal.get("label", f"proposed_sandbox_{index}")),
                "intent": str(proposal.get("intent", "design_only")),
                "status": status,
                "blockers": blockers,
            }
        )

    overall_status = _overall_status([str(item["status"]) for item in results])
    counts = _counts_by_status([str(item["status"]) for item in results])

    payload = {
        "schema_version": FUTURE_SLICE_09_H2_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "sandbox_id": FUTURE_SLICE_09_SANDBOX_ID,
        "rules": get_h2_sandbox_rules(),
        "results": results,
        "proposed_sandbox_status": overall_status,
        "counts_by_status": counts,
        "dataset_readiness_status_input": dataset_readiness_status or "not_provided",
        "base_app_dependency_changes_allowed": False,
        "ml_dependencies_added": False,
        "training_added": False,
        "inference_added": False,
        "weights_downloaded": False,
        "dataset_created": False,
        "public_exposure_changes": False,
        "artifact_generation": False,
        "notes": (
            "Future Slice 09 (H2) defines the optional ML dependency sandbox policy and "
            "checks proposed sandboxes against it. The base app stays free of required ML "
            "packages. Optional ML dependency groups are allowed only in a later approved "
            "slice after the I2 dataset gate passes. Training and inference stay blocked."
        ),
    }
    if overall_status not in ALLOWED_SANDBOX_STATUSES:
        raise ValueError(f"unsupported sandbox status: {overall_status}")

    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return MlDependencySandboxResult(
        report_path=report_path,
        proposed_sandbox_status=overall_status,
        results=tuple(results),
        payload=payload,
    )


def _changes_base_dependencies(proposal: Mapping[str, Any]) -> bool:
    if proposal.get("changes_base_dependencies") is True:
        return True
    if proposal.get("required_base_dependency") is True:
        return True
    group = proposal.get("dependency_group")
    if group is not None and str(group) not in {OPTIONAL_DEPENDENCY_GROUP, "design_only"}:
        return True
    return False


def _imports_at_startup(proposal: Mapping[str, Any]) -> bool:
    return bool(
        proposal.get("imported_at_startup")
        or proposal.get("eager_import")
        or proposal.get("imported_at_app_startup")
    )


def _has_api_frontend_dependency(proposal: Mapping[str, Any]) -> bool:
    return bool(
        proposal.get("api_dependency")
        or proposal.get("frontend_dependency")
        or proposal.get("api_frontend_dependency")
    )


def _weights_policy_complete(weights_policy: Any) -> bool:
    if not isinstance(weights_policy, Mapping):
        return False
    for field in REQUIRED_WEIGHTS_POLICY_FIELDS:
        value = weights_policy.get(field)
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
    return True


def _overall_status(statuses: list[str]) -> str:
    if not statuses:
        return "sandbox_design_only"
    blocking_precedence = (
        "blocked_base_dependency_change",
        "blocked_eager_import",
        "blocked_api_frontend_dependency",
        "blocked_missing_weights_policy",
        "blocked_inference_gate",
        "blocked_no_ready_dataset",
        "blocked_training_gate",
    )
    for status in blocking_precedence:
        if status in statuses:
            return status
    if "allowed_later_optional_extra" in statuses:
        return "allowed_later_optional_extra"
    return "sandbox_design_only"


def _counts_by_status(statuses: list[str]) -> dict[str, int]:
    counts = {status: 0 for status in sorted(ALLOWED_SANDBOX_STATUSES)}
    for status in statuses:
        counts[status] += 1
    return counts
