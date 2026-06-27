import json

from app.pipeline.parity.final_probability_overlay_gate import (
    REQUIRED_OVERLAY_GATES,
    SOURCE_CELL,
    build_plan_b39_final_probability_overlay_gate_payload,
    write_plan_b39_final_probability_overlay_gate_report,
)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_plan_b39_selects_cell_238_and_keeps_geemap_cell_as_existing_shell(tmp_path):
    payload = build_plan_b39_final_probability_overlay_gate_payload(run_dir=tmp_path, run_id="run-39")

    assert payload["source_cell"] == "cell_238"
    assert payload["selected_canonical_probability_overlay_cell"] == "cell_238"

    cells = payload["source_cell_decisions"]
    assert cells["cell_238"]["status"] == "selected_gate_source"
    assert cells["cell_243"]["status"] == "already_replaced_by_item_38"
    assert cells["cell_242"]["next_item"] == "Plan B item #40"
    assert cells["cell_169"]["status"] == "blocked_dependency"


def test_plan_b39_payload_is_gate_only_not_overlay_execution(tmp_path):
    payload = build_plan_b39_final_probability_overlay_gate_payload(run_dir=tmp_path, run_id="run-39")

    assert payload["source_cell"] == SOURCE_CELL
    assert payload["status"] == "implemented_probability_overlay_gate_only"
    assert payload["privacy"] == "FILESYSTEM_ONLY"
    assert payload["http_servable"] is False
    assert payload["frontend_visible"] is False
    assert payload["downloadable_via_api"] is False

    assert payload["uses_geemap"] is False
    assert payload["imports_earth_engine"] is False
    assert payload["imports_torch"] is False
    assert payload["runs_model_inference"] is False
    assert payload["creates_probability_map"] is False
    assert payload["creates_overlay_tiles"] is False
    assert payload["creates_markers"] is False
    assert payload["creates_geojson"] is False
    assert payload["creates_kmz"] is False
    assert payload["exposes_exact_coordinates"] is False
    assert payload["raw_geometry_in_manifest"] is False
    assert payload["exact_coordinates_in_manifest"] is False


def test_plan_b39_remains_blocked_without_probability_map_even_with_upstream_manifests(tmp_path):
    _write_json(
        tmp_path / "manifests" / "AI_FINAL_INFERENCE_GATE_V7_2.json",
        {"approved_for_real_inference": False},
    )
    _write_json(
        tmp_path / "full_job" / "focus" / "APP_NATIVE_LIVE_OVERLAY_MANIFEST_V7_2.json",
        {"type": "AppNativeLiveOverlayManifest"},
    )

    payload = build_plan_b39_final_probability_overlay_gate_payload(run_dir=tmp_path, run_id="run-39")

    assert tuple(payload["required_overlay_gates"]) == REQUIRED_OVERLAY_GATES

    gate_status = payload["gate_status"]
    assert gate_status["item_32_inference_gate_exists"] is True
    assert gate_status["item_38_live_overlay_manifest_exists"] is True
    assert gate_status["item_32_real_inference_approved"] is False
    assert gate_status["probability_map_exists"] is False
    assert gate_status["target_records_exist"] is False
    assert payload["approved_for_probability_overlay"] is False
    assert "blocked" in payload["blocked_reason"].lower()


def test_plan_b39_report_writes_private_json_only(tmp_path):
    report_path = write_plan_b39_final_probability_overlay_gate_report(tmp_path, "run-39")

    assert report_path == tmp_path / "manifests" / "AI_FINAL_PROBABILITY_OVERLAY_GATE_V7_2.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["source_cell"] == "cell_238"
    assert payload["status"] == "implemented_probability_overlay_gate_only"
    assert payload["approved_for_probability_overlay"] is False
    assert payload["layer_count"] == len(payload["overlay_layer_contract"])

    created = [path for path in tmp_path.rglob("*") if path.is_file()]
    assert created == [report_path]


def test_plan_b39_module_does_not_expose_overlay_or_model_execution_functions():
    import app.pipeline.parity.final_probability_overlay_gate as module

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
        "create_tiles_",
        "write_geojson_",
        "write_kmz_",
    )
    forbidden = [name for name in dir(module) if name.startswith(forbidden_prefixes)]

    assert forbidden == []
