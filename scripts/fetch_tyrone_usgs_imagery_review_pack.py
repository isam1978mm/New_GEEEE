#!/usr/bin/env python3
"""Create a USGS orthoimagery review pack for Tyrone Route B.

The pack is a discovery aid only. It downloads a grid of coordinate-controlled
USGS National Map imagery around the EPA Tyrone Mine site coordinate, writes
tile metadata, and builds a labeled contact sheet for comparison with the
official Tyrone maps.

It does not georeference Test Plots 5 or 6 and does not unlock numerical depth.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer

DEFAULT_CENTER_LON = -108.360000
DEFAULT_CENTER_LAT = 32.658333
DEFAULT_GRID_SIZE = 5
DEFAULT_TILE_SPAN_M = 3000.0
DEFAULT_TILE_PIXELS = 1536
DEFAULT_TIMEOUT_SECONDS = 120

SERVICE_URL = (
    "https://basemap.nationalmap.gov/arcgis/rest/services/"
    "USGSImageryOnly/MapServer/export"
)

OUTPUT_MANIFEST = "tyrone_usgs_imagery_review_manifest.json"
OUTPUT_CONTACT_SHEET = "tyrone_usgs_imagery_contact_sheet.jpg"


@dataclass(frozen=True)
class TileSpec:
    tile_id: str
    row: int
    column: int
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    center_easting_3857: float
    center_northing_3857: float

    @property
    def bbox(self) -> str:
        return f"{self.xmin:.3f},{self.ymin:.3f},{self.xmax:.3f},{self.ymax:.3f}"


class ImageryFetchError(RuntimeError):
    """Raised when an imagery tile cannot be downloaded or decoded."""


def validate_grid_size(value: int) -> int:
    if value < 1 or value % 2 == 0:
        raise ValueError("grid-size must be a positive odd integer")
    if value > 9:
        raise ValueError("grid-size must be 9 or smaller")
    return value


def center_to_web_mercator(longitude: float, latitude: float) -> tuple[float, float]:
    if not (-180 <= longitude <= 180):
        raise ValueError("center longitude is invalid")
    if not (-85.05112878 <= latitude <= 85.05112878):
        raise ValueError("center latitude is outside Web Mercator limits")
    transformer = Transformer.from_crs(4326, 3857, always_xy=True)
    x, y = transformer.transform(longitude, latitude)
    return float(x), float(y)


def build_tile_specs(
    *,
    center_x: float,
    center_y: float,
    grid_size: int,
    tile_span_m: float,
) -> list[TileSpec]:
    validate_grid_size(grid_size)
    if tile_span_m <= 0:
        raise ValueError("tile-span-m must be positive")
    half = grid_size // 2
    specs: list[TileSpec] = []
    for row in range(grid_size):
        for column in range(grid_size):
            x_offset = (column - half) * tile_span_m
            y_offset = (half - row) * tile_span_m
            tile_center_x = center_x + x_offset
            tile_center_y = center_y + y_offset
            half_span = tile_span_m / 2.0
            specs.append(
                TileSpec(
                    tile_id=f"R{row + 1}C{column + 1}",
                    row=row + 1,
                    column=column + 1,
                    xmin=tile_center_x - half_span,
                    ymin=tile_center_y - half_span,
                    xmax=tile_center_x + half_span,
                    ymax=tile_center_y + half_span,
                    center_easting_3857=tile_center_x,
                    center_northing_3857=tile_center_y,
                )
            )
    return specs


def build_export_url(
    *,
    service_url: str,
    spec: TileSpec,
    tile_pixels: int,
) -> str:
    if tile_pixels < 256 or tile_pixels > 4096:
        raise ValueError("tile-pixels must be between 256 and 4096")
    params = {
        "bbox": spec.bbox,
        "bboxSR": "3857",
        "imageSR": "3857",
        "size": f"{tile_pixels},{tile_pixels}",
        "format": "jpg",
        "transparent": "false",
        "dpi": "96",
        "f": "image",
    }
    return f"{service_url}?{urlencode(params)}"


def fetch_tile(*, url: str, timeout_seconds: int) -> Image.Image:
    request = Request(
        url,
        headers={
            "User-Agent": "New-GEE-Tyrone-Route-B/1.0",
            "Accept": "image/jpeg,image/*;q=0.8",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            content_type = (response.headers.get("Content-Type") or "").lower()
            raw = response.read()
    except Exception as exc:  # pragma: no cover - exercised locally
        raise ImageryFetchError(f"USGS imagery request failed: {exc}") from exc

    if "image" not in content_type:
        preview = raw[:200].decode("utf-8", errors="replace")
        raise ImageryFetchError(
            f"USGS imagery response was not an image: {content_type}; {preview}"
        )
    try:
        with Image.open(io.BytesIO(raw)) as image:
            return image.convert("RGB")
    except Exception as exc:
        raise ImageryFetchError("USGS imagery response could not be decoded") from exc


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def build_contact_sheet(
    *,
    tiles: list[tuple[TileSpec, Image.Image | None, str | None]],
    grid_size: int,
    output_path: Path,
    thumbnail_px: int = 340,
) -> None:
    margin = 18
    header_h = 82
    label_h = 42
    cell_w = thumbnail_px + margin
    cell_h = thumbnail_px + label_h + margin
    canvas = Image.new(
        "RGB",
        (margin + grid_size * cell_w, header_h + margin + grid_size * cell_h),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (margin, 12),
        "Tyrone Route B — USGS orthoimagery discovery grid",
        fill="black",
        font=_font(24),
    )
    draw.text(
        (margin, 46),
        "North is up. Tile IDs correspond to the manifest. Discovery only; not final geometry.",
        fill="black",
        font=_font(15),
    )

    for spec, image, error in tiles:
        x0 = margin + (spec.column - 1) * cell_w
        y0 = header_h + margin + (spec.row - 1) * cell_h
        if image is None:
            thumb = Image.new("RGB", (thumbnail_px, thumbnail_px), "#eeeeee")
            thumb_draw = ImageDraw.Draw(thumb)
            thumb_draw.text(
                (12, 12),
                f"DOWNLOAD FAILED\n{error or 'unknown error'}",
                fill="black",
                font=_font(14),
            )
        else:
            thumb = image.copy()
            thumb.thumbnail((thumbnail_px, thumbnail_px), Image.Resampling.LANCZOS)
            framed = Image.new("RGB", (thumbnail_px, thumbnail_px), "black")
            paste_x = (thumbnail_px - thumb.width) // 2
            paste_y = (thumbnail_px - thumb.height) // 2
            framed.paste(thumb, (paste_x, paste_y))
            thumb = framed
        canvas.paste(thumb, (x0, y0))
        draw.rectangle(
            (x0, y0, x0 + thumbnail_px - 1, y0 + thumbnail_px - 1),
            outline="black",
            width=1,
        )
        draw.text(
            (x0 + 6, y0 + thumbnail_px + 5),
            f"{spec.tile_id}  row {spec.row}, col {spec.column}",
            fill="black",
            font=_font(14),
        )
        draw.text(
            (x0 + 6, y0 + thumbnail_px + 22),
            f"center 3857: {spec.center_easting_3857:.0f}, {spec.center_northing_3857:.0f}",
            fill="black",
            font=_font(11),
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="JPEG", quality=90, optimize=True)


def write_manifest(
    *,
    output_path: Path,
    service_url: str,
    center_lon: float,
    center_lat: float,
    center_x: float,
    center_y: float,
    grid_size: int,
    tile_span_m: float,
    tile_pixels: int,
    tiles: list[dict[str, Any]],
    contact_sheet: Path,
) -> None:
    report = {
        "schema": "tyrone_usgs_imagery_review_manifest_v1",
        "status": "usgs_imagery_review_pack_created",
        "source": "USGS The National Map USGSImageryOnly MapServer",
        "service_url": service_url,
        "center_basis": "EPA Tyrone Mine site coordinate; broad discovery center only",
        "center_wgs84": {"longitude": center_lon, "latitude": center_lat},
        "center_web_mercator": {"easting_m": center_x, "northing_m": center_y},
        "grid_size": grid_size,
        "tile_span_m": tile_span_m,
        "tile_pixels": tile_pixels,
        "approx_pixel_size_m": tile_span_m / tile_pixels,
        "tile_count": len(tiles),
        "successful_tile_count": sum(1 for tile in tiles if tile["status"] == "downloaded"),
        "failed_tile_count": sum(1 for tile in tiles if tile["status"] != "downloaded"),
        "contact_sheet": str(contact_sheet.resolve()),
        "tiles": tiles,
        "next_gate": (
            "Identify the tile containing the reclaimed 3X impoundment, then download "
            "a tighter image and select at least six well-distributed permanent fit "
            "features plus two independent check features shared with the official maps."
        ),
        "does_not_prove": [
            "the exact location of Test Plot 5 or Test Plot 6",
            "a valid map-to-imagery transformation",
            "acceptable checkpoint accuracy",
            "a stable Sentinel-1 calibration interval",
            "numerical depth readiness",
        ],
        "coordinate_geometry_unblocked": False,
        "numerical_depth_unlocked": False,
    }
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a USGS orthoimagery discovery grid for Tyrone Route B."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--center-lon", type=float, default=DEFAULT_CENTER_LON)
    parser.add_argument("--center-lat", type=float, default=DEFAULT_CENTER_LAT)
    parser.add_argument("--grid-size", type=int, default=DEFAULT_GRID_SIZE)
    parser.add_argument("--tile-span-m", type=float, default=DEFAULT_TILE_SPAN_M)
    parser.add_argument("--tile-pixels", type=int, default=DEFAULT_TILE_PIXELS)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--service-url", default=SERVICE_URL)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validate_grid_size(args.grid_size)
        if args.tile_span_m <= 0:
            raise ValueError("tile-span-m must be positive")
        if not 256 <= args.tile_pixels <= 4096:
            raise ValueError("tile-pixels must be between 256 and 4096")
        if args.timeout_seconds <= 0:
            raise ValueError("timeout-seconds must be positive")

        center_x, center_y = center_to_web_mercator(args.center_lon, args.center_lat)
        specs = build_tile_specs(
            center_x=center_x,
            center_y=center_y,
            grid_size=args.grid_size,
            tile_span_m=args.tile_span_m,
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        tile_dir = args.output_dir / "tiles"
        tile_dir.mkdir(parents=True, exist_ok=True)

        contact_rows: list[tuple[TileSpec, Image.Image | None, str | None]] = []
        manifest_tiles: list[dict[str, Any]] = []

        for spec in specs:
            url = build_export_url(
                service_url=args.service_url,
                spec=spec,
                tile_pixels=args.tile_pixels,
            )
            tile_path = tile_dir / f"{spec.tile_id}.jpg"
            try:
                image = fetch_tile(url=url, timeout_seconds=args.timeout_seconds)
                image.save(tile_path, format="JPEG", quality=92)
                contact_rows.append((spec, image, None))
                manifest_tiles.append(
                    {
                        **asdict(spec),
                        "bbox_3857": spec.bbox,
                        "request_url": url,
                        "image": str(tile_path.resolve()),
                        "status": "downloaded",
                        "error": None,
                    }
                )
            except ImageryFetchError as exc:
                contact_rows.append((spec, None, str(exc)))
                manifest_tiles.append(
                    {
                        **asdict(spec),
                        "bbox_3857": spec.bbox,
                        "request_url": url,
                        "image": None,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        contact_sheet = args.output_dir / OUTPUT_CONTACT_SHEET
        manifest = args.output_dir / OUTPUT_MANIFEST
        build_contact_sheet(
            tiles=contact_rows,
            grid_size=args.grid_size,
            output_path=contact_sheet,
        )
        write_manifest(
            output_path=manifest,
            service_url=args.service_url,
            center_lon=args.center_lon,
            center_lat=args.center_lat,
            center_x=center_x,
            center_y=center_y,
            grid_size=args.grid_size,
            tile_span_m=args.tile_span_m,
            tile_pixels=args.tile_pixels,
            tiles=manifest_tiles,
            contact_sheet=contact_sheet,
        )
    except (OSError, ValueError, ImageryFetchError) as exc:
        print(
            json.dumps(
                {
                    "status": "usgs_imagery_review_pack_failed",
                    "error": str(exc),
                    "coordinate_geometry_unblocked": False,
                    "numerical_depth_unlocked": False,
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    successful = sum(1 for row in manifest_tiles if row["status"] == "downloaded")
    print(
        json.dumps(
            {
                "status": "usgs_imagery_review_pack_created",
                "tile_count": len(manifest_tiles),
                "successful_tile_count": successful,
                "failed_tile_count": len(manifest_tiles) - successful,
                "manifest": str(manifest.resolve()),
                "contact_sheet": str(contact_sheet.resolve()),
                "coordinate_geometry_unblocked": False,
                "numerical_depth_unlocked": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
