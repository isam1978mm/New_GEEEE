from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import Settings
from app.services.grid import GridManifest
from app.services.roi_contract import write_run_roi_contract_from_grid_manifest
from app.services.storage import write_grid_manifest, write_stage_manifest

GRID_MANIFEST_NAME = "grid_manifest.json"


def save_grid_manifest(settings: Settings, run_id: str, grid_manifest: GridManifest) -> Path:
    manifest_path = write_grid_manifest(settings, run_id, grid_manifest)
    write_run_roi_contract_from_grid_manifest(settings=settings, run_id=run_id, grid_manifest=grid_manifest)
    return manifest_path


def save_stage_manifest(
    settings: Settings,
    run_id: str,
    stage_name: str,
    payload: dict[str, Any],
) -> Path:
    return write_stage_manifest(settings, run_id, stage_name, payload)
