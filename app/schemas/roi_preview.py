from __future__ import annotations

from pydantic import BaseModel, Field

from app.pipeline.roi_preview import RoiGridPreview


class RoiPreviewRequest(BaseModel):
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)


RoiPreviewPublic = RoiGridPreview
