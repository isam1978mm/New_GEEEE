"""Secret layers stage: AI_READY_640_Secret_* raster generation.

Computes the six notebook secret layers that feed the FINAL_TESLA_V7_2_HYPERCUBE.
Each layer is implemented only when exact source-equivalent inputs are available
from previously-persisted pipeline outputs.

Layers with missing source bands are recorded as not_implemented_no_source_equivalent.
"""
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
from app.pipeline.stages.dem_derivatives import box_mean_nanaware
from app.pipeline.stages.grid import GridSpec
from app.pipeline.stages.s2_indices import S2_SOURCE_BANDS, S2_RAW_CUBE_NPY_NAME
from app.pipeline.stages.thermal import L9_RAW_ST_B10_NPY_NAME, NOTEBOOK_L9_ST_B10_COLLECTION
from app.services.ee_session import initialize_ee_session

EPS = 1e-10
NOTEBOOK_SECRET_EPS = 1e-6
SECRET_LAYER_OUTPUT_DIR = "AI_READY_640"
NOTEBOOK_SECRET_S2_START = "2022-01-01"
NOTEBOOK_SECRET_S2_END = "2026-03-01"
NOTEBOOK_SECRET_S2_CLOUD_MAX = 5
NOTEBOOK_SECRET_S2_SOURCE_BANDS = ("B1", "B2", "B4", "B8", "B11", "B12")
S2_SECRET_LAYER_NAMES = (
    "AI_READY_640_Secret_Gold_Halo",
    "AI_READY_640_Secret_Silver_Oxide",
    "AI_READY_640_Secret_Tunnel_Ceiling",
    "AI_READY_640_Secret_Chemical_Protector",
)
THERMAL_INERTIA_LAYER_NAME = "AI_READY_640_Secret_Thermal_Inertia"
THERMAL_INERTIA_SOURCE_PROVENANCE = "notebook_l9_st_b10_raw"
THERMAL_INERTIA_SOURCE_UNIT = "raw_dn"


class HiddenDoorsFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray: ...


class SecretS2CubeFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray: ...


class SecretS2LayerFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> dict[str, np.ndarray]: ...


class ThermalInertiaFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray: ...


SECRET_LAYER_SPECS = [
    {
        "name": "AI_READY_640_Secret_Gold_Halo",
        "formula": "B12 / (B8 + eps)",
        "source_type": "s2_raw",
        "inputs": ["B12", "B8"],
    },
    {
        "name": "AI_READY_640_Secret_Silver_Oxide",
        "formula": "B2 / (B1 + eps)",
        "source_type": "s2_raw",
        "inputs": ["B2", "B1"],
    },
    {
        "name": "AI_READY_640_Secret_Tunnel_Ceiling",
        "formula": "B8 - B4",
        "source_type": "s2_raw",
        "inputs": ["B8", "B4"],
    },
    {
        "name": THERMAL_INERTIA_LAYER_NAME,
        "formula": "l9_col / focal_mean(l9_col, 500m)",
        "source_type": "thermal",
        "inputs": ["l9_st_b10_raw"],
    },
    {
        "name": "AI_READY_640_Secret_Chemical_Protector",
        "formula": "B1 / (B11 + eps)",
        "source_type": "s2_raw",
        "inputs": ["B1", "B11"],
    },
    {
        "name": "AI_READY_640_Secret_Hidden_Doors",
        "formula": "hillshade(315,35) - hillshade(135,35)",
        "source_type": "dem",
        "inputs": ["dem"],
    },
]


def compute_hillshade_parameterized(
    dem: np.ndarray, *, nodata: float, scale_m: float, azimuth_deg: float, altitude_deg: float
) -> np.ndarray:
    """Compute EE-style hillshade for arbitrary sun azimuth and altitude (in degrees)."""
    dem_float = dem.astype(np.float32, copy=True)
    dem_float = np.where(dem_float == nodata, np.nan, dem_float)
    source_valid = np.isfinite(dem_float)
    dz_dy, dz_dx = np.gradient(dem_float, scale_m, scale_m)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    aspect_rad = np.arctan2(-dz_dx, dz_dy)
    azimuth_rad = np.deg2rad(azimuth_deg)
    altitude_rad = np.deg2rad(altitude_deg)
    hillshade = (
        np.sin(altitude_rad) * np.cos(slope_rad)
        + np.cos(altitude_rad) * np.sin(slope_rad) * np.cos(azimuth_rad - aspect_rad)
    )
    hillshade = (np.clip(hillshade, 0.0, 1.0) * np.float32(255.0)).astype(np.float32)
    hillshade[~source_valid] = nodata
    hillshade[~np.isfinite(hillshade)] = nodata
    return hillshade.astype(np.float32, copy=False)


def _check_source_available(spec: dict, available_s2_bands: set[str]) -> tuple[bool, str]:
    """Return (is_available, reason) for a layer spec."""
    if spec["source_type"] == "s2_raw":
        missing = [band for band in spec["inputs"] if band not in available_s2_bands]
        if missing:
            return False, f"Raw S2 band(s) {', '.join(missing)} not available in app S2_SOURCE_BANDS {sorted(available_s2_bands)}"
        return True, ""
    return True, ""


def _band_index(band_name: str, band_names: tuple[str, ...]) -> int:
    try:
        return band_names.index(band_name)
    except ValueError as exc:
        raise StageError(f"S2 cube is missing required notebook secret band {band_name}.") from exc


def compute_secret_gold_halo(
    s2_cube: np.ndarray, *, nodata: float, band_names: tuple[str, ...] = S2_SOURCE_BANDS
) -> np.ndarray:
    """B12 / (B8 + eps)"""
    b12 = s2_cube[:, :, _band_index("B12", band_names)]
    b8 = s2_cube[:, :, _band_index("B8", band_names)]
    valid = (b12 != nodata) & (b8 != nodata) & np.isfinite(b12) & np.isfinite(b8)
    result = np.full(b12.shape, nodata, dtype=np.float32)
    result[valid] = (b12[valid] / (b8[valid] + EPS)).astype(np.float32)
    return result


def compute_secret_silver_oxide(
    s2_cube: np.ndarray, *, nodata: float, band_names: tuple[str, ...] = S2_SOURCE_BANDS
) -> np.ndarray:
    """B2 / (B1 + eps)"""
    b2 = s2_cube[:, :, _band_index("B2", band_names)]
    b1 = s2_cube[:, :, _band_index("B1", band_names)]
    valid = (b2 != nodata) & (b1 != nodata) & np.isfinite(b2) & np.isfinite(b1)
    result = np.full(b2.shape, nodata, dtype=np.float32)
    result[valid] = (b2[valid] / (b1[valid] + EPS)).astype(np.float32)
    return result


def compute_secret_chemical_protector(
    s2_cube: np.ndarray, *, nodata: float, band_names: tuple[str, ...] = S2_SOURCE_BANDS
) -> np.ndarray:
    """B1 / (B11 + eps)"""
    b1 = s2_cube[:, :, _band_index("B1", band_names)]
    b11 = s2_cube[:, :, _band_index("B11", band_names)]
    valid = (b1 != nodata) & (b11 != nodata) & np.isfinite(b1) & np.isfinite(b11)
    result = np.full(b1.shape, nodata, dtype=np.float32)
    result[valid] = (b1[valid] / (b11[valid] + EPS)).astype(np.float32)
    return result


def compute_secret_tunnel_ceiling(
    s2_cube: np.ndarray, *, nodata: float, band_names: tuple[str, ...] = S2_SOURCE_BANDS
) -> np.ndarray:
    """B8 - B4"""
    b8 = s2_cube[:, :, _band_index("B8", band_names)]
    b4 = s2_cube[:, :, _band_index("B4", band_names)]
    valid = (b8 != nodata) & (b4 != nodata) & np.isfinite(b8) & np.isfinite(b4)
    result = np.full(b8.shape, nodata, dtype=np.float32)
    result[valid] = (b8[valid] - b4[valid]).astype(np.float32)
    return result


def compute_secret_thermal_inertia(
    l9_st_b10_raw: np.ndarray, *, nodata: float, scale_m: float
) -> np.ndarray:
    """l9_col / focal_mean(l9_col, 500m), computed on raw Landsat 9 ST_B10 DN."""
    source = l9_st_b10_raw.astype(np.float32, copy=True)
    source = np.where(source == nodata, np.nan, source)
    radius_px = max(1, int(round(500.0 / scale_m)))
    focal_mean = box_mean_nanaware(source, radius_px)
    source_valid = np.isfinite(source) & np.isfinite(focal_mean) & (focal_mean != 0.0)
    result = np.full(l9_st_b10_raw.shape, nodata, dtype=np.float32)
    result[source_valid] = (source[source_valid] / focal_mean[source_valid]).astype(np.float32)
    return result


def compute_secret_hidden_doors(
    dem: np.ndarray, *, nodata: float, scale_m: float
) -> np.ndarray:
    """hillshade(315,35) - hillshade(135,35)"""
    hs_315 = compute_hillshade_parameterized(dem, nodata=nodata, scale_m=scale_m, azimuth_deg=315.0, altitude_deg=35.0)
    hs_135 = compute_hillshade_parameterized(dem, nodata=nodata, scale_m=scale_m, azimuth_deg=135.0, altitude_deg=35.0)
    valid = (hs_315 != nodata) & (hs_135 != nodata) & np.isfinite(hs_315) & np.isfinite(hs_135)
    result = np.full(dem.shape[:2], nodata, dtype=np.float32)
    result[valid] = (hs_315[valid] - hs_135[valid]).astype(np.float32)
    return result


def build_grid_region(grid_spec: GridSpec):
    scale_x, _, xmin, _, scale_y, ymax = grid_spec.transform
    xmax = xmin + grid_spec.size * scale_x
    ymin = ymax + grid_spec.size * scale_y
    return ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], grid_spec.crs, False)


def build_ee_hidden_doors_image(grid_spec: GridSpec):
    roi = build_grid_region(grid_spec)
    srtm_dem = ee.Image("USGS/SRTMGL1_003").clip(roi)
    hidden_doors = (
        ee.Terrain.hillshade(srtm_dem, 315, 35)
        .subtract(ee.Terrain.hillshade(srtm_dem, 135, 35))
        .rename("Secret_Hidden_Doors")
        .float()
        .reproject(crs=grid_spec.crs, crsTransform=list(grid_spec.transform))
    )
    return hidden_doors


def build_notebook_secret_s2_composite(grid_spec: GridSpec):
    return (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(build_grid_region(grid_spec))
        .filterDate(NOTEBOOK_SECRET_S2_START, NOTEBOOK_SECRET_S2_END)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", NOTEBOOK_SECRET_S2_CLOUD_MAX))
        .select(list(NOTEBOOK_SECRET_S2_SOURCE_BANDS))
        .median()
    )


def build_notebook_secret_s2_image(grid_spec: GridSpec):
    return (
        ee.Image(build_notebook_secret_s2_composite(grid_spec))
        .toFloat()
        .reproject(crs=grid_spec.crs, crsTransform=list(grid_spec.transform))
        .clip(build_grid_region(grid_spec))
    )


def build_notebook_secret_s2_layers_image(grid_spec: GridSpec):
    s2_col = build_notebook_secret_s2_composite(grid_spec)
    eps = ee.Image.constant(NOTEBOOK_SECRET_EPS)
    layers = ee.Image.cat(
        [
            s2_col.select("B12").divide(s2_col.select("B8").add(eps)).rename("AI_READY_640_Secret_Gold_Halo"),
            s2_col.select("B2").divide(s2_col.select("B1").add(eps)).rename("AI_READY_640_Secret_Silver_Oxide"),
            s2_col.select("B8").subtract(s2_col.select("B4")).rename("AI_READY_640_Secret_Tunnel_Ceiling"),
            s2_col.select("B1").divide(s2_col.select("B11").add(eps)).rename("AI_READY_640_Secret_Chemical_Protector"),
        ]
    )
    return (
        layers.toFloat()
        .reproject(crs=grid_spec.crs, crsTransform=list(grid_spec.transform))
        .clip(build_grid_region(grid_spec))
    )


def create_ee_notebook_secret_s2_cube_fetcher(settings, grid_spec: GridSpec) -> SecretS2CubeFetcher:
    initialize_ee_session(settings)
    s2_image = build_notebook_secret_s2_image(grid_spec)
    requests = build_dem_tile_requests(grid_spec)

    def fetch_secret_s2_cube(*, grid_spec: GridSpec) -> np.ndarray:
        cube = np.full(
            (grid_spec.size, grid_spec.size, len(NOTEBOOK_SECRET_S2_SOURCE_BANDS)),
            grid_spec.nodata,
            dtype=np.float32,
        )
        for request in requests:
            tile_geo = ee.Geometry.Rectangle([request.xmin, request.ymin, request.xmax, request.ymax], grid_spec.crs, False)
            rect = s2_image.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            for band_index, band_name in enumerate(NOTEBOOK_SECRET_S2_SOURCE_BANDS):
                tile = np.array(rect["properties"][band_name], dtype=np.float32)[: request.size, : request.size]
                if tile.shape != (request.size, request.size):
                    raise StageError(
                        f"EE notebook secret S2 tile ({request.tile_row},{request.tile_col}) band {band_name} "
                        f"returned shape {tile.shape}, expected {(request.size, request.size)}."
                    )
                row_start = request.tile_row * request.size
                col_start = request.tile_col * request.size
                cube[row_start : row_start + request.size, col_start : col_start + request.size, band_index] = tile
        return cube

    return fetch_secret_s2_cube


def create_ee_notebook_secret_s2_layer_fetcher(settings, grid_spec: GridSpec) -> SecretS2LayerFetcher:
    initialize_ee_session(settings)
    s2_layers_image = build_notebook_secret_s2_layers_image(grid_spec)
    requests = build_dem_tile_requests(grid_spec)

    def fetch_secret_s2_layers(*, grid_spec: GridSpec) -> dict[str, np.ndarray]:
        arrays = {
            layer_name: np.full((grid_spec.size, grid_spec.size), grid_spec.nodata, dtype=np.float32)
            for layer_name in S2_SECRET_LAYER_NAMES
        }
        for request in requests:
            tile_geo = ee.Geometry.Rectangle([request.xmin, request.ymin, request.xmax, request.ymax], grid_spec.crs, False)
            rect = s2_layers_image.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            for layer_name in S2_SECRET_LAYER_NAMES:
                tile = np.array(rect["properties"][layer_name], dtype=np.float32)[: request.size, : request.size]
                if tile.shape != (request.size, request.size):
                    raise StageError(
                        f"EE notebook secret S2 tile ({request.tile_row},{request.tile_col}) layer {layer_name} "
                        f"returned shape {tile.shape}, expected {(request.size, request.size)}."
                    )
                row_start = request.tile_row * request.size
                col_start = request.tile_col * request.size
                arrays[layer_name][row_start : row_start + request.size, col_start : col_start + request.size] = tile
        return arrays

    return fetch_secret_s2_layers


def create_ee_hidden_doors_fetcher(settings, grid_spec: GridSpec) -> HiddenDoorsFetcher:
    initialize_ee_session(settings)
    hidden_doors_image = build_ee_hidden_doors_image(grid_spec)
    requests = build_dem_tile_requests(grid_spec)

    def fetch_hidden_doors(*, grid_spec: GridSpec) -> np.ndarray:
        array = np.full((grid_spec.size, grid_spec.size), np.nan, dtype=np.float32)
        for request in requests:
            tile_geo = ee.Geometry.Rectangle([request.xmin, request.ymin, request.xmax, request.ymax], grid_spec.crs, False)
            rect = hidden_doors_image.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            tile = np.array(rect["properties"]["Secret_Hidden_Doors"], dtype=np.float32)[: request.size, : request.size]
            if tile.shape != (request.size, request.size):
                raise StageError(
                    f"EE Secret_Hidden_Doors tile ({request.tile_row},{request.tile_col}) returned shape {tile.shape}, "
                    f"expected {(request.size, request.size)}."
                )
            tile[tile == grid_spec.nodata] = np.nan
            row_start = request.tile_row * request.size
            col_start = request.tile_col * request.size
            array[row_start : row_start + request.size, col_start : col_start + request.size] = tile
        return array

    return fetch_hidden_doors


def load_s2_raw_cube(run_dir: Path) -> np.ndarray:
    """Load the raw S2 band cube persisted by the S2 indices stage."""
    path = run_dir / S2_RAW_CUBE_NPY_NAME
    if not path.is_file():
        raise StageError("S2 raw band cube is required before secret layers stage.")
    return np.load(path)


def load_dem_array(run_dir: Path) -> np.ndarray:
    """Load the DEM array persisted by the DEM stage."""
    path = run_dir / "dem.npy"
    if not path.is_file():
        raise StageError("DEM stage output is required before secret layers stage.")
    return np.load(path)


def load_l9_st_b10_raw_array(run_dir: Path) -> np.ndarray:
    """Load the notebook-basis raw L9 ST_B10 array persisted by the thermal stage."""
    path = run_dir / L9_RAW_ST_B10_NPY_NAME
    if not path.is_file():
        raise StageError("Thermal L9 raw ST_B10 output is required before secret thermal inertia.")
    return np.load(path)


def write_secret_layer_output(run_dir: Path, grid_spec: GridSpec, name: str, array: np.ndarray) -> Path:
    """Write a single secret layer as a georeferenced GeoTIFF under AI_READY_640/."""
    output_dir = run_dir / SECRET_LAYER_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    tif_path = output_dir / f"{name}.tif"
    write_georeferenced_raster(tif_path, array, grid_spec)
    write_raster_sidecar(
        tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=array.shape[:2],
    )
    return tif_path


def write_secret_layers_manifest(
    run_dir: Path,
    *,
    implemented: list[dict],
    not_implemented: list[dict],
) -> Path:
    """Write a manifest documenting secret layer status."""
    qa_dir = ensure_run_qa_dir(run_dir) / "stacks"
    qa_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = qa_dir / "secret_layers_manifest.json"
    payload = {
        "schema": "secret_layers_manifest_v1",
        "stage": "secret_layers",
        "layer_count": len(SECRET_LAYER_SPECS),
        "implemented_count": len(implemented),
        "not_implemented_count": len(not_implemented),
        "implemented": implemented,
        "not_implemented": not_implemented,
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")
    return manifest_path


def _source_provenance_for_spec(
    spec: dict,
    *,
    secret_s2_cube_fetcher: SecretS2CubeFetcher | None,
    secret_s2_layer_fetcher: SecretS2LayerFetcher | None,
    thermal_inertia_fetcher: ThermalInertiaFetcher | None,
) -> str:
    if spec["name"] in S2_SECRET_LAYER_NAMES and (secret_s2_cube_fetcher is not None or secret_s2_layer_fetcher is not None):
        return "notebook_secret_s2"
    if spec["name"] == THERMAL_INERTIA_LAYER_NAME:
        return "notebook_l9_st_b10" if thermal_inertia_fetcher is not None else THERMAL_INERTIA_SOURCE_PROVENANCE
    return str(spec["source_type"])


def _source_unit_for_spec(spec: dict) -> str | None:
    if spec["name"] == THERMAL_INERTIA_LAYER_NAME:
        return THERMAL_INERTIA_SOURCE_UNIT
    return None


class SecretLayersStage(Stage):
    """Compute AI_READY_640_Secret_* layers from persisted pipeline outputs."""

    name = "secret_layers"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(
        self,
        *,
        grid_spec: GridSpec,
        hidden_doors_fetcher: HiddenDoorsFetcher | None = None,
        secret_s2_cube_fetcher: SecretS2CubeFetcher | None = None,
        secret_s2_layer_fetcher: SecretS2LayerFetcher | None = None,
        thermal_inertia_fetcher: ThermalInertiaFetcher | None = None,
    ) -> None:
        self.grid_spec = grid_spec
        self.hidden_doors_fetcher = hidden_doors_fetcher
        self.secret_s2_cube_fetcher = secret_s2_cube_fetcher
        self.secret_s2_layer_fetcher = secret_s2_layer_fetcher
        self.thermal_inertia_fetcher = thermal_inertia_fetcher

    async def run(self, context: StageContext) -> StageResult:
        s2_band_names = NOTEBOOK_SECRET_S2_SOURCE_BANDS if self.secret_s2_cube_fetcher is not None else S2_SOURCE_BANDS
        available_s2_bands = set(s2_band_names)
        scale_m = float(self.grid_spec.manifest.scale_m)
        nodata = self.grid_spec.nodata

        s2_cube = None
        s2_layers = None
        dem = None
        l9_st_b10_raw = None

        implemented_specs: list[dict] = []
        not_implemented_specs: list[dict] = []
        artifacts = []
        layer_metadata: dict[str, dict] = {}

        for spec in SECRET_LAYER_SPECS:
            available, reason = _check_source_available(spec, available_s2_bands)
            if not available:
                not_implemented_specs.append({
                    "name": spec["name"],
                    "formula": spec["formula"],
                    "status": "not_implemented_no_source_equivalent",
                    "reason": reason,
                })
                layer_metadata[spec["name"]] = {
                    "status": "not_implemented_no_source_equivalent",
                    "reason": reason,
                }
                continue

            if spec["name"] == "AI_READY_640_Secret_Gold_Halo":
                if self.secret_s2_layer_fetcher is not None:
                    if s2_layers is None:
                        s2_layers = self.secret_s2_layer_fetcher(grid_spec=self.grid_spec)
                    array = s2_layers[spec["name"]]
                else:
                    if s2_cube is None:
                        s2_cube = self.secret_s2_cube_fetcher(grid_spec=self.grid_spec) if self.secret_s2_cube_fetcher is not None else load_s2_raw_cube(context.run_dir)
                    array = compute_secret_gold_halo(s2_cube, nodata=nodata, band_names=s2_band_names)
            elif spec["name"] == "AI_READY_640_Secret_Silver_Oxide":
                if self.secret_s2_layer_fetcher is not None:
                    if s2_layers is None:
                        s2_layers = self.secret_s2_layer_fetcher(grid_spec=self.grid_spec)
                    array = s2_layers[spec["name"]]
                else:
                    if s2_cube is None:
                        s2_cube = self.secret_s2_cube_fetcher(grid_spec=self.grid_spec) if self.secret_s2_cube_fetcher is not None else load_s2_raw_cube(context.run_dir)
                    array = compute_secret_silver_oxide(s2_cube, nodata=nodata, band_names=s2_band_names)
            elif spec["name"] == "AI_READY_640_Secret_Tunnel_Ceiling":
                if self.secret_s2_layer_fetcher is not None:
                    if s2_layers is None:
                        s2_layers = self.secret_s2_layer_fetcher(grid_spec=self.grid_spec)
                    array = s2_layers[spec["name"]]
                else:
                    if s2_cube is None:
                        s2_cube = self.secret_s2_cube_fetcher(grid_spec=self.grid_spec) if self.secret_s2_cube_fetcher is not None else load_s2_raw_cube(context.run_dir)
                    array = compute_secret_tunnel_ceiling(s2_cube, nodata=nodata, band_names=s2_band_names)
            elif spec["name"] == THERMAL_INERTIA_LAYER_NAME:
                if self.thermal_inertia_fetcher is not None:
                    array = self.thermal_inertia_fetcher(grid_spec=self.grid_spec)
                else:
                    if l9_st_b10_raw is None:
                        l9_st_b10_raw = load_l9_st_b10_raw_array(context.run_dir)
                    array = compute_secret_thermal_inertia(l9_st_b10_raw, nodata=nodata, scale_m=scale_m)
            elif spec["name"] == "AI_READY_640_Secret_Chemical_Protector":
                if self.secret_s2_layer_fetcher is not None:
                    if s2_layers is None:
                        s2_layers = self.secret_s2_layer_fetcher(grid_spec=self.grid_spec)
                    array = s2_layers[spec["name"]]
                else:
                    if s2_cube is None:
                        s2_cube = self.secret_s2_cube_fetcher(grid_spec=self.grid_spec) if self.secret_s2_cube_fetcher is not None else load_s2_raw_cube(context.run_dir)
                    array = compute_secret_chemical_protector(s2_cube, nodata=nodata, band_names=s2_band_names)
            elif spec["name"] == "AI_READY_640_Secret_Hidden_Doors":
                if self.hidden_doors_fetcher is not None:
                    array = self.hidden_doors_fetcher(grid_spec=self.grid_spec)
                else:
                    if dem is None:
                        dem = load_dem_array(context.run_dir)
                    array = compute_secret_hidden_doors(dem, nodata=nodata, scale_m=scale_m)
            else:
                continue

            expected_shape = (self.grid_spec.size, self.grid_spec.size)
            if array.shape[:2] != expected_shape:
                raise StageError(f"Secret layer {spec['name']} shape {array.shape[:2]} != expected {expected_shape}")

            tif_path = write_secret_layer_output(context.run_dir, self.grid_spec, spec["name"], array)
            artifacts.append(
                build_stage_artifact(
                    name=spec["name"],
                    relative_path=tif_path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                    size_bytes=tif_path.stat().st_size,
                )
            )
            source_provenance = _source_provenance_for_spec(
                spec,
                secret_s2_cube_fetcher=self.secret_s2_cube_fetcher,
                secret_s2_layer_fetcher=self.secret_s2_layer_fetcher,
                thermal_inertia_fetcher=self.thermal_inertia_fetcher,
            )
            implemented_item = {
                "name": spec["name"],
                "formula": spec["formula"],
                "status": "implemented",
                "source_type": spec["source_type"],
                "inputs": spec["inputs"],
                "output_path": f"{SECRET_LAYER_OUTPUT_DIR}/{spec['name']}.tif",
                "source_provenance": source_provenance,
            }
            layer_item = {
                "status": "implemented",
                "formula": spec["formula"],
                "source_provenance": source_provenance,
            }
            source_unit = _source_unit_for_spec(spec)
            if source_unit is not None:
                implemented_item["source_unit"] = source_unit
                implemented_item["source_collection"] = NOTEBOOK_L9_ST_B10_COLLECTION
                layer_item["source_unit"] = source_unit
                layer_item["source_collection"] = NOTEBOOK_L9_ST_B10_COLLECTION
            implemented_specs.append(implemented_item)
            layer_metadata[spec["name"]] = layer_item

        manifest_path = write_secret_layers_manifest(context.run_dir, implemented=implemented_specs, not_implemented=not_implemented_specs)
        artifacts.append(
            build_stage_artifact(
                name="secret_layers_manifest",
                relative_path=manifest_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=manifest_path.stat().st_size,
                http_servable=False,
            )
        )

        return StageResult(
            artifacts=artifacts,
            metadata={
                "implemented_layers": [spec["name"] for spec in implemented_specs],
                "not_implemented_layers": [spec["name"] for spec in not_implemented_specs],
                "layer_details": layer_metadata,
            },
        )
