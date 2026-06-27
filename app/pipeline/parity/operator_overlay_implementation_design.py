from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.private_map_artifact_comparator import (
    PHASE_D1_GEOJSON_FAMILY_ID,
    PHASE_D2_KMZ_FAMILY_ID,
    PHASE_D3_HEATMAP_FAMILY_ID,
    PHASE_D_PRIVATE_MAP_ARTIFACT_FAMILIES,
)


FUTURE_SLICE_10_G2_DESIGN_SCHEMA_VERSION = "future_slice_10_g2_implementation_design_v1"
FUTURE_SLICE_10_G2_DESIGN_REPORT_RELATIVE_PATH = (
    "manifests/future_slice_10_g2_implementation_design.json"
)
FUTURE_SLICE_10_DESIGN_ID = "future_slice_10_g2_implementation_design"

# G2 future implementation shows generated private overlay results after private
# artifacts exist; it is operator-only and never public.
ALLOWED_ACCESS_MODE = "operator_only_preview"
BLOCKED_PUBLIC_EXPOSURE_MODES = ("redacted_public", "public_exact_coordinate")
PLAN_B38_LIVE_OVERLAY_MANIFEST_FAMILY_ID = "plan_b38_live_overlay_manifest"

ALLOWED_ARTIFACT_FAMILIES = (
    *PHASE_D_PRIVATE_MAP_ARTIFACT_FAMILIES,
    PLAN_B38_LIVE_OVERLAY_MANIFEST_FAMILY_ID,
)
FORBIDDEN_ARTIFACT_FAMILIES = (
    "public_overlay_any",
    "redacted_public_overlay",
    "public_exact_coordinate_overlay",
)

# Future Slice 11 implements the auth/role/audit foundation; Future Slice 12
# implements the operator-only private overlay preview only after Slice 11 passes.
REQUIRED_FUTURE_SLICE_AUTH_FOUNDATION = "Future Slice 11"
REQUIRED_FUTURE_SLICE_OPERATOR_PREVIEW = "Future Slice 12"

ALLOWED_DESIGN_STATUSES = {
    "design_only",
    "blocked_until_auth_role_audit",
    "blocked_until_default_off_config",
    "blocked_until_future_implementation",
    "public_exposure_blocked",
    "artifact_serving_change_not_allowed",
}

# Fields that must never appear in any public or redacted response/DTO/audit record.
PUBLIC_FORBIDDEN_FIELDS = (
    "exact_coordinates",
    "raw_geometry",
    "bounds",
    "kml_contents",
    "heatmap_point_payloads",
    "local_paths",
    "private_hashes",
    "download_urls",
    "private_artifact_contents",
)

AUDIT_EVENT_FIELDS = (
    "event_type",
    "actor_id",
    "run_id",
    "artifact_family",
    "access_mode",
    "access_outcome",
    "timestamp",
    "reason_code",
    "request_id",
    "client_context_redacted",
)

AUDIT_FORBIDDEN_FIELDS = (
    "exact_coordinates",
    "raw_geometry",
    "kml_contents",
    "heatmap_point_payloads",
    "local_filesystem_paths",
    "private_hashes",
    "artifact_contents",
)

REDACTED_DENIAL_FIELDS = ("outcome", "reason_code", "request_id")


@dataclass(frozen=True)
class BackendRouteDesign:
    route_name: str
    method: str
    path: str
    auth_required: bool
    operator_role_required: bool
    per_run_authorization_required: bool
    audit_log_required: bool
    default_off_required: bool
    allowed_artifact_families: tuple[str, ...]
    forbidden_artifact_families: tuple[str, ...]
    request_fields: tuple[str, ...]
    response_fields: tuple[str, ...]
    redacted_denial_fields: tuple[str, ...]
    forbidden_response_fields: tuple[str, ...]
    serving_policy: str
    implementation_allowed_now: bool
    required_future_slice: str
    status: str
    blocker: str
    notes: str

    def __post_init__(self) -> None:
        if self.status not in ALLOWED_DESIGN_STATUSES:
            raise ValueError(f"unsupported design status: {self.status}")
        if self.implementation_allowed_now:
            raise ValueError("G2 design is design-only; route implementation is not allowed now")
        if not (
            self.auth_required
            and self.operator_role_required
            and self.per_run_authorization_required
            and self.audit_log_required
            and self.default_off_required
        ):
            raise ValueError("operator_only_preview route requires all private access gates")
        leaked = set(self.redacted_denial_fields) & set(PUBLIC_FORBIDDEN_FIELDS)
        if leaked:
            raise ValueError(f"redacted denial fields must not leak: {sorted(leaked)}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrontendPanelDesign:
    component_or_panel_name: str
    visibility_rule: str
    default_state: str
    operator_role_required: bool
    run_authorization_required: bool
    audit_event_required: bool
    artifact_family_tabs: tuple[str, ...]
    allowed_display_modes: tuple[str, ...]
    forbidden_display_modes: tuple[str, ...]
    redaction_behavior: str
    error_and_denial_behavior: str
    implementation_allowed_now: bool
    required_future_slice: str
    status: str
    notes: str

    def __post_init__(self) -> None:
        if self.status not in ALLOWED_DESIGN_STATUSES:
            raise ValueError(f"unsupported design status: {self.status}")
        if self.implementation_allowed_now:
            raise ValueError("G2 design is design-only; panel implementation is not allowed now")
        if ALLOWED_ACCESS_MODE not in self.allowed_display_modes:
            raise ValueError("frontend panel must allow operator_only_preview")
        if set(self.forbidden_display_modes) != set(BLOCKED_PUBLIC_EXPOSURE_MODES):
            raise ValueError("frontend panel must block the public exposure modes")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OperatorOverlayImplementationDesign:
    backend_route_design: BackendRouteDesign
    frontend_panel_design: FrontendPanelDesign
    dto_policy: dict[str, Any]
    audit_policy: dict[str, Any]
    config_policy: dict[str, Any]
    allowed_artifact_families: tuple[str, ...]
    blocked_public_exposure_modes: tuple[str, ...]
    required_future_slices: dict[str, str]
    design_status_items: tuple[dict[str, str], ...] = field(default_factory=tuple)


def get_operator_overlay_implementation_design() -> OperatorOverlayImplementationDesign:
    backend = BackendRouteDesign(
        route_name="operator_private_overlays",
        method="GET",
        path="/runs/{run_id}/operator/private-overlays",
        auth_required=True,
        operator_role_required=True,
        per_run_authorization_required=True,
        audit_log_required=True,
        default_off_required=True,
        allowed_artifact_families=ALLOWED_ARTIFACT_FAMILIES,
        forbidden_artifact_families=FORBIDDEN_ARTIFACT_FAMILIES,
        request_fields=("run_id", "artifact_family", "access_mode"),
        response_fields=(
            "run_id",
            "artifact_family",
            "access_mode",
            "operator_overlay_payload_ref",
            "audit_event_id",
        ),
        redacted_denial_fields=REDACTED_DENIAL_FIELDS,
        forbidden_response_fields=PUBLIC_FORBIDDEN_FIELDS,
        serving_policy=(
            "operator_only_preview; filesystem-only artifacts; not public HTTP; no public "
            "download; artifact-serving policy unchanged"
        ),
        implementation_allowed_now=False,
        required_future_slice=REQUIRED_FUTURE_SLICE_OPERATOR_PREVIEW,
        status="blocked_until_future_implementation",
        blocker=(
            "No operator-only private overlay route is approved for implementation; auth, "
            "role, per-run authorization, audit, and default-off gates do not exist yet."
        ),
        notes=(
            "Design only. The success response payload reference is permissible only after "
            "the Future Slice 11 auth/role/audit foundation and default-off config exist."
        ),
    )

    frontend = FrontendPanelDesign(
        component_or_panel_name="OperatorPrivateOverlayPanel",
        visibility_rule=(
            "visible only to an authenticated operator with per-run authorization after "
            "private artifacts exist; hidden otherwise"
        ),
        default_state="hidden_default_off",
        operator_role_required=True,
        run_authorization_required=True,
        audit_event_required=True,
        artifact_family_tabs=ALLOWED_ARTIFACT_FAMILIES,
        allowed_display_modes=(ALLOWED_ACCESS_MODE,),
        forbidden_display_modes=BLOCKED_PUBLIC_EXPOSURE_MODES,
        redaction_behavior=(
            "no public DTO; private overlay content is shown only to an authorized operator "
            "after all gates pass; denied users receive a generic redacted response"
        ),
        error_and_denial_behavior=(
            "generic redacted denial; no presence leak; no coordinates, geometry, paths, or "
            "hashes in errors"
        ),
        implementation_allowed_now=False,
        required_future_slice=REQUIRED_FUTURE_SLICE_OPERATOR_PREVIEW,
        status="blocked_until_future_implementation",
        notes=(
            "Design only. This panel differs from the Phase A point/ROI/GRID preview, which "
            "runs before outputs exist; this panel views generated private overlays after "
            "private artifacts exist."
        ),
    )

    dto_policy: dict[str, Any] = {
        "operator_success_dto": {
            "allowed_only_after_gates": True,
            "required_gates": [
                "authentication",
                "operator_role",
                "per_run_authorization",
                "audit_logging",
                "default_off_config",
            ],
            "may_include_private_overlay_payload_after_gates": True,
            "fields": [
                "run_id",
                "artifact_family",
                "access_mode",
                "operator_overlay_payload_ref",
                "audit_event_id",
            ],
            "required_future_slice": REQUIRED_FUTURE_SLICE_OPERATOR_PREVIEW,
        },
        "redacted_denial_dto": {
            "fields": list(REDACTED_DENIAL_FIELDS),
            "excluded_fields": list(PUBLIC_FORBIDDEN_FIELDS),
            "must_not_reveal_overlay_presence": True,
        },
        "public_redacted_dto": {
            "fields": ["outcome", "reason_code", "request_id"],
            "forbidden_fields": list(PUBLIC_FORBIDDEN_FIELDS),
        },
        "status": "public_exposure_blocked",
    }

    audit_policy: dict[str, Any] = {
        "event_fields": list(AUDIT_EVENT_FIELDS),
        "forbidden_fields": list(AUDIT_FORBIDDEN_FIELDS),
        "allow_and_deny_events_required": True,
        "status": "blocked_until_auth_role_audit",
    }

    config_policy: dict[str, Any] = {
        "default_off_required": True,
        "proposed_config_key_name": "operator_private_overlay_preview_enabled",
        "proposed_default_value": False,
        "config_added_now": False,
        "implementation_allowed_now": False,
        "status": "blocked_until_default_off_config",
    }

    required_future_slices = {
        REQUIRED_FUTURE_SLICE_AUTH_FOUNDATION: (
            "Implement the auth, operator role, per-run authorization, audit logging, and "
            "default-off configuration foundation. No overlay payload is exposed in this slice."
        ),
        REQUIRED_FUTURE_SLICE_OPERATOR_PREVIEW: (
            "Implement the operator-only private overlay preview route and panel only after "
            "Future Slice 11 passes, keeping default-off, redacted denials, and no public exposure."
        ),
    }

    design_status_items = (
        {"component": "backend_route_design", "status": "blocked_until_future_implementation"},
        {"component": "frontend_panel_design", "status": "blocked_until_future_implementation"},
        {"component": "auth_role_audit_gate", "status": "blocked_until_auth_role_audit"},
        {"component": "default_off_config", "status": "blocked_until_default_off_config"},
        {"component": "public_exposure", "status": "public_exposure_blocked"},
        {"component": "artifact_serving", "status": "artifact_serving_change_not_allowed"},
        {"component": "overall_design", "status": "design_only"},
    )

    return OperatorOverlayImplementationDesign(
        backend_route_design=backend,
        frontend_panel_design=frontend,
        dto_policy=dto_policy,
        audit_policy=audit_policy,
        config_policy=config_policy,
        allowed_artifact_families=ALLOWED_ARTIFACT_FAMILIES,
        blocked_public_exposure_modes=BLOCKED_PUBLIC_EXPOSURE_MODES,
        required_future_slices=required_future_slices,
        design_status_items=design_status_items,
    )


def write_future_slice_10_g2_implementation_design_report(
    *,
    run_dir: str | Path,
    run_id: str,
    design: OperatorOverlayImplementationDesign | None = None,
    report_relative_path: str | Path = FUTURE_SLICE_10_G2_DESIGN_REPORT_RELATIVE_PATH,
) -> Path:
    """Write the private Future Slice 10 G2 implementation design report.

    This is design/details only. It does not implement an API route or frontend UI,
    expose private overlays or exact coordinates, change artifact serving, call Earth
    Engine, or generate map artifacts.
    """

    selected = design or get_operator_overlay_implementation_design()
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": FUTURE_SLICE_10_G2_DESIGN_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "design_id": FUTURE_SLICE_10_DESIGN_ID,
        "backend_route_design": selected.backend_route_design.to_dict(),
        "frontend_panel_design": selected.frontend_panel_design.to_dict(),
        "dto_policy": selected.dto_policy,
        "audit_policy": selected.audit_policy,
        "config_policy": selected.config_policy,
        "allowed_artifact_families": list(selected.allowed_artifact_families),
        "blocked_public_exposure_modes": list(selected.blocked_public_exposure_modes),
        "required_future_slices": selected.required_future_slices,
        "counts_by_status": _counts_by_status(selected.design_status_items),
        "g2_implementation_design_only": True,
        "api_route_added": False,
        "frontend_ui_added": False,
        "artifact_serving_changes": False,
        "public_exposure_changes": False,
        "runtime_added": False,
        "earth_engine_calls_added": False,
        "artifact_generation": False,
        "notes": (
            "Future Slice 10 specifies the detailed operator-only private overlay UI "
            "implementation contract. It adds no API route, no frontend UI, no artifact "
            "serving change, and no public exposure. The operator-only overlay UI remains "
            "blocked until Future Slice 11 (auth/role/audit foundation) and Future Slice 12 "
            "(operator-only private overlay preview)."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by_status(design_status_items: tuple[dict[str, str], ...]) -> dict[str, int]:
    counts = {status: 0 for status in sorted(ALLOWED_DESIGN_STATUSES)}
    for item in design_status_items:
        counts[item["status"]] += 1
    return counts
