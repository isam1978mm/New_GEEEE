from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import Run
from app.deps import get_db_session, get_settings_from_request
from app.errors import AppError
from app.services.nb_results import build_nb_results
from app.services.storage import get_run_dir

router = APIRouter(tags=["nb-results"])


class NbRunNotFoundError(AppError):
    status_code = 404
    public_code = "run_not_found"
    public_message = "Run is unavailable."


@router.get("/runs/{run_id}/nb-results", response_model=None)
async def get_nb_results(
    run_id: str,
    settings: Settings = Depends(get_settings_from_request),
    session: AsyncSession = Depends(get_db_session),
):
    run_exists = await session.scalar(select(Run.id).where(Run.id == run_id))
    if run_exists is None:
        raise NbRunNotFoundError()
    return build_nb_results(get_run_dir(settings, run_id))
