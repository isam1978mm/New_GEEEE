from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_creates_runs_artifacts_and_deletion_audit_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "gee_screening.db"
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")

    command.upgrade(cfg, "head")

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    inspector = inspect(engine)
    assert set(inspector.get_table_names()) >= {"runs", "artifacts", "run_deletion_audit"}
    run_columns = {column["name"] for column in inspector.get_columns("runs")}
    assert {"disk_usage_bytes", "output_file_count", "last_disk_scan_at"} <= run_columns
    audit_columns = {column["name"] for column in inspector.get_columns("run_deletion_audit")}
    assert {
        "run_id",
        "run_name",
        "deleted_at",
        "deleted_files_count",
        "deleted_dirs_count",
        "freed_bytes",
        "status",
        "message",
    } <= audit_columns
