from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import ee
import numpy as np

from app.config import get_settings
from app.pipeline.stages.grid import grid_spec_from_manifest
from app.pipeline.stages.dem import DEM_TILE_SIZE
from app.pipeline.stages.sar_rtc import (
    DEFAULT_END,
    DEFAULT_START,
    RADAR_BANDS,
    OUTPUT_BANDS,
    apply_local_dem_rtc,
    build_final_radar_image,
    build_sar_tile_requests,
    finalize_for_sample,
    img_by_id,
    load_dem_array,
    per_image_products_db,
    to_grid_radar,
)
from app.services.ee_session import initialize_ee_session
from app.services.grid import GridManifest

APP_INTERMEDIATE_MANIFEST_NAME = "sar_intermediate_manifest.json"
POST_RTC_BANDS = {
    "VV_dB": "VV_dB.npy",
    "VH_dB": "VH_dB.npy",
    "logRatio_dB": "logRatio_dB.npy",
    "incidence": "incidence.npy",
}
MODE_POST_RTC_ONLY = "post-rtc-only"
MODE_LIVE_CELL25_FULL = "live-cell25-full"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export local-only app-side Cell 25 SAR intermediate manifests."
    )
    parser.add_argument("--app-run-dir", type=Path, required=True, help="App run directory under data/runs/<run_id>.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory for the local-only intermediate manifest. Defaults to qa/sar/intermediates under the run.",
    )
    parser.add_argument(
        "--mode",
        choices=(MODE_POST_RTC_ONLY, MODE_LIVE_CELL25_FULL),
        default=MODE_POST_RTC_ONLY,
        help=(
            "Export mode. 'post-rtc-only' copies existing local final arrays without Earth Engine. "
            "'live-cell25-full' replays Cell 25 selection and exports all app-side SAR intermediate stages."
        ),
    )
    parser.add_argument("--start-date", type=str, default=DEFAULT_START, help="SAR start date for live replay mode.")
    parser.add_argument("--end-date", type=str, default=DEFAULT_END, help="SAR exclusive end date for live replay mode.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == MODE_LIVE_CELL25_FULL:
        manifest_path = export_app_full_intermediate_manifest(
            app_run_dir=args.app_run_dir,
            output_dir=args.output_dir,
            start_date=args.start_date,
            end_date=args.end_date,
        )
    else:
        manifest_path = export_app_post_rtc_manifest(app_run_dir=args.app_run_dir, output_dir=args.output_dir)
    print("Wrote local-only SAR intermediate manifest.")
    print(manifest_path)
    return 0


def export_app_post_rtc_manifest(*, app_run_dir: Path, output_dir: Path | None = None) -> Path:
    base_output_dir = _resolve_output_dir(app_run_dir, output_dir)
    post_rtc_dir = base_output_dir / "post_rtc"
    post_rtc_dir.mkdir(parents=True, exist_ok=True)

    bands: dict[str, str] = {}
    for band_name, filename in POST_RTC_BANDS.items():
        source_path = app_run_dir / "npy_radar_bands" / filename
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        destination = post_rtc_dir / filename
        shutil.copyfile(source_path, destination)
        manifest_band_name = "angle" if band_name == "incidence" else band_name
        bands[manifest_band_name] = f"post_rtc/{filename}"

    manifest = build_intermediate_manifest(
        stages={
            "post_rtc": {
                "label": "final",
                "bands": bands,
            }
        },
        missing_stages=[
            "per_image_products_db",
            "pair_median",
            "final_median_pre_rtc",
            "post_sample_pre_rtc",
        ],
        recommended_next_action=(
            "Run live-cell25-full mode or export notebook-side Cell 25 intermediates in the same manifest layout "
            "to localize the first divergence before changing SAR logic."
        ),
    )
    return write_intermediate_manifest(base_output_dir / APP_INTERMEDIATE_MANIFEST_NAME, manifest)


def export_app_full_intermediate_manifest(
    *,
    app_run_dir: Path,
    output_dir: Path | None,
    start_date: str,
    end_date: str,
) -> Path:
    base_output_dir = _resolve_output_dir(app_run_dir, output_dir)
    grid_manifest = GridManifest.model_validate_json((app_run_dir / "grid_manifest.json").read_text(encoding="utf-8"))
    grid_spec = grid_spec_from_manifest(grid_manifest)
    settings = get_settings()
    initialize_ee_session(settings)

    final_radar, pairs = build_final_radar_image(grid_spec, start_date=start_date, end_date=end_date)
    stage_arrays: dict[str, dict[str, dict[str, np.ndarray]]] = {
        "per_image_products_db": {},
        "pair_median": {},
    }

    pair_images: list[Any] = []
    for pair_index, pair in enumerate(pairs):
        asc_image = per_image_products_db(img_by_id(pair.asc_id, grid_spec))
        desc_image = per_image_products_db(img_by_id(pair.desc_id, grid_spec))
        stage_arrays["per_image_products_db"][f"pair{pair_index}_asc"] = _sample_stage_image(
            image=asc_image,
            grid_spec=grid_spec,
            band_names=RADAR_BANDS,
        )
        stage_arrays["per_image_products_db"][f"pair{pair_index}_desc"] = _sample_stage_image(
            image=desc_image,
            grid_spec=grid_spec,
            band_names=RADAR_BANDS,
        )
        pair_image = ee.ImageCollection([asc_image, desc_image]).median().select(list(RADAR_BANDS))
        pair_images.append(pair_image)
        stage_arrays["pair_median"][f"pair{pair_index}"] = _sample_stage_image(
            image=pair_image,
            grid_spec=grid_spec,
            band_names=RADAR_BANDS,
        )

    final_pair_stack = ee.ImageCollection(pair_images).median().select(list(RADAR_BANDS))
    stage_arrays["final_median_pre_rtc"] = {
        "final": _sample_stage_image(
            image=final_pair_stack,
            grid_spec=grid_spec,
            band_names=RADAR_BANDS,
        )
    }

    final_grid = to_grid_radar(final_pair_stack, grid_spec)
    final_for_sample = finalize_for_sample(final_grid, grid_spec)
    cube_3 = _sample_stage_cube(final_for_sample=final_for_sample, grid_spec=grid_spec)
    stage_arrays["post_sample_pre_rtc"] = {
        "final": {
            "VV_dB": cube_3[:, :, 0],
            "VH_dB": cube_3[:, :, 1],
            "angle": cube_3[:, :, 2],
        }
    }

    dem = load_dem_array(app_run_dir)
    outputs = apply_local_dem_rtc(
        cube_3,
        dem,
        nodata=grid_spec.nodata,
        scale_m=float(grid_spec.manifest.scale_m),
    )
    stage_arrays["post_rtc"] = {
        "final": {
            "VV_dB": outputs["VV_dB"],
            "VH_dB": outputs["VH_dB"],
            "logRatio_dB": outputs["logRatio_dB"],
            "angle": outputs["incidence"],
        }
    }

    manifest = build_intermediate_manifest(
        stages=serialize_stage_arrays(stage_arrays, base_output_dir),
        missing_stages=[],
        recommended_next_action="Use the matching notebook-side manifest to rerun F24 and localize the first divergence stage.",
    )
    return write_intermediate_manifest(base_output_dir / APP_INTERMEDIATE_MANIFEST_NAME, manifest)


def serialize_stage_arrays(
    stage_arrays: dict[str, dict[str, dict[str, np.ndarray]]],
    base_output_dir: Path,
) -> dict[str, Any]:
    stages_payload: dict[str, Any] = {}
    for stage_name, items in stage_arrays.items():
        if stage_name == "post_rtc" and set(items.keys()) == {"final"}:
            bands_payload = _write_band_arrays(
                base_output_dir=base_output_dir,
                stage_name=stage_name,
                label="final",
                bands=items["final"],
            )
            stages_payload[stage_name] = {"label": "final", "bands": bands_payload}
            continue
        item_payloads: list[dict[str, Any]] = []
        for label, bands in items.items():
            bands_payload = _write_band_arrays(
                base_output_dir=base_output_dir,
                stage_name=stage_name,
                label=label,
                bands=bands,
            )
            item_payloads.append({"label": label, "bands": bands_payload})
        stages_payload[stage_name] = {"items": item_payloads}
    return stages_payload


def build_intermediate_manifest(
    *,
    stages: dict[str, Any],
    missing_stages: list[str],
    recommended_next_action: str,
) -> dict[str, Any]:
    return {
        "artifact_class": "FILESYSTEM_ONLY",
        "local_only": True,
        "source_profile": "cell25_pixel_export",
        "stages": stages,
        "missing_stages": missing_stages,
        "recommended_next_action": recommended_next_action,
    }


def write_intermediate_manifest(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_band_arrays(
    *,
    base_output_dir: Path,
    stage_name: str,
    label: str,
    bands: dict[str, np.ndarray],
) -> dict[str, str]:
    bands_payload: dict[str, str] = {}
    for band_name, array in bands.items():
        relative = Path(stage_name) / f"{label}_{band_name}.npy"
        npy_path = base_output_dir / relative
        npy_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(npy_path, array.astype(np.float32, copy=False))
        bands_payload[band_name] = relative.as_posix()
    return bands_payload


def _resolve_output_dir(app_run_dir: Path, output_dir: Path | None) -> Path:
    return output_dir or (app_run_dir / "qa" / "sar" / "intermediates")


def _sample_stage_image(
    *,
    image,
    grid_spec,
    band_names: tuple[str, ...],
) -> dict[str, np.ndarray]:
    sampled = finalize_for_sample(to_grid_radar(ee.Image(image).select(list(band_names)), grid_spec), grid_spec)
    cube = _sample_stage_cube(final_for_sample=sampled, grid_spec=grid_spec, band_names=band_names)
    return {band_name: cube[:, :, idx] for idx, band_name in enumerate(band_names)}


def _sample_stage_cube(
    *,
    final_for_sample,
    grid_spec,
    band_names: tuple[str, ...] = RADAR_BANDS,
) -> np.ndarray:
    cube = np.full((grid_spec.size, grid_spec.size, len(band_names)), grid_spec.nodata, dtype=np.float32)
    for request in build_sar_tile_requests(grid_spec):
        tile_geo = ee.Geometry.Rectangle(
            [request["xmin"], request["ymin"], request["xmax"], request["ymax"]],
            grid_spec.crs,
            False,
        )
        rect = final_for_sample.sampleRectangle(region=tile_geo, defaultValue=grid_spec.nodata).getInfo()
        for band_index, band_name in enumerate(band_names):
            data = np.array(rect["properties"][band_name], dtype=np.float32)
            data = data[:DEM_TILE_SIZE, :DEM_TILE_SIZE]
            row_start = int(request["tile_row"]) * DEM_TILE_SIZE
            col_start = int(request["tile_col"]) * DEM_TILE_SIZE
            cube[row_start : row_start + DEM_TILE_SIZE, col_start : col_start + DEM_TILE_SIZE, band_index] = data
    return cube


if __name__ == "__main__":
    raise SystemExit(main())
