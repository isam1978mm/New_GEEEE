from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path


AI_MODEL_BUILD_POLICY_SCHEMA_VERSION = "plan_b31_ai_model_build_policy_v1"
AI_MODEL_BUILD_POLICY_REPORT_RELATIVE_PATH = (
    "manifests/AI_MODEL_BUILD_POLICY_V7_2.json"
)

SOURCE_CELL = "cell_232"
SOURCE_NOTEBOOK_FAMILY = "LEADER_AI_MODEL_BUILD_UNETPLUSPLUS_SWIN_WITH_RESNET_FALLBACK"

MODEL_BUILD_SOURCE_CELLS = {
    "cell_231": {
        "role": "input_preprocess_hint",
        "status": "upstream_tensor_hint_only",
        "input_shape": [3, 224, 224],
        "notes": "Notebook resizes RGB-like input for Swin; app tensor builder keeps 640-grid tensors and records 224 use as optional future adapter.",
    },
    "cell_232": {
        "role": "canonical_model_build_cell",
        "status": "selected_policy_source",
        "primary_architecture": "UnetPlusPlus",
        "primary_encoder": "tu-swin_base_patch4_window7_224",
        "fallback_architecture": "UnetPlusPlus",
        "fallback_encoder": "resnet50",
        "in_channels": 3,
        "classes": 5,
        "notebook_requested_encoder_weights": "imagenet",
        "app_policy": "document build config only; no runtime model instantiation or weight download",
    },
    "cell_233": {
        "role": "experimental_custom_swin_large_unetplusplus_decoder",
        "status": "not_selected",
        "not_selected_reason": "Contains custom class attempt and immediate inference; notebook code also uses init instead of __init__.",
        "next_item_if_revisited": "Plan B item #31 extension only after dependency sandbox approval",
    },
    "cell_234": {
        "role": "ortho_calibrated_inference_postprocess",
        "status": "excluded_from_item_31",
        "next_item": "Plan B item #32 or #40",
    },
    "cell_235": {
        "role": "resnet50_unetplusplus_fallback_plus_inference",
        "status": "fallback_model_config_only",
        "fallback_architecture": "UnetPlusPlus",
        "fallback_encoder": "resnet50",
        "in_channels": 3,
        "classes": 5,
        "excluded_behavior": "inference and coordinate printing",
    },
    "cell_236": {
        "role": "final_target_inference",
        "status": "excluded_from_item_31",
        "next_item": "Plan B item #32",
    },
    "cell_237": {
        "role": "target_map_exports",
        "status": "excluded_from_item_31",
        "next_item": "Plan B item #39/#40",
    },
}

MODEL_FAMILY_CONTRACTS = {
    "UnetPlusPlus_Swin": {
        "architecture": "UnetPlusPlus",
        "encoder_name": "tu-swin_base_patch4_window7_224",
        "encoder_weights_policy": "offline_preapproved_or_none",
        "in_channels": 3,
        "classes": 5,
        "input_tensor": "AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy or future 224 adapter",
        "implementation_status": "policy_only_not_instantiated",
        "normal_app_build_allowed": False,
    },
    "UnetPlusPlus_ResNet50_Fallback": {
        "architecture": "UnetPlusPlus",
        "encoder_name": "resnet50",
        "encoder_weights_policy": "offline_preapproved_or_none",
        "in_channels": 3,
        "classes": 5,
        "input_tensor": "AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy",
        "implementation_status": "fallback_policy_only_not_instantiated",
        "normal_app_build_allowed": False,
    },
    "Swin_Custom_Decoder": {
        "architecture": "custom_swin_large_plus_unetplusplus_decoder",
        "encoder_name": "swin_large_patch4_window7_224",
        "encoder_weights_policy": "blocked_until_dependency_sandbox_approval",
        "in_channels": 3,
        "classes": 5,
        "input_tensor": "future 224 adapter",
        "implementation_status": "not_selected",
        "normal_app_build_allowed": False,
    },
    "SegFormer": {
        "architecture": "SegFormer-compatible segmentation model",
        "encoder_name": "not_selected_in_cell_232",
        "encoder_weights_policy": "blocked_until model source is selected",
        "in_channels": 3,
        "classes": 5,
        "input_tensor": "AI_TENSORS_STAGE4/SWINSEGFORMER_16B_640.npy or future adapter",
        "implementation_status": "requirements_carried_forward_only",
        "normal_app_build_allowed": False,
    },
}

REQUIRED_MODEL_BUILD_GATES = (
    "ai_tensor_builder_outputs_exist",
    "training_workflow_boundary_acknowledged",
    "ml_dependency_sandbox_approved",
    "offline_weights_policy_approved",
    "model_source_cell_selected",
    "cpu_gpu_runtime_expectations_approved",
    "model_card_template_approved",
    "no_normal_app_inference_acknowledged",
    "promotion_to_item_32_inference_gate_approved",
)


def build_plan_b31_ai_model_build_policy_payload(*, run_id: str) -> dict[str, object]:
    return {
        "schema_version": AI_MODEL_BUILD_POLICY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "source_cell": SOURCE_CELL,
        "source_notebook_family": SOURCE_NOTEBOOK_FAMILY,
        "status": "implemented_model_build_policy_only",
        "privacy": "FILESYSTEM_ONLY",
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,

        "normal_app_runs_must_build_models": False,
        "normal_app_runs_must_train_models": False,
        "normal_app_runs_must_install_ml_dependencies": False,
        "normal_app_runs_must_download_weights": False,
        "normal_app_runs_must_write_model_artifacts": False,
        "normal_app_runs_must_run_inference": False,

        "imports_torch": False,
        "imports_timm": False,
        "imports_segmentation_models_pytorch": False,
        "instantiates_model": False,
        "loads_weights": False,
        "runs_forward_pass": False,

        "selected_canonical_model_build_cell": SOURCE_CELL,
        "model_build_source_cells": MODEL_BUILD_SOURCE_CELLS,
        "model_family_contracts": MODEL_FAMILY_CONTRACTS,
        "required_model_build_gates": list(REQUIRED_MODEL_BUILD_GATES),

        "selected_primary_model_policy": {
            "architecture": "UnetPlusPlus",
            "encoder_name": "tu-swin_base_patch4_window7_224",
            "fallback_encoder_name": "resnet50",
            "in_channels": 3,
            "classes": 5,
            "encoder_weights_policy": "offline_preapproved_or_none",
            "notebook_requested_encoder_weights": "imagenet",
            "app_runtime_weight_download_allowed": False,
            "app_runtime_model_instantiation_allowed": False,
        },

        "input_dependency_contract": {
            "depends_on_item_29": True,
            "preferred_input": "AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy",
            "preferred_input_shape": [3, 640, 640],
            "optional_swin_adapter_shape": [3, 224, 224],
            "dtype": "float32",
            "range": [0.0, 1.0],
        },

        "output_contract_when_later_approved": {
            "model_config_manifest": "private model config JSON",
            "model_card": "private model card",
            "weights": "private/offline weights only after gate approval",
            "no_probability_maps_until_item_32": True,
        },

        "next_dependency_unblocking_item": (
            "Plan B item #32: CNN final target inference, after dependency/weights/model gates"
        ),

        "notes": (
            "This ports the notebook model-build behavior as a policy/config manifest only. "
            "It intentionally does not import ML frameworks, instantiate models, download weights, "
            "run forward passes, train, or create model artifacts."
        ),
    }


def write_plan_b31_ai_model_build_policy_report(
    run_dir: str | Path,
    run_id: str,
    *,
    report_relative_path: str | Path = AI_MODEL_BUILD_POLICY_REPORT_RELATIVE_PATH,
) -> Path:
    report_path = Path(run_dir) / Path(report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_plan_b31_ai_model_build_policy_payload(run_id=run_id)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report_path
