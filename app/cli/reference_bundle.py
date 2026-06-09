"""Local CLI for validating a frozen D1 ``notebooks/new.ipynb`` reference bundle.

By default the CLI prints a counts-only safe summary and never echoes raw,
potentially coordinate-bearing relative paths. The ``--show-details`` flag is a
local-only opt-in that additionally prints per-file findings (including relative
paths) for an operator debugging a bundle on their own machine.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from app.services.reference_bundle_validator import (
    STATUS_VALID,
    validate_reference_bundle,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a frozen D1 notebook reference bundle (presence, sizes, and "
            "SHA256 checksums). Read-only; does not generate or serve any outputs."
        ),
    )
    parser.add_argument(
        "--bundle-dir",
        required=True,
        help="Local filesystem path to the frozen reference bundle (outside Git).",
    )
    parser.add_argument(
        "--allow-empty-files",
        action="store_true",
        default=False,
        help="Treat zero-byte reference files as acceptable instead of flagging them.",
    )
    parser.add_argument(
        "--show-details",
        action="store_true",
        default=False,
        help="Local-only: also print per-file findings, including relative paths.",
    )
    return parser


def run_cli(
    *,
    bundle_dir: str,
    allow_empty_files: bool = False,
    show_details: bool = False,
) -> int:
    result = validate_reference_bundle(bundle_dir, allow_empty_files=allow_empty_files)
    payload = result.detailed_report() if show_details else result.safe_summary()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.status == STATUS_VALID else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_cli(
        bundle_dir=args.bundle_dir,
        allow_empty_files=args.allow_empty_files,
        show_details=args.show_details,
    )


if __name__ == "__main__":
    raise SystemExit(main())
