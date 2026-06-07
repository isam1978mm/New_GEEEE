from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.pipeline.parity.operator_overlay_implementation_design import ALLOWED_ACCESS_MODE

ALLOWED_PREVIEW_ACCESS_MODE = ALLOWED_ACCESS_MODE


class OperatorPrivateOverlayPreviewSuccess(BaseModel):
    """Operator-only private overlay preview success DTO.

    The preview payload is coordinate-free (counts, neutral kinds, scalar weight
    summary). It carries no local filesystem path, private hash, public download
    URL, or artifact-serving URL.
    """

    outcome: str = Field(description="allowed or not_available for an authorized operator")
    run_id: str
    artifact_family: str
    access_mode: str
    preview_type: str
    item_count: int | None = None
    preview_payload: dict[str, Any] | None = None
    audit_event_summary: dict[str, Any]
    filesystem_only: bool = True
    http_servable: bool = False
    downloadable_via_api: bool = False
    frontend_visible: str = "operator_only"


class OperatorPrivateOverlayDenial(BaseModel):
    """Generic redacted denial DTO.

    Identical for every denial cause so it cannot reveal whether a run or private
    artifact exists.
    """

    outcome: str = "denied"
    status: str
    reason_code: str
    request_id: str
    message: str
    retry_allowed: bool = False
    support_reference: str
