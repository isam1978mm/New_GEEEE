import json

from app.pipeline.parity.ai_requirements_mapper import (
    AI_REQUIREMENTS_MAPPER_SCHEMA_VERSION,
    MODEL_FAMILIES,
    REQUIRED_CORE_BANDS,
    build_plan_b28_ai_requirements_mapper_payload,
    get_plan_b28_ai_requirements,
    write_plan_b28_ai_requirements_mapper_report,
)


def test_plan_b28_requirements_include_expected_model_families():
    requirements = get_plan_b28_ai_requirements()
    families = {item.model_family for item in requirements}

    assert families == set(MODEL_FAMILIES)
    assert {"YOLOv11", "CNN", "Swin", "SegFormer", "UnetPlusPlus"} <= families

    for item in requirements:
        assert item.implementation_status == "requirements_mapped_only"
        assert item.next_item == "Plan B item #29"
        assert item.required_bands == REQUIRED_CORE_BANDS
        assert item.blockers


def test_plan_b28_payload_is_private_planning_only():
    payload = build_plan_b28_ai_requirements_mapper_payload(run_id="run-28")

    assert payload["schema_version"] == AI_REQUIREMENTS_MAPPER_SCHEMA_VERSION
    assert payload["run_id"] == "run-28"
    assert payload["source_cell"] == "cell_140"
    assert payload["status"] == "implemented_requirements_mapper_only"
    assert payload["privacy"] == "FILESYSTEM_ONLY"
    assert payload["http_servable"] is False
    assert payload["frontend_visible"] is False
    assert payload["downloadable_via_api"] is False
    assert payload["trains_models"] is False
    assert payload["runs_inference"] is False
    assert payload["downloads_weights"] is False
    assert payload["adds_heavy_ml_dependencies"] is False
    assert payload["creates_model_artifacts"] is False
    assert payload["notebook_value_parity_verified"] is False
    assert payload["next_dependency_unblocking_item"].startswith("Plan B item #29")


def test_plan_b28_report_writes_only_json_manifest(tmp_path):
    run_dir = tmp_path / "run"
    report_path = write_plan_b28_ai_requirements_mapper_report(run_dir, "run-28")

    assert report_path == run_dir / "manifests" / "AI_MODEL_REQUIREMENTS_MAPPER_V7_2.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["source_cell"] == "cell_140"
    assert len(payload["requirements"]) == len(MODEL_FAMILIES)

    created = [path for path in run_dir.rglob("*") if path.is_file()]
    assert created == [report_path]
    assert report_path.suffix == ".json"


def test_plan_b28_module_does_not_expose_model_execution_functions():
    import app.pipeline.parity.ai_requirements_mapper as module

    forbidden_prefixes = (
        "train_",
        "infer_",
        "predict_",
        "classify_",
        "run_model_",
        "load_model_",
        "download_",
    )
    forbidden = [name for name in dir(module) if name.startswith(forbidden_prefixes)]

    assert forbidden == []
