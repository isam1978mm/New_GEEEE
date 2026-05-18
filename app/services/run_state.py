from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.run import Run
from app.db.models.enums import RunStatus
from app.errors import ActiveRunConflictError


ACTIVE_RUN_STATUSES = (RunStatus.QUEUED, RunStatus.RUNNING)


async def mark_stale_running_runs(session: AsyncSession) -> int:
    result = await session.execute(select(Run).where(Run.status == RunStatus.RUNNING))
    running_runs = result.scalars().all()
    for run in running_runs:
        run.status = RunStatus.STALE_FAILED
    await session.commit()
    return len(running_runs)


async def ensure_single_active_run(session: AsyncSession) -> None:
    result = await session.execute(select(Run.id).where(Run.status.in_(ACTIVE_RUN_STATUSES)).limit(1))
    active_run_id = result.scalar_one_or_none()
    if active_run_id is not None:
        raise ActiveRunConflictError()
