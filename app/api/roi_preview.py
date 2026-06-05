from __future__ import annotations

from fastapi import APIRouter

from app.pipeline.roi_preview import build_roi_grid_preview
from app.schemas.roi_preview import RoiPreviewPublic, RoiPreviewRequest

router = APIRouter(prefix="/roi", tags=["roi-preview"])


@router.post("/preview", response_model=RoiPreviewPublic)
async def preview_roi_grid(payload: RoiPreviewRequest) -> RoiPreviewPublic:
    return build_roi_grid_preview(latitude=payload.lat, longitude=payload.lon)
