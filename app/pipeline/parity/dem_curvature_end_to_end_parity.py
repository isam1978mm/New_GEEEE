"""D3B-2 — end-to-end app-generated DEM curvature parity against D1C.

Where D3B-1 isolated the curvature *formulas* (feeding the app's
``compute_dem_derivatives`` the frozen reference DEM), D3B-2 compares an
**independently app-generated** output directory (its own EE-fetched DEM on the
app's grid, plus its curvature rasters) against the frozen D1C reference.

It compares, file-vs-file:

  * ``DEM_GEO8_TIFS/DEM_640.tif``            (app DEM vs reference DEM)
  * ``DEM_GEO8_TIFS/curv_laplacian_640.tif``
  * ``DEM_GEO8_TIFS/curv_plan_640.tif``
  * ``DEM_GEO8_TIFS/curv_profile_640.tif``

Diagnostic rule: if the app DEM differs from the reference DEM, curvature
differences are attributed to an upstream DEM/grid/source mismatch. If the DEM
matches but curvature differs, that is a writer/path/integration issue (since
D3B-1 proved formula parity). Interior vs edge/nodata differences are reported
separately and never hidden.

Read-only with respect to the bundle; gated on D2. Does not change DEM formulas,
run Earth Engine, or modify the notebook/bundle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from app.pipeline.parity.dem_curvature_formula_parity import (
    DEFAULT_ATOL,
    DEFAULT_RTOL,
    DEFAULT_NODATA,
    RasterReader,
    RasterUnavailableError,
    _diff_block,
    _edge_mask,
    _read_raw_raster,
)
from app.services.reference_bundle_validator import STATUS_VALID, validate_reference_bundle

DEM_RELATIVE_PATH = "DEM_GEO8_TIFS/DEM_640.tif"
# (logical_name, relative_path); DEM first so it can drive the diagnostic.
END_TO_END_ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("DEM_640", "DEM_GEO8_TIFS/DEM_640.tif"),
    ("curv_laplacian_640", "DEM_GEO8_TIFS/curv_laplacian_640.tif"),
    ("curv_plan_640", "DEM_GEO8_TIFS/curv_plan_640.tif"),
    ("curv_profile_640", "DEM_GEO8_TIFS/curv_profile_640.tif"),
)

STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_INCOMPLETE = "incomplete"
STATUS_REFERENCE_INVALID = "reference_bundle_invalid"
STATUS_UNAVAILABLE = "comparison_unavailable"

ART_PASSED = "passed"
ART_INTERIOR_MISMATCH = "interior_mismatch"
ART_EDGE_ONLY_MISMATCH = "edge_or_nodata_only_mismatch"
ART_MISSING_APP = "missing_app_output"
ART_MISSING_REFERENCE = "missing_reference_output"
ART_SHAPE_MISMATCH = "shape_mismatch"


@dataclass(frozen=True)
class EndToEndArtifactResult:
    logical_name: str
    relative_path: str
    status: str
    app_present: bool
    reference_present: bool
    shape_match: bool | None = None
    dtype_match: bool | None = None
    nodata_match: bool | None = None
    finite_compared_count: int = 0
    max_abs_diff: float | None = None
    mean_abs_diff: float | None = None
    allclose: bool = False
    interior_compared_count: int = 0
    interior_max_abs_diff: float | None = None
    interior_mean_abs_diff: float | None = None
    interior_allclose: bool = False
    edge_nodata_compared_count: int = 0
    edge_nodata_max_abs_diff: float | None = None
    app_dtype: str = ""
    reference_dtype: str = ""
    notes: str = ""

    @property
    def passed(self) -> bool:
        return self.status == ART_PASSED

    def safe_entry(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "pass": self.passed,
            "app_present": self.app_present,
            "reference_present": self.reference_present,
            "shape_match": self.shape_match,
            "max_abs_diff": self.max_abs_diff,
            "interior_max_abs_diff": self.interior_max_abs_diff,
            "interior_allclose": self.interior_allclose,
            "finite_compared_count": self.finite_compared_count,
            "interior_compared_count": self.interior_compared_count,
            "edge_nodata_compared_count": self.edge_nodata_compared_count,
        }

    def detailed_entry(self) -> dict[str, Any]:
        entry = self.safe_entry()
        entry.update(
            {
                "relative_path": self.relative_path,
                "dtype_match": self.dtype_match,
                "nodata_match": self.nodata_match,
                "mean_abs_diff": self.mean_abs_diff,
                "allclose": self.allclose,
                "interior_mean_abs_diff": self.interior_mean_abs_diff,
                "edge_nodata_max_abs_diff": self.edge_nodata_max_abs_diff,
                "app_dtype": self.app_dtype,
                "reference_dtype": self.reference_dtype,
                "notes": self.notes,
            }
        )
        return entry


@dataclass(frozen=True)
class EndToEndParityResult:
    status: str
    atol: float
    rtol: float
    nodata: float
    bundle_status: str
    dem_matches: bool | None = None
    diagnostic: str = ""
    pass_count: int = 0
    fail_count: int = 0
    artifacts: tuple[EndToEndArtifactResult, ...] = field(default_factory=tuple)
    error: str | None = None

    @property
    def is_passed(self) -> bool:
        return self.status == STATUS_PASSED

    def safe_summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "bundle_status": self.bundle_status,
            "dem_matches": self.dem_matches,
            "diagnostic": self.diagnostic,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "tolerance": {"atol": self.atol, "rtol": self.rtol},
            "nodata": self.nodata,
            "interior_max_abs_diff": {
                a.logical_name: a.interior_max_abs_diff for a in self.artifacts
            },
            "pass": {a.logical_name: a.passed for a in self.artifacts},
            "artifact_status": {a.logical_name: a.status for a in self.artifacts},
            "error": self.error,
        }

    def detailed_report(self) -> dict[str, Any]:
        report = self.safe_summary()
        report["artifacts"] = {a.logical_name: a.detailed_entry() for a in self.artifacts}
        return report


def compare_dem_curvature_end_to_end(
    app_output_dir: str | Path,
    reference_bundle_dir: str | Path,
    *,
    atol: float = DEFAULT_ATOL,
    rtol: float = DEFAULT_RTOL,
    nodata: float = DEFAULT_NODATA,
    raster_reader: RasterReader | None = None,
) -> EndToEndParityResult:
    app_root = Path(app_output_dir)
    reference_root = Path(reference_bundle_dir)
    reader = raster_reader or _read_raw_raster

    bundle_result = validate_reference_bundle(reference_root)
    if bundle_result.status != STATUS_VALID:
        return EndToEndParityResult(
            status=STATUS_REFERENCE_INVALID, atol=atol, rtol=rtol, nodata=nodata,
            bundle_status=bundle_result.status,
            error="Frozen reference bundle failed D2 validation; refusing to compare.",
        )

    try:
        artifacts = tuple(
            _compare_one(name, rel, app_root=app_root, reference_root=reference_root,
                         reader=reader, atol=atol, rtol=rtol, nodata=nodata)
            for name, rel in END_TO_END_ARTIFACTS
        )
    except RasterUnavailableError as exc:
        return EndToEndParityResult(
            status=STATUS_UNAVAILABLE, atol=atol, rtol=rtol, nodata=nodata,
            bundle_status=bundle_result.status, error=str(exc),
        )

    dem = next((a for a in artifacts if a.logical_name == "DEM_640"), None)
    dem_matches = dem.passed if dem is not None else None
    curv = [a for a in artifacts if a.logical_name != "DEM_640"]
    curv_ok = all(a.status in {ART_PASSED, ART_EDGE_ONLY_MISMATCH} for a in curv)

    diagnostic = _diagnostic(dem, curv_ok)

    pass_count = sum(1 for a in artifacts if a.passed)
    fail_count = sum(
        1 for a in artifacts if a.status in {ART_INTERIOR_MISMATCH, ART_SHAPE_MISMATCH}
    )
    missing = sum(
        1 for a in artifacts if a.status in {ART_MISSING_APP, ART_MISSING_REFERENCE}
    )

    if any(a.status in {ART_INTERIOR_MISMATCH, ART_SHAPE_MISMATCH} for a in artifacts):
        overall = STATUS_FAILED
    elif missing:
        overall = STATUS_INCOMPLETE
    elif artifacts and all(a.status in {ART_PASSED, ART_EDGE_ONLY_MISMATCH} for a in artifacts):
        overall = STATUS_PASSED
    else:
        overall = STATUS_INCOMPLETE

    return EndToEndParityResult(
        status=overall, atol=atol, rtol=rtol, nodata=nodata,
        bundle_status=bundle_result.status, dem_matches=dem_matches,
        diagnostic=diagnostic, pass_count=pass_count, fail_count=fail_count, artifacts=artifacts,
    )


def _diagnostic(dem: EndToEndArtifactResult | None, curv_ok: bool) -> str:
    if dem is None or not dem.reference_present or not dem.app_present:
        return "DEM artifact missing on one side; cannot classify curvature differences."
    if dem.status in {ART_INTERIOR_MISMATCH, ART_SHAPE_MISMATCH}:
        return (
            "App DEM differs from reference DEM -> classify curvature differences as "
            "upstream DEM/grid/source mismatch until proven otherwise."
        )
    if dem.passed or dem.status == ART_EDGE_ONLY_MISMATCH:
        if curv_ok:
            return "DEM and curvature match end-to-end; DEM curvature parity accepted."
        return (
            "App DEM matches but curvature differs -> unexpected (D3B-1 passed); "
            "report as writer/path/integration issue, not a formula error."
        )
    return "Indeterminate DEM status."


def _compare_one(
    logical_name: str,
    rel: str,
    *,
    app_root: Path,
    reference_root: Path,
    reader: RasterReader,
    atol: float,
    rtol: float,
    nodata: float,
) -> EndToEndArtifactResult:
    app_path = app_root / rel
    ref_path = reference_root / rel
    app_present = app_path.is_file()
    ref_present = ref_path.is_file()
    base = dict(logical_name=logical_name, relative_path=rel,
                app_present=app_present, reference_present=ref_present)

    if not app_present:
        return EndToEndArtifactResult(status=ART_MISSING_APP,
                                      notes="App output is missing.", **base)
    if not ref_present:
        return EndToEndArtifactResult(status=ART_MISSING_REFERENCE,
                                      notes="Frozen reference output is missing.", **base)

    app = reader(app_path)
    ref = reader(ref_path)
    app_arr = np.asarray(app.values, dtype=np.float64)
    ref_arr = np.asarray(ref.values, dtype=np.float64)

    if app_arr.shape != ref_arr.shape:
        return EndToEndArtifactResult(
            status=ART_SHAPE_MISMATCH, shape_match=False,
            app_dtype=app.dtype, reference_dtype=ref.dtype,
            notes=f"Shape differs: app {app_arr.shape} vs reference {ref_arr.shape}.", **base,
        )

    app_nodata = app.nodata if app.nodata is not None else nodata
    ref_nodata = ref.nodata if ref.nodata is not None else nodata
    app_invalid = ~np.isfinite(app_arr) | (app_arr == app_nodata)
    ref_invalid = ~np.isfinite(ref_arr) | (ref_arr == ref_nodata)
    valid = ~(app_invalid | ref_invalid)

    edge = _edge_mask(app_arr.shape)
    total_count, total_max, total_mean, total_allclose = _diff_block(
        app_arr, ref_arr, valid, atol=atol, rtol=rtol)
    int_count, int_max, int_mean, int_allclose = _diff_block(
        app_arr, ref_arr, valid & ~edge, atol=atol, rtol=rtol)
    edge_count, edge_max, _m, _a = _diff_block(
        app_arr, ref_arr, valid & edge, atol=atol, rtol=rtol)

    if not int_allclose:
        status, notes = ART_INTERIOR_MISMATCH, "Interior differs beyond tolerance."
    elif not total_allclose:
        status, notes = ART_EDGE_ONLY_MISMATCH, "Interior matches; differences confined to edge/nodata."
    else:
        status, notes = ART_PASSED, "App and reference match within tolerance (interior + edge)."

    return EndToEndArtifactResult(
        status=status, shape_match=True,
        dtype_match=app.dtype == ref.dtype,
        nodata_match=(app_nodata == ref_nodata),
        finite_compared_count=total_count, max_abs_diff=total_max, mean_abs_diff=total_mean,
        allclose=total_allclose,
        interior_compared_count=int_count, interior_max_abs_diff=int_max,
        interior_mean_abs_diff=int_mean, interior_allclose=int_allclose,
        edge_nodata_compared_count=edge_count, edge_nodata_max_abs_diff=edge_max,
        app_dtype=app.dtype, reference_dtype=ref.dtype, notes=notes, **base,
    )
