"""Local CLI for D3B-2 end-to-end app-generated DEM curvature parity.

Compares an independently app-generated output directory (DEM_640 + curvature
trio) against the frozen D1C reference bundle. Gated on D2. Read-only.

Default output is a counts + diff-magnitude safe summary with no raw paths;
``--show-details`` adds per-artifact detail including relative paths.
"""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from app.pipeline.parity.dem_curvature_end_to_end_parity import (
    DEFAULT_ATOL,
    DEFAULT_RTOL,
    DEFAULT_NODATA,
    STATUS_PASSED,
    compare_dem_curvature_end_to_end,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "D3B-2: compare an independently app-generated DEM + curvature output "
            "directory against the frozen D1C reference bundle. Gated on D2."
        ),
    )
    parser.add_argument("--app-output-dir", required=True, help="App-generated output directory.")
    parser.add_argument("--bundle-dir", required=True, help="Local path to the frozen D1C bundle.")
    parser.add_argument("--atol", type=float, default=DEFAULT_ATOL, help="Absolute tolerance.")
    parser.add_argument("--rtol", type=float, default=DEFAULT_RTOL, help="Relative tolerance.")
    parser.add_argument("--nodata", type=float, default=DEFAULT_NODATA, help="nodata sentinel.")
    parser.add_argument(
        "--show-details",
        action="store_true",
        default=False,
        help="Local-only: also print per-artifact detail including relative paths.",
    )
    return parser


def run_cli(
    *,
    app_output_dir: str,
    bundle_dir: str,
    atol: float = DEFAULT_ATOL,
    rtol: float = DEFAULT_RTOL,
    nodata: float = DEFAULT_NODATA,
    show_details: bool = False,
) -> int:
    result = compare_dem_curvature_end_to_end(
        app_output_dir, bundle_dir, atol=atol, rtol=rtol, nodata=nodata
    )
    payload = result.detailed_report() if show_details else result.safe_summary()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.status == STATUS_PASSED else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_cli(
        app_output_dir=args.app_output_dir,
        bundle_dir=args.bundle_dir,
        atol=args.atol,
        rtol=args.rtol,
        nodata=args.nodata,
        show_details=args.show_details,
    )


if __name__ == "__main__":
    raise SystemExit(main())
