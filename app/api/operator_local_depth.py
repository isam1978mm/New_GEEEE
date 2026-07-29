from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.config import Settings
from app.deps import get_settings_from_request
from app.services.operator_auth_context import resolve_operator_auth_context
from app.services.operator_local_depth_app import (
    OperatorLocalDepthAppError,
    build_denied_operator_local_depth_result,
    evaluate_operator_local_depth_access,
    run_operator_local_depth_app,
)

router = APIRouter(tags=["operator-local-depth"])


class OperatorLocalDepthRequest(BaseModel):
    geojson: dict[str, Any]
    site_id: str = Field(min_length=1, max_length=120)
    calibration_dataset_version: str = Field(min_length=1, max_length=120)
    method_version: str = Field(
        default="operator_local_depth_app_v1",
        min_length=1,
        max_length=120,
    )
    input_crs: str = Field(default="EPSG:4326", min_length=1, max_length=80)
    erosion_pixels: int = Field(default=2, ge=0, le=10)
    minimum_valid_pixels: int = Field(default=20, ge=1, le=100000)
    allow_run_quality_warning: bool = False
    force: bool = False
    operator_confirmed_review: bool = False


@router.post("/runs/{run_id}/operator/local-depth")
async def run_operator_local_depth(
    run_id: str,
    payload: OperatorLocalDepthRequest,
    settings: Settings = Depends(get_settings_from_request),
    x_operator_authenticated: str | None = Header(default=None),
    x_operator_id: str | None = Header(default=None),
    x_operator_roles: str | None = Header(default=None),
    x_operator_authorized_runs: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    """Run private operator-calibrated local depth for a completed run.

    Uploaded GeoJSON is accepted as JSON rather than streamed as a file. Denied
    requests are rejected before any run file is read or written. Successful
    responses contain no geometry, coordinates, local paths, or download URLs.
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
    decision = evaluate_operator_local_depth_access(
        settings=settings,
        run_id=run_id,
        actor_id=auth_context.actor_id,
        is_authenticated=auth_context.is_authenticated,
        roles=auth_context.roles,
    )
    if not decision.allowed:
        denied = build_denied_operator_local_depth_result(
            request_id=auth_context.request_id,
            reason=decision.reason,
        )
        return JSONResponse(status_code=denied.status_code, content=denied.body)

    try:
        result = await run_in_threadpool(
            run_operator_local_depth_app,
            settings=settings,
            run_id=run_id,
            geojson=payload.geojson,
            site_id=payload.site_id,
            calibration_dataset_version=payload.calibration_dataset_version,
            method_version=payload.method_version,
            input_crs=payload.input_crs,
            erosion_pixels=payload.erosion_pixels,
            minimum_valid_pixels=payload.minimum_valid_pixels,
            allow_run_quality_warning=payload.allow_run_quality_warning,
            force=payload.force,
            operator_confirmed_review=payload.operator_confirmed_review,
        )
    except (OperatorLocalDepthAppError, FileExistsError, FileNotFoundError, ValueError) as exc:
        return JSONResponse(
            status_code=422,
            content={
                "outcome": "error",
                "status": "local_depth_request_rejected",
                "message": _safe_operator_message(exc),
                "geometry_returned": False,
                "filesystem_only": True,
            },
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "outcome": "error",
                "status": "local_depth_processing_failed",
                "message": "Local depth processing could not be completed.",
                "geometry_returned": False,
                "filesystem_only": True,
            },
        )

    return JSONResponse(status_code=200, content=result)


def _safe_operator_message(exc: Exception) -> str:
    message = str(exc).strip()
    if not message or "/" in message or "\\" in message:
        return "The reviewed local-depth request could not be processed."
    return message[:300]


__all__ = ("OperatorLocalDepthRequest", "router")
