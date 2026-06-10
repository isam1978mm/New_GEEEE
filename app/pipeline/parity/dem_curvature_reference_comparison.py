"""D3 — DEM curvature reference comparison against the frozen D1 bundle.

This module compares the app's existing DEM curvature rasters against a frozen
``notebooks/new.ipynb`` D1 reference bundle. It is comparison/verification only:
it does not regenerate notebook outputs, change curvature formulas, call Earth
Engine, or serve any artifact.

Gating: the frozen reference bundle MUST pass the D2 bundle/file validator
(:func:`app.services.reference_bundle_validator.validate_reference_bundle`)
before any raster comparison runs. If the bundle is invalid the comparison is
refused.

Safety: the default machine-readable result (``safe_summary``) is counts-only
plus per-logical-artifact diff magnitudes and pass/fail. It never echoes raw,
potentially coordinate-bearing filesystem paths. Detailed per-file findings
(including relative paths) are surfaced only via the explicit, local-only
``detailed_report``.

Raster reading is injectable. The default backend uses ``rasterio`` when it is
importable; when it is not, the comparison degrades to ``comparison_unavailable``
rather than failing. Tests inject a lightweight numpy-backed reader so the
comparison logic can be exercised without GDAL/rasterio installed.
"""

from __future__ import annotations

import importlib.util
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

from app.services.reference_bundle_validator import (
    STATUS_VALID,
    validate_reference_bundle,
)

# Logical curvature artifacts compared by D3. The relative path is identical on
# the app-output side and the frozen reference side. The notebook writes these
# under DEM_GEO8_TIFS/ via save_tif(name) -> DEM_GEO8_TIFS/{name}_640.tif.
CURVATURE_ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("curv_laplacian_640", "DEM_GEO8_TIFS/curv_laplacian_640.tif"),
    ("curv_plan_640", "DEM_GEO8_TIFS/curv_plan_640.tif"),
    ("curv_profile_640", "DEM_GEO8_TIFS/curv_profile_640.tif"),
)

DEFAULT_ATOL = 1e-6
DEFAULT_RTOL = 1e-6

# Per-artifact statuses.
ARTIFACT_PASSED = "passed"
ARTIFACT_MISSING_APP = "missing_app_output"
ARTIFACT_MISSING_REFERENCE = "missing_reference_output"
ARTIFACT_SHAPE_MISMATCH = "shape_mismatch"
ARTIFACT_METADATA_MISMATCH = "metadata_mismatch"
ARTIFACT_VALUE_MISMATCH = "value_mismatch"
ARTIFACT_UNAVAILABLE = "comparison_unavailable"
ARTIFACT_ERROR = "error"

# Overall statuses.
OVERALL_PASSED = "passed"
OVERALL_FAILED = "failed"
OVERALL_INCOMPLETE = "incomplete"
OVERALL_UNAVAILABLE = "comparison_unavailable"
OVERALL_REFERENCE_INVALID = "reference_bundle_invalid"


class RasterUnavailableError(RuntimeError):
    """Raised by a raster reader when no raster backend is importable."""


@dataclass(frozen=True)
class RasterData:
    """A minimal, backend-agnostic raster view used by the comparison."""

    values: np.ndarray  # float64, nodata/masked entries set to NaN
    shape: tuple[int, ...]
    dtype: str
    band_count: int
    crs: str | None = None
    transform: tuple[float, ...] | None = None
    nodata: float | None = None

    @property
    def finite_count(self) -> int:
        return int(np.count_nonzero(np.isfinite(self.values)))


RasterReader = Callable[[Path], RasterData]


@dataclass(frozen=True)
class CurvatureArtifactResult:
    logical_name: str
    filename: str
    status: str
    app_present: bool
    reference_present: bool
    shape_match: bool | None = None
    dtype_match: bool | None = None
    crs_match: bool | None = None
    transform_match: bool | None = None
    nodata_match: bool | None = None
    max_abs_diff: float | None = None
    mean_abs_diff: float | None = None
    finite_pixel_count: int = 0
    compared_pixel_count: int = 0
    within_tolerance: bool = False
    app_relative_path: str = ""
    reference_relative_path: str = ""
    notes: str = ""

    @property
    def passed(self) -> bool:
        return self.status == ARTIFACT_PASSED

    def safe_entry(self) -> dict[str, Any]:
        """Counts/diff-only entry. Never includes filesystem paths."""

        return {
            "status": self.status,
            "pass": self.passed,
            "app_present": self.app_present,
            "reference_present": self.reference_present,
            "shape_match": self.shape_match,
            "max_abs_diff": self.max_abs_diff,
            "finite_pixel_count": self.finite_pixel_count,
            "compared_pixel_count": self.compared_pixel_count,
        }

    def detailed_entry(self) -> dict[str, Any]:
        entry = self.safe_entry()
        entry.update(
            {
                "filename": self.filename,
                "dtype_match": self.dtype_match,
                "crs_match": self.crs_match,
                "transform_match": self.transform_match,
                "nodata_match": self.nodata_match,
                "mean_abs_diff": self.mean_abs_diff,
                "within_tolerance": self.within_tolerance,
                "app_relative_path": self.app_relative_path,
                "reference_relative_path": self.reference_relative_path,
                "notes": self.notes,
            }
        )
        return entry


@dataclass(frozen=True)
class CurvatureComparisonResult:
    status: str
    atol: float
    rtol: float
    bundle_status: str
    compared_count: int = 0
    missing_count: int = 0
    shape_mismatch_count: int = 0
    pass_count: int = 0
    fail_count: int = 0
    artifacts: tuple[CurvatureArtifactResult, ...] = field(default_factory=tuple)
    error: str | None = None

    @property
    def is_passed(self) -> bool:
        return self.status == OVERALL_PASSED

    def safe_summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "bundle_status": self.bundle_status,
            "compared_count": self.compared_count,
            "missing_count": self.missing_count,
            "shape_mismatch_count": self.shape_mismatch_count,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "tolerance": {"atol": self.atol, "rtol": self.rtol},
            "max_abs_diff": {
                a.logical_name: a.max_abs_diff for a in self.artifacts
            },
            "pass": {a.logical_name: a.passed for a in self.artifacts},
            "artifact_status": {
                a.logical_name: a.status for a in self.artifacts
            },
            "error": self.error,
        }

    def detailed_report(self) -> dict[str, Any]:
        report = self.safe_summary()
        report["artifacts"] = {
            a.logical_name: a.detailed_entry() for a in self.artifacts
        }
        return report


# ---------------------------------------------------------------------------
# Raster readers
# ---------------------------------------------------------------------------
def _rasterio_available() -> bool:
    return importlib.util.find_spec("rasterio") is not None


def rasterio_raster_reader(path: Path) -> RasterData:
    """Default raster reader backed by ``rasterio``.

    Raises :class:`RasterUnavailableError` when rasterio is not importable so
    callers can degrade to ``comparison_unavailable`` instead of failing.
    """

    if not _rasterio_available():
        raise RasterUnavailableError("rasterio is not importable")

    import rasterio

    with rasterio.open(path) as dataset:
        masked = dataset.read(masked=True).astype("float64")
        values = np.asarray(np.ma.filled(masked, np.nan), dtype=np.float64)
        nodata = dataset.nodatavals[0] if dataset.nodatavals else None
        return RasterData(
            values=values,
            shape=tuple(int(v) for v in values.shape),
            dtype=str(dataset.dtypes[0]) if dataset.dtypes else "",
            band_count=int(dataset.count),
            crs=str(dataset.crs) if dataset.crs is not None else None,
            transform=tuple(float(v) for v in dataset.transform),
            nodata=float(nodata) if nodata is not None else None,
        )


def _tifffile_available() -> bool:
    return importlib.util.find_spec("tifffile") is not None


# GDAL_NODATA GeoTIFF tag.
_GDAL_NODATA_TAG = 42113


def tifffile_raster_reader(path: Path) -> RasterData:
    """Fallback raster reader backed by ``tifffile`` (no GDAL/rasterio needed).

    Reads pixel values and the GDAL_NODATA tag. CRS/transform are left ``None``
    (treated as "not comparable" by the audit, never a forced failure). Raises
    :class:`RasterUnavailableError` when tifffile is not importable.
    """

    if not _tifffile_available():
        raise RasterUnavailableError("tifffile is not importable")

    import tifffile

    with tifffile.TiffFile(path) as handle:
        page = handle.pages[0]
        raw = np.asarray(page.asarray())
        dtype = str(raw.dtype)
        nodata: float | None = None
        tag = page.tags.get(_GDAL_NODATA_TAG)
        if tag is not None:
            try:
                nodata = float(str(tag.value).strip())
            except (TypeError, ValueError):
                nodata = None

    values = raw.astype(np.float64)
    if nodata is not None:
        values = np.where(values == nodata, np.nan, values)
    band_count = 1 if values.ndim == 2 else int(values.shape[0])
    return RasterData(
        values=values,
        shape=tuple(int(v) for v in values.shape),
        dtype=dtype,
        band_count=band_count,
        crs=None,
        transform=None,
        nodata=nodata,
    )


def default_raster_reader(path: Path) -> RasterData:
    """Read a raster using rasterio when available, else tifffile."""

    if _rasterio_available():
        return rasterio_raster_reader(path)
    if _tifffile_available():
        return tifffile_raster_reader(path)
    raise RasterUnavailableError("no raster backend (rasterio/tifffile) is importable")


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def compare_dem_curvature_references(
    app_output_dir: str | Path,
    reference_bundle_dir: str | Path,
    *,
    atol: float = DEFAULT_ATOL,
    rtol: float = DEFAULT_RTOL,
    allow_empty_reference_files: bool = False,
    raster_reader: RasterReader | None = None,
) -> CurvatureComparisonResult:
    """Compare app DEM curvature rasters against a frozen D1 reference bundle.

    The reference bundle must pass the D2 validator first; otherwise the
    comparison is refused with ``reference_bundle_invalid`` and no rasters are
    read.
    """

    app_root = Path(app_output_dir)
    reference_root = Path(reference_bundle_dir)
    reader = raster_reader or default_raster_reader

    bundle_result = validate_reference_bundle(
        reference_root, allow_empty_files=allow_empty_reference_files
    )
    if bundle_result.status != STATUS_VALID:
        return CurvatureComparisonResult(
            status=OVERALL_REFERENCE_INVALID,
            atol=atol,
            rtol=rtol,
            bundle_status=bundle_result.status,
            error=(
                "Frozen reference bundle failed D2 validation; "
                "refusing to compare."
            ),
        )

    artifacts = tuple(
        _compare_one(
            logical_name,
            filename,
            app_root=app_root,
            reference_root=reference_root,
            atol=atol,
            rtol=rtol,
            reader=reader,
        )
        for logical_name, filename in CURVATURE_ARTIFACTS
    )

    return _summarize(artifacts, atol=atol, rtol=rtol, bundle_status=bundle_result.status)


def _compare_one(
    logical_name: str,
    filename: str,
    *,
    app_root: Path,
    reference_root: Path,
    atol: float,
    rtol: float,
    reader: RasterReader,
) -> CurvatureArtifactResult:
    app_path = app_root / filename
    reference_path = reference_root / filename
    app_present = app_path.is_file()
    reference_present = reference_path.is_file()

    base = dict(
        logical_name=logical_name,
        filename=filename,
        app_present=app_present,
        reference_present=reference_present,
        app_relative_path=filename if app_present else "",
        reference_relative_path=filename if reference_present else "",
    )

    if not app_present:
        return CurvatureArtifactResult(
            status=ARTIFACT_MISSING_APP,
            notes="App curvature output is missing.",
            **base,
        )
    if not reference_present:
        return CurvatureArtifactResult(
            status=ARTIFACT_MISSING_REFERENCE,
            notes="Frozen reference curvature output is missing.",
            **base,
        )

    try:
        app_raster = reader(app_path)
        reference_raster = reader(reference_path)
    except RasterUnavailableError as exc:
        return CurvatureArtifactResult(
            status=ARTIFACT_UNAVAILABLE,
            notes=f"Raster comparison unavailable: {exc}",
            **base,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return CurvatureArtifactResult(
            status=ARTIFACT_ERROR,
            notes=f"Raster read failed: {type(exc).__name__}: {exc}",
            **base,
        )

    shape_match = app_raster.shape == reference_raster.shape
    if not shape_match:
        return CurvatureArtifactResult(
            status=ARTIFACT_SHAPE_MISMATCH,
            shape_match=False,
            finite_pixel_count=app_raster.finite_count,
            notes=(
                f"Shape differs: app {app_raster.shape} vs "
                f"reference {reference_raster.shape}."
            ),
            **base,
        )

    dtype_match = app_raster.dtype == reference_raster.dtype
    crs_match = _optional_match(app_raster.crs, reference_raster.crs)
    transform_match = _optional_match(app_raster.transform, reference_raster.transform)
    nodata_match = _nodata_match(app_raster.nodata, reference_raster.nodata)

    diff = _diff_stats(app_raster.values, reference_raster.values, atol=atol, rtol=rtol)

    metadata_ok = dtype_match and (crs_match is not False) and (
        transform_match is not False
    ) and (nodata_match is not False)

    common = dict(
        shape_match=True,
        dtype_match=dtype_match,
        crs_match=crs_match,
        transform_match=transform_match,
        nodata_match=nodata_match,
        max_abs_diff=diff["max_abs_diff"],
        mean_abs_diff=diff["mean_abs_diff"],
        finite_pixel_count=app_raster.finite_count,
        compared_pixel_count=diff["compared_pixel_count"],
        within_tolerance=diff["within_tolerance"],
        **base,
    )

    if not metadata_ok:
        return CurvatureArtifactResult(
            status=ARTIFACT_METADATA_MISMATCH,
            notes="Raster metadata (dtype/crs/transform/nodata) did not match.",
            **common,
        )
    if not diff["within_tolerance"]:
        return CurvatureArtifactResult(
            status=ARTIFACT_VALUE_MISMATCH,
            notes="Raster values differ outside tolerance.",
            **common,
        )
    return CurvatureArtifactResult(
        status=ARTIFACT_PASSED,
        notes="App and reference curvature match within tolerance.",
        **common,
    )


def _optional_match(app_value: Any, reference_value: Any) -> bool | None:
    """Compare metadata that may be unavailable on either side.

    Returns ``None`` ("not comparable") when either side is missing, so a
    missing CRS/transform never forces a failure.
    """

    if app_value is None or reference_value is None:
        return None
    return app_value == reference_value


def _nodata_match(app_nodata: float | None, reference_nodata: float | None) -> bool:
    if app_nodata is None and reference_nodata is None:
        return True
    if app_nodata is None or reference_nodata is None:
        return False
    if math.isnan(app_nodata) and math.isnan(reference_nodata):
        return True
    return app_nodata == reference_nodata


def _diff_stats(
    app_values: np.ndarray,
    reference_values: np.ndarray,
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    app = np.asarray(app_values, dtype=np.float64)
    reference = np.asarray(reference_values, dtype=np.float64)
    valid = np.isfinite(app) & np.isfinite(reference)
    compared = int(np.count_nonzero(valid))
    if compared == 0:
        return {
            "max_abs_diff": None,
            "mean_abs_diff": None,
            "compared_pixel_count": 0,
            "within_tolerance": False,
        }
    app_valid = app[valid]
    reference_valid = reference[valid]
    abs_diff = np.abs(app_valid - reference_valid)
    return {
        "max_abs_diff": float(np.max(abs_diff)),
        "mean_abs_diff": float(np.mean(abs_diff)),
        "compared_pixel_count": compared,
        "within_tolerance": bool(
            np.allclose(app_valid, reference_valid, atol=atol, rtol=rtol, equal_nan=True)
        ),
    }


def _summarize(
    artifacts: tuple[CurvatureArtifactResult, ...],
    *,
    atol: float,
    rtol: float,
    bundle_status: str,
) -> CurvatureComparisonResult:
    statuses = [a.status for a in artifacts]
    compared = sum(
        1
        for a in artifacts
        if a.status
        in {ARTIFACT_PASSED, ARTIFACT_VALUE_MISMATCH, ARTIFACT_METADATA_MISMATCH}
    )
    missing = sum(
        1
        for s in statuses
        if s in {ARTIFACT_MISSING_APP, ARTIFACT_MISSING_REFERENCE}
    )
    shape_mismatch = sum(1 for s in statuses if s == ARTIFACT_SHAPE_MISMATCH)
    pass_count = sum(1 for a in artifacts if a.passed)
    fail_statuses = {
        ARTIFACT_SHAPE_MISMATCH,
        ARTIFACT_METADATA_MISMATCH,
        ARTIFACT_VALUE_MISMATCH,
        ARTIFACT_ERROR,
    }
    fail_count = sum(1 for s in statuses if s in fail_statuses)

    if any(s == ARTIFACT_UNAVAILABLE for s in statuses):
        overall = OVERALL_UNAVAILABLE
    elif any(s in fail_statuses for s in statuses):
        overall = OVERALL_FAILED
    elif missing:
        overall = OVERALL_INCOMPLETE
    elif statuses and all(s == ARTIFACT_PASSED for s in statuses):
        overall = OVERALL_PASSED
    else:
        overall = OVERALL_INCOMPLETE

    return CurvatureComparisonResult(
        status=overall,
        atol=atol,
        rtol=rtol,
        bundle_status=bundle_status,
        compared_count=compared,
        missing_count=missing,
        shape_mismatch_count=shape_mismatch,
        pass_count=pass_count,
        fail_count=fail_count,
        artifacts=artifacts,
    )
