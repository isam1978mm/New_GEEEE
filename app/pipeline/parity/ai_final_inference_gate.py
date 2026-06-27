from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path


AI_FINAL_INFERENCE_GATE_SCHEMA_VERSION = "plan_b32_ai_final_inference_gate_v1"
AI_FINAL_INFERENCE_GATE_REPORT_RELATIVE_PATH = (
    "manifests/AI_FINAL_INFERENCE_GATE_V7_2.json"
)

SOURCE_CELL = "cell_169"
SOURCE_NOTEBOOK_FAMILY = "MODEL_BASED_ARCHEO_INFERENCE_DEM_SLOPE_FUSION_STRICT_RUN"

INFERENCE_SOURCE_CELLS = {
    "cell_167": {
        "role": "early_professional_scan",
        "status": "not_selected",
        "reason": "Requires Professional_Target_Model, torch forward pass, and coordinate output.",
    },
    "cell_168": {
        "role": "model_inference_dem_slope_fusion",
        "status": "superseded_by_cell_169",
        "reason": "Requires Final_Target_Model/final_data_input and exact coordinates.",
    },
    "cell_169": {
        "role": "canonical_strict_model_inference_with_csv_json",
        "status": "selected_gate_source",
        "not_executed_reason": "Requires approved model object, torch runtime, weights, forward pass, and private coordinate-bearing outputs.",
        "notebook_outputs_if_later_approved": [
            "QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.csv",
            "QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.json",
        ],
    },
    "cell_232": {
        "role": "model_build_plus_immediate_inference",
        "status": "excluded_from_item_32_execution",
        "reason": "Handled as item #31 policy; immediate inference remains gated.",
    },
    "cell_235": {
        "role": "resnet50_fallback_plus_inference",
        "status": "fallback_inference_policy_only",
        "reason": "Fallback model config retained in item #31; inference remains gated.",
    },
    "cell_236": {
        "role": "final_target_inference_grid_locked",
        "status": "secondary_inference_reference",
        "reason": "Useful class/signature mapping, but prints exact coordinates and runs torch forward pass.",
    },
    "cell_237": {
        "role": "final_target_map_exports",
        "status": "excluded_from_item_32",
        "next_item": "Plan B item #39/#40",
    },
}

REQUIRED_INFERENCE_GATES = (
    "item_29_tensor_outputs_exist",
    "item_30_training_workflow_boundary_exists",
    "item_31_model_build_policy_exists",
    "ml_dependency_sandbox_approved",
    "offline_weights_available_and_approved",
    "trained_model_artifact_registered_private",
    "model_card_and_metrics_approved",
    "inference_runtime_cpu_gpu_policy_approved",
    "coordinate_privacy_policy_approved",
    "private_output_storage_policy_approved",
    "operator_access_policy_approved",
)

EXPECTED_UPSTREAM_FILES = {
    "item_29_full_tensor": "AI_TENSORS_STAGE4/AI_FULL_52B_FLOAT32_640.npy",
    "item_29_yolo_rgb": "AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy",
    "item_29_cnn_tensor": "AI_TENSORS_STAGE4/CNN_MULTI_24B_640.npy",
    "item_29_swin_tensor": "AI_TENSORS_STAGE4/SWINSEGFORMER_16B_640.npy",
    "item_29_report": "QA/STAGE4_AI_TENSOR_BUILDER.json",
    "item_30_training_boundary": "manifests/AI_TRAINING_WORKFLOW_BOUNDARY_V7_2.json",
    "item_31_model_build_policy": "manifests/AI_MODEL_BUILD_POLICY_V7_2.json",
}

CLASS_SIGNATURES = {
    1: "metal_or_solid_object",
    2: "void_entry_or_corridor",
    3: "chamber_or_internal_space",
    4: "structure_wall_or_built_feature",
}

FUTURE_PRIVATE_OUTPUTS_IF_APPROVED = {
    "inference_csv": "QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.csv",
    "inference_json": "QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.json",
    "probability_stack": "AI_INFERENCE_STAGE5/AI_MODEL_PROBABILITIES_640.npy",
    "redacted_summary": "manifests/AI_FINAL_INFERENCE_REDACTED_SUMMARY_V7_2.json",
}


def _file_status(run_dir: Path) -> dict[str, dict[str, object]]:
    statuses: dict[str, dict[str, object]] = {}
    for key, rel in EXPECTED_UPSTREAM_FILES.items():
        path = run_dir / rel
        statuses[key] = {
            "relative_path": rel,
            "exists": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else 0,
        }
    return statuses


def build_plan_b32_ai_final_inference_gate_payload(*, run_dir: str | Path, run_id: str) -> dict[str, object]:
    run_dir = Path(run_dir)
    upstream = _file_status(run_dir)
    upstream_ready = all(bool(item["exists"]) for item in upstream.values())

    gate_status = {
        "item_29_tensor_outputs_exist": upstream["item_29_yolo_rgb"]["exists"]
            and upstream["item_29_cnn_tensor"]["exists"]
            and upstream["item_29_swin_tensor"]["exists"],
        "item_30_training_workflow_boundary_exists": upstream["item_30_training_boundary"]["exists"],
        "item_31_model_build_policy_exists": upstream["item_31_model_build_policy"]["exists"],
        "ml_dependency_sandbox_approved": False,
        "offline_weights_available_and_approved": False,
        "trained_model_artifact_registered_private": False,
        "model_card_and_metrics_approved": False,
        "inference_runtime_cpu_gpu_policy_approved": False,
        "coordinate_privacy_policy_approved": False,
        "private_output_storage_policy_approved": False,
        "operator_access_policy_approved": False,
    }

    approved_for_real_inference = all(gate_status.values())

    return {
        "schema_version": AI_FINAL_INFERENCE_GATE_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "source_cell": SOURCE_CELL,
        "source_notebook_family": SOURCE_NOTEBOOK_FAMILY,
        "status": "implemented_inference_gate_only",
        "privacy": "FILESYSTEM_ONLY",
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,

        "normal_app_runs_must_run_inference": False,
        "normal_app_runs_must_import_torch": False,
        "normal_app_runs_must_load_weights": False,
        "normal_app_runs_must_instantiate_model": False,
        "normal_app_runs_must_write_coordinate_outputs": False,
        "normal_app_runs_must_write_probability_maps": False,
        "normal_app_runs_must_write_geojson_or_kmz": False,

        "imports_torch": False,
        "loads_model": False,
        "loads_weights": False,
        "runs_forward_pass": False,
        "creates_probability_map": False,
        "creates_target_csv": False,
        "creates_target_json": False,
        "creates_geojson": False,
        "creates_kmz": False,
        "exposes_exact_coordinates": False,

        "selected_canonical_inference_cell": SOURCE_CELL,
        "inference_source_cells": INFERENCE_SOURCE_CELLS,
        "required_inference_gates": list(REQUIRED_INFERENCE_GATES),
        "gate_status": gate_status,
        "upstream_file_status": upstream,
        "upstream_tensor_policy_ready": upstream_ready,
        "approved_for_real_inference": approved_for_real_inference,
        "blocked_reason": None if approved_for_real_inference else (
            "Real model inference is blocked until dependency, weights, model-card, runtime, "
            "privacy, storage, and operator-access gates are explicitly approved."
        ),

        "class_signatures": CLASS_SIGNATURES,
        "future_private_outputs_if_approved": FUTURE_PRIVATE_OUTPUTS_IF_APPROVED,
        "future_inference_contract": {
            "input": "AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy or approved model-specific adapter",
            "input_shape": [3, 640, 640],
            "softmax_temperature": 3.5,
            "peak_detection": "local maximum filtering over private probability maps",
            "coordinate_policy": "exact coordinates remain private/operator-only; no public API payload",
            "output_policy": "CSV/JSON/probability maps are filesystem-only unless separate private serving policy is approved",
        },
        "next_dependency_unblocking_item": (
            "Plan B item #33 or approved continuation of #32 real inference after gates"
        ),
        "notes": (
            "This ports the final CNN/model inference notebook behavior as a gated readiness manifest only. "
            "It intentionally does not import torch, load weights, instantiate a model, run a forward pass, "
            "write probability maps, write target CSV/JSON, or expose coordinates."
        ),
    }


def write_plan_b32_ai_final_inference_gate_report(
    run_dir: str | Path,
    run_id: str,
    *,
    report_relative_path: str | Path = AI_FINAL_INFERENCE_GATE_REPORT_RELATIVE_PATH,
) -> Path:
    report_path = Path(run_dir) / Path(report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_plan_b32_ai_final_inference_gate_payload(run_dir=run_dir, run_id=run_id)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report_path
