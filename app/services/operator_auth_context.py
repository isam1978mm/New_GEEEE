from __future__ import annotations

from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class OperatorAuthContext:
    actor_id: str | None
    is_authenticated: bool
    roles: tuple[str, ...]
    authorized_run_ids: tuple[str, ...]
    request_id: str


def resolve_operator_auth_context(
    *,
    trusted_proxy_enabled: bool,
    x_operator_authenticated: str | None,
    x_operator_id: str | None,
    x_operator_roles: str | None,
    x_operator_authorized_runs: str | None,
    x_request_id: str | None,
) -> OperatorAuthContext:
    if not trusted_proxy_enabled:
        return OperatorAuthContext(
            actor_id=None,
            is_authenticated=False,
            roles=(),
            authorized_run_ids=(),
            request_id=f"req_{uuid.uuid4().hex}",
        )

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


__all__ = (
    "OperatorAuthContext",
    "resolve_operator_auth_context",
)
