"""V6 geospatial feature-layer extraction boundary.

This module ports the V6 notebook feature-layer formulas into app-side service
code while keeping unit tests offline. Runtime calls are made only through the
runtime boundary from `v6_real_gee_runtime`.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from app.services.v6_real_gee_runtime import V6AoiBounds, V6EarthEngineRuntime


SENTINEL2_COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"
DEM_IMAGE_ID = "NASA/NASADEM_HGT/001"
SURFACE_WATER_IMAGE_ID = "JRC/GSW1_4/GlobalSurfaceWater"
WORLDCOVER_COLLECTION_ID = "ESA/WorldCover/v200"
DYNAMIC_WORLD_COLLECTION_ID = "GOOGLE/DYNAMICWORLD/V1"


REQUIRED_V6_FEATURE_BANDS: tuple[str, ...] = (
    "s2_count",
    "ndvi",
    "bsi",
    "mndwi",
    "low_vegetation",
    "bare_soil_proxy",
    "visibility_score",
    "spectral_contrast",
    "slope_deg",
    "tpi_m",
    "gentle_slope_score",
    "terrain_score",
    "surface_water_frac",
    "water_edge_frac",
    "worldcover_class",
    "builtup_frac",
    "cropland_frac",
    "v6_dw_built_prob",
    "v6_strong_built_frac",
    "v6_building_near_frac",
    "v6_road_like_edge_frac",
    "v6_modern_corridor_frac",
)


@dataclass(frozen=True)
class V6FeatureLayerConfig:
    start_date: str
    end_date: str
    sentinel_cloud_pct_max: int = 40
    dynamic_world_built_threshold: float = 0.35
    local_contrast_radius_m: int = 90
    building_near_radius_m: int = 200

    def __post_init__(self) -> None:
        if not self.start_date or not self.end_date:
            raise ValueError("start_date and end_date are required")
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be earlier than end_date")
        if self.sentinel_cloud_pct_max < 0 or self.sentinel_cloud_pct_max > 100:
            raise ValueError("sentinel_cloud_pct_max must be between 0 and 100")
        if not 0 <= self.dynamic_world_built_threshold <= 1:
            raise ValueError("dynamic_world_built_threshold must be between 0 and 1")
        if self.local_contrast_radius_m <= 0 or self.building_near_radius_m <= 0:
            raise ValueError("feature radii must be positive")


@dataclass(frozen=True)
class V6FeatureStackPlan:
    dataset_ids: tuple[str, ...]
    required_bands: tuple[str, ...]

    def safe_summary(self) -> dict[str, Any]:
        return {
            "dataset_count": len(self.dataset_ids),
            "required_band_count": len(self.required_bands),
            "required_bands": list(self.required_bands),
            "contains_feature_values": False,
        }


def build_v6_feature_stack_plan() -> V6FeatureStackPlan:
    return V6FeatureStackPlan(
        dataset_ids=(
            SENTINEL2_COLLECTION_ID,
            DEM_IMAGE_ID,
            SURFACE_WATER_IMAGE_ID,
            WORLDCOVER_COLLECTION_ID,
            DYNAMIC_WORLD_COLLECTION_ID,
        ),
        required_bands=REQUIRED_V6_FEATURE_BANDS,
    )


class V6GeeFeatureExtractor:
    """Builds the V6 feature image stack through the runtime boundary."""

    def __init__(self, runtime: V6EarthEngineRuntime, config: V6FeatureLayerConfig) -> None:
        self.runtime = runtime
        self.config = config

    def build_feature_stack(self, aoi: V6AoiBounds) -> Any:
        ee = self.runtime.initialize()
        region = self.runtime.rectangle_geometry(aoi)

        s2_col = (
            ee.ImageCollection(SENTINEL2_COLLECTION_ID)
            .filterBounds(region)
            .filterDate(self.config.start_date, self.config.end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", self.config.sentinel_cloud_pct_max))
        )
        s2 = s2_col.median().clip(region)
        s2_count = s2_col.select("B4").count().rename("s2_count")

        ndvi = s2.normalizedDifference(["B8", "B4"]).rename("ndvi")
        bsi = s2.expression(
            "((SWIR + RED) - (NIR + BLUE)) / ((SWIR + RED) + (NIR + BLUE))",
            {
                "SWIR": s2.select("B11"),
                "RED": s2.select("B4"),
                "NIR": s2.select("B8"),
                "BLUE": s2.select("B2"),
            },
        ).rename("bsi")
        mndwi = s2.normalizedDifference(["B3", "B11"]).rename("mndwi")

        low_vegetation = _clamp01(ee, ee.Image(0.55).subtract(ndvi).divide(0.55)).rename("low_vegetation")
        bare_soil_proxy = _clamp01(ee, bsi.subtract(-0.10).divide(0.40)).rename("bare_soil_proxy")
        visibility_score = low_vegetation.multiply(0.55).add(bare_soil_proxy.multiply(0.45)).rename("visibility_score")
        spectral_contrast = _clamp01(
            ee,
            _local_abs_z(ee, bsi, self.config.local_contrast_radius_m).divide(3.0),
        ).rename("spectral_contrast")

        dem = ee.Image(DEM_IMAGE_ID).select("elevation").clip(region)
        slope_deg = ee.Terrain.slope(dem).rename("slope_deg")
        tpi_m = dem.subtract(dem.focal_mean(radius=self.config.local_contrast_radius_m, units="meters")).rename("tpi_m")
        gentle_slope_score = _clamp01(ee, ee.Image(12).subtract(slope_deg).divide(12)).rename("gentle_slope_score")
        terrain_score = gentle_slope_score.rename("terrain_score")

        surface_water = (
            ee.Image(SURFACE_WATER_IMAGE_ID)
            .select("occurrence")
            .gte(50)
            .rename("surface_water_frac")
            .clip(region)
        )
        water_edge = surface_water.focal_max(radius=60, units="meters").And(surface_water.Not()).rename("water_edge_frac")

        worldcover = (
            ee.ImageCollection(WORLDCOVER_COLLECTION_ID)
            .first()
            .select("Map")
            .rename("worldcover_class")
            .clip(region)
        )
        builtup = worldcover.eq(50).rename("builtup_frac")
        cropland = worldcover.eq(40).rename("cropland_frac")

        dw_built_prob = (
            ee.ImageCollection(DYNAMIC_WORLD_COLLECTION_ID)
            .filterBounds(region)
            .filterDate(self.config.start_date, self.config.end_date)
            .select("built")
            .median()
            .unmask(0)
            .clip(region)
            .rename("v6_dw_built_prob")
        )
        dw_built_mask = dw_built_prob.gte(self.config.dynamic_world_built_threshold)
        strong_built = builtup.Or(dw_built_mask).rename("v6_strong_built_frac")
        building_near = strong_built.focal_max(radius=self.config.building_near_radius_m, units="meters").rename("v6_building_near_frac")

        optical_edge = ee.Image(
            ee.Algorithms.CannyEdgeDetector(
                image=bsi.unmask(0),
                threshold=0.35,
                sigma=1,
            )
        ).gt(0)
        road_like_edge = optical_edge.And(low_vegetation.gt(0.35)).rename("v6_road_like_edge_frac")
        modern_corridor = road_like_edge.And(building_near.Or(cropland).Or(gentle_slope_score.gt(0.60))).rename(
            "v6_modern_corridor_frac"
        )

        return ee.Image.cat(
            [
                s2_count,
                ndvi,
                bsi,
                mndwi,
                low_vegetation,
                bare_soil_proxy,
                visibility_score,
                spectral_contrast,
                slope_deg,
                tpi_m,
                gentle_slope_score,
                terrain_score,
                surface_water,
                water_edge,
                worldcover,
                builtup,
                cropland,
                dw_built_prob,
                strong_built,
                building_near,
                road_like_edge,
                modern_corridor,
            ]
        ).clip(region)


def validate_v6_feature_row(row: Mapping[str, Any]) -> tuple[str, ...]:
    """Return validation issues for a reduced per-grid-cell feature row."""

    issues: list[str] = []
    for band in REQUIRED_V6_FEATURE_BANDS:
        if band not in row:
            issues.append(f"missing_feature:{band}")
            continue
        value = row[band]
        if isinstance(value, bool):
            issues.append(f"non_numeric_feature:{band}")
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            issues.append(f"non_numeric_feature:{band}")
            continue
        if not math.isfinite(number):
            issues.append(f"non_finite_feature:{band}")
    return tuple(issues)


def _clamp01(ee: Any, image: Any) -> Any:
    return image.max(ee.Image(0)).min(ee.Image(1))


def _local_abs_z(ee: Any, image: Any, radius_m: int) -> Any:
    kernel = ee.Kernel.circle(radius=radius_m, units="meters")
    local_mean = image.reduceNeighborhood(reducer=ee.Reducer.mean(), kernel=kernel)
    local_std = image.reduceNeighborhood(reducer=ee.Reducer.stdDev(), kernel=kernel)
    return image.subtract(local_mean).divide(local_std.max(0.0001)).abs()
