from __future__ import annotations

import argparse
from pathlib import Path

from app.services.full_job_local_output_report import FULL_JOB_LOCAL_OUTPUT_REPORT_NAME, write_full_job_local_output_comparison_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write the local full-job notebook-output comparison report after scanning a run directory."
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Completed run directory to scan. Defaults to --output-dir for backwards compatibility.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data") / "reports",
        help="Local directory where the comparison report will be written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_path = write_full_job_local_output_comparison_report(args.output_dir, run_dir=args.run_dir)
    print(f"Wrote {FULL_JOB_LOCAL_OUTPUT_REPORT_NAME} to local output directory.")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
