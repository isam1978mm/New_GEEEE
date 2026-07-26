"""Validate provisional Sconondoa polygons against official NYS 2022 orthoimagery.

This script is intentionally separate from Earth Engine. It downloads only the
intersecting official NYS ortho tile(s), crops a small QA image around the two
provisional polygons, overlays the polygons and official building footprints,
and writes a machine-readable report. It does not mark the polygons execution
ready; the produced overlay must be reviewed first.
"""
from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import matplotlib.pyplot as plt
import numpy as np
import rasterio
import requests
from pyproj import Transformer
from rasterio.merge import merge
from rasterio.windows import from_bounds
from shapely.geometry import shape, mapping, box
from shapely.ops import transform as shapely_transform

INDEX_QUERY = (
    "https://orthos.its.ny.gov/arcgis/rest/services/vector/ortho_indexes/"
    "MapServer/14/query"
)
BUILDING_QUERY = (
    "https://gisservices.its.ny.gov/arcgis/rest/services/"
    "BuildingFootprints/FeatureServer/2/query"
)
FALLBACK_ZIP = (
    "https://gisdata.ny.gov/ortho/nysdop10/madison/spcs/zips/"
    "city_Oneida_sp22.zip"
)


def request_json(url: str, params: dict[str, object], timeout: int = 90) -> dict:
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(f"ArcGIS error from {url}: {payload['error']}")
    return payload


def feature_bbox_wgs84(payload: dict, margin_deg: float = 0.0012) -> tuple[float, float, float, float]:
    geometries = [shape(feature["geometry"]) for feature in payload["features"]]
    xmin = min(item.bounds[0] for item in geometries) - margin_deg
    ymin = min(item.bounds[1] for item in geometries) - margin_deg
    xmax = max(item.bounds[2] for item in geometries) + margin_deg
    ymax = max(item.bounds[3] for item in geometries) + margin_deg
    return xmin, ymin, xmax, ymax


def query_tile_index(bounds: tuple[float, float, float, float]) -> dict:
    xmin, ymin, xmax, ymax = bounds
    return request_json(
        INDEX_QUERY,
        {
            "f": "json",
            "where": "1=1",
            "geometry": f"{xmin},{ymin},{xmax},{ymax}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": 4326,
        },
    )


def find_download_urls(index_payload: dict) -> list[str]:
    urls: list[str] = []
    for feature in index_payload.get("features", []):
        for value in feature.get("attributes", {}).values():
            if not isinstance(value, str):
                continue
            text = value.strip()
            if text.lower().startswith(("http://", "https://")) and (
                ".zip" in text.lower() or "download" in text.lower()
            ):
                urls.append(text)
    # Preserve order while removing duplicates.
    return list(dict.fromkeys(urls))


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)


def extract_rasters(zip_path: Path, destination: Path) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    supported = {".tif", ".tiff", ".jp2", ".img"}
    paths: list[Path] = []
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if Path(member.filename).suffix.lower() not in supported:
                continue
            member.filename = Path(member.filename).name
            archive.extract(member, destination)
            paths.append(destination / member.filename)
    return paths


def raster_intersects_wgs84(path: Path, bounds_wgs84: tuple[float, float, float, float]) -> bool:
    try:
        with rasterio.open(path) as dataset:
            to_src = Transformer.from_crs(4326, dataset.crs, always_xy=True)
            xmin, ymin = to_src.transform(bounds_wgs84[0], bounds_wgs84[1])
            xmax, ymax = to_src.transform(bounds_wgs84[2], bounds_wgs84[3])
            return box(*dataset.bounds).intersects(box(min(xmin, xmax), min(ymin, ymax), max(xmin, xmax), max(ymin, ymax)))
    except Exception:
        return False


def crop_mosaic(rasters: list[Path], bounds_wgs84: tuple[float, float, float, float], output_tif: Path) -> tuple[np.ndarray, rasterio.Affine, object]:
    relevant = [path for path in rasters if raster_intersects_wgs84(path, bounds_wgs84)]
    if not relevant:
        raise RuntimeError("No extracted ortho raster intersects the QA polygon bounds")
    sources = [rasterio.open(path) for path in relevant]
    try:
        target_crs = sources[0].crs
        if any(source.crs != target_crs for source in sources):
            raise RuntimeError("Intersecting ortho rasters do not share one CRS")
        to_src = Transformer.from_crs(4326, target_crs, always_xy=True)
        x1, y1 = to_src.transform(bounds_wgs84[0], bounds_wgs84[1])
        x2, y2 = to_src.transform(bounds_wgs84[2], bounds_wgs84[3])
        crop_bounds = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        mosaic, transform = merge(sources, bounds=crop_bounds)
        profile = sources[0].profile.copy()
        profile.update(
            driver="GTiff",
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            transform=transform,
            count=mosaic.shape[0],
            compress="deflate",
        )
        output_tif.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(output_tif, "w", **profile) as output:
            output.write(mosaic)
        return mosaic, transform, target_crs
    finally:
        for source in sources:
            source.close()


def query_buildings(bounds: tuple[float, float, float, float]) -> dict:
    xmin, ymin, xmax, ymax = bounds
    return request_json(
        BUILDING_QUERY,
        {
            "f": "geojson",
            "where": "1=1",
            "geometry": f"{xmin},{ymin},{xmax},{ymax}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": 4326,
        },
    )


def normalize_rgb(array: np.ndarray) -> np.ndarray:
    if array.shape[0] < 3:
        rgb = np.repeat(array[:1], 3, axis=0)
    else:
        rgb = array[:3]
    rgb = np.moveaxis(rgb, 0, -1).astype(np.float32)
    output = np.zeros_like(rgb, dtype=np.float32)
    for band in range(3):
        values = rgb[:, :, band]
        valid = values[np.isfinite(values)]
        if not valid.size:
            continue
        low, high = np.percentile(valid, (2, 98))
        if high <= low:
            high = low + 1
        output[:, :, band] = np.clip((values - low) / (high - low), 0, 1)
    return output


def plot_overlay(
    mosaic: np.ndarray,
    transform: rasterio.Affine,
    raster_crs: object,
    qa_payload: dict,
    buildings: dict,
    output_png: Path,
) -> dict:
    rgb = normalize_rgb(mosaic)
    height, width = rgb.shape[:2]
    left, top = transform * (0, 0)
    right, bottom = transform * (width, height)
    to_raster = Transformer.from_crs(4326, raster_crs, always_xy=True).transform

    fig, axis = plt.subplots(figsize=(12, 12))
    axis.imshow(rgb, extent=(left, right, bottom, top), origin="upper")

    zone_metrics: list[dict[str, object]] = []
    for feature in qa_payload["features"]:
        geom = shapely_transform(to_raster, shape(feature["geometry"]))
        x, y = geom.exterior.xy
        axis.plot(x, y, linewidth=3, label=feature["properties"]["zone_id"])
        axis.fill(x, y, alpha=0.16)
        centroid = geom.centroid
        axis.text(centroid.x, centroid.y, feature["properties"]["class"].upper(), fontsize=11)
        zone_metrics.append(
            {
                "zone_id": feature["properties"]["zone_id"],
                "centroid_raster_crs": [centroid.x, centroid.y],
                "area_raster_units_squared": geom.area,
            }
        )

    building_count = 0
    for feature in buildings.get("features", []):
        geom = shapely_transform(to_raster, shape(feature["geometry"]))
        if geom.geom_type == "Polygon":
            polygons = [geom]
        elif geom.geom_type == "MultiPolygon":
            polygons = list(geom.geoms)
        else:
            continue
        for polygon in polygons:
            x, y = polygon.exterior.xy
            axis.plot(x, y, linestyle="--", linewidth=1.5)
            building_count += 1

    axis.set_title("Sconondoa Phase 3 QA polygons on official NYS 2022 ortho")
    axis.set_aspect("equal")
    axis.legend(loc="best")
    fig.tight_layout()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=180)
    plt.close(fig)
    return {"official_building_polygon_count": building_count, "zones": zone_metrics}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    qa_path = repo_root / "data/sconondoa_phase3_depth_ordering_qa_only.geojson"
    output_dir = repo_root / "artifacts/sconondoa_ortho_validation"
    work_dir = output_dir / "work"
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    qa_payload = json.loads(qa_path.read_text(encoding="utf-8"))
    bounds = feature_bbox_wgs84(qa_payload)
    index_payload = query_tile_index(bounds)
    (output_dir / "official_tile_index_query.json").write_text(
        json.dumps(index_payload, indent=2), encoding="utf-8"
    )
    urls = find_download_urls(index_payload)
    used_fallback = False
    if not urls:
        urls = [FALLBACK_ZIP]
        used_fallback = True

    all_rasters: list[Path] = []
    downloads: list[dict[str, object]] = []
    for index, url in enumerate(urls, start=1):
        filename = Path(urlparse(url).path).name or f"ortho_{index}.zip"
        zip_path = work_dir / filename
        download_file(url, zip_path)
        extract_dir = work_dir / f"extract_{index}"
        rasters = extract_rasters(zip_path, extract_dir)
        all_rasters.extend(rasters)
        downloads.append(
            {
                "url": url,
                "zip_bytes": zip_path.stat().st_size,
                "extracted_raster_count": len(rasters),
            }
        )

    if not all_rasters:
        raise RuntimeError("Official ortho download contained no supported raster files")

    mosaic, transform, raster_crs = crop_mosaic(
        all_rasters,
        bounds,
        output_dir / "sconondoa_2022_ortho_crop.tif",
    )
    try:
        buildings = query_buildings(bounds)
    except Exception as exc:
        buildings = {"type": "FeatureCollection", "features": [], "query_error": str(exc)}
    (output_dir / "official_building_footprints.geojson").write_text(
        json.dumps(buildings, indent=2), encoding="utf-8"
    )
    plot_metrics = plot_overlay(
        mosaic,
        transform,
        raster_crs,
        qa_payload,
        buildings,
        output_dir / "sconondoa_2022_ortho_overlay.png",
    )

    report = {
        "status": "OFFICIAL_ORTHO_OVERLAY_CREATED_MANUAL_REVIEW_REQUIRED",
        "earth_engine_query_executed": False,
        "source": "NYS 2022 one-foot four-band ortho index and imagery",
        "index_service": INDEX_QUERY,
        "building_service": BUILDING_QUERY,
        "qa_bounds_wgs84": bounds,
        "index_feature_count": len(index_payload.get("features", [])),
        "download_urls": urls,
        "used_citywide_fallback_zip": used_fallback,
        "downloads": downloads,
        "ortho_crs": str(raster_crs),
        "ortho_shape": list(mosaic.shape),
        "overlay": plot_metrics,
        "decision": "HOLD_UNTIL_OVERLAY_VISUALLY_REVIEWED",
    }
    (output_dir / "validation_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    shutil.rmtree(work_dir, ignore_errors=True)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "validation_failed", "error": str(exc)}), file=sys.stderr)
        raise
