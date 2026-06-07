from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import JSONResponse

from app.config import Settings
from app.deps import get_settings_from_request
from app.pipeline.parity.operator_overlay_implementation_design import ALLOWED_ACCESS_MODE
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
) -> JSONResponse:
    """Default-off, operator-only private overlay preview.

    The operator identity, role, and per-run authorization are supplied by an
    upstream authenticated context (here mapped from request headers). The route
    stays default-off: when the config flag is disabled, every request is denied
    regardless of headers. No public overlay, public download, or artifact-serving
    URL is produced, and no private artifact file is read on a denied decision.
    """

    is_authenticated = (x_operator_authenticated or "").strip().lower() == "true"
    roles = tuple(role.strip() for role in (x_operator_roles or "").split(",") if role.strip())
    authorized_run_ids = tuple(
        value.strip() for value in (x_operator_authorized_runs or "").split(",") if value.strip()
    )
    request_id = (x_request_id or "").strip() or f"req_{uuid.uuid4().hex}"

    result = build_operator_overlay_preview(
        settings=settings,
        run_id=run_id,
        requested_artifact_family=artifact_family,
        requested_access_mode=access_mode,
        actor_id=(x_operator_id or "").strip() or None,
        is_authenticated=is_authenticated,
        roles=roles,
        authorized_run_ids=authorized_run_ids,
        request_id=request_id,
    )
    return JSONResponse(status_code=result.status_code, content=result.body)
