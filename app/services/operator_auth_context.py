from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.config import Settings
from app.pipeline.parity.operator_overlay_access_foundation import OPERATOR_ROLE
from app.services.operator_token_verifier import verify_operator_token


_LOCAL_OPERATOR_ACTOR_ID = "local-operator"
_LOCAL_OPERATOR_AUTHORIZED_RUNS = ("*",)


@dataclass(frozen=True)
class OperatorAuthContext:
    actor_id: str | None
    is_authenticated: bool
    roles: tuple[str, ...]
    authorized_run_ids: tuple[str, ...]
    request_id: str


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    stripped = authorization.strip()
    if stripped.lower().startswith("bearer "):
        token = stripped[7:].strip()
        return token if token else None
    return None


def resolve_operator_auth_context(
    *,
    trusted_proxy_enabled: bool,
    x_operator_authenticated: str | None,
    x_operator_id: str | None,
    x_operator_roles: str | None,
    x_operator_authorized_runs: str | None,
    x_request_id: str | None,
    settings: Settings | None = None,
    authorization: str | None = None,
) -> OperatorAuthContext:
    if settings is not None and settings.operator_auth_oidc_enabled:
        token = _extract_bearer_token(authorization)
        result = verify_operator_token(token=token, settings=settings)
        if result.verified:
            request_id = (x_request_id or "").strip() or f"req_{uuid.uuid4().hex}"
            return OperatorAuthContext(
                actor_id=result.actor_id,
                is_authenticated=True,
                roles=result.roles,
                authorized_run_ids=(),
                request_id=request_id,
            )
        return OperatorAuthContext(
            actor_id=None,
            is_authenticated=False,
            roles=(),
            authorized_run_ids=(),
            request_id=f"req_{uuid.uuid4().hex}",
        )

    if trusted_proxy_enabled and _has_trusted_proxy_headers(
        x_operator_authenticated=x_operator_authenticated,
        x_operator_id=x_operator_id,
        x_operator_roles=x_operator_roles,
        x_operator_authorized_runs=x_operator_authorized_runs,
    ):
        return _trusted_proxy_context(
            x_operator_authenticated=x_operator_authenticated,
            x_operator_id=x_operator_id,
            x_operator_roles=x_operator_roles,
            x_operator_authorized_runs=x_operator_authorized_runs,
            x_request_id=x_request_id,
        )

    if _local_development_operator_bypass_allowed(settings):
        return _local_development_operator_context(x_request_id=x_request_id)

    if not trusted_proxy_enabled:
        return OperatorAuthContext(
            actor_id=None,
            is_authenticated=False,
            roles=(),
            authorized_run_ids=(),
            request_id=f"req_{uuid.uuid4().hex}",
        )

    return _trusted_proxy_context(
        x_operator_authenticated=x_operator_authenticated,
        x_operator_id=x_operator_id,
        x_operator_roles=x_operator_roles,
        x_operator_authorized_runs=x_operator_authorized_runs,
        x_request_id=x_request_id,
    )


def _trusted_proxy_context(
    *,
    x_operator_authenticated: str | None,
    x_operator_id: str | None,
    x_operator_roles: str | None,
    x_operator_authorized_runs: str | None,
    x_request_id: str | None,
) -> OperatorAuthContext:
    is_authenticated = (x_operator_authenticated or "").strip().lower() == "true"
    roles = tuple(role.strip() for role in (x_operator_roles or "").split(",") if role.strip())
    authorized_run_ids = tuple(
        value.strip() for value in (x_operator_authorized_runs or "").split(",") if value.strip()
    )
    request_id = (x_request_id or "").strip() or f"req_{uuid.uuid4().hex}"

    return OperatorAuthContext(
        actor_id=(x_operator_id or "").strip() or None,
        is_authenticated=is_authenticated,
        roles=roles,
        authorized_run_ids=authorized_run_ids,
        request_id=request_id,
    )


def _has_trusted_proxy_headers(
    *,
    x_operator_authenticated: str | None,
    x_operator_id: str | None,
    x_operator_roles: str | None,
    x_operator_authorized_runs: str | None,
) -> bool:
    return any(
        (value or "").strip()
        for value in (
            x_operator_authenticated,
            x_operator_id,
            x_operator_roles,
            x_operator_authorized_runs,
        )
    )


def _local_development_operator_bypass_allowed(settings: Settings | None) -> bool:
    return settings is not None and not settings.operator_auth_oidc_enabled and not settings.allow_network_bind


def _local_development_operator_context(*, x_request_id: str | None) -> OperatorAuthContext:
    request_id = (x_request_id or "").strip() or f"req_{uuid.uuid4().hex}"
    return OperatorAuthContext(
        actor_id=_LOCAL_OPERATOR_ACTOR_ID,
        is_authenticated=True,
        roles=(OPERATOR_ROLE,),
        authorized_run_ids=_LOCAL_OPERATOR_AUTHORIZED_RUNS,
        request_id=request_id,
    )


__all__ = (
    "OperatorAuthContext",
    "resolve_operator_auth_context",
)
