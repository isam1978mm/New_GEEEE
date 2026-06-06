from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Iterable

from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.operator_overlay_implementation_design import (
    ALLOWED_ACCESS_MODE,
    ALLOWED_ARTIFACT_FAMILIES,
    BLOCKED_PUBLIC_EXPOSURE_MODES,
)


FUTURE_SLICE_11_G2_SCHEMA_VERSION = "future_slice_11_g2_auth_role_audit_foundation_v1"
FUTURE_SLICE_11_G2_REPORT_RELATIVE_PATH = (
    "manifests/future_slice_11_g2_auth_role_audit_foundation.json"
)
FUTURE_SLICE_11_FOUNDATION_ID = "future_slice_11_g2_auth_role_audit_foundation"

OPERATOR_ROLE = "operator"
AUDIT_EVENT_TYPE = "operator_overlay_access_decision"

ALLOWED_ACCESS_DECISION_STATUSES = {
    "allowed_operator_preview",
    "denied_default_off",
    "denied_unauthenticated",
    "denied_missing_operator_role",
    "denied_run_not_authorized",
    "denied_unsupported_artifact_family",
    "denied_unsupported_access_mode",
    "denied_public_exposure_blocked",
}

# Internal reason codes carried in the server-side decision and the private audit
# event. The public redacted denial response intentionally uses a single generic
# reason code so that denials cannot reveal artifact or run existence.
_INTERNAL_REASON_CODES = {
    "allowed_operator_preview": "ACCESS_GRANTED",
    "denied_default_off": "OVERLAY_PREVIEW_DISABLED",
    "denied_unauthenticated": "NOT_AUTHENTICATED",
    "denied_missing_operator_role": "OPERATOR_ROLE_REQUIRED",
    "denied_run_not_authorized": "RUN_NOT_AUTHORIZED",
    "denied_unsupported_artifact_family": "UNSUPPORTED_ARTIFACT_FAMILY",
    "denied_unsupported_access_mode": "UNSUPPORTED_ACCESS_MODE",
    "denied_public_exposure_blocked": "PUBLIC_EXPOSURE_BLOCKED",
}

GENERIC_DENIAL_REASON_CODE = "ACCESS_DENIED"
GENERIC_DENIAL_STATUS = "access_denied"
GENERIC_DENIAL_MESSAGE = "Access to the requested resource is not available."
GENERIC_DENIAL_SUPPORT_REFERENCE = "contact_operator_administrator"

REDACTED_DENIAL_RESPONSE_FIELDS = (
    "status",
    "reason_code",
    "request_id",
    "message",
    "retry_allowed",
    "support_reference",
)

REDACTED_DENIAL_FORBIDDEN_FIELDS = (
    "exact_coordinates",
    "raw_geometry",
    "bounds",
    "kml_contents",
    "heatmap_point_payloads",
    "local_paths",
    "private_hashes",
    "artifact_contents",
    "private_artifact_existence",
    "download_urls",
    "file_names",
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
    "download_urls",
)


@dataclass(frozen=True)
class OverlayAccessRequest:
    actor_id: str | None
    is_authenticated: bool
    roles: tuple[str, ...]
    run_id: str
    requested_artifact_family: str
    requested_access_mode: str
    operator_overlay_preview_enabled: bool
    request_id: str
    authorized_run_ids: tuple[str, ...] | None = None
    authorization_result: bool | None = None
    reason_context: str | None = None


@dataclass(frozen=True)
class OverlayAccessDecision:
    allowed: bool
    status: str
    actor_id_redacted: str
    run_id: str
    artifact_family: str
    access_mode: str
    request_id: str
    reason_code: str
    audit_required: bool
    redacted_denial: dict[str, Any] | None
    public_exposure_changes: bool = False
    artifact_serving_changes: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_operator_overlay_access_foundation_policy() -> dict[str, Any]:
    """Return the G2 access-control and audit foundation policy."""

    return {
        "allowed_artifact_families": list(ALLOWED_ARTIFACT_FAMILIES),
        "allowed_access_modes": [ALLOWED_ACCESS_MODE],
        "denied_access_modes": [*BLOCKED_PUBLIC_EXPOSURE_MODES, "unknown_or_unsupported"],
        "operator_role_required": OPERATOR_ROLE,
        "default_off_required": True,
        "decision_policy": {
            "gate_order": [
                "operator_overlay_preview_enabled",
                "is_authenticated",
                "operator_role",
                "per_run_authorization",
                "access_mode",
                "artifact_family",
            ],
            "allow_only_when_all_gates_pass": True,
            "fail_closed": True,
            "every_decision_requires_audit": True,
            "no_artifact_file_is_opened": True,
            "statuses": sorted(ALLOWED_ACCESS_DECISION_STATUSES),
        },
        "redacted_denial_policy": {
            "fields": list(REDACTED_DENIAL_RESPONSE_FIELDS),
            "forbidden_fields": list(REDACTED_DENIAL_FORBIDDEN_FIELDS),
            "generic_reason_code": GENERIC_DENIAL_REASON_CODE,
            "must_not_reveal_artifact_existence": True,
            "must_not_distinguish_denial_cause": True,
        },
        "audit_policy": {
            "event_fields": list(AUDIT_EVENT_FIELDS),
            "forbidden_fields": list(AUDIT_FORBIDDEN_FIELDS),
            "allow_and_deny_events_required": True,
            "internal_reason_codes": dict(_INTERNAL_REASON_CODES),
        },
    }


def evaluate_overlay_access(request: OverlayAccessRequest) -> OverlayAccessDecision:
    """Decide whether an operator-only private overlay preview is allowed.

    This is an internal access-control decision only. It does not read or serve any
    private artifact file, add a route, or change artifact serving.
    """

    status = _decide_status(request)
    allowed = status == "allowed_operator_preview"
    reason_code = _INTERNAL_REASON_CODES[status]
    redacted_denial = None if allowed else _build_generic_denial(request.request_id)
    return OverlayAccessDecision(
        allowed=allowed,
        status=status,
        actor_id_redacted=_redact_actor_id(request.actor_id, request.is_authenticated),
        run_id=request.run_id,
        artifact_family=request.requested_artifact_family,
        access_mode=request.requested_access_mode,
        request_id=request.request_id,
        reason_code=reason_code,
        audit_required=True,
        redacted_denial=redacted_denial,
    )


def build_redacted_denial_response(decision: OverlayAccessDecision) -> dict[str, Any]:
    """Build the public-safe redacted denial response for a decision.

    The response is identical for every denial cause so it cannot reveal whether a
    run or private artifact exists.
    """

    if decision.allowed:
        raise ValueError("redacted denial response is only built for denied decisions")
    return _build_generic_denial(decision.request_id)


def build_audit_event(
    decision: OverlayAccessDecision,
    *,
    actor_id: str | None,
    event_type: str = AUDIT_EVENT_TYPE,
) -> dict[str, Any]:
    """Build a private audit event for an access decision.

    The audit event records accountability fields and the internal reason code. It
    does not include coordinates, geometry, KML contents, heatmap payloads, paths,
    hashes, artifact contents, or download URLs.
    """

    return {
        "event_type": event_type,
        "actor_id": actor_id if actor_id else "anonymous",
        "run_id": decision.run_id,
        "artifact_family": decision.artifact_family,
        "access_mode": decision.access_mode,
        "access_outcome": "allowed" if decision.allowed else "denied",
        "timestamp": datetime.now(UTC).isoformat(),
        "reason_code": decision.reason_code,
        "request_id": decision.request_id,
        "client_context_redacted": "redacted",
    }


def write_future_slice_11_g2_auth_role_audit_foundation_report(
    *,
    run_dir: str | Path,
    run_id: str,
    sample_requests: Iterable[OverlayAccessRequest] | None = None,
    report_relative_path: str | Path = FUTURE_SLICE_11_G2_REPORT_RELATIVE_PATH,
) -> Path:
    """Write the private Future Slice 11 access/audit foundation report.

    This is auth/role/audit foundation only. It does not implement the overlay API
    route or frontend UI, expose private overlays or exact coordinates, read or
    serve private artifact files, change artifact serving, call Earth Engine, or
    generate map artifacts.
    """

    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    requests = tuple(sample_requests) if sample_requests is not None else _default_sample_requests()
    sample_decisions: list[dict[str, Any]] = []
    statuses: list[str] = []
    for request in requests:
        decision = evaluate_overlay_access(request)
        statuses.append(decision.status)
        audit_event = build_audit_event(decision, actor_id=request.actor_id)
        sample_decisions.append(
            {
                "decision": decision.to_dict(),
                "audit_event": audit_event,
            }
        )

    policy = get_operator_overlay_access_foundation_policy()
    payload = {
        "schema_version": FUTURE_SLICE_11_G2_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "foundation_id": FUTURE_SLICE_11_FOUNDATION_ID,
        "allowed_artifact_families": list(ALLOWED_ARTIFACT_FAMILIES),
        "allowed_access_modes": [ALLOWED_ACCESS_MODE],
        "denied_access_modes": [*BLOCKED_PUBLIC_EXPOSURE_MODES, "unknown_or_unsupported"],
        "decision_policy": policy["decision_policy"],
        "redacted_denial_policy": policy["redacted_denial_policy"],
        "audit_policy": policy["audit_policy"],
        "sample_decisions": sample_decisions,
        "counts_by_status": _counts_by_status(statuses),
        "g2_auth_role_audit_foundation_only": True,
        "api_route_added": False,
        "frontend_ui_added": False,
        "overlay_runtime_added": False,
        "artifact_serving_changes": False,
        "public_exposure_changes": False,
        "earth_engine_calls_added": False,
        "artifact_generation": False,
        "notes": (
            "Future Slice 11 adds the operator-only private overlay access-control and "
            "audit foundation. Access is denied by default unless the default-off config is "
            "enabled, and is allowed only when authentication, operator role, per-run "
            "authorization, an allowed artifact family, and operator_only_preview mode all "
            "pass. No API route, frontend UI, or artifact-serving change is added and no "
            "private artifact file is read or served. Future Slice 12 implements the "
            "operator-only private overlay preview only after this foundation passes."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _decide_status(request: OverlayAccessRequest) -> str:
    if not request.operator_overlay_preview_enabled:
        return "denied_default_off"
    if not request.is_authenticated:
        return "denied_unauthenticated"
    if OPERATOR_ROLE not in set(request.roles):
        return "denied_missing_operator_role"
    if not _is_run_authorized(request):
        return "denied_run_not_authorized"
    if request.requested_access_mode in set(BLOCKED_PUBLIC_EXPOSURE_MODES):
        return "denied_public_exposure_blocked"
    if request.requested_access_mode != ALLOWED_ACCESS_MODE:
        return "denied_unsupported_access_mode"
    if request.requested_artifact_family not in set(ALLOWED_ARTIFACT_FAMILIES):
        return "denied_unsupported_artifact_family"
    return "allowed_operator_preview"


def _is_run_authorized(request: OverlayAccessRequest) -> bool:
    if request.authorization_result is not None:
        return bool(request.authorization_result)
    if request.authorized_run_ids is not None:
        return request.run_id in set(request.authorized_run_ids)
    return False


def _build_generic_denial(request_id: str) -> dict[str, Any]:
    return {
        "status": GENERIC_DENIAL_STATUS,
        "reason_code": GENERIC_DENIAL_REASON_CODE,
        "request_id": request_id,
        "message": GENERIC_DENIAL_MESSAGE,
        "retry_allowed": False,
        "support_reference": GENERIC_DENIAL_SUPPORT_REFERENCE,
    }


def _redact_actor_id(actor_id: str | None, is_authenticated: bool) -> str:
    if not actor_id or not is_authenticated:
        return "anonymous"
    return "operator_redacted"


def _counts_by_status(statuses: Iterable[str]) -> dict[str, int]:
    counts = {status: 0 for status in sorted(ALLOWED_ACCESS_DECISION_STATUSES)}
    for status in statuses:
        counts[status] += 1
    return counts


def _default_sample_requests() -> tuple[OverlayAccessRequest, ...]:
    base = {
        "actor_id": "operator_sample",
        "is_authenticated": True,
        "roles": (OPERATOR_ROLE,),
        "run_id": "run_sample_authorized",
        "requested_artifact_family": ALLOWED_ARTIFACT_FAMILIES[0],
        "requested_access_mode": ALLOWED_ACCESS_MODE,
        "operator_overlay_preview_enabled": True,
        "authorized_run_ids": ("run_sample_authorized",),
    }
    return (
        OverlayAccessRequest(request_id="sample_allowed", **base),
        OverlayAccessRequest(
            request_id="sample_default_off",
            **{**base, "operator_overlay_preview_enabled": False},
        ),
        OverlayAccessRequest(
            request_id="sample_unauthenticated",
            **{**base, "is_authenticated": False},
        ),
        OverlayAccessRequest(
            request_id="sample_missing_role",
            **{**base, "roles": ("viewer",)},
        ),
        OverlayAccessRequest(
            request_id="sample_run_not_authorized",
            **{**base, "authorized_run_ids": ("other_run",)},
        ),
        OverlayAccessRequest(
            request_id="sample_public_mode",
            **{**base, "requested_access_mode": BLOCKED_PUBLIC_EXPOSURE_MODES[0]},
        ),
        OverlayAccessRequest(
            request_id="sample_bad_family",
            **{**base, "requested_artifact_family": "public_overlay_any"},
        ),
    )
