from __future__ import annotations

import json
import os
import shutil
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import Settings
from app.db.models.enums import ArtifactClass
from app.errors import ArtifactServeViolation
from app.services.grid import GridManifest


@dataclass(frozen=True)
class RunDirectoryDeleteSummary:
    deleted_files_count: int
    deleted_dirs_count: int
    freed_bytes: int


def ensure_data_dirs(settings: Settings) -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    get_runs_dir(settings).mkdir(parents=True, exist_ok=True)


def get_runs_dir(settings: Settings) -> Path:
    return settings.data_dir / "runs"


def get_run_dir(settings: Settings, run_id: str) -> Path:
    return get_runs_dir(settings) / run_id


def delete_run_directory(settings: Settings, run_id: str) -> RunDirectoryDeleteSummary:
    runs_dir = get_runs_dir(settings).resolve()
    run_dir = get_run_dir(settings, run_id).resolve()
    if runs_dir not in (run_dir, *run_dir.parents):
        raise ArtifactServeViolation()
    if not run_dir.is_dir():
        return RunDirectoryDeleteSummary(deleted_files_count=0, deleted_dirs_count=0, freed_bytes=0)

    summary = summarize_run_directory(settings, run_id)
    shutil.rmtree(run_dir)
    return summary


def summarize_run_directory(settings: Settings, run_id: str) -> RunDirectoryDeleteSummary:
    runs_dir = get_runs_dir(settings).resolve()
    run_dir = get_run_dir(settings, run_id).resolve()
    if runs_dir not in (run_dir, *run_dir.parents):
        raise ArtifactServeViolation()
    if not run_dir.is_dir():
        return RunDirectoryDeleteSummary(deleted_files_count=0, deleted_dirs_count=0, freed_bytes=0)
    return _summarize_run_directory_for_delete(run_dir)


def get_redacted_cache_dir(settings: Settings, run_id: str) -> Path:
    return get_run_dir(settings, run_id) / "_redacted"


def initialize_run_storage(settings: Settings, run_id: str) -> Path:
    run_dir = get_run_dir(settings, run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    get_redacted_cache_dir(settings, run_id).mkdir(parents=True, exist_ok=True)
    return run_dir


def write_grid_manifest(settings: Settings, run_id: str, grid_manifest: GridManifest) -> Path:
    return _write_manifest_file(
        settings=settings,
        run_id=run_id,
        filename="grid_manifest.json",
        payload=grid_manifest.model_dump(),
    )


def write_stage_manifest(
    settings: Settings,
    run_id: str,
    stage_name: str,
    payload: dict[str, Any],
) -> Path:
    manifest_payload = {
        **payload,
        "artifact_class": ArtifactClass.LOCAL_SENSITIVE.value,
        "stage_name": stage_name,
    }
    return _write_manifest_file(
        settings=settings,
        run_id=run_id,
        filename=f"stage_{stage_name}.manifest.json",
        payload=manifest_payload,
    )


def read_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_atomic(
    path: Path,
    payload: dict[str, Any],
    *,
    indent: int | None = 2,
    sort_keys: bool = True,
    newline: bool = False,
) -> Path:
    text = json.dumps(payload, indent=indent, sort_keys=sort_keys)
    if newline:
        text += "\n"
    return write_text_atomic(path, text, encoding="utf-8")


def write_text_atomic(path: Path, text: str, *, encoding: str = "utf-8") -> Path:
    return write_bytes_atomic(path, text.encode(encoding))


def write_bytes_atomic(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise
    return path


def resolve_run_artifact_path(settings: Settings, run_id: str, relative_path: str) -> Path:
    if not relative_path:
        raise ArtifactServeViolation()
    if relative_path.startswith(("/", "\\")):
        raise ArtifactServeViolation()
    if re.match(r"^[A-Za-z]:[\\/]", relative_path):
        raise ArtifactServeViolation()

    raw_segments = re.split(r"[\\/]", relative_path)
    if any(segment in {"", ".", ".."} for segment in raw_segments):
        raise ArtifactServeViolation()

    run_dir = get_run_dir(settings, run_id).resolve()
    candidate = (run_dir / relative_path).resolve()
    if run_dir not in (candidate, *candidate.parents):
        raise ArtifactServeViolation()
    return candidate


def _summarize_run_directory_for_delete(run_dir: Path) -> RunDirectoryDeleteSummary:
    deleted_files_count = 0
    deleted_dirs_count = 0
    freed_bytes = 0
    for path in run_dir.rglob("*"):
        try:
            stat_result = path.lstat()
        except OSError:
            continue
        if path.is_dir() and not path.is_symlink():
            deleted_dirs_count += 1
            continue
        deleted_files_count += 1
        freed_bytes += stat_result.st_size
    return RunDirectoryDeleteSummary(
        deleted_files_count=deleted_files_count,
        deleted_dirs_count=deleted_dirs_count,
        freed_bytes=freed_bytes,
    )


def _write_manifest_file(
    *,
    settings: Settings,
    run_id: str,
    filename: str,
    payload: dict[str, Any],
) -> Path:
    run_dir = initialize_run_storage(settings, run_id)
    manifest_path = run_dir / filename
    write_json_atomic(manifest_path, payload, indent=2, sort_keys=True)
    return manifest_path
