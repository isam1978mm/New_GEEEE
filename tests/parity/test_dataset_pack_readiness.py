from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import app.pipeline.parity.dataset_pack_readiness as module
from app.pipeline.parity.dataset_pack_readiness import (
    FUTURE_SLICE_08_I2_SCHEMA_VERSION,
    evaluate_dataset_pack_readiness,
)


FORBIDDEN_ARTIFACT_SUFFIXES = {
    ".tif",
    ".tiff",
    ".npy",
    ".geojson",
    ".kmz",
    ".kml",
    ".html",
    ".png",
    ".jpg",
    ".jpeg",
    ".pt",
    ".pth",
    ".onnx",
    ".h5",
    ".pkl",
    ".joblib",
    ".parquet",
}

_FAKE_MANIFEST_HASH = "manifesthash_aabbccddeeff"
_FAKE_CONTENT_HASH = "contenthash_aabbccddeeff"


def _claim_terms() -> tuple[str, ...]:
    return (
        "con" + "firmed",
        "fou" + "nd",
        "pro" + "ven",
        "dig" + " target",
        "def" + "initely",
        "disc" + "overy",
        "burial " + "pro" + "ven",
        "tomb " + "con" + "firmed",
        "target " + "con" + "firmed",
    )


def _wording_violation(content: str, term: str) -> bool:
    if " " in term:
        return term in content
    return re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", content) is not None


def _example(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": "training_example_v1",
        "sample_id": "sample_0001",
        "dataset_id": "dataset_demo_v1",
        "area_id": "area_001",
        "group_id": "group_001",
        "chip_id": "chip_001",
        "split": "train",
        "label": "Class_A",
        "label_quality": "reviewed_independent",
        "label_evidence_source": "external_reference_v1:item_1",
        "evidence_source_type": "field_validation",
        "evidence_source_version": "external_reference_v1",
        "evidence_review_method": "direct_match_to_external_reference",
        "reviewer_or_source_reference": "reviewer_1",
        "acquisition_window": "2025-01-01_to_2025-03-31",
        "sensor_sources": ["s2", "s1"],
        "grid_version": "local_grid_v1",
        "preprocessing_commit": "abc123",
        "features_ref": "features/sample_0001.json",
        "metadata_ref": "metadata/sample_0001.json",
        "redaction_class": "LOCAL_SENSITIVE",
        "notes": "",
    }
    base.update(overrides)
    return base


def _valid_examples() -> list[dict[str, object]]:
    return [
        _example(sample_id="s1", group_id="g1", split="train", label="Class_A"),
        _example(sample_id="s2", group_id="g2", split="final_holdout", label="Class_A"),
        _example(sample_id="s3", group_id="g3", split="train", label="Class_Negative"),
        _example(sample_id="s4", group_id="g4", split="train", label="Class_HardNegative"),
    ]


def _manifest(storage_path: str, **overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "dataset_id": "dataset_demo_v1",
        "schema_version": "dataset_pack_v1",
        "created_at": "2026-01-01T00:00:00Z",
        "build_commit": "abc123",
        "build_command_or_procedure": "build_dataset_pack.py",
        "dataset_manifest_hash": _FAKE_MANIFEST_HASH,
        "dataset_content_hash": _FAKE_CONTENT_HASH,
        "split_seed": 12345,
        "split_policy_version": "split_policy_v1",
        "data_source_list": ["s2", "s1", "dem"],
        "label_source_list": ["external_reference_v1"],
        "label_evidence_source_counts": {"field_validation": 4},
        "label_quality_counts": {"reviewed_independent": 4},
        "class_prevalence_by_split": {"train": {"Class_A": 0.34}},
        "storage_path_outside_git": storage_path,
        "artifact_class": "FILESYSTEM_ONLY",
        "filesystem_only": True,
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
        "redaction_policy": "redact coordinate proxies",
        "dataset_card_ref": "dataset_card.md",
        "known_limitations": "tiny demo pack",
        "intended_use": "private research",
        "unacceptable_use": "public targeting",
        "misuse_review_status": "reviewed",
        "minimum_holdout_size": 1,
        "minimum_reviewed_tier_label_count_per_class": 1,
        "minimum_negative_background_count": 1,
        "minimum_hard_negative_count": 1,
        "preregistered_baseline_margin": 0.05,
        "primary_metric": "pr_auc",
        "threshold_selection_policy": {
            "selected_on": ["train", "validation"],
            "uses_final_holdout": False,
        },
    }
    base.update(overrides)
    return base


def _run(
    tmp_path: Path,
    *,
    manifest: dict[str, object] | None,
    examples: list[dict[str, object]] | None,
    storage_path: str | None = None,
    run_id: str = "i2-test",
    write_manifest: bool = True,
    write_examples: bool = True,
):
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    storage = storage_path if storage_path is not None else str(tmp_path / "dataset_storage")

    manifest_path = pack_dir / "dataset_manifest.json"
    examples_path = pack_dir / "training_examples.jsonl"

    resolved_manifest = manifest if manifest is not None else _manifest(storage)
    if write_manifest:
        manifest_path.write_text(json.dumps(resolved_manifest), encoding="utf-8")

    resolved_examples = examples if examples is not None else _valid_examples()
    if write_examples:
        examples_path.write_text(
            "\n".join(json.dumps(record) for record in resolved_examples),
            encoding="utf-8",
        )

    return evaluate_dataset_pack_readiness(
        dataset_manifest_path=manifest_path,
        training_examples_path=examples_path,
        run_dir=tmp_path / "run",
        run_id=run_id,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------
def test_valid_tiny_pack_is_ready_only_when_all_gates_pass(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    result = _run(tmp_path, manifest=_manifest(storage), examples=_valid_examples())

    assert result.dataset_readiness_status == "ready_for_private_training_later"
    assert result.training_allowed is True
    assert result.inference_allowed is False
    assert result.payload["independent_evidence_status"] == "ok"
    assert result.payload["storage_policy_status"] == "ok"
    assert result.payload["split_policy_status"] == "ok"


# ---------------------------------------------------------------------------
# Manifest / examples presence
# ---------------------------------------------------------------------------
def test_missing_manifest_returns_invalid_manifest(tmp_path: Path) -> None:
    result = _run(tmp_path, manifest=None, examples=_valid_examples(), write_manifest=False)
    assert result.dataset_readiness_status in {"invalid_manifest", "not_ready"}
    assert result.payload["dataset_manifest_present"] is False
    assert result.training_allowed is False


def test_missing_examples_returns_invalid_examples(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    result = _run(
        tmp_path, manifest=_manifest(storage), examples=None, write_examples=False
    )
    assert result.dataset_readiness_status in {"invalid_examples", "not_ready"}
    assert result.payload["training_examples_present"] is False


# ---------------------------------------------------------------------------
# Independent evidence
# ---------------------------------------------------------------------------
def test_reviewed_tier_label_without_independent_evidence_fails(tmp_path: Path) -> None:
    examples = _valid_examples()
    examples[0]["label_evidence_source"] = ""
    result = _run(tmp_path, manifest=None, examples=examples)
    assert result.dataset_readiness_status == "independent_evidence_missing"


def test_unknown_or_missing_evidence_fails_reviewed_tier(tmp_path: Path) -> None:
    examples = _valid_examples()
    for record in examples:
        record["evidence_source_type"] = "unknown_or_missing"
    result = _run(tmp_path, manifest=None, examples=examples)
    assert result.dataset_readiness_status == "independent_evidence_missing"


def test_weak_label_does_not_count_as_reviewed_tier(tmp_path: Path) -> None:
    examples = _valid_examples()
    for record in examples:
        record["label_quality"] = "weak_label"
        record["evidence_source_type"] = "weak_heuristic_hint"
    result = _run(tmp_path, manifest=None, examples=examples)
    assert result.dataset_readiness_status == "independent_evidence_missing"


# ---------------------------------------------------------------------------
# Manifest field gates
# ---------------------------------------------------------------------------
def test_missing_dataset_id_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    manifest = _manifest(storage)
    del manifest["dataset_id"]
    result = _run(tmp_path, manifest=manifest, examples=_valid_examples())
    assert result.dataset_readiness_status == "invalid_manifest"


def test_missing_dataset_manifest_hash_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    manifest = _manifest(storage)
    del manifest["dataset_manifest_hash"]
    result = _run(tmp_path, manifest=manifest, examples=_valid_examples())
    assert result.dataset_readiness_status == "invalid_manifest"
    assert result.payload["manifest_hash_status"] == "missing"


def test_missing_dataset_content_hash_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    manifest = _manifest(storage)
    del manifest["dataset_content_hash"]
    result = _run(tmp_path, manifest=manifest, examples=_valid_examples())
    assert result.dataset_readiness_status == "invalid_manifest"
    assert result.payload["content_hash_status"] == "missing"


# ---------------------------------------------------------------------------
# Storage policy
# ---------------------------------------------------------------------------
def test_invalid_artifact_class_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    result = _run(
        tmp_path, manifest=_manifest(storage, artifact_class="PUBLIC"), examples=_valid_examples()
    )
    assert result.dataset_readiness_status == "storage_policy_failed"


def test_http_servable_true_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    result = _run(
        tmp_path, manifest=_manifest(storage, http_servable=True), examples=_valid_examples()
    )
    assert result.dataset_readiness_status == "storage_policy_failed"


def test_frontend_visible_true_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    result = _run(
        tmp_path, manifest=_manifest(storage, frontend_visible=True), examples=_valid_examples()
    )
    assert result.dataset_readiness_status == "storage_policy_failed"


def test_downloadable_via_api_true_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    result = _run(
        tmp_path,
        manifest=_manifest(storage, downloadable_via_api=True),
        examples=_valid_examples(),
    )
    assert result.dataset_readiness_status == "storage_policy_failed"


def test_storage_path_inside_repo_fails_unless_pytest_tmp(tmp_path: Path) -> None:
    inside_repo = str(module._REPO_ROOT / "i2_inside_repo_dataset_should_fail")
    result = _run(
        tmp_path, manifest=_manifest(inside_repo), examples=_valid_examples()
    )
    assert result.dataset_readiness_status == "storage_policy_failed"


# ---------------------------------------------------------------------------
# Split / leakage / temporal holdout / threshold
# ---------------------------------------------------------------------------
def test_group_leakage_across_splits_fails(tmp_path: Path) -> None:
    examples = _valid_examples()
    examples[1]["group_id"] = "g1"  # same group as a train example, but in final_holdout
    result = _run(tmp_path, manifest=None, examples=examples)
    assert result.dataset_readiness_status == "split_policy_failed"


def test_temporal_holdout_missing_fails(tmp_path: Path) -> None:
    examples = _valid_examples()
    examples[1]["split"] = "train"  # remove the only holdout example
    result = _run(tmp_path, manifest=None, examples=examples)
    assert result.dataset_readiness_status == "split_policy_failed"
    assert result.payload["temporal_holdout_status"] == "missing"


def test_threshold_policy_using_holdout_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    manifest = _manifest(
        storage,
        threshold_selection_policy={
            "selected_on": ["train", "final_holdout"],
            "uses_final_holdout": True,
        },
    )
    result = _run(tmp_path, manifest=manifest, examples=_valid_examples())
    assert result.dataset_readiness_status == "split_policy_failed"


# ---------------------------------------------------------------------------
# Quantitative gates
# ---------------------------------------------------------------------------
def test_holdout_below_minimum_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    manifest = _manifest(storage, minimum_holdout_size=5)
    result = _run(tmp_path, manifest=manifest, examples=_valid_examples())
    assert result.dataset_readiness_status == "insufficient_holdout"


def test_missing_preregistered_baseline_margin_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    # Present but non-numeric so the manifest field check passes and the baseline gate fires.
    manifest = _manifest(storage, preregistered_baseline_margin="unset")
    result = _run(tmp_path, manifest=manifest, examples=_valid_examples())
    assert result.dataset_readiness_status == "baseline_policy_missing"


def test_insufficient_reviewed_tier_labels_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    manifest = _manifest(storage, minimum_reviewed_tier_label_count_per_class=5)
    result = _run(tmp_path, manifest=manifest, examples=_valid_examples())
    assert result.dataset_readiness_status == "insufficient_reviewed_tier_labels"


def test_insufficient_negative_background_count_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    manifest = _manifest(storage, minimum_negative_background_count=10)
    result = _run(tmp_path, manifest=manifest, examples=_valid_examples())
    assert result.dataset_readiness_status == "insufficient_negatives"


def test_insufficient_hard_negative_count_fails(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    manifest = _manifest(storage, minimum_hard_negative_count=10)
    result = _run(tmp_path, manifest=manifest, examples=_valid_examples())
    assert result.dataset_readiness_status == "insufficient_hard_negatives"


# ---------------------------------------------------------------------------
# Report shape, path, and redaction
# ---------------------------------------------------------------------------
def test_valid_report_writes_and_parses_under_run_dir(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    result = _run(tmp_path, manifest=_manifest(storage), examples=_valid_examples())
    run_dir = tmp_path / "run"

    payload = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert result.report_path == (
        run_dir / "manifests" / "future_slice_08_i2_dataset_pack_readiness.json"
    )
    assert result.report_path.resolve().is_relative_to(run_dir.resolve())
    assert payload["schema_version"] == FUTURE_SLICE_08_I2_SCHEMA_VERSION
    assert payload["i2_dataset_pack_validation_only"] is True
    assert payload["dataset_created"] is False
    assert payload["training_added"] is False
    assert payload["inference_added"] is False
    assert payload["weights_downloaded"] is False
    assert payload["ml_dependencies_added"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["artifact_generation"] is False
    required_fields = {
        "schema_version",
        "run_id",
        "created_at",
        "dataset_id",
        "dataset_manifest_present",
        "training_examples_present",
        "dataset_readiness_status",
        "training_allowed",
        "inference_allowed",
        "independent_evidence_status",
        "reviewed_tier_label_count_status",
        "split_policy_status",
        "temporal_holdout_status",
        "negative_sampling_status",
        "hard_negative_status",
        "holdout_size_status",
        "baseline_margin_status",
        "storage_policy_status",
        "manifest_hash_status",
        "content_hash_status",
        "counts_by_label_quality",
        "counts_by_evidence_source_type",
        "counts_by_split",
        "class_prevalence_by_split",
        "blockers",
        "next_actions",
    }
    assert required_fields <= set(payload)


def test_report_contains_no_local_paths_coordinates_or_private_hashes(tmp_path: Path) -> None:
    storage = str(tmp_path / "private_dataset_storage_PATHTOKEN")
    examples = _valid_examples()
    examples[0]["area_id"] = "lat35p55823_lon36p14443"
    manifest = _manifest(storage)
    result = _run(tmp_path, manifest=manifest, examples=examples)

    text = result.report_path.read_text(encoding="utf-8")
    assert str(tmp_path) not in text
    assert "PATHTOKEN" not in text
    assert _FAKE_MANIFEST_HASH not in text
    assert _FAKE_CONTENT_HASH not in text
    assert "lat35p55823_lon36p14443" not in text


def test_url_input_path_is_rejected(tmp_path: Path) -> None:
    result = evaluate_dataset_pack_readiness(
        dataset_manifest_path="https://example.com/manifest.json",
        training_examples_path=str(tmp_path / "pack" / "training_examples.jsonl"),
        run_dir=tmp_path / "run",
        run_id="i2-url",
    )
    assert result.dataset_readiness_status == "error"
    assert result.training_allowed is False


def test_report_creates_no_dataset_or_disallowed_artifacts(tmp_path: Path) -> None:
    storage = str(tmp_path / "dataset_storage")
    _run(tmp_path, manifest=_manifest(storage), examples=_valid_examples())
    run_dir = tmp_path / "run"

    created = [
        path
        for path in run_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created == []
    # The validator must not write into the dataset storage location.
    assert not (tmp_path / "dataset_storage").exists()


# ---------------------------------------------------------------------------
# Safety boundaries
# ---------------------------------------------------------------------------
def test_module_adds_no_heavy_ml_runtime_pipeline_or_public_hooks() -> None:
    source = inspect.getsource(module)
    lowered = source.lower()

    assert "import torch" not in source
    assert "import tensorflow" not in source
    assert "keras" not in lowered
    assert "import cuda" not in lowered
    assert "ultralytics" not in lowered
    assert "segmentation_models_pytorch" not in lowered
    assert "urlretrieve" not in lowered
    assert "requests.get" not in lowered
    assert "urllib" not in lowered
    assert "serve_artifact_response" not in source
    assert "can_serve_artifact" not in source
    assert "FileResponse" not in source
    assert "StreamingResponse" not in source
    assert "APIRouter" not in source
    assert "BackgroundTasks" not in source
    assert "enqueue_core_pipeline_run" not in source
    assert "run_core_pipeline" not in source
    assert "ee.Authenticate" not in source
    assert "import ee" not in source
    assert "earthengine" not in lowered
    assert "google.colab" not in source
    assert "drive.mount" not in source
    assert "/content/drive" not in source


def test_readiness_doc_and_module_avoid_claim_wording() -> None:
    paths = (
        Path("app/pipeline/parity/dataset_pack_readiness.py"),
        Path("docs/FUTURE_SLICE_08_I2_PRIVATE_DATASET_PACK_READINESS.md"),
    )
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in paths if path.exists()
    )
    assert all(not _wording_violation(combined, term) for term in _claim_terms())
