from __future__ import annotations

import csv
import fnmatch
import json
import math
import warnings
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import numpy as np
import rasterio
from rasterio.errors import NotGeoreferencedWarning, RasterioIOError

NUMERIC_PARITY_REPORT_PREFIX = "numeric_parity"
DEFAULT_ABS_TOL = 1e-5
DEFAULT_REL_TOL = 1e-5
KMZ_COORD_PRECISION = 6
JSON_NUMERIC_PRECISION = 8
CSV_FLOAT_PRECISION = 8
NOTEBOOK_FOCUS_MASK_PATTERN = "QA/FOCUS_" "MASK_17m_inside_640.tif"
UNSTABLE_KEY_PARTS = (
    "timestamp",
    "created_at",
    "updated_at",
    "captured_at",
    "run_id",
    "sha",
    "hash",
    "checksum",
    "fingerprint",
    "path",
    "drive",
)
STABLE_SORT_KEYS = ("object_id", "cluster_id", "band_name", "name", "id")
REPORT_FIELDNAMES = [
    "family",
    "notebook_file",
    "app_file",
    "comparison_type",
    "status",
    "shape_match",
    "crs_match",
    "transform_match",
    "dtype_match",
    "exact_equal",
    "max_abs_diff",
    "mean_abs_diff",
    "differing_count",
    "matching_percent",
    "tolerance_used",
    "skipped_reason",
    "notes",
]


@dataclass(frozen=True, slots=True)
class RasterSnapshot:
    crs: str | None
    transform: tuple[float, ...] | None
    width: int
    height: int
    count: int
    nodata: float | None
    dtypes: tuple[str, ...]
    array: np.ndarray
    missing_metadata: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Tolerance:
    abs_tol: float = DEFAULT_ABS_TOL
    rel_tol: float = DEFAULT_REL_TOL

    def as_dict(self) -> dict[str, float]:
        return {"abs_tol": self.abs_tol, "rel_tol": self.rel_tol}


@dataclass(frozen=True, slots=True)
class ComparisonSpec:
    family: str
    comparison_type: str
    app_file: str
    notebook_candidates: tuple[str, ...]
    tolerance: Tolerance = Tolerance()
    notes: str = ""


@dataclass(frozen=True, slots=True)
class ComparisonRow:
    family: str
    notebook_file: str | None
    app_file: str | None
    comparison_type: str
    status: str
    shape_match: bool | None = None
    crs_match: bool | None = None
    transform_match: bool | None = None
    dtype_match: bool | None = None
    exact_equal: bool | None = None
    max_abs_diff: float | None = None
    mean_abs_diff: float | None = None
    differing_count: int | None = None
    matching_percent: float | None = None
    tolerance_used: dict[str, float] | None = None
    skipped_reason: str | None = None
    notes: str = ""

    def to_report_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["notebook_file"] = self.notebook_file or ""
        payload["app_file"] = self.app_file or ""
        payload["tolerance_used"] = self.tolerance_used or {}
        return payload

    def to_csv_dict(self) -> dict[str, str]:
        payload = self.to_report_dict()
        payload["shape_match"] = _stringify_bool(self.shape_match)
        payload["crs_match"] = _stringify_bool(self.crs_match)
        payload["transform_match"] = _stringify_bool(self.transform_match)
        payload["dtype_match"] = _stringify_bool(self.dtype_match)
        payload["exact_equal"] = _stringify_bool(self.exact_equal)
        payload["max_abs_diff"] = _stringify_number(self.max_abs_diff)
        payload["mean_abs_diff"] = _stringify_number(self.mean_abs_diff)
        payload["differing_count"] = "" if self.differing_count is None else str(self.differing_count)
        payload["matching_percent"] = _stringify_number(self.matching_percent)
        payload["tolerance_used"] = json.dumps(payload["tolerance_used"], sort_keys=True) if payload["tolerance_used"] else ""
        payload["skipped_reason"] = self.skipped_reason or ""
        return {field: payload.get(field, "") for field in REPORT_FIELDNAMES}


def build_default_comparison_specs() -> tuple[ComparisonSpec, ...]:
    specs: list[ComparisonSpec] = [
        ComparisonSpec("run_grid_manifest", "json", "grid_manifest.json", ("grid_manifest.json",)),
        ComparisonSpec("dem_core", "raster", "dem.tif", ("dem.tif", "DEM_GEO8_TIFS/DEM_640.tif")),
        ComparisonSpec("dem_core", "npy", "dem.npy", ("dem.npy",)),
    ]
    for name in ("VV_dB", "VH_dB", "logRatio_dB", "incidence"):
        notebook_candidates = {
            "VV_dB": ("VV_dB.tif", "GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640*.tif"),
            "VH_dB": ("VH_dB.tif", "GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640*.tif"),
            "logRatio_dB": ("logRatio_dB.tif", "GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640*.tif"),
            "incidence": ("incidence.tif", "GEOTIFF_RADAR_BANDS/RADAR_angle_640*.tif"),
        }[name]
        specs.append(
            ComparisonSpec(
                "sar_geotiff_bands",
                "raster",
                f"{name}.tif",
                notebook_candidates,
                tolerance=Tolerance(abs_tol=1e-4, rel_tol=1e-5),
            )
        )
    specs.extend(
        (
            ComparisonSpec(
                "sar_npy_bands",
                "npy",
                "npy_radar_bands/VV_dB.npy",
                ("npy_radar_bands/VV_dB.npy", "NPY_RADAR_BANDS/RADAR_VV_dB_640*.npy", "NPY_RADAR_BANDS/*VV*.npy"),
                tolerance=Tolerance(abs_tol=1e-4, rel_tol=1e-5),
            ),
            ComparisonSpec(
                "sar_npy_bands",
                "npy",
                "npy_radar_bands/VH_dB.npy",
                ("npy_radar_bands/VH_dB.npy", "NPY_RADAR_BANDS/RADAR_VH_dB_640*.npy", "NPY_RADAR_BANDS/*VH*.npy"),
                tolerance=Tolerance(abs_tol=1e-4, rel_tol=1e-5),
            ),
            ComparisonSpec(
                "sar_npy_bands",
                "npy",
                "npy_radar_bands/logRatio_dB.npy",
                ("npy_radar_bands/logRatio_dB.npy", "NPY_RADAR_BANDS/RADAR_logRatio_dB_640*.npy", "NPY_RADAR_BANDS/*logRatio*.npy"),
                tolerance=Tolerance(abs_tol=1e-4, rel_tol=1e-5),
            ),
            ComparisonSpec(
                "sar_npy_bands",
                "npy",
                "npy_radar_bands/incidence.npy",
                ("npy_radar_bands/incidence.npy", "NPY_RADAR_BANDS/RADAR_angle_640*.npy", "NPY_RADAR_BANDS/*angle*.npy", "NPY_RADAR_BANDS/*incidence*.npy"),
                tolerance=Tolerance(abs_tol=1e-4, rel_tol=1e-5),
            ),
        )
    )
    derivative_candidates = {
        "slope": ("slope.tif", "DEM_GEO8_TIFS/slope*_640.tif"),
        "aspect": ("aspect.tif", "DEM_GEO8_TIFS/aspect*_640.tif"),
        "curvature": ("curvature.tif", "DEM_GEO8_TIFS/curvature*_640.tif"),
        "TPI": ("TPI.tif", "DEM_GEO8_TIFS/tpi*_640.tif"),
        "TRI": ("TRI.tif", "DEM_GEO8_TIFS/tri*_640.tif"),
        "roughness": ("roughness.tif", "DEM_GEO8_TIFS/roughness*_640.tif"),
        "TWI": ("TWI.tif", "DEM_GEO8_TIFS/twi*_640.tif"),
    }
    for name in ("slope", "aspect", "curvature", "TPI", "TRI", "roughness", "TWI"):
        specs.append(
            ComparisonSpec(
                "dem_derivatives",
                "raster",
                f"{name}.tif",
                derivative_candidates[name],
                tolerance=Tolerance(abs_tol=1e-4, rel_tol=1e-5),
            )
        )
    specs.extend(
        (
            ComparisonSpec("radar_tensor_stack", "raster", "stacks/tensor_support/radar_linear_support_stack.tif", ("stacks/tensor_support/radar_linear_support_stack.tif",)),
            ComparisonSpec("radar_tensor_stack", "npy", "stacks/tensor_support/radar_linear_support_stack.npy", ("stacks/tensor_support/radar_linear_support_stack.npy", "NPY_STACKS/RADAR_STACK_HWC_640*.npy")),
            ComparisonSpec("radar_tensor_stack", "raster", "stacks/tensor_support/science_core_stack.tif", ("stacks/tensor_support/science_core_stack.tif",)),
            ComparisonSpec("radar_tensor_stack", "npy", "stacks/tensor_support/science_core_stack.npy", ("stacks/tensor_support/science_core_stack.npy",)),
            ComparisonSpec("radar_tensor_stack", "raster", "stacks/tensor_support/ai_ready_support_stack.tif", ("stacks/tensor_support/ai_ready_support_stack.tif",)),
            ComparisonSpec("radar_tensor_stack", "npy", "stacks/tensor_support/ai_ready_support_stack.npy", ("stacks/tensor_support/ai_ready_support_stack.npy",)),
        )
    )
    specs.extend(
        (
            ComparisonSpec("tesla_hypercube_family", "raster", "hypercube.tif", ("hypercube.tif", "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE*.tif")),
            ComparisonSpec("tesla_hypercube_family", "npy", "hypercube.npy", ("hypercube.npy",)),
            ComparisonSpec("tesla_hypercube_family", "csv", "hypercube_band_order.csv", ("hypercube_band_order.csv",), tolerance=Tolerance(abs_tol=0.0, rel_tol=0.0)),
            ComparisonSpec("tesla_hypercube_family", "csv", "hypercube_band_stats.csv", ("hypercube_band_stats.csv",), tolerance=Tolerance(abs_tol=1e-6, rel_tol=1e-6)),
            ComparisonSpec("tesla_hypercube_family", "csv", "hypercube_norm_params.csv", ("hypercube_norm_params.csv",), tolerance=Tolerance(abs_tol=1e-6, rel_tol=1e-6)),
        )
    )
    specs.extend(
        (
            ComparisonSpec("focus_zone_local", "raster", "full_job/focus/focus_zone_17m.tif", ("full_job/focus/focus_zone_17m.tif", NOTEBOOK_FOCUS_MASK_PATTERN, "*focus*17*.tif")),
            ComparisonSpec("focus_zone_local", "npy", "full_job/focus/focus_zone_17m.npy", ("full_job/focus/focus_zone_17m.npy", "*focus*17*.npy")),
            ComparisonSpec("focus_zone_local", "json", "full_job/focus/focus_zone_summary.json", ("full_job/focus/focus_zone_summary.json", "*focus*summary*.json")),
            ComparisonSpec("focus_zone_local", "csv", "full_job/focus/focus_zone_band_summary.csv", ("full_job/focus/focus_zone_band_summary.csv", "*focus*band*summary*.csv")),
        )
    )
    specs.extend(
        (
            ComparisonSpec("exact_location_geojson_kmz", "json", "full_job/location/site_location.geojson", ("full_job/location/site_location.geojson", "*location*.geojson", "*site*.geojson")),
            ComparisonSpec("exact_location_geojson_kmz", "kmz", "kmz/site_location.kmz", ("kmz/site_location.kmz", "*location*.kmz", "*site*.kmz"), notes="KMZ compares canonical KML content, not raw zip bytes."),
        )
    )
    specs.extend(
        (
            ComparisonSpec("final_intelligence_reports", "json", "full_job/field_ops/field_ops_report.json", ("full_job/field_ops/field_ops_report.json", "*field*ops*.json")),
            ComparisonSpec("final_intelligence_reports", "text", "full_job/field_ops/field_ops_brief.txt", ("full_job/field_ops/field_ops_brief.txt", "*field*ops*.txt")),
            ComparisonSpec("final_intelligence_reports", "json", "full_job/gps/gps_point_comparison.json", ("full_job/gps/gps_point_comparison.json", "*gps*comparison*.json")),
            ComparisonSpec("final_intelligence_reports", "csv", "full_job/gps/gps_point_comparison.csv", ("full_job/gps/gps_point_comparison.csv", "*gps*comparison*.csv")),
        )
    )
    specs.extend(
        (
            ComparisonSpec("sar_geotiff_bands", "csv", "qa/sar/sar_summary.csv", ("qa/sar/sar_summary.csv", "SUMMARY_RADAR*.csv")),
            ComparisonSpec("alignment_qa_summaries", "json", "alignment_qa.json", ("alignment_qa.json",), tolerance=Tolerance(abs_tol=1e-6, rel_tol=1e-6)),
            ComparisonSpec("alignment_qa_summaries", "json", "alignment_mask_selection.json", ("alignment_mask_selection.json", "*mask*selection*.json")),
            ComparisonSpec("alignment_qa_summaries", "csv", "alignment_audit.csv", ("alignment_audit.csv", "*alignment*audit*.csv")),
            ComparisonSpec("alignment_qa_summaries", "json", "qa/parity/parity_qa_summary.json", ("qa/parity/parity_qa_summary.json", "*parity*qa*summary*.json")),
        )
    )
    return tuple(specs)


def build_numeric_parity_report(
    notebook_root: Path,
    app_run_dir: Path,
    *,
    specs: tuple[ComparisonSpec, ...] | None = None,
) -> dict[str, Any]:
    comparison_specs = specs or build_default_comparison_specs()
    rows = [compare_spec(spec, notebook_root=notebook_root, app_run_dir=app_run_dir) for spec in comparison_specs]
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row.status] = status_counts.get(row.status, 0) + 1
    return {
        "report_type": "numeric_and_content_parity",
        "artifact_class": "FILESYSTEM_ONLY",
        "local_only": True,
        "notebook_root_label": notebook_root.name,
        "app_run_id": app_run_dir.name,
        "rows": [row.to_report_dict() for row in rows],
        "summary": {
            "comparison_count": len(rows),
            "status_counts": status_counts,
        },
    }


def write_numeric_parity_report(
    notebook_root: Path,
    app_run_dir: Path,
    output_dir: Path,
    *,
    specs: tuple[ComparisonSpec, ...] | None = None,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_numeric_parity_report(notebook_root, app_run_dir, specs=specs)
    stem = f"{NUMERIC_PARITY_REPORT_PREFIX}_{app_run_dir.name}"
    json_path = output_dir / f"{stem}.json"
    csv_path = output_dir / f"{stem}.csv"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDNAMES)
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow(ComparisonRow(**_row_dict_to_init_kwargs(row)).to_csv_dict())
    return json_path, csv_path


def compare_spec(spec: ComparisonSpec, *, notebook_root: Path, app_run_dir: Path) -> ComparisonRow:
    app_path = app_run_dir / spec.app_file
    app_file = spec.app_file
    notebook_match = resolve_notebook_file(notebook_root, spec.notebook_candidates)
    notebook_file = notebook_match[0]

    if not app_path.is_file():
        return ComparisonRow(
            family=spec.family,
            notebook_file=notebook_file,
            app_file=app_file,
            comparison_type=spec.comparison_type,
            status="SKIP_MISSING_APP",
            skipped_reason="app_file_missing",
            notes=spec.notes,
        )
    if notebook_file is None:
        return ComparisonRow(
            family=spec.family,
            notebook_file="",
            app_file=app_file,
            comparison_type=spec.comparison_type,
            status="SKIP_MISSING_NOTEBOOK",
            skipped_reason="notebook_file_missing",
            notes=spec.notes,
        )
    if notebook_match[1] == "ambiguous":
        return ComparisonRow(
            family=spec.family,
            notebook_file="",
            app_file=app_file,
            comparison_type=spec.comparison_type,
            status="SKIP_UNMAPPED",
            skipped_reason="ambiguous_notebook_mapping",
            notes=spec.notes,
        )

    notebook_path = notebook_root / notebook_file
    if spec.comparison_type == "raster":
        return compare_raster_files(spec, notebook_path=notebook_path, app_path=app_path, notebook_file=notebook_file)
    if spec.comparison_type == "npy":
        return compare_npy_files(spec, notebook_path=notebook_path, app_path=app_path, notebook_file=notebook_file)
    if spec.comparison_type == "csv":
        return compare_csv_files(spec, notebook_path=notebook_path, app_path=app_path, notebook_file=notebook_file)
    if spec.comparison_type == "json":
        return compare_json_files(spec, notebook_path=notebook_path, app_path=app_path, notebook_file=notebook_file)
    if spec.comparison_type == "kmz":
        return compare_kmz_files(spec, notebook_path=notebook_path, app_path=app_path, notebook_file=notebook_file)
    if spec.comparison_type == "text":
        return compare_text_files(spec, notebook_path=notebook_path, app_path=app_path, notebook_file=notebook_file)
    return ComparisonRow(
        family=spec.family,
        notebook_file=notebook_file,
        app_file=app_file,
        comparison_type=spec.comparison_type,
        status="SKIP_UNSUPPORTED_CONTAINER",
        skipped_reason="unsupported_comparison_type",
        notes=spec.notes,
    )


def resolve_notebook_file(notebook_root: Path, candidates: tuple[str, ...]) -> tuple[str | None, str]:
    matches: set[str] = set()
    for candidate in candidates:
        exact_path = notebook_root / candidate
        if exact_path.is_file():
            matches.add(candidate.replace("\\", "/"))
            continue
        for path in notebook_root.rglob("*"):
            if path.is_file() and fnmatch.fnmatch(path.relative_to(notebook_root).as_posix(), candidate):
                matches.add(path.relative_to(notebook_root).as_posix())
    if not matches:
        return None, "missing"
    sorted_matches = sorted(matches)
    if len(sorted_matches) > 1:
        return None, "ambiguous"
    return sorted_matches[0], "ok"


def compare_raster_files(
    spec: ComparisonSpec,
    *,
    notebook_path: Path,
    app_path: Path,
    notebook_file: str,
) -> ComparisonRow:
    try:
        notebook_raster = load_raster_snapshot(notebook_path)
        app_raster = load_raster_snapshot(app_path)
    except RasterioIOError:
        return ComparisonRow(
            family=spec.family,
            notebook_file=notebook_file,
            app_file=spec.app_file,
            comparison_type=spec.comparison_type,
            status="SKIP_UNSUPPORTED_CONTAINER",
            skipped_reason="unsupported_raster_container",
            notes=_append_note(spec.notes, "rasterio_open_failed"),
        )

    array_result = compare_arrays(notebook_raster.array, app_raster.array, tolerance=spec.tolerance)
    shape_match = (
        notebook_raster.width == app_raster.width
        and notebook_raster.height == app_raster.height
        and notebook_raster.count == app_raster.count
        and array_result["shape_match"]
    )
    crs_match = notebook_raster.crs == app_raster.crs if notebook_raster.crs is not None and app_raster.crs is not None else False
    transform_match = (
        np.allclose(notebook_raster.transform, app_raster.transform, atol=1e-9, rtol=0.0)
        if notebook_raster.transform is not None and app_raster.transform is not None
        else False
    )
    dtype_match = notebook_raster.dtypes == app_raster.dtypes
    notes = spec.notes
    missing_metadata = [*notebook_raster.missing_metadata, *app_raster.missing_metadata]
    if missing_metadata:
        notes = _append_note(notes, ",".join(sorted(missing_metadata)))
    if notebook_raster.count != app_raster.count:
        notes = _append_note(notes, "band_count_mismatch")
    if notebook_raster.nodata != app_raster.nodata:
        notes = _append_note(notes, "nodata_policy_mismatch")
    if not dtype_match:
        notes = _append_note(notes, "dtype_mismatch")

    metadata_ok = (
        shape_match
        and crs_match
        and transform_match
        and dtype_match
        and not missing_metadata
        and notebook_raster.nodata == app_raster.nodata
    )
    status = "PASS" if metadata_ok and array_result["pass"] else "FAIL"
    return ComparisonRow(
        family=spec.family,
        notebook_file=notebook_file,
        app_file=spec.app_file,
        comparison_type=spec.comparison_type,
        status=status,
        shape_match=shape_match,
        crs_match=crs_match,
        transform_match=transform_match,
        dtype_match=dtype_match,
        exact_equal=array_result["exact_equal"],
        max_abs_diff=array_result["max_abs_diff"],
        mean_abs_diff=array_result["mean_abs_diff"],
        differing_count=array_result["differing_count"],
        matching_percent=array_result["matching_percent"],
        tolerance_used=spec.tolerance.as_dict(),
        notes=notes,
    )


def compare_npy_files(
    spec: ComparisonSpec,
    *,
    notebook_path: Path,
    app_path: Path,
    notebook_file: str,
) -> ComparisonRow:
    notebook_array = np.load(notebook_path)
    app_array = np.load(app_path)
    array_result = compare_arrays(notebook_array, app_array, tolerance=spec.tolerance)
    dtype_match = str(notebook_array.dtype) == str(app_array.dtype)
    status = "PASS" if dtype_match and array_result["pass"] else "FAIL"
    return ComparisonRow(
        family=spec.family,
        notebook_file=notebook_file,
        app_file=spec.app_file,
        comparison_type=spec.comparison_type,
        status=status,
        shape_match=array_result["shape_match"],
        dtype_match=dtype_match,
        exact_equal=array_result["exact_equal"],
        max_abs_diff=array_result["max_abs_diff"],
        mean_abs_diff=array_result["mean_abs_diff"],
        differing_count=array_result["differing_count"],
        matching_percent=array_result["matching_percent"],
        tolerance_used=spec.tolerance.as_dict(),
        notes=spec.notes,
    )


def compare_csv_files(
    spec: ComparisonSpec,
    *,
    notebook_path: Path,
    app_path: Path,
    notebook_file: str,
) -> ComparisonRow:
    notebook_rows = canonicalize_csv_rows(notebook_path)
    app_rows = canonicalize_csv_rows(app_path)
    exact_equal = notebook_rows == app_rows
    shape_match = len(notebook_rows) == len(app_rows)
    status = "PASS" if exact_equal else "FAIL"
    notes = spec.notes
    if not shape_match:
        notes = _append_note(notes, "row_count_mismatch")
    return ComparisonRow(
        family=spec.family,
        notebook_file=notebook_file,
        app_file=spec.app_file,
        comparison_type=spec.comparison_type,
        status=status,
        shape_match=shape_match,
        exact_equal=exact_equal,
        tolerance_used=spec.tolerance.as_dict(),
        notes=notes,
    )


def compare_json_files(
    spec: ComparisonSpec,
    *,
    notebook_path: Path,
    app_path: Path,
    notebook_file: str,
) -> ComparisonRow:
    notebook_payload = canonicalize_json_payload(json.loads(notebook_path.read_text(encoding="utf-8")))
    app_payload = canonicalize_json_payload(json.loads(app_path.read_text(encoding="utf-8")))
    exact_equal = notebook_payload == app_payload
    status = "PASS" if exact_equal else "FAIL"
    return ComparisonRow(
        family=spec.family,
        notebook_file=notebook_file,
        app_file=spec.app_file,
        comparison_type=spec.comparison_type,
        status=status,
        exact_equal=exact_equal,
        tolerance_used=spec.tolerance.as_dict(),
        notes=spec.notes,
    )


def compare_kmz_files(
    spec: ComparisonSpec,
    *,
    notebook_path: Path,
    app_path: Path,
    notebook_file: str,
) -> ComparisonRow:
    notebook_payload = canonicalize_kmz_payload(notebook_path)
    app_payload = canonicalize_kmz_payload(app_path)
    exact_equal = notebook_payload == app_payload
    status = "PASS" if exact_equal else "FAIL"
    return ComparisonRow(
        family=spec.family,
        notebook_file=notebook_file,
        app_file=spec.app_file,
        comparison_type=spec.comparison_type,
        status=status,
        exact_equal=exact_equal,
        tolerance_used=spec.tolerance.as_dict(),
        notes=spec.notes,
    )


def compare_text_files(
    spec: ComparisonSpec,
    *,
    notebook_path: Path,
    app_path: Path,
    notebook_file: str,
) -> ComparisonRow:
    notebook_text = canonicalize_text(notebook_path.read_text(encoding="utf-8"))
    app_text = canonicalize_text(app_path.read_text(encoding="utf-8"))
    exact_equal = notebook_text == app_text
    status = "PASS" if exact_equal else "FAIL"
    return ComparisonRow(
        family=spec.family,
        notebook_file=notebook_file,
        app_file=spec.app_file,
        comparison_type=spec.comparison_type,
        status=status,
        exact_equal=exact_equal,
        tolerance_used=spec.tolerance.as_dict(),
        notes=spec.notes,
    )


def compare_arrays(notebook_array: np.ndarray, app_array: np.ndarray, *, tolerance: Tolerance) -> dict[str, Any]:
    if notebook_array.shape != app_array.shape:
        return {
            "pass": False,
            "shape_match": False,
            "exact_equal": False,
            "max_abs_diff": None,
            "mean_abs_diff": None,
            "differing_count": None,
            "matching_percent": 0.0,
        }

    exact_equal = bool(np.array_equal(notebook_array, app_array))
    if exact_equal:
        return {
            "pass": True,
            "shape_match": True,
            "exact_equal": True,
            "max_abs_diff": 0.0,
            "mean_abs_diff": 0.0,
            "differing_count": 0,
            "matching_percent": 100.0,
        }

    if np.issubdtype(notebook_array.dtype, np.integer) and np.issubdtype(app_array.dtype, np.integer):
        differing = int(np.count_nonzero(notebook_array != app_array))
        return {
            "pass": False,
            "shape_match": True,
            "exact_equal": False,
            "max_abs_diff": float(np.max(np.abs(notebook_array.astype(np.int64) - app_array.astype(np.int64)))),
            "mean_abs_diff": float(np.mean(np.abs(notebook_array.astype(np.float64) - app_array.astype(np.float64)))),
            "differing_count": differing,
            "matching_percent": _matching_percent(notebook_array.size, differing),
        }

    notebook_float = notebook_array.astype(np.float64, copy=False)
    app_float = app_array.astype(np.float64, copy=False)
    finite_mask = np.isfinite(notebook_float) & np.isfinite(app_float)
    same_non_finite = np.array_equal(np.isfinite(notebook_float), np.isfinite(app_float))
    if not same_non_finite:
        differing = int(np.count_nonzero(np.isfinite(notebook_float) != np.isfinite(app_float)))
        return {
            "pass": False,
            "shape_match": True,
            "exact_equal": False,
            "max_abs_diff": None,
            "mean_abs_diff": None,
            "differing_count": differing,
            "matching_percent": _matching_percent(notebook_array.size, differing),
        }

    if not finite_mask.any():
        return {
            "pass": True,
            "shape_match": True,
            "exact_equal": False,
            "max_abs_diff": 0.0,
            "mean_abs_diff": 0.0,
            "differing_count": 0,
            "matching_percent": 100.0,
        }

    abs_diff = np.abs(notebook_float[finite_mask] - app_float[finite_mask])
    close_mask = np.isclose(
        notebook_float[finite_mask],
        app_float[finite_mask],
        atol=tolerance.abs_tol,
        rtol=tolerance.rel_tol,
        equal_nan=True,
    )
    differing = int(close_mask.size - int(np.count_nonzero(close_mask)))
    return {
        "pass": differing == 0,
        "shape_match": True,
        "exact_equal": False,
        "max_abs_diff": float(abs_diff.max(initial=0.0)),
        "mean_abs_diff": float(abs_diff.mean()) if abs_diff.size else 0.0,
        "differing_count": differing,
        "matching_percent": _matching_percent(close_mask.size, differing),
    }


def load_raster_snapshot(path: Path) -> RasterSnapshot:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", NotGeoreferencedWarning)
        with rasterio.open(path) as dataset:
            crs = dataset.crs.to_string() if dataset.crs else None
            transform = None
            if dataset.transform is not None and not dataset.transform.is_identity:
                transform = tuple(float(value) for value in dataset.transform[:6])
            missing_metadata: list[str] = []
            if crs is None:
                missing_metadata.append("missing_crs_metadata")
            if transform is None:
                missing_metadata.append("missing_transform_metadata")
            return RasterSnapshot(
                crs=crs,
                transform=transform,
                width=int(dataset.width),
                height=int(dataset.height),
                count=int(dataset.count),
                nodata=dataset.nodata,
                dtypes=tuple(str(value) for value in dataset.dtypes),
                array=dataset.read(),
                missing_metadata=tuple(missing_metadata),
            )


def canonicalize_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [
            {
                key: _normalize_scalar(value, precision=CSV_FLOAT_PRECISION)
                for key, value in row.items()
                if not _is_unstable_key(key)
            }
            for row in reader
        ]
    sort_key = next((key for key in STABLE_SORT_KEYS if rows and key in rows[0]), None)
    if sort_key is not None:
        rows.sort(key=lambda item: str(item.get(sort_key, "")))
    return rows


def canonicalize_json_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        items = []
        for key in sorted(payload):
            if _is_unstable_key(key):
                continue
            items.append((key, canonicalize_json_payload(payload[key])))
        if "features" in payload:
            features = [value for key, value in items if key == "features"][0]
            if isinstance(features, list):
                features.sort(key=_feature_sort_key)
        return {key: value for key, value in items}
    if isinstance(payload, list):
        return [canonicalize_json_payload(item) for item in payload]
    if isinstance(payload, float):
        return _rounded_float(payload, precision=JSON_NUMERIC_PRECISION)
    return payload


def canonicalize_kmz_payload(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path, "r") as archive:
        kml_name = next((name for name in archive.namelist() if name.lower().endswith(".kml")), None)
        if kml_name is None:
            return {"feature_count": 0, "placemarks": []}
        root = ElementTree.fromstring(archive.read(kml_name))
    placemarks = []
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    for placemark in root.findall(".//kml:Placemark", ns):
        name = placemark.findtext("kml:name", default="", namespaces=ns)
        coordinates = []
        for node in placemark.findall(".//kml:coordinates", ns):
            coordinates.extend(_parse_kml_coordinates(node.text or ""))
        placemarks.append(
            {
                "name": name.strip(),
                "coordinates": coordinates,
            }
        )
    placemarks.sort(key=lambda item: item["name"])
    return {"feature_count": len(placemarks), "placemarks": placemarks}


def canonicalize_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def _row_dict_to_init_kwargs(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    payload["notebook_file"] = payload.get("notebook_file") or None
    payload["app_file"] = payload.get("app_file") or None
    payload["tolerance_used"] = payload.get("tolerance_used") or None
    payload["skipped_reason"] = payload.get("skipped_reason") or None
    return payload


def _matching_percent(total_count: int, differing_count: int) -> float:
    if total_count <= 0:
        return 100.0
    return round(((total_count - differing_count) / total_count) * 100.0, 6)


def _append_note(existing: str, addition: str) -> str:
    if not existing:
        return addition
    return f"{existing}; {addition}"


def _stringify_bool(value: bool | None) -> str:
    if value is None:
        return ""
    return str(value).lower()


def _stringify_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.8f}"


def _normalize_scalar(value: str | None, *, precision: int) -> Any:
    if value is None:
        return ""
    stripped = value.strip()
    if stripped == "":
        return ""
    try:
        number = float(stripped)
    except ValueError:
        return stripped
    if math.isfinite(number) and number.is_integer():
        return int(number)
    return _rounded_float(number, precision=precision)


def _rounded_float(value: float, *, precision: int) -> float:
    return round(float(value), precision)


def _is_unstable_key(key: str) -> bool:
    lowered = key.casefold()
    return any(part in lowered for part in UNSTABLE_KEY_PARTS)


def _feature_sort_key(feature: Any) -> str:
    if not isinstance(feature, dict):
        return ""
    properties = feature.get("properties", {})
    if isinstance(properties, dict):
        for key in ("export_role", "name", "id"):
            if key in properties:
                return str(properties[key])
    geometry = feature.get("geometry", {})
    geometry_type = geometry.get("type", "") if isinstance(geometry, dict) else ""
    return str(geometry_type)


def _parse_kml_coordinates(text: str) -> list[list[float]]:
    coordinates: list[list[float]] = []
    for chunk in text.replace("\n", " ").split():
        parts = chunk.split(",")
        if len(parts) < 2:
            continue
        lon = _rounded_float(float(parts[0]), precision=KMZ_COORD_PRECISION)
        lat = _rounded_float(float(parts[1]), precision=KMZ_COORD_PRECISION)
        alt = _rounded_float(float(parts[2]), precision=KMZ_COORD_PRECISION) if len(parts) > 2 and parts[2] else 0.0
        coordinates.append([lon, lat, alt])
    return coordinates
