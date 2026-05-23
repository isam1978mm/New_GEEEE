from __future__ import annotations

import argparse
from pathlib import Path

from app.services.sar_processing_parity import write_sar_processing_parity_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write a local-only SAR processing parity report from notebook outputs and an app run."
    )
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
        help="Local directory where SAR processing parity JSON and CSV reports will be written.",
    )
    parser.add_argument(
        "--prior-report",
        type=Path,
        default=None,
        help="Optional previous local SAR processing parity JSON report for improvement/regression diagnostics.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    json_path, csv_path = write_sar_processing_parity_report(
        app_run_dir=args.app_run_dir,
        notebook_roots=args.notebook_root,
        output_dir=args.output_dir,
        prior_report_path=args.prior_report,
    )
    print("Wrote local-only SAR processing parity reports.")
    print(json_path)
    print(csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
