from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import ee
import numpy as np
import rasterio
from rasterio.transform import Affine

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import (
    ParityCategory,
    Stage,
    StageContext,
    StageResult,
    build_stage_artifact,
)
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.grid import GridSpec
from app.services.ee_session import initialize_ee_session
from app.services.grid import GridManifest

DEM_TIF_NAME = "dem.tif"
DEM_NPY_NAME = "dem.npy"
DEM_TILE_SIZE = 320
NOTEBOOK_DEM_DIR_NAME = "DEM_GEO8_TIFS"
NOTEBOOK_DEM_TIF_NAME = "DEM_640.tif"
MIN_DEM_VALID_FRACTION = 0.001


class DemTileFetcher(Protocol):
    def __call__(
        self,
        *,
        grid_spec: GridSpec,
        tile_row: int,
        tile_col: int,
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        size: int,
    ) -> np.ndarray: ...


@dataclass(frozen=True, slots=True)
class DemTileRequest:
    tile_row: int
    tile_col: int
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    size: int


def build_dem_tile_requests(grid_spec: GridSpec, *, tile_size: int = DEM_TILE_SIZE) -> list[DemTileRequest]:
    if grid_spec.size % tile_size != 0:
        raise ValueError(f"GRID size {grid_spec.size} must be divisible by tile size {tile_size}.")

    scale_x, _, xmin, _, scale_y, ymax = grid_spec.transform
    requests: list[DemTileRequest] = []
    n_tiles = grid_spec.size // tile_size

    for tile_row in range(n_tiles):
        for tile_col in range(n_tiles):
            tile_xmin = xmin + tile_col * tile_size * scale_x
            tile_xmax = tile_xmin + tile_size * scale_x
            tile_ymax = ymax + tile_row * tile_size * scale_y
            tile_ymin = tile_ymax + tile_size * scale_y
            requests.append(
                DemTileRequest(
                    tile_row=tile_row,
                    tile_col=tile_col,
                    xmin=float(tile_xmin),
                    ymin=float(tile_ymin),
                    xmax=float(tile_xmax),
                    ymax=float(tile_ymax),
                    size=tile_size,
                )
            )
    return requests


def deterministic_dem_tile(
    *,
    grid_spec: GridSpec,
    tile_row: int,
    tile_col: int,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    size: int,
) -> np.ndarray:
    del xmin, ymin, xmax, ymax
    row_offset = tile_row * size
    col_offset = tile_col * size
    rows, cols = np.indices((size, size), dtype=np.float32)
    zone_term = np.float32(grid_spec.manifest.utm_zone * 3.0)
    hemisphere_term = np.float32(25.0 if grid_spec.manifest.hemisphere == "north" else -25.0)
    elevation = (
        np.float32(1000.0)
        + zone_term
        + hemisphere_term
        + (rows + np.float32(row_offset)) * np.float32(0.5)
        + (cols + np.float32(col_offset)) * np.float32(0.25)
    )
    return elevation.astype(np.float32, copy=False)


def build_grid_region(grid_spec: GridSpec):
    scale_x, _, xmin, _, scale_y, ymax = grid_spec.transform
    xmax = xmin + grid_spec.size * scale_x
    ymin = ymax + grid_spec.size * scale_y
    return ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], grid_spec.crs, False)


def build_ee_dem_image(grid_spec: GridSpec):
    return (
        ee.ImageCollection("COPERNICUS/DEM/GLO30")
        .mosaic()
        .select("DEM")
        .clip(build_grid_region(grid_spec))
        .toFloat()
        .reproject(crs=grid_spec.crs, crsTransform=list(grid_spec.transform))
        .unmask(grid_spec.nodata)
    )


def create_ee_dem_tile_fetcher(settings, grid_spec: GridSpec) -> DemTileFetcher:
    initialize_ee_session(settings)
    dem_image = build_ee_dem_image(grid_spec)

    def fetch_tile(
        *,
        grid_spec: GridSpec,
        tile_row: int,
        tile_col: int,
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        size: int,
    ) -> np.ndarray:
        del tile_row, tile_col
        tile_geo = ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], grid_spec.crs, False)
        rect = dem_image.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
        tile = np.array(rect["properties"]["DEM"], dtype=np.float32)[:size, :size]
        if tile.shape != (size, size):
            raise StageError(f"EE DEM tile returned shape {tile.shape}, expected {(size, size)}.")
        return tile

    return fetch_tile


def valid_fraction(array: np.ndarray, *, nodata: float) -> float:
    valid = np.isfinite(array) & (array != nodata)
    return float(valid.mean())


def validate_dem_array(dem_array: np.ndarray, grid_spec: GridSpec) -> float:
    expected_shape = (grid_spec.size, grid_spec.size)
    if dem_array.shape != expected_shape:
        raise StageError(f"DEM output shape {dem_array.shape} does not match expected {expected_shape}.")
    fraction = valid_fraction(dem_array, nodata=grid_spec.nodata)
    if fraction < MIN_DEM_VALID_FRACTION:
        raise StageError(
            f"DEM source produced insufficient valid data: valid_fraction={fraction:.6f}, "
            f"minimum={MIN_DEM_VALID_FRACTION:.6f}."
        )
    return fraction


def build_dem_array(
    grid_spec: GridSpec,
    *,
    tile_fetcher: DemTileFetcher,
    tile_size: int = DEM_TILE_SIZE,
) -> np.ndarray:
    requests = build_dem_tile_requests(grid_spec, tile_size=tile_size)
    dem = np.full((grid_spec.size, grid_spec.size), grid_spec.nodata, dtype=np.float32)

    for request in requests:
        tile = tile_fetcher(
            grid_spec=grid_spec,
            tile_row=request.tile_row,
            tile_col=request.tile_col,
            xmin=request.xmin,
            ymin=request.ymin,
            xmax=request.xmax,
            ymax=request.ymax,
            size=request.size,
        )
        if tile.shape != (request.size, request.size):
            raise StageError(
                f"DEM tile ({request.tile_row},{request.tile_col}) returned shape {tile.shape}, "
                f"expected {(request.size, request.size)}."
            )
        row_start = request.tile_row * request.size
        col_start = request.tile_col * request.size
        dem[row_start : row_start + request.size, col_start : col_start + request.size] = tile

    validate_dem_array(dem, grid_spec)
    return dem


def raster_sidecar_path(raster_path: Path) -> Path:
    return raster_path.with_name(f"{raster_path.name}.meta.json")


def write_raster_sidecar(
    raster_path: Path,
    *,
    grid_manifest: GridManifest,
    nodata: float,
    dtype: str,
    shape: tuple[int, int],
) -> Path:
    payload = {
        "crs": f"EPSG:{grid_manifest.epsg}",
        "dtype": dtype,
        "height": int(shape[0]),
        "width": int(shape[1]),
        "nodata": float(nodata),
        "transform": [float(value) for value in grid_manifest.crs_transform],
    }
    sidecar_path = raster_sidecar_path(raster_path)
    sidecar_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return sidecar_path


def write_georeferenced_raster(path: Path, array: np.ndarray, grid_spec: GridSpec) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = array.astype(np.float32, copy=False)
    if data.ndim == 2:
        raster_data = data[np.newaxis, :, :]
    elif data.ndim == 3:
        raster_data = np.moveaxis(data, -1, 0)
    else:
        raise ValueError("GeoTIFF output must be a 2D array or HWC cube.")
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=int(data.shape[0]),
        width=int(data.shape[1]),
        count=int(raster_data.shape[0]),
        dtype="float32",
        crs=grid_spec.crs,
        transform=Affine(*grid_spec.transform),
        nodata=float(grid_spec.nodata),
        compress="deflate",
    ) as dataset:
        dataset.write(raster_data)


def write_dem_outputs(run_dir: Path, grid_spec: GridSpec, dem_array: np.ndarray) -> dict[str, Path]:
    dem_tif_path = run_dir / DEM_TIF_NAME
    dem_npy_path = run_dir / DEM_NPY_NAME
    notebook_dem_tif_path = run_dir / NOTEBOOK_DEM_DIR_NAME / NOTEBOOK_DEM_TIF_NAME

    write_georeferenced_raster(dem_tif_path, dem_array, grid_spec)
    np.save(dem_npy_path, dem_array)
    sidecar_path = write_raster_sidecar(
        dem_tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=dem_array.shape,
    )
    write_georeferenced_raster(notebook_dem_tif_path, dem_array, grid_spec)
    notebook_sidecar_path = write_raster_sidecar(
        notebook_dem_tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=dem_array.shape,
    )
    return {
        "dem_tif": dem_tif_path,
        "dem_npy": dem_npy_path,
        "dem_tif_sidecar": sidecar_path,
        "notebook_dem_tif": notebook_dem_tif_path,
        "notebook_dem_tif_sidecar": notebook_sidecar_path,
    }


def write_dem_audit_summary(run_dir: Path, grid_spec: GridSpec, dem_array: np.ndarray, *, valid_fraction_value: float) -> Path:
    qa_dir = ensure_run_qa_dir(run_dir) / "grid_dem"
    qa_dir.mkdir(parents=True, exist_ok=True)
    summary_path = qa_dir / "dem_audit_summary.json"
    nodata_count = int((dem_array == grid_spec.nodata).sum())
    valid = np.isfinite(dem_array) & (dem_array != grid_spec.nodata)
    values = dem_array[valid]
    payload = {
        "stage": "dem",
        "shape": [int(dem_array.shape[0]), int(dem_array.shape[1])],
        "dtype": str(dem_array.dtype),
        "tile_size": DEM_TILE_SIZE,
        "tile_count": len(build_dem_tile_requests(grid_spec)),
        "nodata_count": nodata_count,
        "nodata_fraction": round(nodata_count / float(dem_array.size), 6),
        "valid_fraction": round(float(valid_fraction_value), 6),
        "minimum_valid_fraction": MIN_DEM_VALID_FRACTION,
        "dem_min": round(float(values.min()), 6),
        "dem_max": round(float(values.max()), 6),
        "grid_locked": True,
    }
    summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return summary_path


class DemStage(Stage):
    name = "dem"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(
        self,
        *,
        grid_spec: GridSpec,
        tile_fetcher: DemTileFetcher | None = None,
    ) -> None:
        self.grid_spec = grid_spec
        self.tile_fetcher = tile_fetcher

    async def run(self, context: StageContext) -> StageResult:
        tile_fetcher = self.tile_fetcher or create_ee_dem_tile_fetcher(context.settings, self.grid_spec)
        dem_array = build_dem_array(self.grid_spec, tile_fetcher=tile_fetcher)
        dem_valid_fraction = validate_dem_array(dem_array, self.grid_spec)
        outputs = write_dem_outputs(context.run_dir, self.grid_spec, dem_array)
        audit_summary_path = write_dem_audit_summary(
            context.run_dir,
            self.grid_spec,
            dem_array,
            valid_fraction_value=dem_valid_fraction,
        )
        artifacts = [
            build_stage_artifact(
                name="dem_tif",
                relative_path=outputs["dem_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["dem_tif"].stat().st_size,
            ),
            build_stage_artifact(
                name="dem_npy",
                relative_path=outputs["dem_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["dem_npy"].stat().st_size,
            ),
            build_stage_artifact(
                name="notebook_dem_640_tif",
                relative_path=outputs["notebook_dem_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["notebook_dem_tif"].stat().st_size,
            ),
            build_stage_artifact(
                name="dem_audit_summary",
                relative_path=audit_summary_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=audit_summary_path.stat().st_size,
                http_servable=False,
            ),
        ]
        return StageResult(
            artifacts=artifacts,
            metadata={
                "dem_shape": list(dem_array.shape),
                "dem_min": float(dem_array[np.isfinite(dem_array) & (dem_array != self.grid_spec.nodata)].min()),
                "dem_max": float(dem_array[np.isfinite(dem_array) & (dem_array != self.grid_spec.nodata)].max()),
                "dem_valid_fraction": round(float(dem_valid_fraction), 6),
                "grid_crs": f"EPSG:{self.grid_spec.manifest.epsg}",
                "tile_size": DEM_TILE_SIZE,
                "tile_count": len(build_dem_tile_requests(self.grid_spec)),
            },
        )
