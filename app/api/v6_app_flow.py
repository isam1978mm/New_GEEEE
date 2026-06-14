from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from fastapi.responses import FileResponse, JSONResponse, Response

from app.config import Settings
from app.deps import get_settings_from_request
from app.services.operator_auth_context import resolve_operator_auth_context
from app.services.v6_app_flow import (
    V6PrivatePackageAccessContext,
    generate_private_v6_package,
    resolve_private_v6_package_download,
    review_private_v6_package,
)

router = APIRouter(tags=["v6-private-package"])


@router.post("/runs/{run_id}/operator/v6/package/generate", response_model=None)
async def generate_v6_private_package(
    run_id: str,
    settings: Settings = Depends(get_settings_from_request),
    x_operator_authenticated: str | None = Header(default=None),
    x_operator_id: str | None = Header(default=None),
    x_operator_roles: str | None = Header(default=None),
    x_operator_authorized_runs: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    access_context = _access_context_from_headers(
        settings=settings,
        x_operator_authenticated=x_operator_authenticated,
        x_operator_id=x_operator_id,
        x_operator_roles=x_operator_roles,
        x_operator_authorized_runs=x_operator_authorized_runs,
        x_request_id=x_request_id,
        authorization=authorization,
    )
    result = generate_private_v6_package(settings=settings, run_id=run_id, access_context=access_context)
    return JSONResponse(status_code=result.status_code, content=result.body)


@router.get("/runs/{run_id}/operator/v6/package/review", response_model=None)
async def review_v6_private_package(
    run_id: str,
    settings: Settings = Depends(get_settings_from_request),
    x_operator_authenticated: str | None = Header(default=None),
    x_operator_id: str | None = Header(default=None),
    x_operator_roles: str | None = Header(default=None),
    x_operator_authorized_runs: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    access_context = _access_context_from_headers(
        settings=settings,
        x_operator_authenticated=x_operator_authenticated,
        x_operator_id=x_operator_id,
        x_operator_roles=x_operator_roles,
        x_operator_authorized_runs=x_operator_authorized_runs,
        x_request_id=x_request_id,
        authorization=authorization,
    )
    result = review_private_v6_package(settings=settings, run_id=run_id, access_context=access_context)
    return JSONResponse(status_code=result.status_code, content=result.body)


@router.get("/runs/{run_id}/operator/v6/package/download", response_model=None)
async def download_v6_private_package(
    run_id: str,
    settings: Settings = Depends(get_settings_from_request),
    x_operator_authenticated: str | None = Header(default=None),
    x_operator_id: str | None = Header(default=None),
    x_operator_roles: str | None = Header(default=None),
    x_operator_authorized_runs: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> Response:
    access_context = _access_context_from_headers(
        settings=settings,
        x_operator_authenticated=x_operator_authenticated,
        x_operator_id=x_operator_id,
        x_operator_roles=x_operator_roles,
        x_operator_authorized_runs=x_operator_authorized_runs,
        x_request_id=x_request_id,
        authorization=authorization,
    )
    result = resolve_private_v6_package_download(settings=settings, run_id=run_id, access_context=access_context)
    if result.file_path is None:
        return JSONResponse(status_code=result.status_code, content=result.body)
    return FileResponse(result.file_path, filename=result.file_name, media_type="application/zip")


def _access_context_from_headers(
    *,
    settings: Settings,
    x_operator_authenticated: str | None,
    x_operator_id: str | None,
    x_operator_roles: str | None,
    x_operator_authorized_runs: str | None,
    x_request_id: str | None,
    authorization: str | None,
) -> V6PrivatePackageAccessContext:
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
    return V6PrivatePackageAccessContext(
        actor_id=auth_context.actor_id,
        is_authenticated=auth_context.is_authenticated,
        roles=auth_context.roles,
        authorized_run_ids=auth_context.authorized_run_ids,
        request_id=auth_context.request_id,
    )
