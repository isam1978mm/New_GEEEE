from __future__ import annotations

from pathlib import Path

from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models.enums import ArtifactClass
from app.db.models.artifact import Artifact
from app.errors import ArtifactNotFoundError, ArtifactServeViolation
from app.schemas.artifact import ArtifactInternal
from app.services.artifact_policy import can_serve_artifact
from app.services.operator_outputs import resolve_operator_output_path
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


def serve_private_file_response(*, file_path: Path, file_name: str, media_type: str) -> FileResponse:
    return FileResponse(path=file_path, filename=file_name, media_type=media_type)


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


async def serve_operator_output_response(
    *,
    run_id: str,
    relative_path: str,
    settings: Settings,
) -> FileResponse:
    artifact_path = resolve_operator_output_path(settings, run_id, relative_path)
    internal_artifact = ArtifactInternal(
        run_id=run_id,
        name=artifact_path.name,
        relative_path=relative_path,
        artifact_class=ArtifactClass.LOCAL_SENSITIVE,
        http_servable=True,
    )
    decision = can_serve_artifact(internal_artifact, settings)
    if not decision.allow:
        raise ArtifactServeViolation()
    return FileResponse(path=artifact_path, filename=artifact_path.name, media_type="application/octet-stream")
