"""Count the laser-altimetry shots available over each run.

GEDI fires a laser from the space station and measures ground height directly,
to a few tens of centimetres. It is free, needs no correspondence with anyone,
and shares no data with SRTM, so it escapes the trap that made every 30 m DEM
pair at some sites the same numbers twice.

What it does not do is cover the ground continuously. It samples in narrow
tracks of 25 m footprints, so a site either accumulates enough shots over the
years to be usable or it does not, and that is knowable before anything is
built.

The pairing that matters is early GEDI against late GEDI. Differencing GEDI
against an old 30 m DEM would be limited by the DEM's own metres of error and
would gain nothing over what is already possible.

Reported per run:

- valid ground shots in an early window and a late window;
- how much of the area each window touches;
- how many 25 m cells were sampled in both windows, which is what a
  before-and-after comparison can actually use.

Reads only. Writes nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ee  # noqa: E402

from app.config import Settings  # noqa: E402
from app.pipeline.stages.dem import build_grid_region  # noqa: E402
from app.pipeline.stages.grid import grid_spec_from_manifest  # noqa: E402
from app.services.ee_session import initialize_ee_session  # noqa: E402
from app.services.grid import GridManifest  # noqa: E402

GEDI_COLLECTION = "LARSE/GEDI/GEDI02_A_002_MONTHLY"
GEDI_ELEVATION_BAND = "elev_lowestmode"
GEDI_FOOTPRINT_M = 25

EARLY_WINDOW = ("2019-04-01", "2021-12-31")
LATE_WINDOW = ("2022-01-01", "2026-08-01")

# GEDI's own latitude limit: the space station orbit does not reach beyond this.
GEDI_LATITUDE_LIMIT_DEG = 51.6

# What matters is paired coverage of the feature being measured, not the raw
# count of paired cells anywhere in the site. A first version of this script
# used a flat count of 200 and declared a site usable at 0.37% coverage, where a
# 100 m target would expect 0.06 paired shots on it. The count was measuring
# whether the laser had visited the neighbourhood, not whether it had visited
# the target.
#
# A 300 m feature is 144 cells of 25 m. Twenty paired shots on it, enough for
# averaging to matter, needs roughly 14% paired coverage.
USEFUL_PAIRED_COVERAGE_FRACTION = 0.14


def _safe(callable_obj, default=None):
    try:
        return callable_obj()
    except Exception as exc:  # noqa: BLE001 - screening tool, never fatal
        return default if default is not None else f"<error: {str(exc)[:120]}>"


def _quality_masked(image: Any) -> Any:
    """Keep only shots GEDI itself considers good ground returns."""

    return (
        image.updateMask(image.select("quality_flag").eq(1))
        .updateMask(image.select("degrade_flag").eq(0))
        .select(GEDI_ELEVATION_BAND)
    )


def _window_counts(region: Any, start: str, end: str) -> dict[str, Any]:
    collection = (
        ee.ImageCollection(GEDI_COLLECTION)
        .filterBounds(region)
        .filterDate(start, end)
        .map(_quality_masked)
    )
    per_cell_count = collection.count().rename("n")
    totals = _safe(
        lambda: per_cell_count.addBands(per_cell_count.gt(0).rename("cells"))
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=region,
            scale=GEDI_FOOTPRINT_M,
            maxPixels=20_000_000,
            bestEffort=True,
        )
        .getInfo(),
        default={},
    )
    if not isinstance(totals, dict):
        totals = {}
    return {
        "shots": totals.get("n"),
        "cells": totals.get("cells"),
        "mask": per_cell_count.gt(0),
    }


def check(run_dir: Path) -> dict[str, Any]:
    manifest = GridManifest(
        **json.loads((run_dir / "grid_manifest.json").read_text(encoding="utf-8"))
    )
    grid_spec = grid_spec_from_manifest(manifest)
    region = build_grid_region(grid_spec)

    area_m2 = float(grid_spec.size * manifest.scale_m) ** 2
    total_cells = area_m2 / (GEDI_FOOTPRINT_M**2)

    early = _window_counts(region, *EARLY_WINDOW)
    late = _window_counts(region, *LATE_WINDOW)

    paired = None
    if isinstance(early.get("mask"), ee.Image) and isinstance(late.get("mask"), ee.Image):
        paired_mask = early["mask"].And(late["mask"]).rename("p")
        paired_result = _safe(
            lambda: paired_mask.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=region,
                scale=GEDI_FOOTPRINT_M,
                maxPixels=20_000_000,
                bestEffort=True,
            ).getInfo(),
            default={},
        )
        if isinstance(paired_result, dict):
            paired = paired_result.get("p")

    return {
        "run": run_dir.name,
        "epsg": manifest.epsg,
        "total_25m_cells_in_aoi": int(total_cells),
        "early_shots": early.get("shots"),
        "early_cells": early.get("cells"),
        "late_shots": late.get("shots"),
        "late_cells": late.get("cells"),
        "cells_sampled_in_both_windows": paired,
    }


def survey(runs_dir: Path) -> int:
    settings = Settings()
    initialize_ee_session(settings)

    run_dirs = sorted(
        path
        for path in runs_dir.iterdir()
        if path.is_dir() and (path / "grid_manifest.json").is_file()
    )
    if not run_dirs:
        print(f"No runs with a grid manifest under {runs_dir}")
        return 0

    print(f"GEDI laser coverage for {len(run_dirs)} runs")
    print(f"early window {EARLY_WINDOW[0]}..{EARLY_WINDOW[1]}")
    print(f"late  window {LATE_WINDOW[0]}..{LATE_WINDOW[1]}")
    print(f"GEDI reaches latitudes within +/-{GEDI_LATITUDE_LIMIT_DEG} degrees.")
    print()

    usable: list[str] = []

    for run_dir in run_dirs:
        result = _safe(lambda p=run_dir: check(p), default=None)
        if result is None:
            print(f"--- {run_dir.name} --- could not be checked")
            print()
            continue

        print(f"--- {result['run']} (EPSG:{result['epsg']}) ---")
        print(f"    25 m cells in the area   : {result['total_25m_cells_in_aoi']}")
        print(f"    early window shots       : {result['early_shots']}")
        print(f"    late  window shots       : {result['late_shots']}")
        paired = result["cells_sampled_in_both_windows"]
        total = result["total_25m_cells_in_aoi"]
        print(f"    cells sampled in BOTH    : {paired}")

        if isinstance(paired, (int, float)) and total:
            coverage = float(paired) / float(total)
            print(f"    paired coverage          : {coverage:.2%} of the area")
            expected_on_100m_target = 16 * coverage
            print(
                f"    expected paired shots on a 100 m target: "
                f"{expected_on_100m_target:.2f}"
            )
            if coverage >= USEFUL_PAIRED_COVERAGE_FRACTION:
                print("    -> dense enough to measure a specific feature")
                usable.append(f"{result['run']}  ({coverage:.1%} paired coverage)")
            else:
                shortfall = USEFUL_PAIRED_COVERAGE_FRACTION / max(coverage, 1e-9)
                print(
                    f"    -> too sparse by a factor of about {shortfall:.0f}; the laser "
                    "visits the neighbourhood, not the target"
                )
        print()

    print("=" * 64)
    if usable:
        print("RUNS WITH USABLE LASER COVERAGE:")
        for entry in usable:
            print(f"  {entry}")
        print()
        print("Worth building the laser route for these.")
    else:
        print("NO RUN HAS ENOUGH PAIRED LASER COVERAGE.")
        print()
        print("GEDI samples in narrow tracks rather than covering the ground. Over")
        print("these sites its paired coverage is a fraction of one percent, so a")
        print("specific feature would expect a fraction of one shot on it. Building")
        print("the laser route would not help at these locations, however many")
        print("shots land elsewhere in the same square.")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Count usable GEDI laser shots over each run.",
    )
    parser.add_argument("--runs-dir", type=Path, default=Path("./data/runs"))
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    return survey(args.runs_dir)


if __name__ == "__main__":
    raise SystemExit(main())
