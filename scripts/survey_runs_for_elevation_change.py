"""Find which of your existing runs can support an elevation-change measurement.

Testing sites one at a time is slow, and most of the answer is knowable before
any data is downloaded. For every run directory this reports:

- whether US lidar covers it, which is the only route to a sub-metre cover;
- for each pair of global sources, how much of their difference is exactly zero.

That last figure is the one that has mattered in practice. Public global DEMs
fill their gaps from each other, and SRTM is the common ancestor of most of
them, so two apparently different products can turn out to be the same numbers
over a given site. Where they are, no amount of processing recovers a real
measurement.

Reads only. Writes nothing. Changes nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

if __package__ in (None, ""):  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ee  # noqa: E402

from app.config import Settings  # noqa: E402
from app.pipeline.elevation_change.coregistration import (  # noqa: E402
    SHARED_DATA_REFUSE_FRACTION,
)
from app.pipeline.elevation_change.sources import (  # noqa: E402
    ASSET_IMAGE_COLLECTION,
    SOURCES_BY_KEY,
)
from app.pipeline.stages.dem import build_grid_region  # noqa: E402
from app.pipeline.stages.grid import grid_spec_from_manifest  # noqa: E402
from app.services.ee_session import initialize_ee_session  # noqa: E402
from app.services.grid import GridManifest  # noqa: E402

GLOBAL_KEYS = ("nasadem", "alos_aw3d30", "copernicus_glo30")
LIDAR_KEY = "usgs_3dep_1m"
SAMPLE_SCALE_M = 90  # coarse on purpose; this is a screen, not a measurement


def _safe(callable_obj, default=None):
    try:
        return callable_obj()
    except Exception:  # noqa: BLE001 - screening tool, never fatal
        return default


def _source_image(key: str, region):
    source = SOURCES_BY_KEY[key]
    if source.asset_kind == ASSET_IMAGE_COLLECTION:
        return ee.ImageCollection(source.asset_id).filterBounds(region).mosaic().select(
            source.band
        )
    return ee.Image(source.asset_id).select(source.band)


def _shared_fraction(key_a: str, key_b: str, region) -> float | None:
    difference = _source_image(key_a, region).subtract(_source_image(key_b, region))
    result = _safe(
        lambda: difference.abs()
        .lt(0.0001)
        .rename("z")
        .reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=SAMPLE_SCALE_M,
            maxPixels=5_000_000,
            bestEffort=True,
        )
        .getInfo()
    )
    if isinstance(result, dict) and isinstance(result.get("z"), (int, float)):
        return float(result["z"])
    return None


def survey(runs_dir: Path) -> int:
    settings = Settings()
    initialize_ee_session(settings)

    run_dirs = sorted(
        path for path in runs_dir.iterdir()
        if path.is_dir() and (path / "grid_manifest.json").is_file()
    )
    if not run_dirs:
        print(f"No runs with a grid manifest under {runs_dir}")
        return 0

    print(f"Screening {len(run_dirs)} runs under {runs_dir}")
    print()

    viable: list[str] = []

    for run_dir in run_dirs:
        print(f"--- {run_dir.name} ---")
        manifest = _safe(
            lambda p=run_dir: GridManifest(
                **json.loads((p / "grid_manifest.json").read_text(encoding="utf-8"))
            )
        )
        if manifest is None:
            print("    unreadable grid manifest")
            print()
            continue

        grid_spec = grid_spec_from_manifest(manifest)
        region = build_grid_region(grid_spec)
        print(f"    grid: EPSG:{manifest.epsg}")

        lidar_source = SOURCES_BY_KEY[LIDAR_KEY]
        lidar_count = _safe(
            lambda: int(
                ee.ImageCollection(lidar_source.asset_id)
                .filterBounds(region)
                .size()
                .getInfo()
            ),
            default=None,
        )
        if lidar_count:
            print(f"    US lidar images    : {lidar_count}  <-- sub-metre route available")
        else:
            print("    US lidar images    : 0")

        best_pair = None
        best_shared = None
        for key_a, key_b in combinations(GLOBAL_KEYS, 2):
            shared = _shared_fraction(key_a, key_b, region)
            if shared is None:
                print(f"    {key_a:17s} vs {key_b:17s}: unavailable")
                continue
            verdict = "SHARED DATA" if shared >= SHARED_DATA_REFUSE_FRACTION else "independent"
            print(f"    {key_a:17s} vs {key_b:17s}: {shared:6.1%} identical  {verdict}")
            if best_shared is None or shared < best_shared:
                best_shared = shared
                best_pair = (key_a, key_b)

        if lidar_count and lidar_count > 1:
            viable.append(f"{run_dir.name}  (US lidar)")
        elif best_shared is not None and best_shared < SHARED_DATA_REFUSE_FRACTION:
            viable.append(f"{run_dir.name}  ({best_pair[0]} + {best_pair[1]})")
        print()

    print("=" * 64)
    if viable:
        print("RUNS THAT COULD SUPPORT A MEASUREMENT:")
        for entry in viable:
            print(f"  {entry}")
    else:
        print("NO RUN HERE CAN SUPPORT AN ELEVATION-CHANGE MEASUREMENT.")
        print()
        print("Every available source pair is substantially the same data at")
        print("these locations, and none has US lidar. That is a limit of the")
        print("free elevation record at these sites, not a software fault.")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Screen every run for elevation-change feasibility.",
    )
    parser.add_argument("--runs-dir", type=Path, default=Path("./data/runs"))
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    return survey(args.runs_dir)


if __name__ == "__main__":
    raise SystemExit(main())
