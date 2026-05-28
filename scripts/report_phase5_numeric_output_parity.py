from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from app.services.phase5_numeric_output_parity_summary import build_phase5_numeric_output_parity_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the local Phase 5 numeric output parity summary.")
    parser.add_argument("--app-run-dir", type=Path, default=None)
    parser.add_argument("--reference-bundle-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    app_run_dir = args.app_run_dir or _env_path("APP_NOTEBOOK_OUTPUT_RUN_DIR")
    reference_bundle_dir = args.reference_bundle_dir or _env_path("NOTEBOOK_REFERENCE_BUNDLE_DIR")
    report = build_phase5_numeric_output_parity_summary(
        app_run_dir=app_run_dir,
        notebook_reference_bundle_dir=reference_bundle_dir,
    )
    payload = json.dumps(report, indent=2, sort_keys=True)
    print(payload)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    return 0


def _env_path(name: str) -> Path | None:
    raw = os.environ.get(name)
    if raw:
        return Path(raw).expanduser()
    env_path = Path(".env")
    if not env_path.is_file():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == name:
            return Path(value.strip().strip('"').strip("'")).expanduser()
    return None


if __name__ == "__main__":
    raise SystemExit(main())
