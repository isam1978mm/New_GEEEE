from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.pipeline.parity.end_to_end_harness import EndToEndFamilyResult, FamilyDefinition
from app.pipeline.parity.frozen_reference_verifier import (
    PHASE_E_FROZEN_REFERENCE_VERIFIER_SCHEMA_VERSION,
    REQUIRED_PHASE_E_FAMILIES,
    run_private_frozen_reference_verifier,
    validate_frozen_reference_bundle,
)


FORBIDDEN_ARTIFACT_SUFFIXES = {
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
}


def _write_manifest(bundle_dir: Path, files_by_family: dict[str, list[str]]) -> None:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "frozen_notebook_reference_bundle_v1",
        "bundle_id": "fake-bundle",
        "captured_at": "2026-01-01T00:00:00Z",
        "notebook_source": "notebooks/new.ipynb",
        "families": sorted(files_by_family),
        "files": files_by_family,
        "notes": "tiny fake bundle for tests",
    }
    (bundle_dir / "manifest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _touch_family_file(bundle_dir: Path, family_id: str, filename: str) -> Path:
    path = bundle_dir / "references" / family_id / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("tiny reference", encoding="utf-8")
    return path


def _touch_app_file(app_dir: Path, filename: str) -> Path:
    path = app_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("tiny app output", encoding="utf-8")
    return path


def _stub_family(family_id: str, status: str) -> EndToEndFamilyResult:
    return EndToEndFamilyResult(
        family_id=family_id,
        contract_doc="docs/stub.md",
        module_used="stub",
        expected_reference_artifacts=("stub-reference",),
        app_output_status="present",
        reference_status="present",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        comparison_status=status,
        status=status,
        blocker="stub blocker",
        recommended_next_action="stub next",
        notes="stub notes",
    )


def test_valid_fake_reference_bundle_validates(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    _write_manifest(bundle_dir, {"phase_c_semantic_feature_writers": ["feature.npy"]})
    _touch_family_file(bundle_dir, "phase_c_semantic_feature_writers", "feature.npy")

    validation = validate_frozen_reference_bundle(bundle_dir)

    assert validation.status == "present"
    assert validation.bundle_id == "fake-bundle"
    assert validation.files_by_family == {
        "phase_c_semantic_feature_writers": ("feature.npy",)
    }


def test_missing_reference_bundle_reports_reference_missing(tmp_path: Path) -> None:
    result = run_private_frozen_reference_verifier(
        app_output_dir=tmp_path / "app",
        reference_bundle_dir=tmp_path / "missing-bundle",
        run_dir=tmp_path / "run",
        run_id="phase-e-missing-bundle",
        selected_families=("report_640",),
    )

    assert result.reference_bundle_status == "reference_missing"
    assert result.overall_status == "incomplete"
    assert result.families[0].status == "reference_missing"
    assert result.notebook_value_parity_verified is False


def test_malformed_manifest_reports_error_safely(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    bundle_dir = tmp_path / "bundle"
    app_dir.mkdir()
    bundle_dir.mkdir()
    (bundle_dir / "manifest.json").write_text("{not-json", encoding="utf-8")

    result = run_private_frozen_reference_verifier(
        app_output_dir=app_dir,
        reference_bundle_dir=bundle_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e-bad-manifest",
        selected_families=("report_640",),
    )

    assert result.reference_bundle_status == "error"
    assert result.overall_status == "error"
    assert result.families[0].status == "error"


def test_selected_family_filtering_works(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    bundle_dir = tmp_path / "bundle"
    app_dir.mkdir()
    _write_manifest(
        bundle_dir,
        {
            "phase_c_semantic_feature_writers": ["AI_BEH_VegRoot_REL_ND_DOM_lin_640.npy"],
            "phase_d_private_geojson_writer": ["private_features.geojson"],
        },
    )

    result = run_private_frozen_reference_verifier(
        app_output_dir=app_dir,
        reference_bundle_dir=bundle_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e-filter",
        selected_families=("phase_d_private_geojson_writer",),
    )

    assert [family.family_id for family in result.families] == [
        "phase_d_private_geojson_writer"
    ]


def test_missing_family_reference_files_are_reference_missing_not_passed(
    tmp_path: Path,
) -> None:
    app_dir = tmp_path / "app"
    bundle_dir = tmp_path / "bundle"
    app_dir.mkdir()
    _write_manifest(
        bundle_dir,
        {"phase_c_semantic_feature_writers": ["AI_BEH_VegRoot_REL_ND_DOM_lin_640.npy"]},
    )

    result = run_private_frozen_reference_verifier(
        app_output_dir=app_dir,
        reference_bundle_dir=bundle_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e-missing-ref-file",
        selected_families=("phase_c_semantic_feature_writers",),
    )

    family = result.families[0]
    assert family.status == "reference_missing"
    assert family.status != "passed"
    assert result.overall_status == "incomplete"


def test_missing_app_output_files_are_app_output_missing_not_passed(
    tmp_path: Path,
) -> None:
    app_dir = tmp_path / "app"
    bundle_dir = tmp_path / "bundle"
    app_dir.mkdir()
    _write_manifest(
        bundle_dir,
        {"phase_c_semantic_feature_writers": ["AI_BEH_VegRoot_REL_ND_DOM_lin_640.npy"]},
    )
    _touch_family_file(
        bundle_dir,
        "phase_c_semantic_feature_writers",
        "AI_BEH_VegRoot_REL_ND_DOM_lin_640.npy",
    )

    result = run_private_frozen_reference_verifier(
        app_output_dir=app_dir,
        reference_bundle_dir=bundle_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e-missing-app-file",
        selected_families=("phase_c_semantic_feature_writers",),
    )

    family = result.families[0]
    assert family.status == "app_output_missing"
    assert family.status != "passed"
    assert result.overall_status == "incomplete"


def test_verifier_not_available_does_not_set_notebook_value_parity_true(
    tmp_path: Path,
) -> None:
    app_dir = tmp_path / "app"
    bundle_dir = tmp_path / "bundle"
    filename = "AI_BEH_VegRoot_REL_ND_DOM_lin_640.npy"
    _write_manifest(bundle_dir, {"phase_c_semantic_feature_writers": [filename]})
    _touch_family_file(bundle_dir, "phase_c_semantic_feature_writers", filename)
    _touch_app_file(app_dir, filename)

    result = run_private_frozen_reference_verifier(
        app_output_dir=app_dir,
        reference_bundle_dir=bundle_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e-verifier-not-available",
        selected_families=("phase_c_semantic_feature_writers",),
    )

    family = result.families[0]
    assert family.status == "verifier_not_available"
    assert family.notebook_value_parity_verified is False
    assert result.notebook_value_parity_verified is False


def test_inventory_only_family_does_not_set_notebook_value_parity_true(
    tmp_path: Path,
) -> None:
    app_dir = tmp_path / "app"
    bundle_dir = tmp_path / "bundle"
    app_dir.mkdir()
    _write_manifest(bundle_dir, {"private_map_artifacts": []})

    result = run_private_frozen_reference_verifier(
        app_output_dir=app_dir,
        reference_bundle_dir=bundle_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e-inventory",
        selected_families=("private_map_artifacts",),
    )

    assert result.families[0].status == "inventory_only"
    assert result.notebook_value_parity_verified is False


def test_comparison_unavailable_is_preserved_from_underlying_harness(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    app_dir = tmp_path / "app"
    bundle_dir = tmp_path / "bundle"
    app_dir.mkdir()
    _write_manifest(bundle_dir, {"report_640": []})
    (bundle_dir / "references" / "report_640").mkdir(parents=True)

    import app.pipeline.parity.end_to_end_harness as harness

    original = harness.FAMILY_REGISTRY["report_640"]
    monkeypatch.setitem(
        harness.FAMILY_REGISTRY,
        "report_640",
        FamilyDefinition(
            family_id="report_640",
            contract_doc=original.contract_doc,
            module_used=original.module_used,
            expected_reference_artifacts=original.expected_reference_artifacts,
            collector=lambda **_: _stub_family("report_640", "comparison_unavailable"),
        ),
    )

    result = run_private_frozen_reference_verifier(
        app_output_dir=app_dir,
        reference_bundle_dir=bundle_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e-comparison-unavailable",
        selected_families=("report_640",),
    )

    assert result.families[0].status == "comparison_unavailable"
    assert result.overall_status == "comparison_unavailable"


def test_overall_status_rules_are_enforced(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    bundle_dir = tmp_path / "bundle"
    app_dir.mkdir()
    _write_manifest(
        bundle_dir,
        {
            "phase_c_semantic_feature_writers": ["missing.npy"],
            "private_map_artifacts": [],
        },
    )

    result = run_private_frozen_reference_verifier(
        app_output_dir=app_dir,
        reference_bundle_dir=bundle_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e-overall",
        selected_families=("phase_c_semantic_feature_writers", "private_map_artifacts"),
    )

    assert result.overall_status == "incomplete"
    assert result.notebook_value_parity_verified is False


def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    bundle_dir = tmp_path / "bundle"
    app_dir.mkdir()
    _write_manifest(bundle_dir, {"private_map_artifacts": []})

    result = run_private_frozen_reference_verifier(
        app_output_dir=app_dir,
        reference_bundle_dir=bundle_dir,
        run_dir=tmp_path / "run",
        run_id="phase-e-report",
        selected_families=("private_map_artifacts",),
    )
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))

    assert result.report_path == tmp_path / "run" / "manifests" / "private_frozen_reference_verifier_report.json"
    assert result.report_path.resolve().relative_to((tmp_path / "run").resolve())
    assert payload["schema_version"] == PHASE_E_FROZEN_REFERENCE_VERIFIER_SCHEMA_VERSION
    assert payload["run_id"] == "phase-e-report"
    assert payload["phase_e_runtime_changes"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["artifact_generation"] is False
    assert payload["earth_engine_calls_added"] is False


def test_no_non_report_artifact_files_are_created_under_run_dir(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    bundle_dir = tmp_path / "bundle"
    app_dir.mkdir()
    _write_manifest(bundle_dir, {"private_map_artifacts": []})
    run_dir = tmp_path / "run"

    run_private_frozen_reference_verifier(
        app_output_dir=app_dir,
        reference_bundle_dir=bundle_dir,
        run_dir=run_dir,
        run_id="phase-e-no-artifacts",
        selected_families=("private_map_artifacts",),
    )

    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created == []


def test_required_phase_e_family_registry_is_present() -> None:
    assert REQUIRED_PHASE_E_FAMILIES == {
        "report_640",
        "secret_layers",
        "dem_curvature",
        "sar_asc_desc",
        "s1_filtered_stack",
        "pan_stack",
        "pan_components",
        "hypercube_res25",
        "semantic_rasters",
        "private_map_artifacts",
        "phase_c_semantic_feature_writers",
        "phase_d_private_geojson_writer",
    }


def test_module_adds_no_earth_engine_pipeline_or_public_serving_calls() -> None:
    import app.pipeline.parity.frozen_reference_verifier as module

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
