"""Local CLI for the D1A bundle-wide frozen reference scope audit.

Reports which expected ``notebooks/new.ipynb`` outputs are present, missing, or
extra in a frozen D1 reference bundle. Read-only; does not run the notebook,
Earth Engine, or modify the bundle.

By default the CLI prints a counts + family-name safe summary and never echoes
raw relative paths. ``--show-details`` is a local-only opt-in that additionally
prints per-family relative paths and the extra-file list.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from app.pipeline.parity.reference_scope_audit import (
    STATUS_COMPLETE,
    audit_reference_scope,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit a frozen D1 reference bundle's scope against the notebook "
            "expected-output set (present / missing / extra). Read-only."
        ),
    )
    parser.add_argument(
        "--bundle-dir",
        required=True,
        help="Local path to the frozen D1 reference bundle (outside Git).",
    )
    parser.add_argument(
        "--expected-outputs",
        default=None,
        help=(
            "Optional path to an expected-output source (.json parity doc or .md). "
            "Defaults to docs/parity_expected_outputs.json."
        ),
    )
    parser.add_argument(
        "--show-details",
        action="store_true",
        default=False,
        help="Local-only: also print per-family relative paths and the extra list.",
    )
    return parser


def run_cli(
    *,
    bundle_dir: str,
    expected_outputs: str | None = None,
    show_details: bool = False,
) -> int:
    result = audit_reference_scope(
        bundle_dir,
        expected_outputs_path=expected_outputs,
    )
    payload = result.detailed_report() if show_details else result.safe_summary()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.status == STATUS_COMPLETE else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_cli(
        bundle_dir=args.bundle_dir,
        expected_outputs=args.expected_outputs,
        show_details=args.show_details,
    )


if __name__ == "__main__":
    raise SystemExit(main())
