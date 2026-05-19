from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import ee
import numpy as np
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.dem import DEM_TILE_SIZE, raster_sidecar_path, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.services.ee_session import initialize_ee_session

DEFAULT_START = "2026-01-01"
DEFAULT_END = "2026-03-01"
MAX_ORBIT_DT_DAYS = 9
MAX_PAIR_DT_HOURS = 36
MIN_PAIRS = 2
MAX_PAIRS_TARGETS = (4, 3, 2)
RADAR_BANDS = ("VV_dB", "VH_dB", "angle")
OUTPUT_BANDS = ("VV_dB", "VH_dB", "logRatio_dB", "incidence")


class RadarCubeFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray: ...


@dataclass(frozen=True, slots=True)
class SarPair:
    asc_id: str
    desc_id: str
    dt_ms: int


def build_grid_region(grid_spec: GridSpec):
    xmin = grid_spec.manifest.bounds_m["xmin"]
    ymin = grid_spec.manifest.bounds_m["ymin"]
    xmax = grid_spec.manifest.bounds_m["xmax"]
    ymax = grid_spec.manifest.bounds_m["ymax"]
    return ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], grid_spec.crs, False)


def build_s1_base_collection(grid_spec: GridSpec, *, start_date: str, end_date: str):
    grid_region = build_grid_region(grid_spec)
    return (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(grid_region)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.eq("resolution_meters", 10))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VV", "VH", "angle"])
    )


def pick_best_track(collection):
    tracks = ee.List(collection.aggregate_array("relativeOrbitNumber_start")).distinct()

    def _track_count(track):
        track = ee.Number(track)
        count = collection.filter(ee.Filter.eq("relativeOrbitNumber_start", track)).size()
        return ee.Feature(None, {"t": track, "c": count})

    best_track = ee.Number(
        ee.FeatureCollection(tracks.map(_track_count)).sort("c", False).first().get("t")
    )
    return collection.filter(ee.Filter.eq("relativeOrbitNumber_start", best_track))


def fc_time_ids(collection) -> list[dict[str, Any]]:
    def _to_feature(img):
        img = ee.Image(img)
        return ee.Feature(None, {"ms": ee.Number(img.get("system:time_start")), "id": ee.String(img.id())})

    features = ee.FeatureCollection(collection.map(_to_feature)).sort("ms").getInfo()["features"]
    return [{"ms": int(feature["properties"]["ms"]), "id": feature["properties"]["id"]} for feature in features]


def apply_orbit_window(items: list[dict[str, Any]], max_dt_ms: int) -> tuple[list[dict[str, Any]], int | None]:
    if not items:
        return [], None
    ms_sorted = sorted(item["ms"] for item in items)
    mid = ms_sorted[len(ms_sorted) // 2]
    return ([item for item in items if abs(item["ms"] - mid) <= max_dt_ms], mid)


def greedy_pairs_with_cap(
    asc_list: list[dict[str, Any]],
    desc_list: list[dict[str, Any]],
    *,
    max_pairs: int,
    max_dt_ms: int,
) -> list[SarPair]:
    used_desc: set[int] = set()
    pairs: list[SarPair] = []
    for asc in asc_list:
        best_match: tuple[dict[str, Any], dict[str, Any], int, int] | None = None
        for desc_index, desc in enumerate(desc_list):
            if desc_index in used_desc:
                continue
            dt_ms = abs(int(asc["ms"]) - int(desc["ms"]))
            if dt_ms > max_dt_ms:
                continue
            if best_match is None or dt_ms < best_match[2]:
                best_match = (asc, desc, dt_ms, desc_index)
        if best_match is not None:
            asc_item, desc_item, dt_ms, desc_index = best_match
            used_desc.add(desc_index)
            pairs.append(SarPair(asc_id=asc_item["id"], desc_id=desc_item["id"], dt_ms=dt_ms))
        if len(pairs) >= max_pairs:
            break
    pairs.sort(key=lambda item: item.dt_ms)
    return pairs


def select_pairs(
    asc_items: list[dict[str, Any]],
    desc_items: list[dict[str, Any]],
    *,
    max_orbit_dt_days: int = MAX_ORBIT_DT_DAYS,
    max_pair_dt_hours: int = MAX_PAIR_DT_HOURS,
    min_pairs: int = MIN_PAIRS,
) -> list[SarPair]:
    orbit_ms = max_orbit_dt_days * 24 * 60 * 60 * 1000
    pair_ms = max_pair_dt_hours * 60 * 60 * 1000
    asc_windowed, _ = apply_orbit_window(asc_items, orbit_ms)
    desc_windowed, _ = apply_orbit_window(desc_items, orbit_ms)
    max_pairs_possible = min(len(asc_windowed), len(desc_windowed))
    targets = [target for target in MAX_PAIRS_TARGETS if target <= max_pairs_possible]
    for target in targets:
        pairs = greedy_pairs_with_cap(asc_windowed, desc_windowed, max_pairs=target, max_dt_ms=pair_ms)
        if len(pairs) >= target:
            return pairs
    fallback = greedy_pairs_with_cap(asc_windowed, desc_windowed, max_pairs=max_pairs_possible, max_dt_ms=pair_ms)
    if len(fallback) < min_pairs:
        raise StageError("Not enough ASC/DESC SAR pairs within the notebook constraints.")
    return fallback


def img_by_id(image_id: str, grid_spec: GridSpec):
    return ee.Image(f"COPERNICUS/S1_GRD/{image_id}").select(["VV", "VH", "angle"]).clip(build_grid_region(grid_spec))


def per_image_products_db(image):
    image_db = ee.Image(image).select(["VV", "VH", "angle"])
    vv_db = image_db.select("VV").rename("VV_dB")
    vh_db = image_db.select("VH").rename("VH_dB")
    angle = image_db.select("angle").rename("angle")
    return ee.Image.cat([vv_db, vh_db, angle])


def to_grid_radar(image, grid_spec: GridSpec):
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


def build_final_radar_image(grid_spec: GridSpec, *, start_date: str, end_date: str):
    base = build_s1_base_collection(grid_spec, start_date=start_date, end_date=end_date)
    asc = pick_best_track(base.filter(ee.Filter.eq("orbitProperties_pass", "ASCENDING")))
    desc = pick_best_track(base.filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING")))
    pairs = select_pairs(fc_time_ids(asc), fc_time_ids(desc))

    pair_images = []
    for pair in pairs:
        asc_image = per_image_products_db(img_by_id(pair.asc_id, grid_spec))
        desc_image = per_image_products_db(img_by_id(pair.desc_id, grid_spec))
        pair_images.append(ee.ImageCollection([asc_image, desc_image]).median())

    final_radar = ee.ImageCollection(pair_images).median().select(list(RADAR_BANDS))
    return to_grid_radar(final_radar, grid_spec), pairs


def create_ee_radar_cube_fetcher(settings, grid_spec: GridSpec, *, start_date: str, end_date: str) -> RadarCubeFetcher:
    initialize_ee_session(settings)
    final_radar, _pairs = build_final_radar_image(grid_spec, start_date=start_date, end_date=end_date)
    final_for_sample = finalize_for_sample(final_radar, grid_spec)
    requests = build_sar_tile_requests(grid_spec)

    def fetch_cube(*, grid_spec: GridSpec) -> np.ndarray:
        cube = np.full((grid_spec.size, grid_spec.size, len(RADAR_BANDS)), grid_spec.nodata, dtype=np.float32)
        for request in requests:
            tile_geo = ee.Geometry.Rectangle([request["xmin"], request["ymin"], request["xmax"], request["ymax"]], grid_spec.crs, False)
            rect = final_for_sample.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            for band_index, band_name in enumerate(RADAR_BANDS):
                data = np.array(rect["properties"][band_name], dtype=np.float32)[: DEM_TILE_SIZE, : DEM_TILE_SIZE]
                row_start = request["tile_row"] * DEM_TILE_SIZE
                col_start = request["tile_col"] * DEM_TILE_SIZE
                cube[row_start : row_start + DEM_TILE_SIZE, col_start : col_start + DEM_TILE_SIZE, band_index] = data
        return cube

    return fetch_cube


def build_sar_tile_requests(grid_spec: GridSpec) -> list[dict[str, float | int]]:
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


def db_to_lin(db: np.ndarray) -> np.ndarray:
    return np.power(10.0, db / 10.0)


def lin_to_db(lin: np.ndarray) -> np.ndarray:
    return 10.0 * np.log10(np.maximum(lin, 1e-12))


def apply_local_dem_rtc(cube_3: np.ndarray, dem: np.ndarray, *, nodata: float) -> dict[str, np.ndarray]:
    if cube_3.shape[-1] != 3:
        raise ValueError("SAR cube must contain VV_dB, VH_dB, and angle bands.")
    if cube_3.shape[:2] != dem.shape:
        raise ValueError("DEM shape must match SAR grid shape.")

    dem_float = dem.astype(np.float32, copy=True)
    dem_float = np.where(dem_float == nodata, np.nan, dem_float)
    dz_dy, dz_dx = np.gradient(dem_float, 10.0, 10.0)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    corr = np.cos(slope_rad)
    corr = np.where(np.isfinite(corr), np.maximum(corr, 0.25), np.nan)

    vv_db = cube_3[:, :, 0]
    vh_db = cube_3[:, :, 1]
    angle = cube_3[:, :, 2]

    inc_rad = np.deg2rad(angle)
    cos_inc = np.cos(inc_rad)
    cos_inc = np.where(np.isfinite(cos_inc), np.maximum(cos_inc, 1e-6), np.nan)

    valid = (vv_db != nodata) & (vh_db != nodata) & np.isfinite(corr) & np.isfinite(cos_inc)
    vv_lin = np.full(dem.shape, np.nan, dtype=np.float32)
    vh_lin = np.full(dem.shape, np.nan, dtype=np.float32)
    vv_lin[valid] = db_to_lin(vv_db[valid]).astype(np.float32)
    vh_lin[valid] = db_to_lin(vh_db[valid]).astype(np.float32)

    vv_lin = vv_lin / cos_inc / corr
    vh_lin = vh_lin / cos_inc / corr

    vv_db_corr = np.full(dem.shape, nodata, dtype=np.float32)
    vh_db_corr = np.full(dem.shape, nodata, dtype=np.float32)
    log_ratio = np.full(dem.shape, nodata, dtype=np.float32)
    incidence = np.full(dem.shape, nodata, dtype=np.float32)

    vv_db_corr[valid] = lin_to_db(vv_lin[valid]).astype(np.float32)
    vh_db_corr[valid] = lin_to_db(vh_lin[valid]).astype(np.float32)
    log_ratio[valid] = (vv_db_corr[valid] - vh_db_corr[valid]).astype(np.float32)
    incidence[angle != nodata] = angle[angle != nodata].astype(np.float32)

    return {
        "VV_dB": vv_db_corr,
        "VH_dB": vh_db_corr,
        "logRatio_dB": log_ratio,
        "incidence": incidence,
    }


def load_dem_array(run_dir: Path) -> np.ndarray:
    dem_path = run_dir / "dem.npy"
    if not dem_path.is_file():
        raise StageError("DEM stage output is required before SAR RTC.")
    return np.load(dem_path)


def write_raster(path: Path, array: np.ndarray) -> None:
    Image.fromarray(array.astype(np.float32)).save(path, format="TIFF")


def write_sar_outputs(run_dir: Path, grid_spec: GridSpec, outputs: dict[str, np.ndarray]) -> list[Path]:
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


def deterministic_radar_cube_fetcher(*, grid_spec: GridSpec) -> np.ndarray:
    size = grid_spec.size
    rows, cols = np.indices((size, size), dtype=np.float32)
    vv = np.float32(-12.0) + rows * np.float32(0.01) + cols * np.float32(0.005)
    vh = np.float32(-18.0) + rows * np.float32(0.008) + cols * np.float32(0.004)
    angle = np.full((size, size), np.float32(38.5), dtype=np.float32)
    return np.stack([vv, vh, angle], axis=-1).astype(np.float32)


class SarRtcStage(Stage):
    name = "sar_rtc"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(
        self,
        *,
        grid_spec: GridSpec,
        start_date: str = DEFAULT_START,
        end_date: str = DEFAULT_END,
        radar_cube_fetcher: RadarCubeFetcher | None = None,
    ) -> None:
        self.grid_spec = grid_spec
        self.start_date = start_date
        self.end_date = end_date
        self.radar_cube_fetcher = radar_cube_fetcher

    async def run(self, context: StageContext) -> StageResult:
        dem = load_dem_array(context.run_dir)
        fetcher = self.radar_cube_fetcher or create_ee_radar_cube_fetcher(
            context.settings,
            self.grid_spec,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        cube_3 = fetcher(grid_spec=self.grid_spec)
        outputs = apply_local_dem_rtc(cube_3, dem, nodata=self.grid_spec.nodata)
        written_paths = write_sar_outputs(context.run_dir, self.grid_spec, outputs)
        artifacts = [
            build_stage_artifact(
                name=path.stem,
                relative_path=path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=path.stat().st_size,
            )
            for path in written_paths
        ]
        return StageResult(
            artifacts=artifacts,
            metadata={
                "band_names": list(OUTPUT_BANDS),
                "sar_shape": list(outputs["VV_dB"].shape),
                "start_date": self.start_date,
                "end_date": self.end_date,
            },
        )
