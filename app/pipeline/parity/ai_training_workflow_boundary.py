from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path


AI_TRAINING_WORKFLOW_SCHEMA_VERSION = "plan_b30_ai_training_workflow_boundary_v1"
AI_TRAINING_WORKFLOW_REPORT_RELATIVE_PATH = (
    "manifests/AI_TRAINING_WORKFLOW_BOUNDARY_V7_2.json"
)

SOURCE_CELL = "cell_166"
SOURCE_NOTEBOOK_FAMILY = "PROFESSIONAL_GLOBAL_ARCHEO_TRAINING_LOW_MEMORY_SAFE"

TRAINING_SOURCE_CELLS = {
    "cell_150": {
        "role": "dependency_install_probe",
        "status": "documented_only",
        "not_ported_reason": "Notebook pip install cell; app must not install ML dependencies during normal runs.",
        "packages": ["ultralytics", "timm", "segmentation-models-pytorch", "plotly", "kaleido"],
    },
    "cell_151": {
        "role": "expanded_dependency_install_probe",
        "status": "documented_only",
        "not_ported_reason": "Notebook pip install cell; dependency policy must be separate from app pipeline.",
        "packages": ["ultralytics", "timm", "segmentation-models-pytorch", "albumentations", "einops", "plotly", "kaleido"],
    },
    "cell_163": {
        "role": "small_224_training_scaffold",
        "status": "superseded_by_cell_166_policy",
        "input_shape": [3, 224, 224],
        "classes": 5,
    },
    "cell_164": {
        "role": "640_training_scaffold_memory_optimized_12gb",
        "status": "superseded_by_cell_166_policy",
        "input_shape": [3, 640, 640],
        "classes": 10,
    },
    "cell_165": {
        "role": "high_fidelity_640_training_variant",
        "status": "superseded_by_cell_166_policy",
        "input_shape": [3, 640, 640],
        "classes": 10,
    },
    "cell_166": {
        "role": "canonical_low_memory_safe_training_scaffold",
        "status": "selected_policy_source",
        "input_shape": [3, 640, 640],
        "classes": 10,
        "model_family": "UnetPlusPlus",
        "encoder": "resnet34",
        "optimizer": "AdamW",
        "loss": "CrossEntropyLoss",
        "amp_policy": "cuda_amp_if_available",
        "memory_policy": "micro_batch_size=1; grad_accum_steps=2; low decoder channels",
    },
    "cell_167": {
        "role": "model_based_inference",
        "status": "excluded_from_item_30",
        "next_item": "Plan B item #32",
    },
    "cell_168": {
        "role": "model_based_inference",
        "status": "excluded_from_item_30",
        "next_item": "Plan B item #32",
    },
    "cell_169": {
        "role": "large_model_based_inference_loop",
        "status": "excluded_from_item_30",
        "next_item": "Plan B item #32",
    },
}

CLASS_LABELS_10 = {
    0: "background_normal",
    1: "metal_treasure_small",
    2: "tunnel_void",
    3: "vertical_shaft",
    4: "royal_tomb",
    5: "rock_cut_sarcophagus",
    6: "coffin",
    7: "straight_stairs",
    8: "spiral_stairs",
    9: "secret_door",
}

REQUIRED_APPROVAL_GATES = (
    "training_dataset_source_approved",
    "positive_labels_reviewed",
    "negative_backgrounds_reviewed",
    "hard_negatives_reviewed",
    "train_val_test_split_locked",
    "ml_dependency_sandbox_approved",
    "weights_storage_policy_approved",
    "offline_training_runner_approved",
    "evaluation_metrics_thresholds_approved",
    "inference_promotion_gate_approved",
)


def build_plan_b30_ai_training_workflow_payload(*, run_id: str) -> dict[str, object]:
    return {
        "schema_version": AI_TRAINING_WORKFLOW_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "source_cell": SOURCE_CELL,
        "source_notebook_family": SOURCE_NOTEBOOK_FAMILY,
        "status": "implemented_training_workflow_boundary_only",
        "privacy": "FILESYSTEM_ONLY",
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,

        "normal_app_runs_must_train_models": False,
        "normal_app_runs_must_install_ml_dependencies": False,
        "normal_app_runs_must_download_weights": False,
        "normal_app_runs_must_write_model_artifacts": False,
        "normal_app_runs_must_run_inference": False,

        "separate_training_workflow_required": True,
        "selected_canonical_training_cell": SOURCE_CELL,
        "training_source_cells": TRAINING_SOURCE_CELLS,
        "class_labels": CLASS_LABELS_10,
        "required_approval_gates": list(REQUIRED_APPROVAL_GATES),

        "training_input_contract": {
            "depends_on": "Plan B item #29 AI_TENSORS_STAGE4 outputs",
            "preferred_input": "AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy",
            "shape": [3, 640, 640],
            "dtype": "float32",
            "range": [0.0, 1.0],
            "nodata_policy": "non-finite/nodata values must be converted to 0.0 before training",
        },

        "training_output_contract_when_later_approved": {
            "weights": "private/offline weights only; never public by default",
            "metrics": "private training metrics JSON/CSV",
            "model_card": "private model card documenting data sources, class labels, and evaluation",
            "promotion_gate": "weights cannot be used by app inference until item #31/#32 approval",
        },

        "dependency_policy": {
            "no_runtime_pip_install": True,
            "required_packages_if_training_workflow_is_later_approved": [
                "torch",
                "segmentation-models-pytorch",
                "timm",
                "ultralytics",
                "albumentations",
                "einops",
            ],
            "must_run_outside_normal_app_pipeline": True,
        },

        "next_dependency_unblocking_item": (
            "Plan B item #31: CNN / Unet++ / Swin / SegFormer model build policy"
        ),

        "notes": (
            "This ports the notebook training/learn-weights behavior as a boundary contract only. "
            "It intentionally does not train, install ML dependencies, download weights, or produce model artifacts."
        ),
    }


def write_plan_b30_ai_training_workflow_report(
    run_dir: str | Path,
    run_id: str,
    *,
    report_relative_path: str | Path = AI_TRAINING_WORKFLOW_REPORT_RELATIVE_PATH,
) -> Path:
    report_path = Path(run_dir) / Path(report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_plan_b30_ai_training_workflow_payload(run_id=run_id)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report_path
