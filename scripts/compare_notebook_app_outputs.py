from __future__ import annotations

import argparse
from pathlib import Path

from app.services.numeric_parity_report import write_numeric_parity_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare notebook outputs against an app run directory and write a local-only parity report."
    )
    parser.add_argument("--notebook-root", type=Path, required=True, help="Root directory containing notebook outputs.")
    parser.add_argument("--app-run-dir", type=Path, required=True, help="App run directory under data/runs/<run_id>.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Local directory where numeric parity JSON and CSV reports will be written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    json_path, csv_path = write_numeric_parity_report(
        notebook_root=args.notebook_root,
        app_run_dir=args.app_run_dir,
        output_dir=args.output_dir,
    )
    print("Wrote local-only numeric parity reports.")
    print(json_path)
    print(csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
