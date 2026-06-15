from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np

from app.pipeline.parity.report_640_verify import REPORT_640_OUTPUT_NAMES

STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_INCOMPLETE = "incomplete"
STATUS_UNAVAILABLE = "comparison_unavailable"

ART_PASSED = "passed"
ART_MISSING_APP = "missing_app_output"
ART_MISSING_REFERENCE = "missing_reference_output"
ART_METADATA_MISMATCH = "metadata_mismatch"
ART_VALUE_MISMATCH = "value_mismatch"
ART_UNAVAILABLE = "comparison_unavailable"

DEFAULT_ATOL = 1e-6
DEFAULT_RTOL = 1e-6


class D1ReportParityError(ValueError):
    pass


class ReportRasterUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReportRaster:
    values: np.ndarray
    dtype: str
    nodata: tuple[float | None, ...]
    width: int
    height: int
    count: int
    crs: str
    transform: tuple[float, ...]


ReportRasterReader = Callable[[Path], ReportRaster]


def find_by_name(root: Path, filename: str) -> Path | None:
    direct = root / filename
    if direct.is_file():
        return direct
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    return matches[0] if matches else None


def read_report_raster(path: Path) -> ReportRaster:
    try:
        import rasterio
    except ImportError as exc:
        raise ReportRasterUnavailableError("rasterio is not importable") from exc

    with rasterio.open(path) as dataset:
        values = dataset.read(masked=True).astype("float64")
        return ReportRaster(
            values=np.ma.asarray(values),
            dtype=",".join(str(item) for item in dataset.dtypes),
            nodata=tuple(float(item) if item is not None else None for item in dataset.nodatavals),
            width=int(dataset.width),
            height=int(dataset.height),
            count=int(dataset.count),
            crs=str(dataset.crs),
            transform=tuple(float(item) for item in dataset.transform),
        )


def metadata_matches(app: ReportRaster, ref: ReportRaster) -> bool:
    return all((
        app.width == ref.width,
        app.height == ref.height,
        app.count == ref.count,
        app.dtype == ref.dtype,
        app.nodata == ref.nodata,
        app.crs == ref.crs,
        app.transform == ref.transform,
    ))


def diff_stats(app_values: np.ma.MaskedArray, ref_values: np.ma.MaskedArray, *, atol: float, rtol: float) -> dict[str, Any]:
    app_mask = np.ma.getmaskarray(app_values) | ~np.isfinite(np.asarray(app_values.filled(np.nan)))
    ref_mask = np.ma.getmaskarray(ref_values) | ~np.isfinite(np.asarray(ref_values.filled(np.nan)))
    valid = ~(app_mask | ref_mask)
    count_compared = int(np.count_nonzero(valid))
    count_invalid = int(np.size(valid) - count_compared)
    if count_compared == 0:
        return {"max_abs_diff": None, "mean_abs_diff": None, "count_compared_pixels": 0, "count_nan_or_nodata_pixels": count_invalid, "within_tolerance": False}
    app_valid = np.asarray(app_values.filled(np.nan), dtype=np.float64)[valid]
    ref_valid = np.asarray(ref_values.filled(np.nan), dtype=np.float64)[valid]
    abs_diff = np.abs(app_valid - ref_valid)
    return {
        "max_abs_diff": float(np.max(abs_diff)),
        "mean_abs_diff": float(np.mean(abs_diff)),
        "count_compared_pixels": count_compared,
        "count_nan_or_nodata_pixels": count_invalid,
        "within_tolerance": bool(np.allclose(app_valid, ref_valid, atol=atol, rtol=rtol, equal_nan=True)),
    }


def compare_one(output_name: str, *, app_root: Path, reference_root: Path, reader: ReportRasterReader, atol: float, rtol: float) -> dict[str, Any]:
    app_path = find_by_name(app_root, output_name)
    ref_path = find_by_name(reference_root, output_name)
    item: dict[str, Any] = {
        "output_name": output_name,
        "status": ART_UNAVAILABLE,
        "app_present": app_path is not None,
        "reference_present": ref_path is not None,
        "metadata_match": None,
        "values_compared": False,
        "max_abs_diff": None,
        "mean_abs_diff": None,
        "count_compared_pixels": 0,
        "count_nan_or_nodata_pixels": 0,
        "within_tolerance": False,
    }
    if app_path is None:
        item["status"] = ART_MISSING_APP
        return item
    if ref_path is None:
        item["status"] = ART_MISSING_REFERENCE
        return item
    try:
        app = reader(app_path)
        ref = reader(ref_path)
    except ReportRasterUnavailableError:
        item["status"] = ART_UNAVAILABLE
        return item
    if not metadata_matches(app, ref):
        item["status"] = ART_METADATA_MISMATCH
        item["metadata_match"] = False
        return item
    stats = diff_stats(np.ma.asarray(app.values), np.ma.asarray(ref.values), atol=atol, rtol=rtol)
    item.update(stats)
    item["metadata_match"] = True
    item["values_compared"] = True
    item["status"] = ART_PASSED if stats["within_tolerance"] else ART_VALUE_MISMATCH
    return item


def compare_d1_report_value_parity(*, app_output_dir: str | Path, reference_report_root: str | Path, atol: float = DEFAULT_ATOL, rtol: float = DEFAULT_RTOL, reader: ReportRasterReader | None = None) -> dict[str, Any]:
    app_root = Path(app_output_dir)
    ref_root = Path(reference_report_root)
    if not app_root.is_dir():
        raise D1ReportParityError("app output directory is missing")
    if not ref_root.is_dir():
        raise D1ReportParityError("reference report root is missing")
    raster_reader = reader or read_report_raster
    outputs = [compare_one(name, app_root=app_root, reference_root=ref_root, reader=raster_reader, atol=atol, rtol=rtol) for name in REPORT_640_OUTPUT_NAMES]
    statuses = {item["status"] for item in outputs}
    if statuses == {ART_PASSED}:
        status = STATUS_PASSED
    elif statuses & {ART_MISSING_APP, ART_MISSING_REFERENCE}:
        status = STATUS_INCOMPLETE
    elif statuses == {ART_UNAVAILABLE}:
        status = STATUS_UNAVAILABLE
    else:
        status = STATUS_FAILED
    return {
        "schema_version": "d1_report_value_parity_v1",
        "created_at": datetime.now(UTC).isoformat(),
        "status": status,
        "pass_count": sum(item["status"] == ART_PASSED for item in outputs),
        "fail_count": sum(item["status"] in {ART_METADATA_MISMATCH, ART_VALUE_MISMATCH} for item in outputs),
        "missing_count": sum(item["status"] in {ART_MISSING_APP, ART_MISSING_REFERENCE} for item in outputs),
        "comparison_unavailable_count": sum(item["status"] == ART_UNAVAILABLE for item in outputs),
        "outputs": outputs,
        "tolerance": {"atol": atol, "rtol": rtol},
        "notes": "Report value parity reads local report rasters and reports safe metrics only.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run D1 local report output value parity against app outputs.")
    parser.add_argument("--app-output-dir", required=True)
    parser.add_argument("--reference-report-root", required=True)
    parser.add_argument("--report")
    parser.add_argument("--atol", type=float, default=DEFAULT_ATOL)
    parser.add_argument("--rtol", type=float, default=DEFAULT_RTOL)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = compare_d1_report_value_parity(app_output_dir=args.app_output_dir, reference_report_root=args.reference_report_root, atol=args.atol, rtol=args.rtol)
    except D1ReportParityError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"FAIL: {exc}")
        return 1
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps({"ok": result["status"] == STATUS_PASSED, **result}, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        print(f"pass_count: {result['pass_count']}")
        print(f"fail_count: {result['fail_count']}")
        print(f"missing_count: {result['missing_count']}")
        print(f"comparison_unavailable_count: {result['comparison_unavailable_count']}")
        print("note: report value parity only; not full notebook parity")
    return 0 if result["status"] == STATUS_PASSED else 2


if __name__ == "__main__":
    sys.exit(main())
