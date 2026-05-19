from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult
from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.grid import GridSpec, pixel_center_from_transform
from app.errors import GridDriftError

TOL_CENTER_M = 0.001
TOL_ROT = 1e-12
HALF_PIXEL_TOLERANCE_M = 0.01


def read_raster_metadata(raster_path: Path) -> dict[str, object]:
    sidecar_path = raster_sidecar_path(raster_path)
    if not sidecar_path.is_file():
        raise GridDriftError(f"Missing raster metadata sidecar for {raster_path.name}.")
    return json.loads(sidecar_path.read_text(encoding="utf-8"))


def validate_raster_alignment(raster_path: Path, grid_spec: GridSpec) -> None:
    metadata = read_raster_metadata(raster_path)
    transform = tuple(float(value) for value in metadata["transform"])
    crs = str(metadata["crs"])
    width = int(metadata["width"])
    height = int(metadata["height"])

    issues: list[str] = []
    if crs != grid_spec.crs:
        issues.append("crs_mismatch")
    if width != grid_spec.size or height != grid_spec.size:
        issues.append("size_mismatch")

    if abs(transform[1]) > TOL_ROT or abs(transform[3]) > TOL_ROT:
        issues.append("rotation_detected")

    master_transform = grid_spec.transform
    master_ul = pixel_center_from_transform(master_transform, row=0, col=0)
    master_lr = pixel_center_from_transform(master_transform, row=grid_spec.size - 1, col=grid_spec.size - 1)
    ul = pixel_center_from_transform(transform, row=0, col=0)
    lr = pixel_center_from_transform(transform, row=height - 1, col=width - 1)

    dx_ul = ul[0] - master_ul[0]
    dy_ul = ul[1] - master_ul[1]
    dx_lr = lr[0] - master_lr[0]
    dy_lr = lr[1] - master_lr[1]

    if abs(dx_ul) > TOL_CENTER_M or abs(dy_ul) > TOL_CENTER_M or abs(dx_lr) > TOL_CENTER_M or abs(dy_lr) > TOL_CENTER_M:
        issues.append("pixel_center_mismatch")

    half_px_x = abs(abs(dx_ul) - abs(master_transform[0]) / 2.0) <= HALF_PIXEL_TOLERANCE_M
    half_px_y = abs(abs(dy_ul) - abs(master_transform[4]) / 2.0) <= HALF_PIXEL_TOLERANCE_M
    if half_px_x or half_px_y:
        issues.append("half_pixel_shift")

    if issues:
        raise GridDriftError(f"{raster_path.name} failed alignment checks: {','.join(issues)}")


def validate_array_alignment(array_path: Path, grid_spec: GridSpec) -> None:
    array = np.load(array_path)
    if array.shape != (grid_spec.size, grid_spec.size):
        raise GridDriftError(f"{array_path.name} failed alignment checks: size_mismatch")


class ZeroShiftStage(Stage):
    name = "zero_shift"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        tif_paths = sorted(path for path in context.run_dir.rglob("*.tif") if path.is_file())
        npy_paths = sorted(path for path in context.run_dir.rglob("*.npy") if path.is_file())
        if not tif_paths:
            raise GridDriftError("No GeoTIFF outputs found for zero-shift validation.")

        for tif_path in tif_paths:
            validate_raster_alignment(tif_path, self.grid_spec)
        for npy_path in npy_paths:
            validate_array_alignment(npy_path, self.grid_spec)

        return StageResult(
            metadata={
                "validated_tifs": len(tif_paths),
                "validated_arrays": len(npy_paths),
                "status": "grid_locked",
            }
        )
