"""Local read-only CLI for validating an external frozen V6 package."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from app.services.v6_package_validator import validate_v6_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an external frozen V6 package by streaming ZIP members and "
            "checking the inventory. Read-only; does not extract, copy, or serve outputs."
        ),
    )
    parser.add_argument("--zip", required=True, help="External frozen V6 ZIP path.")
    parser.add_argument("--inventory", required=True, help="External frozen V6 inventory JSON path.")
    parser.add_argument(
        "--reference-doc",
        default="docs/V6_FROZEN_REFERENCE.md",
        help="Tracked V6 reference doc containing the expected ZIP SHA256.",
    )
    return parser


def run_cli(*, zip_path: str, inventory_path: str, reference_doc_path: str) -> int:
    result = validate_v6_package(
        zip_path=zip_path,
        inventory_path=inventory_path,
        reference_doc_path=reference_doc_path,
    )
    print(json.dumps(result.safe_summary(), indent=2, sort_keys=True))
    return 0 if result.is_verified else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_cli(
        zip_path=args.zip,
        inventory_path=args.inventory,
        reference_doc_path=args.reference_doc,
    )


if __name__ == "__main__":
    raise SystemExit(main())
