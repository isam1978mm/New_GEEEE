from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

import ee
import numpy as np
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import DEM_TILE_SIZE, raster_sidecar_path, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.services.ee_session import initialize_ee_session

DEFAULT_START = "2022-01-01"
DEFAULT_END = "2026-02-28"
DEFAULT_S2_CLOUD_MAX = 3
S2_SOURCE_BANDS = ("B2", "B3", "B4", "B8", "B11", "B12", "B1")
INDEX_NAMES = ("NDVI", "NDWI", "NDMI", "NBR", "IRONOX", "IRON_SWIR", "BSI")
S2_RAW_CUBE_NPY_NAME = "s2_raw_cube.npy"


class S2CubeFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray: ...


def build_grid_region(grid_spec: GridSpec):
    xmin = grid_spec.manifest.bounds_m["xmin"]
    ymin = grid_spec.manifest.bounds_m["ymin"]
    xmax = grid_spec.manifest.bounds_m["xmax"]
    ymax = grid_spec.manifest.bounds_m["ymax"]
    return ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], grid_spec.crs, False)


def build_s2_composite(
    grid_spec: GridSpec,
    *,
    start_date: str = DEFAULT_START,
    end_date: str = DEFAULT_END,
    cloud_max: int = DEFAULT_S2_CLOUD_MAX,
):
    return (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(build_grid_region(grid_spec))
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_max))
        .select(list(S2_SOURCE_BANDS))
        .median()
    )


def to_grid_s2(image, grid_spec: GridSpec):
    return ee.Image(image).toFloat().reproject(crs=grid_spec.crs, crsTransform=list(grid_spec.transform)).clip(
        build_grid_region(grid_spec)
    )


def finalize_for_sample(image, grid_spec: GridSpec):
    return (
        ee.Image(image)
        .toFloat()
        .unmask(grid_spec.nodata)
        .reproject(crs=grid_spec.crs, crsTransform=list(grid_spec.transform))
        .clip(build_grid_region(grid_spec))
    )


def build_s2_tile_requests(grid_spec: GridSpec) -> list[dict[str, float | int]]:
    xmin = grid_spec.manifest.bounds_m["xmin"]
    xmax = grid_spec.manifest.bounds_m["xmax"]
    ymin = grid_spec.manifest.bounds_m["ymin"]
    ymax = grid_spec.manifest.bounds_m["ymax"]
    mid_x = (xmin + xmax) / 2.0
    mid_y = (ymin + ymax) / 2.0
    return [
        {"tile_row": 0, "tile_col": 0, "xmin": xmin, "ymin": mid_y, "xmax": mid_x, "ymax": ymax},
        {"tile_row": 0, "tile_col": 1, "xmin": mid_x, "ymin": mid_y, "xmax": xmax, "ymax": ymax},
        {"tile_row": 1, "tile_col": 0, "xmin": xmin, "ymin": ymin, "xmax": mid_x, "ymax": mid_y},
        {"tile_row": 1, "tile_col": 1, "xmin": mid_x, "ymin": ymin, "xmax": xmax, "ymax": mid_y},
    ]


def create_ee_s2_cube_fetcher(
    settings,
    grid_spec: GridSpec,
    *,
    start_date: str = DEFAULT_START,
    end_date: str = DEFAULT_END,
    cloud_max: int = DEFAULT_S2_CLOUD_MAX,
) -> S2CubeFetcher:
    initialize_ee_session(settings)
    s2 = build_s2_composite(grid_spec, start_date=start_date, end_date=end_date, cloud_max=cloud_max)
    final_for_sample = finalize_for_sample(to_grid_s2(s2, grid_spec), grid_spec)
    requests = build_s2_tile_requests(grid_spec)

    def fetch_cube(*, grid_spec: GridSpec) -> np.ndarray:
        cube = np.full((grid_spec.size, grid_spec.size, len(S2_SOURCE_BANDS)), grid_spec.nodata, dtype=np.float32)
        for request in requests:
            tile_geo = ee.Geometry.Rectangle([request["xmin"], request["ymin"], request["xmax"], request["ymax"]], grid_spec.crs, False)
            rect = final_for_sample.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            for band_index, band_name in enumerate(S2_SOURCE_BANDS):
                data = np.array(rect["properties"][band_name], dtype=np.float32)[: DEM_TILE_SIZE, : DEM_TILE_SIZE]
                row_start = request["tile_row"] * DEM_TILE_SIZE
                col_start = request["tile_col"] * DEM_TILE_SIZE
                cube[row_start : row_start + DEM_TILE_SIZE, col_start : col_start + DEM_TILE_SIZE, band_index] = data
        return cube

    return fetch_cube


def deterministic_s2_cube_fetcher(*, grid_spec: GridSpec) -> np.ndarray:
    size = grid_spec.size
    rows, cols = np.indices((size, size), dtype=np.float32)
    b2 = np.float32(0.10) + rows * np.float32(0.00002)
    b3 = np.float32(0.20) + cols * np.float32(0.00002)
    b4 = np.float32(0.30) + rows * np.float32(0.00003)
    b8 = np.float32(0.60) + cols * np.float32(0.00003)
    b11 = np.float32(0.40) + rows * np.float32(0.00001)
    b12 = np.float32(0.25) + cols * np.float32(0.00001)
    b1 = np.float32(0.15) + rows * np.float32(0.000015)
    return np.stack([b2, b3, b4, b8, b11, b12, b1], axis=-1).astype(np.float32)


def _safe_divide(
    numerator: np.ndarray,
    denominator: np.ndarray,
    *,
    nodata: float,
    valid_mask: np.ndarray | None = None,
) -> np.ndarray:
    result = np.full(numerator.shape, nodata, dtype=np.float32)
    valid = (
        np.isfinite(numerator)
        & np.isfinite(denominator)
        & (numerator != nodata)
        & (denominator != nodata)
        & (denominator != 0.0)
    )
    if valid_mask is not None:
        valid &= valid_mask
    result[valid] = (numerator[valid] / denominator[valid]).astype(np.float32)
    return result


def _normalized_difference(a: np.ndarray, b: np.ndarray, *, nodata: float) -> np.ndarray:
    return _safe_divide(a - b, a + b, nodata=nodata, valid_mask=(a != nodata) & (b != nodata))


def compute_s2_indices(cube: np.ndarray, *, nodata: float) -> dict[str, np.ndarray]:
    if cube.shape[-1] != len(S2_SOURCE_BANDS):
        raise ValueError("S2 cube must contain B1, B2, B3, B4, B8, B11, and B12.")

    b2 = cube[:, :, 0]
    b3 = cube[:, :, 1]
    b4 = cube[:, :, 2]
    b8 = cube[:, :, 3]
    b11 = cube[:, :, 4]
    b12 = cube[:, :, 5]

    ndvi = _normalized_difference(b8, b4, nodata=nodata)
    ndwi = _normalized_difference(b3, b8, nodata=nodata)
    ndmi = _normalized_difference(b8, b11, nodata=nodata)
    nbr = _normalized_difference(b8, b12, nodata=nodata)
    ironox = _safe_divide(b4, b3, nodata=nodata, valid_mask=(b4 != nodata) & (b3 != nodata))
    # Corrects the notebook bug: denominator must be (B11 + B12), not (B11 - B12).
    iron_swir = _safe_divide(
        b11 - b12,
        b11 + b12,
        nodata=nodata,
        valid_mask=(b11 != nodata) & (b12 != nodata),
    )
    bsi = _safe_divide(
        (b11 + b4) - (b8 + b2),
        (b11 + b4) + (b8 + b2),
        nodata=nodata,
        valid_mask=(b11 != nodata) & (b4 != nodata) & (b8 != nodata) & (b2 != nodata),
    )

    return {
        "NDVI": ndvi,
        "NDWI": ndwi,
        "NDMI": ndmi,
        "NBR": nbr,
        "IRONOX": ironox,
        "IRON_SWIR": iron_swir,
        "BSI": bsi,
    }


def write_raster(path: Path, array: np.ndarray) -> None:
    Image.fromarray(array.astype(np.float32)).save(path, format="TIFF")


def write_s2_outputs(run_dir: Path, grid_spec: GridSpec, outputs: dict[str, np.ndarray]) -> list[Path]:
    written_paths: list[Path] = []
    for name, array in outputs.items():
        tif_path = run_dir / f"{name}.tif"
        write_raster(tif_path, array)
        write_raster_sidecar(
            tif_path,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=array.shape,
        )
        written_paths.append(tif_path)
    return written_paths


def write_s2_summary(run_dir: Path, outputs: dict[str, np.ndarray], *, nodata: float, start_date: str, end_date: str, cloud_max: int) -> Path:
    qa_dir = ensure_run_qa_dir(run_dir) / "stacks"
    qa_dir.mkdir(parents=True, exist_ok=True)
    summary_path = qa_dir / "s2_indices_summary.json"
    index_summaries = {}
    for name in INDEX_NAMES:
        array = outputs[name]
        valid = array != nodata
        values = array[valid]
        index_summaries[name] = {
            "valid_fraction": round(float(valid.mean()), 6),
            "min": round(float(values.min()), 6) if values.size else None,
            "max": round(float(values.max()), 6) if values.size else None,
            "mean": round(float(values.mean()), 6) if values.size else None,
        }
    summary_path.write_text(
        json.dumps(
            {
                "stage": "s2_indices",
                "start_date": start_date,
                "end_date": end_date,
                "cloud_max": cloud_max,
                "source_bands": list(S2_SOURCE_BANDS),
                "index_bands": list(INDEX_NAMES),
                "index_summaries": index_summaries,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return summary_path


class S2IndicesStage(Stage):
    name = "s2_indices"
    parity_category = ParityCategory.PARITY_CORRECTS
    parity_reason = "IRON_SWIR denominator corrected from notebook bug (B11-B12) to (B11+B12)"

    def __init__(
        self,
        *,
        grid_spec: GridSpec,
        start_date: str = DEFAULT_START,
        end_date: str = DEFAULT_END,
        cloud_max: int = DEFAULT_S2_CLOUD_MAX,
        s2_cube_fetcher: S2CubeFetcher | None = None,
    ) -> None:
        self.grid_spec = grid_spec
        self.start_date = start_date
        self.end_date = end_date
        self.cloud_max = cloud_max
        self.s2_cube_fetcher = s2_cube_fetcher

    async def run(self, context: StageContext) -> StageResult:
        fetcher = self.s2_cube_fetcher or create_ee_s2_cube_fetcher(
            context.settings,
            self.grid_spec,
            start_date=self.start_date,
            end_date=self.end_date,
            cloud_max=self.cloud_max,
        )
        cube = fetcher(grid_spec=self.grid_spec)
        outputs = compute_s2_indices(cube, nodata=self.grid_spec.nodata)
        written_paths = write_s2_outputs(context.run_dir, self.grid_spec, outputs)
        summary_path = write_s2_summary(
            context.run_dir,
            outputs,
            nodata=self.grid_spec.nodata,
            start_date=self.start_date,
            end_date=self.end_date,
            cloud_max=self.cloud_max,
        )
        # Persist raw S2 band cube for downstream secret layers stage.
        raw_cube_path = context.run_dir / S2_RAW_CUBE_NPY_NAME
        np.save(raw_cube_path, cube.astype(np.float32))
        artifacts = [
            build_stage_artifact(
                name=path.stem,
                relative_path=path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=path.stat().st_size,
            )
            for path in written_paths
        ]
        artifacts.append(
            build_stage_artifact(
                name="s2_indices_summary",
                relative_path=summary_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=summary_path.stat().st_size,
                http_servable=False,
            )
        )
        artifacts.append(
            build_stage_artifact(
                name="s2_raw_cube",
                relative_path=raw_cube_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=raw_cube_path.stat().st_size,
                http_servable=False,
            )
        )
        return StageResult(
            artifacts=artifacts,
            metadata={
                "band_names": list(INDEX_NAMES),
                "source_bands": list(S2_SOURCE_BANDS),
                "start_date": self.start_date,
                "end_date": self.end_date,
                "cloud_max": self.cloud_max,
            },
        )
