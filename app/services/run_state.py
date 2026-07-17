from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.run import Run
from app.db.models.enums import RunStatus
from app.errors import ActiveRunConflictError


ACTIVE_RUN_STATUSES = (RunStatus.QUEUED, RunStatus.RUNNING)
SINGLE_ACTIVE_RUN_INDEX_NAME = "uq_runs_single_active"


async def mark_stale_active_runs(session: AsyncSession) -> int:
    return await _mark_stale_runs(session, ACTIVE_RUN_STATUSES)


async def mark_stale_running_runs(session: AsyncSession) -> int:
    return await _mark_stale_runs(session, (RunStatus.RUNNING,))


async def _mark_stale_runs(
    session: AsyncSession,
    statuses: tuple[RunStatus, ...],
) -> int:
    try:
        result = await session.execute(
            select(Run).where(Run.status.in_(statuses))
        )
    except OperationalError as exc:
        if _is_missing_runs_table_error(exc):
            await session.rollback()
            return 0
        raise

    stale_runs = result.scalars().all()
    for run in stale_runs:
        run.status = RunStatus.STALE_FAILED
    await session.commit()
    return len(stale_runs)


async def ensure_single_active_run(session: AsyncSession) -> None:
    result = await session.execute(
        select(Run.id).where(Run.status.in_(ACTIVE_RUN_STATUSES)).limit(1)
    )
    active_run_id = result.scalar_one_or_none()
    if active_run_id is not None:
        raise ActiveRunConflictError()


def is_single_active_run_integrity_error(exc: IntegrityError) -> bool:
    return SINGLE_ACTIVE_RUN_INDEX_NAME in str(exc.orig)


def _is_missing_runs_table_error(exc: OperationalError) -> bool:
    return "no such table: runs" in str(exc.orig).lower()
