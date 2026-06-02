from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RunDeletionAudit(Base):
    __tablename__ = "run_deletion_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    run_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_files_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deleted_dirs_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    freed_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="deleted")
    message: Mapped[str] = mapped_column(String(255), nullable=False, default="Run deleted.")
