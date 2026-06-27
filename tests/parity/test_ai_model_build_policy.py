import json

from app.pipeline.parity.ai_model_build_policy import (
    AI_MODEL_BUILD_POLICY_SCHEMA_VERSION,
    MODEL_BUILD_SOURCE_CELLS,
    MODEL_FAMILY_CONTRACTS,
    REQUIRED_MODEL_BUILD_GATES,
    SOURCE_CELL,
    build_plan_b31_ai_model_build_policy_payload,
    write_plan_b31_ai_model_build_policy_report,
)


def test_plan_b31_selects_cell_232_and_excludes_inference_cells():
    payload = build_plan_b31_ai_model_build_policy_payload(run_id="run-31")

    assert payload["source_cell"] == "cell_232"
    assert payload["selected_canonical_model_build_cell"] == "cell_232"

    cells = payload["model_build_source_cells"]
    assert cells["cell_232"]["status"] == "selected_policy_source"
    assert cells["cell_232"]["primary_encoder"] == "tu-swin_base_patch4_window7_224"
    assert cells["cell_235"]["status"] == "fallback_model_config_only"
    assert cells["cell_236"]["status"] == "excluded_from_item_31"
    assert cells["cell_237"]["status"] == "excluded_from_item_31"


def test_plan_b31_payload_is_policy_only_not_model_execution():
    payload = build_plan_b31_ai_model_build_policy_payload(run_id="run-31")

    assert payload["schema_version"] == AI_MODEL_BUILD_POLICY_SCHEMA_VERSION
    assert payload["run_id"] == "run-31"
    assert payload["source_cell"] == SOURCE_CELL
    assert payload["status"] == "implemented_model_build_policy_only"
    assert payload["privacy"] == "FILESYSTEM_ONLY"
    assert payload["http_servable"] is False
    assert payload["frontend_visible"] is False
    assert payload["downloadable_via_api"] is False

    assert payload["normal_app_runs_must_build_models"] is False
    assert payload["normal_app_runs_must_train_models"] is False
    assert payload["normal_app_runs_must_install_ml_dependencies"] is False
    assert payload["normal_app_runs_must_download_weights"] is False
    assert payload["normal_app_runs_must_write_model_artifacts"] is False
    assert payload["normal_app_runs_must_run_inference"] is False

    assert payload["imports_torch"] is False
    assert payload["imports_timm"] is False
    assert payload["imports_segmentation_models_pytorch"] is False
    assert payload["instantiates_model"] is False
    assert payload["loads_weights"] is False
    assert payload["runs_forward_pass"] is False


def test_plan_b31_contract_has_model_gates_and_item29_input_dependency():
    payload = build_plan_b31_ai_model_build_policy_payload(run_id="run-31")

    assert payload["model_family_contracts"] == MODEL_FAMILY_CONTRACTS
    assert tuple(payload["required_model_build_gates"]) == REQUIRED_MODEL_BUILD_GATES

    selected = payload["selected_primary_model_policy"]
    assert selected["architecture"] == "UnetPlusPlus"
    assert selected["encoder_name"] == "tu-swin_base_patch4_window7_224"
    assert selected["fallback_encoder_name"] == "resnet50"
    assert selected["in_channels"] == 3
    assert selected["classes"] == 5
    assert selected["app_runtime_weight_download_allowed"] is False
    assert selected["app_runtime_model_instantiation_allowed"] is False

    input_contract = payload["input_dependency_contract"]
    assert input_contract["depends_on_item_29"] is True
    assert input_contract["preferred_input"] == "AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy"
    assert input_contract["preferred_input_shape"] == [3, 640, 640]
    assert input_contract["optional_swin_adapter_shape"] == [3, 224, 224]


def test_plan_b31_report_writes_private_json_only(tmp_path):
    report_path = write_plan_b31_ai_model_build_policy_report(tmp_path, "run-31")

    assert report_path == tmp_path / "manifests" / "AI_MODEL_BUILD_POLICY_V7_2.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["source_cell"] == "cell_232"
    assert payload["status"] == "implemented_model_build_policy_only"
    assert payload["model_build_source_cells"] == MODEL_BUILD_SOURCE_CELLS

    created = [path for path in tmp_path.rglob("*") if path.is_file()]
    assert created == [report_path]
    assert report_path.suffix == ".json"


def test_plan_b31_module_does_not_expose_model_execution_functions():
    import app.pipeline.parity.ai_model_build_policy as module

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
        "instantiate_",
    )
    forbidden = [name for name in dir(module) if name.startswith(forbidden_prefixes)]

    assert forbidden == []
