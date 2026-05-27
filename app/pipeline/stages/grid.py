from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.db.models.enums import ArtifactClass
from app.pipeline._base import (
    ParityCategory,
    Stage,
    StageContext,
    StageResult,
    build_stage_artifact,
)
from app.pipeline.manifest import save_grid_manifest
from app.pipeline.qa_paths import NOTEBOOK_QA_DIRNAME, ensure_run_qa_dir
from app.services.grid import GridManifest, build_grid_manifest

DEFAULT_NODATA = -9999.0
NOTEBOOK_QA_DIR = NOTEBOOK_QA_DIRNAME
NOTEBOOK_QA_GRID_DX_NAME = "QA_GRID_dx_m_640.tif"
NOTEBOOK_QA_GRID_DY_NAME = "QA_GRID_dy_m_640.tif"
NOTEBOOK_QA_GRID_VALIDMASK_NAME = "QA_GRID_validmask_640.tif"
NOTEBOOK_RUN_MANIFEST_NAME = "RUN_MANIFEST.json"


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


def grid_spec_from_notebook_radar_meta(path: Path) -> GridSpec:
    payload = json.loads(path.read_text(encoding="utf-8"))
    crs_raw = str(payload.get("CRS", ""))
    if not crs_raw.startswith("EPSG:"):
        raise ValueError("Notebook radar metadata must include CRS as EPSG:<code>.")
    epsg = int(crs_raw.split(":", 1)[1])
    scale = float(payload["SCALE"])
    size = int(payload["OUT_SIZE"])
    transform = payload.get("crsTransform", payload.get("ct"))
    bounds = payload["bounds_utm"]
    if not isinstance(transform, list) or len(transform) != 6:
        raise ValueError("Notebook radar metadata must include a 6-value crsTransform/ct.")
    if not isinstance(bounds, list) or len(bounds) != 4:
        raise ValueError("Notebook radar metadata must include 4-value bounds_utm.")
    if not scale.is_integer():
        raise ValueError("Notebook radar metadata SCALE must be an integer meter value for app GRID manifests.")
    utm_zone = epsg % 100
    hemisphere = "north" if 32601 <= epsg <= 32660 else "south" if 32701 <= epsg <= 32760 else ""
    if not hemisphere:
        raise ValueError("Notebook radar metadata CRS must be a UTM EPSG code.")
    manifest = GridManifest(
        epsg=epsg,
        utm_zone=utm_zone,
        hemisphere=hemisphere,
        scale_m=int(scale),
        size_px=size,
        crs_transform=[float(value) for value in transform],
        bounds_m={
            "xmin": float(bounds[0]),
            "ymin": float(bounds[1]),
            "xmax": float(bounds[2]),
            "ymax": float(bounds[3]),
        },
    )
    return grid_spec_from_manifest(manifest, nodata=float(payload.get("NODATA", DEFAULT_NODATA)))


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
    qa_dir = ensure_run_qa_dir(run_dir) / "grid_dem"
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


def write_notebook_qa_grid_outputs(run_dir: Path, grid_spec: GridSpec) -> list[Path]:
    from app.pipeline.stages.dem import write_georeferenced_raster, write_raster_sidecar

    qa_dir = ensure_run_qa_dir(run_dir)
    qa_dir.mkdir(parents=True, exist_ok=True)
    zeros = np.zeros((grid_spec.size, grid_spec.size), dtype=np.float32)
    validmask = np.ones((grid_spec.size, grid_spec.size), dtype=np.float32)
    outputs = [
        (NOTEBOOK_QA_GRID_DX_NAME, zeros),
        (NOTEBOOK_QA_GRID_DY_NAME, zeros),
        (NOTEBOOK_QA_GRID_VALIDMASK_NAME, validmask),
    ]
    written_paths: list[Path] = []
    for filename, array in outputs:
        path = qa_dir / filename
        write_georeferenced_raster(path, array, grid_spec)
        write_raster_sidecar(
            path,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=array.shape,
        )
        written_paths.append(path)
    return written_paths


def write_notebook_run_manifest(run_dir: Path, run_id: str, grid_spec: GridSpec) -> Path:
    qa_dir = ensure_run_qa_dir(run_dir)
    qa_dir.mkdir(parents=True, exist_ok=True)
    path = qa_dir / NOTEBOOK_RUN_MANIFEST_NAME
    payload = {
        "schema": "notebook_compatible_run_manifest_v1",
        "run_id": run_id,
        "grid": {
            "crs": grid_spec.crs,
            "epsg": int(grid_spec.manifest.epsg),
            "scale_m": float(grid_spec.manifest.scale_m),
            "out_size": grid_spec.size,
            "nodata": float(grid_spec.nodata),
        },
        "output_groups": [
            "DEM_GEO8_TIFS",
            "GEOTIFF_RADAR_BANDS",
            "NPY_RADAR_BANDS",
            "NPY_STACKS",
            "QA",
        ],
        "qa_grid_outputs": [
            NOTEBOOK_QA_GRID_DX_NAME,
            NOTEBOOK_QA_GRID_DY_NAME,
            NOTEBOOK_QA_GRID_VALIDMASK_NAME,
        ],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


class GridStage(Stage):
    name = "grid"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(
        self,
        *,
        latitude: float,
        longitude: float,
        nodata: float = DEFAULT_NODATA,
        grid_spec_override: GridSpec | None = None,
    ) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.nodata = float(nodata)
        self.grid_spec_override = grid_spec_override

    async def run(self, context: StageContext) -> StageResult:
        grid_spec = self.grid_spec_override or build_run_grid(self.latitude, self.longitude, nodata=self.nodata)
        manifest_path = save_grid_manifest(context.settings, context.run_id, grid_spec.manifest)
        guard_summary_path = write_grid_guard_summary(context.run_dir, grid_spec)
        qa_grid_paths = write_notebook_qa_grid_outputs(context.run_dir, grid_spec)
        notebook_manifest_path = write_notebook_run_manifest(context.run_dir, context.run_id, grid_spec)
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
        artifacts.extend(
            build_stage_artifact(
                name={
                    NOTEBOOK_QA_GRID_DX_NAME: "notebook_QA_GRID_dx_m_640",
                    NOTEBOOK_QA_GRID_DY_NAME: "notebook_QA_GRID_dy_m_640",
                    NOTEBOOK_QA_GRID_VALIDMASK_NAME: "notebook_QA_GRID_validmask_640",
                }[path.name],
                relative_path=path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=path.stat().st_size,
            )
            for path in qa_grid_paths
        )
        artifacts.append(
            build_stage_artifact(
                name="notebook_RUN_MANIFEST",
                relative_path=notebook_manifest_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=notebook_manifest_path.stat().st_size,
            )
        )
        return StageResult(
            artifacts=artifacts,
            metadata={
                "crs": grid_spec.crs,
                "size_px": grid_spec.size,
                "nodata": grid_spec.nodata,
                "notebook_qa_grid_outputs": [path.name for path in qa_grid_paths],
                "notebook_run_manifest": NOTEBOOK_RUN_MANIFEST_NAME,
            },
        )
