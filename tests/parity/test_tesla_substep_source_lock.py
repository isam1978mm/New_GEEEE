import json
import re
from pathlib import Path

from app.pipeline.parity import tesla_substep_source_lock as source_lock


EXPECTED_OUTPUTS = {
    "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif",
    "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif",
    "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif",
}

EXPECTED_FORMULAS = {
    "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif": "B12 / B11",
    "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif": "B4 / B2",
    "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif": "(B8 + B4) / (B11 + 0.001)",
}


def _claim_terms() -> tuple[str, ...]:
    return (
        "con" + "firmed",
        "fou" + "nd",
        "pro" + "ven",
        "dig " + "target",
        "defi" + "nitely",
        "dis" + "covery",
        "burial " + "pro" + "ven",
        "tomb " + "con" + "firmed",
        "target " + "con" + "firmed",
    )


def test_source_lock_item_selects_exactly_one_coherent_family() -> None:
    item = source_lock.get_future_slice_j2_source_lock_item()

    assert item.id == "future_slice_j2_ai_beh_extended_source_lock"
    assert item.selected_substep_name == "AI_BEH extended semantic rasters"
    assert item.selected_outputs == tuple(sorted(EXPECTED_OUTPUTS))
    assert item.output_names == tuple(sorted(EXPECTED_OUTPUTS))
    assert item.source_lock_status == "source_locked_for_future_phase_c2"
    assert item.implementation_ready is True


def test_source_contracts_modules_formulas_and_inputs_are_locked() -> None:
    item = source_lock.get_future_slice_j2_source_lock_item()

    assert "docs/AI_BEH_EXTENDED_PARITY_CONTRACT.md" in item.source_contracts
    assert "app/pipeline/parity/ai_beh_extended_recovery.py" in item.source_recovery_modules
    assert item.notebook_evidence_summary
    assert item.formulas == EXPECTED_FORMULAS
    assert set(item.required_input_bands_or_arrays) == {"B2", "B4", "B8", "B11", "B12"}


def test_private_boundary_and_no_public_exposure_are_locked() -> None:
    item = source_lock.get_future_slice_j2_source_lock_item()

    assert item.privacy_boundary == "private_notebook_parity_only"
    assert item.clean_app_allowed is False
    assert item.parity_private_allowed is True
    assert item.http_servable is False
    assert item.frontend_visible is False
    assert item.downloadable_via_api is False
    assert item.earth_engine_required_for_tests is False


def test_metadata_blockers_and_phase_c2_scope_are_explicit() -> None:
    item = source_lock.get_future_slice_j2_source_lock_item()

    assert item.expected_shape_policy
    assert item.expected_dtype_policy
    assert item.nodata_or_nan_policy
    assert item.grid_metadata_policy
    assert item.implementation_blockers
    assert "Phase C2" in item.recommended_phase_c_followup_scope
    assert "Phase C2" in item.recommended_next_slice
    assert "frozen reference comparison" in item.notebook_value_parity_requirement
    assert item.frozen_reference_requirement
    assert item.tests_required_for_implementation


def test_report_writes_json_under_run_dir_without_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    report_path = source_lock.write_future_slice_j2_source_lock_report(
        run_dir=run_dir,
        run_id="j2-test-run",
    )

    assert report_path == run_dir / "manifests" / "future_slice_j2_source_lock_report.json"
    assert report_path.resolve().is_relative_to(run_dir.resolve())
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "j2-test-run"
    assert payload["source_lock_status"] == "source_locked_for_future_phase_c2"
    assert payload["recommended_next_slice"] == "Phase C2 separate implementation slice"
    assert payload["j2_source_lock_only"] is True
    assert payload["runtime_added"] is False
    assert payload["writer_added"] is False
    assert payload["artifact_generation"] is False
    assert payload["earth_engine_calls_added"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["selected_substep"]["selected_outputs"] == sorted(EXPECTED_OUTPUTS)

    blocked_suffixes = {
        ".tif",
        ".tiff",
        ".npy",
        ".geojson",
        ".kmz",
        ".kml",
        ".html",
        ".png",
        ".jpg",
        ".jpeg",
        ".csv",
        ".pt",
        ".pth",
        ".onnx",
        ".h5",
        ".pkl",
        ".joblib",
        ".parquet",
        ".sqlite",
        ".db",
        ".jsonl",
    }
    created = [path for path in run_dir.rglob("*") if path.is_file()]
    assert created == [report_path]
    assert not any(path.suffix.lower() in blocked_suffixes for path in created)


def test_source_lock_module_has_no_runtime_writer_or_heavy_hooks() -> None:
    source = Path(source_lock.__file__).read_text(encoding="utf-8")

    blocked_tokens = [
        "import ee",
        "ee.Authenticate",
        "earthengine",
        "import torch",
        "import tensorflow",
        "import keras",
        "ultralytics",
        "segmentation_models_pytorch",
        "APIRouter",
        "BackgroundTasks",
        "serve_artifact_response",
        "can_serve_artifact",
        "requests.get",
        "urlretrieve",
        "run_orchestrator",
        "run_core_pipeline",
        "np.save",
        "rasterio",
        "FileResponse",
    ]
    for token in blocked_tokens:
        assert token not in source


def test_no_forbidden_claim_wording_in_j2_docs_or_code() -> None:
    paths = [
        Path(source_lock.__file__),
        Path("docs/FUTURE_SLICE_J2_TESLA_SUBSTEP_SOURCE_LOCK.md"),
    ]
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for term in _claim_terms():
            pattern = re.compile(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])")
            assert not pattern.search(text)
