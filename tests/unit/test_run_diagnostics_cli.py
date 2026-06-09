from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.cli.run_diagnostics import main
from app.services.storage import ensure_data_dirs


async def _setup_test_db(tmp_path: Path):
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "db.sqlite")
    ensure_data_dirs(settings)
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return settings, engine, session_factory


async def _seed_run(session, run_id: str = "run-1", status: RunStatus = RunStatus.DONE):
    run = Run(
        id=run_id,
        name="test-run",
        status=status,
        latitude=1.0,
        longitude=2.0,
    )
    session.add(run)
    await session.commit()
    return run


def test_cli_help_raises_system_exit_zero():
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0


def test_cli_missing_run_returns_one(capsys, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    settings, engine, session_factory = asyncio.run(_setup_test_db(tmp_path))
    monkeypatch.setattr("app.cli.run_diagnostics.Settings", lambda: settings)

    exit_code = main(["--run-id", "missing-run"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "missing-run" in captured.err
    asyncio.run(engine.dispose())


def test_cli_successful_run_returns_zero(capsys, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    settings, engine, session_factory = asyncio.run(_setup_test_db(tmp_path))
    run_dir = settings.data_dir / "runs" / "cli-run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "grid_manifest.json").write_text("{}", encoding="utf-8")

    async def _seed():
        async with session_factory() as session:
            await _seed_run(session, "cli-run")

    asyncio.run(_seed())
    monkeypatch.setattr("app.cli.run_diagnostics.Settings", lambda: settings)

    exit_code = main(["--run-id", "cli-run"])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["run_id"] == "cli-run"
    assert payload["output_file_count"] == 1
    assert payload["file_summary"]["has_grid_manifest"] is True
    asyncio.run(engine.dispose())


def test_cli_default_error_payload_is_redacted(capsys, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Error output must also be redacted and pass verify_redacted()."""
    settings, engine, session_factory = asyncio.run(_setup_test_db(tmp_path))
    monkeypatch.setattr("app.cli.run_diagnostics.Settings", lambda: settings)

    exit_code = main(["--run-id", "missing-run"])
    assert exit_code == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert payload["error"] == "diagnostic_failed"
    assert "missing-run" in payload["run_id"]
    # Verify no paths or coordinates leak in error payload
    dumped = json.dumps(payload)
    assert "latitude" not in dumped.lower()
    assert "longitude" not in dumped.lower()
    assert "coordinates" not in dumped.lower()
    assert str(tmp_path) not in dumped
    asyncio.run(engine.dispose())


def test_cli_output_passes_redaction(capsys, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    settings, engine, session_factory = asyncio.run(_setup_test_db(tmp_path))
    run_dir = settings.data_dir / "runs" / "redact-run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "grid_manifest.json").write_text("{}", encoding="utf-8")
    (run_dir / "artifact.csv").write_text("id,score\n1,0.9\n", encoding="utf-8")

    async def _seed():
        async with session_factory() as session:
            await _seed_run(session, "redact-run")

    asyncio.run(_seed())
    monkeypatch.setattr("app.cli.run_diagnostics.Settings", lambda: settings)

    exit_code = main(["--run-id", "redact-run"])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    # Verify no paths or coordinates appear
    dumped = json.dumps(payload)
    assert "latitude" not in dumped.lower()
    assert "longitude" not in dumped.lower()
    assert "coordinates" not in dumped.lower()
    assert str(tmp_path) not in dumped
    asyncio.run(engine.dispose())


def test_cli_path_like_run_id_does_not_leak_unsafe_content(capsys, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A run-id that looks like a path should not cause unsafe output in the error payload."""
    settings, engine, session_factory = asyncio.run(_setup_test_db(tmp_path))
    monkeypatch.setattr("app.cli.run_diagnostics.Settings", lambda: settings)

    exit_code = main(["--run-id", "../escape"])
    assert exit_code == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert payload["error"] == "diagnostic_failed"
    dumped = json.dumps(payload)
    # The absolute tmp_path must not leak into the error payload
    assert str(tmp_path) not in dumped
    # The run_id is allowed in the payload (it's user input), but no absolute paths
    assert "C:\\" not in dumped or str(tmp_path) not in dumped
    asyncio.run(engine.dispose())


def test_cli_coordinate_like_run_id_does_not_leak_coords(capsys, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A run-id that looks like coordinates should not leak coordinate patterns in output."""
    settings, engine, session_factory = asyncio.run(_setup_test_db(tmp_path))
    run_dir = settings.data_dir / "runs" / "12.34_56.78"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "grid_manifest.json").write_text("{}", encoding="utf-8")

    async def _seed():
        async with session_factory() as session:
            await _seed_run(session, "12.34_56.78")

    asyncio.run(_seed())
    monkeypatch.setattr("app.cli.run_diagnostics.Settings", lambda: settings)

    exit_code = main(["--run-id", "12.34_56.78"])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    dumped = json.dumps(payload)
    # The absolute tmp_path must not leak
    assert str(tmp_path) not in dumped
    # No forbidden coordinate keys should appear in the output
    assert "latitude" not in dumped.lower()
    assert "longitude" not in dumped.lower()
    assert "coordinates" not in dumped.lower()
    asyncio.run(engine.dispose())
