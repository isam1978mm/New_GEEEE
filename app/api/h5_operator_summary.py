from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from app.config import Settings
from app.deps import get_settings_from_request
from app.pipeline.parity.operator_overlay_access_foundation import OPERATOR_ROLE
from app.services.h5_operator_summary import (
    H5OperatorSummaryError,
    assert_h5_operator_summary_is_redacted,
    load_h5_operator_aggregate_summary,
)
from app.services.operator_auth_context import resolve_operator_auth_context


router = APIRouter(tags=["h5-operator-summary"])


@router.get("/operator/h5/aggregate-summary", response_model=None)
async def get_h5_operator_aggregate_summary(
    settings: Settings = Depends(get_settings_from_request),
    x_operator_authenticated: str | None = Header(default=None),
    x_operator_id: str | None = Header(default=None),
    x_operator_roles: str | None = Header(default=None),
    x_operator_authorized_runs: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> JSONResponse:
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

    if not auth_context.is_authenticated or OPERATOR_ROLE not in set(auth_context.roles):
        return JSONResponse(
            status_code=403,
            content={
                "outcome": "denied",
                "status": "access_denied",
                "reason_code": "ACCESS_DENIED",
                "request_id": auth_context.request_id,
                "message": "Access to the requested resource is not available.",
            },
        )

    try:
        summary = load_h5_operator_aggregate_summary()
    except FileNotFoundError:
        summary = {
            "status": "not_available",
            "pipeline_stage": "h5_operator_aggregate_summary",
            "total_row_count": 0,
            "row_level_output_included": False,
            "private_paths_included": False,
        }
    except H5OperatorSummaryError:
        return JSONResponse(
            status_code=500,
            content={
                "outcome": "error",
                "status": "summary_unavailable",
                "reason_code": "SUMMARY_UNAVAILABLE",
                "request_id": auth_context.request_id,
                "message": "The aggregate summary is not available.",
            },
        )

    body = {
        "outcome": "allowed",
        "access_mode": "operator_only_aggregate",
        "summary": summary,
        "http_servable": False,
        "downloadable_via_api": False,
        "row_level_output_included": False,
        "api_frontend_changed": False,
        "overlays_created": False,
    }
    assert_h5_operator_summary_is_redacted(body)
    return JSONResponse(status_code=200, content=body)
