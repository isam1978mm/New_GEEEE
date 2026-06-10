"""Local CLI for D3B-1 DEM curvature formula-isolation parity.

Feeds the app's curvature formulas the frozen D1C reference DEM and compares the
app-computed curvature rasters against the D1C reference rasters. Gated on D2
bundle validation. Read-only with respect to the bundle; writes generated
rasters only when ``--write-outputs-dir`` is given (use a temp dir outside Git).

Default output is a counts + diff-magnitude safe summary with no raw paths;
``--show-details`` adds per-artifact detail including relative reference paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from app.pipeline.parity.dem_curvature_formula_parity import (
    DEFAULT_ATOL,
    DEFAULT_RTOL,
    DEFAULT_NODATA,
    STATUS_PASSED,
    compare_dem_curvature_formula_parity,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "D3B-1: run the app DEM curvature formulas on the frozen D1C reference "
            "DEM and compare against D1C reference curvature rasters. Gated on D2."
        ),
    )
    parser.add_argument("--bundle-dir", required=True, help="Local path to the frozen D1C bundle.")
    parser.add_argument("--atol", type=float, default=DEFAULT_ATOL, help="Absolute tolerance.")
    parser.add_argument("--rtol", type=float, default=DEFAULT_RTOL, help="Relative tolerance.")
    parser.add_argument(
        "--scale-m",
        type=float,
        default=None,
        help="Pixel scale in metres (default: read SCALE from bundle RUN_MANIFEST, else 10).",
    )
    parser.add_argument("--nodata", type=float, default=DEFAULT_NODATA, help="DEM nodata sentinel.")
    parser.add_argument(
        "--write-outputs-dir",
        default=None,
        help="Optional temp dir (outside Git) to write the generated curvature arrays.",
    )
    parser.add_argument(
        "--show-details",
        action="store_true",
        default=False,
        help="Local-only: also print per-artifact detail including relative paths.",
    )
    return parser


def run_cli(
    *,
    bundle_dir: str,
    atol: float = DEFAULT_ATOL,
    rtol: float = DEFAULT_RTOL,
    scale_m: float | None = None,
    nodata: float = DEFAULT_NODATA,
    write_outputs_dir: str | None = None,
    show_details: bool = False,
) -> int:
    result = compare_dem_curvature_formula_parity(
        bundle_dir,
        atol=atol,
        rtol=rtol,
        scale_m=scale_m,
        nodata=nodata,
        write_outputs_dir=write_outputs_dir,
    )
    payload = result.detailed_report() if show_details else result.safe_summary()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.status == STATUS_PASSED else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_cli(
        bundle_dir=args.bundle_dir,
        atol=args.atol,
        rtol=args.rtol,
        scale_m=args.scale_m,
        nodata=args.nodata,
        write_outputs_dir=args.write_outputs_dir,
        show_details=args.show_details,
    )


if __name__ == "__main__":
    raise SystemExit(main())
