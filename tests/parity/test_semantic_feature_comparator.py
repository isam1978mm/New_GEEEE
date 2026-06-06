from __future__ import annotations

import inspect
import json
from pathlib import Path

import numpy as np

from app.pipeline.parity.semantic_feature_comparator import (
    PHASE_C_SEMANTIC_FEATURE_OUTPUT_NAMES,
    PHASE_E3_SEMANTIC_FEATURE_COMPARATOR_SCHEMA_VERSION,
    compare_phase_c_semantic_features,
)


FORBIDDEN_ARTIFACT_SUFFIXES = {
    ".tif",
    ".tiff",
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
}


def _write_array(root: Path, output_name: str, values: object) -> Path:
    path = root / f"{output_name}.npy"
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.asarray(values, dtype=np.float32))
    return path


def _matching_dirs(tmp_path: Path) -> tuple[Path, Path]:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    for index, output_name in enumerate(PHASE_C_SEMANTIC_FEATURE_OUTPUT_NAMES):
        values = np.array([[index, index + 1.0], [np.nan, index + 2.0]], dtype=np.float32)
        _write_array(app_dir, output_name, values)
        _write_array(reference_dir, output_name, values)
    return app_dir, reference_dir


def test_comparator_passes_for_exact_matching_tiny_arrays(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_dirs(tmp_path)

    result = compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e3-exact",
    )

    assert result.overall_status == "passed"
    assert result.runtime_output_verified is True
    assert result.notebook_value_parity_verified is True
    assert {item["status"] for item in result.results} == {"passed"}


def test_comparator_passes_for_arrays_within_tolerance(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    output_name = "AI_BEH_VegRoot_REL_ND_DOM_lin_640"
    _write_array(app_dir, output_name, [[1.000001, 2.0]])
    _write_array(reference_dir, output_name, [[1.0, 2.0]])

    result = compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e3-tolerance",
        selected_outputs=(output_name,),
        atol=1e-5,
        rtol=1e-6,
    )

    assert result.overall_status == "passed"
    assert result.results[0]["max_abs_error"] < 1e-5


def test_comparator_fails_for_numeric_mismatch_above_tolerance(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    output_name = "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640"
    _write_array(app_dir, output_name, [[2.0]])
    _write_array(reference_dir, output_name, [[1.0]])

    result = compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e3-numeric-mismatch",
        selected_outputs=(output_name,),
        atol=1e-6,
        rtol=1e-6,
    )

    assert result.overall_status == "failed"
    assert result.results[0]["status"] == "failed"
    assert result.results[0]["notebook_value_parity_verified"] is False


def test_comparator_fails_for_shape_mismatch(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    output_name = "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640"
    _write_array(app_dir, output_name, [[1.0, 2.0]])
    _write_array(reference_dir, output_name, [[1.0], [2.0]])

    result = compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e3-shape",
        selected_outputs=(output_name,),
    )

    assert result.overall_status == "failed"
    assert result.results[0]["status"] == "failed"
    assert result.results[0]["shape_match"] is False


def test_comparator_treats_matching_nan_positions_as_equal(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    output_name = "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640"
    _write_array(app_dir, output_name, [[np.nan, 1.0]])
    _write_array(reference_dir, output_name, [[np.nan, 1.0]])

    result = compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e3-nan-match",
        selected_outputs=(output_name,),
    )

    assert result.results[0]["status"] == "passed"
    assert result.results[0]["notebook_value_parity_verified"] is True


def test_comparator_fails_for_nan_position_mismatch(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    output_name = "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640"
    _write_array(app_dir, output_name, [[np.nan, 1.0]])
    _write_array(reference_dir, output_name, [[1.0, 1.0]])

    result = compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e3-nan-mismatch",
        selected_outputs=(output_name,),
    )

    assert result.overall_status == "failed"
    assert result.results[0]["status"] == "failed"
    assert result.results[0]["notes"] == "NaN positions differ."


def test_missing_reference_returns_reference_missing_not_passed(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    output_name = "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640"
    _write_array(app_dir, output_name, [[1.0]])

    result = compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e3-missing-reference",
        selected_outputs=(output_name,),
    )

    assert result.overall_status == "incomplete"
    assert result.results[0]["status"] == "reference_missing"
    assert result.notebook_value_parity_verified is False


def test_missing_app_output_returns_app_output_missing_not_passed(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    output_name = "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640"
    _write_array(reference_dir, output_name, [[1.0]])

    result = compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e3-missing-app",
        selected_outputs=(output_name,),
    )

    assert result.overall_status == "incomplete"
    assert result.results[0]["status"] == "app_output_missing"
    assert result.runtime_output_verified is False


def test_selected_output_filtering_works(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_dirs(tmp_path)
    selected = ("AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640",)

    result = compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e3-filter",
        selected_outputs=selected,
    )

    assert [item["output_name"] for item in result.results] == list(selected)
    assert result.selected_outputs == selected


def test_comparator_accepts_in_memory_array_inputs(tmp_path: Path) -> None:
    output_name = "AI_BEH_VegRoot_REL_ND_DOM_lin_640"

    result = compare_phase_c_semantic_features(
        app_output_dir=tmp_path / "unused-app",
        reference_bundle_dir=tmp_path / "unused-refs",
        run_dir=tmp_path / "run",
        run_id="phase-e3-memory-arrays",
        selected_outputs=(output_name,),
        app_arrays={output_name: np.array([[1.0, np.nan]], dtype=np.float32)},
        reference_arrays={output_name: np.array([[1.0, np.nan]], dtype=np.float32)},
    )

    assert result.overall_status == "passed"
    assert result.results[0]["status"] == "passed"


def test_comparison_unavailable_does_not_pass(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "refs"
    output_name = "AI_BEH_VegRoot_REL_ND_DOM_lin_640"
    app_path = app_dir / f"{output_name}.npy"
    reference_path = reference_dir / f"{output_name}.npy"
    app_path.parent.mkdir(parents=True, exist_ok=True)
    reference_path.parent.mkdir(parents=True, exist_ok=True)
    app_path.write_text("not an array", encoding="utf-8")
    reference_path.write_text("not an array", encoding="utf-8")

    result = compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e3-unavailable",
        selected_outputs=(output_name,),
    )

    assert result.overall_status == "comparison_unavailable"
    assert result.results[0]["status"] == "comparison_unavailable"
    assert result.notebook_value_parity_verified is False


def test_all_six_phase_c_canonical_output_names_are_supported() -> None:
    assert PHASE_C_SEMANTIC_FEATURE_OUTPUT_NAMES == (
        "AI_BEH_VegRoot_REL_ND_DOM_lin_640",
        "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640",
        "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640",
        "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640",
        "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640",
        "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640",
    )


def test_overall_status_rules_are_enforced(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_dirs(tmp_path)
    mismatch_name = "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640"
    _write_array(app_dir, mismatch_name, [[10.0]])
    _write_array(reference_dir, mismatch_name, [[1.0]])

    result = compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e3-overall",
    )

    assert result.overall_status == "failed"
    assert result.notebook_value_parity_verified is False
    assert result.runtime_output_verified is True


def test_report_writes_and_parses_under_run_dir(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_dirs(tmp_path)
    run_dir = tmp_path / "run"

    result = compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase-e3-report",
        selected_outputs=("AI_BEH_VegRoot_REL_ND_DOM_lin_640",),
    )
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))

    assert result.report_path == run_dir / "manifests" / "phase_e3_semantic_feature_comparator.json"
    assert result.report_path.resolve().relative_to(run_dir.resolve())
    assert payload["schema_version"] == PHASE_E3_SEMANTIC_FEATURE_COMPARATOR_SCHEMA_VERSION
    assert payload["comparator_id"] == "phase_e3_semantic_feature_comparator"
    assert payload["phase_e3_comparator_only"] is True
    assert payload["runtime_added"] is False
    assert payload["writer_added"] is False
    assert payload["earth_engine_calls_added"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["artifact_generation"] is False


def test_report_creates_no_output_artifacts_under_run_dir(tmp_path: Path) -> None:
    app_dir, reference_dir = _matching_dirs(tmp_path)
    run_dir = tmp_path / "run"

    compare_phase_c_semantic_features(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase-e3-no-artifacts",
        selected_outputs=("AI_BEH_VegRoot_REL_ND_DOM_lin_640",),
    )

    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created == []


def test_comparator_adds_no_earth_engine_runtime_or_public_serving_calls() -> None:
    import app.pipeline.parity.semantic_feature_comparator as module

    source = inspect.getsource(module)

    assert "ee.Authenticate" not in source
    assert "import ee" not in source
    assert "earthengine" not in source.lower()
    assert "google.colab" not in source
    assert "drive.mount" not in source
    assert "/content/drive" not in source
    assert "enqueue_core_pipeline_run" not in source
    assert "run_core_pipeline" not in source
    assert "serve_artifact_response" not in source
    assert "can_serve_artifact" not in source
    assert "FileResponse" not in source
    assert "StreamingResponse" not in source
