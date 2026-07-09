from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.run import Run
from app.db.models.enums import RunStatus
from app.errors import ActiveRunConflictError


ACTIVE_RUN_STATUSES = (RunStatus.QUEUED, RunStatus.RUNNING)


async def mark_stale_running_runs(session: AsyncSession) -> int:
    try:
        result = await session.execute(select(Run).where(Run.status.in_(ACTIVE_RUN_STATUSES)))
    except OperationalError as exc:
        if _is_missing_runs_table_error(exc):
            await session.rollback()
            return 0
        raise

    active_runs = result.scalars().all()
    for run in active_runs:
        run.status = RunStatus.STALE_FAILED
    await session.commit()
    return len(active_runs)


async def ensure_single_active_run(session: AsyncSession) -> None:
    result = await session.execute(select(Run.id).where(Run.status.in_(ACTIVE_RUN_STATUSES)).limit(1))
    active_run_id = result.scalar_one_or_none()
    if active_run_id is not None:
        raise ActiveRunConflictError()


def _is_missing_runs_table_error(exc: OperationalError) -> bool:
    return "no such table: runs" in str(exc.orig).lower()
