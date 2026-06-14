from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import JSONResponse

from app.api.v6_app_flow import router as v6_app_flow_router
from app.config import Settings
from app.deps import get_settings_from_request
from app.pipeline.parity.operator_overlay_implementation_design import ALLOWED_ACCESS_MODE
from app.services.operator_auth_context import resolve_operator_auth_context
from app.services.operator_overlay_preview import build_operator_overlay_preview

router = APIRouter(tags=["operator-overlays"])


@router.get("/runs/{run_id}/operator/private-overlays")
async def get_operator_private_overlay_preview(
    run_id: str,
    artifact_family: str = Query(..., description="Requested private artifact family"),
    access_mode: str = Query(default=ALLOWED_ACCESS_MODE),
    settings: Settings = Depends(get_settings_from_request),
    x_operator_authenticated: str | None = Header(default=None),
    x_operator_id: str | None = Header(default=None),
    x_operator_roles: str | None = Header(default=None),
    x_operator_authorized_runs: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    """Default-off, operator-only private overlay preview.

    The operator identity, role, and per-run authorization are supplied by an
    upstream authenticated context (here mapped from request headers). The route
    stays default-off: when the config flag is disabled, every request is denied
    regardless of headers. No public overlay, public download, or artifact-serving
    URL is produced, and no private artifact file is read on a denied decision.
    """

    auth_context = resolve_operator_auth_context(
        trusted_proxy_enabled=settings.operator_auth_trusted_proxy_enabled,
        x_operator_authenticated=x_operator_authenticated,
        x_operator_id=x_operator_id,
        x_operator_roles=x_operator_roles,
        x_operator_authorized_runs=x_operator_authorized_runs,
        x_request_id=x_request_id,
        settings=settings,
        authorization=authorization,
    )

    result = build_operator_overlay_preview(
        settings=settings,
        run_id=run_id,
        requested_artifact_family=artifact_family,
        requested_access_mode=access_mode,
        actor_id=auth_context.actor_id,
        is_authenticated=auth_context.is_authenticated,
        roles=auth_context.roles,
        authorized_run_ids=auth_context.authorized_run_ids,
        request_id=auth_context.request_id,
    )
    return JSONResponse(status_code=result.status_code, content=result.body)


router.include_router(v6_app_flow_router)
