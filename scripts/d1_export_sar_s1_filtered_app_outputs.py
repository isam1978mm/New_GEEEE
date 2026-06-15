from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import ee
import numpy as np

from app.config import get_settings
from app.pipeline.stages.dem import DEM_TILE_SIZE, write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import grid_spec_from_manifest
from app.pipeline.stages.sar_rtc import S1_COLLECTION_ID, build_grid_region, build_sar_tile_requests, finalize_for_sample
from app.services.ee_session import initialize_ee_session
from app.services.grid import GridManifest

DEFAULT_S1_FILTERED_START = "2022-01-01"
DEFAULT_S1_FILTERED_END = "2026-03-01"

GEOTIFF_RADAR_BANDS_DIR = "GEOTIFF_RADAR_BANDS"
NPY_RADAR_BANDS_DIR = "NPY_RADAR_BANDS"
NPY_STACKS_DIR = "NPY_STACKS"
STACK_NAME = "S1_FILTERED_LAYERS_STACK_640.npy"

S1_FILTERED_BAND_SPECS: tuple[tuple[str, str, str], ...] = (
    ("ASCENDING", "VV", "S1_ASC_VV_Filtered"),
    ("ASCENDING", "VH", "S1_ASC_VH_Filtered"),
    ("DESCENDING", "VV", "S1_DESC_VV_Filtered"),
    ("DESCENDING", "VH", "S1_DESC_VH_Filtered"),
)


class D1SarS1FilteredExportError(ValueError):
    pass


def build_s1_filtered_base_collection(grid_spec, *, start_date: str, end_date: str):
    region = build_grid_region(grid_spec)
    return (
        ee.ImageCollection(S1_COLLECTION_ID)
        .filterBounds(region)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
    )


def newest_image_for_pass(collection, *, orbit_pass: str, start_date: str, end_date: str):
    pass_collection = collection.filter(ee.Filter.eq("orbitProperties_pass", orbit_pass)).sort("system:time_start", False)
    count = int(pass_collection.size().getInfo())
    if count < 1:
        raise D1SarS1FilteredExportError(
            f"No Sentinel-1 {orbit_pass} image found for notebook S1 filtered export window {start_date} to {end_date}."
        )
    image = ee.Image(pass_collection.first())
    return image, count


def speckle_filter(image):
    return ee.Image(image).focal_mean(radius=1.5, kernelType="circle", units="pixels")


def build_filtered_stack_image(grid_spec, *, start_date: str, end_date: str) -> tuple[Any, dict[str, Any]]:
    base = build_s1_filtered_base_collection(grid_spec, start_date=start_date, end_date=end_date)
    asc_image, asc_count = newest_image_for_pass(base, orbit_pass="ASCENDING", start_date=start_date, end_date=end_date)
    desc_image, desc_count = newest_image_for_pass(base, orbit_pass="DESCENDING", start_date=start_date, end_date=end_date)

    filtered_by_pass = {
        "ASCENDING": speckle_filter(asc_image.select(["VV", "VH"])),
        "DESCENDING": speckle_filter(desc_image.select(["VV", "VH"])),
    }
    bands = [
        filtered_by_pass[orbit_pass].select(source_band).rename(output_band)
        for orbit_pass, source_band, output_band in S1_FILTERED_BAND_SPECS
    ]
    stack_image = ee.Image.cat(bands)
    stack_image = finalize_for_sample(stack_image, grid_spec)
    provenance = {
        "start_date": start_date,
        "end_date": end_date,
        "collection": S1_COLLECTION_ID,
        "asc_count": asc_count,
        "desc_count": desc_count,
        "asc_image_id": asc_image.id().getInfo(),
        "desc_image_id": desc_image.id().getInfo(),
        "asc_time_start": asc_image.get("system:time_start").getInfo(),
        "desc_time_start": desc_image.get("system:time_start").getInfo(),
        "band_order": [spec[2] for spec in S1_FILTERED_BAND_SPECS],
        "filter": "focal_mean(radius=1.5, kernelType='circle', units='pixels')",
        "shape_convention": "HWC",
        "dtype": "float32",
    }
    return stack_image, provenance


def sample_filtered_stack(stack_image, grid_spec) -> np.ndarray:
    band_names = tuple(spec[2] for spec in S1_FILTERED_BAND_SPECS)
    cube = np.full((grid_spec.size, grid_spec.size, len(band_names)), grid_spec.nodata, dtype=np.float32)
    for request in build_sar_tile_requests(grid_spec):
        tile_geo = ee.Geometry.Rectangle(
            [request["xmin"], request["ymin"], request["xmax"], request["ymax"]],
            grid_spec.crs,
            False,
        )
        rect = ee.Image(stack_image).sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
        for band_index, band_name in enumerate(band_names):
            data = np.array(rect["properties"][band_name], dtype=np.float32)[:DEM_TILE_SIZE, :DEM_TILE_SIZE]
            row_start = int(request["tile_row"]) * DEM_TILE_SIZE
            col_start = int(request["tile_col"]) * DEM_TILE_SIZE
            cube[row_start : row_start + DEM_TILE_SIZE, col_start : col_start + DEM_TILE_SIZE, band_index] = data
    return cube


def write_filtered_outputs(app_run_dir: Path, grid_spec, cube: np.ndarray, provenance: dict[str, Any]) -> dict[str, Any]:
    geotiff_dir = app_run_dir / GEOTIFF_RADAR_BANDS_DIR
    npy_dir = app_run_dir / NPY_RADAR_BANDS_DIR
    stack_dir = app_run_dir / NPY_STACKS_DIR
    geotiff_dir.mkdir(parents=True, exist_ok=True)
    npy_dir.mkdir(parents=True, exist_ok=True)
    stack_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[dict[str, Any]] = []
    for band_index, (_, _, stem) in enumerate(S1_FILTERED_BAND_SPECS):
        array = cube[:, :, band_index].astype(np.float32, copy=False)
        tif_path = geotiff_dir / f"{stem}_640.tif"
        npy_path = npy_dir / f"{stem}_640.npy"
        write_georeferenced_raster(tif_path, array, grid_spec)
        write_raster_sidecar(
            tif_path,
            grid_manifest=grid_spec.manifest,
            nodata=grid_spec.nodata,
            dtype="float32",
            shape=array.shape,
        )
        np.save(npy_path, array)
        outputs.append({"output_name": tif_path.name, "relative_path": tif_path.relative_to(app_run_dir).as_posix()})
        outputs.append({"output_name": npy_path.name, "relative_path": npy_path.relative_to(app_run_dir).as_posix()})

    stack_path = stack_dir / STACK_NAME
    np.save(stack_path, cube.astype(np.float32, copy=False))
    outputs.append({"output_name": stack_path.name, "relative_path": stack_path.relative_to(app_run_dir).as_posix()})

    manifest_path = app_run_dir / "manifests" / "d1_sar_s1_filtered_export_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "d1_sar_s1_filtered_export_manifest_v1",
        "created_at": datetime.now(UTC).isoformat(),
        "output_count": len(outputs),
        "outputs": outputs,
        "provenance": provenance,
        "value_parity_proven": False,
        "notes": "Notebook-compatible S1 filtered support outputs only. This does not modify final SAR RTC outputs and does not prove value parity.",
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def export_s1_filtered_outputs(*, app_run_dir: str | Path, start_date: str, end_date: str) -> dict[str, Any]:
    run_dir = Path(app_run_dir)
    if not run_dir.is_dir():
        raise D1SarS1FilteredExportError("app run directory is missing")
    grid_manifest_path = run_dir / "grid_manifest.json"
    if not grid_manifest_path.is_file():
        raise D1SarS1FilteredExportError("grid_manifest.json is missing from app run directory")
    grid_manifest = GridManifest.model_validate_json(grid_manifest_path.read_text(encoding="utf-8"))
    grid_spec = grid_spec_from_manifest(grid_manifest)
    initialize_ee_session(get_settings())
    stack_image, provenance = build_filtered_stack_image(grid_spec, start_date=start_date, end_date=end_date)
    cube = sample_filtered_stack(stack_image, grid_spec)
    return write_filtered_outputs(run_dir, grid_spec, cube, provenance)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export notebook-compatible D1 SAR/S1 filtered support outputs into an app run directory.")
    parser.add_argument("--app-run-dir", required=True)
    parser.add_argument("--start-date", default=DEFAULT_S1_FILTERED_START)
    parser.add_argument("--end-date", default=DEFAULT_S1_FILTERED_END)
    args = parser.parse_args(argv)
    try:
        result = export_s1_filtered_outputs(app_run_dir=args.app_run_dir, start_date=args.start_date, end_date=args.end_date)
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1
    print("status: exported")
    print(f"output_count: {result['output_count']}")
    print("value_parity_proven: False")
    print("note: exported app-side S1 filtered outputs only; run recovery inventory and value parity next")
    return 0


if __name__ == "__main__":
    sys.exit(main())
