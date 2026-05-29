from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

import ee
import numpy as np

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import build_dem_tile_requests, write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.pipeline.stages.s2_indices import S2_SOURCE_BANDS, S2_RAW_CUBE_NPY_NAME
from app.pipeline.stages.thermal import (
    build_notebook_l9_st_b10_image,
    RAW_ST_B10_NPY_NAME,
)
from app.services.ee_session import initialize_ee_session

EPS = 1e-10
REPORT_640_MANIFEST_NAME = "REPORT_640_manifest.json"
NOTEBOOK_REPORT_S2_START = "2022-01-01"
NOTEBOOK_REPORT_S2_END = "2026-03-01"
NOTEBOOK_REPORT_S2_CLOUD_MAX = 10
NOTEBOOK_REPORT_S2_SOURCE_BANDS = ("B11", "B12")
REPORT_POTTERY_NAME = "REPORT_640_Pottery_Report"
REPORT_MASS_NAME = "REPORT_640_Mass_Report"

_S2_BAND_INDEX = {name: index for index, name in enumerate(S2_SOURCE_BANDS)}


class ReportPotteryFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray: ...


class ReportMassFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray: ...


def load_s2_raw_cube(run_dir: Path) -> np.ndarray:
    path = run_dir / S2_RAW_CUBE_NPY_NAME
    if not path.is_file():
        raise StageError("S2 raw band cube is required before report_640 stage.")
    return np.load(path)


def load_st_b10_raw(run_dir: Path) -> np.ndarray:
    path = run_dir / RAW_ST_B10_NPY_NAME
    if not path.is_file():
        raise StageError("Raw ST_B10 source is required before report_640 stage.")
    return np.load(path)


def compute_report_pottery_report(s2_cube: np.ndarray, *, nodata: float) -> np.ndarray:
    """B12 / B11"""
    b12 = s2_cube[:, :, _S2_BAND_INDEX["B12"]]
    b11 = s2_cube[:, :, _S2_BAND_INDEX["B11"]]
    valid = (b12 != nodata) & (b11 != nodata) & np.isfinite(b12) & np.isfinite(b11) & (b11 != 0.0)
    result = np.full(b12.shape, nodata, dtype=np.float32)
    result[valid] = (b12[valid] / b11[valid]).astype(np.float32)
    return result


def compute_report_mass_report(s2_cube: np.ndarray, st_b10_raw: np.ndarray, *, nodata: float) -> np.ndarray:
    """B12 * ST_B10 / 1000"""
    b12 = s2_cube[:, :, _S2_BAND_INDEX["B12"]]
    valid = (
        (b12 != nodata)
        & (st_b10_raw != nodata)
        & np.isfinite(b12)
        & np.isfinite(st_b10_raw)
    )
    result = np.full(b12.shape, nodata, dtype=np.float32)
    result[valid] = ((b12[valid] * st_b10_raw[valid]) / np.float32(1000.0)).astype(np.float32)
    return result


def compute_report_zero_point_targets(s2_cube: np.ndarray, *, nodata: float) -> np.ndarray:
    """Threshold intersection of behavior tensors derived from S2 raw bands."""
    b12 = s2_cube[:, :, _S2_BAND_INDEX["B12"]]
    b11 = s2_cube[:, :, _S2_BAND_INDEX["B11"]]
    b4 = s2_cube[:, :, _S2_BAND_INDEX["B4"]]
    b3 = s2_cube[:, :, _S2_BAND_INDEX["B3"]]
    b8 = s2_cube[:, :, _S2_BAND_INDEX["B8"]]

    valid = (
        (b12 != nodata) & (b11 != nodata) & (b4 != nodata) & (b3 != nodata) & (b8 != nodata)
        & np.isfinite(b12) & np.isfinite(b11) & np.isfinite(b4) & np.isfinite(b3) & np.isfinite(b8)
        & (b11 != 0.0) & (b3 != 0.0) & ((b8 + b4) != 0.0)
    )

    # AI_BEH_GoldAlloy_Signal = B12 / B11 > 1.45
    gold_alloy = np.full(b12.shape, 0.0, dtype=np.float32)
    gold_alloy[valid] = (b12[valid] / b11[valid]).astype(np.float32)
    cond1 = (gold_alloy > 1.45) & valid

    # AI_BEH_IronOxide_Hardness = B4 / B3 > 1.25
    iron_oxide = np.full(b12.shape, 0.0, dtype=np.float32)
    iron_oxide[valid] = (b4[valid] / b3[valid]).astype(np.float32)
    cond2 = (iron_oxide > 1.25) & valid

    # AI_BEH_VegRoot_Anomaly = NDVI = (B8 - B4) / (B8 + B4) > 0.35
    ndvi = np.full(b12.shape, 0.0, dtype=np.float32)
    ndvi[valid] = ((b8[valid] - b4[valid]) / (b8[valid] + b4[valid])).astype(np.float32)
    cond3 = (ndvi > 0.35) & valid

    result = np.full(b12.shape, nodata, dtype=np.float32)
    result[valid] = np.float32(0.0)
    result[cond1 & cond2 & cond3] = np.float32(1.0)
    return result


def build_grid_region(grid_spec: GridSpec):
    scale_x, _, xmin, _, scale_y, ymax = grid_spec.transform
    xmax = xmin + grid_spec.size * scale_x
    ymin = ymax + grid_spec.size * scale_y
    return ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], grid_spec.crs, False)


def build_notebook_report_s2_composite(grid_spec: GridSpec):
    return (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(build_grid_region(grid_spec))
        .filterDate(NOTEBOOK_REPORT_S2_START, NOTEBOOK_REPORT_S2_END)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", NOTEBOOK_REPORT_S2_CLOUD_MAX))
        .select(list(NOTEBOOK_REPORT_S2_SOURCE_BANDS))
        .median()
    )


def build_notebook_report_pottery_image(grid_spec: GridSpec):
    s2_col = build_notebook_report_s2_composite(grid_spec)
    pottery = s2_col.select("B12").divide(s2_col.select("B11")).rename(REPORT_POTTERY_NAME)
    return (
        pottery.toFloat()
        .reproject(crs=grid_spec.crs, crsTransform=list(grid_spec.transform))
        .clip(build_grid_region(grid_spec))
    )


def build_notebook_report_mass_image(grid_spec: GridSpec):
    s2_col = build_notebook_report_s2_composite(grid_spec)
    l9_col = build_notebook_l9_st_b10_image(grid_spec)
    mass = s2_col.select("B12").multiply(l9_col.select("ST_B10")).divide(1000).rename(REPORT_MASS_NAME)
    return (
        mass.toFloat()
        .reproject(crs=grid_spec.crs, crsTransform=list(grid_spec.transform))
        .clip(build_grid_region(grid_spec))
    )


def create_ee_notebook_report_pottery_fetcher(settings, grid_spec: GridSpec) -> ReportPotteryFetcher:
    initialize_ee_session(settings)
    pottery_image = build_notebook_report_pottery_image(grid_spec)
    requests = build_dem_tile_requests(grid_spec)

    def fetch_pottery(*, grid_spec: GridSpec) -> np.ndarray:
        array = np.full((grid_spec.size, grid_spec.size), grid_spec.nodata, dtype=np.float32)
        for request in requests:
            tile_geo = ee.Geometry.Rectangle([request.xmin, request.ymin, request.xmax, request.ymax], grid_spec.crs, False)
            rect = pottery_image.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            tile = np.array(rect["properties"][REPORT_POTTERY_NAME], dtype=np.float32)[: request.size, : request.size]
            if tile.shape != (request.size, request.size):
                raise StageError(
                    f"EE notebook report Pottery tile ({request.tile_row},{request.tile_col}) returned shape {tile.shape}, "
                    f"expected {(request.size, request.size)}."
                )
            row_start = request.tile_row * request.size
            col_start = request.tile_col * request.size
            array[row_start : row_start + request.size, col_start : col_start + request.size] = tile
        return array

    return fetch_pottery


def create_ee_notebook_report_mass_fetcher(settings, grid_spec: GridSpec) -> ReportMassFetcher:
    initialize_ee_session(settings)
    mass_image = build_notebook_report_mass_image(grid_spec)
    requests = build_dem_tile_requests(grid_spec)

    def fetch_mass(*, grid_spec: GridSpec) -> np.ndarray:
        array = np.full((grid_spec.size, grid_spec.size), grid_spec.nodata, dtype=np.float32)
        for request in requests:
            tile_geo = ee.Geometry.Rectangle([request.xmin, request.ymin, request.xmax, request.ymax], grid_spec.crs, False)
            rect = mass_image.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            tile = np.array(rect["properties"][REPORT_MASS_NAME], dtype=np.float32)[: request.size, : request.size]
            if tile.shape != (request.size, request.size):
                raise StageError(
                    f"EE notebook report Mass tile ({request.tile_row},{request.tile_col}) returned shape {tile.shape}, "
                    f"expected {(request.size, request.size)}."
                )
            row_start = request.tile_row * request.size
            col_start = request.tile_col * request.size
            array[row_start : row_start + request.size, col_start : col_start + request.size] = tile
        return array

    return fetch_mass


def write_report_640_output(
    run_dir: Path, grid_spec: GridSpec, name: str, array: np.ndarray
) -> Path:
    tif_path = run_dir / f"{name}.tif"
    write_georeferenced_raster(tif_path, array, grid_spec)
    write_raster_sidecar(
        tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=array.shape[:2],
    )
    return tif_path


def write_report_640_manifest(
    run_dir: Path,
    *,
    implemented: list[dict],
    not_implemented: list[dict],
) -> Path:
    qa_dir = ensure_run_qa_dir(run_dir)
    qa_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = qa_dir / REPORT_640_MANIFEST_NAME
    reports: dict[str, dict] = {}
    for item in implemented:
        reports[item["filename"]] = {
            "status": "implemented",
            "formula": item["formula"],
            "source_equivalent": item.get("source_equivalent"),
            "source_provenance": item.get("source_provenance"),
        }
    for item in not_implemented:
        reports[item["filename"]] = {
            "status": "not_implemented_no_source_equivalent",
            "source_equivalent": None,
            "reason": item["reason"],
        }
    payload = {
        "schema": "notebook_report_640_manifest_v1",
        "stage": "report_640",
        "reports": reports,
    }
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest_path


class Report640Stage(Stage):
    """Compute REPORT_640 rasters from persisted pipeline outputs."""

    name = "report_640"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(
        self,
        *,
        grid_spec: GridSpec,
        pottery_fetcher: ReportPotteryFetcher | None = None,
        mass_fetcher: ReportMassFetcher | None = None,
    ) -> None:
        self.grid_spec = grid_spec
        self.pottery_fetcher = pottery_fetcher
        self.mass_fetcher = mass_fetcher

    async def run(self, context: StageContext) -> StageResult:
        nodata = self.grid_spec.nodata
        s2_cube = load_s2_raw_cube(context.run_dir)
        st_b10_raw = load_st_b10_raw(context.run_dir)

        implemented_specs: list[dict] = []
        artifacts = []
        layer_metadata: dict[str, dict] = {}

        # Pottery_Report
        array = self.pottery_fetcher(grid_spec=self.grid_spec) if self.pottery_fetcher is not None else compute_report_pottery_report(s2_cube, nodata=nodata)
        expected_shape = (self.grid_spec.size, self.grid_spec.size)
        if array.shape[:2] != expected_shape:
            raise StageError(f"REPORT_640_Pottery_Report shape {array.shape[:2]} != expected {expected_shape}")
        tif_path = write_report_640_output(
            context.run_dir, self.grid_spec, "REPORT_640_Pottery_Report", array
        )
        artifacts.append(
            build_stage_artifact(
                name="REPORT_640_Pottery_Report",
                relative_path=tif_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=tif_path.stat().st_size,
            )
        )
        implemented_specs.append({
            "filename": "REPORT_640_Pottery_Report.tif",
            "formula": "B12 / B11",
            "source_equivalent": "notebook_report_s2" if self.pottery_fetcher is not None else "s2_raw_cube.npy",
            "source_provenance": "notebook_report_s2" if self.pottery_fetcher is not None else "s2_raw",
        })
        layer_metadata["REPORT_640_Pottery_Report"] = {
            "status": "implemented",
            "formula": "B12 / B11",
            "source_provenance": "notebook_report_s2" if self.pottery_fetcher is not None else "s2_raw",
        }

        # Mass_Report
        array = self.mass_fetcher(grid_spec=self.grid_spec) if self.mass_fetcher is not None else compute_report_mass_report(s2_cube, st_b10_raw, nodata=nodata)
        if array.shape[:2] != expected_shape:
            raise StageError(f"REPORT_640_Mass_Report shape {array.shape[:2]} != expected {expected_shape}")
        tif_path = write_report_640_output(
            context.run_dir, self.grid_spec, "REPORT_640_Mass_Report", array
        )
        artifacts.append(
            build_stage_artifact(
                name="REPORT_640_Mass_Report",
                relative_path=tif_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=tif_path.stat().st_size,
            )
        )
        implemented_specs.append({
            "filename": "REPORT_640_Mass_Report.tif",
            "formula": "B12 * ST_B10 / 1000",
            "source_equivalent": "notebook_report_s2 + notebook_l9_st_b10" if self.mass_fetcher is not None else f"{S2_RAW_CUBE_NPY_NAME} + {RAW_ST_B10_NPY_NAME}",
            "source_provenance": "notebook_report_s2_l9_st_b10" if self.mass_fetcher is not None else "s2_raw_st_b10_raw",
        })
        layer_metadata["REPORT_640_Mass_Report"] = {
            "status": "implemented",
            "formula": "B12 * ST_B10 / 1000",
            "source_provenance": "notebook_report_s2_l9_st_b10" if self.mass_fetcher is not None else "s2_raw_st_b10_raw",
        }

        # FINAL_Zero_Point_Targets
        array = compute_report_zero_point_targets(s2_cube, nodata=nodata)
        if array.shape[:2] != expected_shape:
            raise StageError(f"REPORT_640_FINAL_Zero_Point_Targets shape {array.shape[:2]} != expected {expected_shape}")
        tif_path = write_report_640_output(
            context.run_dir, self.grid_spec, "REPORT_640_FINAL_Zero_Point_Targets", array
        )
        artifacts.append(
            build_stage_artifact(
                name="REPORT_640_FINAL_Zero_Point_Targets",
                relative_path=tif_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=tif_path.stat().st_size,
            )
        )
        implemented_specs.append({
            "filename": "REPORT_640_FINAL_Zero_Point_Targets.tif",
            "formula": "threshold_intersection(GoldAlloy>1.45, IronOxide>1.25, VegRoot>0.35)",
            "source_equivalent": "s2_raw_cube.npy",
        })
        layer_metadata["REPORT_640_FINAL_Zero_Point_Targets"] = {
            "status": "implemented",
            "formula": "threshold_intersection(GoldAlloy>1.45, IronOxide>1.25, VegRoot>0.35)",
        }

        manifest_path = write_report_640_manifest(
            context.run_dir,
            implemented=implemented_specs,
            not_implemented=[],
        )
        artifacts.append(
            build_stage_artifact(
                name="REPORT_640_manifest",
                relative_path=manifest_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=manifest_path.stat().st_size,
                http_servable=False,
            )
        )

        return StageResult(
            artifacts=artifacts,
            metadata={
                "implemented_reports": [spec["filename"] for spec in implemented_specs],
                "not_implemented_reports": [],
                "report_details": layer_metadata,
            },
        )
