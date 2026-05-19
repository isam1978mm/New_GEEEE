from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.db.models.enums import ArtifactClass


class ArtifactInternal(BaseModel):
    run_id: str
    name: str
    relative_path: str
    artifact_class: ArtifactClass
    http_servable: bool


class ArtifactPublic(BaseModel):
    name: str
    artifact_class: ArtifactClass
    created_at: datetime | None = None
