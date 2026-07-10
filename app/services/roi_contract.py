from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from pyproj import Transformer

from app.config import Settings
from app.services.grid import GridManifest, build_grid_manifest
from app.services.storage import initialize_run_storage, write_json_atomic

ROI_CONTRACT_RELATIVE_PATH = "PRIVATE/RUN_ROI_CONTRACT.json"
ROI_CONTRACT_SCHEMA = "notebook_roi_contract_v1"
DEFAULT_SEARCH_ROI_SIDE_KM = 15.0


def build_run_roi_contract(
    *,
    latitude: float,
    longitude: float,
    grid_manifest: GridManifest | None = None,
) -> dict[str, Any]:
    """Build the private notebook-compatible point/ROI/GRID contract for a run.

    This is the app-native replacement for the notebook map-picker cells:
    selected point -> WGS84 search ROI -> exact 6.4 km UTM processing ROI ->
    authoritative GRID dict.

    The returned payload intentionally contains raw coordinates, bounds, and
    transforms, so it must remain local/private and must not be exposed through
    public APIs or operator-visible output listings.
    """

    lat = _coerce_coordinate(latitude, minimum=-90.0, maximum=90.0, label="latitude")
    lon = _coerce_coordinate(longitude, minimum=-180.0, maximum=180.0, label="longitude")
    grid = grid_manifest or build_grid_manifest(lat, lon)
    crs = f"EPSG:{grid.epsg}"

    transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    center_x, center_y = transformer.transform(lon, lat)
    bounds = _normalized_bounds(grid)
    processing_roi_polygon = _utm_polygon_from_bounds(bounds)
    search_roi_polygon = _approx_wgs84_square(lon=lon, lat=lat, side_km=DEFAULT_SEARCH_ROI_SIDE_KM)

    return {
        "schema": ROI_CONTRACT_SCHEMA,
        "source_notebook_inventory": {
            "map_point_picker_roi": "Phase B cells 9-13",
            "run_folder_grid_manifest": "Phase C cell 14",
        },
        "selected_point": {
            "crs": "EPSG:4326",
            "latitude": lat,
            "longitude": lon,
            "utm": {
                "crs": crs,
                "easting_m": float(center_x),
                "northing_m": float(center_y),
            },
        },
        "roi_15km_wgs84_approx": {
            "purpose": "Notebook-style search/acquisition ROI centered on the selected point.",
            "method": "degree_approx_square_centered_on_selected_point",
            "side_length_km": DEFAULT_SEARCH_ROI_SIDE_KM,
            "coordinates_lon_lat": search_roi_polygon,
        },
        "roi_6_4km_utm": {
            "purpose": "Exact processing ROI used by the 640 x 640 at 10 m master grid.",
            "crs": crs,
            "side_length_m": float(grid.scale_m * grid.size_px),
            "bounds_m": bounds,
            "coordinates_xy_m": processing_roi_polygon,
        },
        "grid": {
            "crs": crs,
            "epsg": int(grid.epsg),
            "utm_zone": int(grid.utm_zone),
            "hemisphere": grid.hemisphere,
            "scale_m": int(grid.scale_m),
            "size_px": int(grid.size_px),
            "crs_transform": [float(value) for value in grid.crs_transform],
            "bounds_m": bounds,
        },
        "notebook_grid_dict": {
            "CRS": crs,
            "SCALE": float(grid.scale_m),
            "OUT_SIZE": int(grid.size_px),
            "crsTransform": [float(value) for value in grid.crs_transform],
            "bounds_utm": [bounds["xmin"], bounds["ymin"], bounds["xmax"], bounds["ymax"]],
        },
        "privacy": {
            "artifact_class": "LOCAL_SENSITIVE",
            "public_api_exposure": "forbidden",
            "operator_output_listing": "forbidden",
        },
    }


def write_run_roi_contract(
    *,
    settings: Settings,
    run_id: str,
    latitude: float,
    longitude: float,
    grid_manifest: GridManifest | None = None,
) -> Path:
    contract = build_run_roi_contract(latitude=latitude, longitude=longitude, grid_manifest=grid_manifest)
    return write_run_roi_contract_payload(settings=settings, run_id=run_id, contract=contract)


def build_run_roi_contract_from_grid_manifest(*, grid_manifest: GridManifest) -> dict[str, Any]:
    """Rebuild the private ROI contract from an authoritative GRID manifest.

    This lets save_grid_manifest() create the A1 contract without duplicating
    run-creation logic. The selected point is recovered from the exact UTM grid
    center and transformed back to WGS84.
    """

    bounds = _normalized_bounds(grid_manifest)
    center_x = (bounds["xmin"] + bounds["xmax"]) / 2.0
    center_y = (bounds["ymin"] + bounds["ymax"]) / 2.0
    crs = f"EPSG:{grid_manifest.epsg}"
    transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(center_x, center_y)
    return build_run_roi_contract(latitude=float(lat), longitude=float(lon), grid_manifest=grid_manifest)


def write_run_roi_contract_from_grid_manifest(
    *,
    settings: Settings,
    run_id: str,
    grid_manifest: GridManifest,
) -> Path:
    contract = build_run_roi_contract_from_grid_manifest(grid_manifest=grid_manifest)
    return write_run_roi_contract_payload(settings=settings, run_id=run_id, contract=contract)


def write_run_roi_contract_payload(*, settings: Settings, run_id: str, contract: dict[str, Any]) -> Path:
    run_dir = initialize_run_storage(settings, run_id)
    path = run_dir / ROI_CONTRACT_RELATIVE_PATH
    write_json_atomic(path, contract, indent=2, sort_keys=True)
    return path


def _coerce_coordinate(value: float, *, minimum: float, maximum: float, label: str) -> float:
    try:
        coordinate = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric.") from exc
    if coordinate < minimum or coordinate > maximum:
        raise ValueError(f"{label} is outside the allowed range.")
    return coordinate


def _normalized_bounds(grid: GridManifest) -> dict[str, float]:
    return {
        "xmin": float(grid.bounds_m["xmin"]),
        "ymin": float(grid.bounds_m["ymin"]),
        "xmax": float(grid.bounds_m["xmax"]),
        "ymax": float(grid.bounds_m["ymax"]),
    }


def _utm_polygon_from_bounds(bounds: dict[str, float]) -> list[list[float]]:
    xmin = float(bounds["xmin"])
    ymin = float(bounds["ymin"])
    xmax = float(bounds["xmax"])
    ymax = float(bounds["ymax"])
    return [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax], [xmin, ymin]]


def _approx_wgs84_square(*, lon: float, lat: float, side_km: float) -> list[list[float]]:
    half_side_km = float(side_km) / 2.0
    lat_delta = half_side_km / 111.32
    cos_lat = abs(math.cos(math.radians(lat)))
    if cos_lat < 1.0e-6:
        lon_delta = 180.0
    else:
        lon_delta = half_side_km / (111.32 * cos_lat)
    west = max(-180.0, lon - lon_delta)
    east = min(180.0, lon + lon_delta)
    south = max(-90.0, lat - lat_delta)
    north = min(90.0, lat + lat_delta)
    return [[west, south], [east, south], [east, north], [west, north], [west, south]]
