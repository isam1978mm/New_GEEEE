"""Add run disk usage and deletion audit.

Revision ID: 0002_run_disk_usage_and_deletion_audit
Revises: 0001_runs_and_artifacts
Create Date: 2026-06-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_run_disk_usage_and_deletion_audit"
down_revision = "0001_runs_and_artifacts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("disk_usage_bytes", sa.BigInteger(), nullable=True))
    op.add_column("runs", sa.Column("output_file_count", sa.Integer(), nullable=True))
    op.add_column("runs", sa.Column("last_disk_scan_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "run_deletion_audit",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("run_name", sa.String(length=255), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_files_count", sa.Integer(), nullable=False),
        sa.Column("deleted_dirs_count", sa.Integer(), nullable=False),
        sa.Column("freed_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("message", sa.String(length=255), nullable=False),
    )
    op.create_index("ix_run_deletion_audit_run_id", "run_deletion_audit", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_run_deletion_audit_run_id", table_name="run_deletion_audit")
    op.drop_table("run_deletion_audit")
    op.drop_column("runs", "last_disk_scan_at")
    op.drop_column("runs", "output_file_count")
    op.drop_column("runs", "disk_usage_bytes")
