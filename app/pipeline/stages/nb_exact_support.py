from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import ee
import numpy as np

from app.db.models.enums import ArtifactClass
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.dem import DEM_TILE_SIZE
from app.pipeline.stages.grid import GridSpec
from app.services.ee_session import initialize_ee_session
from app.services.nb_exact_support import (
    ASC_DESC_CONSISTENCY_FILENAME,
    MIN_ROBUST_NORM_VALID_PIXELS,
    THERMAL_DELTA_FILENAME,
    ExactNotebookSupportUnavailable,
    compute_asc_desc_consistency,
    notebook_robust_norm01,
    write_exact_support_raster,
)

S1_COLLECTION_ID = "COPERNICUS/S1_GRD"
S1_START_DATE = "2022-01-01"
S1_END_DATE = "2026-03-01"
THERMAL_START_DATE = "2022-01-01"
THERMAL_END_DATE = "2026-04-28"
LANDSAT_8_COLLECTION_ID = "LANDSAT/LC08/C02/T1_L2"
LANDSAT_9_COLLECTION_ID = "LANDSAT/LC09/C02/T1_L2"
MODIS_TERRA_COLLECTION_ID = "MODIS/061/MOD11A1"
MODIS_AQUA_COLLECTION_ID = "MODIS/061/MYD11A1"
THERMAL_EXPORT_SCALE_M = 1000

ASC_VV_BAND = "S1_ASC_VV_Filtered"
ASC_VH_BAND = "S1_ASC_VH_Filtered"
DESC_VV_BAND = "S1_DESC_VV_Filtered"
DESC_VH_BAND = "S1_DESC_VH_Filtered"
THERMAL_DELTA_RAW_BAND = "THERMAL_DELTA_DAY_NIGHT_PROXY"


@dataclass(frozen=True, slots=True)
class NotebookSupportInputs:
    asc_vv: np.ndarray
    asc_vh: np.ndarray
    desc_vv: np.ndarray
    desc_vh: np.ndarray
    thermal_delta_raw: np.ndarray
    source_counts: dict[str, int]


class NotebookSupportFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> NotebookSupportInputs: ...


def _grid_region(grid_spec: GridSpec):
    bounds = grid_spec.manifest.bounds_m
    return ee.Geometry.Rectangle(
        [bounds["xmin"], bounds["ymin"], bounds["xmax"], bounds["ymax"]],
        grid_spec.crs,
        False,
    )


def _finalize_for_sample(image, grid_spec: GridSpec):
    return (
        ee.Image(image)
        .toFloat()
        .unmask(grid_spec.nodata)
        .reproject(crs=grid_spec.crs, crsTransform=list(grid_spec.transform))
        .clip(_grid_region(grid_spec))
    )


def _sample_multiband(image, *, band_names: list[str], grid_spec: GridSpec) -> dict[str, np.ndarray]:
    arrays = {
        name: np.full((grid_spec.size, grid_spec.size), grid_spec.nodata, dtype=np.float32)
        for name in band_names
    }
    bounds = grid_spec.manifest.bounds_m
    scale = float(grid_spec.manifest.scale_m)
    xmin = float(bounds["xmin"])
    ymax = float(bounds["ymax"])

    for row_start in range(0, grid_spec.size, DEM_TILE_SIZE):
        for col_start in range(0, grid_spec.size, DEM_TILE_SIZE):
            tile_height = min(DEM_TILE_SIZE, grid_spec.size - row_start)
            tile_width = min(DEM_TILE_SIZE, grid_spec.size - col_start)
            x0 = xmin + col_start * scale
            x1 = x0 + tile_width * scale
            y1 = ymax - row_start * scale
            y0 = y1 - tile_height * scale
            tile_geo = ee.Geometry.Rectangle([x0, y0, x1, y1], grid_spec.crs, False)
            rect = image.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            for band_name in band_names:
                tile = np.asarray(rect["properties"][band_name], dtype=np.float32)[:tile_height, :tile_width]
                if tile.shape != (tile_height, tile_width):
                    raise ExactNotebookSupportUnavailable("ee_tile_shape_mismatch")
                arrays[band_name][
                    row_start : row_start + tile_height,
                    col_start : col_start + tile_width,
                ] = tile
    return arrays


def _speckle_filter(image):
    # Earth Engine copyProperties returns Element even when the destination is an
    # Image. Re-wrap it so downstream Image methods such as rename remain valid.
    filtered = image.focalMean(radius=1.5, kernelType="circle", units="pixels")
    return ee.Image(filtered.copyProperties(image, image.propertyNames()))


def _prep_landsat_l2(image):
    qa = image.select("QA_PIXEL")
    cloud_shadow = qa.bitwiseAnd(1 << 4).eq(0)
    clouds = qa.bitwiseAnd(1 << 3).eq(0)
    cirrus = qa.bitwiseAnd(1 << 2).eq(0)
    mask = cloud_shadow.And(clouds).And(cirrus)
    lst_k = image.select("ST_B10").multiply(0.00341802).add(149.0).rename("LST_DAY_K_LANDSAT")
    return ee.Image(lst_k.updateMask(mask).copyProperties(image, ["system:time_start"]))


def _prep_modis_night(image):
    night = image.select("LST_Night_1km").multiply(0.02).rename("LST_NIGHT_K_MODIS_PROXY")
    mask = night.gt(200).And(night.lt(340))
    return ee.Image(night.updateMask(mask).copyProperties(image, ["system:time_start"]))


def _collection_count(collection) -> int:
    return int(collection.size().getInfo())


def create_ee_notebook_support_fetcher(settings, grid_spec: GridSpec) -> NotebookSupportInputs:
    """Fetch source-equivalent inputs for the exact new.ipynb support formulas.

    This reproduces notebook Cell 108 Sentinel-1 selection/filtering and Stage 2C
    Landsat-day/MODIS-night delta sourcing. It does not run or alter the app classifier.
    """
    initialize_ee_session(settings)
    region = _grid_region(grid_spec)

    s1 = (
        ee.ImageCollection(S1_COLLECTION_ID)
        .filterBounds(region)
        .filterDate(S1_START_DATE, S1_END_DATE)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
    )
    asc_collection = s1.filter(ee.Filter.eq("orbitProperties_pass", "ASCENDING")).sort("system:time_start", False)
    desc_collection = s1.filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING")).sort("system:time_start", False)

    l8 = ee.ImageCollection(LANDSAT_8_COLLECTION_ID).filterBounds(region).filterDate(THERMAL_START_DATE, THERMAL_END_DATE)
    l9 = ee.ImageCollection(LANDSAT_9_COLLECTION_ID).filterBounds(region).filterDate(THERMAL_START_DATE, THERMAL_END_DATE)
    landsat = l8.merge(l9).map(_prep_landsat_l2)
    terra_night = (
        ee.ImageCollection(MODIS_TERRA_COLLECTION_ID)
        .filterBounds(region)
        .filterDate(THERMAL_START_DATE, THERMAL_END_DATE)
        .map(_prep_modis_night)
    )
    aqua_night = (
        ee.ImageCollection(MODIS_AQUA_COLLECTION_ID)
        .filterBounds(region)
        .filterDate(THERMAL_START_DATE, THERMAL_END_DATE)
        .map(_prep_modis_night)
    )
    modis_night = terra_night.merge(aqua_night)

    source_counts = {
        "s1_ascending": _collection_count(asc_collection),
        "s1_descending": _collection_count(desc_collection),
        "landsat_day": _collection_count(landsat),
        "modis_night": _collection_count(modis_night),
    }
    if any(count < 1 for count in source_counts.values()):
        raise ExactNotebookSupportUnavailable("required_notebook_source_collection_empty")

    asc_image = ee.Image(asc_collection.first())
    desc_image = ee.Image(desc_collection.first())
    s1_stack = ee.Image.cat(
        [
            _speckle_filter(asc_image.select("VV")).rename(ASC_VV_BAND),
            _speckle_filter(asc_image.select("VH")).rename(ASC_VH_BAND),
            _speckle_filter(desc_image.select("VV")).rename(DESC_VV_BAND),
            _speckle_filter(desc_image.select("VH")).rename(DESC_VH_BAND),
        ]
    )
    s1_arrays = _sample_multiband(
        _finalize_for_sample(s1_stack, grid_spec),
        band_names=[ASC_VV_BAND, ASC_VH_BAND, DESC_VV_BAND, DESC_VH_BAND],
        grid_spec=grid_spec,
    )

    lst_day = landsat.median().rename("LST_DAY_K_LANDSAT")
    lst_night_proxy = modis_night.median().rename("LST_NIGHT_K_MODIS_PROXY")
    thermal_delta = lst_day.subtract(lst_night_proxy).rename(THERMAL_DELTA_RAW_BAND)
    # The notebook exports this proxy at 1000 m, then bilinearly forces it to
    # the exact 10 m reference grid before robust normalization.
    thermal_delta = (
        thermal_delta.toFloat()
        .reproject(crs=grid_spec.crs, scale=THERMAL_EXPORT_SCALE_M)
        .resample("bilinear")
        .reproject(crs=grid_spec.crs, crsTransform=list(grid_spec.transform))
        .clip(region)
    )
    thermal_array = _sample_multiband(
        _finalize_for_sample(thermal_delta, grid_spec),
        band_names=[THERMAL_DELTA_RAW_BAND],
        grid_spec=grid_spec,
    )[THERMAL_DELTA_RAW_BAND]

    return NotebookSupportInputs(
        asc_vv=s1_arrays[ASC_VV_BAND],
        asc_vh=s1_arrays[ASC_VH_BAND],
        desc_vv=s1_arrays[DESC_VV_BAND],
        desc_vh=s1_arrays[DESC_VH_BAND],
        thermal_delta_raw=thermal_array,
        source_counts=source_counts,
    )


def _resolve_support_inputs(
    *,
    settings,
    grid_spec: GridSpec,
    support_fetcher: NotebookSupportFetcher | None,
) -> NotebookSupportInputs:
    if support_fetcher is not None:
        return support_fetcher(grid_spec=grid_spec)
    return create_ee_notebook_support_fetcher(settings, grid_spec)


def _valid_count(array: np.ndarray, *, nodata: float) -> int:
    return int((np.isfinite(array) & (array != np.float32(nodata))).sum())


def _validate_inputs(inputs: NotebookSupportInputs, *, grid_spec: GridSpec) -> None:
    expected_shape = (grid_spec.size, grid_spec.size)
    arrays = {
        "asc_vv": inputs.asc_vv,
        "asc_vh": inputs.asc_vh,
        "desc_vv": inputs.desc_vv,
        "desc_vh": inputs.desc_vh,
        "thermal_delta_raw": inputs.thermal_delta_raw,
    }
    for name, array in arrays.items():
        if array.shape != expected_shape:
            raise ExactNotebookSupportUnavailable(f"{name}_shape_mismatch")
        if _valid_count(array, nodata=grid_spec.nodata) < MIN_ROBUST_NORM_VALID_PIXELS:
            raise ExactNotebookSupportUnavailable(f"{name}_insufficient_valid_pixels")


class NbExactSupportStage(Stage):
    name = "nb_exact_support"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(
        self,
        *,
        grid_spec: GridSpec,
        support_fetcher: NotebookSupportFetcher | None = None,
    ) -> None:
        self.grid_spec = grid_spec
        self.support_fetcher = support_fetcher

    async def run(self, context: StageContext) -> StageResult:
        try:
            inputs = _resolve_support_inputs(
                settings=context.settings,
                grid_spec=self.grid_spec,
                support_fetcher=self.support_fetcher,
            )
            _validate_inputs(inputs, grid_spec=self.grid_spec)

            asc_desc_consistency = compute_asc_desc_consistency(
                asc_vv=inputs.asc_vv,
                asc_vh=inputs.asc_vh,
                desc_vv=inputs.desc_vv,
                desc_vh=inputs.desc_vh,
                nodata=self.grid_spec.nodata,
            )
            thermal_delta = notebook_robust_norm01(inputs.thermal_delta_raw, nodata=self.grid_spec.nodata)

            asc_path = write_exact_support_raster(
                context.run_dir,
                grid_spec=self.grid_spec,
                filename=ASC_DESC_CONSISTENCY_FILENAME,
                array=asc_desc_consistency,
            )
            thermal_path = write_exact_support_raster(
                context.run_dir,
                grid_spec=self.grid_spec,
                filename=THERMAL_DELTA_FILENAME,
                array=thermal_delta,
            )
            artifacts = [
                build_stage_artifact(
                    name="nb_exact_asc_desc_consistency",
                    relative_path=asc_path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=asc_path.stat().st_size,
                    http_servable=False,
                ),
                build_stage_artifact(
                    name="nb_exact_thermal_delta",
                    relative_path=thermal_path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=thermal_path.stat().st_size,
                    http_servable=False,
                ),
            ]
            return StageResult(
                artifacts=artifacts,
                metadata={
                    "status": "available",
                    "source": "new.ipynb",
                    "classifier_modified": False,
                    "source_counts": inputs.source_counts,
                    "s1_date_window": [S1_START_DATE, S1_END_DATE],
                    "thermal_date_window": [THERMAL_START_DATE, THERMAL_END_DATE],
                    "thermal_night_support": "MODIS_1KM_PROXY_DOWNSCALED_TO_RUN_GRID",
                    "support_bands": ["FS_ASC_DESC_CONSISTENCY_640", "THERMAL_DELTA_DAY_NIGHT_PROXY"],
                },
            )
        except Exception as exc:
            # N8 support is additive only. Missing EE data/support must never make
            # the core run or classifier fail; nb_results will continue to abstain.
            return StageResult(
                artifacts=[],
                metadata={
                    "status": "not_available",
                    "source": "new.ipynb",
                    "classifier_modified": False,
                    "reason": "exact_notebook_support_unavailable",
                    "error_type": type(exc).__name__,
                },
            )
