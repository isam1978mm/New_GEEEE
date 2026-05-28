from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import NOTEBOOK_DEM_DIR_NAME, write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec

WINDOW_RADIUS_METERS = 100.0
OUTPUT_NAMES = ("slope", "aspect", "curvature", "TPI", "TRI", "roughness", "TWI")
NOTEBOOK_DEM_FILENAMES = {
    "slope": "slope_deg_640.tif",
    "aspect": "aspect_deg_640.tif",
    "roughness": "roughness_100m_640.tif",
    "TPI": "tpi_100m_640.tif",
}
NOTEBOOK_HILLSHADE_NAME = "hillshade_0to1_640.tif"


def _integral_image(array: np.ndarray) -> np.ndarray:
    ii = np.zeros((array.shape[0] + 1, array.shape[1] + 1), dtype=np.float64)
    np.cumsum(np.cumsum(array, axis=0), axis=1, out=ii[1:, 1:])
    return ii


def box_mean_nanaware(array: np.ndarray, radius_px: int) -> np.ndarray:
    kernel = 2 * radius_px + 1
    padded = np.pad(array, ((radius_px, radius_px), (radius_px, radius_px)), mode="edge")
    valid = np.isfinite(padded)
    padded0 = np.where(valid, padded, 0.0).astype(np.float64)
    valid0 = valid.astype(np.float64)
    ii_sum = _integral_image(padded0)
    ii_cnt = _integral_image(valid0)
    window_sum = ii_sum[kernel:, kernel:] - ii_sum[:-kernel, kernel:] - ii_sum[kernel:, :-kernel] + ii_sum[:-kernel, :-kernel]
    window_cnt = ii_cnt[kernel:, kernel:] - ii_cnt[:-kernel, kernel:] - ii_cnt[kernel:, :-kernel] + ii_cnt[:-kernel, :-kernel]
    return np.where(window_cnt > 0, window_sum / window_cnt, np.nan).astype(np.float32)


def box_std_nanaware(array: np.ndarray, radius_px: int) -> np.ndarray:
    kernel = 2 * radius_px + 1
    padded = np.pad(array, ((radius_px, radius_px), (radius_px, radius_px)), mode="edge")
    valid = np.isfinite(padded)
    padded0 = np.where(valid, padded, 0.0).astype(np.float64)
    valid0 = valid.astype(np.float64)
    ii_sum = _integral_image(padded0)
    ii_sum2 = _integral_image(padded0 * padded0)
    ii_cnt = _integral_image(valid0)
    window_sum = ii_sum[kernel:, kernel:] - ii_sum[:-kernel, kernel:] - ii_sum[kernel:, :-kernel] + ii_sum[:-kernel, :-kernel]
    window_sum2 = ii_sum2[kernel:, kernel:] - ii_sum2[:-kernel, kernel:] - ii_sum2[kernel:, :-kernel] + ii_sum2[:-kernel, :-kernel]
    window_cnt = ii_cnt[kernel:, kernel:] - ii_cnt[:-kernel, kernel:] - ii_cnt[kernel:, :-kernel] + ii_cnt[:-kernel, :-kernel]
    mean = np.where(window_cnt > 0, window_sum / window_cnt, np.nan)
    variance = np.where(window_cnt > 0, (window_sum2 / window_cnt) - mean * mean, np.nan)
    return np.sqrt(np.maximum(variance, 0.0)).astype(np.float32)


def load_dem_array(run_dir: Path) -> np.ndarray:
    dem_path = run_dir / "dem.npy"
    if not dem_path.is_file():
        raise StageError("DEM stage output is required before DEM derivatives.")
    return np.load(dem_path)


def compute_dem_derivatives(dem: np.ndarray, *, nodata: float, scale_m: float) -> dict[str, np.ndarray]:
    dem_float = dem.astype(np.float32, copy=True)
    dem_float = np.where(dem_float == nodata, np.nan, dem_float)
    source_valid = np.isfinite(dem_float)

    dz_dy, dz_dx = np.gradient(dem_float, scale_m, scale_m)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    slope = np.degrees(slope_rad).astype(np.float32)
    aspect_rad = np.arctan2(-dz_dx, dz_dy)
    aspect = ((np.degrees(aspect_rad) + 360.0) % 360.0).astype(np.float32)

    d2z_dxx = np.gradient(dz_dx, scale_m, axis=1)
    d2z_dyy = np.gradient(dz_dy, scale_m, axis=0)
    curvature = (d2z_dxx + d2z_dyy).astype(np.float32)

    radius_px = max(1, int(round(WINDOW_RADIUS_METERS / scale_m)))
    mean_100 = box_mean_nanaware(dem_float, radius_px)
    tpi = (dem_float - mean_100).astype(np.float32)
    roughness = box_std_nanaware(dem_float, radius_px).astype(np.float32)

    # PRD requires TRI/TWI outputs in addition to the notebook's local gradient/TPI block.
    tri = box_mean_nanaware(np.abs(dem_float - mean_100).astype(np.float32), radius_px).astype(np.float32)
    twi = np.log((np.maximum(mean_100 - dem_float, 0.0) + 1.0) / np.maximum(np.tan(slope_rad), 1e-6)).astype(np.float32)

    outputs = {
        "slope": slope,
        "aspect": aspect,
        "curvature": curvature,
        "TPI": tpi,
        "TRI": tri,
        "roughness": roughness,
        "TWI": twi,
    }
    for name, array in outputs.items():
        array[~source_valid] = nodata
        array[~np.isfinite(array)] = nodata
        outputs[name] = array.astype(np.float32, copy=False)
    return outputs


def compute_hillshade(dem: np.ndarray, *, nodata: float, scale_m: float) -> np.ndarray:
    dem_float = dem.astype(np.float32, copy=True)
    dem_float = np.where(dem_float == nodata, np.nan, dem_float)
    source_valid = np.isfinite(dem_float)
    dz_dy, dz_dx = np.gradient(dem_float, scale_m, scale_m)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    aspect_rad = np.arctan2(-dz_dx, dz_dy)
    azimuth_rad = np.deg2rad(45.0)
    altitude_rad = np.deg2rad(45.0)
    hillshade = (
        np.sin(altitude_rad) * np.cos(slope_rad)
        + np.cos(altitude_rad) * np.sin(slope_rad) * np.cos(azimuth_rad - aspect_rad)
    )
    hillshade = np.clip(hillshade, 0.0, 1.0).astype(np.float32)
    hillshade[~source_valid] = nodata
    hillshade[~np.isfinite(hillshade)] = nodata
    return hillshade.astype(np.float32, copy=False)


def write_dem_derivative_outputs(run_dir: Path, grid_spec: GridSpec, outputs: dict[str, np.ndarray]) -> list[Path]:
    written_paths: list[Path] = []
    for name in OUTPUT_NAMES:
        tif_path = run_dir / f"{name}.tif"
        array = outputs[name]
        write_georeferenced_raster(tif_path, array, grid_spec)
        write_raster_sidecar(
            tif_path,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=array.shape,
        )
        written_paths.append(tif_path)
    return written_paths


def write_notebook_dem_outputs(
    run_dir: Path,
    grid_spec: GridSpec,
    *,
    dem: np.ndarray,
    outputs: dict[str, np.ndarray],
) -> list[Path]:
    notebook_dir = run_dir / NOTEBOOK_DEM_DIR_NAME
    notebook_outputs = {
        "DEM_640.tif": dem.astype(np.float32, copy=False),
        NOTEBOOK_DEM_FILENAMES["slope"]: outputs["slope"],
        NOTEBOOK_DEM_FILENAMES["aspect"]: outputs["aspect"],
        NOTEBOOK_DEM_FILENAMES["roughness"]: outputs["roughness"],
        NOTEBOOK_DEM_FILENAMES["TPI"]: outputs["TPI"],
        NOTEBOOK_HILLSHADE_NAME: compute_hillshade(
            dem,
            nodata=grid_spec.nodata,
            scale_m=float(grid_spec.manifest.scale_m),
        ),
    }
    written_paths: list[Path] = []
    for filename, array in notebook_outputs.items():
        tif_path = notebook_dir / filename
        write_georeferenced_raster(tif_path, array, grid_spec)
        write_raster_sidecar(
            tif_path,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=array.shape,
        )
        written_paths.append(tif_path)
    return written_paths


def write_dem_derivatives_summary(run_dir: Path, outputs: dict[str, np.ndarray], *, nodata: float) -> Path:
    qa_dir = ensure_run_qa_dir(run_dir) / "stacks"
    qa_dir.mkdir(parents=True, exist_ok=True)
    summary_path = qa_dir / "dem_derivatives_summary.json"
    band_summaries = {}
    for name in OUTPUT_NAMES:
        array = outputs[name]
        valid = array != nodata
        values = array[valid]
        band_summaries[name] = {
            "valid_fraction": round(float(valid.mean()), 6),
            "min": round(float(values.min()), 6) if values.size else None,
            "max": round(float(values.max()), 6) if values.size else None,
            "mean": round(float(values.mean()), 6) if values.size else None,
        }
    summary_path.write_text(
        json.dumps(
            {
                "stage": "dem_derivatives",
                "band_count": len(OUTPUT_NAMES),
                "bands": list(OUTPUT_NAMES),
                "band_summaries": band_summaries,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return summary_path


class DemDerivativesStage(Stage):
    name = "dem_derivatives"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        dem = load_dem_array(context.run_dir)
        if dem.shape != (self.grid_spec.size, self.grid_spec.size):
            raise StageError("DEM derivative stage requires a DEM aligned to the authoritative GRID.")
        outputs = compute_dem_derivatives(
            dem,
            nodata=self.grid_spec.nodata,
            scale_m=float(self.grid_spec.manifest.scale_m),
        )
        written_paths = write_dem_derivative_outputs(context.run_dir, self.grid_spec, outputs)
        notebook_written_paths = write_notebook_dem_outputs(
            context.run_dir,
            self.grid_spec,
            dem=dem,
            outputs=outputs,
        )
        summary_path = write_dem_derivatives_summary(context.run_dir, outputs, nodata=self.grid_spec.nodata)
        artifacts = [
            build_stage_artifact(
                name=path.stem,
                relative_path=path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=path.stat().st_size,
            )
            for path in written_paths
        ]
        artifacts.extend(
            build_stage_artifact(
                name=f"notebook_{path.stem}",
                relative_path=path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=path.stat().st_size,
            )
            for path in notebook_written_paths
        )
        artifacts.append(
            build_stage_artifact(
                name="dem_derivatives_summary",
                relative_path=summary_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=summary_path.stat().st_size,
                http_servable=False,
            )
        )
        return StageResult(
            artifacts=artifacts,
            metadata={
                "band_names": list(OUTPUT_NAMES),
                "shape": [self.grid_spec.size, self.grid_spec.size],
                "scale_m": self.grid_spec.manifest.scale_m,
            },
        )
