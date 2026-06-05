import json
import re
from pathlib import Path

import pytest

from app.pipeline.parity.private_map_artifact_inventory import (
    ALLOWED_ARTIFACT_CLASSES,
    ALLOWED_CATEGORIES,
    ALLOWED_IMPLEMENTATION_STATUSES,
    ALLOWED_PARITY_STATUSES,
    ALLOWED_SOURCE_STATUSES,
    PHASE_6_PRIVATE_MAP_ARTIFACT_SCHEMA_VERSION,
    PrivateMapArtifactInventoryItem,
    get_phase_6_private_map_artifact_inventory,
    write_phase_6_private_map_artifact_inventory_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_6_CONTRACT = (
    REPO_ROOT / "docs" / "PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md"
)
FULL_CHECKLIST = REPO_ROOT / "docs" / "NOTEBOOK_PARITY_FULL_CHECKLIST.md"
MODULE_PATH = REPO_ROOT / "app" / "pipeline" / "parity" / "private_map_artifact_inventory.py"

FORBIDDEN_WORDING = {
    "confirmed",
    "proven",
    "dig target",
    "definitely",
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
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_inventory_includes_all_required_categories():
    categories = {item.category for item in get_phase_6_private_map_artifact_inventory()}

    assert categories == {
        "kmz_outputs",
        "geojson_outputs",
        "heatmap_outputs",
        "visual_map_outputs",
        "coordinate_bearing_filesystem_artifacts",
        "redaction_and_serving_policy",
    }


def test_each_item_uses_valid_enums_and_nonblank_actions():
    for item in get_phase_6_private_map_artifact_inventory():
        assert item.category in ALLOWED_CATEGORIES
        assert item.source_status in ALLOWED_SOURCE_STATUSES
        assert item.parity_status in ALLOWED_PARITY_STATUSES
        assert item.implementation_status in ALLOWED_IMPLEMENTATION_STATUSES
        assert item.artifact_class in ALLOWED_ARTIFACT_CLASSES
        assert item.blocker.strip() or item.recommended_next_action.strip()


def test_coordinate_bearing_items_stay_filesystem_only_and_private():
    for item in get_phase_6_private_map_artifact_inventory():
        assert item.target_mode != "public_shared"
        if (
            item.contains_coordinates
            or item.contains_geometry
            or item.contains_bounds
            or item.contains_crs_or_transform
        ):
            assert item.filesystem_only is True
            assert item.http_servable is False
            assert item.frontend_visible is False
            assert item.downloadable_via_api is False


def test_all_items_default_to_private_no_http_no_frontend_no_download():
    for item in get_phase_6_private_map_artifact_inventory():
        assert item.filesystem_only is True
        assert item.http_servable is False
        assert item.frontend_visible is False
        assert item.downloadable_via_api is False


def test_runtime_and_notebook_value_parity_flags_remain_false():
    for item in get_phase_6_private_map_artifact_inventory():
        assert item.runtime_output_verified is False
        assert item.notebook_value_parity_verified is False


def test_allowed_enums_and_safety_boundaries_are_enforced():
    base_kwargs = dict(
        id="bad",
        category="kmz_outputs",
        notebook_artifact_or_pattern="bad",
        current_app_artifact_or_pattern="bad",
        source_status="exact_source_found",
        current_app_status="bad",
        parity_status="inventory_only",
        contains_coordinates=True,
        contains_geometry=True,
        contains_bounds=False,
        contains_crs_or_transform=False,
        expected_inputs=(),
        expected_outputs=(),
        required_reference_artifacts=(),
        required_metadata=(),
        target_mode="notebook_parity",
        classification="bad",
        artifact_class="PRIVATE_COORDINATE_ARTIFACT",
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="implementation_deferred",
        blocker="bad",
        recommended_next_action="bad",
        notes="bad",
    )

    with pytest.raises(ValueError, match="unsupported category"):
        PrivateMapArtifactInventoryItem(**{**base_kwargs, "category": "bad_category"})

    with pytest.raises(ValueError, match="unsupported source_status"):
        PrivateMapArtifactInventoryItem(**{**base_kwargs, "source_status": "bad"})

    with pytest.raises(ValueError, match="unsupported parity_status"):
        PrivateMapArtifactInventoryItem(**{**base_kwargs, "parity_status": "bad"})

    with pytest.raises(ValueError, match="unsupported implementation_status"):
        PrivateMapArtifactInventoryItem(**{**base_kwargs, "implementation_status": "bad"})

    with pytest.raises(ValueError, match="unsupported artifact_class"):
        PrivateMapArtifactInventoryItem(**{**base_kwargs, "artifact_class": "bad"})

    with pytest.raises(ValueError, match="must not target public_shared"):
        PrivateMapArtifactInventoryItem(**{**base_kwargs, "target_mode": "public_shared"})

    with pytest.raises(ValueError, match="must remain filesystem_only"):
        PrivateMapArtifactInventoryItem(**{**base_kwargs, "filesystem_only": False})

    with pytest.raises(ValueError, match="must not be http_servable"):
        PrivateMapArtifactInventoryItem(**{**base_kwargs, "http_servable": True})

    with pytest.raises(ValueError, match="must not be frontend_visible"):
        PrivateMapArtifactInventoryItem(**{**base_kwargs, "frontend_visible": True})

    with pytest.raises(ValueError, match="must not be downloadable_via_api"):
        PrivateMapArtifactInventoryItem(**{**base_kwargs, "downloadable_via_api": True})


def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path):
    run_dir = tmp_path / "run"
    report_path = write_phase_6_private_map_artifact_inventory_report(
        run_dir,
        "phase6-run",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == run_dir / "manifests" / "phase_6_private_map_artifact_inventory.json"
    assert report_path.resolve().relative_to(run_dir.resolve())
    assert payload["schema_version"] == PHASE_6_PRIVATE_MAP_ARTIFACT_SCHEMA_VERSION
    assert payload["run_id"] == "phase6-run"
    assert payload["phase_6_runtime_changes"] is False
    assert payload["public_exposure_changes"] is False
    assert set(payload["counts_by_category"]) == ALLOWED_CATEGORIES
    assert set(payload["counts_by_parity_status"]) == ALLOWED_PARITY_STATUSES
    assert set(payload["counts_by_implementation_status"]) == ALLOWED_IMPLEMENTATION_STATUSES
    assert set(payload["counts_by_artifact_class"]) == ALLOWED_ARTIFACT_CLASSES


def test_report_creates_no_map_coordinate_or_binary_artifacts(tmp_path):
    run_dir = tmp_path / "run"
    write_phase_6_private_map_artifact_inventory_report(run_dir, "phase6-no-artifacts")

    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]

    assert created == []


def test_module_does_not_add_compute_generate_alias_copy_or_map_export_functions():
    import app.pipeline.parity.private_map_artifact_inventory as module

    forbidden_public_functions = [
        name
        for name in dir(module)
        if name.startswith(
            (
                "compute_",
                "generate_",
                "alias_",
                "copy_",
                "raster_",
                "export_",
                "map_export_",
            )
        )
    ]

    assert forbidden_public_functions == []


def test_docs_do_not_claim_public_availability_for_private_coordinate_artifacts():
    contract = _read(PHASE_6_CONTRACT).lower()

    assert "does not expose coordinate/map artifacts through http" in contract
    assert "frontend_visible=false" in contract
    assert "downloadable_via_api=false" in contract
    assert "public availability" not in contract


def test_docs_and_module_avoid_forbidden_certainty_wording():
    merged = "\n".join([_read(PHASE_6_CONTRACT).lower(), _read(MODULE_PATH).lower()])

    for term in FORBIDDEN_WORDING:
        assert re.search(rf"\b{re.escape(term)}\b", merged) is None


def test_phase_6_contract_and_checklist_reference_exist():
    checklist = _read(FULL_CHECKLIST)

    assert PHASE_6_CONTRACT.exists()
    assert "Phase 6 — Coordinate/map/private parity outputs" in checklist
    assert "docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md" in checklist
    assert "Phase 7 — Classifier/model parity" in checklist
