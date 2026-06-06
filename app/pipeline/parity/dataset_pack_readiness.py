from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import tempfile
from typing import Any, Iterable, Mapping

from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.dataset_training_design import (
    DATASET_MANIFEST_FIELDS,
    EVIDENCE_SOURCE_TYPES,
    INDEPENDENT_EVIDENCE_SOURCE_TYPES,
    LABEL_QUALITY_VALUES,
    REVIEWED_TIER_LABEL_QUALITIES,
    TRAINING_EXAMPLE_FIELDS,
    label_record_passes_reviewed_tier_gate,
)


FUTURE_SLICE_08_I2_SCHEMA_VERSION = "future_slice_08_i2_dataset_pack_readiness_v1"
FUTURE_SLICE_08_I2_REPORT_RELATIVE_PATH = (
    "manifests/future_slice_08_i2_dataset_pack_readiness.json"
)

# The I2 dataset manifest extends the I1 manifest fields with the quantitative
# training gates that must exist before training can be considered.
QUANTITATIVE_MANIFEST_FIELDS = (
    "minimum_holdout_size",
    "minimum_reviewed_tier_label_count_per_class",
    "minimum_negative_background_count",
    "minimum_hard_negative_count",
    "preregistered_baseline_margin",
    "primary_metric",
    "threshold_selection_policy",
)
I2_REQUIRED_MANIFEST_FIELDS = (*DATASET_MANIFEST_FIELDS, *QUANTITATIVE_MANIFEST_FIELDS)

ALLOWED_ARTIFACT_CLASSES = ("LOCAL_SENSITIVE", "FILESYSTEM_ONLY")
HOLDOUT_SPLIT_NAMES = ("final_holdout", "temporal_holdout", "holdout")
DEFAULT_NEGATIVE_BACKGROUND_LABELS = ("Class_Negative", "Class_Background")
DEFAULT_HARD_NEGATIVE_LABELS = ("Class_HardNegative",)

ALLOWED_READINESS_STATUSES = {
    "ready_for_private_training_later",
    "not_ready",
    "invalid_manifest",
    "invalid_examples",
    "independent_evidence_missing",
    "split_policy_failed",
    "storage_policy_failed",
    "baseline_policy_missing",
    "insufficient_holdout",
    "insufficient_reviewed_tier_labels",
    "insufficient_negatives",
    "insufficient_hard_negatives",
    "error",
}

_REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class DatasetPackReadinessResult:
    report_path: Path
    dataset_readiness_status: str
    training_allowed: bool
    inference_allowed: bool
    payload: dict[str, Any]


def evaluate_dataset_pack_readiness(
    *,
    dataset_manifest_path: str | Path,
    training_examples_path: str | Path,
    run_dir: str | Path,
    run_id: str,
    allowed_dataset_root: str | Path | None = None,
    validation_config: Mapping[str, Any] | None = None,
    report_relative_path: str | Path = FUTURE_SLICE_08_I2_REPORT_RELATIVE_PATH,
) -> DatasetPackReadinessResult:
    """Validate a private dataset pack and write an I2 readiness report.

    This is dataset-pack readiness/validation only. It does not create or commit a
    real dataset, train, run inference, download data or weights, add ML
    dependencies, call Earth Engine, or expose anything publicly.
    """

    config = dict(validation_config or {})
    negative_labels = set(
        config.get("negative_background_labels", DEFAULT_NEGATIVE_BACKGROUND_LABELS)
    )
    hard_negative_labels = set(
        config.get("hard_negative_labels", DEFAULT_HARD_NEGATIVE_LABELS)
    )

    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    state = _ReadinessState()

    manifest_path_ok = _input_path_is_local_safe(
        dataset_manifest_path, allowed_dataset_root
    )
    examples_path_ok = _input_path_is_local_safe(
        training_examples_path, allowed_dataset_root
    )
    if not manifest_path_ok or not examples_path_ok:
        state.status = "error"
        state.blockers.append(
            "input_path_rejected: paths must be local, free of traversal, and must not "
            "be public URLs"
        )

    manifest: dict[str, Any] | None = None
    if state.status is None:
        manifest, manifest_present = _load_manifest(Path(dataset_manifest_path), state)
        state.dataset_manifest_present = manifest_present

    examples: list[dict[str, Any]] | None = None
    if state.status is None:
        examples, examples_present = _load_examples(Path(training_examples_path), state)
        state.training_examples_present = examples_present

    if state.status is None and manifest is not None and examples is not None:
        _evaluate_gates(
            manifest=manifest,
            examples=examples,
            negative_labels=negative_labels,
            hard_negative_labels=hard_negative_labels,
            state=state,
        )

    if state.status is None:
        state.status = "ready_for_private_training_later"

    dataset_id = ""
    if isinstance(manifest, Mapping):
        raw_id = manifest.get("dataset_id")
        if isinstance(raw_id, str):
            dataset_id = raw_id

    training_allowed = state.status == "ready_for_private_training_later"
    payload = {
        "schema_version": FUTURE_SLICE_08_I2_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_id": dataset_id,
        "dataset_manifest_present": state.dataset_manifest_present,
        "training_examples_present": state.training_examples_present,
        "dataset_readiness_status": state.status,
        "training_allowed": training_allowed,
        "inference_allowed": False,
        "independent_evidence_status": state.gate_status["independent_evidence"],
        "reviewed_tier_label_count_status": state.gate_status["reviewed_tier_label_count"],
        "split_policy_status": state.gate_status["split_policy"],
        "temporal_holdout_status": state.gate_status["temporal_holdout"],
        "negative_sampling_status": state.gate_status["negative_sampling"],
        "hard_negative_status": state.gate_status["hard_negative"],
        "holdout_size_status": state.gate_status["holdout_size"],
        "baseline_margin_status": state.gate_status["baseline_margin"],
        "storage_policy_status": state.gate_status["storage_policy"],
        "manifest_hash_status": state.gate_status["manifest_hash"],
        "content_hash_status": state.gate_status["content_hash"],
        "counts_by_label_quality": state.counts_by_label_quality,
        "counts_by_evidence_source_type": state.counts_by_evidence_source_type,
        "counts_by_split": state.counts_by_split,
        "class_prevalence_by_split": state.class_prevalence_by_split,
        "blockers": list(state.blockers),
        "next_actions": _next_actions(state.status),
        "i2_dataset_pack_validation_only": True,
        "dataset_created": False,
        "training_added": False,
        "inference_added": False,
        "weights_downloaded": False,
        "ml_dependencies_added": False,
        "public_exposure_changes": False,
        "artifact_generation": False,
        "notes": (
            "Future Slice 08 (I2) validates a private dataset pack against the binding "
            "data gates and writes a private readiness report. It does not create or "
            "commit a real dataset, train, run inference, or expose data. Datasets stay "
            "outside git and remain LOCAL_SENSITIVE or FILESYSTEM_ONLY."
        ),
    }
    if state.status not in ALLOWED_READINESS_STATUSES:
        raise ValueError(f"unsupported readiness status: {state.status}")

    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return DatasetPackReadinessResult(
        report_path=report_path,
        dataset_readiness_status=state.status,
        training_allowed=training_allowed,
        inference_allowed=False,
        payload=payload,
    )


class _ReadinessState:
    def __init__(self) -> None:
        self.status: str | None = None
        self.dataset_manifest_present = False
        self.training_examples_present = False
        self.blockers: list[str] = []
        self.gate_status: dict[str, str] = {
            "independent_evidence": "not_checked",
            "reviewed_tier_label_count": "not_checked",
            "split_policy": "not_checked",
            "temporal_holdout": "not_checked",
            "negative_sampling": "not_checked",
            "hard_negative": "not_checked",
            "holdout_size": "not_checked",
            "baseline_margin": "not_checked",
            "storage_policy": "not_checked",
            "manifest_hash": "not_checked",
            "content_hash": "not_checked",
        }
        self.counts_by_label_quality: dict[str, int] = {}
        self.counts_by_evidence_source_type: dict[str, int] = {}
        self.counts_by_split: dict[str, int] = {}
        self.class_prevalence_by_split: dict[str, dict[str, float]] = {}

    def fail(self, status: str, blocker: str, *, gate: str | None = None) -> None:
        if gate is not None:
            self.gate_status[gate] = "fail"
        self.blockers.append(blocker)
        if self.status is None:
            self.status = status


def _input_path_is_local_safe(
    path: str | Path,
    allowed_dataset_root: str | Path | None,
) -> bool:
    raw = str(path)
    if "://" in raw:
        return False
    candidate = Path(path)
    if ".." in candidate.parts:
        return False
    if allowed_dataset_root is not None:
        try:
            candidate.resolve().relative_to(Path(allowed_dataset_root).resolve())
        except ValueError:
            return False
    return True


def _load_manifest(
    manifest_path: Path,
    state: _ReadinessState,
) -> tuple[dict[str, Any] | None, bool]:
    if not manifest_path.is_file():
        state.fail("invalid_manifest", "dataset_manifest_missing")
        return None, False
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state.fail("invalid_manifest", "dataset_manifest_unreadable")
        return None, True
    if not isinstance(payload, Mapping):
        state.fail("invalid_manifest", "dataset_manifest_not_an_object")
        return None, True

    missing = [field for field in I2_REQUIRED_MANIFEST_FIELDS if not _has_value(payload, field)]
    state.gate_status["manifest_hash"] = (
        "present" if _has_value(payload, "dataset_manifest_hash") else "missing"
    )
    state.gate_status["content_hash"] = (
        "present" if _has_value(payload, "dataset_content_hash") else "missing"
    )
    if missing:
        state.fail(
            "invalid_manifest",
            "dataset_manifest_missing_required_fields:" + ",".join(sorted(missing)),
        )
        return dict(payload), True
    return dict(payload), True


def _load_examples(
    examples_path: Path,
    state: _ReadinessState,
) -> tuple[list[dict[str, Any]] | None, bool]:
    if not examples_path.is_file():
        state.fail("invalid_examples", "training_examples_missing")
        return None, False
    try:
        lines = examples_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        state.fail("invalid_examples", "training_examples_unreadable")
        return None, True

    records: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            record = json.loads(stripped)
        except ValueError:
            state.fail("invalid_examples", f"training_example_unparsable_line:{index}")
            return None, True
        if not isinstance(record, Mapping):
            state.fail("invalid_examples", f"training_example_not_an_object_line:{index}")
            return None, True
        missing = [field for field in TRAINING_EXAMPLE_FIELDS if field not in record]
        if missing:
            state.fail(
                "invalid_examples",
                f"training_example_missing_fields_line:{index}",
            )
            return None, True
        if record.get("label_quality") not in LABEL_QUALITY_VALUES:
            state.fail("invalid_examples", f"training_example_bad_label_quality_line:{index}")
            return None, True
        if record.get("evidence_source_type") not in EVIDENCE_SOURCE_TYPES:
            state.fail("invalid_examples", f"training_example_bad_evidence_type_line:{index}")
            return None, True
        records.append(dict(record))

    if not records:
        state.fail("invalid_examples", "training_examples_empty")
        return None, True
    return records, True


def _evaluate_gates(
    *,
    manifest: Mapping[str, Any],
    examples: list[dict[str, Any]],
    negative_labels: set[str],
    hard_negative_labels: set[str],
    state: _ReadinessState,
) -> None:
    _compute_counts(examples, state)

    _check_storage_policy(manifest, state)
    _check_baseline_margin(manifest, state)
    _check_independent_evidence(examples, state)
    _check_split_policy(manifest, examples, state)
    _check_reviewed_tier_counts(
        manifest, examples, negative_labels, hard_negative_labels, state
    )
    _check_holdout_size(manifest, examples, state)
    _check_negative_sampling(
        manifest, examples, negative_labels, hard_negative_labels, state
    )


def _check_storage_policy(manifest: Mapping[str, Any], state: _ReadinessState) -> None:
    artifact_class = manifest.get("artifact_class")
    storage_path = manifest.get("storage_path_outside_git")
    problems: list[str] = []
    if artifact_class not in ALLOWED_ARTIFACT_CLASSES:
        problems.append("artifact_class_not_local_sensitive_or_filesystem_only")
    if manifest.get("filesystem_only") is not True:
        problems.append("filesystem_only_must_be_true")
    if manifest.get("http_servable") is not False:
        problems.append("http_servable_must_be_false")
    if manifest.get("frontend_visible") is not False:
        problems.append("frontend_visible_must_be_false")
    if manifest.get("downloadable_via_api") is not False:
        problems.append("downloadable_via_api_must_be_false")
    if not _storage_path_outside_git(storage_path):
        problems.append("storage_path_must_be_outside_repo_or_pytest_tmp")

    if problems:
        state.fail(
            "storage_policy_failed",
            "storage_policy_failed:" + ",".join(problems),
            gate="storage_policy",
        )
    else:
        state.gate_status["storage_policy"] = "ok"


def _check_baseline_margin(manifest: Mapping[str, Any], state: _ReadinessState) -> None:
    margin = manifest.get("preregistered_baseline_margin")
    if isinstance(margin, bool) or not isinstance(margin, (int, float)):
        state.fail(
            "baseline_policy_missing",
            "preregistered_baseline_margin_missing_or_non_numeric",
            gate="baseline_margin",
        )
        return
    state.gate_status["baseline_margin"] = "present"


def _check_independent_evidence(
    examples: list[dict[str, Any]], state: _ReadinessState
) -> None:
    reviewed_claimed = [
        example
        for example in examples
        if example.get("label_quality") in REVIEWED_TIER_LABEL_QUALITIES
    ]
    valid_reviewed = [
        example
        for example in reviewed_claimed
        if label_record_passes_reviewed_tier_gate(
            label_quality=str(example.get("label_quality", "")),
            evidence_source_type=str(example.get("evidence_source_type", "")),
            label_evidence_source=str(example.get("label_evidence_source", "")),
        )
    ]
    invalid_reviewed = [
        example for example in reviewed_claimed if example not in valid_reviewed
    ]
    if invalid_reviewed:
        state.fail(
            "independent_evidence_missing",
            "reviewed_tier_label_without_independent_evidence",
            gate="independent_evidence",
        )
        return
    if not valid_reviewed:
        state.fail(
            "independent_evidence_missing",
            "no_reviewed_tier_labels_with_independent_evidence",
            gate="independent_evidence",
        )
        return
    state.gate_status["independent_evidence"] = "ok"


def _check_split_policy(
    manifest: Mapping[str, Any],
    examples: list[dict[str, Any]],
    state: _ReadinessState,
) -> None:
    problems: list[str] = []

    group_to_splits: dict[str, set[str]] = {}
    for example in examples:
        group_key = str(example.get("group_id") or example.get("area_id") or "")
        split = str(example.get("split", ""))
        group_to_splits.setdefault(group_key, set()).add(split)
    if any(len(splits) > 1 for splits in group_to_splits.values()):
        problems.append("group_or_area_leakage_across_splits")

    holdout_count = sum(
        1 for example in examples if str(example.get("split", "")) in HOLDOUT_SPLIT_NAMES
    )
    if holdout_count == 0:
        state.gate_status["temporal_holdout"] = "missing"
        problems.append("temporal_holdout_missing")
    else:
        state.gate_status["temporal_holdout"] = "present"

    if not _threshold_policy_avoids_holdout(manifest.get("threshold_selection_policy")):
        problems.append("threshold_selection_uses_final_holdout")

    if problems:
        state.fail(
            "split_policy_failed",
            "split_policy_failed:" + ",".join(problems),
            gate="split_policy",
        )
    else:
        state.gate_status["split_policy"] = "ok"


def _check_reviewed_tier_counts(
    manifest: Mapping[str, Any],
    examples: list[dict[str, Any]],
    negative_labels: set[str],
    hard_negative_labels: set[str],
    state: _ReadinessState,
) -> None:
    minimum = _as_non_negative_int(
        manifest.get("minimum_reviewed_tier_label_count_per_class")
    )
    if minimum is None:
        state.fail(
            "insufficient_reviewed_tier_labels",
            "minimum_reviewed_tier_label_count_per_class_missing_or_invalid",
            gate="reviewed_tier_label_count",
        )
        return

    excluded = negative_labels | hard_negative_labels
    counts: dict[str, int] = {}
    for example in examples:
        label = str(example.get("label", ""))
        if label in excluded:
            continue
        if label_record_passes_reviewed_tier_gate(
            label_quality=str(example.get("label_quality", "")),
            evidence_source_type=str(example.get("evidence_source_type", "")),
            label_evidence_source=str(example.get("label_evidence_source", "")),
        ):
            counts[label] = counts.get(label, 0) + 1

    if not counts or any(count < minimum for count in counts.values()):
        state.fail(
            "insufficient_reviewed_tier_labels",
            "reviewed_tier_label_count_below_minimum_per_class",
            gate="reviewed_tier_label_count",
        )
        return
    state.gate_status["reviewed_tier_label_count"] = "ok"


def _check_holdout_size(
    manifest: Mapping[str, Any],
    examples: list[dict[str, Any]],
    state: _ReadinessState,
) -> None:
    minimum = _as_non_negative_int(manifest.get("minimum_holdout_size"))
    if minimum is None:
        state.fail(
            "insufficient_holdout",
            "minimum_holdout_size_missing_or_invalid",
            gate="holdout_size",
        )
        return
    holdout_count = sum(
        1 for example in examples if str(example.get("split", "")) in HOLDOUT_SPLIT_NAMES
    )
    if holdout_count < minimum:
        state.fail(
            "insufficient_holdout",
            "holdout_size_below_minimum",
            gate="holdout_size",
        )
        return
    state.gate_status["holdout_size"] = "ok"


def _check_negative_sampling(
    manifest: Mapping[str, Any],
    examples: list[dict[str, Any]],
    negative_labels: set[str],
    hard_negative_labels: set[str],
    state: _ReadinessState,
) -> None:
    negative_minimum = _as_non_negative_int(manifest.get("minimum_negative_background_count"))
    hard_minimum = _as_non_negative_int(manifest.get("minimum_hard_negative_count"))

    hard_count = sum(
        1 for example in examples if str(example.get("label", "")) in hard_negative_labels
    )
    negative_count = (
        sum(1 for example in examples if str(example.get("label", "")) in negative_labels)
        + hard_count
    )

    if negative_minimum is None or negative_count < negative_minimum:
        state.fail(
            "insufficient_negatives",
            "negative_background_count_below_minimum_or_minimum_invalid",
            gate="negative_sampling",
        )
    else:
        state.gate_status["negative_sampling"] = "ok"

    if hard_minimum is None or hard_count < hard_minimum:
        state.fail(
            "insufficient_hard_negatives",
            "hard_negative_count_below_minimum_or_minimum_invalid",
            gate="hard_negative",
        )
    else:
        state.gate_status["hard_negative"] = "ok"


def _compute_counts(examples: list[dict[str, Any]], state: _ReadinessState) -> None:
    label_quality: dict[str, int] = {}
    evidence_type: dict[str, int] = {}
    split_counts: dict[str, int] = {}
    split_label_counts: dict[str, dict[str, int]] = {}
    for example in examples:
        quality = str(example.get("label_quality", ""))
        evidence = str(example.get("evidence_source_type", ""))
        split = str(example.get("split", ""))
        label = str(example.get("label", ""))
        label_quality[quality] = label_quality.get(quality, 0) + 1
        evidence_type[evidence] = evidence_type.get(evidence, 0) + 1
        split_counts[split] = split_counts.get(split, 0) + 1
        split_label_counts.setdefault(split, {})
        split_label_counts[split][label] = split_label_counts[split].get(label, 0) + 1

    prevalence: dict[str, dict[str, float]] = {}
    for split, labels in split_label_counts.items():
        total = sum(labels.values())
        if total == 0:
            continue
        prevalence[split] = {
            label: round(count / total, 6) for label, count in sorted(labels.items())
        }

    state.counts_by_label_quality = dict(sorted(label_quality.items()))
    state.counts_by_evidence_source_type = dict(sorted(evidence_type.items()))
    state.counts_by_split = dict(sorted(split_counts.items()))
    state.class_prevalence_by_split = dict(sorted(prevalence.items()))


def _threshold_policy_avoids_holdout(policy: Any) -> bool:
    if isinstance(policy, Mapping):
        if policy.get("uses_final_holdout") is True:
            return False
        selected_on = policy.get("selected_on")
        if isinstance(selected_on, Iterable) and not isinstance(selected_on, (str, bytes)):
            selected = {str(item) for item in selected_on}
            if selected & set(HOLDOUT_SPLIT_NAMES):
                return False
        return True
    if isinstance(policy, str):
        return "holdout" not in policy.lower()
    return False


def _storage_path_outside_git(storage_path: Any) -> bool:
    if not isinstance(storage_path, str) or not storage_path.strip():
        return False
    if "://" in storage_path:
        return False
    resolved = Path(storage_path).resolve()
    if _is_pytest_tmp_path(resolved):
        return True
    try:
        resolved.relative_to(_REPO_ROOT)
    except ValueError:
        return True
    return False


def _is_pytest_tmp_path(path: Path) -> bool:
    text = str(path).lower()
    if "pytest" in text:
        return True
    try:
        path.relative_to(Path(tempfile.gettempdir()).resolve())
        return True
    except ValueError:
        return False


def _has_value(payload: Mapping[str, Any], field: str) -> bool:
    if field not in payload:
        return False
    value = payload[field]
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _as_non_negative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _next_actions(status: str) -> list[str]:
    if status == "ready_for_private_training_later":
        return [
            "Keep the dataset pack private and outside git.",
            "Proceed to a later approved training slice only after the H2 dependency "
            "sandbox and the preregistered baseline gate are in place.",
        ]
    return [
        "Resolve the recorded blockers before training can be considered.",
        "Supply independent evidence-backed labels and complete the manifest gates.",
        "Keep datasets, labels, chips, and coordinate-bearing metadata outside git.",
    ]
