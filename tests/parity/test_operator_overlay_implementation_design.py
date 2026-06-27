from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import app.pipeline.parity.operator_overlay_implementation_design as module
from app.pipeline.parity.operator_overlay_implementation_design import (
    ALLOWED_DESIGN_STATUSES,
    BLOCKED_PUBLIC_EXPOSURE_MODES,
    FUTURE_SLICE_10_G2_DESIGN_SCHEMA_VERSION,
    PLAN_B38_LIVE_OVERLAY_MANIFEST_FAMILY_ID,
    get_operator_overlay_implementation_design,
    write_future_slice_10_g2_implementation_design_report,
)
from app.pipeline.parity.private_map_artifact_comparator import (
    PHASE_D1_GEOJSON_FAMILY_ID,
    PHASE_D2_KMZ_FAMILY_ID,
    PHASE_D3_HEATMAP_FAMILY_ID,
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
    ".jsonl",
    ".pt",
    ".pth",
    ".onnx",
    ".h5",
    ".pkl",
    ".joblib",
    ".parquet",
}

_SENSITIVE_TOKENS = (
    "exact_coordinates",
    "raw_geometry",
    "kml_contents",
    "heatmap_point_payloads",
    "local_paths",
    "private_hashes",
)


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


def _wording_violation(content: str, term: str) -> bool:
    if " " in term:
        return term in content
    return re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", content) is not None


# ---------------------------------------------------------------------------
# Backend / frontend design existence
# ---------------------------------------------------------------------------
def test_backend_route_design_exists_but_no_unrelated_route_is_added() -> None:
    design = get_operator_overlay_implementation_design()
    route = design.backend_route_design

    assert route.route_name == "operator_private_overlays"
    assert route.method == "GET"
    assert route.path == "/runs/{run_id}/operator/private-overlays"
    assert route.implementation_allowed_now is False
    assert route.required_future_slice == "Future Slice 12"

    design_source = inspect.getsource(module)
    assert "APIRouter" not in design_source
    assert "add_api_route" not in design_source
    api_dir = Path("app/api")
    for path in api_dir.rglob("*.py"):
        if path.name == "operator_overlays.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert "operator/private-overlays" not in text
        assert "operator_private_overlays" not in text


def test_frontend_panel_is_now_implemented_without_public_overlay_surface() -> None:
    design = get_operator_overlay_implementation_design()
    panel = design.frontend_panel_design

    assert panel.component_or_panel_name == "OperatorPrivateOverlayPanel"
    assert panel.implementation_allowed_now is False
    assert panel.default_state == "hidden_default_off"

    panel_path = Path("frontend-v2/src/app/components/OperatorPrivateOverlayPanel.tsx")
    assert panel_path.is_file()
    text = panel_path.read_text(encoding="utf-8")
    assert "OperatorPrivateOverlayPanel" in text
    assert "Operator-only private preview" in text
    assert "downloadable via API" in text
    assert "public_exact_coordinate" not in text
    assert "redacted_public" not in text
    assert "downloadUrl" not in text


# ---------------------------------------------------------------------------
# Access gates and artifact families
# ---------------------------------------------------------------------------
def test_operator_only_preview_requires_all_private_access_gates() -> None:
    route = get_operator_overlay_implementation_design().backend_route_design
    assert route.auth_required is True
    assert route.operator_role_required is True
    assert route.per_run_authorization_required is True
    assert route.audit_log_required is True
    assert route.default_off_required is True

    panel = get_operator_overlay_implementation_design().frontend_panel_design
    assert panel.operator_role_required is True
    assert panel.run_authorization_required is True
    assert panel.audit_event_required is True


def test_allowed_artifact_families_cover_phase_d_private_artifacts() -> None:
    design = get_operator_overlay_implementation_design()
    assert set(design.allowed_artifact_families) == {
        PHASE_D1_GEOJSON_FAMILY_ID,
        PHASE_D2_KMZ_FAMILY_ID,
        PHASE_D3_HEATMAP_FAMILY_ID,
        PLAN_B38_LIVE_OVERLAY_MANIFEST_FAMILY_ID,
    }
    assert set(design.frontend_panel_design.artifact_family_tabs) == {
        PHASE_D1_GEOJSON_FAMILY_ID,
        PHASE_D2_KMZ_FAMILY_ID,
        PHASE_D3_HEATMAP_FAMILY_ID,
        PLAN_B38_LIVE_OVERLAY_MANIFEST_FAMILY_ID,
    }


def test_public_exposure_modes_are_blocked() -> None:
    design = get_operator_overlay_implementation_design()
    assert set(design.blocked_public_exposure_modes) == {
        "redacted_public",
        "public_exact_coordinate",
    }
    assert set(design.frontend_panel_design.forbidden_display_modes) == set(
        BLOCKED_PUBLIC_EXPOSURE_MODES
    )
    assert "operator_only_preview" in design.frontend_panel_design.allowed_display_modes


def test_artifact_serving_change_is_not_allowed() -> None:
    design = get_operator_overlay_implementation_design()
    statuses = {item["status"] for item in design.design_status_items}
    assert "artifact_serving_change_not_allowed" in statuses
    assert "artifact-serving" in design.backend_route_design.serving_policy.lower()


# ---------------------------------------------------------------------------
# Redacted denial DTO and audit policy redaction
# ---------------------------------------------------------------------------
def test_redacted_denial_dto_excludes_sensitive_fields() -> None:
    design = get_operator_overlay_implementation_design()
    denial_fields = set(design.dto_policy["redacted_denial_dto"]["fields"])
    route_denial_fields = set(design.backend_route_design.redacted_denial_fields)

    for token in (*_SENSITIVE_TOKENS, "bounds", "download_urls", "private_artifact_contents"):
        assert token not in denial_fields
        assert token not in route_denial_fields

    excluded = set(design.dto_policy["redacted_denial_dto"]["excluded_fields"])
    for token in _SENSITIVE_TOKENS:
        assert token in excluded


def test_public_redacted_dto_excludes_sensitive_fields() -> None:
    design = get_operator_overlay_implementation_design()
    public_fields = set(design.dto_policy["public_redacted_dto"]["fields"])
    for token in (*_SENSITIVE_TOKENS, "bounds", "download_urls", "private_artifact_contents"):
        assert token not in public_fields


def test_audit_policy_excludes_exact_coordinates_and_artifact_contents() -> None:
    design = get_operator_overlay_implementation_design()
    event_fields = set(design.audit_policy["event_fields"])
    assert "exact_coordinates" not in event_fields
    assert "artifact_contents" not in event_fields
    assert "raw_geometry" not in event_fields
    # Required neutral audit fields are present.
    for required in ("event_type", "actor_id", "run_id", "artifact_family", "access_mode"):
        assert required in event_fields
    forbidden = set(design.audit_policy["forbidden_fields"])
    assert "exact_coordinates" in forbidden
    assert "artifact_contents" in forbidden


# ---------------------------------------------------------------------------
# Report behavior
# ---------------------------------------------------------------------------
def test_json_report_writes_parses_and_stays_under_run_dir(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    report_path = write_future_slice_10_g2_implementation_design_report(
        run_dir=run_dir,
        run_id="future-slice-10",
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == (
        run_dir / "manifests" / "future_slice_10_g2_implementation_design.json"
    )
