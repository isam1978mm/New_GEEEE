from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import Artifact, Run
from app.errors import ArtifactServeViolation
from app.services.redaction import redact, verify_redacted
from app.services.run_history import read_run_history_events
from app.services.storage import get_run_dir, resolve_run_artifact_path


class RunFileSummary(BaseModel):
    total_files: int
    total_bytes: int
    by_extension: dict[str, int]
    manifest_files: list[str]
    missing_artifacts: list[str]
    extra_files: list[str]
    stage_history_events: int
    has_grid_manifest: bool
    has_run_status_history: bool


class RunDiagnosticResult(BaseModel):
    run_id: str
    run_status: str
    run_name: str | None
    disk_usage_bytes: int
    output_file_count: int
    file_summary: RunFileSummary
    warnings: list[str]
    scanned_at: str


async def inspect_run(
    *,
    settings: Settings,
    session: AsyncSession,
    run_id: str,
    redacted: bool = True,
) -> RunDiagnosticResult:
    """Inspect a run directory and return a safe diagnostic summary.

    Parameters
    ----------
    settings:
        Application settings.
    session:
        Active database session.
    run_id:
        Run identifier to inspect.
    redacted:
        If True (default), the returned result is passed through the redaction
        verifier to guarantee no paths, coordinates, or hashes leak.

    Returns
    -------
    RunDiagnosticResult
    """
    run_dir = get_run_dir(settings, run_id)
    runs_dir = settings.data_dir / "runs"
    resolved_run_dir = run_dir.resolve()
    resolved_runs_dir = runs_dir.resolve()

    if resolved_runs_dir not in (resolved_run_dir, *resolved_run_dir.parents):
        raise ArtifactServeViolation()

    run = await session.scalar(select(Run).where(Run.id == run_id))
    if run is None:
        raise ValueError(f"Run not found: {run_id}")

    artifacts = await session.scalars(select(Artifact).where(Artifact.run_id == run_id))
    artifact_list = list(artifacts)
    tracked_relative_paths: set[str] = set()
    missing_artifacts: list[str] = []

    for artifact in artifact_list:
        try:
            artifact_path = resolve_run_artifact_path(settings, run_id, artifact.relative_path)
            if artifact_path.is_file():
                # Store the normalized relative path from the run directory
                rel_path = artifact_path.relative_to(resolved_run_dir).as_posix()
                tracked_relative_paths.add(rel_path)
            else:
                missing_artifacts.append(artifact.name)
        except Exception:
            missing_artifacts.append(artifact.name)

    total_files = 0
    total_bytes = 0
    by_extension: dict[str, int] = defaultdict(int)
    manifest_files: list[str] = []
    extra_files: list[str] = []
    has_grid_manifest = False
    has_run_status_history = False

    if run_dir.is_dir():
        for path in run_dir.rglob("*"):
            if not path.is_file():
                continue
            # Skip symlinks
            if path.is_symlink():
                continue
            # Skip hidden files
            if path.name.startswith("."):
                continue
            # Skip files inside hidden directories
            try:
                rel_parts = path.relative_to(resolved_run_dir).parts
            except ValueError:
                continue
            if any(part.startswith(".") for part in rel_parts):
                continue
            # Validate the resolved path is still under the run directory
            resolved_path = path.resolve()
            if resolved_run_dir not in (resolved_path, *resolved_path.parents):
                continue

            total_files += 1
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            total_bytes += size

            ext = path.suffix.lower() if path.suffix else "(no ext)"
            by_extension[ext] += 1

            file_rel_path = path.relative_to(resolved_run_dir).as_posix()
            if file_rel_path.endswith(".manifest.json") or file_rel_path == "grid_manifest.json":
                manifest_files.append(file_rel_path)

            if file_rel_path == "grid_manifest.json":
                has_grid_manifest = True
            if file_rel_path == "run_status_history.json":
                has_run_status_history = True

            # Detect extra files using relative paths, not basenames
            if file_rel_path not in tracked_relative_paths and file_rel_path not in {
                "grid_manifest.json",
                "run_status_history.json",
            }:
                extra_files.append(file_rel_path)

    history_events = read_run_history_events(settings, run_id)
    stage_history_events = len(history_events)

    warnings: list[str] = []
    if missing_artifacts:
        warnings.append(f"Missing artifacts on disk: {len(missing_artifacts)}")
    if extra_files:
        warnings.append(f"Extra files not tracked in DB: {len(extra_files)}")
    if not has_grid_manifest:
        warnings.append("Grid manifest is missing.")
    if not has_run_status_history:
        warnings.append("Run status history is missing.")

    result = RunDiagnosticResult(
        run_id=run_id,
        run_status=run.status.value,
        run_name=run.name,
        disk_usage_bytes=total_bytes,
        output_file_count=total_files,
        file_summary=RunFileSummary(
            total_files=total_files,
            total_bytes=total_bytes,
            by_extension=dict(by_extension),
            manifest_files=manifest_files,
            missing_artifacts=missing_artifacts,
            extra_files=extra_files,
            stage_history_events=stage_history_events,
            has_grid_manifest=has_grid_manifest,
            has_run_status_history=has_run_status_history,
        ),
        warnings=warnings,
        scanned_at=datetime.now(timezone.utc).isoformat(),
    )

    if redacted:
        raw = result.model_dump()
        redacted_raw = redact(raw)
        verify_redacted(redacted_raw)
        result = RunDiagnosticResult.model_validate(redacted_raw)

    return result
