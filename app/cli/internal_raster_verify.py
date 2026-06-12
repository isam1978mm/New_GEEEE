"""Local operator CLI for INT-1 internal semantic raster verification.

This CLI D2-gates the frozen reference bundle, delegates value comparison to
the existing AI_BEH raster verifiers, and prints a path-safe summary by default.
``--show-details`` adds local relative paths for operator debugging.

Read-only with respect to inputs. The delegated verifiers write only JSON
reports under ``--run-dir``. No rasters or NPY arrays are generated. Does not
run Earth Engine.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from app.pipeline.parity.ai_beh_alloy_statue_verify import (
    AI_BEH_ALLOY_STATUE_OUTPUT_NAME,
    verify_ai_beh_alloy_statue_parity,
)
from app.pipeline.parity.ai_beh_density_artifact_verify import (
    AI_BEH_DENSITY_ARTIFACT_OUTPUT_NAMES,
    verify_ai_beh_density_artifact_parity,
)
from app.pipeline.parity.ai_beh_extended_verify import (
    AI_BEH_EXTENDED_OUTPUT_NAMES,
    verify_ai_beh_extended_parity,
)
from app.pipeline.parity.ai_beh_logic_verify import (
    AI_BEH_LOGIC_OUTPUT_NAMES,
    verify_ai_beh_logic_parity,
)
from app.pipeline.parity.ai_beh_rare_material_verify import (
    AI_BEH_RARE_MATERIAL_OUTPUT_NAMES,
    verify_ai_beh_rare_material_parity,
)
from app.pipeline.parity.ai_beh_relation_verify import (
    AI_BEH_RELATION_OUTPUT_NAMES,
    verify_ai_beh_relation_parity,
)
from app.services.reference_bundle_validator import STATUS_VALID, validate_reference_bundle

DEFAULT_ATOL = 1e-6
DEFAULT_RTOL = 1e-6
STATUS_REFERENCE_INVALID = "reference_invalid"


VerifyFunction = Callable[..., Any]


@dataclass(frozen=True)
class InternalRasterFamilySpec:
    logical_name: str
    output_names: tuple[str, ...]
    verify: VerifyFunction


INT1_AI_BEH_FAMILIES: tuple[InternalRasterFamilySpec, ...] = (
    InternalRasterFamilySpec(
        logical_name="ai_beh_relation",
        output_names=AI_BEH_RELATION_OUTPUT_NAMES,
        verify=verify_ai_beh_relation_parity,
    ),
    InternalRasterFamilySpec(
        logical_name="ai_beh_extended",
        output_names=AI_BEH_EXTENDED_OUTPUT_NAMES,
        verify=verify_ai_beh_extended_parity,
    ),
    InternalRasterFamilySpec(
        logical_name="ai_beh_logic",
        output_names=AI_BEH_LOGIC_OUTPUT_NAMES,
        verify=verify_ai_beh_logic_parity,
    ),
    InternalRasterFamilySpec(
        logical_name="ai_beh_density_artifact",
        output_names=AI_BEH_DENSITY_ARTIFACT_OUTPUT_NAMES,
        verify=verify_ai_beh_density_artifact_parity,
    ),
    InternalRasterFamilySpec(
        logical_name="ai_beh_rare_material",
        output_names=AI_BEH_RARE_MATERIAL_OUTPUT_NAMES,
        verify=verify_ai_beh_rare_material_parity,
    ),
    InternalRasterFamilySpec(
        logical_name="ai_beh_alloy_statue",
        output_names=(AI_BEH_ALLOY_STATUE_OUTPUT_NAME,),
        verify=verify_ai_beh_alloy_statue_parity,
    ),
)


def _logical_output_name(output_name: str) -> str:
    return output_name[:-4] if output_name.endswith(".tif") else output_name


def _counts_by_status(outputs: Sequence[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in outputs:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return dict(sorted(counts.items()))


def _overall_status(outputs: Sequence[dict[str, Any]]) -> str:
    statuses = {item["status"] for item in outputs}
    if statuses == {"passed"}:
        return "passed"
    if statuses <= {"comparison_unavailable"}:
        return "comparison_unavailable"
    if "missing_app_output" in statuses or "missing_reference_output" in statuses:
        return "incomplete"
    return "failed"


def _result_outputs(result: Any) -> tuple[dict[str, Any], ...]:
    outputs = getattr(result, "outputs", None)
    if outputs is not None:
        return tuple(outputs)
    output = getattr(result, "output", None)
    return (output,) if output is not None else ()


def _family_summary(
    spec: InternalRasterFamilySpec,
    result: Any,
) -> dict[str, Any]:
    outputs = _result_outputs(result)
    return {
        "status": result.overall_status,
        "expected_count": len(spec.output_names),
        "compared_count": len(outputs),
        "counts_by_status": _counts_by_status(outputs),
        "raster_value_comparison_available": result.raster_value_comparison_available,
    }


def _safe_output_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": item["status"],
        "app_present": item["app_exists"],
        "reference_present": item["reference_exists"],
        "app_width": item.get("app_width"),
        "app_height": item.get("app_height"),
        "app_crs": item.get("app_crs"),
        "app_transform": item.get("app_transform"),
        "app_dtype": item.get("app_dtype"),
        "app_nodata": item.get("app_nodata"),
        "app_band_count": item.get("app_band_count"),
        "reference_width": item.get("reference_width"),
        "reference_height": item.get("reference_height"),
        "reference_crs": item.get("reference_crs"),
        "reference_transform": item.get("reference_transform"),
        "reference_dtype": item.get("reference_dtype"),
        "reference_nodata": item.get("reference_nodata"),
        "reference_band_count": item.get("reference_band_count"),
        "width_match": item["width_match"],
        "height_match": item["height_match"],
        "crs_match": item["crs_match"],
        "transform_match": item["transform_match"],
        "dtype_match": item["dtype_match"],
        "nodata_match": item["nodata_match"],
        "band_count_match": item["band_count_match"],
        "finite_compared_pixel_count": item["count_compared_values"],
        "nan_or_nodata_pixel_count": item["count_nan_or_nodata_values"],
        "max_abs_diff": item["max_abs_diff"],
        "mean_abs_diff": item["mean_abs_diff"],
        "allclose_pass": item["within_tolerance"],
        "sha256_match": item["hash_match"],
    }


def _safe_summary(
    family_results: Sequence[tuple[InternalRasterFamilySpec, Any]],
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    outputs = [
        item
        for _spec, result in family_results
        for item in _result_outputs(result)
    ]
    per_output = {
        _logical_output_name(item["output_name"]): _safe_output_item(item)
        for item in outputs
    }
    return {
        "overall_status": _overall_status(outputs),
        "family_count": len(family_results),
        "expected_count": sum(len(spec.output_names) for spec, _result in family_results),
        "compared_count": len(outputs),
        "tolerance": {"atol": atol, "rtol": rtol},
        "counts_by_status": _counts_by_status(outputs),
        "families": {
            spec.logical_name: _family_summary(spec, result)
            for spec, result in family_results
        },
        "per_output": dict(sorted(per_output.items())),
    }


def _relative_to_root(path_text: str, root: Path) -> str:
    path = Path(path_text)
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _rasterio_available() -> bool:
    return importlib.util.find_spec("rasterio") is not None


def _dataset_metadata(path: Path) -> dict[str, Any] | None:
    if not path.is_file() or not _rasterio_available():
        return None

    import rasterio

    with rasterio.open(path) as dataset:
        return {
            "width": dataset.width,
            "height": dataset.height,
            "crs": str(dataset.crs),
            "transform": [float(value) for value in tuple(dataset.transform)],
            "dtype": list(dataset.dtypes),
            "nodata": [
                None if value is None else float(value)
                for value in tuple(dataset.nodatavals)
            ],
            "band_count": dataset.count,
        }


def _enrich_output_metadata(outputs: Sequence[dict[str, Any]]) -> None:
    for item in outputs:
        app_metadata = _dataset_metadata(Path(str(item["app_path"])))
        reference_metadata = _dataset_metadata(Path(str(item["reference_path"])))
        if app_metadata is not None:
            item["app_width"] = app_metadata["width"]
            item["app_height"] = app_metadata["height"]
            item["app_crs"] = app_metadata["crs"]
            item["app_transform"] = app_metadata["transform"]
            item["app_dtype"] = app_metadata["dtype"]
            item["app_nodata"] = app_metadata["nodata"]
            item["app_band_count"] = app_metadata["band_count"]
        if reference_metadata is not None:
            item["reference_width"] = reference_metadata["width"]
            item["reference_height"] = reference_metadata["height"]
            item["reference_crs"] = reference_metadata["crs"]
            item["reference_transform"] = reference_metadata["transform"]
            item["reference_dtype"] = reference_metadata["dtype"]
            item["reference_nodata"] = reference_metadata["nodata"]
            item["reference_band_count"] = reference_metadata["band_count"]


def _detailed_report(
    family_results: Sequence[tuple[InternalRasterFamilySpec, Any]],
    *,
    app_root: Path,
    reference_root: Path,
    run_root: Path,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    payload = _safe_summary(family_results, atol=atol, rtol=rtol)
    detailed_families: dict[str, Any] = {}
    for spec, result in family_results:
        outputs: list[dict[str, Any]] = []
        for item in _result_outputs(result):
            detail = dict(item)
            detail["app_path"] = _relative_to_root(str(item["app_path"]), app_root)
            detail["reference_path"] = _relative_to_root(
                str(item["reference_path"]),
                reference_root,
            )
            outputs.append(detail)
        detailed_families[spec.logical_name] = {
            **_family_summary(spec, result),
            "report_path": _relative_to_root(str(result.report_path), run_root),
            "outputs": outputs,
        }
    payload["family_details"] = detailed_families
    return payload


def run_cli(
    *,
    app_output_dir: str,
    bundle_dir: str,
    run_dir: str | None = None,
    run_id: str = "internal_raster_cli",
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

    effective_run_dir = (
        Path(run_dir) if run_dir else Path(tempfile.mkdtemp(prefix="internal_raster_"))
    )
    family_results: list[tuple[InternalRasterFamilySpec, Any]] = []
    for spec in INT1_AI_BEH_FAMILIES:
        result = spec.verify(
            app_output_dir,
            bundle_dir,
            effective_run_dir,
            f"{run_id}_{spec.logical_name}",
            atol=atol,
            rtol=rtol,
        )
        _enrich_output_metadata(_result_outputs(result))
        family_results.append((spec, result))

    payload = (
        _detailed_report(
            family_results,
            app_root=Path(app_output_dir),
            reference_root=Path(bundle_dir),
            run_root=effective_run_dir,
            atol=atol,
            rtol=rtol,
        )
        if show_details
        else _safe_summary(family_results, atol=atol, rtol=rtol)
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["overall_status"] == "passed" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "INT-1 internal semantic raster parity verification of app outputs "
            "against a frozen D1C reference bundle. D2-gated; delegates to "
            "existing AI_BEH raster verifiers."
        ),
    )
    parser.add_argument("--app-output-dir", required=True, help="App/run output directory.")
    parser.add_argument("--bundle-dir", required=True, help="Local path to the frozen reference bundle.")
    parser.add_argument(
        "--run-dir",
        default=None,
        help="Where JSON verification reports are written (default: a temp dir).",
    )
    parser.add_argument("--run-id", default="internal_raster_cli", help="Run id recorded in reports.")
    parser.add_argument("--atol", type=float, default=DEFAULT_ATOL, help="Absolute tolerance.")
    parser.add_argument("--rtol", type=float, default=DEFAULT_RTOL, help="Relative tolerance.")
    parser.add_argument(
        "--show-details",
        action="store_true",
        default=False,
        help="Local-only: also print per-family detail including relative paths and hashes.",
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
