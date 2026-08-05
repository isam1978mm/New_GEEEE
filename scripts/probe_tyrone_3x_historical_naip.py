#!/usr/bin/env python3
"""Run the historical NAIP probe over the Tyrone No. 3X cross-row AOI.

The broad northern R1C1/R1C2 probe is dominated by reclaimed No. 3 and clips
only the northern edge of No. 3X. The broad southern probe is dominated by
reclaimed No. 2. Official 2007 and 2020 maps place No. 3X between those two
facilities, straddling the R1/R2 tile boundary. This wrapper fixes a tighter
cross-row AOI around that inter-facility zone and refuses a conflicting
--bbox override.

This remains a discovery/review probe. The fixed AOI does not itself prove
TP5/TP6 geometry or unlock numerical depth.
"""
from __future__ import annotations

import sys
from collections.abc import Sequence

from scripts.probe_tyrone_historical_naip import main as generic_probe_main

# Derived from the coordinate-controlled 2x2 USGS R1C1/R1C2/R2C1/R2C2 mosaic.
# The AOI spans the inter-facility strip shown between reclaimed No. 3 and
# reclaimed No. 2 on the official maps, including both sides of the R1/R2
# boundary at latitude 32.69235978274562.
TYRONE_3X_BBOX = (
    -108.42298734121071,
    32.68403150797445,
    -108.40017855469986,
    32.70248851664038,
)
TYRONE_3X_BBOX_TEXT = ",".join(str(value) for value in TYRONE_3X_BBOX)


def build_probe_argv(argv: Sequence[str]) -> list[str]:
    supplied = list(argv)
    if any(value == "--bbox" or value.startswith("--bbox=") for value in supplied):
        raise ValueError(
            "This dedicated No. 3X wrapper fixes the inter-facility cross-row AOI; "
            "do not supply --bbox."
        )
    # Keep the negative west longitude in the same argv token as --bbox.
    # Otherwise argparse can interpret the comma-separated negative value as
    # another option and report: argument --bbox: expected one argument.
    return [f"--bbox={TYRONE_3X_BBOX_TEXT}", *supplied]


def main(argv: Sequence[str] | None = None) -> int:
    supplied = list(sys.argv[1:] if argv is None else argv)
    try:
        probe_argv = build_probe_argv(supplied)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return generic_probe_main(probe_argv)


if __name__ == "__main__":
    raise SystemExit(main())
