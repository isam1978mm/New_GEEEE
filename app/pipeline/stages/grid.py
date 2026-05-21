from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.db.models.enums import ArtifactClass
from app.pipeline._base import (
    ParityCategory,
    Stage,
    StageContext,
    StageResult,
    build_stage_artifact,
)
from app.pipeline.manifest import save_grid_manifest
from app.services.grid import GridManifest, build_grid_manifest

DEFAULT_NODATA = -9999.0


@dataclass(frozen=True, slots=True)
class GridSpec:
    manifest: GridManifest
    nodata: float = DEFAULT_NODATA

    @property
    def crs(self) -> str:
        return f"EPSG:{self.manifest.epsg}"

    @property
    def transform(self) -> tuple[float, float, float, float, float, float]:
        values = self.manifest.crs_transform
        return (float(values[0]), float(values[1]), float(values[2]), float(values[3]), float(values[4]), float(values[5]))

    @property
    def size(self) -> int:
        return int(self.manifest.size_px)


def grid_spec_from_manifest(manifest: GridManifest, *, nodata: float = DEFAULT_NODATA) -> GridSpec:
    return GridSpec(manifest=manifest, nodata=float(nodata))


def build_run_grid(lat: float, lon: float, *, nodata: float = DEFAULT_NODATA) -> GridSpec:
    return grid_spec_from_manifest(build_grid_manifest(lat, lon), nodata=nodata)


def pixel_center_from_transform(
    transform: tuple[float, float, float, float, float, float],
    *,
    row: int,
    col: int,
) -> tuple[float, float]:
    a, b, c, d, e, f = transform
    x = a * (col + 0.5) + b * (row + 0.5) + c
    y = d * (col + 0.5) + e * (row + 0.5) + f
    return (x, y)


def write_grid_guard_summary(run_dir: Path, grid_spec: GridSpec) -> Path:
    qa_dir = run_dir / "qa" / "grid_dem"
    qa_dir.mkdir(parents=True, exist_ok=True)
    path = qa_dir / "grid_guard_summary.json"
    payload = {
        "stage": "grid",
        "crs": grid_spec.crs,
        "size_px": grid_spec.size,
        "scale_m": float(grid_spec.manifest.scale_m),
        "extent_m": float(grid_spec.manifest.scale_m) * float(grid_spec.size),
        "utm_zone": int(grid_spec.manifest.utm_zone),
        "hemisphere": grid_spec.manifest.hemisphere,
        "nodata": float(grid_spec.nodata),
        "grid_identity_recorded": True,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


class GridStage(Stage):
    name = "grid"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, latitude: float, longitude: float, nodata: float = DEFAULT_NODATA) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.nodata = float(nodata)

    async def run(self, context: StageContext) -> StageResult:
        grid_spec = build_run_grid(self.latitude, self.longitude, nodata=self.nodata)
        manifest_path = save_grid_manifest(context.settings, context.run_id, grid_spec.manifest)
        guard_summary_path = write_grid_guard_summary(context.run_dir, grid_spec)
        artifacts = [
            build_stage_artifact(
                name="grid_manifest",
                relative_path=manifest_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=manifest_path.stat().st_size,
            ),
            build_stage_artifact(
                name="grid_guard_summary",
                relative_path=guard_summary_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=guard_summary_path.stat().st_size,
                http_servable=False,
            ),
        ]
        return StageResult(
            artifacts=artifacts,
            metadata={
                "crs": grid_spec.crs,
                "size_px": grid_spec.size,
                "nodata": grid_spec.nodata,
            },
        )
