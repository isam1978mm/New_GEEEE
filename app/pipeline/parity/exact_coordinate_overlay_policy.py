from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


SPECIAL_TRACK_G_SCHEMA_VERSION = "special_track_g_exact_coordinate_overlay_policy_v1"
SPECIAL_TRACK_G_REPORT_RELATIVE_PATH = (
    "manifests/special_track_g_exact_coordinate_overlay_policy.json"
)

ALLOWED_CATEGORIES = {
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

ALLOWED_ACCESS_MODES = {
    "private_filesystem_only",
    "operator_only_authenticated",
    "redacted_public",
    "public_exact_coordinate",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "design_only",
    "blocked_until_future_approval",
    "allowed_private_current_boundary",
    "requires_access_control_implementation",
    "requires_artifact_serving_review",
    "requires_frontend_review",
    "requires_audit_logging",
}

_BASE_TESTS = (
    "public DTO redaction check",
    "artifact serving policy check",
    "operator role check",
    "audit log check",
    "no default public overlay check",
)


@dataclass(frozen=True)
class ExactCoordinateOverlayPolicyItem:
    id: str
    category: str
    access_mode: str
    description: str
    exact_coordinates_allowed: bool
    raw_geometry_allowed: bool
    bounds_allowed: bool
    local_paths_allowed: bool
    private_hashes_allowed: bool
    public_summary_allowed: bool
    operator_role_required: bool
    audit_log_required: bool
    redaction_required: bool
    http_servable: bool
    frontend_visible: bool
    downloadable_via_api: bool
    artifact_serving_change_required: bool
    implementation_allowed_now: bool
    requires_future_user_approval: bool
    implementation_status: str
    required_tests_before_implementation: tuple[str, ...]
    blocker: str
    recommended_next_action: str
    notes: str

    def __post_init__(self) -> None:
        if self.category not in ALLOWED_CATEGORIES:
            raise ValueError(f"unsupported category: {self.category}")
        if self.access_mode not in ALLOWED_ACCESS_MODES:
            raise ValueError(f"unsupported access_mode: {self.access_mode}")
        if self.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"unsupported implementation_status: {self.implementation_status}"
            )
        if self.access_mode == "private_filesystem_only":
            if self.http_servable or self.frontend_visible or self.downloadable_via_api:
                raise ValueError("private filesystem policy must not enable public surfaces")
        if self.access_mode == "operator_only_authenticated":
            if not self.operator_role_required or not self.audit_log_required:
                raise ValueError("operator-only policy requires role and audit gates")
            if self.implementation_allowed_now:
                raise ValueError("operator-only overlay requires future approval")
        if self.access_mode == "redacted_public":
            if (
                self.exact_coordinates_allowed
                or self.raw_geometry_allowed
                or self.local_paths_allowed
                or self.private_hashes_allowed
            ):
                raise ValueError("redacted public policy must block sensitive fields")
        if self.access_mode == "public_exact_coordinate":
            if self.implementation_allowed_now:
                raise ValueError("public exact-coordinate overlay is blocked by default")
            if not self.requires_future_user_approval:
                raise ValueError("public exact-coordinate overlay requires future approval")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_POLICY_ITEMS: tuple[ExactCoordinateOverlayPolicyItem, ...] = (
    ExactCoordinateOverlayPolicyItem(
        id="special_g_overlay_data_classes",
        category="overlay_data_classes",
        access_mode="private_filesystem_only",
        description=(
            "Exact-coordinate overlay data includes private point, line, polygon, "
            "bounds, and GRID-derived geometry stored only inside run-local files."
        ),
        exact_coordinates_allowed=True,
        raw_geometry_allowed=True,
        bounds_allowed=True,
        local_paths_allowed=True,
        private_hashes_allowed=False,
        public_summary_allowed=False,
        operator_role_required=False,
        audit_log_required=False,
        redaction_required=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        artifact_serving_change_required=False,
        implementation_allowed_now=True,
        requires_future_user_approval=False,
        implementation_status="allowed_private_current_boundary",
        required_tests_before_implementation=(
            "run-dir containment check",
            "private artifact class check",
            "redacted summary field check",
        ),
        blocker="No blocker for existing private filesystem-only storage boundary.",
        recommended_next_action=(
            "Keep exact-coordinate data in private run-local files unless a later "
            "approved slice narrows exposure."
        ),
        notes="This item reflects the current private map artifact writer boundary.",
    ),
    ExactCoordinateOverlayPolicyItem(
        id="special_g_access_modes",
        category="access_modes",
        access_mode="redacted_public",
        description=(
            "Access modes are private filesystem-only, operator-only authenticated, "
            "redacted public summary, and blocked public exact-coordinate exposure."
        ),
        exact_coordinates_allowed=False,
        raw_geometry_allowed=False,
        bounds_allowed=False,
        local_paths_allowed=False,
        private_hashes_allowed=False,
        public_summary_allowed=True,
        operator_role_required=False,
        audit_log_required=False,
        redaction_required=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        artifact_serving_change_required=True,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="design_only",
        required_tests_before_implementation=_BASE_TESTS,
        blocker="Public-facing overlay behavior has no approved implementation slice.",
        recommended_next_action="Use the access-mode matrix before any later overlay implementation work.",
        notes="Redacted public mode may include summary metadata only.",
    ),
    ExactCoordinateOverlayPolicyItem(
        id="special_g_role_and_permission_policy",
        category="role_and_permission_policy",
        access_mode="operator_only_authenticated",
        description=(
            "Operator-only mode requires authentication, an explicit operator role, "
            "per-run authorization, and default-off behavior."
        ),
        exact_coordinates_allowed=True,
        raw_geometry_allowed=True,
        bounds_allowed=True,
        local_paths_allowed=False,
        private_hashes_allowed=False,
        public_summary_allowed=False,
        operator_role_required=True,
        audit_log_required=True,
        redaction_required=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        artifact_serving_change_required=True,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="requires_access_control_implementation",
        required_tests_before_implementation=(
            "operator role denial check",
            "operator role allow check",
            "per-run authorization check",
            "default-off check",
            "audit event check",
        ),
        blocker="The app currently has no multi-user authorization model for overlays.",
        recommended_next_action=(
            "Design an operator role and per-run authorization layer before overlay preview work."
        ),
        notes="Loopback-only app behavior is not enough for public overlay exposure.",
    ),
    ExactCoordinateOverlayPolicyItem(
        id="special_g_redaction_policy",
        category="redaction_policy",
        access_mode="redacted_public",
        description=(
            "Public summaries must omit exact coordinate values, raw geometry, bounds, "
            "local paths, and private hashes."
        ),
        exact_coordinates_allowed=False,
        raw_geometry_allowed=False,
        bounds_allowed=False,
        local_paths_allowed=False,
        private_hashes_allowed=False,
        public_summary_allowed=True,
        operator_role_required=False,
        audit_log_required=False,
        redaction_required=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        artifact_serving_change_required=False,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="design_only",
        required_tests_before_implementation=(
            "public response redaction check",
            "validation error redaction check",
            "log redaction check",
        ),
        blocker="A redacted overlay DTO schema is not yet approved.",
        recommended_next_action="Define a public-safe summary schema before any public overlay endpoint exists.",
        notes="Redaction applies to DTOs, logs, validation errors, and summaries.",
    ),
    ExactCoordinateOverlayPolicyItem(
        id="special_g_public_dto_boundary",
        category="public_dto_boundary",
        access_mode="redacted_public",
        description=(
            "Public DTOs may describe artifact type, feature count, and redaction status "
            "only; exact coordinate content remains absent."
        ),
        exact_coordinates_allowed=False,
        raw_geometry_allowed=False,
        bounds_allowed=False,
        local_paths_allowed=False,
        private_hashes_allowed=False,
        public_summary_allowed=True,
        operator_role_required=False,
        audit_log_required=False,
        redaction_required=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        artifact_serving_change_required=False,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="design_only",
        required_tests_before_implementation=(
            "DTO schema deny-list check",
            "middleware redaction check",
            "response snapshot check",
        ),
        blocker="No public overlay DTO is approved in this phase.",
        recommended_next_action="Keep DTOs redacted and add a later schema review before implementation.",
        notes="Public DTO policy remains stricter than private filesystem policy.",
    ),
    ExactCoordinateOverlayPolicyItem(
        id="special_g_artifact_serving_boundary",
        category="artifact_serving_boundary",
        access_mode="public_exact_coordinate",
        description=(
            "Serving exact-coordinate overlay artifacts would require a separate "
            "serving-policy review and a new approved guard path."
        ),
        exact_coordinates_allowed=False,
        raw_geometry_allowed=False,
        bounds_allowed=False,
        local_paths_allowed=False,
        private_hashes_allowed=False,
        public_summary_allowed=False,
        operator_role_required=True,
        audit_log_required=True,
        redaction_required=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        artifact_serving_change_required=True,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="requires_artifact_serving_review",
        required_tests_before_implementation=(
            "artifact class migration check",
            "serving guard denial check",
            "network bind denial check",
            "audit event check",
        ),
        blocker="Current artifact-serving policy blocks coordinate-bearing public artifacts.",
        recommended_next_action=(
            "Keep artifact serving unchanged until a later user-approved serving review."
        ),
        notes="Special Track G1 makes no serving-policy change.",
    ),
    ExactCoordinateOverlayPolicyItem(
        id="special_g_audit_logging_policy",
        category="audit_logging_policy",
        access_mode="operator_only_authenticated",
        description=(
            "Every operator-only or future exact-coordinate access event must record "
            "actor, run identifier, action type, outcome, and timestamp without sensitive values."
        ),
        exact_coordinates_allowed=True,
        raw_geometry_allowed=True,
        bounds_allowed=True,
        local_paths_allowed=False,
        private_hashes_allowed=False,
        public_summary_allowed=False,
        operator_role_required=True,
        audit_log_required=True,
        redaction_required=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        artifact_serving_change_required=True,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="requires_audit_logging",
        required_tests_before_implementation=(
            "audit event write check",
            "audit redaction check",
            "audit denial check",
        ),
        blocker="No overlay-specific audit event model exists.",
        recommended_next_action="Design audit storage and redaction before any operator overlay endpoint.",
        notes="Audit payloads must avoid exact coordinate values and local filesystem paths.",
    ),
    ExactCoordinateOverlayPolicyItem(
        id="special_g_operator_only_preview_policy",
        category="operator_only_preview_policy",
        access_mode="operator_only_authenticated",
        description=(
            "Operator-only preview may show exact-coordinate overlays only after "
            "authentication, role checks, audit logging, and explicit future approval."
        ),
        exact_coordinates_allowed=True,
        raw_geometry_allowed=True,
        bounds_allowed=True,
        local_paths_allowed=False,
        private_hashes_allowed=False,
        public_summary_allowed=False,
        operator_role_required=True,
        audit_log_required=True,
        redaction_required=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        artifact_serving_change_required=True,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="requires_frontend_review",
        required_tests_before_implementation=(
            "operator UI role gate check",
            "no default overlay check",
            "audit event check",
            "redacted fallback check",
        ),
        blocker="No approved frontend operator overlay design exists.",
        recommended_next_action="Create a separate operator-preview implementation plan after G1.",
        notes="G1 does not add frontend overlay controls.",
    ),
    ExactCoordinateOverlayPolicyItem(
        id="special_g_public_overlay_approval_gate",
        category="public_overlay_approval_gate",
        access_mode="public_exact_coordinate",
        description=(
            "Public exact-coordinate overlays are disabled by default and require a "
            "later user-approved implementation phase with access control and audit review."
        ),
        exact_coordinates_allowed=False,
        raw_geometry_allowed=False,
        bounds_allowed=False,
        local_paths_allowed=False,
        private_hashes_allowed=False,
        public_summary_allowed=False,
        operator_role_required=True,
        audit_log_required=True,
        redaction_required=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        artifact_serving_change_required=True,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="blocked_until_future_approval",
        required_tests_before_implementation=(
            "explicit approval marker check",
            "role gate check",
            "audit event check",
            "serving policy review check",
            "frontend review check",
        ),
        blocker="Public exact-coordinate exposure is outside G1 scope.",
        recommended_next_action="Do not implement public exact-coordinate overlays in G1.",
        notes="The default state is disabled.",
    ),
    ExactCoordinateOverlayPolicyItem(
        id="special_g_future_implementation_slices",
        category="future_implementation_slices",
        access_mode="operator_only_authenticated",
        description=(
            "Future work must split access control, audit logging, DTO schema, serving "
            "review, frontend preview, and public exposure decisions into separate slices."
        ),
        exact_coordinates_allowed=True,
        raw_geometry_allowed=True,
        bounds_allowed=True,
        local_paths_allowed=False,
        private_hashes_allowed=False,
        public_summary_allowed=False,
        operator_role_required=True,
        audit_log_required=True,
        redaction_required=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        artifact_serving_change_required=True,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="requires_access_control_implementation",
        required_tests_before_implementation=(
            "slice scope allowlist check",
            "no cross-track behavior check",
            "redaction check",
            "audit check",
        ),
        blocker="No later overlay implementation slice has been approved.",
        recommended_next_action="Start with an access-control design implementation slice if later approved.",
        notes="Special Track H, I, and J remain separate.",
    ),
)


def get_special_track_g_exact_coordinate_overlay_policy() -> tuple[
    ExactCoordinateOverlayPolicyItem,
    ...
]:
    return _POLICY_ITEMS


def write_special_track_g_exact_coordinate_overlay_policy_report(
    *,
    run_dir: str | Path,
    run_id: str,
    items: Iterable[ExactCoordinateOverlayPolicyItem] | None = None,
    report_relative_path: str | Path = SPECIAL_TRACK_G_REPORT_RELATIVE_PATH,
) -> Path:
    report_items = tuple(items or _POLICY_ITEMS)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": SPECIAL_TRACK_G_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_access_mode": _counts_by("access_mode", report_items),
        "counts_by_category": _counts_by("category", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "public_exact_coordinate_enabled": False,
        "runtime_changes": False,
        "public_exposure_changes": False,
        "artifact_serving_changes": False,
        "notes": (
            "Special Track G1 is a policy report only. It does not add overlay "
            "endpoints, frontend controls, artifact-serving changes, or map outputs."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[ExactCoordinateOverlayPolicyItem],
) -> dict[str, int]:
    if field_name == "access_mode":
        counts = {value: 0 for value in sorted(ALLOWED_ACCESS_MODES)}
    elif field_name == "category":
        counts = {value: 0 for value in sorted(ALLOWED_CATEGORIES)}
    elif field_name == "implementation_status":
        counts = {value: 0 for value in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    else:
        raise ValueError(f"unsupported count field: {field_name}")

    for item in items:
        counts[getattr(item, field_name)] += 1
    return counts
