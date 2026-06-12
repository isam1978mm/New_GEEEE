"""Local operator CLI for 2.5 m hypercube/tensor parity verification.

Thin wrapper over
:func:`app.pipeline.parity.hypercube_res25_verify.verify_hypercube_res25_parity`.
It D2-gates the frozen reference bundle, delegates comparison to the existing
verifier, and prints a path-safe summary by default. ``--show-details`` prints
local relative paths for operator debugging.

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

from app.pipeline.parity.hypercube_res25_verify import (
    HYPERCUBE_RES25_OUTPUT_NAMES,
    verify_hypercube_res25_parity,
)
from app.services.reference_bundle_validator import (
    STATUS_VALID,
    validate_reference_bundle,
)

DEFAULT_ATOL = 1e-6
DEFAULT_RTOL = 1e-6

STATUS_REFERENCE_INVALID = "reference_invalid"

_SAFE_OUTPUT_KEYS = {
    "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif": "resampled_hypercube_tif",
    "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy": "resampled_hypercube_npy",
}


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
    per_output = {
        _SAFE_OUTPUT_KEYS[item["output_name"]]: {
            "status": item["status"],
            "app_present": item["app_present"],
            "reference_present": item["reference_present"],
            "shape_match": item["shape_match"],
            "dtype_match": item["dtype_match"],
            "app_finite_count": item["app_finite_count"],
            "app_nan_count": item["app_nan_count"],
            "app_inf_count": item["app_inf_count"],
            "reference_finite_count": item["reference_finite_count"],
            "reference_nan_count": item["reference_nan_count"],
            "reference_inf_count": item["reference_inf_count"],
            "compared_element_count": item["compared_element_count"],
            "max_abs_diff": item["max_abs_diff"],
            "mean_abs_diff": item["mean_abs_diff"],
            "allclose_pass": item["allclose_pass"],
            "sha256_match": item["sha256_match"],
        }
        for item in outputs
    }
    return {
        "overall_status": overall_status,
        "expected_count": len(HYPERCUBE_RES25_OUTPUT_NAMES),
        "compared_count": len(outputs),
        "tolerance": {"atol": atol, "rtol": rtol},
        "counts_by_status": _counts_by_status(outputs),
        "per_output": dict(sorted(per_output.items())),
    }


def _relative_to_root(path_text: str, root: Path) -> str:
    path = Path(path_text)
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _detailed_report(
    overall_status: str,
    outputs: Sequence[dict[str, Any]],
    report_path: Path,
    *,
    app_root: Path,
    reference_root: Path,
    run_root: Path,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    payload = _safe_summary(overall_status, outputs, atol=atol, rtol=rtol)
    payload["report_path"] = _relative_to_root(str(report_path), run_root)
    detail_outputs: list[dict[str, Any]] = []
    for item in outputs:
        detail = dict(item)
        detail["app_path"] = _relative_to_root(str(item["app_path"]), app_root)
        detail["reference_path"] = _relative_to_root(str(item["reference_path"]), reference_root)
        detail_outputs.append(detail)
    payload["outputs"] = detail_outputs
    return payload


def run_cli(
    *,
    app_output_dir: str,
    bundle_dir: str,
    run_dir: str | None = None,
    run_id: str = "hypercube_res25_cli",
    atol: float = DEFAULT_ATOL,
    rtol: float = DEFAULT_RTOL,
    show_details: bool = False,
) -> int:
    d2 = validate_reference_bundle(bundle_dir)
    if d2.status != STATUS_VALID:
        payload: dict[str, Any] = {
            "overall_status": STATUS_REFERENCE_INVALID,
            "reference_bundle_status": d2.status,
            "reference_bundle_error": d2.error,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    effective_run_dir = Path(run_dir) if run_dir else Path(tempfile.mkdtemp(prefix="hypercube_res25_"))
    result = verify_hypercube_res25_parity(
        app_output_dir,
        bundle_dir,
        effective_run_dir,
        run_id,
        atol=atol,
        rtol=rtol,
    )
    outputs = list(result.outputs)
    payload = (
        _detailed_report(
            result.overall_status,
            outputs,
            result.report_path,
            app_root=Path(app_output_dir),
            reference_root=Path(bundle_dir),
            run_root=effective_run_dir,
            atol=atol,
            rtol=rtol,
        )
        if show_details
        else _safe_summary(result.overall_status, outputs, atol=atol, rtol=rtol)
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.overall_status == "passed" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "2.5 m hypercube/tensor parity verification of an app output directory "
            "against a frozen D1C reference bundle. D2-gated; reuses "
            "verify_hypercube_res25_parity."
        ),
    )
    parser.add_argument("--app-output-dir", required=True, help="App/run output directory.")
    parser.add_argument("--bundle-dir", required=True, help="Local path to the frozen reference bundle.")
    parser.add_argument(
        "--run-dir",
        default=None,
        help="Where the JSON verification report is written (default: a temp dir).",
    )
    parser.add_argument("--run-id", default="hypercube_res25_cli", help="Run id recorded in the report.")
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
