from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.db.models.enums import ArtifactClass
from app.schemas.artifact import ArtifactInternal


@dataclass(slots=True)
class ArtifactServeDecision:
    allow: bool
    reason: str


def can_serve_artifact(artifact: ArtifactInternal, settings: Settings) -> ArtifactServeDecision:
    if artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY:
        return ArtifactServeDecision(allow=False, reason="class_iv_filesystem_only")
    if artifact.artifact_class == ArtifactClass.LOCAL_SENSITIVE and settings.allow_network_bind:
        return ArtifactServeDecision(allow=False, reason="class_i_blocked_under_network_bind")
    if not artifact.http_servable:
        return ArtifactServeDecision(allow=False, reason="artifact_not_http_servable")
    return ArtifactServeDecision(allow=True, reason="ok")
