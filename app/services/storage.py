from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.errors import ArtifactServeViolation


def ensure_data_dirs(settings: Settings) -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    get_runs_dir(settings).mkdir(parents=True, exist_ok=True)


def get_runs_dir(settings: Settings) -> Path:
    return settings.data_dir / "runs"


def get_run_dir(settings: Settings, run_id: str) -> Path:
    return get_runs_dir(settings) / run_id


def resolve_run_artifact_path(settings: Settings, run_id: str, relative_path: str) -> Path:
    run_dir = get_run_dir(settings, run_id).resolve()
    candidate = (run_dir / relative_path).resolve()
    if run_dir not in (candidate, *candidate.parents):
        raise ArtifactServeViolation()
    return candidate
