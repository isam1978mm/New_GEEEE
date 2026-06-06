from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import app.pipeline.parity.ml_dependency_sandbox as module
from app.pipeline.parity.ml_dependency_sandbox import (
    ALLOWED_SANDBOX_STATUSES,
    FUTURE_SLICE_09_H2_SCHEMA_VERSION,
    READY_DATASET_STATUS,
    check_ml_dependency_sandbox,
    evaluate_ml_dependency_sandbox,
    get_h2_sandbox_rules,
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
    ".csv",
    ".jsonl",
    ".pt",
    ".pth",
    ".onnx",
    ".h5",
    ".pkl",
    ".joblib",
    ".parquet",
}

DEPENDENCY_FILE_CANDIDATES = (
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "setup.cfg",
    "setup.py",
    "poetry.lock",
    "uv.lock",
)


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


# ---------------------------------------------------------------------------
# Pure checker behavior
# ---------------------------------------------------------------------------
def test_base_app_dependency_changes_are_rejected() -> None:
    status, blockers = check_ml_dependency_sandbox(
        {"intent": "optional_extra_dependency", "changes_base_dependencies": True}
    )
    assert status == "blocked_base_dependency_change"
    assert blockers


def test_required_base_dependency_group_is_rejected() -> None:
    status, _ = check_ml_dependency_sandbox(
        {"intent": "optional_extra_dependency", "dependency_group": "base"}
    )
    assert status == "blocked_base_dependency_change"


def test_optional_extra_only_policy_is_documented() -> None:
    rules = get_h2_sandbox_rules()
    assert rules["base_app_must_remain_ml_free"] is True
    assert rules["optional_ml_dependency_group_allowed_later_only"] is True
    assert rules["optional_dependency_group_name"] == "optional_extra"
    status, _ = check_ml_dependency_sandbox(
        {"intent": "optional_extra_dependency", "dependency_group": "optional_extra"}
    )
    assert status == "allowed_later_optional_extra"


def test_eager_ml_imports_are_rejected() -> None:
    status, _ = check_ml_dependency_sandbox(
        {"intent": "optional_extra_dependency", "imported_at_startup": True}
    )
    assert status == "blocked_eager_import"


def test_api_frontend_dependency_on_ml_packages_is_rejected() -> None:
    status, _ = check_ml_dependency_sandbox(
        {"intent": "optional_extra_dependency", "api_frontend_dependency": True}
    )
    assert status == "blocked_api_frontend_dependency"


def test_training_without_ready_i2_dataset_is_rejected() -> None:
    status, _ = check_ml_dependency_sandbox(
        {"intent": "training"}, dataset_readiness_status="not_ready"
    )
    assert status == "blocked_no_ready_dataset"

    status_none, _ = check_ml_dependency_sandbox({"intent": "training"})
    assert status_none == "blocked_no_ready_dataset"


def test_training_with_ready_dataset_still_blocked_in_h2() -> None:
    status, _ = check_ml_dependency_sandbox(
        {"intent": "training"}, dataset_readiness_status=READY_DATASET_STATUS
    )
    assert status == "blocked_training_gate"


def test_inference_without_validation_is_rejected() -> None:
    status, _ = check_ml_dependency_sandbox({"intent": "inference"})
    assert status == "blocked_inference_gate"


def test_weight_download_without_policy_is_rejected() -> None:
    status, _ = check_ml_dependency_sandbox({"intent": "weights_download"})
    assert status == "blocked_missing_weights_policy"

    incomplete, _ = check_ml_dependency_sandbox(
        {
            "intent": "weights_download",
            "weights_policy": {"source": "approved_repo", "license": "permissive"},
        }
    )
    assert incomplete == "blocked_missing_weights_policy"


def test_design_only_proposal_is_design_only() -> None:
    status, _ = check_ml_dependency_sandbox({"intent": "design_only"})
    assert status == "sandbox_design_only"


# ---------------------------------------------------------------------------
# Report behavior
# ---------------------------------------------------------------------------
def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    result = evaluate_ml_dependency_sandbox(
        run_dir=run_dir,
        run_id="future-slice-09",
        proposed_sandboxes=(
            {"intent": "optional_extra_dependency", "dependency_group": "optional_extra"},
            {"intent": "training"},
        ),
        dataset_readiness_status="not_ready",
    )
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))

    assert result.report_path == (
        run_dir / "manifests" / "future_slice_09_h2_ml_dependency_sandbox.json"
    )
    assert result.report_path.resolve().is_relative_to(run_dir.resolve())
    assert payload["schema_version"] == FUTURE_SLICE_09_H2_SCHEMA_VERSION
    assert payload["sandbox_id"] == "future_slice_09_h2_ml_dependency_sandbox"
    assert payload["base_app_dependency_changes_allowed"] is False
    assert payload["ml_dependencies_added"] is False
    assert payload["training_added"] is False
    assert payload["inference_added"] is False
    assert payload["weights_downloaded"] is False
    assert payload["dataset_created"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["artifact_generation"] is False
    assert payload["proposed_sandbox_status"] in ALLOWED_SANDBOX_STATUSES
    assert set(payload["counts_by_status"]) == ALLOWED_SANDBOX_STATUSES
    required_fields = {
        "schema_version",
        "run_id",
        "created_at",
        "sandbox_id",
        "rules",
        "proposed_sandbox_status",
        "counts_by_status",
        "notes",
    }
    assert required_fields <= set(payload)


def test_report_with_no_proposals_is_design_only(tmp_path: Path) -> None:
    result = evaluate_ml_dependency_sandbox(
        run_dir=tmp_path / "run",
        run_id="future-slice-09-empty",
    )
    assert result.proposed_sandbox_status == "sandbox_design_only"


def test_report_creates_no_dataset_model_weight_or_artifact_files(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    evaluate_ml_dependency_sandbox(
        run_dir=run_dir,
        run_id="future-slice-09-no-artifacts",
        proposed_sandboxes=({"intent": "design_only"},),
    )
    created = [
        path
        for path in run_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created == []


# ---------------------------------------------------------------------------
# Safety boundaries
# ---------------------------------------------------------------------------
def test_no_dependency_files_were_modified_by_this_slice() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    for name in DEPENDENCY_FILE_CANDIDATES:
        path = repo_root / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        assert "ml_dependency_sandbox" not in text
        assert "future_slice_09" not in text


def test_module_adds_no_heavy_ml_runtime_pipeline_or_public_hooks() -> None:
    source = inspect.getsource(module)
    lowered = source.lower()

    assert "import torch" not in source
    assert "import tensorflow" not in source
    assert "import keras" not in lowered
    assert "import cuda" not in lowered
    assert "import ultralytics" not in lowered
    assert "import segmentation_models_pytorch" not in lowered
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


def test_sandbox_doc_and_module_avoid_claim_wording() -> None:
    paths = (
        Path("app/pipeline/parity/ml_dependency_sandbox.py"),
        Path("docs/FUTURE_SLICE_09_H2_ML_DEPENDENCY_SANDBOX.md"),
    )
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in paths if path.exists()
    )
    assert all(not _wording_violation(combined, term) for term in _claim_terms())
