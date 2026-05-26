from __future__ import annotations

from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models.artifact import Artifact
from app.errors import ArtifactNotFoundError, ArtifactServeViolation
from app.schemas.artifact import ArtifactInternal
from app.services.artifact_policy import can_serve_artifact
from app.services.storage import resolve_run_artifact_path


ARTIFACT_DOWNLOAD_FILENAMES = {
    "objects_index": "objects_index.csv",
    "clusters_summary": "clusters_summary.csv",
    "alignment_qa": "alignment_qa.json",
    "alignment_audit": "alignment_audit.json",
    "alignment_mask_selection": "alignment_mask_selection.json",
}


def public_download_filename(artifact_name: str) -> str:
    return ARTIFACT_DOWNLOAD_FILENAMES.get(artifact_name, artifact_name)


def is_expected_download_filename(*, artifact_name: str, download_filename: str) -> bool:
    return public_download_filename(artifact_name) == download_filename


async def serve_artifact_response(
    *,
    run_id: str,
    artifact_name: str,
    download_filename: str | None = None,
    settings: Settings,
    session: AsyncSession,
) -> FileResponse:
    result = await session.execute(
        select(Artifact).where(Artifact.run_id == run_id, Artifact.name == artifact_name)
    )
    artifact = result.scalar_one_or_none()
    if artifact is None:
        raise ArtifactNotFoundError()

    internal_artifact = ArtifactInternal.model_validate(
        {
            "run_id": artifact.run_id,
            "name": artifact.name,
            "relative_path": artifact.relative_path,
            "artifact_class": artifact.artifact_class,
            "http_servable": artifact.http_servable,
        }
    )
    decision = can_serve_artifact(internal_artifact, settings)
    if not decision.allow:
        raise ArtifactServeViolation()
    if download_filename is not None and not is_expected_download_filename(
        artifact_name=artifact.name, download_filename=download_filename
    ):
        raise ArtifactServeViolation()

    artifact_path = resolve_run_artifact_path(settings, run_id, artifact.relative_path)
    if not artifact_path.is_file():
        raise ArtifactNotFoundError()

    return FileResponse(path=artifact_path, filename=public_download_filename(artifact.name))
