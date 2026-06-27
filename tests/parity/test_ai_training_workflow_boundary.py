import json

from app.pipeline.parity.ai_training_workflow_boundary import (
    AI_TRAINING_WORKFLOW_SCHEMA_VERSION,
    CLASS_LABELS_10,
    REQUIRED_APPROVAL_GATES,
    SOURCE_CELL,
    TRAINING_SOURCE_CELLS,
    build_plan_b30_ai_training_workflow_payload,
    write_plan_b30_ai_training_workflow_report,
)


def test_plan_b30_selects_cell_166_but_excludes_inference_cells():
    payload = build_plan_b30_ai_training_workflow_payload(run_id="run-30")

    assert payload["source_cell"] == "cell_166"
    assert payload["selected_canonical_training_cell"] == "cell_166"

    cells = payload["training_source_cells"]
    assert cells["cell_166"]["status"] == "selected_policy_source"
    assert cells["cell_150"]["role"] == "dependency_install_probe"
    assert cells["cell_151"]["role"] == "expanded_dependency_install_probe"
    assert cells["cell_167"]["status"] == "excluded_from_item_30"
    assert cells["cell_168"]["status"] == "excluded_from_item_30"
    assert cells["cell_169"]["status"] == "excluded_from_item_30"


def test_plan_b30_payload_is_boundary_only_not_training_execution():
    payload = build_plan_b30_ai_training_workflow_payload(run_id="run-30")

    assert payload["schema_version"] == AI_TRAINING_WORKFLOW_SCHEMA_VERSION
    assert payload["run_id"] == "run-30"
    assert payload["source_cell"] == SOURCE_CELL
    assert payload["status"] == "implemented_training_workflow_boundary_only"
    assert payload["privacy"] == "FILESYSTEM_ONLY"
    assert payload["http_servable"] is False
    assert payload["frontend_visible"] is False
    assert payload["downloadable_via_api"] is False

    assert payload["normal_app_runs_must_train_models"] is False
    assert payload["normal_app_runs_must_install_ml_dependencies"] is False
    assert payload["normal_app_runs_must_download_weights"] is False
    assert payload["normal_app_runs_must_write_model_artifacts"] is False
    assert payload["normal_app_runs_must_run_inference"] is False

    assert payload["separate_training_workflow_required"] is True
    assert payload["dependency_policy"]["no_runtime_pip_install"] is True
    assert payload["dependency_policy"]["must_run_outside_normal_app_pipeline"] is True


def test_plan_b30_contract_has_classes_gates_and_tensor_dependency():
    payload = build_plan_b30_ai_training_workflow_payload(run_id="run-30")

    assert len(payload["class_labels"]) == 10
    assert payload["class_labels"] == CLASS_LABELS_10
    assert tuple(payload["required_approval_gates"]) == REQUIRED_APPROVAL_GATES

    input_contract = payload["training_input_contract"]
    assert input_contract["depends_on"].startswith("Plan B item #29")
    assert input_contract["preferred_input"] == "AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy"
    assert input_contract["shape"] == [3, 640, 640]
    assert input_contract["dtype"] == "float32"
    assert input_contract["range"] == [0.0, 1.0]


def test_plan_b30_report_writes_private_json_only(tmp_path):
    report_path = write_plan_b30_ai_training_workflow_report(tmp_path, "run-30")

    assert report_path == tmp_path / "manifests" / "AI_TRAINING_WORKFLOW_BOUNDARY_V7_2.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["source_cell"] == "cell_166"
    assert payload["status"] == "implemented_training_workflow_boundary_only"
    assert payload["training_source_cells"] == TRAINING_SOURCE_CELLS

    created = [path for path in tmp_path.rglob("*") if path.is_file()]
    assert created == [report_path]
    assert report_path.suffix == ".json"


def test_plan_b30_module_does_not_expose_training_execution_functions():
    import app.pipeline.parity.ai_training_workflow_boundary as module

    forbidden_prefixes = (
        "train_",
        "fit_",
        "learn_",
        "infer_",
        "predict_",
        "classify_",
        "run_model_",
        "load_model_",
        "download_",
        "install_",
    )
    forbidden = [name for name in dir(module) if name.startswith(forbidden_prefixes)]

    assert forbidden == []
