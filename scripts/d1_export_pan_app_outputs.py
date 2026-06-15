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
from app.pipeline.stages.s2_indices import build_grid_region, build_s2_tile_requests, finalize_for_sample
from app.services.ee_session import initialize_ee_session
from app.services.grid import GridManifest

LANDSAT_COLLECTION_ID = "LANDSAT/LC09/C02/T1_TOA"
S2_COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"

DEFAULT_PAN_START = "2022-01-01"
DEFAULT_PAN_END = "2026-03-01"
DEFAULT_LANDSAT_CLOUD_MAX = 20.0
DEFAULT_S2_CLOUD_MAX = 3.0

PAN_TIFS_DIR = "OPT/PAN_TIFS_640"
PAN_NPY_DIR = "OPT/PAN_NPY_640"
NPY_STACKS_DIR = "NPY_STACKS"
PAN_STACK_NAME = "PAN_LAYERS_STACK_640.npy"

PAN_BANDS: tuple[tuple[str, str], ...] = (
    ("LS_Panchromatic", "PAN_LS_Panchromatic_640"),
    ("S2_Panchromatic_10m", "PAN_S2_Panchromatic_10m_640"),
)


class D1PanExportError(ValueError):
    pass


def _collection_count(collection: Any) -> int:
    return int(collection.size().getInfo())


def _selected_image_metadata(image: Any) -> dict[str, Any]:
    return {
        "image_id": image.id().getInfo(),
        "system_time_start": image.get("system:time_start").getInfo(),
    }


def _select_first_image(collection: Any, *, label: str) -> tuple[Any, int]:
    count = _collection_count(collection)
    if count < 1:
        raise D1PanExportError(f"No {label} image found for the requested PAN export filters.")
    return ee.Image(collection.first()), count


def _landsat_image(
    grid_spec,
    *,
    start_date: str,
    end_date: str,
    cloud_max: float,
    image_id: str | None,
) -> tuple[Any, dict[str, Any]]:
    if image_id:
        image = ee.Image(image_id)
        return image, {
            "collection": LANDSAT_COLLECTION_ID,
            "selection_mode": "explicit_image_id",
            "requested_image_id": image_id,
            **_selected_image_metadata(image),
        }

    collection = (
        ee.ImageCollection(LANDSAT_COLLECTION_ID)
        .filterBounds(build_grid_region(grid_spec))
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUD_COVER", cloud_max))
        .sort("CLOUD_COVER")
    )
    image, count = _select_first_image(collection, label="Landsat 9")
    return image, {
        "collection": LANDSAT_COLLECTION_ID,
        "selection_mode": "lowest_cloud_cover_first",
        "start_date": start_date,
        "end_date": end_date,
        "cloud_property": "CLOUD_COVER",
        "cloud_max": cloud_max,
        "candidate_count": count,
        "cloud_value": image.get("CLOUD_COVER").getInfo(),
        **_selected_image_metadata(image),
    }


def _sentinel2_image(
    grid_spec,
    *,
    start_date: str,
    end_date: str,
    cloud_max: float,
    image_id: str | None,
) -> tuple[Any, dict[str, Any]]:
    if image_id:
        image = ee.Image(image_id)
        return image, {
            "collection": S2_COLLECTION_ID,
            "selection_mode": "explicit_image_id",
            "requested_image_id": image_id,
            **_selected_image_metadata(image),
        }

    collection = (
        ee.ImageCollection(S2_COLLECTION_ID)
        .filterBounds(build_grid_region(grid_spec))
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_max))
        .sort("CLOUDY_PIXEL_PERCENTAGE")
    )
    image, count = _select_first_image(collection, label="Sentinel-2")
    return image, {
        "collection": S2_COLLECTION_ID,
        "selection_mode": "lowest_cloudy_pixel_percentage_first",
        "start_date": start_date,
        "end_date": end_date,
        "cloud_property": "CLOUDY_PIXEL_PERCENTAGE",
        "cloud_max": cloud_max,
        "candidate_count": count,
        "cloud_value": image.get("CLOUDY_PIXEL_PERCENTAGE").getInfo(),
        **_selected_image_metadata(image),
    }


def build_pan_stack_image(
    grid_spec,
    *,
    start_date: str,
    end_date: str,
    landsat_cloud_max: float,
    s2_cloud_max: float,
    landsat_image_id: str | None,
    s2_image_id: str | None,
) -> tuple[Any, dict[str, Any]]:
    landsat, landsat_provenance = _landsat_image(
        grid_spec,
        start_date=start_date,
        end_date=end_date,
        cloud_max=landsat_cloud_max,
        image_id=landsat_image_id,
    )
    sentinel2, s2_provenance = _sentinel2_image(
        grid_spec,
        start_date=start_date,
        end_date=end_date,
        cloud_max=s2_cloud_max,
        image_id=s2_image_id,
    )

    landsat_pan_layer = ee.Image(landsat).select("B8").resample("bilinear").rename("LS_Panchromatic")
    sentinel_high_res = ee.Image(sentinel2).select(["B2", "B3", "B4", "B8"]).reduce(ee.Reducer.mean()).rename(
        "S2_Panchromatic_10m"
    )
    pan_stack = ee.Image.cat([landsat_pan_layer, sentinel_high_res])
    pan_stack = finalize_for_sample(pan_stack, grid_spec)
    provenance = {
        "source_contract": "D1 notebook optical-only PAN cell",
        "start_date": start_date,
        "end_date": end_date,
        "band_order": [band_name for band_name, _ in PAN_BANDS],
        "shape_convention": "HWC",
        "dtype": "float32",
        "nodata_policy": "sampleRectangle(defaultValue=grid_nodata); non-finite values replaced by grid_nodata before tile assignment",
        "landsat": landsat_provenance,
        "sentinel2": s2_provenance,
        "value_parity_proven": False,
    }
    return pan_stack, provenance


def _finite_or_nodata(array: np.ndarray, *, nodata: float) -> np.ndarray:
    result = np.asarray(array, dtype=np.float32)
    return np.where(np.isfinite(result), result, np.float32(nodata)).astype(np.float32, copy=False)


def sample_pan_stack(stack_image: Any, grid_spec) -> np.ndarray:
    band_names = tuple(band_name for band_name, _ in PAN_BANDS)
    cube = np.full((grid_spec.size, grid_spec.size, len(band_names)), grid_spec.nodata, dtype=np.float32)
    for request in build_s2_tile_requests(grid_spec):
        tile_geo = ee.Geometry.Rectangle(
            [request["xmin"], request["ymin"], request["xmax"], request["ymax"]],
            grid_spec.crs,
            False,
        )
        rect = ee.Image(stack_image).sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
        for band_index, band_name in enumerate(band_names):
            data = np.array(rect["properties"][band_name], dtype=np.float32)[:DEM_TILE_SIZE, :DEM_TILE_SIZE]
            data = _finite_or_nodata(data, nodata=grid_spec.nodata)
            row_start = int(request["tile_row"]) * DEM_TILE_SIZE
            col_start = int(request["tile_col"]) * DEM_TILE_SIZE
            cube[row_start : row_start + DEM_TILE_SIZE, col_start : col_start + DEM_TILE_SIZE, band_index] = data
    return cube


def write_pan_outputs(app_run_dir: Path, grid_spec, cube: np.ndarray, provenance: dict[str, Any]) -> dict[str, Any]:
    tif_dir = app_run_dir / PAN_TIFS_DIR
    npy_dir = app_run_dir / PAN_NPY_DIR
    stack_dir = app_run_dir / NPY_STACKS_DIR
    tif_dir.mkdir(parents=True, exist_ok=True)
    npy_dir.mkdir(parents=True, exist_ok=True)
    stack_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[dict[str, Any]] = []
    for band_index, (_, output_stem) in enumerate(PAN_BANDS):
        array = cube[:, :, band_index].astype(np.float32, copy=False)
        tif_path = tif_dir / f"{output_stem}.tif"
        npy_path = npy_dir / f"{output_stem}.npy"
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

    stack_path = stack_dir / PAN_STACK_NAME
    np.save(stack_path, cube.astype(np.float32, copy=False))
    outputs.append({"output_name": stack_path.name, "relative_path": stack_path.relative_to(app_run_dir).as_posix()})

    manifest_path = app_run_dir / "manifests" / "d1_pan_export_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "d1_pan_export_manifest_v1",
        "created_at": datetime.now(UTC).isoformat(),
        "output_count": len(outputs),
        "outputs": outputs,
        "provenance": provenance,
        "value_parity_proven": False,
        "notes": "Notebook-compatible D1 PAN outputs only. This does not alter live optical stages and does not prove value parity.",
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def export_pan_outputs(
    *,
    app_run_dir: str | Path,
    start_date: str,
    end_date: str,
    landsat_cloud_max: float,
    s2_cloud_max: float,
    landsat_image_id: str | None,
    s2_image_id: str | None,
) -> dict[str, Any]:
    run_dir = Path(app_run_dir)
    if not run_dir.is_dir():
        raise D1PanExportError("app run directory is missing")
    grid_manifest_path = run_dir / "grid_manifest.json"
    if not grid_manifest_path.is_file():
        raise D1PanExportError("grid_manifest.json is missing from app run directory")
    grid_manifest = GridManifest.model_validate_json(grid_manifest_path.read_text(encoding="utf-8"))
    grid_spec = grid_spec_from_manifest(grid_manifest)
    initialize_ee_session(get_settings())
    stack_image, provenance = build_pan_stack_image(
        grid_spec,
        start_date=start_date,
        end_date=end_date,
        landsat_cloud_max=landsat_cloud_max,
        s2_cloud_max=s2_cloud_max,
        landsat_image_id=landsat_image_id,
        s2_image_id=s2_image_id,
    )
    cube = sample_pan_stack(stack_image, grid_spec)
    return write_pan_outputs(run_dir, grid_spec, cube, provenance)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export notebook-compatible D1 PAN outputs into an app run directory.")
    parser.add_argument("--app-run-dir", required=True)
    parser.add_argument("--start-date", default=DEFAULT_PAN_START)
    parser.add_argument("--end-date", default=DEFAULT_PAN_END)
    parser.add_argument("--landsat-cloud-max", type=float, default=DEFAULT_LANDSAT_CLOUD_MAX)
    parser.add_argument("--s2-cloud-max", type=float, default=DEFAULT_S2_CLOUD_MAX)
    parser.add_argument("--landsat-image-id", default=None)
    parser.add_argument("--s2-image-id", default=None)
    args = parser.parse_args(argv)
    try:
        result = export_pan_outputs(
            app_run_dir=args.app_run_dir,
            start_date=args.start_date,
            end_date=args.end_date,
            landsat_cloud_max=args.landsat_cloud_max,
            s2_cloud_max=args.s2_cloud_max,
            landsat_image_id=args.landsat_image_id,
            s2_image_id=args.s2_image_id,
        )
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1
    print("status: exported")
    print(f"output_count: {result['output_count']}")
    print("value_parity_proven: False")
    print("note: exported app-side D1 PAN outputs only; run PAN component and stack parity next")
    return 0


if __name__ == "__main__":
    sys.exit(main())
