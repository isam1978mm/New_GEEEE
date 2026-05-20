from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.config import Settings
from app.db.models.enums import ArtifactClass
from app.errors import ArtifactServeViolation
from app.services.grid import GridManifest


def ensure_data_dirs(settings: Settings) -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    get_runs_dir(settings).mkdir(parents=True, exist_ok=True)


def get_runs_dir(settings: Settings) -> Path:
    return settings.data_dir / "runs"


def get_run_dir(settings: Settings, run_id: str) -> Path:
    return get_runs_dir(settings) / run_id


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


def _write_manifest_file(
    *,
    settings: Settings,
    run_id: str,
    filename: str,
    payload: dict[str, Any],
) -> Path:
    run_dir = initialize_run_storage(settings, run_id)
    manifest_path = run_dir / filename
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path
