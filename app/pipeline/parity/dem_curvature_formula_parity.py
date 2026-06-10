"""D3B-1 — DEM curvature formula-isolation parity.

This isolates the app's DEM *curvature formulas* from upstream DEM generation.
It feeds the app's existing :func:`compute_dem_derivatives` the frozen D1C
reference DEM (``DEM_GEO8_TIFS/DEM_640.tif``) and compares the app-computed
curvature rasters directly against the D1C reference curvature rasters:

  * ``DEM_GEO8_TIFS/curv_laplacian_640.tif``
  * ``DEM_GEO8_TIFS/curv_plan_640.tif``
  * ``DEM_GEO8_TIFS/curv_profile_640.tif``

Because both sides use the same DEM input, any interior difference is a genuine
formula-parity finding. Edge/nodata-only differences (np.gradient one-sided
boundaries, masked cells) are reported separately and never hidden.

It is local-only and read-only with respect to the bundle. It does NOT change
DEM formulas, regenerate the DEM, run Earth Engine, modify the notebook, or
commit any raster. Generated curvature rasters are written to a caller-supplied
temp directory (outside the repo) only if requested; by default nothing is
written — the comparison runs in memory.

Gating: the frozen reference bundle MUST pass the D2 validator first.
"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

from app.pipeline.stages.dem_derivatives import compute_dem_derivatives
from app.services.reference_bundle_validator import (
    STATUS_VALID,
    validate_reference_bundle,
)

# Declared project tolerance (matches dem_curv_laplacian_verify defaults).
DEFAULT_ATOL = 1e-6
DEFAULT_RTOL = 1e-6

# Notebook DEM grid: save_tif writes float32; RUN_MANIFEST SCALE = 10 m.
DEFAULT_SCALE_M = 10.0
DEFAULT_NODATA = -9999.0

REFERENCE_DEM_PATH = "DEM_GEO8_TIFS/DEM_640.tif"
# logical name -> (app compute_dem_derivatives key, reference relative path)
CURVATURE_TARGETS: tuple[tuple[str, str, str], ...] = (
    ("curv_laplacian_640", "curv_laplacian", "DEM_GEO8_TIFS/curv_laplacian_640.tif"),
    ("curv_plan_640", "curv_plan", "DEM_GEO8_TIFS/curv_plan_640.tif"),
    ("curv_profile_640", "curv_profile", "DEM_GEO8_TIFS/curv_profile_640.tif"),
)

STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_INCOMPLETE = "incomplete"
STATUS_REFERENCE_INVALID = "reference_bundle_invalid"
STATUS_UNAVAILABLE = "comparison_unavailable"
STATUS_MISSING_DEM = "missing_reference_dem"

ART_PASSED = "passed"
ART_INTERIOR_MISMATCH = "interior_mismatch"
ART_EDGE_ONLY_MISMATCH = "edge_or_nodata_only_mismatch"
ART_MISSING_REFERENCE = "missing_reference_output"
ART_SHAPE_MISMATCH = "shape_mismatch"


class RasterUnavailableError(RuntimeError):
    """Raised when no raster backend (rasterio/tifffile) is importable."""


@dataclass(frozen=True)
class RawRaster:
    values: np.ndarray  # float64, nodata sentinel preserved
    dtype: str
    nodata: float | None


def _read_raw_raster(path: Path) -> RawRaster:
    """Read a single-band raster's raw values + nodata, preferring rasterio."""

    if importlib.util.find_spec("rasterio") is not None:
        import rasterio

        with rasterio.open(path) as dataset:
            arr = dataset.read(1).astype(np.float64)
            nodata = dataset.nodatavals[0] if dataset.nodatavals else None
            return RawRaster(arr, str(dataset.dtypes[0]), float(nodata) if nodata is not None else None)

    if importlib.util.find_spec("tifffile") is not None:
        import tifffile

        with tifffile.TiffFile(path) as handle:
            page = handle.pages[0]
            arr = np.asarray(page.asarray())
            nodata = None
            tag = page.tags.get(42113)  # GDAL_NODATA
            if tag is not None:
                try:
                    nodata = float(str(tag.value).strip())
                except (TypeError, ValueError):
                    nodata = None
            return RawRaster(arr.astype(np.float64), str(arr.dtype), nodata)

    raise RasterUnavailableError("no raster backend (rasterio/tifffile) is importable")


RasterReader = Callable[[Path], RawRaster]


@dataclass(frozen=True)
class CurvatureFormulaArtifactResult:
    logical_name: str
    reference_relative_path: str
    status: str
    reference_present: bool
    shape_match: bool | None = None
    dtype_match: bool | None = None
    nodata_match: bool | None = None
    finite_compared_count: int = 0
    max_abs_diff: float | None = None
    mean_abs_diff: float | None = None
    allclose: bool = False
    # interior vs edge/nodata classification
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
                "reference_relative_path": self.reference_relative_path,
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
class CurvatureFormulaParityResult:
    status: str
    atol: float
    rtol: float
    scale_m: float
    nodata: float
    bundle_status: str
    pass_count: int = 0
    fail_count: int = 0
    artifacts: tuple[CurvatureFormulaArtifactResult, ...] = field(default_factory=tuple)
    error: str | None = None

    @property
    def is_passed(self) -> bool:
        return self.status == STATUS_PASSED

    def safe_summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "bundle_status": self.bundle_status,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "tolerance": {"atol": self.atol, "rtol": self.rtol},
            "scale_m": self.scale_m,
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


def _edge_mask(shape: tuple[int, int]) -> np.ndarray:
    """True on the 1-pixel border, where np.gradient uses one-sided diffs."""

    mask = np.zeros(shape, dtype=bool)
    mask[0, :] = True
    mask[-1, :] = True
    mask[:, 0] = True
    mask[:, -1] = True
    return mask


def _diff_block(app: np.ndarray, ref: np.ndarray, sel: np.ndarray, *, atol: float, rtol: float):
    count = int(np.count_nonzero(sel))
    if count == 0:
        return count, None, None, True
    a = app[sel]
    b = ref[sel]
    abs_diff = np.abs(a - b)
    return (
        count,
        float(np.max(abs_diff)),
        float(np.mean(abs_diff)),
        bool(np.allclose(a, b, atol=atol, rtol=rtol, equal_nan=True)),
    )


def compare_dem_curvature_formula_parity(
    reference_bundle_dir: str | Path,
    *,
    atol: float = DEFAULT_ATOL,
    rtol: float = DEFAULT_RTOL,
    scale_m: float | None = None,
    nodata: float = DEFAULT_NODATA,
    raster_reader: RasterReader | None = None,
    write_outputs_dir: str | Path | None = None,
) -> CurvatureFormulaParityResult:
    """Run the app curvature formulas on the frozen DEM and compare to reference."""

    reference_root = Path(reference_bundle_dir)
    reader = raster_reader or _read_raw_raster
    used_scale = float(scale_m) if scale_m is not None else _scale_from_bundle(reference_root)

    bundle_result = validate_reference_bundle(reference_root)
    if bundle_result.status != STATUS_VALID:
        return CurvatureFormulaParityResult(
            status=STATUS_REFERENCE_INVALID,
            atol=atol,
            rtol=rtol,
            scale_m=used_scale,
            nodata=nodata,
            bundle_status=bundle_result.status,
            error="Frozen reference bundle failed D2 validation; refusing to compare.",
        )

    dem_path = reference_root / REFERENCE_DEM_PATH
    if not dem_path.is_file():
        return CurvatureFormulaParityResult(
            status=STATUS_MISSING_DEM,
            atol=atol,
            rtol=rtol,
            scale_m=used_scale,
            nodata=nodata,
            bundle_status=bundle_result.status,
            error=f"Reference DEM {REFERENCE_DEM_PATH} is missing from the bundle.",
        )

    try:
        dem_raster = reader(dem_path)
        app_outputs = compute_dem_derivatives(
            dem_raster.values, nodata=nodata, scale_m=used_scale
        )
    except RasterUnavailableError as exc:
        return CurvatureFormulaParityResult(
            status=STATUS_UNAVAILABLE,
            atol=atol,
            rtol=rtol,
            scale_m=used_scale,
            nodata=nodata,
            bundle_status=bundle_result.status,
            error=str(exc),
        )

    if write_outputs_dir is not None:
        _write_outputs(Path(write_outputs_dir), app_outputs)

    artifacts = tuple(
        _compare_one(
            logical_name,
            app_key,
            ref_rel,
            app_outputs=app_outputs,
            reference_root=reference_root,
            reader=reader,
            atol=atol,
            rtol=rtol,
            nodata=nodata,
        )
        for logical_name, app_key, ref_rel in CURVATURE_TARGETS
    )

    pass_count = sum(1 for a in artifacts if a.passed)
    fail_count = sum(
        1 for a in artifacts if a.status in {ART_INTERIOR_MISMATCH, ART_SHAPE_MISMATCH}
    )
    missing = sum(1 for a in artifacts if a.status == ART_MISSING_REFERENCE)

    if any(a.status == ART_SHAPE_MISMATCH or a.status == ART_INTERIOR_MISMATCH for a in artifacts):
        overall = STATUS_FAILED
    elif missing:
        overall = STATUS_INCOMPLETE
    elif all(a.status in {ART_PASSED, ART_EDGE_ONLY_MISMATCH} for a in artifacts) and artifacts:
        overall = STATUS_PASSED
    else:
        overall = STATUS_INCOMPLETE

    return CurvatureFormulaParityResult(
        status=overall,
        atol=atol,
        rtol=rtol,
        scale_m=used_scale,
        nodata=nodata,
        bundle_status=bundle_result.status,
        pass_count=pass_count,
        fail_count=fail_count,
        artifacts=artifacts,
    )


def _compare_one(
    logical_name: str,
    app_key: str,
    ref_rel: str,
    *,
    app_outputs: dict[str, np.ndarray],
    reference_root: Path,
    reader: RasterReader,
    atol: float,
    rtol: float,
    nodata: float,
) -> CurvatureFormulaArtifactResult:
    ref_path = reference_root / ref_rel
    base = dict(logical_name=logical_name, reference_relative_path=ref_rel)
    if not ref_path.is_file():
        return CurvatureFormulaArtifactResult(
            status=ART_MISSING_REFERENCE, reference_present=False,
            notes="Frozen reference curvature output is missing.", **base,
        )

    ref = reader(ref_path)
    app_arr = np.asarray(app_outputs[app_key], dtype=np.float64)
    ref_arr = np.asarray(ref.values, dtype=np.float64)
    app_dtype = str(np.asarray(app_outputs[app_key]).dtype)

    if app_arr.shape != ref_arr.shape:
        return CurvatureFormulaArtifactResult(
            status=ART_SHAPE_MISMATCH, reference_present=True, shape_match=False,
            app_dtype=app_dtype, reference_dtype=ref.dtype,
            notes=f"Shape differs: app {app_arr.shape} vs reference {ref_arr.shape}.",
            **base,
        )

    # Treat the app's nodata fill and the reference nodata as invalid; compare
    # only jointly-finite, non-nodata pixels.
    app_invalid = ~np.isfinite(app_arr) | (app_arr == nodata)
    ref_nodata = ref.nodata if ref.nodata is not None else nodata
    ref_invalid = ~np.isfinite(ref_arr) | (ref_arr == ref_nodata)
    valid = ~(app_invalid | ref_invalid)

    edge = _edge_mask(app_arr.shape)
    interior_sel = valid & ~edge
    edge_sel = valid & edge

    total_count, total_max, total_mean, total_allclose = _diff_block(
        app_arr, ref_arr, valid, atol=atol, rtol=rtol
    )
    int_count, int_max, int_mean, int_allclose = _diff_block(
        app_arr, ref_arr, interior_sel, atol=atol, rtol=rtol
    )
    edge_count, edge_max, _edge_mean, _edge_allclose = _diff_block(
        app_arr, ref_arr, edge_sel, atol=atol, rtol=rtol
    )

    dtype_match = app_dtype == ref.dtype
    nodata_match = ref.nodata is None or ref.nodata == nodata

    if not int_allclose:
        status = ART_INTERIOR_MISMATCH
        notes = (
            "Interior curvature differs beyond tolerance — genuine formula-parity finding. "
            "Reconcile against notebook formulas; do not alias or relax tolerance."
        )
    elif not total_allclose:
        status = ART_EDGE_ONLY_MISMATCH
        notes = "Interior matches; differences confined to edge/nodata pixels (reported, not hidden)."
    else:
        status = ART_PASSED
        notes = "App curvature formula matches reference within tolerance (interior + edge)."

    return CurvatureFormulaArtifactResult(
        status=status,
        reference_present=True,
        shape_match=True,
        dtype_match=dtype_match,
        nodata_match=nodata_match,
        finite_compared_count=total_count,
        max_abs_diff=total_max,
        mean_abs_diff=total_mean,
        allclose=total_allclose,
        interior_compared_count=int_count,
        interior_max_abs_diff=int_max,
        interior_mean_abs_diff=int_mean,
        interior_allclose=int_allclose,
        edge_nodata_compared_count=edge_count,
        edge_nodata_max_abs_diff=edge_max,
        app_dtype=app_dtype,
        reference_dtype=ref.dtype,
        notes=notes,
        **base,
    )


def _scale_from_bundle(reference_root: Path) -> float:
    """Read SCALE from the bundle RUN_MANIFEST if present, else default."""

    for candidate in (
        reference_root / "QA" / "RUN_MANIFEST.json",
        reference_root / "RUN_MANIFEST.json",
    ):
        if candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                scale = data.get("SCALE")
                if isinstance(scale, (int, float)) and scale > 0:
                    return float(scale)
            except (OSError, ValueError):
                pass
    return DEFAULT_SCALE_M


def _write_outputs(out_dir: Path, app_outputs: dict[str, np.ndarray]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for _logical, app_key, ref_rel in CURVATURE_TARGETS:
        np.save(out_dir / (Path(ref_rel).stem + ".npy"), np.asarray(app_outputs[app_key]))
