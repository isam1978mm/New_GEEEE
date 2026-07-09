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
from app.pipeline.stages.dem import DEM_TILE_SIZE, raster_sidecar_path, write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.services.ee_session import initialize_ee_session

DEFAULT_START = "2022-01-01"
DEFAULT_END = "2026-02-28"
DEFAULT_S2_CLOUD_MAX = 3
FUSION_REPORT_CLOUD_MAX = 10
S2_SR_REFLECTANCE_SCALE = 0.0001
S2_SOURCE_BANDS = ("B2", "B3", "B4", "B8", "B11", "B12", "B1")
INDEX_NAMES = ("NDVI", "NDWI", "NDMI", "NBR", "IRONOX", "IRON_SWIR", "BSI")
S2_RAW_CUBE_NPY_NAME = "s2_raw_cube.npy"
S2_MASK_OUTPUT_DIR = "S2_MASKS"
S2_RAW_VALID_MASK_TIF = "S2_RAW_VALID_MASK_640.tif"
S2_INDEX_VALID_MASK_TIF = "S2_INDEX_VALID_MASK_640.tif"
S2_DEM_MATCHED_MASK_MANIFEST_JSON = "S2_DEM_MATCHED_MASKS_manifest.json"
NOTEBOOK_STACK_OUTPUT_DIR = "NPY_STACKS"
NOTEBOOK_SAR_GEOTIFF_OUTPUT_DIR = "GEOTIFF_RADAR_BANDS"
NOTEBOOK_SAR_NPY_OUTPUT_DIR = "NPY_RADAR_BANDS"
NOTEBOOK_STACK_ALIAS_MANIFEST_JSON = "STACK_ALIAS_MANIFEST.json"
AIX_TIME_TAG = "2022_2026_CLOUDLT3"
AIX_EXTRA_TENSORS_STACK_NPY = f"AIX_{AIX_TIME_TAG}_EXTRA_TENSORS_STACK_640.npy"
AIX_MONTH_WINDOWS = {
    "Jan": (1, 1, 31),
    "Apr": (4, 1, 30),
    "Aug": (8, 1, 31),
}
AIX_EXTRA_TENSOR_BANDS = (
    f"AIX_{AIX_TIME_TAG}_Jan_IronOxideProxy_Norm01",
    f"AIX_{AIX_TIME_TAG}_Jan_MineralAlterationProxy_Norm01",
    f"AIX_{AIX_TIME_TAG}_Jan_ThermalAnomaly_Norm01",
    f"AIX_{AIX_TIME_TAG}_Apr_IronOxideProxy_Norm01",
    f"AIX_{AIX_TIME_TAG}_Apr_MineralAlterationProxy_Norm01",
    f"AIX_{AIX_TIME_TAG}_Apr_ThermalAnomaly_Norm01",
    f"AIX_{AIX_TIME_TAG}_Aug_IronOxideProxy_Norm01",
    f"AIX_{AIX_TIME_TAG}_Aug_MineralAlterationProxy_Norm01",
    f"AIX_{AIX_TIME_TAG}_Aug_ThermalAnomaly_Norm01",
    f"AIX_{AIX_TIME_TAG}_Elevation_Norm01",
    f"AIX_{AIX_TIME_TAG}_Slope_Norm01",
    f"AIX_{AIX_TIME_TAG}_Aspect_Norm01",
    f"AIX_{AIX_TIME_TAG}_Hillshade_Norm01",
)
AIX_DEM_MASK_TIME_TAG = "2022_2026FEB_CLOUDLT3"
AIX_DEM_MATCHED_MASKS_STACK_NPY = f"AIX_{AIX_DEM_MASK_TIME_TAG}_DEM_MATCHED_MASKS_STACK_640.npy"
AIX_DEM_MATCHED_MASK_BANDS = (
    f"AIX_{AIX_DEM_MASK_TIME_TAG}_MaskVegetationRoots_Norm01",
    f"AIX_{AIX_DEM_MASK_TIME_TAG}_MaskWaterMoisture_Norm01",
    f"AIX_{AIX_DEM_MASK_TIME_TAG}_IndexIronOxide_Norm01",
    f"AIX_{AIX_DEM_MASK_TIME_TAG}_IndexFerricIron_Norm01",
    f"AIX_{AIX_DEM_MASK_TIME_TAG}_IndexClayThermal_Norm01",
    f"AIX_{AIX_DEM_MASK_TIME_TAG}_MaskCharcoalLead_Norm01",
    f"AIX_{AIX_DEM_MASK_TIME_TAG}_MaskQuartzBasalt_Norm01",
    f"AIX_{AIX_DEM_MASK_TIME_TAG}_MaskCarbonate_Norm01",
    f"AIX_{AIX_DEM_MASK_TIME_TAG}_ThermalTimeSeriesAnomaly_Norm01",
)
FUSION_INTELLIGENCE_STACK_NPY = "REPORT_640_FINAL_INTELLIGENCE_STACK_640.npy"
FUSION_INTELLIGENCE_BANDS = (
    "REPORT_640_FINAL_Zero_Point_Targets",
    "REPORT_640_Mass_Report",
    "REPORT_640_Pottery_Report",
)
TESLA_ATOMIC_INFERENCE_STACK_NPY = "TESLA_V7_2_ATOMIC_INFERENCE_STACK_640.npy"
TESLA_ATOMIC_INFERENCE_BANDS = (
    "AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640",
    "AI_BEH_Artifacts_Jars_Chests_DOM_lin_640",
    "AI_BEH_Mercury_RareChemicals_DOM_lin_640",
    "AI_BEH_Gemstones_AncientGlass_DOM_lin_640",
    "AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640",
)


class S2CubeFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray: ...


class AIXExtraTensorFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray: ...


class AIXDemMatchedMaskFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray: ...


class FusionIntelligenceFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray: ...


class TeslaAtomicInferenceFetcher(Protocol):
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



def prep_landsat_st_b10_masked(img):
    qa = img.select("QA_PIXEL")
    cloud_shadow = qa.bitwiseAnd(1 << 4).eq(0)
    clouds = qa.bitwiseAnd(1 << 3).eq(0)
    cirrus = qa.bitwiseAnd(1 << 2).eq(0)
    mask = cloud_shadow.And(clouds).And(cirrus)
    return img.select("ST_B10").updateMask(mask).copyProperties(img, ["system:time_start"])


def build_aix_s2_month_composite(
    grid_spec: GridSpec,
    *,
    month_num: int,
    day_start: int,
    day_end: int,
    start_year: int = 2022,
    end_year: int = 2026,
    cloud_max: int = DEFAULT_S2_CLOUD_MAX,
):
    col = ee.ImageCollection([])
    region = build_grid_region(grid_spec)
    for year in range(start_year, end_year + 1):
        start = ee.Date.fromYMD(year, month_num, day_start)
        end = ee.Date.fromYMD(year, month_num, day_end).advance(1, "day")
        sub = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_max))
            .select(["B3", "B4", "B11", "B12"])
        )
        col = col.merge(sub)
    return col.median()


def build_aix_landsat_thermal_month_composite(
    grid_spec: GridSpec,
    *,
    month_num: int,
    day_start: int,
    day_end: int,
    start_year: int = 2022,
    end_year: int = 2026,
):
    col = ee.ImageCollection([])
    region = build_grid_region(grid_spec)
    for year in range(start_year, end_year + 1):
        start = ee.Date.fromYMD(year, month_num, day_start)
        end = ee.Date.fromYMD(year, month_num, day_end).advance(1, "day")
        l9 = (
            ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
            .filterBounds(region)
            .filterDate(start, end)
            .map(prep_landsat_st_b10_masked)
        )
        l8 = (
            ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filterBounds(region)
            .filterDate(start, end)
            .map(prep_landsat_st_b10_masked)
        )
        col = col.merge(l9).merge(l8)
    return col.median()


def build_aix_extra_tensor_image(grid_spec: GridSpec):
    region = build_grid_region(grid_spec)
    band_images = []
    for tag, (month_num, day_start, day_end) in AIX_MONTH_WINDOWS.items():
        s2 = build_aix_s2_month_composite(
            grid_spec,
            month_num=month_num,
            day_start=day_start,
            day_end=day_end,
        )
        thermal = build_aix_landsat_thermal_month_composite(
            grid_spec,
            month_num=month_num,
            day_start=day_start,
            day_end=day_end,
        )

        band_images.extend(
            [
                s2.select("B4").divide(s2.select("B3")).unitScale(0, 2).rename(
                    f"AIX_{AIX_TIME_TAG}_{tag}_IronOxideProxy_Norm01"
                ),
                s2.select("B11").divide(s2.select("B12")).unitScale(0, 2).rename(
                    f"AIX_{AIX_TIME_TAG}_{tag}_MineralAlterationProxy_Norm01"
                ),
                thermal.select("ST_B10")
                .multiply(0.00341802)
                .add(149.0)
                .unitScale(280, 320)
                .rename(
                    f"AIX_{AIX_TIME_TAG}_{tag}_ThermalAnomaly_Norm01"
                ),
            ]
        )

    topo_dem = ee.ImageCollection("COPERNICUS/DEM/GLO30").filterBounds(region).first().select("DEM")
    slope = ee.Terrain.slope(topo_dem)
    aspect = ee.Terrain.aspect(topo_dem)
    hillshade = ee.Terrain.hillshade(topo_dem)

    band_images.extend(
        [
            topo_dem.unitScale(0, 3000).rename(f"AIX_{AIX_TIME_TAG}_Elevation_Norm01"),
            slope.unitScale(0, 45).rename(f"AIX_{AIX_TIME_TAG}_Slope_Norm01"),
            aspect.unitScale(0, 360).rename(f"AIX_{AIX_TIME_TAG}_Aspect_Norm01"),
            hillshade.unitScale(0, 255).rename(f"AIX_{AIX_TIME_TAG}_Hillshade_Norm01"),
        ]
    )

    return ee.Image.cat(band_images).rename(list(AIX_EXTRA_TENSOR_BANDS))


def build_aix_dem_matched_mask_image(grid_spec: GridSpec):
    region = build_grid_region(grid_spec)
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate("2022-01-01", "2026-02-28")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 3))
        .select(["B1", "B2", "B3", "B4", "B5", "B8", "B11", "B12"])
        .median()
    )

    l8 = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(region)
        .filterDate("2022-01-01", "2026-02-28")
        .map(prep_landsat_st_b10_masked)
        .median()
    )
    l9 = (
        ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
        .filterBounds(region)
        .filterDate("2022-01-01", "2026-02-28")
        .map(prep_landsat_st_b10_masked)
        .median()
    )
    thermal = ee.ImageCollection([l8.select("ST_B10"), l9.select("ST_B10")]).median()

    return ee.Image.cat(
        [
            s2.normalizedDifference(["B8", "B4"]).unitScale(-1, 1).rename(
                f"AIX_{AIX_DEM_MASK_TIME_TAG}_MaskVegetationRoots_Norm01"
            ),
            s2.normalizedDifference(["B3", "B8"]).unitScale(-1, 1).rename(
                f"AIX_{AIX_DEM_MASK_TIME_TAG}_MaskWaterMoisture_Norm01"
            ),
            s2.select("B4").divide(s2.select("B3")).unitScale(0, 5).rename(
                f"AIX_{AIX_DEM_MASK_TIME_TAG}_IndexIronOxide_Norm01"
            ),
            s2.select("B4").divide(s2.select("B1")).unitScale(0, 5).rename(
                f"AIX_{AIX_DEM_MASK_TIME_TAG}_IndexFerricIron_Norm01"
            ),
            s2.select("B11").divide(s2.select("B12")).unitScale(0, 5).rename(
                f"AIX_{AIX_DEM_MASK_TIME_TAG}_IndexClayThermal_Norm01"
            ),
            s2.normalizedDifference(["B8", "B12"]).unitScale(-1, 1).rename(
                f"AIX_{AIX_DEM_MASK_TIME_TAG}_MaskCharcoalLead_Norm01"
            ),
            s2.select("B12").divide(s2.select("B11")).unitScale(0, 5).rename(
                f"AIX_{AIX_DEM_MASK_TIME_TAG}_MaskQuartzBasalt_Norm01"
            ),
            s2.select("B11").add(s2.select("B4")).divide(s2.select("B8")).unitScale(0, 5).rename(
                f"AIX_{AIX_DEM_MASK_TIME_TAG}_MaskCarbonate_Norm01"
            ),
            thermal.select("ST_B10").multiply(0.00341802).add(149.0).unitScale(280, 320).rename(
                f"AIX_{AIX_DEM_MASK_TIME_TAG}_ThermalTimeSeriesAnomaly_Norm01"
            ),
        ]
    ).rename(list(AIX_DEM_MATCHED_MASK_BANDS))


def build_fusion_intelligence_image(grid_spec: GridSpec):
    region = build_grid_region(grid_spec)
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate("2022-01-01", "2026-02-28")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", FUSION_REPORT_CLOUD_MAX))
        .select(["B1", "B2", "B3", "B4", "B8", "B8A", "B11", "B12"])
        .median()
    )
    l8 = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(region)
        .filterDate("2022-01-01", "2026-02-28")
        .map(prep_landsat_st_b10_masked)
        .median()
    )
    l9 = (
        ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
        .filterBounds(region)
        .filterDate("2022-01-01", "2026-02-28")
        .map(prep_landsat_st_b10_masked)
        .median()
    )

    tensor_gold_alloy_signal = s2.select("B12").divide(s2.select("B11"))
    tensor_pottery_jars = s2.select("B11").divide(s2.select("B8A"))
    mask_carbon_age_indicator = s2.select("B12").subtract(s2.select("B8")).multiply(S2_SR_REFLECTANCE_SCALE)
    mask_quartz_basalt = s2.select("B12").divide(s2.select("B11"))
    tensor_mass_volume_shadow = s2.select("B12").multiply(l9.select("ST_B10")).divide(1000)

    gold_signal = tensor_gold_alloy_signal.gt(1.5)
    void_signal = (
        l8.select("ST_B10")
        .multiply(0.00341802)
        .add(149.0)
        .lt(310)
    )
    hard_target = mask_quartz_basalt.gt(2.0)
    ancient_signal = mask_carbon_age_indicator.gt(0.4)
    final_target_map = gold_signal.And(void_signal).And(hard_target).And(ancient_signal)

    return ee.Image.cat(
        [
            final_target_map.rename("REPORT_640_FINAL_Zero_Point_Targets"),
            tensor_mass_volume_shadow.rename("REPORT_640_Mass_Report"),
            tensor_pottery_jars.rename("REPORT_640_Pottery_Report"),
        ]
    ).rename(list(FUSION_INTELLIGENCE_BANDS))


def build_tesla_atomic_inference_image(grid_spec: GridSpec):
    region = build_grid_region(grid_spec)
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate("2022-01-01", "2026-03-01")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 5))
        .select(["B1", "B2", "B3", "B4", "B8", "B8A", "B11", "B12"])
        .median()
    )

    return ee.Image.cat(
        [
            s2.select("B12").divide(s2.select("B11")).unitScale(1.0, 2.5).rename(
                "AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640"
            ),
            s2.select("B11").divide(s2.select("B8A")).unitScale(0.5, 2.0).rename(
                "AI_BEH_Artifacts_Jars_Chests_DOM_lin_640"
            ),
            s2.select("B1").divide(s2.select("B3")).unitScale(0.8, 1.8).rename(
                "AI_BEH_Mercury_RareChemicals_DOM_lin_640"
            ),
            s2.select("B2").divide(s2.select("B12")).unitScale(0.0, 5.0).rename(
                "AI_BEH_Gemstones_AncientGlass_DOM_lin_640"
            ),
            s2.normalizedDifference(["B4", "B8"]).unitScale(-1.0, 1.0).rename(
                "AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640"
            ),
        ]
    ).rename(list(TESLA_ATOMIC_INFERENCE_BANDS))


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


def create_ee_aix_extra_tensor_fetcher(settings, grid_spec: GridSpec) -> AIXExtraTensorFetcher:
    initialize_ee_session(settings)
    final_for_sample = finalize_for_sample(build_aix_extra_tensor_image(grid_spec), grid_spec)
    requests = build_s2_tile_requests(grid_spec)

    def fetch_cube(*, grid_spec: GridSpec) -> np.ndarray:
        cube = np.full((grid_spec.size, grid_spec.size, len(AIX_EXTRA_TENSOR_BANDS)), grid_spec.nodata, dtype=np.float32)
        for request in requests:
            tile_geo = ee.Geometry.Rectangle([request["xmin"], request["ymin"], request["xmax"], request["ymax"]], grid_spec.crs, False)
            rect = final_for_sample.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            for band_index, band_name in enumerate(AIX_EXTRA_TENSOR_BANDS):
                data = np.array(rect["properties"][band_name], dtype=np.float32)[: DEM_TILE_SIZE, : DEM_TILE_SIZE]
                row_start = request["tile_row"] * DEM_TILE_SIZE
                col_start = request["tile_col"] * DEM_TILE_SIZE
                cube[row_start : row_start + DEM_TILE_SIZE, col_start : col_start + DEM_TILE_SIZE, band_index] = data
        return cube.astype(np.float32, copy=False)

    return fetch_cube


def deterministic_aix_extra_tensor_fetcher(*, grid_spec: GridSpec) -> np.ndarray:
    size = grid_spec.size
    rows, cols = np.indices((size, size), dtype=np.float32)
    row_norm = rows / np.float32(max(size - 1, 1))
    col_norm = cols / np.float32(max(size - 1, 1))

    layers = []
    for month_index, _tag in enumerate(AIX_MONTH_WINDOWS):
        offset = np.float32(month_index) * np.float32(0.05)
        b3 = np.float32(0.20) + col_norm * np.float32(0.03) + offset
        b4 = np.float32(0.30) + row_norm * np.float32(0.04) + offset
        b11 = np.float32(0.42) + row_norm * np.float32(0.02) + offset
        b12 = np.float32(0.26) + col_norm * np.float32(0.02) + offset
        thermal = np.float32(290.0) + row_norm * np.float32(4.0) + col_norm * np.float32(2.0) + offset

        layers.extend(
            [
                (b4 / np.maximum(b3, np.float32(1e-6))) / np.float32(2.0),
                (b11 / np.maximum(b12, np.float32(1e-6))) / np.float32(2.0),
                (thermal - np.float32(280.0)) / np.float32(40.0),
            ]
        )

    elevation = np.float32(1000.0) + rows * np.float32(0.5) + cols * np.float32(0.25)
    slope = np.full((size, size), np.float32(3.0), dtype=np.float32)
    aspect = np.full((size, size), np.float32(135.0), dtype=np.float32)
    hillshade = np.full((size, size), np.float32(180.0), dtype=np.float32)

    layers.extend(
        [
            elevation / np.float32(3000.0),
            slope / np.float32(45.0),
            aspect / np.float32(360.0),
            hillshade / np.float32(255.0),
        ]
    )
    return np.stack(layers, axis=-1).astype(np.float32)


def create_ee_aix_dem_matched_mask_fetcher(settings, grid_spec: GridSpec) -> AIXDemMatchedMaskFetcher:
    initialize_ee_session(settings)
    final_for_sample = finalize_for_sample(build_aix_dem_matched_mask_image(grid_spec), grid_spec)
    requests = build_s2_tile_requests(grid_spec)

    def fetch_cube(*, grid_spec: GridSpec) -> np.ndarray:
        cube = np.full((grid_spec.size, grid_spec.size, len(AIX_DEM_MATCHED_MASK_BANDS)), grid_spec.nodata, dtype=np.float32)
        for request in requests:
            tile_geo = ee.Geometry.Rectangle(
                [request["xmin"], request["ymin"], request["xmax"], request["ymax"]],
                grid_spec.crs,
                False,
            )
            rect = final_for_sample.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            for band_index, band_name in enumerate(AIX_DEM_MATCHED_MASK_BANDS):
                data = np.array(rect["properties"][band_name], dtype=np.float32)[: DEM_TILE_SIZE, : DEM_TILE_SIZE]
                row_start = request["tile_row"] * DEM_TILE_SIZE
                col_start = request["tile_col"] * DEM_TILE_SIZE
                cube[row_start : row_start + DEM_TILE_SIZE, col_start : col_start + DEM_TILE_SIZE, band_index] = data
        return cube.astype(np.float32, copy=False)

    return fetch_cube


def deterministic_aix_dem_matched_mask_fetcher(*, grid_spec: GridSpec) -> np.ndarray:
    s2 = deterministic_s2_cube_fetcher(grid_spec=grid_spec)
    b2 = s2[:, :, 0]
    b3 = s2[:, :, 1]
    b4 = s2[:, :, 2]
    b8 = s2[:, :, 3]
    b11 = s2[:, :, 4]
    b12 = s2[:, :, 5]
    b1 = s2[:, :, 6]

    rows, cols = np.indices((grid_spec.size, grid_spec.size), dtype=np.float32)
    row_norm = rows / np.float32(max(grid_spec.size - 1, 1))
    col_norm = cols / np.float32(max(grid_spec.size - 1, 1))
    thermal_st_b10 = (np.float32(290.0) + row_norm * np.float32(4.0) + col_norm * np.float32(2.0) - np.float32(149.0)) / np.float32(0.00341802)

    def nd(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return ((a - b) / np.maximum(a + b, np.float32(1e-6))).astype(np.float32)

    layers = [
        (nd(b8, b4) + np.float32(1.0)) / np.float32(2.0),
        (nd(b3, b8) + np.float32(1.0)) / np.float32(2.0),
        (b4 / np.maximum(b3, np.float32(1e-6))) / np.float32(5.0),
        (b4 / np.maximum(b1, np.float32(1e-6))) / np.float32(5.0),
        (b11 / np.maximum(b12, np.float32(1e-6))) / np.float32(5.0),
        (nd(b8, b12) + np.float32(1.0)) / np.float32(2.0),
        (b12 / np.maximum(b11, np.float32(1e-6))) / np.float32(5.0),
        ((b11 + b4) / np.maximum(b8, np.float32(1e-6))) / np.float32(5.0),
        ((thermal_st_b10 * np.float32(0.00341802) + np.float32(149.0)) - np.float32(280.0)) / np.float32(40.0),
    ]
    return np.stack(layers, axis=-1).astype(np.float32)


def create_ee_fusion_intelligence_fetcher(settings, grid_spec: GridSpec) -> FusionIntelligenceFetcher:
    initialize_ee_session(settings)
    final_for_sample = finalize_for_sample(build_fusion_intelligence_image(grid_spec), grid_spec)
    requests = build_s2_tile_requests(grid_spec)

    def fetch_cube(*, grid_spec: GridSpec) -> np.ndarray:
        cube = np.full((grid_spec.size, grid_spec.size, len(FUSION_INTELLIGENCE_BANDS)), grid_spec.nodata, dtype=np.float32)
        for request in requests:
            tile_geo = ee.Geometry.Rectangle(
                [request["xmin"], request["ymin"], request["xmax"], request["ymax"]],
                grid_spec.crs,
                False,
            )
            rect = final_for_sample.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            for band_index, band_name in enumerate(FUSION_INTELLIGENCE_BANDS):
                data = np.array(rect["properties"][band_name], dtype=np.float32)[: DEM_TILE_SIZE, : DEM_TILE_SIZE]
                row_start = request["tile_row"] * DEM_TILE_SIZE
                col_start = request["tile_col"] * DEM_TILE_SIZE
                cube[row_start : row_start + DEM_TILE_SIZE, col_start : col_start + DEM_TILE_SIZE, band_index] = data
        return cube.astype(np.float32, copy=False)

    return fetch_cube


def deterministic_fusion_intelligence_fetcher(*, grid_spec: GridSpec) -> np.ndarray:
    s2 = deterministic_s2_cube_fetcher(grid_spec=grid_spec)
    b8 = s2[:, :, 3]
    b11 = s2[:, :, 4]
    b12 = s2[:, :, 5]

    rows, cols = np.indices((grid_spec.size, grid_spec.size), dtype=np.float32)
    row_norm = rows / np.float32(max(grid_spec.size - 1, 1))
    col_norm = cols / np.float32(max(grid_spec.size - 1, 1))
    b8a = b8 + np.float32(0.04)
    l8_st_b10 = np.float32(300.0) + row_norm * np.float32(4.0)
    l9_st_b10 = np.float32(301.0) + col_norm * np.float32(3.0)

    gold_signal_value = b12 / np.maximum(b11, np.float32(1e-6))
    pottery_report = b11 / np.maximum(b8a, np.float32(1e-6))
    mass_report = (b12 * l9_st_b10) / np.float32(1000.0)
    carbon_age = b12 - b8
    final_targets = (
        (gold_signal_value > np.float32(1.5))
        & (l8_st_b10 < np.float32(310.0))
        & (gold_signal_value > np.float32(2.0))
        & (carbon_age > np.float32(0.4))
    ).astype(np.float32)

    return np.stack([final_targets, mass_report, pottery_report], axis=-1).astype(np.float32)


def create_ee_tesla_atomic_inference_fetcher(settings, grid_spec: GridSpec) -> TeslaAtomicInferenceFetcher:
    initialize_ee_session(settings)
    final_for_sample = finalize_for_sample(build_tesla_atomic_inference_image(grid_spec), grid_spec)
    requests = build_s2_tile_requests(grid_spec)

    def fetch_cube(*, grid_spec: GridSpec) -> np.ndarray:
        cube = np.full((grid_spec.size, grid_spec.size, len(TESLA_ATOMIC_INFERENCE_BANDS)), grid_spec.nodata, dtype=np.float32)
        for request in requests:
            tile_geo = ee.Geometry.Rectangle(
                [request["xmin"], request["ymin"], request["xmax"], request["ymax"]],
                grid_spec.crs,
                False,
            )
            rect = final_for_sample.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            for band_index, band_name in enumerate(TESLA_ATOMIC_INFERENCE_BANDS):
                data = np.array(rect["properties"][band_name], dtype=np.float32)[: DEM_TILE_SIZE, : DEM_TILE_SIZE]
                row_start = request["tile_row"] * DEM_TILE_SIZE
                col_start = request["tile_col"] * DEM_TILE_SIZE
                cube[row_start : row_start + DEM_TILE_SIZE, col_start : col_start + DEM_TILE_SIZE, band_index] = data
        return cube.astype(np.float32, copy=False)

    return fetch_cube


def deterministic_tesla_atomic_inference_fetcher(*, grid_spec: GridSpec) -> np.ndarray:
    s2 = deterministic_s2_cube_fetcher(grid_spec=grid_spec)
    b2 = s2[:, :, 0]
    b3 = s2[:, :, 1]
    b4 = s2[:, :, 2]
    b8 = s2[:, :, 3]
    b11 = s2[:, :, 4]
    b12 = s2[:, :, 5]
    b1 = s2[:, :, 6]
    b8a = b8 + np.float32(0.04)

    def nd(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return ((a - b) / np.maximum(a + b, np.float32(1e-6))).astype(np.float32)

    layers = [
        ((b12 / np.maximum(b11, np.float32(1e-6))) - np.float32(1.0)) / np.float32(1.5),
        ((b11 / np.maximum(b8a, np.float32(1e-6))) - np.float32(0.5)) / np.float32(1.5),
        ((b1 / np.maximum(b3, np.float32(1e-6))) - np.float32(0.8)) / np.float32(1.0),
        (b2 / np.maximum(b12, np.float32(1e-6))) / np.float32(5.0),
        (nd(b4, b8) + np.float32(1.0)) / np.float32(2.0),
    ]
    return np.stack(layers, axis=-1).astype(np.float32)


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


def compute_s2_dem_matched_masks(cube: np.ndarray, outputs: dict[str, np.ndarray], *, nodata: float) -> dict[str, np.ndarray]:
    raw_valid = np.isfinite(cube).all(axis=-1) & (cube != nodata).all(axis=-1)
    index_valid = np.ones(cube.shape[:2], dtype=bool)
    for name in INDEX_NAMES:
        array = outputs[name]
        index_valid &= np.isfinite(array) & (array != nodata)
    return {
        "raw_valid_mask": raw_valid.astype(np.uint8),
        "index_valid_mask": index_valid.astype(np.uint8),
    }


def write_raster(path: Path, array: np.ndarray) -> None:
    Image.fromarray(array.astype(np.float32)).save(path, format="TIFF")


def write_mask_raster(path: Path, mask: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(mask.astype(np.uint8, copy=False)).save(path, format="TIFF")


def _finite_or_nodata(array: np.ndarray, *, nodata: float) -> np.ndarray:
    return np.where(np.isfinite(array), array, nodata).astype(np.float32)


def _build_aix_extra_tensor_alias() -> dict[str, object]:
    return {
        "filename": AIX_EXTRA_TENSORS_STACK_NPY,
        "source_notebook_family": "AIX_2022_2026_CLOUDLT3_EXTRA_TENSORS_STACK_640",
        "app_artifact": "aix_extra_tensors_stack",
        "band_names": list(AIX_EXTRA_TENSOR_BANDS),
        "status": "implemented",
        "source_cell": "cell_077",
    }


def _build_aix_dem_matched_masks_alias() -> dict[str, object]:
    return {
        "filename": AIX_DEM_MATCHED_MASKS_STACK_NPY,
        "source_notebook_family": "AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640",
        "app_artifact": "aix_dem_matched_masks_stack",
        "band_names": list(AIX_DEM_MATCHED_MASK_BANDS),
        "status": "implemented",
        "source_cell": "cell_081",
    }


def _build_fusion_intelligence_alias() -> dict[str, object]:
    return {
        "filename": FUSION_INTELLIGENCE_STACK_NPY,
        "source_notebook_family": "REPORT_640_FINAL_INTELLIGENCE_STACK_640",
        "app_artifact": "fusion_intelligence_stack",
        "band_names": list(FUSION_INTELLIGENCE_BANDS),
        "status": "implemented",
        "source_cell": "cell_099",
    }


def _build_tesla_atomic_inference_alias() -> dict[str, object]:
    return {
        "filename": TESLA_ATOMIC_INFERENCE_STACK_NPY,
        "source_notebook_family": "PLAN_B19_CELL_095_MATERIAL_STACK_640",
        "app_artifact": "tesla_atomic_inference_stack",
        "band_names": list(TESLA_ATOMIC_INFERENCE_BANDS),
        "status": "implemented",
        "source_cell": "cell_095",
    }


def write_aix_extra_tensor_alias_manifest(stack_dir: Path) -> Path:
    stack_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = stack_dir / NOTEBOOK_STACK_ALIAS_MANIFEST_JSON
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
    else:
        manifest = {}

    manifest.setdefault("schema", "notebook_stack_alias_manifest_v1")
    manifest.setdefault("status", "partial_alias_contract")
    manifest.setdefault("aliases", [])
    manifest.setdefault("deferred_families", [])
    manifest.setdefault("privacy", {"artifact_class": "FILESYSTEM_ONLY", "http_servable": False})

    aliases = [
        _build_aix_extra_tensor_alias(),
        _build_aix_dem_matched_masks_alias(),
        _build_fusion_intelligence_alias(),
        _build_tesla_atomic_inference_alias(),
    ]
    filenames = {alias["filename"] for alias in aliases}
    manifest["aliases"] = [entry for entry in manifest.get("aliases", []) if entry.get("filename") not in filenames]
    manifest["aliases"].extend(aliases)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path


def write_aix_extra_tensor_outputs(run_dir: Path, grid_spec: GridSpec, cube: np.ndarray) -> dict[str, Path]:
    if cube.shape != (grid_spec.size, grid_spec.size, len(AIX_EXTRA_TENSOR_BANDS)):
        raise ValueError(
            f"AIX extra tensor cube shape {cube.shape} does not match expected "
            f"{(grid_spec.size, grid_spec.size, len(AIX_EXTRA_TENSOR_BANDS))}."
        )

    stack_dir = run_dir / NOTEBOOK_STACK_OUTPUT_DIR
    tif_dir = run_dir / NOTEBOOK_SAR_GEOTIFF_OUTPUT_DIR
    npy_dir = run_dir / NOTEBOOK_SAR_NPY_OUTPUT_DIR
    stack_dir.mkdir(parents=True, exist_ok=True)
    tif_dir.mkdir(parents=True, exist_ok=True)
    npy_dir.mkdir(parents=True, exist_ok=True)

    cube = _finite_or_nodata(cube, nodata=grid_spec.nodata)
    stack_path = stack_dir / AIX_EXTRA_TENSORS_STACK_NPY
    np.save(stack_path, cube)

    for band_index, band_name in enumerate(AIX_EXTRA_TENSOR_BANDS):
        band_array = cube[:, :, band_index].astype(np.float32, copy=False)
        tif_path = tif_dir / f"{band_name}_640.tif"
        npy_path = npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(tif_path, band_array, grid_spec)
        write_raster_sidecar(
            tif_path,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(npy_path, band_array)

    alias_manifest_path = write_aix_extra_tensor_alias_manifest(stack_dir)
    return {
        "stack_npy": stack_path,
        "alias_manifest_json": alias_manifest_path,
    }


def write_aix_dem_matched_mask_outputs(run_dir: Path, grid_spec: GridSpec, cube: np.ndarray) -> dict[str, Path]:
    if cube.shape != (grid_spec.size, grid_spec.size, len(AIX_DEM_MATCHED_MASK_BANDS)):
        raise ValueError(
            f"AIX DEM-matched mask cube shape {cube.shape} does not match expected "
            f"{(grid_spec.size, grid_spec.size, len(AIX_DEM_MATCHED_MASK_BANDS))}."
        )

    stack_dir = run_dir / NOTEBOOK_STACK_OUTPUT_DIR
    tif_dir = run_dir / NOTEBOOK_SAR_GEOTIFF_OUTPUT_DIR
    npy_dir = run_dir / NOTEBOOK_SAR_NPY_OUTPUT_DIR
    stack_dir.mkdir(parents=True, exist_ok=True)
    tif_dir.mkdir(parents=True, exist_ok=True)
    npy_dir.mkdir(parents=True, exist_ok=True)

    cube = _finite_or_nodata(cube, nodata=grid_spec.nodata)
    stack_path = stack_dir / AIX_DEM_MATCHED_MASKS_STACK_NPY
    np.save(stack_path, cube)

    for band_index, band_name in enumerate(AIX_DEM_MATCHED_MASK_BANDS):
        band_array = cube[:, :, band_index].astype(np.float32, copy=False)
        tif_path = tif_dir / f"{band_name}_640.tif"
        npy_path = npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(tif_path, band_array, grid_spec)
        write_raster_sidecar(
            tif_path,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(npy_path, band_array)

    alias_manifest_path = write_aix_extra_tensor_alias_manifest(stack_dir)
    return {
        "stack_npy": stack_path,
        "alias_manifest_json": alias_manifest_path,
    }


def write_fusion_intelligence_outputs(run_dir: Path, grid_spec: GridSpec, cube: np.ndarray) -> dict[str, Path]:
    if cube.shape != (grid_spec.size, grid_spec.size, len(FUSION_INTELLIGENCE_BANDS)):
        raise ValueError(
            f"Fusion intelligence cube shape {cube.shape} does not match expected "
            f"{(grid_spec.size, grid_spec.size, len(FUSION_INTELLIGENCE_BANDS))}."
        )

    stack_dir = run_dir / NOTEBOOK_STACK_OUTPUT_DIR
    tif_dir = run_dir / NOTEBOOK_SAR_GEOTIFF_OUTPUT_DIR
    npy_dir = run_dir / NOTEBOOK_SAR_NPY_OUTPUT_DIR
    stack_dir.mkdir(parents=True, exist_ok=True)
    tif_dir.mkdir(parents=True, exist_ok=True)
    npy_dir.mkdir(parents=True, exist_ok=True)

    cube = _finite_or_nodata(cube, nodata=grid_spec.nodata)
    stack_path = stack_dir / FUSION_INTELLIGENCE_STACK_NPY
    np.save(stack_path, cube)

    for band_index, band_name in enumerate(FUSION_INTELLIGENCE_BANDS):
        band_array = cube[:, :, band_index].astype(np.float32, copy=False)
        tif_path = tif_dir / f"{band_name}_640.tif"
        npy_path = npy_dir / f"{band_name}_640.npy"
        write_georeferenced_raster(tif_path, band_array, grid_spec)
        write_raster_sidecar(
            tif_path,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(npy_path, band_array)

    alias_manifest_path = write_aix_extra_tensor_alias_manifest(stack_dir)
    return {
        "stack_npy": stack_path,
        "alias_manifest_json": alias_manifest_path,
    }


def write_tesla_atomic_inference_outputs(run_dir: Path, grid_spec: GridSpec, cube: np.ndarray) -> dict[str, Path]:
    if cube.shape != (grid_spec.size, grid_spec.size, len(TESLA_ATOMIC_INFERENCE_BANDS)):
        raise ValueError(
            f"Tesla atomic inference cube shape {cube.shape} does not match expected "
            f"{(grid_spec.size, grid_spec.size, len(TESLA_ATOMIC_INFERENCE_BANDS))}."
        )

    stack_dir = run_dir / NOTEBOOK_STACK_OUTPUT_DIR
    tif_dir = run_dir / NOTEBOOK_SAR_GEOTIFF_OUTPUT_DIR
    npy_dir = run_dir / NOTEBOOK_SAR_NPY_OUTPUT_DIR
    stack_dir.mkdir(parents=True, exist_ok=True)
    tif_dir.mkdir(parents=True, exist_ok=True)
    npy_dir.mkdir(parents=True, exist_ok=True)

    cube = _finite_or_nodata(cube, nodata=grid_spec.nodata)
    stack_path = stack_dir / TESLA_ATOMIC_INFERENCE_STACK_NPY
    np.save(stack_path, cube)

    for band_index, band_name in enumerate(TESLA_ATOMIC_INFERENCE_BANDS):
        band_array = cube[:, :, band_index].astype(np.float32, copy=False)
        tif_path = tif_dir / f"{band_name}.tif"
        npy_path = npy_dir / f"{band_name}.npy"
        write_georeferenced_raster(tif_path, band_array, grid_spec)
        write_raster_sidecar(
            tif_path,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=band_array.shape,
        )
        np.save(npy_path, band_array)

    alias_manifest_path = write_aix_extra_tensor_alias_manifest(stack_dir)
    return {
        "stack_npy": stack_path,
        "alias_manifest_json": alias_manifest_path,
    }


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


def write_s2_mask_outputs(
    run_dir: Path,
    grid_spec: GridSpec,
    masks: dict[str, np.ndarray],
    *,
    start_date: str,
    end_date: str,
    cloud_max: int,
) -> dict[str, Path]:
    mask_dir = run_dir / S2_MASK_OUTPUT_DIR
    mask_dir.mkdir(parents=True, exist_ok=True)
    raw_valid_path = mask_dir / S2_RAW_VALID_MASK_TIF
    index_valid_path = mask_dir / S2_INDEX_VALID_MASK_TIF
    manifest_path = mask_dir / S2_DEM_MATCHED_MASK_MANIFEST_JSON

    raw_valid = masks["raw_valid_mask"]
    index_valid = masks["index_valid_mask"]
    write_mask_raster(raw_valid_path, raw_valid)
    write_mask_raster(index_valid_path, index_valid)
    for path, mask in ((raw_valid_path, raw_valid), (index_valid_path, index_valid)):
        write_raster_sidecar(
            path,
            grid_manifest=grid_spec.manifest,
            nodata=0.0,
            dtype="uint8",
            shape=mask.shape,
        )

    manifest = {
        "schema": "s2_dem_matched_masks_v1",
        "stage": "s2_indices",
        "coordinate_space": "authoritative_grid",
        "grid_shape": [int(grid_spec.size), int(grid_spec.size)],
        "date_rules": {
            "primary_start": start_date,
            "primary_end": end_date,
            "primary_cloud_max": int(cloud_max),
            "notebook_secret_start": "2022-01-01",
            "notebook_secret_end": "2026-03-01",
            "notebook_secret_cloud_max": 5,
            "notebook_report_start": "2022-01-01",
            "notebook_report_end": "2026-03-01",
            "notebook_report_cloud_max": 10,
        },
        "source_bands": list(S2_SOURCE_BANDS),
        "index_bands": list(INDEX_NAMES),
        "masks": {
            "raw_valid_mask": {
                "path": f"{S2_MASK_OUTPUT_DIR}/{S2_RAW_VALID_MASK_TIF}",
                "valid_fraction": round(float(raw_valid.mean()), 6),
            },
            "index_valid_mask": {
                "path": f"{S2_MASK_OUTPUT_DIR}/{S2_INDEX_VALID_MASK_TIF}",
                "valid_fraction": round(float(index_valid.mean()), 6),
            },
        },
        "privacy": {"artifact_class": "FILESYSTEM_ONLY", "http_servable": False},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "raw_valid_mask_tif": raw_valid_path,
        "index_valid_mask_tif": index_valid_path,
        "mask_manifest_json": manifest_path,
    }


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
        aix_extra_tensor_fetcher: AIXExtraTensorFetcher | None = None,
        aix_dem_matched_mask_fetcher: AIXDemMatchedMaskFetcher | None = None,
        fusion_intelligence_fetcher: FusionIntelligenceFetcher | None = None,
        tesla_atomic_inference_fetcher: TeslaAtomicInferenceFetcher | None = None,
    ) -> None:
        self.grid_spec = grid_spec
        self.start_date = start_date
        self.end_date = end_date
        self.cloud_max = cloud_max
        self.s2_cube_fetcher = s2_cube_fetcher
        self.aix_extra_tensor_fetcher = aix_extra_tensor_fetcher
        self.aix_dem_matched_mask_fetcher = aix_dem_matched_mask_fetcher
        self.fusion_intelligence_fetcher = fusion_intelligence_fetcher
        self.tesla_atomic_inference_fetcher = tesla_atomic_inference_fetcher

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
        masks = compute_s2_dem_matched_masks(cube, outputs, nodata=self.grid_spec.nodata)
        written_paths = write_s2_outputs(context.run_dir, self.grid_spec, outputs)
        mask_outputs = write_s2_mask_outputs(
            context.run_dir,
            self.grid_spec,
            masks,
            start_date=self.start_date,
            end_date=self.end_date,
            cloud_max=self.cloud_max,
        )
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

        if self.aix_extra_tensor_fetcher is not None:
            aix_fetcher = self.aix_extra_tensor_fetcher
        elif self.s2_cube_fetcher is not None:
            # Deterministic test mode: avoid Earth Engine when the primary S2 cube is injected.
            aix_fetcher = deterministic_aix_extra_tensor_fetcher
        else:
            aix_fetcher = create_ee_aix_extra_tensor_fetcher(context.settings, self.grid_spec)
        aix_cube = aix_fetcher(grid_spec=self.grid_spec)
        aix_extra_tensor_outputs = write_aix_extra_tensor_outputs(context.run_dir, self.grid_spec, aix_cube)

        if self.aix_dem_matched_mask_fetcher is not None:
            aix_mask_fetcher = self.aix_dem_matched_mask_fetcher
        elif self.s2_cube_fetcher is not None:
            aix_mask_fetcher = deterministic_aix_dem_matched_mask_fetcher
        else:
            aix_mask_fetcher = create_ee_aix_dem_matched_mask_fetcher(context.settings, self.grid_spec)
        aix_dem_matched_mask_cube = aix_mask_fetcher(grid_spec=self.grid_spec)
        aix_dem_matched_mask_outputs = write_aix_dem_matched_mask_outputs(context.run_dir, self.grid_spec, aix_dem_matched_mask_cube)

        if self.fusion_intelligence_fetcher is not None:
            fusion_fetcher = self.fusion_intelligence_fetcher
        elif self.s2_cube_fetcher is not None:
            fusion_fetcher = deterministic_fusion_intelligence_fetcher
        else:
            fusion_fetcher = create_ee_fusion_intelligence_fetcher(context.settings, self.grid_spec)
        fusion_intelligence_cube = fusion_fetcher(grid_spec=self.grid_spec)
        fusion_intelligence_outputs = write_fusion_intelligence_outputs(context.run_dir, self.grid_spec, fusion_intelligence_cube)

        if self.tesla_atomic_inference_fetcher is not None:
            tesla_fetcher = self.tesla_atomic_inference_fetcher
        elif self.s2_cube_fetcher is not None:
            tesla_fetcher = deterministic_tesla_atomic_inference_fetcher
        else:
            tesla_fetcher = create_ee_tesla_atomic_inference_fetcher(context.settings, self.grid_spec)
        tesla_atomic_inference_cube = tesla_fetcher(grid_spec=self.grid_spec)
        tesla_atomic_inference_outputs = write_tesla_atomic_inference_outputs(
            context.run_dir, self.grid_spec, tesla_atomic_inference_cube
        )

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
            [
                build_stage_artifact(
                    name="s2_raw_valid_mask_640",
                    relative_path=mask_outputs["raw_valid_mask_tif"].relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=mask_outputs["raw_valid_mask_tif"].stat().st_size,
                    http_servable=False,
                ),
                build_stage_artifact(
                    name="s2_index_valid_mask_640",
                    relative_path=mask_outputs["index_valid_mask_tif"].relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=mask_outputs["index_valid_mask_tif"].stat().st_size,
                    http_servable=False,
                ),
                build_stage_artifact(
                    name="s2_dem_matched_masks_manifest",
                    relative_path=mask_outputs["mask_manifest_json"].relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=mask_outputs["mask_manifest_json"].stat().st_size,
                    http_servable=False,
                ),
            ]
        )
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
        artifacts.extend(
            [
                build_stage_artifact(
                    name="notebook_AIX_2022_2026_CLOUDLT3_EXTRA_TENSORS_STACK_640_npy",
                    relative_path=aix_extra_tensor_outputs["stack_npy"].relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=aix_extra_tensor_outputs["stack_npy"].stat().st_size,
                    http_servable=False,
                ),
                build_stage_artifact(
                    name="notebook_AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640_npy",
                    relative_path=aix_dem_matched_mask_outputs["stack_npy"].relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=aix_dem_matched_mask_outputs["stack_npy"].stat().st_size,
                    http_servable=False,
                ),
                build_stage_artifact(
                    name="notebook_REPORT_640_FINAL_INTELLIGENCE_STACK_640_npy",
                    relative_path=fusion_intelligence_outputs["stack_npy"].relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=fusion_intelligence_outputs["stack_npy"].stat().st_size,
                    http_servable=False,
                ),
                build_stage_artifact(
                    name="notebook_TESLA_V7_2_ATOMIC_INFERENCE_STACK_640_npy",
                    relative_path=tesla_atomic_inference_outputs["stack_npy"].relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=tesla_atomic_inference_outputs["stack_npy"].stat().st_size,
                    http_servable=False,
                ),
                build_stage_artifact(
                    name="aix_extra_tensors_stack_alias_manifest",
                    relative_path=aix_dem_matched_mask_outputs["alias_manifest_json"].relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=aix_dem_matched_mask_outputs["alias_manifest_json"].stat().st_size,
                    http_servable=False,
                ),
            ]
        )
        return StageResult(
            artifacts=artifacts,
            metadata={
                "band_names": list(INDEX_NAMES),
                "source_bands": list(S2_SOURCE_BANDS),
                "shape": [self.grid_spec.size, self.grid_spec.size],
                "mask_names": ["s2_raw_valid_mask_640", "s2_index_valid_mask_640"],
                "aix_extra_tensor_stack": AIX_EXTRA_TENSORS_STACK_NPY,
                "aix_extra_tensor_bands": list(AIX_EXTRA_TENSOR_BANDS),
                "aix_dem_matched_masks_stack": AIX_DEM_MATCHED_MASKS_STACK_NPY,
                "aix_dem_matched_mask_bands": list(AIX_DEM_MATCHED_MASK_BANDS),
                "fusion_intelligence_stack": FUSION_INTELLIGENCE_STACK_NPY,
                "fusion_intelligence_bands": list(FUSION_INTELLIGENCE_BANDS),
                "tesla_atomic_inference_stack": TESLA_ATOMIC_INFERENCE_STACK_NPY,
                "tesla_atomic_inference_bands": list(TESLA_ATOMIC_INFERENCE_BANDS),
            },
        )
