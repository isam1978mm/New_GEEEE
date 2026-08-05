#!/usr/bin/env python3
"""Probe historical NAIP imagery over the Tyrone 3X direct-georeferencing AOI.

The script queries Earth Engine's USDA/NAIP/DOQQ collection, groups intersecting
images by acquisition year, downloads one RGB mosaic thumbnail per available
year, and writes a manifest plus a contact sheet.

This is a discovery/review tool only. It does not georeference Test Plots 5/6
and never unlocks coordinate geometry or numerical depth.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

COLLECTION_ID = "USDA/NAIP/DOQQ"
DEFAULT_BBOX = (-108.427374, 32.669677, -108.386950, 32.692360)
DEFAULT_START_DATE = "2003-01-01"
DEFAULT_END_DATE = "2013-01-01"
DEFAULT_DIMENSIONS = 1800
DEFAULT_TIMEOUT_SECONDS = 120
MANIFEST_NAME = "tyrone_historical_naip_manifest.json"
CONTACT_SHEET_NAME = "tyrone_historical_naip_contact_sheet.jpg"


class HistoricalNaipError(RuntimeError):
    """Raised when the historical NAIP probe cannot complete."""


def parse_bbox(raw: str) -> tuple[float, float, float, float]:
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must be west,south,east,north")
    try:
        west, south, east, north = (float(part) for part in parts)
    except ValueError as exc:
        raise ValueError("bbox values must be numeric") from exc
    if not (-180 <= west < east <= 180):
        raise ValueError("bbox west/east values are invalid")
    if not (-90 <= south < north <= 90):
        raise ValueError("bbox south/north values are invalid")
    return west, south, east, north


def validate_date(raw: str) -> str:
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("dates must use YYYY-MM-DD") from exc
    return raw


def timestamp_ms_to_date(value: Any) -> str | None:
    try:
        timestamp_ms = int(value)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc).date().isoformat()


def summarize_dates(timestamps_ms: list[Any]) -> tuple[list[str], dict[int, int]]:
    dates = sorted(
        date for date in (timestamp_ms_to_date(value) for value in timestamps_ms) if date
    )
    year_counts = Counter(int(date[:4]) for date in dates)
    return dates, dict(sorted(year_counts.items()))


def initialize_ee(project: str | None):
    try:
        import ee
    except ImportError as exc:
        raise HistoricalNaipError(
            "earthengine-api is not installed in this Python environment"
        ) from exc

    try:
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()
    except Exception as exc:
        raise HistoricalNaipError(
            "Earth Engine initialization failed. Use the same authenticated "
            "environment/project that runs the app."
        ) from exc
    return ee


def query_collection(
    ee,
    *,
    bbox: tuple[float, float, float, float],
    start_date: str,
    end_date: str,
):
    west, south, east, north = bbox
    region = ee.Geometry.Rectangle([west, south, east, north], geodesic=False)
    collection = (
        ee.ImageCollection(COLLECTION_ID)
        .filterBounds(region)
        .filterDate(start_date, end_date)
        .sort("system:time_start")
    )
    try:
        image_count = int(collection.size().getInfo())
        timestamps = collection.aggregate_array("system:time_start").getInfo()
        image_ids = collection.aggregate_array("system:index").getInfo()
    except Exception as exc:
        raise HistoricalNaipError(f"Earth Engine NAIP query failed: {exc}") from exc

    if not isinstance(timestamps, list):
        timestamps = []
    if not isinstance(image_ids, list):
        image_ids = []
    return region, collection, image_count, timestamps, image_ids


def build_year_mosaic(ee, collection, region, year: int):
    start = f"{year:04d}-01-01"
    end = f"{year + 1:04d}-01-01"
    yearly = collection.filterDate(start, end)
    # Mosaic first, then select RGB so mixed RGB/RGBN assets remain compatible.
    return yearly.mosaic().select(["R", "G", "B"]).clip(region)


def get_thumbnail_url(image, region, dimensions: int) -> str:
    try:
        return image.getThumbURL(
            {
                "region": region,
                "dimensions": dimensions,
                "format": "jpg",
                "min": 0,
                "max": 255,
            }
        )
    except Exception as exc:
        raise HistoricalNaipError(f"failed to create NAIP thumbnail URL: {exc}") from exc


def download_bytes(url: str, timeout_seconds: int) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "New-GEE-Tyrone-Historical-NAIP/1.0",
            "Accept": "image/jpeg,image/*;q=0.9,*/*;q=0.1",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            payload = response.read()
    except Exception as exc:
        raise HistoricalNaipError(f"thumbnail download failed: {exc}") from exc
    if len(payload) < 1024:
        raise HistoricalNaipError("thumbnail response was unexpectedly small")
    return payload


def create_contact_sheet(
    rows: list[dict[str, Any]], output_path: Path, *, cell_width: int = 700
) -> None:
    if not rows:
        return
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise HistoricalNaipError("Pillow is required to build the contact sheet") from exc

    opened: list[tuple[dict[str, Any], Any]] = []
    for row in rows:
        path = Path(row["image"])
        if not path.exists():
            continue
        with Image.open(path) as image:
            opened.append((row, image.convert("RGB").copy()))
    if not opened:
        return

    columns = min(3, len(opened))
    rows_count = math.ceil(len(opened) / columns)
    label_height = 42
    resized: list[tuple[dict[str, Any], Any]] = []
    cell_height = 0
    for row, image in opened:
        scale = cell_width / image.width
        height = max(1, round(image.height * scale))
        thumb = image.resize((cell_width, height))
        cell_height = max(cell_height, height + label_height)
        resized.append((row, thumb))

    sheet = Image.new(
        "RGB",
        (columns * cell_width, rows_count * cell_height),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for index, (row, image) in enumerate(resized):
        column = index % columns
        row_index = index // columns
        x = column * cell_width
        y = row_index * cell_height
        sheet.paste(image, (x, y + label_height))
        label = (
            f"{row['year']} — {row['image_count']} source image"
            f"{'s' if row['image_count'] != 1 else ''}"
        )
        draw.text((x + 12, y + 12), label, fill="black")
    sheet.save(output_path, quality=92)


def write_manifest(
    *,
    output_dir: Path,
    bbox: tuple[float, float, float, float],
    start_date: str,
    end_date: str,
    ee_project: str | None,
    image_count: int,
    acquisition_dates: list[str],
    image_ids: list[Any],
    year_counts: dict[int, int],
    year_rows: list[dict[str, Any]],
) -> Path:
    manifest_path = output_dir / MANIFEST_NAME
    payload = {
        "schema": "tyrone_historical_naip_manifest_v1",
        "status": (
            "historical_naip_review_pack_created"
            if year_rows
            else "no_historical_naip_available_in_requested_period"
        ),
        "collection_id": COLLECTION_ID,
        "earth_engine_project": ee_project,
        "bbox_wgs84": {
            "west": bbox[0],
            "south": bbox[1],
            "east": bbox[2],
            "north": bbox[3],
        },
        "date_range": {"start": start_date, "end_exclusive": end_date},
        "source_image_count": image_count,
        "acquisition_dates": acquisition_dates,
        "source_image_ids": [str(value) for value in image_ids],
        "year_counts": {str(year): count for year, count in year_counts.items()},
        "year_mosaics": year_rows,
        "contact_sheet": str((output_dir / CONTACT_SHEET_NAME).resolve())
        if year_rows
        else None,
        "review_goal": (
            "Find the earliest coordinate-controlled imagery where the 2006 "
            "TP5/TP6 plot roads, berms, or internal boundaries are visually distinct."
        ),
        "does_not_prove": [
            "coordinate-tied TP5 or TP6 geometry",
            "acceptable map-to-imagery fit accuracy",
            "a stable post-2014 Sentinel-1 calibration interval",
            "numerical depth readiness",
        ],
        "coordinate_geometry_unblocked": False,
        "numerical_depth_unlocked": False,
    }
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a historical NAIP review pack for Tyrone Route B."
    )
    parser.add_argument(
        "--bbox",
        default=",".join(str(value) for value in DEFAULT_BBOX),
        help="WGS84 west,south,east,north AOI.",
    )
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--ee-project",
        default=os.environ.get("EARTH_ENGINE_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT"),
    )
    parser.add_argument("--dimensions", type=int, default=DEFAULT_DIMENSIONS)
    parser.add_argument(
        "--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bbox = parse_bbox(args.bbox)
        start_date = validate_date(args.start_date)
        end_date = validate_date(args.end_date)
        if start_date >= end_date:
            raise ValueError("start-date must be before end-date")
        if args.dimensions < 256 or args.dimensions > 4096:
            raise ValueError("dimensions must be between 256 and 4096")
        if args.timeout_seconds <= 0:
            raise ValueError("timeout-seconds must be positive")

        ee = initialize_ee(args.ee_project)
        region, collection, image_count, timestamps, image_ids = query_collection(
            ee,
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
        )
        acquisition_dates, year_counts = summarize_dates(timestamps)
        args.output_dir.mkdir(parents=True, exist_ok=True)

        year_rows: list[dict[str, Any]] = []
        for year, count in year_counts.items():
            mosaic = build_year_mosaic(ee, collection, region, year)
            url = get_thumbnail_url(mosaic, region, args.dimensions)
            image_path = args.output_dir / f"tyrone_naip_{year}.jpg"
            image_path.write_bytes(download_bytes(url, args.timeout_seconds))
            year_rows.append(
                {
                    "year": year,
                    "image_count": count,
                    "image": str(image_path.resolve()),
                }
            )

        contact_sheet = args.output_dir / CONTACT_SHEET_NAME
        create_contact_sheet(year_rows, contact_sheet)
        manifest = write_manifest(
            output_dir=args.output_dir,
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            ee_project=args.ee_project,
            image_count=image_count,
            acquisition_dates=acquisition_dates,
            image_ids=image_ids,
            year_counts=year_counts,
            year_rows=year_rows,
        )
    except (ValueError, OSError, HistoricalNaipError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "status": "historical_naip_probe_failed",
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
                    "historical_naip_review_pack_created"
                    if year_rows
                    else "no_historical_naip_available_in_requested_period"
                ),
                "source_image_count": image_count,
                "available_years": sorted(year_counts),
                "year_mosaic_count": len(year_rows),
                "manifest": str(manifest.resolve()),
                "contact_sheet": str(contact_sheet.resolve()) if year_rows else None,
                "coordinate_geometry_unblocked": False,
                "numerical_depth_unlocked": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
