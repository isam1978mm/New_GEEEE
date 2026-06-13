"""Private CLI for app-side synthetic V6 package generation."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from app.services.v6_generator_package import generate_synthetic_v6_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a synthetic app-side V6 package shape. This command does not run "
            "Earth Engine and does not use real V6 artifacts."
        ),
    )
    parser.add_argument("--out", required=True, help="Operator-supplied output directory.")
    parser.add_argument(
        "--timestamp",
        default="20260101T120000Z",
        help="Synthetic timestamp in YYYYMMDDTHHMMSSZ format.",
    )
    parser.add_argument(
        "--package-name",
        default=None,
        help="Optional ZIP filename for the generated synthetic package.",
    )
    return parser


def run_cli(*, output_dir: str, timestamp: str, package_name: str | None = None) -> int:
    result = generate_synthetic_v6_package(
        output_dir=output_dir,
        timestamp=timestamp,
        package_name=package_name,
    )
    print(json.dumps(result.cli_summary(), indent=2, sort_keys=True))
    return 0 if result.is_verified else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_cli(
        output_dir=args.out,
        timestamp=args.timestamp,
        package_name=args.package_name,
    )


if __name__ == "__main__":
    raise SystemExit(main())
