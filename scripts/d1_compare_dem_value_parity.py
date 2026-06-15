from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from app.pipeline.parity.dem_curvature_end_to_end_parity import (
    ART_EDGE_ONLY_MISMATCH,
    ART_INTERIOR_MISMATCH,
    ART_MISSING_APP,
    ART_MISSING_REFERENCE,
    ART_PASSED,
    ART_SHAPE_MISMATCH,
    END_TO_END_ARTIFACTS,
    STATUS_FAILED,
    STATUS_INCOMPLETE,
    STATUS_PASSED,
    STATUS_UNAVAILABLE,
    EndToEndArtifactResult,
    _compare_one,
    _diagnostic,
)
from app.pipeline.parity.dem_curvature_formula_parity import (
    DEFAULT_ATOL,
    DEFAULT_NODATA,
    DEFAULT_RTOL,
    RasterReader,
    RasterUnavailableError,
    _read_raw_raster,
)


class D1DemParityError(ValueError):
    pass


def _safe_artifact_entry(result: EndToEndArtifactResult) -> dict[str, Any]:
    entry = result.safe_entry()
    entry["logical_name"] = result.logical_name
    entry["relative_path"] = result.relative_path
    entry["notes"] = result.notes
    return entry


def compare_d1_dem_value_parity(
    *,
    app_output_dir: str | Path,
    reference_dem_root: str | Path,
    atol: float = DEFAULT_ATOL,
    rtol: float = DEFAULT_RTOL,
    nodata: float = DEFAULT_NODATA,
    raster_reader: RasterReader | None = None,
) -> dict[str, Any]:
    app_root = Path(app_output_dir)
    ref_root = Path(reference_dem_root)
    if not app_root.is_dir():
        raise D1DemParityError("app output directory is missing")
    if not ref_root.is_dir():
        raise D1DemParityError("reference DEM root is missing")

    reader = raster_reader or _read_raw_raster
    try:
        artifacts = tuple(
            _compare_one(
                name,
                rel,
                app_root=app_root,
                reference_root=ref_root,
                reader=reader,
                atol=atol,
                rtol=rtol,
                nodata=nodata,
            )
            for name, rel in END_TO_END_ARTIFACTS
        )
    except RasterUnavailableError as exc:
        return {
            "schema_version": "d1_dem_value_parity_v1",
            "created_at": datetime.now(UTC).isoformat(),
            "status": STATUS_UNAVAILABLE,
            "pass_count": 0,
            "fail_count": 0,
            "missing_count": 0,
            "dem_matches": None,
            "diagnostic": str(exc),
            "artifacts": [],
            "notes": "DEM value parity could not run because no raster backend is available.",
        }

    dem = next((item for item in artifacts if item.logical_name == "DEM_640"), None)
    dem_matches = dem.passed if dem is not None else None
    curvature_ok = all(
        item.status in {ART_PASSED, ART_EDGE_ONLY_MISMATCH}
        for item in artifacts
        if item.logical_name != "DEM_640"
    )
    fail_count = sum(item.status in {ART_INTERIOR_MISMATCH, ART_SHAPE_MISMATCH} for item in artifacts)
    missing_count = sum(item.status in {ART_MISSING_APP, ART_MISSING_REFERENCE} for item in artifacts)
    pass_count = sum(item.status == ART_PASSED for item in artifacts)

    if fail_count:
        status = STATUS_FAILED
    elif missing_count:
        status = STATUS_INCOMPLETE
    elif artifacts and all(item.status in {ART_PASSED, ART_EDGE_ONLY_MISMATCH} for item in artifacts):
        status = STATUS_PASSED
    else:
        status = STATUS_INCOMPLETE

    return {
        "schema_version": "d1_dem_value_parity_v1",
        "created_at": datetime.now(UTC).isoformat(),
        "status": status,
        "pass_count": pass_count,
        "fail_count": int(fail_count),
        "missing_count": int(missing_count),
        "dem_matches": dem_matches,
        "diagnostic": _diagnostic(dem, curvature_ok),
        "tolerance": {"atol": atol, "rtol": rtol},
        "nodata": nodata,
        "artifacts": [_safe_artifact_entry(item) for item in artifacts],
        "notes": "DEM value parity reads local raster values and reports only safe metrics. It does not expose artifact contents or local private paths.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run D1-local DEM value parity against app outputs.")
    parser.add_argument("--app-output-dir", required=True)
    parser.add_argument("--reference-dem-root", required=True)
    parser.add_argument("--report")
    parser.add_argument("--atol", type=float, default=DEFAULT_ATOL)
    parser.add_argument("--rtol", type=float, default=DEFAULT_RTOL)
    parser.add_argument("--nodata", type=float, default=DEFAULT_NODATA)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = compare_d1_dem_value_parity(
            app_output_dir=args.app_output_dir,
            reference_dem_root=args.reference_dem_root,
            atol=args.atol,
            rtol=args.rtol,
            nodata=args.nodata,
        )
    except D1DemParityError as exc:
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
        print(f"dem_matches: {result['dem_matches']}")
        print(f"diagnostic: {result['diagnostic']}")
        print("note: DEM value parity only; not full notebook parity")
    return 0 if result["status"] == STATUS_PASSED else 2


if __name__ == "__main__":
    sys.exit(main())
