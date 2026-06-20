from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from app.config import get_settings
from app.pipeline.stages.grid import grid_spec_from_manifest
from app.pipeline.stages.s2_indices import (
    DEFAULT_END,
    DEFAULT_S2_CLOUD_MAX,
    DEFAULT_START,
    build_grid_region,
    build_s2_tile_requests,
)
from app.services.ee_session import initialize_ee_session
from app.services.grid import GridManifest

import int1_recover_s2_b8a as local_recovery

BAND_NAME = "B8A"
COLLECTION_ID = "COPERNICUS/S2_SR_HARMONIZED"


class LiveB8AFetchError(ValueError):
    pass


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        result = fetch_live_b8a(
            app_run_dir=Path(args.app_run_dir),
            output_dir=Path(args.output_dir) if args.output_dir else None,
            write=args.write,
            overwrite=args.overwrite,
            start_date=args.start_date,
            end_date=args.end_date,
            cloud_max=args.cloud_max,
        )
    except LiveB8AFetchError as exc:
        print(json.dumps({"ok": False, "status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


def fetch_live_b8a(
    *,
    app_run_dir: Path,
    output_dir: Path | None = None,
    write: bool = False,
    overwrite: bool = False,
    start_date: str = DEFAULT_START,
    end_date: str = DEFAULT_END,
    cloud_max: int = DEFAULT_S2_CLOUD_MAX,
) -> dict[str, Any]:
    run_root = Path(app_run_dir)
    output_root = Path(output_dir) if output_dir else run_root
    grid_path = run_root / "grid_manifest.json"
    s2_manifest_path = run_root / "stage_s2_indices.manifest.json"
    if not grid_path.is_file():
        raise LiveB8AFetchError("grid_manifest.json is missing")
    if not s2_manifest_path.is_file():
        raise LiveB8AFetchError("stage_s2_indices.manifest.json is missing")

    grid_manifest = GridManifest.model_validate_json(grid_path.read_text(encoding="utf-8"))
    s2_manifest = json.loads(s2_manifest_path.read_text(encoding="utf-8"))
    source_bands = list(s2_manifest.get("metadata", {}).get("source_bands", []))
    existing_outputs = [
        path.name
        for path in (
            output_root / local_recovery.B8A_NPY_NAME,
            output_root / local_recovery.B8A_TIF_NAME,
            output_root / local_recovery.B8A_MANIFEST_NAME,
        )
        if path.exists()
    ]

    result: dict[str, Any] = {
        "ok": True,
        "status": "dry_run_ready",
        "mode": "write" if write else "dry_run",
        "created_at": datetime.now(UTC).isoformat(),
        "app_run_dir": str(run_root),
        "output_dir": str(output_root),
        "source_collection": COLLECTION_ID,
        "band_name": BAND_NAME,
        "start_date": start_date,
        "end_date": end_date,
        "cloud_max": cloud_max,
        "grid_epsg": grid_manifest.epsg,
        "grid_size_px": grid_manifest.size_px,
        "grid_scale_m": grid_manifest.scale_m,
        "source_bands_before_recovery": source_bands,
        "b8a_already_in_s2_manifest": BAND_NAME in source_bands,
        "existing_outputs": existing_outputs,
        "earth_engine_called": False,
        "reference_outputs_read": False,
        "api_frontend_changed": False,
        "raster_payloads_committed": False,
        "output_npy_written": False,
        "output_tif_written": False,
        "manifest_written": False,
    }
    if not write:
        return result
    if existing_outputs and not overwrite:
        raise LiveB8AFetchError("B8A recovery outputs already exist; use --overwrite")

    array = _fetch_b8a_array(grid_manifest, start_date=start_date, end_date=end_date, cloud_max=cloud_max)
    output_root.mkdir(parents=True, exist_ok=True)
    temp_array_path = output_root / (local_recovery.B8A_NPY_NAME + ".live.tmp.npy")
    with temp_array_path.open("wb") as handle:
        np.save(handle, array.astype(np.float32, copy=False))
    try:
        registered = local_recovery.recover_b8a_from_local_array(
            app_run_dir=run_root,
            b8a_array=temp_array_path,
            output_dir=output_root,
            write=True,
            overwrite=True,
        )
    finally:
        if temp_array_path.exists():
            os.remove(temp_array_path)

    result.update(
        {
            "status": "live_s2_b8a_recovery_written",
            "earth_engine_called": True,
            "output_npy_written": True,
            "output_tif_written": True,
            "manifest_written": True,
            "output_npy_size_bytes": registered.get("output_npy_size_bytes"),
            "output_tif_size_bytes": registered.get("output_tif_size_bytes"),
            "finite_count": int(np.isfinite(array).sum()),
            "nan_count": int(np.isnan(array).sum()),
            "min": float(np.nanmin(array)),
            "max": float(np.nanmax(array)),
        }
    )
    return result


def _fetch_b8a_array(
    grid_manifest: GridManifest,
    *,
    start_date: str,
    end_date: str,
    cloud_max: int,
) -> np.ndarray:
    import ee

    settings = get_settings()
    initialize_ee_session(settings)
    grid_spec = grid_spec_from_manifest(grid_manifest)
    image = (
        ee.ImageCollection(COLLECTION_ID)
        .filterBounds(build_grid_region(grid_spec))
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_max))
        .select([BAND_NAME])
        .median()
    )
    final = (
        ee.Image(image)
        .toFloat()
        .unmask(grid_spec.nodata)
        .reproject(crs=grid_spec.crs, crsTransform=list(grid_spec.transform))
        .clip(build_grid_region(grid_spec))
    )
    tile_size = int(grid_spec.size // 2)
    output = np.full((grid_spec.size, grid_spec.size), grid_spec.nodata, dtype=np.float32)
    for request in build_s2_tile_requests(grid_spec):
        tile_geo = ee.Geometry.Rectangle(
            [request["xmin"], request["ymin"], request["xmax"], request["ymax"]],
            grid_spec.crs,
            False,
        )
        rect = final.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
        data = np.array(rect["properties"][BAND_NAME], dtype=np.float32)[:tile_size, :tile_size]
        row_start = int(request["tile_row"] * tile_size)
        col_start = int(request["tile_col"] * tile_size)
        output[row_start : row_start + data.shape[0], col_start : col_start + data.shape[1]] = data
    return output


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Live-fetch Sentinel-2 B8A for INT-1 onto an app run grid.")
    parser.add_argument("--app-run-dir", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--start-date", default=DEFAULT_START)
    parser.add_argument("--end-date", default=DEFAULT_END)
    parser.add_argument("--cloud-max", type=int, default=DEFAULT_S2_CLOUD_MAX)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
