from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "plan_b40_gps_path_tracing_gate_v1"
REPORT_RELATIVE_PATH = "manifests/AI_GPS_PATH_TRACING_GATE_V7_2.json"

SOURCE_CELL = "cell_242"
SOURCE_NOTEBOOK_FAMILY = "TRACE_STAIRS_PATH_GPS_FINDINGS"

EXPECTED_UPSTREAM_FILES = {
    "item_39_probability_overlay_gate": "manifests/AI_FINAL_PROBABILITY_OVERLAY_GATE_V7_2.json",
    "item_32_inference_gate": "manifests/AI_FINAL_INFERENCE_GATE_V7_2.json",
    "future_probability_map": "AI_INFERENCE_STAGE5/AI_MODEL_PROBABILITIES_640.npy",
    "future_inference_json": "QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.json",
    "future_inference_csv": "QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.csv",
}

SOURCE_CELL_DECISIONS = {
    "cell_242": {
        "role": "canonical_gps_path_tracing_from_stairs_pixel",
        "status": "selected_gate_source",
        "reason": "Defines trace_stairs_path(probs_map, stairs_loc), searches near a stairs pixel, then converts findings to GPS.",
        "blocked_behavior": "Requires probability map, detected stairs seed, get_nano_gps/NewPoint, and exact coordinate output.",
    },
    "cell_227": {
        "role": "gps_point_search_and_layer_comparison",
        "status": "supporting_reference_only",
        "reason": "Compares external GPS points against layers, not the final path-tracing behavior.",
    },
    "cell_228": {
        "role": "gps_matching_report",
        "status": "supporting_reference_only",
        "reason": "Writes a layer/GPS matching report, not final path tracing.",
    },
    "cell_237": {
        "role": "final_targets_field_map_geojson_kmz",
        "status": "excluded_from_item_40",
        "reason": "Coordinate-bearing GeoJSON/KMZ export; already covered by private map/field-output contracts.",
    },
    "cell_238": {
        "role": "probability_target_engine",
        "status": "upstream_dependency",
        "reason": "Produces final_targets from probability map; item #39 gates this dependency.",
    },
    "cell_240": {
        "role": "final_decision_scanner",
        "status": "blocked_dependency",
        "reason": "Uses torch/probabilities and prints exact coordinates.",
    },
    "cell_241": {
        "role": "field_navigation_geojson_kmz",
        "status": "excluded_from_item_40",
        "reason": "Writes coordinate-bearing GeoJSON/KMZ, not safe as public route output.",
    },
    "cell_243": {
        "role": "live_overlay_path_line",
        "status": "already_replaced_by_item_38_and_gated_by_item_39",
        "reason": "Draws live map line from exact target coordinates; route display remains gated.",
    },
}

REQUIRED_PATH_TRACING_GATES = (
    "item_39_probability_overlay_gate_exists",
    "item_32_inference_gate_exists",
    "item_39_probability_overlay_approved",
    "probability_map_exists",
    "target_records_exist",
    "stairs_seed_available",
    "exact_coordinate_policy_approved",
    "private_route_storage_policy_approved",
    "operator_route_preview_policy_approved",
)

FUTURE_PRIVATE_OUTPUTS_IF_APPROVED = {
    "path_trace_json": "QA/AI_GPS_PATH_TRACE_V7_2.json",
    "path_trace_csv": "QA/AI_GPS_PATH_TRACE_V7_2.csv",
    "redacted_path_summary": "manifests/AI_GPS_PATH_TRACE_REDACTED_SUMMARY_V7_2.json",
    "route_geojson_private": "QA/AI_GPS_PATH_TRACE_PRIVATE.geojson",
    "route_kmz_private": "QA/AI_GPS_PATH_TRACE_PRIVATE.kmz",
}

PATH_TRACE_CONTRACT = {
    "input_probability_map": "AI_INFERENCE_STAGE5/AI_MODEL_PROBABILITIES_640.npy",
    "input_target_records": "QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.json",
    "canonical_seed": "detected stairs/staircase pixel from approved target records",
    "roi_window_px": [40, 40],
    "class_scan_range": [1, 2, 3],
    "minimum_probability": 0.15,
    "score_formula": "min(max_probability * 100 + 35, 99.1)",
    "coordinate_policy": "exact coordinates remain private/operator-only",
}


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


def build_plan_b40_gps_path_tracing_gate_payload(
    *,
    run_dir: str | Path,
    run_id: str,
) -> dict[str, object]:
    run_dir = Path(run_dir)
    upstream = _file_status(run_dir)

    item39_payload = _read_json(run_dir / EXPECTED_UPSTREAM_FILES["item_39_probability_overlay_gate"])
    item39_overlay_approved = bool(item39_payload.get("approved_for_probability_overlay", False))

    target_records_exist = bool(upstream["future_inference_json"]["exists"]) and bool(
        upstream["future_inference_csv"]["exists"]
    )

    gate_status = {
        "item_39_probability_overlay_gate_exists": bool(upstream["item_39_probability_overlay_gate"]["exists"]),
        "item_32_inference_gate_exists": bool(upstream["item_32_inference_gate"]["exists"]),
        "item_39_probability_overlay_approved": item39_overlay_approved,
        "probability_map_exists": bool(upstream["future_probability_map"]["exists"]),
        "target_records_exist": target_records_exist,
        "stairs_seed_available": False,
        "exact_coordinate_policy_approved": False,
        "private_route_storage_policy_approved": False,
        "operator_route_preview_policy_approved": False,
    }

    approved_for_path_tracing = all(gate_status.values())

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "source_cell": SOURCE_CELL,
        "source_notebook_family": SOURCE_NOTEBOOK_FAMILY,
        "status": "implemented_gps_path_tracing_gate_only",
        "privacy": "FILESYSTEM_ONLY",
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,

        "uses_geemap": False,
        "imports_earth_engine": False,
        "imports_torch": False,
        "runs_model_inference": False,
        "reads_probability_map": False,
        "creates_path_trace": False,
        "creates_route_geojson": False,
        "creates_route_kmz": False,
        "creates_public_route": False,
        "exposes_exact_coordinates": False,
        "raw_geometry_in_manifest": False,
        "exact_coordinates_in_manifest": False,

        "selected_canonical_path_tracing_cell": SOURCE_CELL,
        "source_cell_decisions": SOURCE_CELL_DECISIONS,
        "required_path_tracing_gates": list(REQUIRED_PATH_TRACING_GATES),
        "gate_status": gate_status,
        "upstream_file_status": upstream,
        "approved_for_gps_path_tracing": approved_for_path_tracing,
        "blocked_reason": None if approved_for_path_tracing else (
            "GPS/path tracing is blocked until real #32/#39 probability outputs, "
            "stairs seed records, exact-coordinate policy, private route storage, "
            "and operator route preview gates are approved."
        ),

        "path_trace_contract": PATH_TRACE_CONTRACT,
        "future_private_outputs_if_approved": FUTURE_PRIVATE_OUTPUTS_IF_APPROVED,
        "replacement_policy": {
            "public_route_not_created": True,
            "public_geojson_not_created": True,
            "public_kmz_not_created": True,
            "coordinate_bearing_outputs_private_only": True,
            "operator_preview_must_be_redacted": True,
        },
        "next_dependency_unblocking_item": "Plan B complete or approved continuation of #40 after real detector/path outputs exist",
        "notes": (
            "This ports the GPS/path-tracing notebook behavior as a gated readiness manifest only. "
            "It intentionally does not read probability maps, compute path findings, convert pixels to GPS, "
            "write route GeoJSON/KMZ, or expose coordinates."
        ),
    }


def write_plan_b40_gps_path_tracing_gate_report(
    run_dir: str | Path,
    run_id: str,
    *,
    report_relative_path: str | Path = REPORT_RELATIVE_PATH,
) -> Path:
    report_path = Path(run_dir) / Path(report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_plan_b40_gps_path_tracing_gate_payload(run_dir=run_dir, run_id=run_id)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report_path
