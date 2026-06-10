"""Local CLI for the D3 DEM curvature reference comparison.

Compares the app's DEM curvature rasters against a frozen D1 reference bundle.
The frozen bundle must first pass the D2 validator; otherwise the comparison is
refused.

By default the CLI prints a counts-only safe summary (per-logical-artifact diff
magnitudes and pass/fail) and never echoes raw, potentially coordinate-bearing
filesystem paths. ``--show-details`` is a local-only opt-in that additionally
prints per-artifact findings including relative paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from app.pipeline.parity.dem_curvature_reference_comparison import (
    DEFAULT_ATOL,
    DEFAULT_RTOL,
    OVERALL_PASSED,
    compare_dem_curvature_references,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare app DEM curvature rasters against a frozen D1 reference "
            "bundle (presence, shape, dtype, CRS/transform, nodata, and value "
            "tolerances). Read-only; gated on D2 bundle validation."
        ),
    )
    parser.add_argument(
        "--app-output-dir",
        required=True,
        help="Local path to the app/run output directory containing curvature rasters.",
    )
    parser.add_argument(
        "--bundle-dir",
        required=True,
        help="Local path to the frozen D1 reference bundle (outside Git).",
    )
    parser.add_argument("--atol", type=float, default=DEFAULT_ATOL, help="Absolute tolerance.")
    parser.add_argument("--rtol", type=float, default=DEFAULT_RTOL, help="Relative tolerance.")
    parser.add_argument(
        "--allow-empty-reference-files",
        action="store_true",
        default=False,
        help="Permit zero-byte files in the reference bundle during D2 validation.",
    )
    parser.add_argument(
        "--show-details",
        action="store_true",
        default=False,
        help="Local-only: also print per-artifact findings, including relative paths.",
    )
    return parser


def run_cli(
    *,
    app_output_dir: str,
    bundle_dir: str,
    atol: float = DEFAULT_ATOL,
    rtol: float = DEFAULT_RTOL,
    allow_empty_reference_files: bool = False,
    show_details: bool = False,
) -> int:
    result = compare_dem_curvature_references(
        app_output_dir,
        bundle_dir,
        atol=atol,
        rtol=rtol,
        allow_empty_reference_files=allow_empty_reference_files,
    )
    payload = result.detailed_report() if show_details else result.safe_summary()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.status == OVERALL_PASSED else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_cli(
        app_output_dir=args.app_output_dir,
        bundle_dir=args.bundle_dir,
        atol=args.atol,
        rtol=args.rtol,
        allow_empty_reference_files=args.allow_empty_reference_files,
        show_details=args.show_details,
    )


if __name__ == "__main__":
    raise SystemExit(main())
