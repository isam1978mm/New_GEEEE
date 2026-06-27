import json
from pathlib import Path

from app.pipeline.parity.ai_final_inference_gate import (
    EXPECTED_UPSTREAM_FILES,
    REQUIRED_INFERENCE_GATES,
    SOURCE_CELL,
    build_plan_b32_ai_final_inference_gate_payload,
    write_plan_b32_ai_final_inference_gate_report,
)


def _write_upstream_files(run_dir):
    for rel in EXPECTED_UPSTREAM_FILES.values():
        path = run_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"placeholder")


def test_plan_b32_selects_cell_169_and_excludes_map_exports():
    payload = build_plan_b32_ai_final_inference_gate_payload(run_dir=Path("/tmp/not-existing"), run_id="run-32")

    assert payload["source_cell"] == "cell_169"
    assert payload["selected_canonical_inference_cell"] == "cell_169"

    cells = payload["inference_source_cells"]
    assert cells["cell_169"]["status"] == "selected_gate_source"
    assert cells["cell_236"]["status"] == "secondary_inference_reference"
    assert cells["cell_237"]["status"] == "excluded_from_item_32"


def test_plan_b32_payload_is_gate_only_not_model_execution(tmp_path):
    _write_upstream_files(tmp_path)
    payload = build_plan_b32_ai_final_inference_gate_payload(run_dir=tmp_path, run_id="run-32")

    assert payload["source_cell"] == SOURCE_CELL
    assert payload["status"] == "implemented_inference_gate_only"
    assert payload["privacy"] == "FILESYSTEM_ONLY"
    assert payload["http_servable"] is False
    assert payload["frontend_visible"] is False
    assert payload["downloadable_via_api"] is False

    assert payload["normal_app_runs_must_run_inference"] is False
    assert payload["normal_app_runs_must_import_torch"] is False
    assert payload["normal_app_runs_must_load_weights"] is False
    assert payload["normal_app_runs_must_instantiate_model"] is False
    assert payload["normal_app_runs_must_write_coordinate_outputs"] is False
    assert payload["normal_app_runs_must_write_probability_maps"] is False
    assert payload["normal_app_runs_must_write_geojson_or_kmz"] is False

    assert payload["imports_torch"] is False
    assert payload["loads_model"] is False
    assert payload["loads_weights"] is False
    assert payload["runs_forward_pass"] is False
    assert payload["creates_probability_map"] is False
    assert payload["creates_target_csv"] is False
    assert payload["creates_target_json"] is False
    assert payload["creates_geojson"] is False
    assert payload["creates_kmz"] is False
    assert payload["exposes_exact_coordinates"] is False


def test_plan_b32_gates_block_real_inference_even_when_upstream_exists(tmp_path):
    _write_upstream_files(tmp_path)
    payload = build_plan_b32_ai_final_inference_gate_payload(run_dir=tmp_path, run_id="run-32")

    assert tuple(payload["required_inference_gates"]) == REQUIRED_INFERENCE_GATES
    assert payload["upstream_tensor_policy_ready"] is True

    gate_status = payload["gate_status"]
    assert gate_status["item_29_tensor_outputs_exist"] is True
    assert gate_status["item_30_training_workflow_boundary_exists"] is True
    assert gate_status["item_31_model_build_policy_exists"] is True
    assert gate_status["offline_weights_available_and_approved"] is False
    assert gate_status["ml_dependency_sandbox_approved"] is False
    assert payload["approved_for_real_inference"] is False
    assert "blocked" in payload["blocked_reason"].lower()


def test_plan_b32_report_writes_private_json_only(tmp_path):
    _write_upstream_files(tmp_path)
    report_path = write_plan_b32_ai_final_inference_gate_report(tmp_path, "run-32")

    assert report_path == tmp_path / "manifests" / "AI_FINAL_INFERENCE_GATE_V7_2.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["source_cell"] == "cell_169"
    assert payload["status"] == "implemented_inference_gate_only"
    assert payload["approved_for_real_inference"] is False

    created = [path for path in tmp_path.rglob("*") if path.is_file()]
    assert report_path in created
    assert report_path.suffix == ".json"


def test_plan_b32_module_does_not_expose_model_execution_functions():
    import app.pipeline.parity.ai_final_inference_gate as module

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
        "forward_",
    )
    forbidden = [name for name in dir(module) if name.startswith(forbidden_prefixes)]

    assert forbidden == []
