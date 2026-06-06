from __future__ import annotations

import inspect
import json
from pathlib import Path


REQUIRED_CATEGORIES = {
    "operator_overlay_ui_modes",
    "authentication_requirement",
    "operator_role_requirement",
    "per_run_authorization_policy",
    "audit_logging_requirement",
    "default_off_configuration",
    "private_overlay_dto_boundary",
    "redacted_denial_response_policy",
    "no_public_download_boundary",
    "future_ui_implementation_slices",
}

REQUIRED_MODES = {
    "disabled_default",
    "operator_only_preview",
    "redacted_denied",
    "future_public_review_required",
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
    from app.pipeline.parity.operator_overlay_ui_policy import (
        get_special_track_g2_operator_overlay_ui_policy,
    )

    items = get_special_track_g2_operator_overlay_ui_policy()

    assert {item.category for item in items} == REQUIRED_CATEGORIES


def test_policy_includes_all_required_modes() -> None:
    from app.pipeline.parity.operator_overlay_ui_policy import (
        get_special_track_g2_operator_overlay_ui_policy,
    )

    items = get_special_track_g2_operator_overlay_ui_policy()

    assert REQUIRED_MODES <= {item.mode for item in items}


def test_disabled_default_has_no_ui_or_public_exposure() -> None:
    from app.pipeline.parity.operator_overlay_ui_policy import (
        get_special_track_g2_operator_overlay_ui_policy,
    )

    disabled_items = [
        item
        for item in get_special_track_g2_operator_overlay_ui_policy()
        if item.mode == "disabled_default"
    ]

    assert disabled_items
    for item in disabled_items:
        assert item.generated_overlay_visible is False
        assert item.exact_coordinates_visible is False
        assert item.raw_geometry_visible is False
        assert item.bounds_visible is False
        assert item.api_change_allowed_now is False
        assert item.frontend_change_allowed_now is False
        assert item.artifact_serving_change_allowed_now is False
        assert item.default_off_required is True


def test_operator_only_preview_requires_all_private_access_gates() -> None:
    from app.pipeline.parity.operator_overlay_ui_policy import (
        get_special_track_g2_operator_overlay_ui_policy,
    )

    operator_items = [
        item
        for item in get_special_track_g2_operator_overlay_ui_policy()
        if item.mode == "operator_only_preview"
    ]

    assert operator_items
    for item in operator_items:
        assert item.authentication_required is True
        assert item.operator_role_required is True
        assert item.per_run_authorization_required is True
        assert item.audit_log_required is True
        assert item.generated_overlay_visible is True
        assert item.public_download_allowed is False
        assert item.implementation_allowed_now is False
        assert item.requires_future_user_approval is True


def test_redacted_denied_policy_leaks_no_sensitive_fields() -> None:
    from app.pipeline.parity.operator_overlay_ui_policy import (
        get_special_track_g2_operator_overlay_ui_policy,
    )

    denial_items = [
        item
        for item in get_special_track_g2_operator_overlay_ui_policy()
        if item.mode == "redacted_denied"
    ]

    assert denial_items
    for item in denial_items:
        assert item.generated_overlay_visible is False
        assert item.exact_coordinates_visible is False
        assert item.raw_geometry_visible is False
        assert item.bounds_visible is False
        assert item.local_paths_visible is False
        assert item.private_hashes_visible is False
        assert item.redacted_denial_required is True


def test_future_public_review_required_is_blocked_by_default() -> None:
    from app.pipeline.parity.operator_overlay_ui_policy import (
        get_special_track_g2_operator_overlay_ui_policy,
    )

    future_items = [
        item
        for item in get_special_track_g2_operator_overlay_ui_policy()
        if item.mode == "future_public_review_required"
    ]

    assert future_items
    for item in future_items:
        assert item.implementation_allowed_now is False
        assert item.requires_future_user_approval is True
        assert item.artifact_serving_change_allowed_now is False
        assert item.frontend_change_allowed_now is False
        assert item.api_change_allowed_now is False
        assert item.implementation_status in {
            "blocked_until_future_approval",
            "requires_artifact_serving_review",
            "requires_frontend_review",
        }


def test_no_item_allows_public_overlay_or_runtime_changes_now() -> None:
    from app.pipeline.parity.operator_overlay_ui_policy import (
        get_special_track_g2_operator_overlay_ui_policy,
    )

    for item in get_special_track_g2_operator_overlay_ui_policy():
        assert item.api_change_allowed_now is False
        assert item.frontend_change_allowed_now is False
        assert item.artifact_serving_change_allowed_now is False
        assert item.implementation_allowed_now is False
        assert item.public_download_allowed is False


def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path: Path) -> None:
    from app.pipeline.parity.operator_overlay_ui_policy import (
        SPECIAL_TRACK_G2_SCHEMA_VERSION,
        write_special_track_g2_operator_overlay_ui_policy_report,
    )

    run_dir = tmp_path / "run"
    report_path = write_special_track_g2_operator_overlay_ui_policy_report(
        run_dir=run_dir,
        run_id="special-track-g2",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path.resolve().is_relative_to(run_dir.resolve())
    assert payload["schema_version"] == SPECIAL_TRACK_G2_SCHEMA_VERSION
    assert payload["run_id"] == "special-track-g2"
    assert payload["operator_overlay_ui_enabled"] is False
    assert payload["runtime_changes"] is False
    assert payload["public_exposure_changes"] is False
    assert payload["artifact_serving_changes"] is False
    assert set(payload["counts_by_category"]) == REQUIRED_CATEGORIES
    assert set(payload["counts_by_mode"]) == REQUIRED_MODES


def test_report_creates_no_map_raster_model_or_artifact_files(tmp_path: Path) -> None:
    from app.pipeline.parity.operator_overlay_ui_policy import (
        write_special_track_g2_operator_overlay_ui_policy_report,
    )

    run_dir = tmp_path / "run"
    write_special_track_g2_operator_overlay_ui_policy_report(
        run_dir=run_dir,
        run_id="special-track-g2-no-artifacts",
    )

    created = [
        path
        for path in run_dir.rglob("*")
        if path.suffix.lower() in FORBIDDEN_ARTIFACT_SUFFIXES
    ]
    assert created == []


def test_module_adds_no_runtime_api_frontend_serving_or_earth_engine_hooks() -> None:
    import app.pipeline.parity.operator_overlay_ui_policy as module

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
        Path("app/pipeline/parity/operator_overlay_ui_policy.py"),
        Path("docs/SPECIAL_TRACK_G2_OPERATOR_ONLY_OVERLAY_UI_DESIGN.md"),
    )

    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in paths
        if path.exists()
    )

    assert all(term not in combined for term in _claim_terms())
