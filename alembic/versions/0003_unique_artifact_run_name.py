"""Prevent duplicate artifact records per run and name.

Revision ID: 0003_unique_artifact_run_name
Revises: 0002_run_disk_usage_and_deletion_audit
Create Date: 2026-07-16
"""

from __future__ import annotations

from alembic import op

revision = "0003_unique_artifact_run_name"
down_revision = "0002_run_disk_usage_and_deletion_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM artifacts
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM artifacts
            GROUP BY run_id, name
        )
        """
    )
    op.create_index(
        "uq_artifacts_run_id_name",
        "artifacts",
        ["run_id", "name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_artifacts_run_id_name", table_name="artifacts")
