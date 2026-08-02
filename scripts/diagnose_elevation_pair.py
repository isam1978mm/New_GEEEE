"""Check whether an elevation pair is really two independent measurements.

A measured vertical offset of exactly zero between two different missions is not
a good sign. It is what you would see if the two surfaces were partly the same
data, and it would make the noise floor look far better than it is while hiding
real change.

The Copernicus DEM ships a Filling Mask band that records where its heights were
taken from another source rather than measured by TanDEM-X. Where that filling
came from SRTM, differencing it against NASADEM compares SRTM with itself.

This script reports:

- how much of the area Copernicus marks as filled rather than measured;
- how much of the area Copernicus marks as edited;
- Copernicus's own per-pixel height error estimate over the area;
- the distribution of the raw difference, including how much of it is exactly
  zero, which is the direct symptom of shared data.

It reads only, writes nothing, and changes nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ee  # noqa: E402

from app.config import Settings  # noqa: E402
from app.pipeline.stages.dem import build_grid_region  # noqa: E402
from app.pipeline.stages.grid import grid_spec_from_manifest  # noqa: E402
from app.services.ee_session import initialize_ee_session  # noqa: E402
from app.services.grid import GridManifest  # noqa: E402

COPERNICUS_ID = "COPERNICUS/DEM/GLO30_2024_1"
NASADEM_ID = "NASA/NASADEM_HGT/001"


def _safe(callable_obj):
    try:
        return callable_obj()
    except Exception as exc:  # noqa: BLE001 - reporting tool, never fatal
        return f"<error: {type(exc).__name__}: {str(exc)[:200]}>"


def diagnose(run_dir: Path) -> int:
    settings = Settings()
    initialize_ee_session(settings)

    manifest_path = run_dir / "grid_manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing grid manifest: {manifest_path}")
    grid_spec = grid_spec_from_manifest(
        GridManifest(**json.loads(manifest_path.read_text(encoding="utf-8")))
    )
    region = build_grid_region(grid_spec)
    scale = 30

    copernicus = ee.ImageCollection(COPERNICUS_ID).filterBounds(region).mosaic()
    nasadem = ee.Image(NASADEM_ID)

    print("=" * 64)
    print("IS THIS PAIR REALLY TWO INDEPENDENT MEASUREMENTS?")
    print("=" * 64)
    print()

    print("--- Copernicus Filling Mask (FLM) ---")
    print("    0 means measured by TanDEM-X. Anything else was filled in from")
    print("    another source, and SRTM is one of those sources.")
    filling = _safe(
        lambda: copernicus.select("FLM")
        .reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=region,
            scale=scale,
            maxPixels=10_000_000,
            bestEffort=True,
        )
        .getInfo()
    )
    print(f"    {filling}")
    print()

    print("--- Copernicus Editing Mask (EDM) ---")
    editing = _safe(
        lambda: copernicus.select("EDM")
        .reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=region,
            scale=scale,
            maxPixels=10_000_000,
            bestEffort=True,
        )
        .getInfo()
    )
    print(f"    {editing}")
    print()

    print("--- Copernicus Height Error Mask (HEM), metres ---")
    print("    Copernicus's own estimate of its per-pixel vertical error.")
    height_error = _safe(
        lambda: copernicus.select("HEM")
        .reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True),
            geometry=region,
            scale=scale,
            maxPixels=10_000_000,
            bestEffort=True,
        )
        .getInfo()
    )
    print(f"    {height_error}")
    print()

    print("--- Raw difference, Copernicus minus NASADEM, metres ---")
    difference = copernicus.select("DEM").subtract(nasadem.select("elevation")).rename("d")
    percentiles = _safe(
        lambda: difference.reduceRegion(
            reducer=ee.Reducer.percentile([1, 5, 25, 50, 75, 95, 99]),
            geometry=region,
            scale=scale,
            maxPixels=10_000_000,
            bestEffort=True,
        ).getInfo()
    )
    print(f"    {percentiles}")
    print()

    print("--- How much of the difference is EXACTLY zero? ---")
    print("    Independent measurements essentially never agree exactly.")
    print("    A large share here means the two surfaces share data.")
    exact_zero = _safe(
        lambda: difference.abs()
        .lt(0.0001)
        .rename("z")
        .reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=scale,
            maxPixels=10_000_000,
            bestEffort=True,
        )
        .getInfo()
    )
    if isinstance(exact_zero, dict) and isinstance(exact_zero.get("z"), (int, float)):
        share = float(exact_zero["z"])
        print(f"    fraction within 0.1 mm of zero: {share:.4f}  ({share * 100:.2f}%)")
        print()
        if share > 0.20:
            print("    VERDICT: these two surfaces share data over much of this area.")
            print("    The measured noise floor is not trustworthy, and real change")
            print("    in the shared parts would be invisible.")
        else:
            print("    VERDICT: no sign of shared data. The exact-zero offset was a")
            print("    coincidence of a flat, well-aligned site.")
    else:
        print(f"    {exact_zero}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check whether an elevation pair is two independent measurements.",
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    return diagnose(args.run_dir)


if __name__ == "__main__":
    raise SystemExit(main())
