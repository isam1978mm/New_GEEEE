from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.db.models.enums import RunStatus
from app.schemas.artifact import ArtifactPublic

COORDINATE_LIKE_PATTERN = re.compile(r"\b-?\d{1,2}\.\d+\s*,\s*-?\d{1,3}\.\d+\b")
FORBIDDEN_RUN_NAME_TERMS = (
    "latitude",
    "longitude",
    "coords",
    "coordinates",
    "geometry",
    "bounds",
    "bbox",
    "transform",
    "path",
    "hash",
    "checksum",
    "fingerprint",
)


class RunCreate(BaseModel):
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    name: str | None = Field(default=None, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_public_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        lowered = value.casefold()
        if COORDINATE_LIKE_PATTERN.search(value):
            raise ValueError("Run name contains coordinate-like content.")
        if any(term in lowered for term in FORBIDDEN_RUN_NAME_TERMS):
            raise ValueError("Run name contains forbidden public text.")
        return value


class RunPublic(BaseModel):
    id: str
    name: str | None
    status: RunStatus
    created_at: datetime


class RunStageProgressPublic(BaseModel):
    name: str
    label: str
    status: str


class RunDetailPublic(RunPublic):
    current_stage: str | None = None
    stages: list[RunStageProgressPublic] = Field(default_factory=list)
    artifacts: list[ArtifactPublic] = Field(default_factory=list)
