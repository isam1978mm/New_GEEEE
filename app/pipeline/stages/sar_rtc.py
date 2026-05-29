from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import ee
import numpy as np

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_canonical_dir, ensure_run_qa_dir
from app.pipeline.stages.dem import DEM_TILE_SIZE, raster_sidecar_path, write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.services.ee_session import initialize_ee_session

DEFAULT_START = "2026-01-01"
DEFAULT_END = "2026-03-01"
S1_COLLECTION_ID = "COPERNICUS/S1_GRD"
SAR_SELECTION_PROFILE = "cell25_pixel_export"
CELL21_MASTER_UNITS_QA_PROFILE = "cell21_master_units_qa_auxiliary"
MAX_ORBIT_DT_DAYS = 9
MAX_PAIR_DT_HOURS = 36
MAX_PAIRS = 4
MIN_PAIRS = 2
MAX_PAIRS_TARGETS = (MAX_PAIRS, 3, 2)
SAR_SIGMA_LEE_SIGMA = 1.0
SAR_SIGMA_LEE_KERNEL_M = 30
SAR_LEE_KERNEL_M = 20
RADAR_BANDS = ("VV_dB", "VH_dB", "angle")
OUTPUT_BANDS = ("VV_dB", "VH_dB", "logRatio_dB", "incidence")
SAR_NPY_OUTPUT_DIR = "npy_radar_bands"
NOTEBOOK_SAR_GEOTIFF_OUTPUT_DIR = "GEOTIFF_RADAR_BANDS"
NOTEBOOK_SAR_NPY_OUTPUT_DIR = "NPY_RADAR_BANDS"
NOTEBOOK_SAR_INTERMEDIATE_DIR = "QA/sar/intermediates"
NOTEBOOK_SAR_OUTPUT_SUFFIX = "app"
SAR_NPY_ARTIFACT_NAMES = {
    "VV_dB": "sar_npy_VV_dB",
    "VH_dB": "sar_npy_VH_dB",
    "logRatio_dB": "sar_npy_logRatio_dB",
    "incidence": "sar_npy_incidence",
}
NOTEBOOK_SAR_BAND_NAMES = {
    "VV_dB": "RADAR_VV_dB",
    "VH_dB": "RADAR_VH_dB",
    "logRatio_dB": "RADAR_logRatio_dB",
    "incidence": "RADAR_angle",
}
APP_BAND_BY_NOTEBOOK_SAR_BAND_NAME = {notebook_name: app_name for app_name, notebook_name in NOTEBOOK_SAR_BAND_NAMES.items()}
NOTEBOOK_SAR_INTERMEDIATE_MISSING_STAGES = (
    "per_image_products_db",
    "pair_median",
    "final_median_pre_rtc",
    "post_sample_pre_rtc",
)
NOTEBOOK_SAR_POST_RTC_BANDS = {
    "VV_dB": "VV_dB",
    "VH_dB": "VH_dB",
    "logRatio_dB": "logRatio_dB",
    "angle": "incidence",
}


class RadarCubeFetcher(Protocol):
    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray: ...


@dataclass(frozen=True, slots=True)
class SarPair:
    asc_id: str
    desc_id: str
    dt_ms: int
    asc_ms: int | None = None
    desc_ms: int | None = None


@dataclass(frozen=True, slots=True)
class SarFetchDiagnostics:
    pairs: list[SarPair]
    tile_request_count: int | None = None


class EeRadarCubeFetcher:
    def __init__(self, *, final_for_sample, requests: list[dict[str, float | int]], grid_spec: GridSpec, diagnostics: SarFetchDiagnostics) -> None:
        self._final_for_sample = final_for_sample
        self._requests = requests
        self._grid_spec = grid_spec
        self.diagnostics = diagnostics

    def __call__(self, *, grid_spec: GridSpec) -> np.ndarray:
        cube = np.full((grid_spec.size, grid_spec.size, len(RADAR_BANDS)), grid_spec.nodata, dtype=np.float32)
        for request in self._requests:
            tile_geo = ee.Geometry.Rectangle(
                [request["xmin"], request["ymin"], request["xmax"], request["ymax"]],
                self._grid_spec.crs,
                False,
            )
            rect = self._final_for_sample.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
            for band_index, band_name in enumerate(RADAR_BANDS):
                data = np.array(rect["properties"][band_name], dtype=np.float32)[: DEM_TILE_SIZE, : DEM_TILE_SIZE]
                row_start = request["tile_row"] * DEM_TILE_SIZE
                col_start = request["tile_col"] * DEM_TILE_SIZE
                cube[row_start : row_start + DEM_TILE_SIZE, col_start : col_start + DEM_TILE_SIZE, band_index] = data
        return cube


def build_grid_region(grid_spec: GridSpec):
    xmin = grid_spec.manifest.bounds_m["xmin"]
    ymin = grid_spec.manifest.bounds_m["ymin"]
    xmax = grid_spec.manifest.bounds_m["xmax"]
    ymax = grid_spec.manifest.bounds_m["ymax"]
    return ee.Geometry.Rectangle([xmin, ymin, xmax, ymax], grid_spec.crs, False)


def build_s1_base_collection(grid_spec: GridSpec, *, start_date: str, end_date: str):
    grid_region = build_grid_region(grid_spec)
    return (
        ee.ImageCollection(S1_COLLECTION_ID)
        .filterBounds(grid_region)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.eq("resolution_meters", 10))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VV", "VH", "angle"])
    )


def ensure_non_empty_pass_collection(collection, *, pass_direction: str, start_date: str, end_date: str) -> None:
    count = int(collection.size().getInfo())
    if count < 1:
        raise StageError(
            f"SAR RTC requires non-empty Sentinel-1 {pass_direction} collections for the configured "
            f"date window ({start_date} to {end_date})."
        )


def pick_best_track(collection, *, pass_direction: str, start_date: str, end_date: str):
    ensure_non_empty_pass_collection(
        collection,
        pass_direction=pass_direction,
        start_date=start_date,
        end_date=end_date,
    )
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
            pairs.append(
                SarPair(
                    asc_id=asc_item["id"],
                    desc_id=desc_item["id"],
                    dt_ms=dt_ms,
                    asc_ms=int(asc_item["ms"]),
                    desc_ms=int(desc_item["ms"]),
                )
            )
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


def _to_linear_from_db(db_image):
    return ee.Image(10).pow(ee.Image(db_image).divide(10.0))


def _to_db_from_linear(linear_image):
    return ee.Image(linear_image).max(1e-12).log10().multiply(10.0)


def _border_noise_mask_db(image_db):
    mask = (
        image_db.select("VV").gt(-35)
        .And(image_db.select("VH").gt(-42))
        .And(image_db.select("angle").gt(29))
        .And(image_db.select("angle").lt(46))
    )
    return image_db.updateMask(mask)


def _lee_filter(linear_image, kernel_m: int):
    kernel = ee.Kernel.square(kernel_m, "meters", True)
    mean = linear_image.reduceNeighborhood(ee.Reducer.mean(), kernel)
    variance = linear_image.reduceNeighborhood(ee.Reducer.variance(), kernel)
    noise_variance = ee.Image.constant(0.25)
    weight = variance.subtract(noise_variance).divide(variance).clamp(0, 1)
    return mean.add(weight.multiply(linear_image.subtract(mean)))


def _sigma_lee_filter(linear_image, kernel_m: int, sigma: float):
    kernel = ee.Kernel.square(kernel_m, "meters", True)
    mean = linear_image.reduceNeighborhood(ee.Reducer.mean(), kernel)
    stddev = linear_image.reduceNeighborhood(ee.Reducer.stdDev(), kernel)
    low = mean.subtract(stddev.multiply(sigma))
    high = mean.add(stddev.multiply(sigma))
    within = linear_image.gte(low).And(linear_image.lte(high))
    lee = _lee_filter(linear_image, kernel_m)
    return linear_image.where(within, lee)


def per_image_products_db(
    image,
    *,
    sigma: float = SAR_SIGMA_LEE_SIGMA,
    kernel_m_sigma: int = SAR_SIGMA_LEE_KERNEL_M,
    kernel_m_ref: int = SAR_LEE_KERNEL_M,
):
    image_db = ee.Image(image).select(["VV", "VH", "angle"])
    image_db = _border_noise_mask_db(image_db)

    vv_linear = _to_linear_from_db(image_db.select("VV"))
    vh_linear = _to_linear_from_db(image_db.select("VH"))

    vv_linear = _sigma_lee_filter(vv_linear, kernel_m_sigma, sigma)
    vh_linear = _sigma_lee_filter(vh_linear, kernel_m_sigma, sigma)
    vv_linear = _lee_filter(vv_linear, kernel_m_ref)
    vh_linear = _lee_filter(vh_linear, kernel_m_ref)

    vv_db = _to_db_from_linear(vv_linear).rename("VV_dB")
    vh_db = _to_db_from_linear(vh_linear).rename("VH_dB")
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
    asc = pick_best_track(
        base.filter(ee.Filter.eq("orbitProperties_pass", "ASCENDING")),
        pass_direction="ASCENDING",
        start_date=start_date,
        end_date=end_date,
    )
    desc = pick_best_track(
        base.filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING")),
        pass_direction="DESCENDING",
        start_date=start_date,
        end_date=end_date,
    )
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
    final_radar, pairs = build_final_radar_image(grid_spec, start_date=start_date, end_date=end_date)
    final_for_sample = finalize_for_sample(final_radar, grid_spec)
    requests = build_sar_tile_requests(grid_spec)
    return EeRadarCubeFetcher(
        final_for_sample=final_for_sample,
        requests=requests,
        grid_spec=grid_spec,
        diagnostics=SarFetchDiagnostics(pairs=list(pairs), tile_request_count=len(requests)),
    )


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


def apply_local_dem_rtc(
    cube_3: np.ndarray,
    dem: np.ndarray,
    *,
    nodata: float,
    scale_m: float,
) -> dict[str, np.ndarray]:
    if cube_3.shape[-1] != 3:
        raise ValueError("SAR cube must contain VV_dB, VH_dB, and angle bands.")
    if cube_3.shape[:2] != dem.shape:
        raise ValueError("DEM shape must match SAR grid shape.")

    dem_float = dem.astype(np.float32, copy=True)
    dem_float = np.where(dem_float == nodata, np.nan, dem_float)
    # The canonical notebook SAR RTC stage performs the local DEM-based
    # RTC/Gamma0 approximation after sampling VV_dB/VH_dB/angle to the GRID.
    # Reproduce that SAR-stage behavior here.
    dz_dy, dz_dx = np.gradient(dem_float, scale_m, scale_m)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    corr = np.cos(slope_rad)
    corr = np.where(np.isfinite(corr), np.maximum(corr, 0.25), np.nan)

    vv_db = cube_3[:, :, 0]
    vh_db = cube_3[:, :, 1]
    angle = cube_3[:, :, 2]

    inc_rad = np.deg2rad(angle)
    cos_inc = np.cos(inc_rad)
    cos_inc = np.where(np.isfinite(cos_inc), np.maximum(cos_inc, 1e-6), np.nan)

    valid = (
        (vv_db != nodata)
        & (vh_db != nodata)
        & np.isfinite(corr)
        & np.isfinite(cos_inc)
    )
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


def write_sar_outputs(run_dir: Path, grid_spec: GridSpec, outputs: dict[str, np.ndarray]) -> list[Path]:
    written_paths: list[Path] = []
    for name, array in outputs.items():
        tif_path = run_dir / f"{name}.tif"
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


def notebook_sar_filename(name: str, extension: str) -> str:
    return f"{NOTEBOOK_SAR_BAND_NAMES[name]}_640_{NOTEBOOK_SAR_OUTPUT_SUFFIX}.{extension}"


def notebook_sar_artifact_name(name: str) -> str:
    return f"notebook_{NOTEBOOK_SAR_BAND_NAMES[name]}_640"


def notebook_sar_npy_artifact_name(name: str) -> str:
    return f"notebook_sar_npy_{NOTEBOOK_SAR_BAND_NAMES[name]}_640"


def _app_band_name_from_notebook_stem(stem: str) -> str:
    notebook_band_name = stem.removesuffix(f"_640_{NOTEBOOK_SAR_OUTPUT_SUFFIX}")
    return APP_BAND_BY_NOTEBOOK_SAR_BAND_NAME[notebook_band_name]


def write_notebook_sar_geotiff_outputs(run_dir: Path, grid_spec: GridSpec, outputs: dict[str, np.ndarray]) -> list[Path]:
    output_dir = run_dir / NOTEBOOK_SAR_GEOTIFF_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []
    for name in OUTPUT_BANDS:
        tif_path = output_dir / notebook_sar_filename(name, "tif")
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


def write_sar_npy_outputs(run_dir: Path, outputs: dict[str, np.ndarray]) -> list[Path]:
    output_dir = run_dir / SAR_NPY_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []
    for name in OUTPUT_BANDS:
        npy_path = output_dir / f"{name}.npy"
        np.save(npy_path, outputs[name].astype(np.float32, copy=False))
        written_paths.append(npy_path)
    return written_paths


def write_notebook_sar_npy_outputs(run_dir: Path, outputs: dict[str, np.ndarray]) -> list[Path]:
    output_dir = ensure_run_canonical_dir(run_dir, NOTEBOOK_SAR_NPY_OUTPUT_DIR)
    written_paths: list[Path] = []
    for name in OUTPUT_BANDS:
        npy_path = output_dir / notebook_sar_filename(name, "npy")
        np.save(npy_path, outputs[name].astype(np.float32, copy=False))
        written_paths.append(npy_path)
    return written_paths


def write_notebook_sar_intermediate_outputs(run_dir: Path, outputs: dict[str, np.ndarray]) -> list[Path]:
    base_dir = ensure_run_qa_dir(run_dir) / "sar" / "intermediates"
    post_rtc_dir = base_dir / "post_rtc"
    post_rtc_dir.mkdir(parents=True, exist_ok=True)

    bands: dict[str, str] = {}
    source_mapping: dict[str, str] = {}
    written_npy_paths: list[Path] = []
    for notebook_band, app_band in NOTEBOOK_SAR_POST_RTC_BANDS.items():
        filename = f"final_{notebook_band}.npy"
        npy_path = post_rtc_dir / filename
        np.save(npy_path, outputs[app_band].astype(np.float32, copy=False))
        bands[notebook_band] = f"post_rtc/{filename}"
        source_mapping[f"post_rtc/{filename}"] = f"{SAR_NPY_OUTPUT_DIR}/{app_band}.npy"
        written_npy_paths.append(npy_path)

    manifest_path = base_dir / "sar_intermediate_manifest.json"
    stages = {
        stage_name: {
            "status": "not_implemented_no_source_equivalent",
            "items": [],
            "missing_reason": "The production SAR stage does not persist this notebook intermediate before post-RTC output.",
        }
        for stage_name in NOTEBOOK_SAR_INTERMEDIATE_MISSING_STAGES
    }
    stages["post_rtc"] = {
        "status": "implemented",
        "bands": bands,
        "source_mapping": source_mapping,
        "source_description": (
            "QA post-RTC arrays are byte-equal copies of the canonical final SAR arrays under "
            f"{SAR_NPY_OUTPUT_DIR}/, persisted here in notebook QA layout."
        ),
    }
    payload = {
        "schema": "notebook_sar_intermediates_v1",
        "stage": "sar_rtc",
        "local_only": True,
        "stages": stages,
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return [manifest_path, *written_npy_paths]


def _notebook_sar_intermediate_artifact_name(path: Path) -> str:
    if path.name == "sar_intermediate_manifest.json":
        return "notebook_sar_intermediate_manifest"
    band_name = path.stem.removeprefix("final_")
    return f"notebook_sar_intermediate_post_rtc_{band_name}"


def build_band_summary_rows(outputs: dict[str, np.ndarray], *, nodata: float) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for band_name in OUTPUT_BANDS:
        array = outputs[band_name]
        valid_mask = array != nodata
        valid_values = array[valid_mask]
        valid_count = int(valid_mask.sum())
        nodata_count = int(array.size - valid_count)
        row = {
            "band_name": band_name,
            "valid_count": str(valid_count),
            "nodata_count": str(nodata_count),
            "nodata_fraction": f"{(nodata_count / array.size):.6f}",
            "min": "",
            "max": "",
            "mean": "",
        }
        if valid_count > 0:
            row["min"] = f"{float(valid_values.min()):.6f}"
            row["max"] = f"{float(valid_values.max()):.6f}"
            row["mean"] = f"{float(valid_values.mean()):.6f}"
        rows.append(row)
    return rows


def build_nodata_audit_rows(outputs: dict[str, np.ndarray], *, nodata: float) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for band_name in OUTPUT_BANDS:
        array = outputs[band_name]
        nodata_count = int((array == nodata).sum())
        rows.append(
            {
                "band_name": band_name,
                "total_pixels": str(int(array.size)),
                "nodata_count": str(nodata_count),
                "nodata_fraction": f"{(nodata_count / array.size):.6f}",
                "all_nodata": str(nodata_count == int(array.size)).lower(),
            }
        )
    return rows


def build_pair_diagnostics_payload(
    *,
    start_date: str,
    end_date: str,
    diagnostics: SarFetchDiagnostics | None,
) -> dict[str, Any]:
    pairs = diagnostics.pairs if diagnostics is not None else []
    return {
        "stage": "sar_rtc",
        "artifact_class": "FILESYSTEM_ONLY",
        "local_only": True,
        "collection_id": S1_COLLECTION_ID,
        "start_date": start_date,
        "end_date": end_date,
        "date_window": {"start_date": start_date, "end_date": end_date},
        "roi_grid_label": "run_grid",
        "source_filters": {
            "selection_profile": SAR_SELECTION_PROFILE,
            "pixel_output_source_cell": "Cell 25",
            "auxiliary_master_units_profile": CELL21_MASTER_UNITS_QA_PROFILE,
            "auxiliary_master_units_source_cell": "Cell 21",
            "instrumentMode": "IW",
            "resolution_meters": 10,
            "polarizations": ["VV", "VH"],
            "orbit_directions": ["ASCENDING", "DESCENDING"],
            "max_orbit_dt_days": MAX_ORBIT_DT_DAYS,
            "max_pair_dt_hours": MAX_PAIR_DT_HOURS,
            "max_pairs": MAX_PAIRS,
            "min_pairs": MIN_PAIRS,
            "max_pairs_targets": list(MAX_PAIRS_TARGETS),
        },
        "selected_band_list": ["VV", "VH", "angle"],
        "sampled_band_list": list(RADAR_BANDS),
        "output_band_list": list(OUTPUT_BANDS),
        "angle_incidence_mapping": {
            "notebook_band": "angle",
            "app_output_band": "incidence",
            "relationship": "incidence stores the sampled raw Sentinel-1 angle band where angle is not nodata.",
        },
        "processing_path": {
            "notebook_source_cells": ["Cell 22", "Cell 24", "Cell 25"],
            "local_dem_rtc": True,
            "speckle_sigma_lee_filtering": True,
            "speckle_lee_filtering": True,
            "speckle_refined_lee_filtering": False,
            "border_noise_mask_db": True,
            "db_to_linear_to_db": True,
            "grid_sampling": "sampleRectangle",
        },
        "pair_diagnostics_available": diagnostics is not None,
        "pair_count": len(pairs),
        "tile_request_count": diagnostics.tile_request_count if diagnostics is not None else None,
        "pairs": [
            {
                "asc_id": pair.asc_id,
                "desc_id": pair.desc_id,
                "asc_date": _ms_to_iso_date(pair.asc_ms),
                "desc_date": _ms_to_iso_date(pair.desc_ms),
                "dt_hours": round(pair.dt_ms / (60.0 * 60.0 * 1000.0), 6),
            }
            for pair in pairs
        ],
    }


def _ms_to_iso_date(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000.0, tz=UTC).date().isoformat()


def build_alignment_summary_payload(
    outputs: dict[str, np.ndarray],
    *,
    diagnostics: SarFetchDiagnostics | None,
) -> dict[str, Any]:
    shape = list(outputs["VV_dB"].shape)
    return {
        "stage": "sar_rtc",
        "band_names": list(OUTPUT_BANDS),
        "expected_shape": shape,
        "all_shapes_match": all(list(array.shape) == shape for array in outputs.values()),
        "all_float32": all(array.dtype == np.float32 for array in outputs.values()),
        "tile_request_count": diagnostics.tile_request_count if diagnostics is not None else None,
        "pair_count": len(diagnostics.pairs) if diagnostics is not None else 0,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv_rows(path: Path, rows: list[dict[str, str]], *, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_sar_qa_outputs(
    run_dir: Path,
    *,
    outputs: dict[str, np.ndarray],
    nodata: float,
    start_date: str,
    end_date: str,
    diagnostics: SarFetchDiagnostics | None,
) -> list[Path]:
    sar_qa_dir = ensure_run_qa_dir(run_dir) / "sar"
    pair_diagnostics_path = sar_qa_dir / "sar_pair_diagnostics.json"
    summary_path = sar_qa_dir / "sar_summary.csv"
    nodata_audit_path = sar_qa_dir / "sar_nodata_audit.csv"
    alignment_summary_path = sar_qa_dir / "sar_alignment_summary.json"

    write_json(
        pair_diagnostics_path,
        build_pair_diagnostics_payload(start_date=start_date, end_date=end_date, diagnostics=diagnostics),
    )
    write_csv_rows(
        summary_path,
        build_band_summary_rows(outputs, nodata=nodata),
        fieldnames=["band_name", "valid_count", "nodata_count", "nodata_fraction", "min", "max", "mean"],
    )
    write_csv_rows(
        nodata_audit_path,
        build_nodata_audit_rows(outputs, nodata=nodata),
        fieldnames=["band_name", "total_pixels", "nodata_count", "nodata_fraction", "all_nodata"],
    )
    write_json(
        alignment_summary_path,
        build_alignment_summary_payload(outputs, diagnostics=diagnostics),
    )
    return [pair_diagnostics_path, summary_path, nodata_audit_path, alignment_summary_path]


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
        diagnostics = getattr(fetcher, "diagnostics", None)
        outputs = apply_local_dem_rtc(
            cube_3,
            dem,
            nodata=self.grid_spec.nodata,
            scale_m=float(self.grid_spec.manifest.scale_m),
        )
        written_paths = write_sar_outputs(context.run_dir, self.grid_spec, outputs)
        notebook_tif_paths = write_notebook_sar_geotiff_outputs(context.run_dir, self.grid_spec, outputs)
        npy_paths = write_sar_npy_outputs(context.run_dir, outputs)
        notebook_npy_paths = write_notebook_sar_npy_outputs(context.run_dir, outputs)
        notebook_intermediate_paths = write_notebook_sar_intermediate_outputs(context.run_dir, outputs)
        qa_paths = write_sar_qa_outputs(
            context.run_dir,
            outputs=outputs,
            nodata=self.grid_spec.nodata,
            start_date=self.start_date,
            end_date=self.end_date,
            diagnostics=diagnostics,
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
            build_stage_artifact(
                name=notebook_sar_artifact_name(_app_band_name_from_notebook_stem(path.stem)),
                relative_path=path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=path.stat().st_size,
            )
            for path in notebook_tif_paths
        )
        artifacts.extend(
            build_stage_artifact(
                name=SAR_NPY_ARTIFACT_NAMES[path.stem],
                relative_path=path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=path.stat().st_size,
                http_servable=False,
            )
            for path in npy_paths
        )
        artifacts.extend(
            build_stage_artifact(
                name=notebook_sar_npy_artifact_name(_app_band_name_from_notebook_stem(path.stem)),
                relative_path=path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=path.stat().st_size,
                http_servable=False,
            )
            for path in notebook_npy_paths
        )
        artifacts.extend(
            build_stage_artifact(
                name=_notebook_sar_intermediate_artifact_name(path),
                relative_path=path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=path.stat().st_size,
                http_servable=False,
            )
            for path in notebook_intermediate_paths
        )
        artifacts.extend(
            build_stage_artifact(
                name=path.stem,
                relative_path=path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=path.stat().st_size,
                http_servable=False,
            )
            for path in qa_paths
        )
        return StageResult(
            artifacts=artifacts,
            metadata={
                "band_names": list(OUTPUT_BANDS),
                "sar_shape": list(outputs["VV_dB"].shape),
                "start_date": self.start_date,
                "end_date": self.end_date,
                "sar_npy_artifact_names": [SAR_NPY_ARTIFACT_NAMES[path.stem] for path in npy_paths],
                "qa_artifact_names": [path.stem for path in qa_paths],
            },
        )
