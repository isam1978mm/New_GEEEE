import json
import re
from pathlib import Path

import numpy as np

from app.pipeline.parity.end_to_end_harness import (
    ALLOWED_FAMILY_STATUSES,
    ALLOWED_OVERALL_STATUSES,
    EndToEndFamilyResult,
    FamilyDefinition,
    PHASE_9_END_TO_END_HARNESS_SCHEMA_VERSION,
    run_end_to_end_notebook_parity_harness,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_9_CONTRACT = REPO_ROOT / "docs" / "PHASE_9_END_TO_END_PARITY_HARNESS.md"
MODULE_PATH = REPO_ROOT / "app" / "pipeline" / "parity" / "end_to_end_harness.py"

FORBIDDEN_WORDING = {
    "confirmed",
    "found",
    "proven",
    "dig target",
    "definitely",
    "discovery",
    "burial proven",
    "tomb confirmed",
    "target confirmed",
}

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

REQUIRED_FAMILIES = {
    "phase0_expected_outputs",
    "v6_package",
    "aliases",
    "missing_raster_families",
    "report_640",
    "secret_layers",
    "dem_curvature",
    "sar_asc_desc",
    "s1_filtered_stack",
    "pan_stack",
    "pan_components",
    "hypercube_res25",
    "semantic_rasters",
    "qa_intermediate",
    "private_map_artifacts",
    "classifier_model",
    "probability_only_design",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _make_stub_family(
    family_id: str,
    *,
    status: str,
    comparison_status: str | None = None,
    runtime_output_verified: bool = False,
    notebook_value_parity_verified: bool = False,
) -> EndToEndFamilyResult:
    return EndToEndFamilyResult(
        family_id=family_id,
        contract_doc="docs/stub.md",
        module_used="stub.module",
        expected_reference_artifacts=("stub-reference",),
        app_output_status="present",
        reference_status="present",
        runtime_output_verified=runtime_output_verified,
        notebook_value_parity_verified=notebook_value_parity_verified,
        comparison_status=comparison_status or status,
        status=status,
        blocker="",
        recommended_next_action="stub",
        notes="stub",
    )


def test_harness_report_writes_and_parses(tmp_path):
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    run_dir = tmp_path / "run"
    app_dir.mkdir()
    reference_dir.mkdir()

    result = run_end_to_end_notebook_parity_harness(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase9-report",
        selected_families=("qa_intermediate", "probability_only_design"),
    )
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))

    assert result.report_path == run_dir / "manifests" / "end_to_end_notebook_parity_report.json"
    assert payload["schema_version"] == PHASE_9_END_TO_END_HARNESS_SCHEMA_VERSION
    assert payload["run_id"] == "phase9-report"
    assert payload["selected_families"] == ["qa_intermediate", "probability_only_design"]
    assert payload["overall_status"] == "inventory_only"
    assert payload["phase_9_runtime_changes"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["earth_engine_calls_added"] is False
    assert payload["artifact_generation"] is False


def test_report_path_stays_under_run_dir(tmp_path):
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    run_dir = tmp_path / "run"
    app_dir.mkdir()
    reference_dir.mkdir()

    result = run_end_to_end_notebook_parity_harness(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase9-path",
        selected_families=("probability_only_design",),
    )

    assert result.report_path.resolve().relative_to(run_dir.resolve())


def test_missing_app_output_directory_is_handled_safely(tmp_path):
    reference_dir = tmp_path / "reference"
    run_dir = tmp_path / "run"
    reference_dir.mkdir()

    result = run_end_to_end_notebook_parity_harness(
        app_output_dir=tmp_path / "missing-app",
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase9-missing-app",
        selected_families=("report_640",),
    )

    family = result.families[0]
    assert family.status == "app_output_missing"
    assert result.overall_status == "incomplete"
    assert family.notebook_value_parity_verified is False


def test_missing_reference_bundle_directory_is_handled_safely(tmp_path):
    app_dir = tmp_path / "app"
    run_dir = tmp_path / "run"
    app_dir.mkdir()

    result = run_end_to_end_notebook_parity_harness(
        app_output_dir=app_dir,
        reference_bundle_dir=tmp_path / "missing-reference",
        run_dir=run_dir,
        run_id="phase9-missing-reference",
        selected_families=("report_640",),
    )

    family = result.families[0]
    assert family.status == "reference_missing"
    assert result.overall_status == "incomplete"
    assert family.notebook_value_parity_verified is False


def test_missing_family_references_produce_reference_missing_or_incomplete_not_passed(tmp_path):
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    run_dir = tmp_path / "run"
    app_dir.mkdir()
    reference_dir.mkdir()
    np.save(app_dir / "PAN_LAYERS_STACK_640.npy", np.ones((2, 2), dtype=np.float32))

    result = run_end_to_end_notebook_parity_harness(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase9-ref-missing",
        selected_families=("pan_stack",),
    )

    family = result.families[0]
    assert family.status in {"reference_missing", "incomplete"}
    assert family.status != "passed"
    assert result.overall_status == "incomplete"


def test_inventory_only_families_do_not_mark_notebook_value_parity_true(tmp_path):
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    run_dir = tmp_path / "run"
    app_dir.mkdir()
    reference_dir.mkdir()

    result = run_end_to_end_notebook_parity_harness(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase9-inventory",
        selected_families=("semantic_rasters", "qa_intermediate"),
    )

    assert result.notebook_value_parity_verified is False
    assert all(family.notebook_value_parity_verified is False for family in result.families)


def test_design_only_family_does_not_mark_notebook_value_parity_true(tmp_path):
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    run_dir = tmp_path / "run"
    app_dir.mkdir()
    reference_dir.mkdir()

    result = run_end_to_end_notebook_parity_harness(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase9-design",
        selected_families=("probability_only_design",),
    )

    family = result.families[0]
    assert family.status == "design_only"
    assert family.notebook_value_parity_verified is False
    assert result.notebook_value_parity_verified is False


def test_comparison_unavailable_is_preserved_when_underlying_family_reports_it(
    monkeypatch,
    tmp_path,
):
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    run_dir = tmp_path / "run"
    app_dir.mkdir()
    reference_dir.mkdir()

    import app.pipeline.parity.end_to_end_harness as harness

    original = harness.FAMILY_REGISTRY["report_640"]

    def collector(*, app_output_dir, reference_bundle_dir, run_dir, run_id, tolerances):
        return _make_stub_family("report_640", status="comparison_unavailable")

    monkeypatch.setitem(
        harness.FAMILY_REGISTRY,
        "report_640",
        FamilyDefinition(
            family_id=original.family_id,
            contract_doc=original.contract_doc,
            module_used=original.module_used,
            expected_reference_artifacts=original.expected_reference_artifacts,
            collector=collector,
        ),
    )

    result = harness.run_end_to_end_notebook_parity_harness(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase9-comparison-unavailable",
        selected_families=("report_640",),
    )

    assert result.families[0].status == "comparison_unavailable"
    assert result.overall_status == "comparison_unavailable"


def test_selected_family_filtering_works(tmp_path):
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    run_dir = tmp_path / "run"
    app_dir.mkdir()
    reference_dir.mkdir()

    result = run_end_to_end_notebook_parity_harness(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase9-filter",
        selected_families=("probability_only_design", "classifier_model"),
    )

    assert [family.family_id for family in result.families] == [
        "probability_only_design",
        "classifier_model",
    ]


def test_overall_status_rules_are_enforced(monkeypatch, tmp_path):
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    run_dir = tmp_path / "run"
    app_dir.mkdir()
    reference_dir.mkdir()

    import app.pipeline.parity.end_to_end_harness as harness

    original_report = harness.FAMILY_REGISTRY["report_640"]
    original_secret = harness.FAMILY_REGISTRY["secret_layers"]
    original_design = harness.FAMILY_REGISTRY["probability_only_design"]

    monkeypatch.setitem(
        harness.FAMILY_REGISTRY,
        "report_640",
        FamilyDefinition(
            family_id="report_640",
            contract_doc=original_report.contract_doc,
            module_used=original_report.module_used,
            expected_reference_artifacts=original_report.expected_reference_artifacts,
            collector=lambda **_: _make_stub_family(
                "report_640",
                status="passed",
                runtime_output_verified=True,
                notebook_value_parity_verified=True,
            ),
        ),
    )
    monkeypatch.setitem(
        harness.FAMILY_REGISTRY,
        "secret_layers",
        FamilyDefinition(
            family_id="secret_layers",
            contract_doc=original_secret.contract_doc,
            module_used=original_secret.module_used,
            expected_reference_artifacts=original_secret.expected_reference_artifacts,
            collector=lambda **_: _make_stub_family("secret_layers", status="failed"),
        ),
    )
    monkeypatch.setitem(
        harness.FAMILY_REGISTRY,
        "probability_only_design",
        FamilyDefinition(
            family_id="probability_only_design",
            contract_doc=original_design.contract_doc,
            module_used=original_design.module_used,
            expected_reference_artifacts=original_design.expected_reference_artifacts,
            collector=lambda **_: _make_stub_family("probability_only_design", status="design_only"),
        ),
    )

    result = harness.run_end_to_end_notebook_parity_harness(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase9-overall",
        selected_families=("report_640", "secret_layers", "probability_only_design"),
    )

    assert result.overall_status == "failed"


def test_no_non_json_artifact_files_are_created_under_run_dir(tmp_path):
    app_dir = tmp_path / "app"
    reference_dir = tmp_path / "reference"
    run_dir = tmp_path / "run"
    app_dir.mkdir()
    reference_dir.mkdir()

    run_end_to_end_notebook_parity_harness(
        app_output_dir=app_dir,
        reference_bundle_dir=reference_dir,
        run_dir=run_dir,
        run_id="phase9-no-artifacts",
        selected_families=("qa_intermediate", "probability_only_design"),
    )

    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created == []


def test_module_registry_contains_required_phase_9_families():
    import app.pipeline.parity.end_to_end_harness as harness

    assert set(harness.FAMILY_REGISTRY) == REQUIRED_FAMILIES


def test_family_and_overall_status_enums_are_enforced():
    assert "passed" in ALLOWED_FAMILY_STATUSES
    assert "reference_missing" in ALLOWED_FAMILY_STATUSES
    assert "design_only" in ALLOWED_FAMILY_STATUSES
    assert "inventory_only" in ALLOWED_OVERALL_STATUSES
    assert "comparison_unavailable" in ALLOWED_OVERALL_STATUSES


def test_docs_and_code_do_not_introduce_forbidden_certainty_wording():
    merged = "\n".join([_read(PHASE_9_CONTRACT).lower(), _read(MODULE_PATH).lower()])

    for term in FORBIDDEN_WORDING:
        assert re.search(rf"\b{re.escape(term)}\b", merged) is None
