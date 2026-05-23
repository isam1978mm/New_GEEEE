from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.services.numeric_parity_report import Tolerance, compare_arrays, load_raster_snapshot, resolve_notebook_file

SAR_PROCESSING_PARITY_PREFIX = "sar_processing_parity"
SAR_PROCESSING_FIELDNAMES = [
    "check",
    "status",
    "band_name",
    "notebook_file",
    "app_file",
    "likely_cause",
    "raw_matching_percent",
    "common_valid_matching_percent",
    "mask_overlap_percent",
    "mean_diff",
    "median_diff",
    "correlation",
    "linear_slope",
    "linear_intercept",
    "evidence",
    "recommended_next_action",
]
SAR_BAND_TOLERANCE = Tolerance(abs_tol=1e-4, rel_tol=1e-5)
SAR_BAND_MAPPINGS = {
    "VV_dB": {
        "notebook_band_name": "VV_dB",
        "app_raster": "VV_dB.tif",
        "notebook_raster_candidates": ("VV_dB.tif", "GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640*.tif"),
        "app_npy": "npy_radar_bands/VV_dB.npy",
        "notebook_npy_candidates": ("npy_radar_bands/VV_dB.npy", "NPY_RADAR_BANDS/RADAR_VV_dB_640*.npy", "NPY_RADAR_BANDS/*VV*.npy"),
    },
    "VH_dB": {
        "notebook_band_name": "VH_dB",
        "app_raster": "VH_dB.tif",
        "notebook_raster_candidates": ("VH_dB.tif", "GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640*.tif"),
        "app_npy": "npy_radar_bands/VH_dB.npy",
        "notebook_npy_candidates": ("npy_radar_bands/VH_dB.npy", "NPY_RADAR_BANDS/RADAR_VH_dB_640*.npy", "NPY_RADAR_BANDS/*VH*.npy"),
    },
    "logRatio_dB": {
        "notebook_band_name": "logRatio_dB",
        "app_raster": "logRatio_dB.tif",
        "notebook_raster_candidates": ("logRatio_dB.tif", "GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640*.tif"),
        "app_npy": "npy_radar_bands/logRatio_dB.npy",
        "notebook_npy_candidates": ("npy_radar_bands/logRatio_dB.npy", "NPY_RADAR_BANDS/RADAR_logRatio_dB_640*.npy", "NPY_RADAR_BANDS/*logRatio*.npy"),
    },
    "incidence": {
        "notebook_band_name": "angle",
        "app_raster": "incidence.tif",
        "notebook_raster_candidates": ("incidence.tif", "GEOTIFF_RADAR_BANDS/RADAR_angle_640*.tif"),
        "app_npy": "npy_radar_bands/incidence.npy",
        "notebook_npy_candidates": ("npy_radar_bands/incidence.npy", "NPY_RADAR_BANDS/RADAR_angle_640*.npy", "NPY_RADAR_BANDS/*angle*.npy", "NPY_RADAR_BANDS/*incidence*.npy"),
    },
}
NOTEBOOK_SUMMARY_CANDIDATES = ("qa/sar/sar_summary.csv", "SUMMARY_RADAR*.csv")
NOTEBOOK_STACK_CANDIDATES = ("stacks/tensor_support/radar_linear_support_stack.npy", "NPY_STACKS/RADAR_STACK_HWC_640*.npy")


@dataclass(frozen=True, slots=True)
class NotebookRelativeFile:
    root_label: str
    relative_path: str


@dataclass(frozen=True, slots=True)
class SarProcessingRow:
    check: str
    status: str
    band_name: str
    notebook_file: str
    app_file: str
    likely_cause: str
    raw_matching_percent: float | None
    common_valid_matching_percent: float | None
    mask_overlap_percent: float | None
    mean_diff: float | None
    median_diff: float | None
    correlation: float | None
    linear_slope: float | None
    linear_intercept: float | None
    evidence: str
    recommended_next_action: str

    def to_report_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_csv_dict(self) -> dict[str, str]:
        payload = self.to_report_dict()
        for field in (
            "raw_matching_percent",
            "common_valid_matching_percent",
            "mask_overlap_percent",
            "mean_diff",
            "median_diff",
            "correlation",
            "linear_slope",
            "linear_intercept",
        ):
            payload[field] = _stringify_number(payload[field])
        return {field: str(payload.get(field, "")) for field in SAR_PROCESSING_FIELDNAMES}


@dataclass(frozen=True, slots=True)
class SarSummaryDiff:
    band_name: str
    status: str
    notebook_value: dict[str, str]
    app_value: dict[str, str]
    evidence: str


def build_sar_processing_parity_report(
    *,
    app_run_dir: Path,
    notebook_roots: list[Path],
) -> dict[str, Any]:
    rows: list[SarProcessingRow] = []
    referenced_notebook_files: dict[tuple[str, str], NotebookRelativeFile] = {}
    referenced_app_files: set[str] = set()

    summary_rows, summary_files = _build_summary_rows(app_run_dir=app_run_dir, notebook_roots=notebook_roots)
    rows.extend(summary_rows)
    for item in summary_files:
        referenced_notebook_files[(item.root_label, item.relative_path)] = item
    if (app_run_dir / "qa" / "sar" / "sar_summary.csv").is_file():
        referenced_app_files.add("qa/sar/sar_summary.csv")

    band_arrays: dict[str, dict[str, Any]] = {}
    for band_name, mapping in SAR_BAND_MAPPINGS.items():
        raster_row, notebook_raster, app_raster, raster_payload = _build_array_row(
            check=f"{band_name}_raster",
            band_name=band_name,
            app_run_dir=app_run_dir,
            notebook_roots=notebook_roots,
            app_file=str(mapping["app_raster"]),
            notebook_candidates=tuple(mapping["notebook_raster_candidates"]),
            loader="raster",
        )
        rows.append(raster_row)
        if notebook_raster is not None:
            referenced_notebook_files[(notebook_raster.root_label, notebook_raster.relative_path)] = notebook_raster
        if (app_run_dir / str(mapping["app_raster"])).is_file():
            referenced_app_files.add(str(mapping["app_raster"]))
        if raster_payload is not None:
            band_arrays.setdefault(band_name, {})["raster"] = raster_payload

        npy_row, notebook_npy, app_npy, npy_payload = _build_array_row(
            check=f"{band_name}_npy",
            band_name=band_name,
            app_run_dir=app_run_dir,
            notebook_roots=notebook_roots,
            app_file=str(mapping["app_npy"]),
            notebook_candidates=tuple(mapping["notebook_npy_candidates"]),
            loader="npy",
        )
        rows.append(npy_row)
        if notebook_npy is not None:
            referenced_notebook_files[(notebook_npy.root_label, notebook_npy.relative_path)] = notebook_npy
        if (app_run_dir / str(mapping["app_npy"])).is_file():
            referenced_app_files.add(str(mapping["app_npy"]))
        if npy_payload is not None:
            band_arrays.setdefault(band_name, {})["npy"] = npy_payload

    rows.extend(_build_log_ratio_rows(band_arrays))
    stack_row, notebook_stack = _build_stack_row(app_run_dir=app_run_dir, notebook_roots=notebook_roots)
    rows.append(stack_row)
    if notebook_stack is not None:
        referenced_notebook_files[(notebook_stack.root_label, notebook_stack.relative_path)] = notebook_stack
    if (app_run_dir / "stacks" / "tensor_support" / "radar_linear_support_stack.npy").is_file():
        referenced_app_files.add("stacks/tensor_support/radar_linear_support_stack.npy")

    status_counts: dict[str, int] = {}
    likely_cause_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row.status] = status_counts.get(row.status, 0) + 1
        likely_cause_counts[row.likely_cause] = likely_cause_counts.get(row.likely_cause, 0) + 1

    return {
        "report_type": "sar_processing_parity",
        "artifact_class": "FILESYSTEM_ONLY",
        "local_only": True,
        "app_run_id": app_run_dir.name,
        "notebook_root_labels": [root.name for root in notebook_roots],
        "app_files": sorted(referenced_app_files),
        "notebook_files": [
            {"root_label": item.root_label, "relative_path": item.relative_path}
            for item in sorted(referenced_notebook_files.values(), key=lambda item: (item.root_label, item.relative_path))
        ],
        "rows": [row.to_report_dict() for row in rows],
        "summary": {
            "row_count": len(rows),
            "status_counts": status_counts,
            "likely_cause_counts": likely_cause_counts,
        },
    }


def write_sar_processing_parity_report(
    *,
    app_run_dir: Path,
    notebook_roots: list[Path],
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_sar_processing_parity_report(app_run_dir=app_run_dir, notebook_roots=notebook_roots)
    stem = f"{SAR_PROCESSING_PARITY_PREFIX}_{app_run_dir.name}"
    json_path = output_dir / f"{stem}.json"
    csv_path = output_dir / f"{stem}.csv"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SAR_PROCESSING_FIELDNAMES)
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow(SarProcessingRow(**row).to_csv_dict())
    return json_path, csv_path


def compare_sar_summary_rows(
    *,
    notebook_rows: dict[str, dict[str, str]],
    app_rows: dict[str, dict[str, str]],
) -> list[SarSummaryDiff]:
    rows: list[SarSummaryDiff] = []
    for app_band_name, mapping in SAR_BAND_MAPPINGS.items():
        notebook_band_name = str(mapping["notebook_band_name"])
        notebook_row = notebook_rows.get(notebook_band_name, {})
        app_row = app_rows.get(app_band_name, {})
        if not notebook_row or not app_row:
            rows.append(
                SarSummaryDiff(
                    band_name=app_band_name,
                    status="MISSING",
                    notebook_value=notebook_row,
                    app_value=app_row,
                    evidence="Notebook or app SAR summary row is missing.",
                )
            )
            continue
        diffs: list[str] = []
        for field in ("min", "max", "mean", "nodata_count"):
            notebook_value = notebook_row.get(field, "")
            app_value = app_row.get(field, "")
            if notebook_value == app_value:
                continue
            if _numeric_close(notebook_value, app_value):
                continue
            diffs.append(field)
        if diffs:
            rows.append(
                SarSummaryDiff(
                    band_name=app_band_name,
                    status="MISMATCH",
                    notebook_value={field: notebook_row.get(field, "") for field in ("min", "max", "mean", "nodata_count")},
                    app_value={field: app_row.get(field, "") for field in ("min", "max", "mean", "nodata_count")},
                    evidence=f"SAR summary statistics differ for {', '.join(diffs)}.",
                )
            )
            continue
        rows.append(
            SarSummaryDiff(
                band_name=app_band_name,
                status="MATCH",
                notebook_value={field: notebook_row.get(field, "") for field in ("min", "max", "mean", "nodata_count")},
                app_value={field: app_row.get(field, "") for field in ("min", "max", "mean", "nodata_count")},
                evidence="SAR summary statistics match within comparison tolerance.",
            )
        )
    return rows


def validate_log_ratio_relationship(
    *,
    vv_array: np.ndarray,
    vh_array: np.ndarray,
    log_ratio_array: np.ndarray,
    nodata: float | None,
    tolerance: Tolerance = SAR_BAND_TOLERANCE,
) -> dict[str, Any]:
    expected = vv_array.astype(np.float64, copy=False) - vh_array.astype(np.float64, copy=False)
    valid_mask = _valid_mask(vv_array, nodata) & _valid_mask(vh_array, nodata) & _valid_mask(log_ratio_array, nodata)
    if not valid_mask.any():
        return {
            "status": "NEEDS_MANUAL_REVIEW",
            "matching_percent": None,
            "differing_count": None,
            "evidence": "No valid pixels remain for logRatio validation.",
        }
    result = compare_arrays(expected[valid_mask], log_ratio_array[valid_mask], tolerance=tolerance)
    status = "MATCH" if result["pass"] else "MISMATCH"
    return {
        "status": status,
        "matching_percent": result["matching_percent"],
        "differing_count": result["differing_count"],
        "evidence": (
            "logRatio matches VV_dB - VH_dB on the common valid mask."
            if status == "MATCH"
            else "logRatio differs from VV_dB - VH_dB on the common valid mask."
        ),
    }


def analyze_array_pair(
    *,
    band_name: str,
    notebook_array: np.ndarray,
    app_array: np.ndarray,
    notebook_nodata: float | None,
    app_nodata: float | None,
    tolerance: Tolerance = SAR_BAND_TOLERANCE,
) -> dict[str, Any]:
    raw_metrics = compare_arrays(notebook_array, app_array, tolerance=tolerance)
    notebook_valid = _valid_mask(notebook_array, notebook_nodata)
    app_valid = _valid_mask(app_array, app_nodata)
    overlap_mask = notebook_valid & app_valid
    mask_equal = bool(np.array_equal(notebook_valid, app_valid))
    overlap_count = int(np.count_nonzero(overlap_mask))
    total_count = int(overlap_mask.size)
    mask_overlap_percent = round((overlap_count / total_count) * 100.0, 6) if total_count else 100.0
    common_metrics: dict[str, Any]
    if overlap_count:
        common_metrics = compare_arrays(
            notebook_array.astype(np.float64, copy=False)[overlap_mask],
            app_array.astype(np.float64, copy=False)[overlap_mask],
            tolerance=tolerance,
        )
        notebook_values = notebook_array.astype(np.float64, copy=False)[overlap_mask]
        app_values = app_array.astype(np.float64, copy=False)[overlap_mask]
        mean_diff = float(np.mean(app_values - notebook_values))
        median_diff = float(np.median(app_values - notebook_values))
        correlation, slope, intercept = _linear_fit(notebook_values, app_values)
    else:
        common_metrics = {
            "pass": False,
            "matching_percent": None,
            "differing_count": None,
        }
        mean_diff = None
        median_diff = None
        correlation = None
        slope = None
        intercept = None

    status = "MATCH"
    if raw_metrics["pass"]:
        status = "MATCH"
    elif overlap_count and common_metrics["pass"]:
        status = "MATCH_COMMON_VALID_MASK"
    else:
        status = "MISMATCH"

    likely_cause = _infer_likely_cause(
        band_name=band_name,
        raw_metrics=raw_metrics,
        common_metrics=common_metrics,
        mask_equal=mask_equal,
        correlation=correlation,
        slope=slope,
        intercept=intercept,
    )
    evidence_parts = [
        f"Raw matching_percent={_stringify_number(raw_metrics.get('matching_percent')) or 'n/a'}.",
        f"Common-valid matching_percent={_stringify_number(common_metrics.get('matching_percent')) or 'n/a'}.",
        f"Mask overlap percent={_stringify_number(mask_overlap_percent)}.",
    ]
    if band_name == "incidence":
        evidence_parts.append("Notebook angle is compared to app incidence as the documented angle-to-incidence mapping.")
    if slope is not None and intercept is not None:
        correlation_text = "n/a" if correlation is None else f"{correlation:.6f}"
        evidence_parts.append(
            f"Linear fit app≈({slope:.6f} * notebook) + {intercept:.6f} with correlation={correlation_text}."
        )
    return {
        "status": status,
        "likely_cause": likely_cause,
        "raw_matching_percent": raw_metrics.get("matching_percent"),
        "common_valid_matching_percent": common_metrics.get("matching_percent"),
        "mask_overlap_percent": mask_overlap_percent,
        "mean_diff": mean_diff,
        "median_diff": median_diff,
        "correlation": correlation,
        "linear_slope": slope,
        "linear_intercept": intercept,
        "evidence": " ".join(evidence_parts),
    }


def _build_summary_rows(
    *,
    app_run_dir: Path,
    notebook_roots: list[Path],
) -> tuple[list[SarProcessingRow], list[NotebookRelativeFile]]:
    rows: list[SarProcessingRow] = []
    referenced_files: list[NotebookRelativeFile] = []
    app_summary_path = app_run_dir / "qa" / "sar" / "sar_summary.csv"
    notebook_summary = _resolve_notebook_relative_file(notebook_roots, NOTEBOOK_SUMMARY_CANDIDATES)
    if not app_summary_path.is_file() or notebook_summary is None:
        rows.append(
            SarProcessingRow(
                check="sar_summary",
                status="MISSING",
                band_name="",
                notebook_file="" if notebook_summary is None else f"{notebook_summary.root_label}:{notebook_summary.relative_path}",
                app_file="qa/sar/sar_summary.csv" if app_summary_path.is_file() else "",
                likely_cause="MISSING_SUMMARY_INPUT",
                raw_matching_percent=None,
                common_valid_matching_percent=None,
                mask_overlap_percent=None,
                mean_diff=None,
                median_diff=None,
                correlation=None,
                linear_slope=None,
                linear_intercept=None,
                evidence="Notebook or app SAR summary CSV is missing.",
                recommended_next_action="Capture both SAR summary CSV files before diagnosing SAR processing parity.",
            )
        )
        return rows, referenced_files
    referenced_files.append(notebook_summary)
    notebook_rows = _read_summary_rows(_notebook_path(notebook_roots, notebook_summary))
    app_rows = _read_summary_rows(app_summary_path)
    for diff in compare_sar_summary_rows(notebook_rows=notebook_rows, app_rows=app_rows):
        rows.append(
            SarProcessingRow(
                check=f"sar_summary_{diff.band_name}",
                status=diff.status,
                band_name=diff.band_name,
                notebook_file=f"{notebook_summary.root_label}:{notebook_summary.relative_path}",
                app_file="qa/sar/sar_summary.csv",
                likely_cause="SUMMARY_STATS_MATCH" if diff.status == "MATCH" else "SUMMARY_STATS_MISMATCH",
                raw_matching_percent=None,
                common_valid_matching_percent=None,
                mask_overlap_percent=None,
                mean_diff=None,
                median_diff=None,
                correlation=None,
                linear_slope=None,
                linear_intercept=None,
                evidence=diff.evidence,
                recommended_next_action=(
                    "No action required."
                    if diff.status == "MATCH"
                    else "Compare the underlying SAR rasters and NPY outputs to isolate the processing difference."
                ),
            )
        )
    return rows, referenced_files


def _build_array_row(
    *,
    check: str,
    band_name: str,
    app_run_dir: Path,
    notebook_roots: list[Path],
    app_file: str,
    notebook_candidates: tuple[str, ...],
    loader: str,
) -> tuple[SarProcessingRow, NotebookRelativeFile | None, str | None, dict[str, Any] | None]:
    notebook_relative = _resolve_notebook_relative_file(notebook_roots, notebook_candidates)
    app_path = app_run_dir / app_file
    notebook_label = "" if notebook_relative is None else f"{notebook_relative.root_label}:{notebook_relative.relative_path}"
    if notebook_relative is None or not app_path.is_file():
        return (
            SarProcessingRow(
                check=check,
                status="MISSING",
                band_name=band_name,
                notebook_file=notebook_label,
                app_file=app_file if app_path.is_file() else "",
                likely_cause="MISSING_PROCESSING_INPUT",
                raw_matching_percent=None,
                common_valid_matching_percent=None,
                mask_overlap_percent=None,
                mean_diff=None,
                median_diff=None,
                correlation=None,
                linear_slope=None,
                linear_intercept=None,
                evidence="Notebook or app SAR processing artifact is missing.",
                recommended_next_action="Capture both notebook and app SAR artifacts before diagnosing processing parity.",
            ),
            notebook_relative,
            app_file if app_path.is_file() else None,
            None,
        )
    notebook_path = _notebook_path(notebook_roots, notebook_relative)
    if loader == "raster":
        notebook_snapshot = load_raster_snapshot(notebook_path)
        app_snapshot = load_raster_snapshot(app_path)
        analysis = analyze_array_pair(
            band_name=band_name,
            notebook_array=_squeeze_array(notebook_snapshot.array),
            app_array=_squeeze_array(app_snapshot.array),
            notebook_nodata=notebook_snapshot.nodata,
            app_nodata=app_snapshot.nodata,
        )
        payload = {
            "array": _squeeze_array(notebook_snapshot.array),
            "app_array": _squeeze_array(app_snapshot.array),
            "notebook_nodata": notebook_snapshot.nodata,
            "app_nodata": app_snapshot.nodata,
        }
    else:
        notebook_array = np.load(notebook_path)
        app_array = np.load(app_path)
        analysis = analyze_array_pair(
            band_name=band_name,
            notebook_array=notebook_array,
            app_array=app_array,
            notebook_nodata=None,
            app_nodata=None,
        )
        payload = {
            "array": notebook_array,
            "app_array": app_array,
            "notebook_nodata": None,
            "app_nodata": None,
        }
    return (
        SarProcessingRow(
            check=check,
            status=str(analysis["status"]),
            band_name=band_name,
            notebook_file=notebook_label,
            app_file=app_file,
            likely_cause=str(analysis["likely_cause"]),
            raw_matching_percent=_as_float(analysis["raw_matching_percent"]),
            common_valid_matching_percent=_as_float(analysis["common_valid_matching_percent"]),
            mask_overlap_percent=_as_float(analysis["mask_overlap_percent"]),
            mean_diff=_as_float(analysis["mean_diff"]),
            median_diff=_as_float(analysis["median_diff"]),
            correlation=_as_float(analysis["correlation"]),
            linear_slope=_as_float(analysis["linear_slope"]),
            linear_intercept=_as_float(analysis["linear_intercept"]),
            evidence=str(analysis["evidence"]),
            recommended_next_action=_recommended_next_action(str(analysis["likely_cause"])),
        ),
        notebook_relative,
        app_file,
        payload,
    )


def _build_log_ratio_rows(band_arrays: dict[str, dict[str, Any]]) -> list[SarProcessingRow]:
    rows: list[SarProcessingRow] = []
    for container in ("raster", "npy"):
        vv = band_arrays.get("VV_dB", {}).get(container)
        vh = band_arrays.get("VH_dB", {}).get(container)
        log_ratio = band_arrays.get("logRatio_dB", {}).get(container)
        if vv is None or vh is None or log_ratio is None:
            rows.append(
                SarProcessingRow(
                    check=f"logratio_formula_{container}",
                    status="MISSING",
                    band_name="logRatio_dB",
                    notebook_file="",
                    app_file="",
                    likely_cause="MISSING_LOGRATIO_INPUT",
                    raw_matching_percent=None,
                    common_valid_matching_percent=None,
                    mask_overlap_percent=None,
                    mean_diff=None,
                    median_diff=None,
                    correlation=None,
                    linear_slope=None,
                    linear_intercept=None,
                    evidence="VV/VH/logRatio inputs were not all available for formula validation.",
                    recommended_next_action="Capture VV, VH, and logRatio artifacts before validating the logRatio relationship.",
                )
            )
            continue
        notebook_formula = validate_log_ratio_relationship(
            vv_array=vv["array"],
            vh_array=vh["array"],
            log_ratio_array=log_ratio["array"],
            nodata=log_ratio["notebook_nodata"],
        )
        app_formula = validate_log_ratio_relationship(
            vv_array=vv["app_array"],
            vh_array=vh["app_array"],
            log_ratio_array=log_ratio["app_array"],
            nodata=log_ratio["app_nodata"],
        )
        for side, result in (("notebook", notebook_formula), ("app", app_formula)):
            rows.append(
                SarProcessingRow(
                    check=f"logratio_formula_{side}_{container}",
                    status=str(result["status"]),
                    band_name="logRatio_dB",
                    notebook_file=side if side == "notebook" else "",
                    app_file=side if side == "app" else "",
                    likely_cause="LOGRATIO_FORMULA_MATCH" if result["status"] == "MATCH" else "LOGRATIO_FORMULA_MISMATCH",
                    raw_matching_percent=_as_float(result.get("matching_percent")),
                    common_valid_matching_percent=_as_float(result.get("matching_percent")),
                    mask_overlap_percent=None,
                    mean_diff=None,
                    median_diff=None,
                    correlation=None,
                    linear_slope=None,
                    linear_intercept=None,
                    evidence=str(result["evidence"]),
                    recommended_next_action=(
                        "No action required."
                        if result["status"] == "MATCH"
                        else "Fix logRatio construction order before blaming downstream stacks."
                    ),
                )
            )
    return rows


def _build_stack_row(
    *,
    app_run_dir: Path,
    notebook_roots: list[Path],
) -> tuple[SarProcessingRow, NotebookRelativeFile | None]:
    app_file = "stacks/tensor_support/radar_linear_support_stack.npy"
    app_path = app_run_dir / app_file
    notebook_relative = _resolve_notebook_relative_file(notebook_roots, NOTEBOOK_STACK_CANDIDATES)
    notebook_label = "" if notebook_relative is None else f"{notebook_relative.root_label}:{notebook_relative.relative_path}"
    if notebook_relative is None or not app_path.is_file():
        return (
            SarProcessingRow(
                check="radar_linear_support_stack",
                status="MISSING",
                band_name="",
                notebook_file=notebook_label,
                app_file=app_file if app_path.is_file() else "",
                likely_cause="MISSING_STACK_INPUT",
                raw_matching_percent=None,
                common_valid_matching_percent=None,
                mask_overlap_percent=None,
                mean_diff=None,
                median_diff=None,
                correlation=None,
                linear_slope=None,
                linear_intercept=None,
                evidence="Notebook or app radar support stack is missing.",
                recommended_next_action="Diagnose VV/VH/logRatio/incidence first; the radar support stack is downstream.",
            ),
            notebook_relative,
        )
    notebook_array = np.load(_notebook_path(notebook_roots, notebook_relative))
    app_array = np.load(app_path)
    metrics = compare_arrays(notebook_array, app_array, tolerance=SAR_BAND_TOLERANCE)
    return (
        SarProcessingRow(
            check="radar_linear_support_stack",
            status="DOWNSTREAM_DIAGNOSTIC" if not metrics["pass"] else "MATCH",
            band_name="",
            notebook_file=notebook_label,
            app_file=app_file,
            likely_cause="DOWNSTREAM_FROM_SAR_BANDS" if not metrics["pass"] else "STACK_MATCH",
            raw_matching_percent=_as_float(metrics.get("matching_percent")),
            common_valid_matching_percent=_as_float(metrics.get("matching_percent")),
            mask_overlap_percent=None,
            mean_diff=_as_float(metrics.get("mean_abs_diff")),
            median_diff=None,
            correlation=None,
            linear_slope=None,
            linear_intercept=None,
            evidence=(
                "Radar support stack matches."
                if metrics["pass"]
                else "Radar support stack mismatch is treated as downstream evidence until SAR band processing parity is resolved."
            ),
            recommended_next_action=(
                "No action required."
                if metrics["pass"]
                else "Do not change stack assembly until SAR band processing parity is understood."
            ),
        ),
        notebook_relative,
    )


def _resolve_notebook_relative_file(
    notebook_roots: list[Path],
    candidates: tuple[str, ...],
) -> NotebookRelativeFile | None:
    for root in notebook_roots:
        relative_path, status = resolve_notebook_file(root, candidates)
        if status == "ok" and relative_path is not None:
            return NotebookRelativeFile(root_label=root.name, relative_path=relative_path)
    return None


def _read_summary_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        (row.get("band_name") or row.get("band") or "").strip(): {key: (value or "").strip() for key, value in row.items()}
        for row in rows
        if (row.get("band_name") or row.get("band") or "").strip()
    }


def _valid_mask(array: np.ndarray, nodata: float | None) -> np.ndarray:
    mask = np.isfinite(array)
    if nodata is not None:
        mask &= array != nodata
    return mask


def _linear_fit(x_values: np.ndarray, y_values: np.ndarray) -> tuple[float | None, float | None, float | None]:
    if x_values.size < 2 or y_values.size < 2:
        return None, None, None
    if np.allclose(x_values, x_values[0]):
        intercept = float(y_values.mean())
        return None, 0.0, intercept
    slope, intercept = np.polyfit(x_values, y_values, deg=1)
    correlation_matrix = np.corrcoef(x_values, y_values)
    correlation = float(correlation_matrix[0, 1]) if correlation_matrix.shape == (2, 2) else None
    return correlation, float(slope), float(intercept)


def _infer_likely_cause(
    *,
    band_name: str,
    raw_metrics: dict[str, Any],
    common_metrics: dict[str, Any],
    mask_equal: bool,
    correlation: float | None,
    slope: float | None,
    intercept: float | None,
) -> str:
    raw_match = raw_metrics.get("matching_percent")
    common_match = common_metrics.get("matching_percent")
    if raw_metrics.get("pass"):
        return "PROCESSING_MATCH"
    if common_metrics.get("pass") and not mask_equal:
        return "ANGLE_MAPPING_OR_MASKING" if band_name == "incidence" else "NODATA_POLICY_OR_MASKING"
    if correlation is not None and slope is not None and intercept is not None and correlation >= 0.999:
        if abs(slope - 1.0) <= 0.01 and abs(intercept) > 0.1:
            return "CONSTANT_OFFSET"
        if abs(slope - 1.0) > 0.01:
            return "LINEAR_SCALE_OR_RTC_DIFFERENCE"
    if band_name == "logRatio_dB" and common_match is not None and common_match < 99.0:
        return "UPSTREAM_VV_VH_PROCESSING_MISMATCH"
    if raw_match is not None and common_match is not None and common_match > raw_match:
        return "COMMON_VALID_MASK_IMPROVES_MATCH"
    return "PROCESSING_ALGORITHM_MISMATCH"


def _recommended_next_action(likely_cause: str) -> str:
    actions = {
        "PROCESSING_MATCH": "No action required.",
        "NODATA_POLICY_OR_MASKING": "Compare nodata masks and masking order before changing SAR math.",
        "ANGLE_MAPPING_OR_MASKING": "Treat notebook angle and app incidence as the same source first, then inspect masking differences.",
        "CONSTANT_OFFSET": "Inspect for a constant offset introduced by aggregation, conversion order, or metadata normalization.",
        "LINEAR_SCALE_OR_RTC_DIFFERENCE": "Inspect dB-linear-dB order and local DEM RTC correction path before changing selection rules.",
        "UPSTREAM_VV_VH_PROCESSING_MISMATCH": "Treat logRatio as downstream and diagnose VV/VH processing first.",
        "COMMON_VALID_MASK_IMPROVES_MATCH": "Use common-valid-mask and nodata-normalized metrics before changing science logic.",
        "PROCESSING_ALGORITHM_MISMATCH": "Inspect SAR aggregation and local DEM RTC processing; do not change tolerances.",
    }
    return actions.get(likely_cause, "Inspect SAR processing parity before changing science logic.")


def _numeric_close(left: str, right: str) -> bool:
    if left == right:
        return True
    try:
        return bool(np.isclose(float(left), float(right), atol=SAR_BAND_TOLERANCE.abs_tol, rtol=SAR_BAND_TOLERANCE.rel_tol))
    except ValueError:
        return False


def _squeeze_array(array: np.ndarray) -> np.ndarray:
    if array.ndim == 3 and array.shape[0] == 1:
        return array[0]
    return array


def _notebook_path(notebook_roots: list[Path], relative_file: NotebookRelativeFile) -> Path:
    for root in notebook_roots:
        if root.name == relative_file.root_label:
            return root / relative_file.relative_path
    raise FileNotFoundError(relative_file.relative_path)


def _stringify_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.8f}"


def _as_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    return float(value)
