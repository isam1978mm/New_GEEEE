from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


SPECIAL_TRACK_G2_SCHEMA_VERSION = "special_track_g2_operator_overlay_ui_policy_v1"
SPECIAL_TRACK_G2_REPORT_RELATIVE_PATH = (
    "manifests/special_track_g2_operator_overlay_ui_policy.json"
)

ALLOWED_CATEGORIES = {
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

ALLOWED_MODES = {
    "disabled_default",
    "operator_only_preview",
    "redacted_denied",
    "future_public_review_required",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "design_only",
    "blocked_until_future_approval",
    "requires_auth_implementation",
    "requires_role_policy",
    "requires_per_run_authorization",
    "requires_audit_logging",
    "requires_frontend_review",
    "requires_artifact_serving_review",
}

_OPERATOR_TESTS = (
    "authentication gate check",
    "operator role check",
    "per-run authorization check",
    "audit event check",
    "default-off check",
    "redacted denial check",
)


@dataclass(frozen=True)
class OperatorOverlayUiPolicyItem:
    id: str
    category: str
    mode: str
    description: str
    generated_overlay_visible: bool
    exact_coordinates_visible: bool
    raw_geometry_visible: bool
    bounds_visible: bool
    local_paths_visible: bool
    private_hashes_visible: bool
    public_download_allowed: bool
    authentication_required: bool
    operator_role_required: bool
    per_run_authorization_required: bool
    audit_log_required: bool
    default_off_required: bool
    redacted_denial_required: bool
    api_change_allowed_now: bool
    frontend_change_allowed_now: bool
    artifact_serving_change_allowed_now: bool
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
        if self.mode not in ALLOWED_MODES:
            raise ValueError(f"unsupported mode: {self.mode}")
        if self.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"unsupported implementation_status: {self.implementation_status}"
            )
        if self.api_change_allowed_now:
            raise ValueError("G2 does not allow API implementation now")
        if self.frontend_change_allowed_now:
            raise ValueError("G2 does not allow frontend implementation now")
        if self.artifact_serving_change_allowed_now:
            raise ValueError("G2 does not allow artifact-serving changes now")
        if self.implementation_allowed_now:
            raise ValueError("G2 is design-only and does not allow implementation now")
        if self.public_download_allowed:
            raise ValueError("G2 does not allow public downloads")
        if self.mode == "disabled_default":
            if self.generated_overlay_visible or self.exact_coordinates_visible:
                raise ValueError("disabled_default must not show generated overlays")
            if not self.default_off_required:
                raise ValueError("disabled_default requires default-off behavior")
        if self.mode == "operator_only_preview":
            if not (
                self.authentication_required
                and self.operator_role_required
                and self.per_run_authorization_required
                and self.audit_log_required
            ):
                raise ValueError("operator_only_preview requires all private access gates")
            if not self.requires_future_user_approval:
                raise ValueError("operator_only_preview requires future approval")
        if self.mode == "redacted_denied":
            if (
                self.generated_overlay_visible
                or self.exact_coordinates_visible
                or self.raw_geometry_visible
                or self.bounds_visible
                or self.local_paths_visible
                or self.private_hashes_visible
            ):
                raise ValueError("redacted_denied must not leak sensitive fields")
            if not self.redacted_denial_required:
                raise ValueError("redacted_denied requires redacted denial responses")
        if self.mode == "future_public_review_required":
            if not self.requires_future_user_approval:
                raise ValueError("future public review requires future approval")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_POLICY_ITEMS: tuple[OperatorOverlayUiPolicyItem, ...] = (
    OperatorOverlayUiPolicyItem(
        id="special_g2_operator_overlay_ui_modes",
        category="operator_overlay_ui_modes",
        mode="disabled_default",
        description=(
            "Generated private overlays are not visible in the UI by default and no "
            "API, frontend, or serving surface is added in G2."
        ),
        generated_overlay_visible=False,
        exact_coordinates_visible=False,
        raw_geometry_visible=False,
        bounds_visible=False,
        local_paths_visible=False,
        private_hashes_visible=False,
        public_download_allowed=False,
        authentication_required=False,
        operator_role_required=False,
        per_run_authorization_required=False,
        audit_log_required=False,
        default_off_required=True,
        redacted_denial_required=True,
        api_change_allowed_now=False,
        frontend_change_allowed_now=False,
        artifact_serving_change_allowed_now=False,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="design_only",
        required_tests_before_implementation=("default-off check", "no public surface check"),
        blocker="G2 is policy design only; no UI implementation is approved.",
        recommended_next_action="Keep generated overlay UI disabled until a later approved slice.",
        notes="This mode is the current default.",
    ),
    OperatorOverlayUiPolicyItem(
        id="special_g2_authentication_requirement",
        category="authentication_requirement",
        mode="operator_only_preview",
        description=(
            "Future operator-only preview must require authentication before private "
            "generated overlay results can be shown."
        ),
        generated_overlay_visible=True,
        exact_coordinates_visible=True,
        raw_geometry_visible=True,
        bounds_visible=True,
        local_paths_visible=False,
        private_hashes_visible=False,
        public_download_allowed=False,
        authentication_required=True,
        operator_role_required=True,
        per_run_authorization_required=True,
        audit_log_required=True,
        default_off_required=True,
        redacted_denial_required=True,
        api_change_allowed_now=False,
        frontend_change_allowed_now=False,
        artifact_serving_change_allowed_now=False,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="requires_auth_implementation",
        required_tests_before_implementation=_OPERATOR_TESTS,
        blocker="The app has no approved overlay authentication layer.",
        recommended_next_action="Design authentication before any generated-overlay UI work.",
        notes="Loopback-only behavior is not a sufficient G2 access gate.",
    ),
    OperatorOverlayUiPolicyItem(
        id="special_g2_operator_role_requirement",
        category="operator_role_requirement",
        mode="operator_only_preview",
        description=(
            "Future preview must require an explicit operator role before generated "
            "private overlay content is visible."
        ),
        generated_overlay_visible=True,
        exact_coordinates_visible=True,
        raw_geometry_visible=True,
        bounds_visible=True,
        local_paths_visible=False,
        private_hashes_visible=False,
        public_download_allowed=False,
        authentication_required=True,
        operator_role_required=True,
        per_run_authorization_required=True,
        audit_log_required=True,
        default_off_required=True,
        redacted_denial_required=True,
        api_change_allowed_now=False,
        frontend_change_allowed_now=False,
        artifact_serving_change_allowed_now=False,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="requires_role_policy",
        required_tests_before_implementation=_OPERATOR_TESTS,
        blocker="No operator role policy is implemented for overlay viewing.",
        recommended_next_action="Define operator role rules before preview implementation.",
        notes="Role checks must happen before private overlay content is loaded.",
    ),
    OperatorOverlayUiPolicyItem(
        id="special_g2_per_run_authorization_policy",
        category="per_run_authorization_policy",
        mode="operator_only_preview",
        description=(
            "Future preview must verify that the operator may access the specific run "
            "whose private overlay is being displayed."
        ),
        generated_overlay_visible=True,
        exact_coordinates_visible=True,
        raw_geometry_visible=True,
        bounds_visible=True,
        local_paths_visible=False,
        private_hashes_visible=False,
        public_download_allowed=False,
        authentication_required=True,
        operator_role_required=True,
        per_run_authorization_required=True,
        audit_log_required=True,
        default_off_required=True,
        redacted_denial_required=True,
        api_change_allowed_now=False,
        frontend_change_allowed_now=False,
        artifact_serving_change_allowed_now=False,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="requires_per_run_authorization",
        required_tests_before_implementation=_OPERATOR_TESTS,
        blocker="No per-run generated-overlay authorization model is approved.",
        recommended_next_action="Design per-run authorization before generated overlay preview work.",
        notes="Authorization failures must use redacted denial responses.",
    ),
    OperatorOverlayUiPolicyItem(
        id="special_g2_audit_logging_requirement",
        category="audit_logging_requirement",
        mode="operator_only_preview",
        description=(
            "Future preview must write an audit event for successful and denied "
            "generated-overlay access attempts without sensitive payload values."
        ),
        generated_overlay_visible=True,
        exact_coordinates_visible=True,
        raw_geometry_visible=True,
        bounds_visible=True,
        local_paths_visible=False,
        private_hashes_visible=False,
        public_download_allowed=False,
        authentication_required=True,
        operator_role_required=True,
        per_run_authorization_required=True,
        audit_log_required=True,
        default_off_required=True,
        redacted_denial_required=True,
        api_change_allowed_now=False,
        frontend_change_allowed_now=False,
        artifact_serving_change_allowed_now=False,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="requires_audit_logging",
        required_tests_before_implementation=(
            "audit allow event check",
            "audit denial event check",
            "audit redaction check",
        ),
        blocker="No generated-overlay audit event schema is approved.",
        recommended_next_action="Define audit event schema before preview implementation.",
        notes="Audit logs must not contain geometry, paths, hashes, or coordinate values.",
    ),
    OperatorOverlayUiPolicyItem(
        id="special_g2_default_off_configuration",
        category="default_off_configuration",
        mode="disabled_default",
        description=(
            "Generated private overlay UI remains default-off even after a future "
            "implementation slice exists."
        ),
        generated_overlay_visible=False,
        exact_coordinates_visible=False,
        raw_geometry_visible=False,
        bounds_visible=False,
        local_paths_visible=False,
        private_hashes_visible=False,
        public_download_allowed=False,
        authentication_required=True,
        operator_role_required=True,
        per_run_authorization_required=True,
        audit_log_required=True,
        default_off_required=True,
        redacted_denial_required=True,
        api_change_allowed_now=False,
        frontend_change_allowed_now=False,
        artifact_serving_change_allowed_now=False,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="design_only",
        required_tests_before_implementation=("config default-off check", "denial response check"),
        blocker="No default-off config key is approved in G2.",
        recommended_next_action="Keep overlay preview disabled until a future config design.",
        notes="G2 does not add configuration or runtime behavior.",
    ),
    OperatorOverlayUiPolicyItem(
        id="special_g2_private_overlay_dto_boundary",
        category="private_overlay_dto_boundary",
        mode="operator_only_preview",
        description=(
            "Future private overlay DTOs may contain generated geometry only after "
            "all operator-only gates pass; public DTOs remain redacted."
        ),
        generated_overlay_visible=True,
        exact_coordinates_visible=True,
        raw_geometry_visible=True,
        bounds_visible=True,
        local_paths_visible=False,
        private_hashes_visible=False,
        public_download_allowed=False,
        authentication_required=True,
        operator_role_required=True,
        per_run_authorization_required=True,
        audit_log_required=True,
        default_off_required=True,
        redacted_denial_required=True,
        api_change_allowed_now=False,
        frontend_change_allowed_now=False,
        artifact_serving_change_allowed_now=False,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="requires_frontend_review",
        required_tests_before_implementation=(
            "private DTO role gate check",
            "public DTO redaction check",
            "no path field check",
        ),
        blocker="No private generated-overlay DTO schema is approved.",
        recommended_next_action="Review private DTO schema in a future implementation slice.",
        notes="Private DTO schema must remain separate from public DTO schema.",
    ),
    OperatorOverlayUiPolicyItem(
        id="special_g2_redacted_denial_response_policy",
        category="redacted_denial_response_policy",
        mode="redacted_denied",
        description=(
            "Denied access responses must be generic and must not reveal generated "
            "overlay presence, coordinate values, geometry, paths, hashes, or file contents."
        ),
        generated_overlay_visible=False,
        exact_coordinates_visible=False,
        raw_geometry_visible=False,
        bounds_visible=False,
        local_paths_visible=False,
        private_hashes_visible=False,
        public_download_allowed=False,
        authentication_required=True,
        operator_role_required=True,
        per_run_authorization_required=True,
        audit_log_required=True,
        default_off_required=True,
        redacted_denial_required=True,
        api_change_allowed_now=False,
        frontend_change_allowed_now=False,
        artifact_serving_change_allowed_now=False,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="design_only",
        required_tests_before_implementation=(
            "denial body redaction check",
            "denial log redaction check",
            "presence leak check",
        ),
        blocker="No overlay denial response schema is approved.",
        recommended_next_action="Define denial response schema before any UI implementation.",
        notes="Denied responses must not reveal whether a generated private overlay exists.",
    ),
    OperatorOverlayUiPolicyItem(
        id="special_g2_no_public_download_boundary",
        category="no_public_download_boundary",
        mode="future_public_review_required",
        description=(
            "Generated overlay artifacts remain non-downloadable through public API by "
            "default; any download behavior requires later serving-policy review."
        ),
        generated_overlay_visible=False,
        exact_coordinates_visible=False,
        raw_geometry_visible=False,
        bounds_visible=False,
        local_paths_visible=False,
        private_hashes_visible=False,
        public_download_allowed=False,
        authentication_required=True,
        operator_role_required=True,
        per_run_authorization_required=True,
        audit_log_required=True,
        default_off_required=True,
        redacted_denial_required=True,
        api_change_allowed_now=False,
        frontend_change_allowed_now=False,
        artifact_serving_change_allowed_now=False,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="requires_artifact_serving_review",
        required_tests_before_implementation=(
            "download denial check",
            "artifact-serving policy review check",
            "audit event check",
        ),
        blocker="Public download behavior is outside G2 scope.",
        recommended_next_action="Do not add generated overlay downloads in G2.",
        notes="Private generated overlays remain filesystem-only unless later approved.",
    ),
    OperatorOverlayUiPolicyItem(
        id="special_g2_future_ui_implementation_slices",
        category="future_ui_implementation_slices",
        mode="future_public_review_required",
        description=(
            "Future work must split authentication, role policy, per-run authorization, "
            "audit logging, DTO review, frontend preview, and serving review into small slices."
        ),
        generated_overlay_visible=False,
        exact_coordinates_visible=False,
        raw_geometry_visible=False,
        bounds_visible=False,
        local_paths_visible=False,
        private_hashes_visible=False,
        public_download_allowed=False,
        authentication_required=True,
        operator_role_required=True,
        per_run_authorization_required=True,
        audit_log_required=True,
        default_off_required=True,
        redacted_denial_required=True,
        api_change_allowed_now=False,
        frontend_change_allowed_now=False,
        artifact_serving_change_allowed_now=False,
        implementation_allowed_now=False,
        requires_future_user_approval=True,
        implementation_status="blocked_until_future_approval",
        required_tests_before_implementation=(
            "slice scope allowlist check",
            "no cross-track behavior check",
            "no public default check",
        ),
        blocker="No future generated-overlay UI implementation slice is approved.",
        recommended_next_action="Start with authentication and role policy if a later G2 implementation is approved.",
        notes="Special Track H, I, and J remain separate.",
    ),
)


def get_special_track_g2_operator_overlay_ui_policy() -> tuple[
    OperatorOverlayUiPolicyItem,
    ...
]:
    return _POLICY_ITEMS


def write_special_track_g2_operator_overlay_ui_policy_report(
    *,
    run_dir: str | Path,
    run_id: str,
    items: Iterable[OperatorOverlayUiPolicyItem] | None = None,
    report_relative_path: str | Path = SPECIAL_TRACK_G2_REPORT_RELATIVE_PATH,
) -> Path:
    report_items = tuple(items or _POLICY_ITEMS)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": SPECIAL_TRACK_G2_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_mode": _counts_by("mode", report_items),
        "counts_by_category": _counts_by("category", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "operator_overlay_ui_enabled": False,
        "runtime_changes": False,
        "public_exposure_changes": False,
        "artifact_serving_changes": False,
        "notes": (
            "Special Track G2 is a policy report only. It does not add overlay UI, "
            "API routes, frontend controls, artifact-serving changes, or map outputs."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[OperatorOverlayUiPolicyItem],
) -> dict[str, int]:
    if field_name == "mode":
        counts = {value: 0 for value in sorted(ALLOWED_MODES)}
    elif field_name == "category":
        counts = {value: 0 for value in sorted(ALLOWED_CATEGORIES)}
    elif field_name == "implementation_status":
        counts = {value: 0 for value in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    else:
        raise ValueError(f"unsupported count field: {field_name}")

    for item in items:
        counts[getattr(item, field_name)] += 1
    return counts
