"""Diagnose INT-1 value mismatches without writing rasters or reports.

This script compares three arrays for each INT-1 output:

- the current app GeoTIFF output;
- the frozen notebook-reference GeoTIFF;
- the value recomputed from the local source cube(s) using the canonical INT-1
  writer formula.

It prints aggregate JSON metrics only. It does not copy reference rasters, does not
write raster outputs, and does not expose coordinate-bearing paths in the payload.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

import int1_generate_internal_rasters as writer


class INT1ValueDiagnosticError(ValueError):
    """Raised when INT-1 value mismatch diagnosis cannot proceed."""


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        payload = diagnose_int1_value_mismatch(
            run_dir=Path(args.run_dir),
            bundle_dir=Path(args.bundle_dir),
            app_output_dir=Path(args.app_output_dir) if args.app_output_dir else None,
            outputs=tuple(args.outputs) if args.outputs else None,
            denominator_epsilon=args.denominator_epsilon,
            atol=args.atol,
            rtol=args.rtol,
        )
    except INT1ValueDiagnosticError as exc:
        print(json.dumps({"ok": False, "status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


def diagnose_int1_value_mismatch(
    *,
    run_dir: Path,
    bundle_dir: Path,
    app_output_dir: Path | None = None,
    outputs: tuple[str, ...] | None = None,
    denominator_epsilon: float = writer.DEFAULT_DENOMINATOR_EPSILON,
    atol: float = 1e-6,
    rtol: float = 1e-6,
) -> dict[str, Any]:
    if denominator_epsilon <= 0:
        raise INT1ValueDiagnosticError("denominator_epsilon must be positive")
    if atol < 0 or rtol < 0:
        raise INT1ValueDiagnosticError("atol and rtol must be non-negative")

    app_root = Path(app_output_dir) if app_output_dir else Path(run_dir)
    reference_root = Path(bundle_dir)
    source_root = Path(run_dir)

    try:
        source_groups, source_payload = _load_notebook_contract_source_groups(source_root)
    except writer.INT1WriterError as exc:
        raise INT1ValueDiagnosticError(str(exc)) from exc

    specs_by_name = {spec.output_name: spec for spec in writer.INT1_OUTPUT_SPECS}
    selected_names = tuple(outputs) if outputs else tuple(specs_by_name)

    unknown_outputs = sorted(set(selected_names) - set(specs_by_name))
    if unknown_outputs:
        raise INT1ValueDiagnosticError("unknown INT-1 output names: " + ", ".join(unknown_outputs))

    rasterio_available = _rasterio_available()
    if not rasterio_available:
        raise INT1ValueDiagnosticError("rasterio is not importable")

    results = []
    for output_name in selected_names:
        spec = specs_by_name[output_name]
        app_path = app_root / output_name
        reference_path = reference_root / output_name
        if not app_path.is_file():
            raise INT1ValueDiagnosticError(f"app output is missing: {output_name}")
        if not reference_path.is_file():
            raise INT1ValueDiagnosticError(f"reference output is missing: {output_name}")

        bands = source_groups[spec.source_group]
        missing = sorted(set(spec.required_bands) - set(bands))
        if missing:
            raise INT1ValueDiagnosticError(f"missing source bands for {output_name}: " + ", ".join(missing))

        formula_data = spec.formula(bands, denominator_epsilon).astype(np.float64, copy=False)
        app_data = _read_raster_band(app_path)
        reference_data = _read_raster_band(reference_path)
        if app_data.shape != formula_data.shape or reference_data.shape != formula_data.shape:
            raise INT1ValueDiagnosticError(
                f"shape mismatch for {output_name}: "
                f"formula={formula_data.shape}, app={app_data.shape}, reference={reference_data.shape}"
            )

        formula_to_app = _compare_arrays(formula_data, app_data, atol=atol, rtol=rtol)
        formula_to_reference = _compare_arrays(formula_data, reference_data, atol=atol, rtol=rtol)
        app_to_reference = _compare_arrays(app_data, reference_data, atol=atol, rtol=rtol)
        results.append(
            {
                "output_name": output_name,
                "source_group": spec.source_group,
                "required_bands": list(spec.required_bands),
                "formula_stats": _array_stats(formula_data),
                "app_stats": _array_stats(app_data),
                "reference_stats": _array_stats(reference_data),
                "formula_to_app": formula_to_app,
                "formula_to_reference": formula_to_reference,
                "app_to_reference": app_to_reference,
                "diagnosis": _classify(formula_to_app, formula_to_reference, app_to_reference),
            }
        )

    diagnosis_counts: dict[str, int] = {}
    for item in results:
        diagnosis_counts[item["diagnosis"]] = diagnosis_counts.get(item["diagnosis"], 0) + 1

    return {
        "ok": True,
        "status": "int1_value_mismatch_diagnosed",
        "diagnostic_only": True,
        "writes_outputs": False,
        "reference_outputs_read": True,
        "raster_payloads_committed": False,
        "source_cube_name": writer.DEFAULT_S2_CUBE_NPY_NAME,
        "optional_b8a_source_name": writer.OPTIONAL_B8A_NPY_NAME,
        "optional_b8a_source_loaded": source_payload["optional_b8a_source_loaded"],
        "relation_source_cube_name": writer.RELATION_S2_CUBE_NPY_NAME,
        "relation_source_loaded": source_payload["relation_source_loaded"],
        "relation_source_fallback_to_default": source_payload["relation_source_fallback_to_default"],
        "optional_statue_logic_diff_name": writer.OPTIONAL_STATUE_LOGIC_DIFF_NPY_NAME,
        "optional_statue_logic_diff_loaded": source_payload["optional_statue_logic_diff_loaded"],
        "source_layout": "HWC_or_CHW_from_manifest_shape",
        "selected_output_count": len(results),
        "diagnosis_counts": diagnosis_counts,
        "tolerance": {"atol": atol, "rtol": rtol},
        "outputs": results,
    }


def _load_notebook_contract_source_groups(source_root: Path) -> tuple[dict[str, dict[str, np.ndarray]], dict[str, Any]]:
    default_bands, optional_b8a_loaded = writer._load_source_bands(
        source_root,
        cube_name=writer.DEFAULT_S2_CUBE_NPY_NAME,
        manifest_name=writer.DEFAULT_S2_MANIFEST_NAME,
        optional_b8a_name=writer.OPTIONAL_B8A_NPY_NAME,
    )
    optional_statue_logic_diff_loaded = writer._load_optional_single_array(
        source_root,
        array_name=writer.OPTIONAL_STATUE_LOGIC_DIFF_NPY_NAME,
        band_name=writer.STATUE_LOGIC_DIFF_BAND,
        bands=default_bands,
    )
    relation_bands, relation_source_loaded = writer._load_optional_relation_source_bands(source_root)
    if not relation_source_loaded:
        relation_bands = default_bands

    return (
        {
            writer.DEFAULT_SOURCE_GROUP: default_bands,
            writer.RELATION_SOURCE_GROUP: relation_bands,
        },
        {
            "optional_b8a_source_loaded": optional_b8a_loaded,
            "relation_source_loaded": relation_source_loaded,
            "relation_source_fallback_to_default": not relation_source_loaded,
            "optional_statue_logic_diff_loaded": optional_statue_logic_diff_loaded,
        },
    )


def _read_raster_band(path: Path) -> np.ndarray:
    import rasterio

    with rasterio.open(path) as dataset:
        data = dataset.read(1, masked=True).astype("float64")
    return np.ma.filled(data, np.nan)


def _array_stats(data: np.ndarray) -> dict[str, Any]:
    finite = np.isfinite(data)
    if not finite.any():
        return {
            "finite_count": 0,
            "nan_or_masked_count": int((~finite).sum()),
            "min": None,
            "max": None,
            "mean": None,
        }
    values = data[finite]
    return {
        "finite_count": int(finite.sum()),
        "nan_or_masked_count": int((~finite).sum()),
        "min": float(values.min()),
        "max": float(values.max()),
        "mean": float(values.mean()),
    }


def _compare_arrays(left: np.ndarray, right: np.ndarray, *, atol: float, rtol: float) -> dict[str, Any]:
    valid = np.isfinite(left) & np.isfinite(right)
    nan_or_masked = (~valid).sum()
    if not valid.any():
        return {
            "allclose_pass": True,
            "finite_compared_count": 0,
            "nan_or_masked_count": int(nan_or_masked),
            "max_abs_diff": 0.0,
            "mean_abs_diff": 0.0,
        }
    diffs = np.abs(left[valid] - right[valid])
    return {
        "allclose_pass": bool(np.allclose(left[valid], right[valid], atol=atol, rtol=rtol, equal_nan=True)),
        "finite_compared_count": int(valid.sum()),
        "nan_or_masked_count": int(nan_or_masked),
        "max_abs_diff": float(diffs.max()),
        "mean_abs_diff": float(diffs.mean()),
    }


def _classify(
    formula_to_app: dict[str, Any],
    formula_to_reference: dict[str, Any],
    app_to_reference: dict[str, Any],
) -> str:
    if app_to_reference["allclose_pass"]:
        return "app_reference_value_parity"
    if formula_to_app["allclose_pass"] and not formula_to_reference["allclose_pass"]:
        return "local_source_formula_matches_app_reference_differs"
    if formula_to_reference["allclose_pass"] and not formula_to_app["allclose_pass"]:
        return "local_source_formula_matches_reference_app_differs"
    if not formula_to_app["allclose_pass"] and not formula_to_reference["allclose_pass"]:
        return "formula_matches_neither_app_nor_reference"
    return "unclassified"


def _rasterio_available() -> bool:
    try:
        import rasterio  # noqa: F401
    except ImportError:
        return False
    return True


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose INT-1 app/reference value mismatches with aggregate metrics only.")
    parser.add_argument("--run-dir", required=True, help="App run directory containing source cube and manifest.")
    parser.add_argument("--app-output-dir", help="Directory containing app INT-1 GeoTIFF outputs. Defaults to --run-dir.")
    parser.add_argument("--bundle-dir", required=True, help="Frozen notebook reference bundle directory.")
    parser.add_argument("--outputs", nargs="*", help="Optional INT-1 output filenames to diagnose. Defaults to all 13 outputs.")
    parser.add_argument("--denominator-epsilon", type=float, default=writer.DEFAULT_DENOMINATOR_EPSILON)
    parser.add_argument("--atol", type=float, default=1e-6)
    parser.add_argument("--rtol", type=float, default=1e-6)
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
