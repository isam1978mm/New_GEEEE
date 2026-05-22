from __future__ import annotations

import argparse
from pathlib import Path

from app.services.numeric_parity_diagnostics import write_numeric_parity_diagnosis_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose numeric parity failures and missing notebook mappings from a local parity report."
    )
    parser.add_argument("--parity-report", type=Path, required=True, help="Path to the F11 numeric parity JSON report.")
    parser.add_argument("--app-run-dir", type=Path, required=True, help="App run directory under data/runs/<run_id>.")
    parser.add_argument(
        "--notebook-root",
        type=Path,
        action="append",
        required=True,
        help="Notebook output root. Repeat this flag to search multiple notebook roots.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Local directory where diagnosis JSON and CSV reports will be written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    json_path, csv_path = write_numeric_parity_diagnosis_report(
        parity_report_path=args.parity_report,
        app_run_dir=args.app_run_dir,
        notebook_roots=args.notebook_root,
        output_dir=args.output_dir,
    )
    print("Wrote local-only numeric parity diagnosis reports.")
    print(json_path)
    print(csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
