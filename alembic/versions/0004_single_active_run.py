"""Enforce one active run and clear stale pre-upgrade active rows.

Revision ID: 0004_single_active_run
Revises: 0003_unique_artifact_run_name
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op

revision = "0004_single_active_run"
down_revision = "0003_unique_artifact_run_name"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE runs
        SET status = 'STALE_FAILED'
        WHERE status IN ('QUEUED', 'RUNNING')
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_runs_single_active
        ON runs (1)
        WHERE status IN ('QUEUED', 'RUNNING')
        """
    )


def downgrade() -> None:
    op.drop_index("uq_runs_single_active", table_name="runs")
