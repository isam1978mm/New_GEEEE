from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import ee
import numpy as np
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import DEM_TILE_SIZE, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.services.ee_session import initialize_ee_session

DEFAULT_START = "2022-01-01"
DEFAULT_END = "2026-02-28"
LST_TIF_NAME = "lst.tif"
RAW_ST_B10_NPY_NAME = ".internal/st_b10_raw.npy"


@dataclass(frozen=True, slots=True)
class ThermalOutputs:
    lst: np.ndarray
    st_b10_raw: np.ndarray


class LstFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> ThermalOutputs: ...


def build_grid_region(grid_spec: GridSpec):
    xmin = grid_spec.manifest.bounds_m["xmin"]
    ymin = grid_spec.manifest.bounds_m["ymin"]
    xmax = grid_spec.manifest.bounds_m["xmax"]
    ymax = grid_spec.manifest.bounds_m["ymax"]
    return ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], grid_spec.crs, False)


def prep_landsat_l2(img):
    qa = img.select("QA_PIXEL")
    cloud_shadow = qa.bitwiseAnd(1 << 4).eq(0)
    clouds = qa.bitwiseAnd(1 << 3).eq(0)
    cirrus = qa.bitwiseAnd(1 << 2).eq(0)
    mask = cloud_shadow.And(clouds).And(cirrus)
    lst_k = img.select("ST_B10").multiply(0.00341802).add(149.0).rename("LST_DAY_K")
    return lst_k.updateMask(mask).copyProperties(img, ["system:time_start"])


def prep_landsat_st_b10(img):
    qa = img.select("QA_PIXEL")
    cloud_shadow = qa.bitwiseAnd(1 << 4).eq(0)
    clouds = qa.bitwiseAnd(1 << 3).eq(0)
    cirrus = qa.bitwiseAnd(1 << 2).eq(0)
    mask = cloud_shadow.And(clouds).And(cirrus)
    return img.select("ST_B10").rename("ST_B10_RAW").updateMask(mask).copyProperties(img, ["system:time_start"])


def build_landsat_lst_collection(grid_spec: GridSpec, *, start_date: str = DEFAULT_START, end_date: str = DEFAULT_END):
    region = build_grid_region(grid_spec)
    l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(region).filterDate(start_date, end_date)
    l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterBounds(region).filterDate(start_date, end_date)
    return l8.merge(l9).map(prep_landsat_l2)


def build_landsat_st_b10_collection(grid_spec: GridSpec, *, start_date: str = DEFAULT_START, end_date: str = DEFAULT_END):
    region = build_grid_region(grid_spec)
    l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(region).filterDate(start_date, end_date)
    l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").filterBounds(region).filterDate(start_date, end_date)
    return l8.merge(l9).map(prep_landsat_st_b10)


def to_grid_lst(image, grid_spec: GridSpec):
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


def build_thermal_tile_requests(grid_spec: GridSpec) -> list[dict[str, float | int]]:
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


def create_ee_lst_fetcher(
    settings,
    grid_spec: GridSpec,
    *,
    start_date: str = DEFAULT_START,
    end_date: str = DEFAULT_END,
) -> LstFetcher:
    initialize_ee_session(settings)
    lst_collection = build_landsat_lst_collection(grid_spec, start_date=start_date, end_date=end_date)
    st_b10_collection = build_landsat_st_b10_collection(grid_spec, start_date=start_date, end_date=end_date)
    lst_day = ee.Image(lst_collection.median()).rename("LST_DAY_K")
    st_b10_day = ee.Image(st_b10_collection.median()).rename("ST_B10_RAW")
    final_lst_for_sample = finalize_for_sample(to_grid_lst(lst_day, grid_spec), grid_spec)
    final_st_b10_for_sample = finalize_for_sample(to_grid_lst(st_b10_day, grid_spec), grid_spec)
    requests = build_thermal_tile_requests(grid_spec)

    def fetch_lst(*, grid_spec: GridSpec) -> ThermalOutputs:
        lst = np.full((grid_spec.size, grid_spec.size), grid_spec.nodata, dtype=np.float32)
        st_b10_raw = np.full((grid_spec.size, grid_spec.size), grid_spec.nodata, dtype=np.float32)
        for request in requests:
            tile_geo = ee.Geometry.Rectangle([request["xmin"], request["ymin"], request["xmax"], request["ymax"]], grid_spec.crs, False)
            lst_rect = final_lst_for_sample.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            st_b10_rect = final_st_b10_for_sample.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            lst_data = np.array(lst_rect["properties"]["LST_DAY_K"], dtype=np.float32)[: DEM_TILE_SIZE, : DEM_TILE_SIZE]
            st_b10_data = np.array(st_b10_rect["properties"]["ST_B10_RAW"], dtype=np.float32)[: DEM_TILE_SIZE, : DEM_TILE_SIZE]
            row_start = request["tile_row"] * DEM_TILE_SIZE
            col_start = request["tile_col"] * DEM_TILE_SIZE
            lst[row_start : row_start + DEM_TILE_SIZE, col_start : col_start + DEM_TILE_SIZE] = lst_data
            st_b10_raw[row_start : row_start + DEM_TILE_SIZE, col_start : col_start + DEM_TILE_SIZE] = st_b10_data
        return ThermalOutputs(lst=lst, st_b10_raw=st_b10_raw)

    return fetch_lst


def deterministic_lst_fetcher(*, grid_spec: GridSpec) -> ThermalOutputs:
    rows, cols = np.indices((grid_spec.size, grid_spec.size), dtype=np.float32)
    lst = (np.float32(295.0) + rows * np.float32(0.01) + cols * np.float32(0.02)).astype(np.float32)
    st_b10_raw = (np.float32(41000.0) + rows * np.float32(1.0) + cols * np.float32(2.0)).astype(np.float32)
    return ThermalOutputs(lst=lst, st_b10_raw=st_b10_raw)


def write_lst_output(run_dir: Path, grid_spec: GridSpec, lst: np.ndarray) -> Path:
    tif_path = run_dir / LST_TIF_NAME
    Image.fromarray(lst.astype(np.float32)).save(tif_path, format="TIFF")
    write_raster_sidecar(
        tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=lst.shape,
    )
    return tif_path


def write_st_b10_raw_output(run_dir: Path, st_b10_raw: np.ndarray) -> Path:
    path = run_dir / RAW_ST_B10_NPY_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, st_b10_raw.astype(np.float32, copy=False))
    return path


def write_thermal_summary(run_dir: Path, lst: np.ndarray, *, nodata: float, start_date: str, end_date: str) -> Path:
    qa_dir = ensure_run_qa_dir(run_dir) / "stacks"
    qa_dir.mkdir(parents=True, exist_ok=True)
    summary_path = qa_dir / "thermal_summary.json"
    valid = lst != nodata
    values = lst[valid]
    summary_path.write_text(
        json.dumps(
            {
                "stage": "thermal",
                "start_date": start_date,
                "end_date": end_date,
                "valid_fraction": round(float(valid.mean()), 6),
                "min": round(float(values.min()), 6) if values.size else None,
                "max": round(float(values.max()), 6) if values.size else None,
                "mean": round(float(values.mean()), 6) if values.size else None,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return summary_path


class ThermalStage(Stage):
    name = "thermal"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(
        self,
        *,
        grid_spec: GridSpec,
        start_date: str = DEFAULT_START,
        end_date: str = DEFAULT_END,
        lst_fetcher: LstFetcher | None = None,
    ) -> None:
        self.grid_spec = grid_spec
        self.start_date = start_date
        self.end_date = end_date
        self.lst_fetcher = lst_fetcher

    async def run(self, context: StageContext) -> StageResult:
        fetcher = self.lst_fetcher or create_ee_lst_fetcher(
            context.settings,
            self.grid_spec,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        outputs = fetcher(grid_spec=self.grid_spec)
        lst = outputs.lst
        st_b10_raw = outputs.st_b10_raw
        if lst.shape != (self.grid_spec.size, self.grid_spec.size):
            raise StageError("Thermal LST output must align to the authoritative GRID.")
        if st_b10_raw.shape != (self.grid_spec.size, self.grid_spec.size):
            raise StageError("Thermal raw ST_B10 output must align to the authoritative GRID.")
        tif_path = write_lst_output(context.run_dir, self.grid_spec, lst)
        st_b10_path = write_st_b10_raw_output(context.run_dir, st_b10_raw)
        summary_path = write_thermal_summary(
            context.run_dir,
            lst,
            nodata=self.grid_spec.nodata,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        artifacts = [
            build_stage_artifact(
                name="lst",
                relative_path=tif_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=tif_path.stat().st_size,
            ),
            build_stage_artifact(
                name="thermal_summary",
                relative_path=summary_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=summary_path.stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="st_b10_raw",
                relative_path=st_b10_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=st_b10_path.stat().st_size,
                http_servable=False,
            ),
        ]
        return StageResult(
            artifacts=artifacts,
            metadata={
                "band_names": ["lst", "st_b10_raw"],
                "shape": [self.grid_spec.size, self.grid_spec.size],
                "start_date": self.start_date,
                "end_date": self.end_date,
            },
        )
