from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.config import Settings
from app.deps import get_db_session, get_settings_from_request
from app.services.artifact_response import serve_artifact_response

router = APIRouter()


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
