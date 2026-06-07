from __future__ import annotations

import inspect
import json
from pathlib import Path
import re

from app.services.redaction import verify_redacted


EXPECTED_FAMILIES = (
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
    "phase_d2_private_kmz_writer",
    "phase_d3_private_heatmap_json_writer",
)

REQUIRED_MANIFEST_FIELDS = (
    "bundle_id",
    "schema_version",
    "created_at",
    "created_by",
    "source_notebook_name",
    "source_notebook_version",
    "source_notebook_commit_or_hash",
    "source_run_id",
    "source_grid_id",
    "source_roi_id_redacted",
    "collection_method",
    "collection_environment",
    "artifact_class",
    "filesystem_only",
    "http_servable",
    "frontend_visible",
    "downloadable_via_api",
    "redaction_policy",
    "families",
    "family_inventory",
    "expected_artifact_counts",
    "hashes_available",
    "tolerance_policy_ref",
    "notes",
)


def _valid_manifest() -> dict[str, object]:
    return {
        "bundle_id": "bundle_001",
        "schema_version": "frozen_notebook_reference_bundle_v1",
        "created_at": "2026-06-07T00:00:00Z",
        "created_by": "operator",
        "source_notebook_name": "new.ipynb",
        "source_notebook_version": "frozen_operator_capture",
        "source_notebook_commit_or_hash": "redacted_or_private",
        "source_run_id": "redacted_source_run",
        "source_grid_id": "redacted_grid",
        "source_roi_id_redacted": "redacted_roi",
        "collection_method": "operator_private_copy",
        "collection_environment": "private_filesystem",
        "artifact_class": "FILESYSTEM_ONLY",
        "filesystem_only": True,
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
        "redaction_policy": "no_public_coordinates_paths_hashes_or_contents",
        "families": list(EXPECTED_FAMILIES),
        "family_inventory": {family: [] for family in EXPECTED_FAMILIES},
        "expected_artifact_counts": {family: 0 for family in EXPECTED_FAMILIES},
        "hashes_available": False,
        "tolerance_policy_ref": "docs/IMPLEMENTATION_PHASE_E_PRIVATE_PARITY_VERIFIER.md",
        "notes": "Template manifest only; no real references are included.",
    }


def test_scaffold_defines_expected_bundle_layout() -> None:
    from app.pipeline.parity.frozen_reference_bundle_scaffold import (
        get_frozen_reference_bundle_scaffold,
    )

    scaffold = get_frozen_reference_bundle_scaffold()

    assert scaffold["bundle_root_template"] == "data/notebook_references/<bundle_id>"
    assert scaffold["manifest_name"] == "manifest.json"
    assert scaffold["references_dir_name"] == "references"
    assert scaffold["expected_family_ids"] == list(EXPECTED_FAMILIES)
    for family in EXPECTED_FAMILIES:
        assert f"references/{family}/" in scaffold["expected_bundle_layout"]


def test_scaffold_includes_required_manifest_fields_and_storage_policy() -> None:
    from app.pipeline.parity.frozen_reference_bundle_scaffold import (
        get_frozen_reference_bundle_scaffold,
    )

    scaffold = get_frozen_reference_bundle_scaffold()
    storage = scaffold["storage_policy"]

    assert scaffold["required_manifest_fields"] == list(REQUIRED_MANIFEST_FIELDS)
    assert storage["allowed_artifact_classes"] == ["LOCAL_SENSITIVE", "FILESYSTEM_ONLY"]
    assert storage["filesystem_only_required"] is True
    assert storage["http_servable_required"] is False
    assert storage["frontend_visible_required"] is False
    assert storage["downloadable_via_api_required"] is False
    assert storage["bundle_root_must_be_outside_git"] is True


def test_validate_manifest_accepts_valid_tmp_bundle(tmp_path: Path) -> None:
    from app.pipeline.parity.frozen_reference_bundle_scaffold import (
        validate_frozen_reference_bundle_manifest,
    )

    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    (bundle_root / "manifest.json").write_text(
        json.dumps(_valid_manifest()),
        encoding="utf-8",
    )

    result = validate_frozen_reference_bundle_manifest(bundle_root)

    assert result["status"] == "ready_for_later_verifier_run"
    assert result["notebook_value_parity_verified"] is False
    assert result["real_references_collected"] is False


def test_bundle_root_inside_repo_is_rejected() -> None:
    from app.pipeline.parity.frozen_reference_bundle_scaffold import (
        validate_frozen_reference_bundle_manifest,
    )

    result = validate_frozen_reference_bundle_manifest(
        Path("data/notebook_references/test_bundle")
    )

    assert result["status"] == "invalid_storage_policy"
    assert result["notebook_value_parity_verified"] is False


def test_missing_manifest_returns_not_collected(tmp_path: Path) -> None:
    from app.pipeline.parity.frozen_reference_bundle_scaffold import (
        validate_frozen_reference_bundle_manifest,
    )

    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()

    result = validate_frozen_reference_bundle_manifest(bundle_root)

    assert result["status"] == "not_collected"
    assert result["notebook_value_parity_verified"] is False
    assert result["runtime_output_verified"] is False


def test_empty_bundle_does_not_pass_parity(tmp_path: Path) -> None:
    from app.pipeline.parity.frozen_reference_bundle_scaffold import (
        validate_frozen_reference_bundle_manifest,
    )

    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    manifest = _valid_manifest()
    manifest["family_inventory"] = {family: [] for family in EXPECTED_FAMILIES}
    manifest["expected_artifact_counts"] = {family: 1 for family in EXPECTED_FAMILIES}
    (bundle_root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_frozen_reference_bundle_manifest(bundle_root)

    assert result["status"] == "not_collected"
    assert result["notebook_value_parity_verified"] is False
    assert "missing_references" in result["blockers"]


def test_invalid_storage_policy_is_rejected(tmp_path: Path) -> None:
    from app.pipeline.parity.frozen_reference_bundle_scaffold import (
        validate_frozen_reference_bundle_manifest,
    )

    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    manifest = _valid_manifest()
    manifest["artifact_class"] = "REDACTED_PUBLIC"
    manifest["filesystem_only"] = False
    manifest["http_servable"] = True
    (bundle_root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_frozen_reference_bundle_manifest(bundle_root)

    assert result["status"] == "invalid_storage_policy"
    assert result["notebook_value_parity_verified"] is False


def test_report_writes_parses_and_stays_under_run_dir(tmp_path: Path) -> None:
    from app.pipeline.parity.frozen_reference_bundle_scaffold import (
        write_frozen_reference_bundle_scaffold_report,
    )

    run_dir = tmp_path / "run"
    report_path = write_frozen_reference_bundle_scaffold_report(
        run_dir=run_dir,
        run_id="run-d1",
    )

    assert report_path.resolve().is_relative_to(run_dir.resolve())
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "d1_frozen_reference_bundle_scaffold_v1"
    assert payload["run_id"] == "run-d1"
    assert payload["bundle_status"] == "ready_for_operator_collection"
    assert payload["notebook_value_parity_verified"] is False
    assert payload["runtime_output_verified"] is False
    assert payload["collection_plan_only"] is True
    assert payload["real_references_collected"] is False
    assert payload["artifact_generation"] is False
    assert payload["earth_engine_calls_added"] is False
    assert payload["public_exposure_changes"] is False


def test_report_is_redacted(tmp_path: Path) -> None:
    from app.pipeline.parity.frozen_reference_bundle_scaffold import (
        write_frozen_reference_bundle_scaffold_report,
    )

    report_path = write_frozen_reference_bundle_scaffold_report(
        run_dir=tmp_path / "run",
        run_id="run-d1",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    verify_redacted(payload)
    serialized = json.dumps(payload, sort_keys=True).lower()

    forbidden_fragments = (
        "latitude",
        "longitude",
        "raw geometry",
        "geometry",
        "local path",
        "local_path",
        "private hash",
        "private_hash",
        "artifact contents",
        "artifact_content",
        str(tmp_path).lower(),
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized


def test_report_creates_no_reference_artifact_files(tmp_path: Path) -> None:
    from app.pipeline.parity.frozen_reference_bundle_scaffold import (
        write_frozen_reference_bundle_scaffold_report,
    )

    run_dir = tmp_path / "run"
    write_frozen_reference_bundle_scaffold_report(run_dir=run_dir, run_id="run-d1")

    created_files = [path for path in run_dir.rglob("*") if path.is_file()]
    assert [path.name for path in created_files] == [
        "d1_frozen_reference_bundle_scaffold.json"
    ]
    blocked_suffixes = (
        ".tif",
        ".tiff",
        ".npy",
        ".geojson",
        ".kmz",
        ".kml",
        ".html",
        ".csv",
        ".png",
        ".jpg",
        ".jpeg",
    )
    for path in created_files:
        assert not path.name.lower().endswith(blocked_suffixes)


def test_no_runtime_web_earth_engine_ml_or_api_logic_exists() -> None:
    import app.pipeline.parity.frozen_reference_bundle_scaffold as module

    source = inspect.getsource(module).lower()
    blocked_terms = [
        "req" + "uests",
        "url" + "lib",
        "htt" + "px",
        "beautiful" + "soup",
        "scr" + "ape",
        "def down" + "load",
        "down" + "load_file",
        "down" + "load_dataset",
        "ee.authenticate",
        "import " + "ee",
        "earth" + "engine",
        "co" + "lab",
        "drive" + ".mount",
        "google " + "drive",
        "tor" + "ch",
        "tensor" + "flow",
        "cu" + "da",
        "sk" + "learn",
        "fast" + "api",
        "api" + "router",
        "serve_" + "artifact_response",
        "orc" + "hes" + "trator",
        "background" + "tasks",
        "train_" + "model",
        "run_" + "inference",
    ]
    for term in blocked_terms:
        assert term not in source


def test_no_forbidden_certainty_wording_is_present() -> None:
    import app.pipeline.parity.frozen_reference_bundle_scaffold as module

    sources = [
        inspect.getsource(module).lower(),
        Path("docs/FUTURE_SLICE_D1_FROZEN_REFERENCE_BUNDLE_COLLECTION_PLAN.md")
        .read_text(encoding="utf-8")
        .lower()
        if Path("docs/FUTURE_SLICE_D1_FROZEN_REFERENCE_BUNDLE_COLLECTION_PLAN.md").exists()
        else "",
    ]
    forbidden_patterns = [
        "con" + "firmed",
        "fo" + "und",
        r"\b" + "pro" + "ven" + r"\b",
        "dig " + "target",
        "def" + "initely",
        "dis" + "covery",
        "burial " + "pro" + "ven",
        "tomb " + "con" + "firmed",
        "target " + "con" + "firmed",
    ]
    for source in sources:
        for pattern in forbidden_patterns:
            assert re.search(pattern, source) is None
