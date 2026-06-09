from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.base import Base
from app.db.models import Artifact, ArtifactClass, Run, RunStatus
from app.errors import ArtifactServeViolation
from app.services.redaction import verify_redacted
from app.services.run_file_inspector import inspect_run
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


async def _seed_artifact(session, run_id: str, name: str, relative_path: str, artifact_class: ArtifactClass):
    artifact = Artifact(
        run_id=run_id,
        name=name,
        relative_path=relative_path,
        size_bytes=0,
        artifact_class=artifact_class,
        http_servable=False,
    )
    session.add(artifact)
    await session.commit()
    return artifact


def test_models_exist_for_inspector():
    assert Run.__tablename__ == "runs"
    assert Artifact.__tablename__ == "artifacts"


@pytest.mark.asyncio
async def test_inspector_returns_empty_for_missing_run_dir(tmp_path: Path):
    settings, engine, session_factory = await _setup_test_db(tmp_path)
    async with session_factory() as session:
        await _seed_run(session, "run-empty")
        result = await inspect_run(
            settings=settings,
            session=session,
            run_id="run-empty",
            redacted=True,
        )
    assert result.run_id == "run-empty"
    assert result.output_file_count == 0
    assert result.disk_usage_bytes == 0
    assert result.file_summary.has_grid_manifest is False
    assert result.file_summary.has_run_status_history is False
    assert "Grid manifest is missing." in result.warnings
    assert "Run status history is missing." in result.warnings
    verify_redacted(result.model_dump())
    await engine.dispose()


@pytest.mark.asyncio
async def test_inspector_counts_files_and_bytes(tmp_path: Path):
    settings, engine, session_factory = await _setup_test_db(tmp_path)
    async with session_factory() as session:
        await _seed_run(session, "run-files")
    run_dir = settings.data_dir / "runs" / "run-files"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "grid_manifest.json").write_text("{}", encoding="utf-8")
    (run_dir / "stage_dem.manifest.json").write_text("{}", encoding="utf-8")
    (run_dir / "artifact.tif").write_text("tif data", encoding="utf-8")

    async with session_factory() as session:
        result = await inspect_run(
            settings=settings,
            session=session,
            run_id="run-files",
            redacted=True,
        )
    assert result.output_file_count == 3
    assert result.disk_usage_bytes == len("{}") * 2 + len("tif data")
    assert result.file_summary.has_grid_manifest is True
    assert result.file_summary.has_run_status_history is False
    assert result.file_summary.by_extension.get(".json") == 2
    assert result.file_summary.by_extension.get(".tif") == 1
    verify_redacted(result.model_dump())
    await engine.dispose()


@pytest.mark.asyncio
async def test_inspector_detects_missing_and_extra_files(tmp_path: Path):
    settings, engine, session_factory = await _setup_test_db(tmp_path)
    async with session_factory() as session:
        await _seed_run(session, "run-mismatch")
        await _seed_artifact(session, "run-mismatch", "artifact_a", "a.txt", ArtifactClass.LOCAL_SENSITIVE)
        await _seed_artifact(session, "run-mismatch", "artifact_b", "b.txt", ArtifactClass.LOCAL_SENSITIVE)

    run_dir = settings.data_dir / "runs" / "run-mismatch"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "a.txt").write_text("a", encoding="utf-8")
    (run_dir / "extra.txt").write_text("extra", encoding="utf-8")

    async with session_factory() as session:
        result = await inspect_run(
            settings=settings,
            session=session,
            run_id="run-mismatch",
            redacted=True,
        )
    assert "artifact_b" in result.file_summary.missing_artifacts
    assert "extra.txt" in result.file_summary.extra_files
    assert "Missing artifacts on disk: 1" in result.warnings
    assert "Extra files not tracked in DB: 1" in result.warnings
    verify_redacted(result.model_dump())
    await engine.dispose()


@pytest.mark.asyncio
async def test_inspector_detects_nested_same_basename_as_extra(tmp_path: Path):
    """Tracked: outputs/a.txt. Untracked: debug/a.txt. debug/a.txt must be detected as extra."""
    settings, engine, session_factory = await _setup_test_db(tmp_path)
    async with session_factory() as session:
        await _seed_run(session, "run-nested")
        await _seed_artifact(session, "run-nested", "artifact_a", "outputs/a.txt", ArtifactClass.LOCAL_SENSITIVE)

    run_dir = settings.data_dir / "runs" / "run-nested"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
    (run_dir / "debug").mkdir(parents=True, exist_ok=True)
    (run_dir / "outputs" / "a.txt").write_text("tracked", encoding="utf-8")
    (run_dir / "debug" / "a.txt").write_text("untracked", encoding="utf-8")

    async with session_factory() as session:
        result = await inspect_run(
            settings=settings,
            session=session,
            run_id="run-nested",
            redacted=True,
        )
    assert "debug/a.txt" in result.file_summary.extra_files
    assert "outputs/a.txt" not in result.file_summary.extra_files
    assert result.file_summary.total_files == 2
    verify_redacted(result.model_dump())
    await engine.dispose()


@pytest.mark.asyncio
async def test_inspector_blocks_path_traversal(tmp_path: Path):
    settings, engine, session_factory = await _setup_test_db(tmp_path)
    async with session_factory() as session:
        await _seed_run(session, "run-traversal")
    bad_run_id = "../outside"
    async with session_factory() as session:
        with pytest.raises((ArtifactServeViolation, ValueError)):
            await inspect_run(
                settings=settings,
                session=session,
                run_id=bad_run_id,
                redacted=True,
            )
    await engine.dispose()


@pytest.mark.asyncio
async def test_inspector_blocks_artifact_relative_path_traversal(tmp_path: Path):
    """An artifact with a traversal relative path should not crash the inspector."""
    settings, engine, session_factory = await _setup_test_db(tmp_path)
    async with session_factory() as session:
        await _seed_run(session, "run-art-traversal")
        await _seed_artifact(session, "run-art-traversal", "bad", "../escape.txt", ArtifactClass.LOCAL_SENSITIVE)

    run_dir = settings.data_dir / "runs" / "run-art-traversal"
    run_dir.mkdir(parents=True, exist_ok=True)

    async with session_factory() as session:
        result = await inspect_run(
            settings=settings,
            session=session,
            run_id="run-art-traversal",
            redacted=True,
        )
    assert "bad" in result.file_summary.missing_artifacts
    verify_redacted(result.model_dump())
    await engine.dispose()


@pytest.mark.asyncio
async def test_inspector_skips_symlinks_and_hidden_files(tmp_path: Path):
    settings, engine, session_factory = await _setup_test_db(tmp_path)
    async with session_factory() as session:
        await _seed_run(session, "run-skip")
    run_dir = settings.data_dir / "runs" / "run-skip"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "visible.txt").write_text("visible", encoding="utf-8")
    (run_dir / ".hidden.txt").write_text("hidden", encoding="utf-8")
    try:
        (run_dir / "link.txt").symlink_to(run_dir / "visible.txt")
    except OSError:
        pass

    async with session_factory() as session:
        result = await inspect_run(
            settings=settings,
            session=session,
            run_id="run-skip",
            redacted=True,
        )
    assert result.output_file_count == 1
    assert "visible.txt" in result.file_summary.extra_files
    assert ".hidden.txt" not in result.file_summary.extra_files
    verify_redacted(result.model_dump())
    await engine.dispose()


@pytest.mark.asyncio
async def test_inspector_skips_hidden_directories(tmp_path: Path):
    """Files inside hidden directories must not be counted."""
    settings, engine, session_factory = await _setup_test_db(tmp_path)
    async with session_factory() as session:
        await _seed_run(session, "run-hidden-dir")
    run_dir = settings.data_dir / "runs" / "run-hidden-dir"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "visible.txt").write_text("visible", encoding="utf-8")
    hidden_dir = run_dir / ".hidden_dir"
    hidden_dir.mkdir(parents=True, exist_ok=True)
    (hidden_dir / "secret.txt").write_text("secret", encoding="utf-8")

    async with session_factory() as session:
        result = await inspect_run(
            settings=settings,
            session=session,
            run_id="run-hidden-dir",
            redacted=True,
        )
    assert result.output_file_count == 1
    assert "visible.txt" in result.file_summary.extra_files
    assert "secret.txt" not in result.file_summary.extra_files
    assert ".hidden_dir/secret.txt" not in result.file_summary.extra_files
    verify_redacted(result.model_dump())
    await engine.dispose()


@pytest.mark.asyncio
async def test_inspector_no_redacted_mode_returns_same_shape(tmp_path: Path):
    settings, engine, session_factory = await _setup_test_db(tmp_path)
    async with session_factory() as session:
        await _seed_run(session, "run-noredact")
    run_dir = settings.data_dir / "runs" / "run-noredact"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "grid_manifest.json").write_text("{}", encoding="utf-8")

    async with session_factory() as session:
        result = await inspect_run(
            settings=settings,
            session=session,
            run_id="run-noredact",
            redacted=False,
        )
    assert result.output_file_count == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_inspector_detects_run_status_history(tmp_path: Path):
    settings, engine, session_factory = await _setup_test_db(tmp_path)
    async with session_factory() as session:
        await _seed_run(session, "run-history")
    run_dir = settings.data_dir / "runs" / "run-history"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_status_history.json").write_text(
        json.dumps({"events": []}, indent=2),
        encoding="utf-8",
    )

    async with session_factory() as session:
        result = await inspect_run(
            settings=settings,
            session=session,
            run_id="run-history",
            redacted=True,
        )
    assert result.file_summary.has_run_status_history is True
    assert result.file_summary.stage_history_events == 0
    assert "Run status history is missing." not in result.warnings
    verify_redacted(result.model_dump())
    await engine.dispose()
