"""Create runs and artifacts tables.

Revision ID: 0001_runs_and_artifacts
Revises:
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_runs_and_artifacts"
down_revision = None
branch_labels = None
depends_on = None

run_status = sa.Enum("queued", "running", "failed", "done", "stale_failed", name="runstatus")
artifact_class = sa.Enum(
    "LOCAL_SENSITIVE",
    "REDACTED_PUBLIC",
    "PREVIEW_ONLY",
    "FILESYSTEM_ONLY",
    name="artifactclass",
)


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("status", run_status, nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "artifacts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("relative_path", sa.String(length=1024), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("artifact_class", artifact_class, nullable=False),
        sa.Column("http_servable", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("artifacts")
    op.drop_table("runs")
    artifact_class.drop(op.get_bind(), checkfirst=False)
    run_status.drop(op.get_bind(), checkfirst=False)
