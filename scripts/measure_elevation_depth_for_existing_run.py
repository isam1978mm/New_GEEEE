"""Measure placed-material depth for an existing run from public elevation data.

One command, end to end, with nobody to contact:

1. fetch two public elevation epochs onto the run's locked grid;
2. co-register them and measure the placed thickness;
3. derive reviewed anchor and candidate zones from the measurement;
4. optionally drive the existing local-depth engine with those zones.

Step 4 is what the depth workstream was blocked on. It has always worked; it
simply had no measured anchors to work from.

Two modes:

- ``--offline-early/--offline-late`` read two elevation GeoTIFFs already on
  disk. No Earth Engine session is required, which makes the whole path
  runnable and reviewable without credentials.
- Otherwise both epochs are fetched from Earth Engine using the run's grid
  manifest, which needs a working service account.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

if __package__ in (None, ""):  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings  # noqa: E402
from app.pipeline._base import StageContext  # noqa: E402
from app.pipeline.elevation_change.sources import COVERAGE_UNITED_STATES  # noqa: E402
from app.pipeline.stages.elevation_change import (  # noqa: E402
    STAGE_DIR_NAME,
    STATUS_MEASURED,
    SUMMARY_NAME,
    ZONES_GEOJSON_NAME,
    ElevationChangeStage,
)
from app.pipeline.stages.grid import GridSpec, grid_spec_from_manifest  # noqa: E402
from app.services.grid import GridManifest  # noqa: E402


class MeasuredElevationDepthError(RuntimeError):
    """Raised when the measured-depth workflow cannot proceed."""


def _load_grid_spec(run_dir: Path) -> GridSpec:
    manifest_path = run_dir / "grid_manifest.json"
    if not manifest_path.is_file():
        raise MeasuredElevationDepthError(
            f"missing grid manifest: {manifest_path}. The run must have completed "
            "its grid stage before elevation change can be measured on the same grid."
        )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return grid_spec_from_manifest(GridManifest(**payload))


def _offline_fetcher(raster_path: Path, grid_spec: GridSpec):
    """Serve grid tiles from a GeoTIFF already aligned to the run grid."""

    import rasterio

    with rasterio.open(raster_path) as dataset:
        surface = dataset.read(1).astype(np.float32)

    expected = (grid_spec.size, grid_spec.size)
    if surface.shape != expected:
        raise MeasuredElevationDepthError(
            f"{raster_path.name} has shape {surface.shape}, expected {expected}. "
            "Offline epochs must already sit on the run grid."
        )

    def fetch_tile(*, grid_spec, tile_row, tile_col, xmin, ymin, xmax, ymax, size):
        del grid_spec, xmin, ymin, xmax, ymax
        row_start = tile_row * size
        col_start = tile_col * size
        return surface[row_start : row_start + size, col_start : col_start + size]

    return fetch_tile


def measure_elevation_depth_for_existing_run(
    *,
    run_dir: Path,
    coverage: str = COVERAGE_UNITED_STATES,
    target_thickness_m: float | None = None,
    source_keys: list[str] | None = None,
    offline_early: Path | None = None,
    offline_late: Path | None = None,
    drive_depth_engine: bool = False,
    site_id: str = "measured-elevation-site",
    force: bool = False,
) -> dict[str, Any]:
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        raise MeasuredElevationDepthError(f"run directory does not exist: {run_dir}")

    grid_spec = _load_grid_spec(run_dir)

    if (offline_early is None) != (offline_late is None):
        raise MeasuredElevationDepthError(
            "offline mode needs both --offline-early and --offline-late"
        )

    early_fetcher = None
    late_fetcher = None
    if offline_early is not None and offline_late is not None:
        early_fetcher = _offline_fetcher(Path(offline_early), grid_spec)
        late_fetcher = _offline_fetcher(Path(offline_late), grid_spec)

    stage = ElevationChangeStage(
        grid_spec=grid_spec,
        coverage=coverage,
        target_thickness_m=target_thickness_m,
        source_keys=source_keys,
        early_tile_fetcher=early_fetcher,
        late_tile_fetcher=late_fetcher,
    )
    context = StageContext(run_id=run_dir.name, settings=Settings(), run_dir=run_dir)
    stage_result = asyncio.run(stage.run(context))

    summary = json.loads(
        (run_dir / STAGE_DIR_NAME / SUMMARY_NAME).read_text(encoding="utf-8")
    )
    result: dict[str, Any] = {
        "status": summary["status"],
        "measurement_kind": summary["measurement_kind"],
        "measures": summary["measures"],
        "does_not_measure": summary["does_not_measure"],
        "zone_count": summary["zone_count"],
        "anchor_count": summary["anchor_count"],
        "candidate_count": summary["candidate_count"],
        "predicted_minimum_detectable_thickness_m": (
            summary["source_pair"]["minimum_detectable_thickness_m"]
            if summary.get("source_pair")
            else None
        ),
        # The predicted figure above is a conservative worldwide average for the
        # products involved. The two below are what this pair actually achieved
        # over this ground, and they are the ones to judge a result by.
        "measured_noise_floor_sigma_m": (
            summary["coregistration"]["stable_ground"]["sigma_m"]
            if summary.get("coregistration")
            else None
        ),
        "measured_minimum_detectable_thickness_m": (
            round(1.96 * summary["coregistration"]["stable_ground"]["sigma_m"], 4)
            if summary.get("coregistration")
            else None
        ),
        "vertical_offset_removed_m": (
            summary["coregistration"]["stable_ground"]["offset_m"]
            if summary.get("coregistration")
            else None
        ),
        "measured_thickness_m": [
            {
                "zone_id": zone["zone_id"],
                "role": zone["role"],
                "thickness_m": zone["mean_change_m"],
                "uncertainty_m": zone["sigma_m"],
            }
            for zone in summary.get("zones", [])
        ],
        "warnings": summary["warnings"],
        "outputs": [
            artifact.relative_path for artifact in stage_result.artifacts
        ],
        "depth_engine": None,
    }

    if not drive_depth_engine:
        return result

    if summary["status"] != STATUS_MEASURED:
        result["depth_engine"] = {"skipped": "no_measurable_change"}
        return result

    zones_path = run_dir / STAGE_DIR_NAME / ZONES_GEOJSON_NAME
    if not zones_path.is_file():
        result["depth_engine"] = {"skipped": "no_reviewed_zone_file"}
        return result

    # Imported lazily so the measurement path does not depend on the depth
    # engine's own imports when the engine is not being driven.
    from scripts.build_operator_local_depth_package import (
        build_operator_local_depth_package,
    )
    from scripts.extract_operator_depth_signals import extract_operator_depth_signals
    from scripts.run_operator_local_depth_for_existing_run import (
        run_operator_depth_for_existing_run,
    )

    work_root = run_dir / STAGE_DIR_NAME / "depth_engine"
    extraction_dir = work_root / "extraction"
    package_dir = work_root / "package"

    extract_operator_depth_signals(
        run_dir=run_dir,
        polygons_path=zones_path,
        output_dir=extraction_dir,
        site_id=site_id,
        method_version="measured_elevation_change_v1",
        calibration_dataset_version="public_elevation_change_v1",
        input_crs=grid_spec.crs,
        erosion_pixels=2,
        minimum_valid_pixels=20,
    )
    build_operator_local_depth_package(
        config_path=extraction_dir / "operator_depth_config.json",
        output_dir=package_dir,
    )
    execution = run_operator_depth_for_existing_run(
        run_dir=run_dir,
        package_dir=package_dir,
        candidate_input=extraction_dir / "operator_depth_candidates.json",
        force=force,
    )
    result["depth_engine"] = {
        "status": execution["status"],
        "candidate_count": execution["candidate_count"],
        "estimated_count": execution["estimated_count"],
        "insufficient_data_count": execution["insufficient_data_count"],
        "method_kind": execution["method_kind"],
        "warnings": execution["warnings"],
    }
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Measure placed-material depth for an existing run from public "
            "elevation data. Requires no site visit, records request, or contact "
            "with any organisation."
        ),
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument(
        "--coverage",
        default=COVERAGE_UNITED_STATES,
        choices=["united_states", "global"],
        help="United States unlocks lidar-to-lidar pairs; global cannot resolve a metre.",
    )
    parser.add_argument(
        "--target-thickness-m",
        type=float,
        default=None,
        help="Warn when the expected cover is below the pair's detection floor.",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=None,
        metavar="KEY",
        help=(
            "Restrict the pair to these source keys, e.g. --sources nasadem "
            "alos_aw3d30. Use after diagnose_elevation_pair.py shows the default "
            "pair shares data at your location."
        ),
    )
    parser.add_argument("--offline-early", type=Path, default=None)
    parser.add_argument("--offline-late", type=Path, default=None)
    parser.add_argument(
        "--drive-depth-engine",
        action="store_true",
        help="Feed the measured zones into the existing local-depth engine.",
    )
    parser.add_argument("--site-id", default="measured-elevation-site")
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = measure_elevation_depth_for_existing_run(
        run_dir=args.run_dir,
        coverage=args.coverage,
        target_thickness_m=args.target_thickness_m,
        source_keys=args.sources,
        offline_early=args.offline_early,
        offline_late=args.offline_late,
        drive_depth_engine=args.drive_depth_engine,
        site_id=args.site_id,
        force=args.force,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
