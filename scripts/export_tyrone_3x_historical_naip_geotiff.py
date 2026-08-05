#!/usr/bin/env python3
"""Export georeferenced historical NAIP mosaics for Tyrone No. 3X.

This is a research-only Route B support tool.  It exports the verified No. 3X
cross-row AOI as RGB GeoTIFFs in NAD83 / UTM zone 13N (EPSG:26913), records the
actual raster affine transform and bounds, and keeps all depth-enablement gates
closed.

The JPEG review packs created by ``probe_tyrone_3x_historical_naip`` are useful
for visual screening but do not contain an explicit pixel geotransform.  These
GeoTIFFs are the coordinate-controlled source required before drawing-to-map
control points can be audited in metres.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from scripts.probe_tyrone_3x_historical_naip import TYRONE_3X_BBOX
from scripts.probe_tyrone_historical_naip import (
    COLLECTION_ID,
    HistoricalNaipError,
    build_year_mosaic,
    initialize_ee,
    query_collection,
    summarize_dates,
)

TARGET_CRS = "EPSG:26913"
DEFAULT_SCALE_M = 1.0
DEFAULT_YEARS = (2009, 2011)
DEFAULT_TIMEOUT_SECONDS = 180
MANIFEST_NAME = "tyrone_3x_historical_naip_geotiff_manifest.json"


class GeotiffExportError(RuntimeError):
    """Raised when a coordinate-controlled NAIP export cannot be completed."""


def parse_years(raw: str) -> tuple[int, ...]:
    values: list[int] = []
    for part in raw.split(","):
        text = part.strip()
        if not text:
            continue
        try:
            year = int(text)
        except ValueError as exc:
            raise ValueError("years must be comma-separated integers") from exc
        if year < 2002 or year > 2100:
            raise ValueError("years must be between 2002 and 2100")
        if year not in values:
            values.append(year)
    if not values:
        raise ValueError("at least one year is required")
    return tuple(values)


def build_download_params(*, region: Any, scale_m: float) -> dict[str, Any]:
    if not math.isfinite(scale_m) or scale_m <= 0:
        raise ValueError("scale-m must be positive and finite")
    return {
        "bands": ["R", "G", "B"],
        "region": region,
        "crs": TARGET_CRS,
        "scale": float(scale_m),
        "format": "GEO_TIFF",
        "filePerBand": False,
    }


def get_download_url(image: Any, *, region: Any, scale_m: float) -> str:
    try:
        value = image.getDownloadURL(
            build_download_params(region=region, scale_m=scale_m)
        )
    except Exception as exc:
        raise GeotiffExportError(f"failed to create GeoTIFF download URL: {exc}") from exc
    if not isinstance(value, str) or not value.startswith(("https://", "http://")):
        raise GeotiffExportError("Earth Engine returned an invalid GeoTIFF URL")
    return value


def download_geotiff(url: str, *, timeout_seconds: int) -> bytes:
    if timeout_seconds <= 0:
        raise ValueError("timeout-seconds must be positive")
    request = Request(
        url,
        headers={
            "User-Agent": "New-GEE-Tyrone-3X-NAIP-GeoTIFF/1.0",
            "Accept": "image/tiff,application/octet-stream,*/*;q=0.1",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            payload = response.read()
    except Exception as exc:
        raise GeotiffExportError(f"GeoTIFF download failed: {exc}") from exc
    if len(payload) < 4096:
        raise GeotiffExportError("GeoTIFF response was unexpectedly small")
    if payload[:4] not in {b"II*\x00", b"MM\x00*"}:
        raise GeotiffExportError("downloaded payload is not a TIFF file")
    return payload


def inspect_geotiff(path: Path, *, requested_scale_m: float) -> dict[str, Any]:
    try:
        import rasterio
    except ImportError as exc:
        raise GeotiffExportError("rasterio is required to inspect GeoTIFF metadata") from exc

    try:
        with rasterio.open(path) as dataset:
            if dataset.crs is None:
                raise GeotiffExportError("GeoTIFF has no CRS")
            actual_crs = dataset.crs.to_string().upper()
            if actual_crs != TARGET_CRS:
                raise GeotiffExportError(
                    f"GeoTIFF CRS mismatch: expected {TARGET_CRS}, got {actual_crs}"
                )
            if dataset.count < 3:
                raise GeotiffExportError("GeoTIFF does not contain three RGB bands")
            transform = dataset.transform
            x_resolution = abs(float(transform.a))
            y_resolution = abs(float(transform.e))
            tolerance = max(0.05, requested_scale_m * 0.10)
            if abs(x_resolution - requested_scale_m) > tolerance:
                raise GeotiffExportError(
                    f"unexpected x resolution: {x_resolution} m"
                )
            if abs(y_resolution - requested_scale_m) > tolerance:
                raise GeotiffExportError(
                    f"unexpected y resolution: {y_resolution} m"
                )
            bounds = dataset.bounds
            return {
                "path": str(path.resolve()),
                "crs": actual_crs,
                "width": int(dataset.width),
                "height": int(dataset.height),
                "band_count": int(dataset.count),
                "dtype": [str(value) for value in dataset.dtypes],
                "pixel_size_m": {
                    "x": x_resolution,
                    "y": y_resolution,
                },
                "affine_transform": [
                    float(transform.a),
                    float(transform.b),
                    float(transform.c),
                    float(transform.d),
                    float(transform.e),
                    float(transform.f),
                ],
                "bounds_m": {
                    "left": float(bounds.left),
                    "bottom": float(bounds.bottom),
                    "right": float(bounds.right),
                    "top": float(bounds.top),
                },
            }
    except GeotiffExportError:
        raise
    except Exception as exc:
        raise GeotiffExportError(f"cannot inspect GeoTIFF: {exc}") from exc


def write_manifest(
    *,
    output_dir: Path,
    ee_project: str | None,
    scale_m: float,
    source_image_count: int,
    acquisition_dates: list[str],
    source_image_ids: list[Any],
    requested_years: tuple[int, ...],
    exports: list[dict[str, Any]],
) -> Path:
    path = output_dir / MANIFEST_NAME
    payload = {
        "schema": "tyrone_3x_historical_naip_geotiff_manifest_v1",
        "status": (
            "historical_naip_geotiffs_created"
            if exports
            else "no_requested_historical_naip_geotiffs_created"
        ),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "collection_id": COLLECTION_ID,
        "earth_engine_project": ee_project,
        "target_crs": TARGET_CRS,
        "requested_scale_m": scale_m,
        "bbox_wgs84": {
            "west": TYRONE_3X_BBOX[0],
            "south": TYRONE_3X_BBOX[1],
            "east": TYRONE_3X_BBOX[2],
            "north": TYRONE_3X_BBOX[3],
        },
        "requested_years": list(requested_years),
        "source_image_count": source_image_count,
        "acquisition_dates": acquisition_dates,
        "source_image_ids": [str(value) for value in source_image_ids],
        "exports": exports,
        "purpose": (
            "Provide an explicit projected CRS and pixel affine transform for "
            "manual Figure 2 control-point drafting and independent audit."
        ),
        "does_not_prove": [
            "correct Figure 2 control-point identification",
            "a passing independent georeference audit",
            "official survey geometry recovery",
            "plot-specific post-2014 Sentinel-1 stability",
            "numerical depth readiness",
        ],
        "coordinate_geometry_unblocked": False,
        "earth_engine_depth_query_allowed": False,
        "calibration_record_allowed": False,
        "numerical_depth_unlocked": False,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export coordinate-controlled historical NAIP GeoTIFFs for Tyrone 3X."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--ee-project",
        default=os.environ.get("EARTH_ENGINE_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT"),
    )
    parser.add_argument(
        "--years",
        default=",".join(str(value) for value in DEFAULT_YEARS),
        help="Comma-separated acquisition years.",
    )
    parser.add_argument("--scale-m", type=float, default=DEFAULT_SCALE_M)
    parser.add_argument(
        "--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        years = parse_years(args.years)
        if not math.isfinite(args.scale_m) or args.scale_m <= 0:
            raise ValueError("scale-m must be positive and finite")
        if args.timeout_seconds <= 0:
            raise ValueError("timeout-seconds must be positive")

        ee = initialize_ee(args.ee_project)
        start_year = min(years)
        end_year = max(years) + 1
        region, collection, source_count, timestamps, source_ids = query_collection(
            ee,
            bbox=TYRONE_3X_BBOX,
            start_date=f"{start_year:04d}-01-01",
            end_date=f"{end_year:04d}-01-01",
        )
        acquisition_dates, year_counts = summarize_dates(timestamps)
        args.output_dir.mkdir(parents=True, exist_ok=True)

        exports: list[dict[str, Any]] = []
        for year in years:
            source_for_year = int(year_counts.get(year, 0))
            if source_for_year <= 0:
                continue
            mosaic = build_year_mosaic(ee, collection, region, year)
            url = get_download_url(mosaic, region=region, scale_m=args.scale_m)
            output_path = args.output_dir / f"tyrone_3x_naip_{year}_{TARGET_CRS.replace(':', '_')}.tif"
            output_path.write_bytes(
                download_geotiff(url, timeout_seconds=args.timeout_seconds)
            )
            metadata = inspect_geotiff(
                output_path, requested_scale_m=args.scale_m
            )
            metadata.update(
                {
                    "year": year,
                    "source_image_count": source_for_year,
                }
            )
            exports.append(metadata)

        manifest = write_manifest(
            output_dir=args.output_dir,
            ee_project=args.ee_project,
            scale_m=args.scale_m,
            source_image_count=source_count,
            acquisition_dates=acquisition_dates,
            source_image_ids=source_ids,
            requested_years=years,
            exports=exports,
        )
    except (ValueError, OSError, HistoricalNaipError, GeotiffExportError) as exc:
        print(
            json.dumps(
                {
                    "status": "historical_naip_geotiff_export_failed",
                    "error": str(exc),
                    "coordinate_geometry_unblocked": False,
                    "numerical_depth_unlocked": False,
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            {
                "status": (
                    "historical_naip_geotiffs_created"
                    if exports
                    else "no_requested_historical_naip_geotiffs_created"
                ),
                "requested_years": list(years),
                "export_count": len(exports),
                "manifest": str(manifest.resolve()),
                "exports": exports,
                "coordinate_geometry_unblocked": False,
                "numerical_depth_unlocked": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
