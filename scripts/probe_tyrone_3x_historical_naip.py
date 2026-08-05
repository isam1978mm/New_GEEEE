#!/usr/bin/env python3
"""Run the historical NAIP probe over the verified Tyrone No. 3X AOI.

The earlier generic probe was accidentally run over the southern R2C1/R2C2
block, which contains the reclaimed No. 2 facility. This wrapper fixes the AOI
to the northern R1C1/R1C2 block that contains No. 3X and refuses a conflicting
--bbox override.
"""
from __future__ import annotations

import sys
from collections.abc import Sequence

from scripts.probe_tyrone_historical_naip import main as generic_probe_main

TYRONE_3X_BBOX = (
    -108.42737364630895,
    32.69235978274562,
    -108.37347472926179,
    32.71503710254814,
)
TYRONE_3X_BBOX_TEXT = ",".join(str(value) for value in TYRONE_3X_BBOX)


def build_probe_argv(argv: Sequence[str]) -> list[str]:
    supplied = list(argv)
    if any(value == "--bbox" or value.startswith("--bbox=") for value in supplied):
        raise ValueError(
            "This dedicated No. 3X wrapper fixes the R1C1/R1C2 AOI; "
            "do not supply --bbox."
        )
    return ["--bbox", TYRONE_3X_BBOX_TEXT, *supplied]


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
