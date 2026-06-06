from __future__ import annotations

import inspect
import json
from pathlib import Path


REQUIRED_CATEGORIES = {
    "overlay_data_classes",
    "access_modes",
    "role_and_permission_policy",
    "redaction_policy",
    "public_dto_boundary",
    "artifact_serving_boundary",
    "audit_logging_policy",
    "operator_only_preview_policy",
    "public_overlay_approval_gate",
    "future_implementation_slices",
}

REQUIRED_ACCESS_MODES = {
    "private_filesystem_only",
    "operator_only_authenticated",
    "redacted_public",
    "public_exact_coordinate",
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


def _claim_terms() -> tuple[str, ...]:
    return (
        "con" + "firmed",
        "fou" + "nd",
        "pro" + "ven",
        "dig" + " target",
        "def" + "initely",
        "disc" + "overy",
        "burial " + "pro" + "ven",
        "tomb " + "con" + "firmed",
        "target " + "con" + "firmed",
    )


def test_policy_includes_all_required_design_categories() -> None:
    from app.pipeline.parity.exact_coordinate_overlay_policy import (
        get_special_track_g_exact_coordinate_overlay_policy,
    )

    items = get_special_track_g_exact_coordinate_overlay_policy()

    assert {item.category for item in items} == REQUIRED_CATEGORIES


def test_policy_includes_all_required_access_modes() -> None:
    from app.pipeline.parity.exact_coordinate_overlay_policy import (
        get_special_track_g_exact_coordinate_overlay_policy,
    )

    items = get_special_track_g_exact_coordinate_overlay_policy()

    assert REQUIRED_ACCESS_MODES <= {item.access_mode for item in items}


def test_private_filesystem_only_allows_exact_coordinates_only_privately() -> None:
    from app.pipeline.parity.exact_coordinate_overlay_policy import (
        get_special_track_g_exact_coordinate_overlay_policy,
    )

    private_items = [
        item
        for item in get_special_track_g_exact_coordinate_overlay_policy()
        if item.access_mode == "private_filesystem_only"
    ]

    assert private_items
    for item in private_items:
        assert item.exact_coordinates_allowed is True
        assert item.raw_geometry_allowed is True
        assert item.local_paths_allowed is True
        assert item.public_summary_allowed is False
        assert item.http_servable is False
        assert item.frontend_visible is False
        assert item.downloadable_via_api is False
        assert item.implementation_status == "allowed_private_current_boundary"


def test_operator_only_mode_requires_role_audit_and_future_approval() -> None:
    from app.pipeline.parity.exact_coordinate_overlay_policy import (
        get_special_track_g_exact_coordinate_overlay_policy,
    )

    operator_items = [
        item
        for item in get_special_track_g_exact_coordinate_overlay_policy()
        if item.access_mode == "operator_only_authenticated"
    ]

    assert operator_items
    for item in operator_items:
        assert item.operator_role_required is True
        assert item.audit_log_required is True
        assert item.requires_future_user_approval is True
        assert item.implementation_allowed_now is False


def test_redacted_public_mode_blocks_sensitive_coordinate_fields() -> None:
    from app.pipeline.parity.exact_coordinate_overlay_policy import (
        get_special_track_g_exact_coordinate_overlay_policy,
    )

    public_items = [
        item
        for item in get_special_track_g_exact_coordinate_overlay_policy()
        if item.access_mode == "redacted_public"
    ]

    assert public_items
    for item in public_items:
        assert item.exact_coordinates_allowed is False
        assert item.raw_geometry_allowed is False
        assert item.local_paths_allowed is False
        assert item.private_hashes_allowed is False
        assert item.public_summary_allowed is True
        assert item.redaction_required is True


def test_public_exact_coordinate_mode_is_blocked_by_default() -> None:
    from app.pipeline.parity.exact_coordinate_overlay_policy import (
        get_special_track_g_exact_coordinate_overlay_policy,
    )

    exact_items = [
        item
        for item in get_special_track_g_exact_coordinate_overlay_policy()
        if item.access_mode == "public_exact_coordinate"
    ]

    assert exact_items
    for item in exact_items:
        assert item.implementation_allowed_now is False
        assert item.requires_future_user_approval is True
        assert item.audit_log_required is True
        assert item.artifact_serving_change_required is True
        assert item.implementation_status in {
            "blocked_until_future_approval",
            "requires_access_control_implementation",
            "requires_artifact_serving_review",
            "requires_frontend_review",
            "requires_audit_logging",
        }


def test_no_public_dto_policy_allows_sensitive_fields_by_default() -> None:
    from app.pipeline.parity.exact_coordinate_overlay_policy import (
        get_special_track_g_exact_coordinate_overlay_policy,
    )

    dto_items = [
        item
        for item in get_special_track_g_exact_coordinate_overlay_policy()
        if item.category == "public_dto_boundary"
    ]

    assert dto_items
    for item in dto_items:
        assert item.exact_coordinates_allowed is False
        assert item.raw_geometry_allowed is False
        assert item.local_paths_allowed is False
        assert item.private_hashes_allowed is False


def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path: Path) -> None:
    from app.pipeline.parity.exact_coordinate_overlay_policy import (
        SPECIAL_TRACK_G_SCHEMA_VERSION,
        write_special_track_g_exact_coordinate_overlay_policy_report,
    )

    run_dir = tmp_path / "run"
    report_path = write_special_track_g_exact_coordinate_overlay_policy_report(
        run_dir=run_dir,
        run_id="special-track-g1",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path.resolve().is_relative_to(run_dir.resolve())
    assert payload["schema_version"] == SPECIAL_TRACK_G_SCHEMA_VERSION
    assert payload["run_id"] == "special-track-g1"
    assert payload["public_exact_coordinate_enabled"] is False
    assert payload["runtime_changes"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["artifact_serving_changes"] is False
    assert set(payload["counts_by_category"]) == REQUIRED_CATEGORIES
    assert set(payload["counts_by_access_mode"]) == REQUIRED_ACCESS_MODES


def test_report_creates_no_map_raster_model_or_artifact_files(tmp_path: Path) -> None:
    from app.pipeline.parity.exact_coordinate_overlay_policy import (
        write_special_track_g_exact_coordinate_overlay_policy_report,
    )

    run_dir = tmp_path / "run"
    write_special_track_g_exact_coordinate_overlay_policy_report(
        run_dir=run_dir,
        run_id="special-track-g1-no-artifacts",
    )

    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created == []


def test_module_adds_no_runtime_public_overlay_or_earth_engine_hooks() -> None:
    import app.pipeline.parity.exact_coordinate_overlay_policy as module

    source = inspect.getsource(module)

    assert "serve_artifact_response" not in source
    assert "can_serve_artifact" not in source
    assert "FileResponse" not in source
    assert "StreamingResponse" not in source
    assert "APIRouter" not in source
    assert "BackgroundTasks" not in source
    assert "enqueue_core_pipeline_run" not in source
    assert "run_core_pipeline" not in source
    assert "ee.Authenticate" not in source
    assert "import ee" not in source
    assert "earthengine" not in source.lower()
    assert "google.colab" not in source
    assert "drive.mount" not in source
    assert "/content/drive" not in source


def test_new_policy_docs_and_code_avoid_claim_wording() -> None:
    paths = (
        Path("app/pipeline/parity/exact_coordinate_overlay_policy.py"),
        Path("docs/SPECIAL_TRACK_G_EXACT_COORDINATE_OVERLAY_ACCESS_CONTROL.md"),
    )

    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in paths
        if path.exists()
    )

    assert all(term not in combined for term in _claim_terms())
