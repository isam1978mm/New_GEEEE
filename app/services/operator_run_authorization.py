from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class OperatorRunAuthorizationResult:
    allowed: bool
    reason: str


def resolve_run_authorization(
    *,
    settings: Settings,
    actor_id: str | None,
    run_id: str,
) -> OperatorRunAuthorizationResult:
    """Return whether an actor is authorized for a given run.

    Fail-closed: any missing or unmatched record returns denied.
    """
    if actor_id is None or actor_id.strip() == "":
        return OperatorRunAuthorizationResult(allowed=False, reason="missing_actor")

    if run_id is None or run_id.strip() == "":
        return OperatorRunAuthorizationResult(allowed=False, reason="missing_run")

    normalized_actor = actor_id.strip()
    normalized_run = run_id.strip()
    authorizations = settings.operator_run_authorizations

    allowed_runs = authorizations.get(normalized_actor)
    if allowed_runs is None:
        return OperatorRunAuthorizationResult(allowed=False, reason="actor_not_authorized")

    if normalized_run in allowed_runs:
        return OperatorRunAuthorizationResult(allowed=True, reason="authorized")

    return OperatorRunAuthorizationResult(allowed=False, reason="run_not_authorized")


__all__ = (
    "OperatorRunAuthorizationResult",
    "resolve_run_authorization",
)
