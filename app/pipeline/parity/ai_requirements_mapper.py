from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


AI_REQUIREMENTS_MAPPER_SCHEMA_VERSION = "plan_b28_ai_requirements_mapper_v1"
AI_REQUIREMENTS_MAPPER_REPORT_RELATIVE_PATH = (
    "manifests/AI_MODEL_REQUIREMENTS_MAPPER_V7_2.json"
)

SOURCE_CELL = "cell_140"
SOURCE_NOTEBOOK_FAMILY = "STAGE_1_MATRIX_AUDIT_AI_REQUIREMENTS_MAPPER"

MODEL_FAMILIES = (
    "YOLOv11",
    "CNN",
    "Swin",
    "SegFormer",
    "UnetPlusPlus",
)

REQUIRED_CORE_BANDS = (
    "Secret_Gold_Halo",
    "Secret_Silver_Oxide",
    "Secret_Tunnel_Ceiling",
    "Secret_Thermal_Inertia",
    "Secret_Chemical_Protector",
    "Secret_Hidden_Doors",
    "REPORT_640_FINAL_Zero_Point_Targets",
    "REPORT_640_Mass_Report",
    "REPORT_640_Pottery_Report",
)

SUPPORTING_SOURCE_CELLS = {
    "cell_140": "matrix audit and AI requirements mapper",
    "cell_147": "tensor builder opens input tif and produces normalized inputs",
    "cell_148": "AI tensor builder for YOLOv11/CNN/Swin/SegFormer",
    "cell_150": "AI library install plan",
    "cell_151": "alternate AI library install plan",
    "cell_163": "training scaffold only, deferred",
    "cell_164": "training scaffold only, deferred",
    "cell_165": "training scaffold only, deferred",
    "cell_166": "training scaffold only, deferred",
    "cell_231": "three-layer RGB-like CNN input attempt",
    "cell_232": "Swin/UnetPlusPlus model attempt",
    "cell_235": "resnet50 UnetPlusPlus model attempt",
}


@dataclass(frozen=True)
class AiModelRequirement:
    model_family: str
    expected_input_kind: str
    expected_input_shape: str
    channel_policy: str
    normalization_policy: str
    required_bands: tuple[str, ...]
    output_contract: tuple[str, ...]
    implementation_status: str
    blockers: tuple[str, ...]
    next_item: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def get_plan_b28_ai_requirements() -> tuple[AiModelRequirement, ...]:
    return (
        AiModelRequirement(
            model_family="YOLOv11",
            expected_input_kind="object-detection tensor",
            expected_input_shape="pending item #29 tensor builder; likely 3-channel or tiled image input",
            channel_policy="requires deterministic channel selection from model-ready hypercube",
            normalization_policy="requires stable 0-1 normalization and nodata handling",
            required_bands=REQUIRED_CORE_BANDS,
            output_contract=("private detection proposal table", "private probability/score map if later approved"),
            implementation_status="requirements_mapped_only",
            blockers=("item #29 tensor builder not implemented", "weights/training data not locked", "dependency policy not approved"),
            next_item="Plan B item #29",
        ),
        AiModelRequirement(
            model_family="CNN",
            expected_input_kind="semantic RGB-like composites or 3-channel tensor",
            expected_input_shape="3 x 224 x 224 or tiled/ROI tensor depending on selected notebook variant",
            channel_policy="metal, void/structure, and material/context composites from core bands",
            normalization_policy="robust ROI normalization with finite fill policy",
            required_bands=REQUIRED_CORE_BANDS,
            output_contract=("private CNN score table", "private GeoJSON or probability map if later approved"),
            implementation_status="requirements_mapped_only",
            blockers=("item #29 tensor builder not implemented", "item #31 model policy not selected", "item #32 inference not approved"),
            next_item="Plan B item #29",
        ),
        AiModelRequirement(
            model_family="Swin",
            expected_input_kind="segmentation backbone tensor",
            expected_input_shape="3 x 224 x 224 notebook attempt; exact app tensor pending item #29",
            channel_policy="same selected model-ready channels as CNN unless later contract changes",
            normalization_policy="stable 0-1 channel normalization, no online notebook preprocessing drift",
            required_bands=REQUIRED_CORE_BANDS,
            output_contract=("private segmentation probability map if later approved",),
            implementation_status="requirements_mapped_only",
            blockers=("optional dependency policy not approved", "weights unavailable", "model implementation deferred"),
            next_item="Plan B item #29",
        ),
        AiModelRequirement(
            model_family="SegFormer",
            expected_input_kind="segmentation tensor",
            expected_input_shape="pending item #29 tensor builder",
            channel_policy="requires explicit band-order manifest before model use",
            normalization_policy="stable 0-1 tensor normalization and nodata mask policy",
            required_bands=REQUIRED_CORE_BANDS,
            output_contract=("private segmentation probability map if later approved",),
            implementation_status="requirements_mapped_only",
            blockers=("tensor contract not locked", "dependency policy not approved", "model implementation deferred"),
            next_item="Plan B item #29",
        ),
        AiModelRequirement(
            model_family="UnetPlusPlus",
            expected_input_kind="segmentation tensor",
            expected_input_shape="3 x 224 x 224 notebook model attempt; 640-grid remapping required later",
            channel_policy="3-channel model input from deterministic composites",
            normalization_policy="robust finite normalized tensors only",
            required_bands=REQUIRED_CORE_BANDS,
            output_contract=("private class probability map", "private target proposal table if later approved"),
            implementation_status="requirements_mapped_only",
            blockers=("model weights/dependencies not locked", "inference stage not approved", "final probability map pending"),
            next_item="Plan B item #29",
        ),
    )


def build_plan_b28_ai_requirements_mapper_payload(
    *,
    run_id: str,
    requirements: Iterable[AiModelRequirement] | None = None,
) -> dict[str, object]:
    items = tuple(requirements or get_plan_b28_ai_requirements())
    return {
        "schema_version": AI_REQUIREMENTS_MAPPER_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "source_cell": SOURCE_CELL,
        "source_notebook_family": SOURCE_NOTEBOOK_FAMILY,
        "status": "implemented_requirements_mapper_only",
        "privacy": "FILESYSTEM_ONLY",
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
        "trains_models": False,
        "runs_inference": False,
        "downloads_weights": False,
        "adds_heavy_ml_dependencies": False,
        "creates_model_artifacts": False,
        "notebook_value_parity_verified": False,
        "model_families": list(MODEL_FAMILIES),
        "required_core_bands": list(REQUIRED_CORE_BANDS),
        "supporting_source_cells": SUPPORTING_SOURCE_CELLS,
        "requirements": [item.to_dict() for item in items],
        "next_dependency_unblocking_item": "Plan B item #29: AI tensor builder for YOLO/CNN/Swin/SegFormer",
        "notes": (
            "This ports the notebook requirements-mapper behavior only. "
            "It does not build tensors, train models, run inference, or expose artifacts."
        ),
    }


def write_plan_b28_ai_requirements_mapper_report(
    run_dir: str | Path,
    run_id: str,
    *,
    report_relative_path: str | Path = AI_REQUIREMENTS_MAPPER_REPORT_RELATIVE_PATH,
) -> Path:
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_plan_b28_ai_requirements_mapper_payload(run_id=run_id)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report_path
