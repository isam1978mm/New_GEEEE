from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "plan_b39_final_probability_overlay_gate_v1"
REPORT_RELATIVE_PATH = "manifests/AI_FINAL_PROBABILITY_OVERLAY_GATE_V7_2.json"

SOURCE_CELL = "cell_238"
SOURCE_NOTEBOOK_FAMILY = "FINAL_ARCHEO_ENGINE_PROBABILITY_MAP_OVERLAY_MARKERS"

EXPECTED_UPSTREAM_FILES = {
    "item_32_inference_gate": "manifests/AI_FINAL_INFERENCE_GATE_V7_2.json",
    "item_38_live_overlay_manifest": "full_job/focus/APP_NATIVE_LIVE_OVERLAY_MANIFEST_V7_2.json",
    "future_probability_map": "AI_INFERENCE_STAGE5/AI_MODEL_PROBABILITIES_640.npy",
    "future_inference_csv": "QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.csv",
    "future_inference_json": "QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.json",
}

SOURCE_CELL_DECISIONS = {
    "cell_238": {
        "role": "canonical_probability_map_target_engine",
        "status": "selected_gate_source",
        "reason": "Defines final_archeo_engine(prob_map) and final_targets from probability maps.",
        "blocked_behavior": "Requires probability map from real model inference.",
    },
    "cell_239": {
        "role": "structural_scanner",
        "status": "not_selected",
        "reason": "Uses torch convolution and exact coordinate prints.",
    },
    "cell_240": {
        "role": "final_decision_scanner",
        "status": "not_selected",
        "reason": "Uses probabilities and exact coordinate prints.",
    },
    "cell_241": {
        "role": "field_navigation_geojson_kmz",
        "status": "excluded_from_item_39",
        "reason": "Coordinate-bearing GeoJSON/KMZ behavior already belongs to private field-map outputs.",
    },
    "cell_242": {
        "role": "stairs_path_tracing",
        "status": "excluded_from_item_39",
        "next_item": "Plan B item #40",
    },
    "cell_243": {
        "role": "live_geemap_overlay_shell",
        "status": "already_replaced_by_item_38",
        "reason": "App-native live overlay manifest exists; #39 only gates probability-map/marker dependency.",
    },
    "cell_169": {
        "role": "real_model_probability_source",
        "status": "blocked_dependency",
        "reason": "Real inference remains gated by item #32.",
    },
    "cell_236": {
        "role": "secondary_model_inference_reference",
        "status": "blocked_dependency",
        "reason": "Requires torch/model execution and exact coordinates.",
    },
}

REQUIRED_OVERLAY_GATES = (
    "item_32_inference_gate_exists",
    "item_38_live_overlay_manifest_exists",
    "item_32_real_inference_approved",
    "probability_map_exists",
    "target_records_exist",
    "probability_map_privacy_policy_approved",
    "operator_marker_preview_policy_approved",
)

FUTURE_PRIVATE_OUTPUTS_IF_APPROVED = {
    "probability_map": "AI_INFERENCE_STAGE5/AI_MODEL_PROBABILITIES_640.npy",
    "target_csv": "QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.csv",
    "target_json": "QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.json",
    "redacted_overlay_summary": "manifests/AI_FINAL_PROBABILITY_OVERLAY_REDACTED_SUMMARY_V7_2.json",
}

OVERLAY_LAYER_CONTRACT = [
    {
        "id": "final_probability_heatmap",
        "type": "raster_probability_overlay",
        "source": FUTURE_PRIVATE_OUTPUTS_IF_APPROVED["probability_map"],
        "status": "pending_real_inference",
        "exact_coordinates_in_manifest": False,
    },
    {
        "id": "final_target_markers_redacted",
        "type": "vector_marker_summary",
        "source": FUTURE_PRIVATE_OUTPUTS_IF_APPROVED["target_json"],
        "status": "pending_private_target_records",
        "exact_coordinates_in_manifest": False,
    },
    {
        "id": "final_target_confidence_bands",
        "type": "confidence_summary",
        "source": FUTURE_PRIVATE_OUTPUTS_IF_APPROVED["target_csv"],
        "status": "pending_private_target_records",
        "exact_coordinates_in_manifest": False,
    },
    {
        "id": "app_native_overlay_shell",
        "type": "app_native_overlay_manifest",
        "source": "full_job/focus/APP_NATIVE_LIVE_OVERLAY_MANIFEST_V7_2.json",
        "status": "available_if_item_38_output_exists",
        "exact_coordinates_in_manifest": False,
    },
]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


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


def build_plan_b39_final_probability_overlay_gate_payload(
    *,
    run_dir: str | Path,
    run_id: str,
) -> dict[str, object]:
    run_dir = Path(run_dir)
    upstream = _file_status(run_dir)

    item32_payload = _read_json(run_dir / EXPECTED_UPSTREAM_FILES["item_32_inference_gate"])
    item32_real_inference_approved = bool(item32_payload.get("approved_for_real_inference", False))

    target_records_exist = bool(upstream["future_inference_csv"]["exists"]) and bool(
        upstream["future_inference_json"]["exists"]
    )

    gate_status = {
        "item_32_inference_gate_exists": bool(upstream["item_32_inference_gate"]["exists"]),
        "item_38_live_overlay_manifest_exists": bool(upstream["item_38_live_overlay_manifest"]["exists"]),
        "item_32_real_inference_approved": item32_real_inference_approved,
        "probability_map_exists": bool(upstream["future_probability_map"]["exists"]),
        "target_records_exist": target_records_exist,
        "probability_map_privacy_policy_approved": False,
        "operator_marker_preview_policy_approved": False,
    }

    approved_for_overlay = all(gate_status.values())

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "source_cell": SOURCE_CELL,
        "source_notebook_family": SOURCE_NOTEBOOK_FAMILY,
        "status": "implemented_probability_overlay_gate_only",
        "privacy": "FILESYSTEM_ONLY",
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
        "uses_geemap": False,
        "imports_earth_engine": False,
        "imports_torch": False,
        "runs_model_inference": False,
        "creates_probability_map": False,
        "creates_overlay_tiles": False,
        "creates_markers": False,
        "creates_geojson": False,
        "creates_kmz": False,
        "exposes_exact_coordinates": False,
        "raw_geometry_in_manifest": False,
        "exact_coordinates_in_manifest": False,
        "selected_canonical_probability_overlay_cell": SOURCE_CELL,
        "source_cell_decisions": SOURCE_CELL_DECISIONS,
        "required_overlay_gates": list(REQUIRED_OVERLAY_GATES),
        "gate_status": gate_status,
        "upstream_file_status": upstream,
        "approved_for_probability_overlay": approved_for_overlay,
        "blocked_reason": None if approved_for_overlay else (
            "Final probability overlay and markers are blocked until real #32 inference, "
            "private probability maps, private target records, privacy policy, and operator preview policy are approved."
        ),
        "overlay_layer_contract": OVERLAY_LAYER_CONTRACT,
        "layer_count": len(OVERLAY_LAYER_CONTRACT),
        "future_private_outputs_if_approved": FUTURE_PRIVATE_OUTPUTS_IF_APPROVED,
        "replacement_policy": {
            "geemap_not_ported": True,
            "public_tiles_not_created": True,
            "coordinate_bearing_outputs_private_only": True,
            "operator_preview_must_be_redacted": True,
        },
        "next_dependency_unblocking_item": "Plan B item #40 or approved continuation of #39 after real probability maps exist",
        "notes": (
            "This ports the final probability-map overlay/marker behavior as a gated readiness manifest only. "
            "It intentionally does not run inference, import torch/geemap/ee, create tiles, create markers, "
            "write GeoJSON/KMZ, or expose coordinates."
        ),
    }


def write_plan_b39_final_probability_overlay_gate_report(
    run_dir: str | Path,
    run_id: str,
    *,
    report_relative_path: str | Path = REPORT_RELATIVE_PATH,
) -> Path:
    report_path = Path(run_dir) / Path(report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_plan_b39_final_probability_overlay_gate_payload(run_dir=run_dir, run_id=run_id)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report_path
