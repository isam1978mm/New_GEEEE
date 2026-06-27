import json

from app.pipeline.parity.gps_path_tracing_gate import (
    REQUIRED_PATH_TRACING_GATES,
    SOURCE_CELL,
    build_plan_b40_gps_path_tracing_gate_payload,
    write_plan_b40_gps_path_tracing_gate_report,
)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_plan_b40_selects_cell_242_and_classifies_supporting_cells(tmp_path):
    payload = build_plan_b40_gps_path_tracing_gate_payload(run_dir=tmp_path, run_id="run-40")

    assert payload["source_cell"] == "cell_242"
    assert payload["selected_canonical_path_tracing_cell"] == "cell_242"

    cells = payload["source_cell_decisions"]
    assert cells["cell_242"]["status"] == "selected_gate_source"
    assert cells["cell_227"]["status"] == "supporting_reference_only"
    assert cells["cell_228"]["status"] == "supporting_reference_only"
    assert cells["cell_238"]["status"] == "upstream_dependency"
    assert cells["cell_243"]["status"] == "already_replaced_by_item_38_and_gated_by_item_39"


def test_plan_b40_payload_is_gate_only_not_path_execution(tmp_path):
    payload = build_plan_b40_gps_path_tracing_gate_payload(run_dir=tmp_path, run_id="run-40")

    assert payload["source_cell"] == SOURCE_CELL
    assert payload["status"] == "implemented_gps_path_tracing_gate_only"
    assert payload["privacy"] == "FILESYSTEM_ONLY"
    assert payload["http_servable"] is False
    assert payload["frontend_visible"] is False
    assert payload["downloadable_via_api"] is False

    assert payload["uses_geemap"] is False
    assert payload["imports_earth_engine"] is False
    assert payload["imports_torch"] is False
    assert payload["runs_model_inference"] is False
    assert payload["reads_probability_map"] is False
    assert payload["creates_path_trace"] is False
    assert payload["creates_route_geojson"] is False
    assert payload["creates_route_kmz"] is False
    assert payload["creates_public_route"] is False
    assert payload["exposes_exact_coordinates"] is False
    assert payload["raw_geometry_in_manifest"] is False
    assert payload["exact_coordinates_in_manifest"] is False


def test_plan_b40_remains_blocked_without_real_probability_outputs_even_with_upstream_gates(tmp_path):
    _write_json(
        tmp_path / "manifests" / "AI_FINAL_PROBABILITY_OVERLAY_GATE_V7_2.json",
        {"approved_for_probability_overlay": False},
    )
    _write_json(
        tmp_path / "manifests" / "AI_FINAL_INFERENCE_GATE_V7_2.json",
        {"approved_for_real_inference": False},
    )

    payload = build_plan_b40_gps_path_tracing_gate_payload(run_dir=tmp_path, run_id="run-40")

    assert tuple(payload["required_path_tracing_gates"]) == REQUIRED_PATH_TRACING_GATES

    gate_status = payload["gate_status"]
    assert gate_status["item_39_probability_overlay_gate_exists"] is True
    assert gate_status["item_32_inference_gate_exists"] is True
    assert gate_status["item_39_probability_overlay_approved"] is False
    assert gate_status["probability_map_exists"] is False
    assert gate_status["target_records_exist"] is False
    assert gate_status["stairs_seed_available"] is False
    assert payload["approved_for_gps_path_tracing"] is False
    assert "blocked" in payload["blocked_reason"].lower()


def test_plan_b40_report_writes_private_json_only(tmp_path):
    report_path = write_plan_b40_gps_path_tracing_gate_report(tmp_path, "run-40")

    assert report_path == tmp_path / "manifests" / "AI_GPS_PATH_TRACING_GATE_V7_2.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["source_cell"] == "cell_242"
    assert payload["status"] == "implemented_gps_path_tracing_gate_only"
    assert payload["approved_for_gps_path_tracing"] is False

    created = [path for path in tmp_path.rglob("*") if path.is_file()]
    assert created == [report_path]


def test_plan_b40_module_does_not_expose_route_or_model_execution_functions():
    import app.pipeline.parity.gps_path_tracing_gate as module

    forbidden_prefixes = (
        "train_",
        "fit_",
        "learn_",
        "infer_",
        "predict_",
        "run_model_",
        "load_model_",
        "download_",
        "install_",
        "forward_",
        "trace_",
        "create_route_",
        "write_geojson_",
        "write_kmz_",
    )
    forbidden = [name for name in dir(module) if name.startswith(forbidden_prefixes)]

    assert forbidden == []
