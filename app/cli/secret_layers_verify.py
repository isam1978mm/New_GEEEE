"""Local operator CLI for AI_READY secret-layer parity verification.

Thin wrapper over
:func:`app.pipeline.parity.secret_layers_verify.verify_secret_layers_parity`.
It does NOT reimplement the comparison: it D2-gates the reference bundle, then
delegates to the existing verifier (which already does raster metadata + masked
value comparison and records SHA256) and prints a safe, path-free summary by
default. ``--show-details`` adds local relative paths and per-output detail.

Read-only with respect to inputs. The underlying verifier writes only a JSON
report under ``--run-dir`` (a temp dir by default). No rasters/NPY are written.
Does not run Earth Engine.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Sequence

from app.pipeline.parity.secret_layers_verify import (
    SECRET_LAYERS_OUTPUT_NAMES,
    verify_secret_layers_parity,
)
from app.services.reference_bundle_validator import (
    STATUS_VALID,
    validate_reference_bundle,
)

DEFAULT_ATOL = 1e-6
DEFAULT_RTOL = 1e-6

STATUS_REFERENCE_INVALID = "reference_invalid"


def _logical_name(output_name: str) -> str:
    return output_name[:-4] if output_name.endswith(".tif") else output_name


def _counts_by_status(outputs: Sequence[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in outputs:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return dict(sorted(counts.items()))


def _safe_summary(
    overall_status: str,
    outputs: Sequence[dict[str, Any]],
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    """Counts + per-output status keyed by logical name. No raw paths/filenames."""

    per_output = {
        _logical_name(item["output_name"]): {
            "status": item["status"],
            "within_tolerance": item["within_tolerance"],
            "max_abs_diff": item["max_abs_diff"],
            "mean_abs_diff": item["mean_abs_diff"],
            "count_compared_pixels": item["count_compared_pixels"],
            "hash_match": item["hash_match"],
        }
        for item in outputs
    }
    return {
        "overall_status": overall_status,
        "expected_count": len(SECRET_LAYERS_OUTPUT_NAMES),
        "compared_count": len(outputs),
        "tolerance": {"atol": atol, "rtol": rtol},
        "counts_by_status": _counts_by_status(outputs),
        "per_output": dict(sorted(per_output.items())),
    }


def _detailed_report(
    overall_status: str,
    outputs: Sequence[dict[str, Any]],
    report_path: Path,
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    payload = _safe_summary(overall_status, outputs, atol=atol, rtol=rtol)
    payload["report_path"] = str(report_path)
    payload["outputs"] = list(outputs)
    return payload


def run_cli(
    *,
    app_output_dir: str,
    bundle_dir: str,
    run_dir: str | None = None,
    run_id: str = "secret_layers_cli",
    atol: float = DEFAULT_ATOL,
    rtol: float = DEFAULT_RTOL,
    show_details: bool = False,
) -> int:
    # D2 gate: refuse to compare against an invalid frozen reference bundle.
    d2 = validate_reference_bundle(bundle_dir)
    if d2.status != STATUS_VALID:
        payload: dict[str, Any] = {
            "overall_status": STATUS_REFERENCE_INVALID,
            "reference_bundle_status": d2.status,
            "reference_bundle_error": d2.error,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    effective_run_dir = Path(run_dir) if run_dir else Path(tempfile.mkdtemp(prefix="secret_layers_"))
    result = verify_secret_layers_parity(
        app_output_dir,
        bundle_dir,
        effective_run_dir,
        run_id,
        atol=atol,
        rtol=rtol,
    )
    outputs = list(result.outputs)
    payload = (
        _detailed_report(result.overall_status, outputs, result.report_path, atol=atol, rtol=rtol)
        if show_details
        else _safe_summary(result.overall_status, outputs, atol=atol, rtol=rtol)
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.overall_status == "passed" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "AI_READY secret-layer parity verification of an app output directory "
            "against a frozen reference bundle. D2-gated; reuses "
            "verify_secret_layers_parity."
        ),
    )
    parser.add_argument("--app-output-dir", required=True, help="App/run output directory.")
    parser.add_argument("--bundle-dir", required=True, help="Local path to the frozen reference bundle.")
    parser.add_argument(
        "--run-dir",
        default=None,
        help="Where the JSON verification report is written (default: a temp dir).",
    )
    parser.add_argument("--run-id", default="secret_layers_cli", help="Run id recorded in the report.")
    parser.add_argument("--atol", type=float, default=DEFAULT_ATOL, help="Absolute tolerance.")
    parser.add_argument("--rtol", type=float, default=DEFAULT_RTOL, help="Relative tolerance.")
    parser.add_argument(
        "--show-details",
        action="store_true",
        default=False,
        help="Local-only: also print per-output detail including relative paths and hashes.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_cli(
        app_output_dir=args.app_output_dir,
        bundle_dir=args.bundle_dir,
        run_dir=args.run_dir,
        run_id=args.run_id,
        atol=args.atol,
        rtol=args.rtol,
        show_details=args.show_details,
    )


if __name__ == "__main__":
    raise SystemExit(main())
