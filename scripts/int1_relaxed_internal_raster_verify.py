from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

from app.services.reference_bundle_validator import STATUS_VALID, validate_reference_bundle

DEFAULT_ATOL = 1e-6
DEFAULT_RTOL = 1e-6
DEFAULT_TRANSFORM_ATOL = 1e-5
ACCEPTED_APP_NODATA = -9999.0

OUTPUTS = (
    "AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif",
    "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif",
    "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif",
    "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif",
    "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif",
    "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif",
    "AI_BEH_SecretEntry_REL_ND_DOM_lin_640.tif",
    "AI_BEH_StatueLogic_REL_Diff_DOM_lin_640.tif",
    "AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640.tif",
    "AI_BEH_Artifacts_Jars_Chests_DOM_lin_640.tif",
    "AI_BEH_Mercury_RareChemicals_DOM_lin_640.tif",
    "AI_BEH_Gemstones_AncientGlass_DOM_lin_640.tif",
    "AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.tif",
)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = verify_int1_relaxed(
        app_output_dir=Path(args.app_output_dir),
        bundle_dir=Path(args.bundle_dir),
        run_dir=Path(args.run_dir),
        run_id=args.run_id,
        atol=args.atol,
        rtol=args.rtol,
        transform_atol=args.transform_atol,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["overall_status"] == "passed" else 1


def verify_int1_relaxed(
    *,
    app_output_dir: Path,
    bundle_dir: Path,
    run_dir: Path,
    run_id: str,
    atol: float = DEFAULT_ATOL,
    rtol: float = DEFAULT_RTOL,
    transform_atol: float = DEFAULT_TRANSFORM_ATOL,
) -> dict[str, Any]:
    d2 = validate_reference_bundle(bundle_dir)
    if d2.status != STATUS_VALID:
        return {"overall_status": "reference_invalid", "reference_bundle_status": d2.status, "reference_bundle_error": d2.error}
    outputs = [
        _compare_one(
            output_name=name,
            app_path=app_output_dir / name,
            reference_path=bundle_dir / name,
            atol=atol,
            rtol=rtol,
            transform_atol=transform_atol,
        )
        for name in OUTPUTS
    ]
    counts: dict[str, int] = {}
    for item in outputs:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    payload = {
        "schema_version": "int1_relaxed_internal_raster_verification_v1",
        "run_id": run_id,
        "overall_status": "passed" if set(counts) == {"passed"} else "failed",
        "expected_count": len(OUTPUTS),
        "compared_count": len(outputs),
        "counts_by_status": dict(sorted(counts.items())),
        "tolerance": {"atol": atol, "rtol": rtol, "transform_atol": transform_atol},
        "per_output": {Path(item["output_name"]).stem: _safe_item(item) for item in outputs},
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / f"{run_id}_relaxed_summary.private.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _compare_one(*, output_name: str, app_path: Path, reference_path: Path, atol: float, rtol: float, transform_atol: float) -> dict[str, Any]:
    item: dict[str, Any] = {
        "output_name": output_name,
        "app_present": app_path.is_file(),
        "reference_present": reference_path.is_file(),
        "status": "comparison_unavailable",
        "sha256_match": None,
        "width_match": None,
        "height_match": None,
        "crs_match": None,
        "transform_match": None,
        "transform_max_abs_delta": None,
        "dtype_match": None,
        "nodata_match": None,
        "nodata_accepted": None,
        "band_count_match": None,
        "allclose_pass": False,
        "finite_compared_pixel_count": 0,
        "nan_or_nodata_pixel_count": 0,
        "max_abs_diff": None,
        "mean_abs_diff": None,
    }
    if not item["app_present"]:
        item["status"] = "missing_app_output"
        return item
    if not item["reference_present"]:
        item["status"] = "missing_reference_output"
        return item
    item["sha256_match"] = _sha256(app_path) == _sha256(reference_path)
    with rasterio.open(app_path) as app, rasterio.open(reference_path) as ref:
        app_transform = tuple(float(v) for v in tuple(app.transform))
        ref_transform = tuple(float(v) for v in tuple(ref.transform))
        transform_delta = [a - b for a, b in zip(app_transform, ref_transform)]
        transform_max_abs_delta = max(abs(v) for v in transform_delta)
        nodata_match = tuple(app.nodatavals) == tuple(ref.nodatavals)
        nodata_accepted = _nodata_accepted(tuple(app.nodatavals), tuple(ref.nodatavals))
        item.update({
            "app_width": app.width,
            "app_height": app.height,
            "app_crs": str(app.crs),
            "app_transform": list(app_transform),
            "app_dtype": list(app.dtypes),
            "app_nodata": [None if v is None else float(v) for v in app.nodatavals],
            "app_band_count": app.count,
            "reference_width": ref.width,
            "reference_height": ref.height,
            "reference_crs": str(ref.crs),
            "reference_transform": list(ref_transform),
            "reference_dtype": list(ref.dtypes),
            "reference_nodata": [None if v is None else float(v) for v in ref.nodatavals],
            "reference_band_count": ref.count,
            "width_match": app.width == ref.width,
            "height_match": app.height == ref.height,
            "crs_match": str(app.crs) == str(ref.crs),
            "transform_match": transform_max_abs_delta <= transform_atol,
            "transform_max_abs_delta": transform_max_abs_delta,
            "dtype_match": tuple(app.dtypes) == tuple(ref.dtypes),
            "nodata_match": nodata_match,
            "nodata_accepted": nodata_accepted,
            "band_count_match": app.count == ref.count,
        })
        metadata_ok = all(item[k] for k in ("width_match", "height_match", "crs_match", "transform_match", "dtype_match", "band_count_match")) and nodata_accepted
        if not metadata_ok:
            item["status"] = "metadata_mismatch"
            return item
        app_data = app.read(masked=True).astype("float64")
        ref_data = ref.read(masked=True).astype("float64")
    stats = _diff_stats(app_data, ref_data, atol=atol, rtol=rtol)
    item.update(stats)
    item["status"] = "passed" if stats["allclose_pass"] else "value_mismatch"
    return item


def _nodata_accepted(app_values: tuple[Any, ...], reference_values: tuple[Any, ...]) -> bool:
    if app_values == reference_values:
        return True
    if len(app_values) != len(reference_values):
        return False
    return all(ref is None and app == ACCEPTED_APP_NODATA for app, ref in zip(app_values, reference_values))


def _diff_stats(app_data: Any, ref_data: Any, *, atol: float, rtol: float) -> dict[str, Any]:
    app_filled = np.ma.filled(app_data, np.nan)
    ref_filled = np.ma.filled(ref_data, np.nan)
    valid = np.isfinite(app_filled) & np.isfinite(ref_filled)
    nan_or_nodata = int((~valid).sum())
    if not valid.any():
        return {"finite_compared_pixel_count": 0, "nan_or_nodata_pixel_count": nan_or_nodata, "max_abs_diff": 0.0, "mean_abs_diff": 0.0, "allclose_pass": True}
    diffs = np.abs(app_filled[valid] - ref_filled[valid])
    return {
        "finite_compared_pixel_count": int(valid.sum()),
        "nan_or_nodata_pixel_count": nan_or_nodata,
        "max_abs_diff": float(diffs.max()),
        "mean_abs_diff": float(diffs.mean()),
        "allclose_pass": bool(np.allclose(app_filled[valid], ref_filled[valid], atol=atol, rtol=rtol, equal_nan=True)),
    }


def _safe_item(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key != "output_name"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="D2-gated relaxed INT-1 internal raster verifier.")
    parser.add_argument("--app-output-dir", required=True)
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--run-id", default="int1-relaxed")
    parser.add_argument("--atol", type=float, default=DEFAULT_ATOL)
    parser.add_argument("--rtol", type=float, default=DEFAULT_RTOL)
    parser.add_argument("--transform-atol", type=float, default=DEFAULT_TRANSFORM_ATOL)
    return parser


if __name__ == "__main__":
    sys.exit(main())
