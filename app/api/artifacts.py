from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.config import Settings
from app.db.models import Run
from app.deps import get_db_session, get_settings_from_request
from app.errors import AppError
from app.schemas.operator_output import OperatorOutputTreePublic
from app.services.artifact_response import serve_artifact_response, serve_operator_output_response
from app.services.operator_outputs import build_operator_output_tree

router = APIRouter()


class RunNotFoundError(AppError):
    status_code = 404
    public_code = "run_not_found"
    public_message = "Run is unavailable."


@router.get("/runs/{run_id}/artifacts/{artifact_name}")
async def get_artifact(
    run_id: str,
    artifact_name: str,
    settings: Settings = Depends(get_settings_from_request),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    return await serve_artifact_response(
        run_id=run_id,
        artifact_name=artifact_name,
        settings=settings,
        session=session,
    )


@router.get("/runs/{run_id}/artifacts/{artifact_name}/download/{download_filename}")
async def download_artifact(
    run_id: str,
    artifact_name: str,
    download_filename: str,
    settings: Settings = Depends(get_settings_from_request),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    return await serve_artifact_response(
        run_id=run_id,
        artifact_name=artifact_name,
        download_filename=download_filename,
        settings=settings,
        session=session,
    )


@router.get("/runs/{run_id}/outputs", response_model=OperatorOutputTreePublic)
async def get_operator_output_tree(
    run_id: str,
    settings: Settings = Depends(get_settings_from_request),
    session: AsyncSession = Depends(get_db_session),
) -> OperatorOutputTreePublic:
    await _ensure_run_exists(session, run_id)
    return build_operator_output_tree(settings=settings, run_id=run_id)


@router.get("/runs/{run_id}/outputs/download/{relative_path:path}")
async def download_operator_output(
    run_id: str,
    relative_path: str,
    settings: Settings = Depends(get_settings_from_request),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    await _ensure_run_exists(session, run_id)
    return await serve_operator_output_response(
        run_id=run_id,
        relative_path=relative_path,
        settings=settings,
    )


async def _ensure_run_exists(session: AsyncSession, run_id: str) -> None:
    run = await session.scalar(select(Run.id).where(Run.id == run_id))
    if run is None:
        raise RunNotFoundError()
