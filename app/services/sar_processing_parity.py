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
ANGLE_LARGE_DELTA_DEGREES = 0.01
ANGLE_EDGE_DELTA_DEGREES = 1.0
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
NOTEBOOK_SUMMARY_CANDIDATES = ("qa/sar/sar_summary.csv", "QA/SUMMARY_RADAR*.csv", "SUMMARY_RADAR*.csv")
NOTEBOOK_STACK_CANDIDATES = ("stacks/tensor_support/radar_linear_support_stack.npy", "NPY_STACKS/RADAR_STACK_HWC_640*.npy")
NOTEBOOK_RADAR_META_CANDIDATES = ("QA/QA_RADAR_META*.json", "QA_RADAR_META*.json")


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
    prior_report_path: Path | None = None,
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

    metadata_rows, metadata_npy_candidates, metadata_files = _build_notebook_metadata_rows(notebook_roots)
    rows.extend(metadata_rows)
    for item in metadata_files:
        referenced_notebook_files[(item.root_label, item.relative_path)] = item

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
            notebook_candidates=metadata_npy_candidates.get(band_name) or tuple(mapping["notebook_npy_candidates"]),
            loader="npy",
        )
        rows.append(npy_row)
        if notebook_npy is not None:
            referenced_notebook_files[(notebook_npy.root_label, notebook_npy.relative_path)] = notebook_npy
        if (app_run_dir / str(mapping["app_npy"])).is_file():
            referenced_app_files.add(str(mapping["app_npy"]))
        if npy_payload is not None:
            band_arrays.setdefault(band_name, {})["npy"] = npy_payload

    rows.extend(_build_pixel_probe_rows(band_arrays))
    rows.extend(_build_f20_delta_diagnostic_rows(band_arrays))
    rows.extend(_build_log_ratio_rows(band_arrays))
    stack_row, notebook_stack = _build_stack_row(app_run_dir=app_run_dir, notebook_roots=notebook_roots)
    rows.append(stack_row)
    if notebook_stack is not None:
        referenced_notebook_files[(notebook_stack.root_label, notebook_stack.relative_path)] = notebook_stack
    if (app_run_dir / "stacks" / "tensor_support" / "radar_linear_support_stack.npy").is_file():
        referenced_app_files.add("stacks/tensor_support/radar_linear_support_stack.npy")

    if prior_report_path is not None:
        rows.extend(_build_prior_comparison_rows(current_rows=rows, prior_report_path=prior_report_path))

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
    prior_report_path: Path | None = None,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_sar_processing_parity_report(
        app_run_dir=app_run_dir,
        notebook_roots=notebook_roots,
        prior_report_path=prior_report_path,
    )
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
            diffs.append(_summary_delta(field, notebook_value, app_value))
        if diffs:
            rows.append(
                SarSummaryDiff(
                    band_name=app_band_name,
                    status="MISMATCH",
                    notebook_value={field: notebook_row.get(field, "") for field in ("min", "max", "mean", "nodata_count")},
                    app_value={field: app_row.get(field, "") for field in ("min", "max", "mean", "nodata_count")},
                    evidence=f"SAR summary statistics differ: {'; '.join(diffs)}.",
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


def _build_notebook_metadata_rows(
    notebook_roots: list[Path],
) -> tuple[list[SarProcessingRow], dict[str, tuple[str, ...]], list[NotebookRelativeFile]]:
    metadata_file = _resolve_notebook_relative_file(notebook_roots, NOTEBOOK_RADAR_META_CANDIDATES)
    if metadata_file is None:
        return [], {}, []
    payload = json.loads(_notebook_path(notebook_roots, metadata_file).read_text(encoding="utf-8"))
    npy_candidates = _metadata_npy_candidates(payload=payload, notebook_roots=notebook_roots)
    metadata_value = {
        "local_dem_rtc": bool(payload.get("LOCAL_DEM_RTC")),
        "pairs_used": payload.get("pairs_used"),
        "npy_outputs": sorted(npy_candidates),
        "stack_output": _metadata_output_available(payload, "stack"),
    }
    row = SarProcessingRow(
        check="notebook_radar_metadata",
        status="FOUND",
        band_name="",
        notebook_file=f"{metadata_file.root_label}:{metadata_file.relative_path}",
        app_file="",
        likely_cause="NOTEBOOK_PROCESSING_METADATA",
        raw_matching_percent=None,
        common_valid_matching_percent=None,
        mask_overlap_percent=None,
        mean_diff=None,
        median_diff=None,
        correlation=None,
        linear_slope=None,
        linear_intercept=None,
        evidence=(
            "Notebook QA_RADAR_META was parsed as local-only processing provenance: "
            f"{_compact_json(metadata_value)}."
        ),
        recommended_next_action=(
            "Use QA_RADAR_META output keys to avoid ambiguous SAR NPY wildcard mapping before changing SAR math."
        ),
    )
    return [row], npy_candidates, [metadata_file]


def _metadata_npy_candidates(*, payload: dict[str, Any], notebook_roots: list[Path]) -> dict[str, tuple[str, ...]]:
    outputs = payload.get("outputs")
    if not isinstance(outputs, dict):
        return {}
    npys = outputs.get("npys")
    if not isinstance(npys, dict):
        return {}
    band_key_map = {
        "VV_dB": "VV_dB",
        "VH_dB": "VH_dB",
        "logRatio_dB": "logRatio_dB",
        "angle": "incidence",
        "incidence": "incidence",
    }
    candidates: dict[str, list[str]] = {}
    for metadata_key, band_name in band_key_map.items():
        value = npys.get(metadata_key)
        if not isinstance(value, str) or not value:
            continue
        relative_path = _resolve_output_basename(notebook_roots=notebook_roots, output_value=value)
        if relative_path is not None:
            candidates.setdefault(band_name, []).append(relative_path)
    return {band_name: tuple(paths) for band_name, paths in candidates.items()}


def _metadata_output_available(payload: dict[str, Any], output_key: str) -> bool:
    outputs = payload.get("outputs")
    return isinstance(outputs, dict) and bool(outputs.get(output_key))


def _resolve_output_basename(*, notebook_roots: list[Path], output_value: str) -> str | None:
    output_name = output_value.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    if not output_name:
        return None
    matches: list[str] = []
    for root in notebook_roots:
        for path in root.rglob(output_name):
            if path.is_file() and path.name == output_name:
                matches.append(path.relative_to(root).as_posix())
    if not matches:
        return None
    return sorted(set(matches))[0]


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


def _build_pixel_probe_rows(band_arrays: dict[str, dict[str, Any]]) -> list[SarProcessingRow]:
    rows: list[SarProcessingRow] = []
    for band_name, containers in band_arrays.items():
        for container, payload in containers.items():
            notebook_array = _squeeze_array(payload["array"])
            app_array = _squeeze_array(payload["app_array"])
            if notebook_array.shape != app_array.shape or notebook_array.ndim != 2:
                rows.append(
                    SarProcessingRow(
                        check=f"pixel_probe_{band_name}_{container}",
                        status="NEEDS_MANUAL_REVIEW",
                        band_name=band_name,
                        notebook_file="",
                        app_file="",
                        likely_cause="PIXEL_PROBE_SHAPE_MISMATCH",
                        raw_matching_percent=None,
                        common_valid_matching_percent=None,
                        mask_overlap_percent=None,
                        mean_diff=None,
                        median_diff=None,
                        correlation=None,
                        linear_slope=None,
                        linear_intercept=None,
                        evidence=(
                            "Pixel probes require matching two-dimensional arrays; "
                            f"notebook_shape={list(notebook_array.shape)}; app_shape={list(app_array.shape)}."
                        ),
                        recommended_next_action="Inspect artifact shape and band mapping before interpreting pixel probes.",
                    )
                )
                continue
            rows.extend(
                _pixel_probe_rows_for_array(
                    band_name=band_name,
                    container=container,
                    notebook_array=notebook_array,
                    app_array=app_array,
                    notebook_nodata=payload["notebook_nodata"],
                    app_nodata=payload["app_nodata"],
                )
            )
    return rows


def _build_f20_delta_diagnostic_rows(band_arrays: dict[str, dict[str, Any]]) -> list[SarProcessingRow]:
    rows: list[SarProcessingRow] = []
    rows.extend(_build_edge_interior_rows(band_arrays))
    rows.extend(_build_nodata_edge_overlap_rows(band_arrays))
    rows.extend(_build_angle_delta_rows(band_arrays))
    rows.extend(_build_vv_vh_without_angle_delta_rows(band_arrays))
    return rows


def _build_edge_interior_rows(band_arrays: dict[str, dict[str, Any]]) -> list[SarProcessingRow]:
    rows: list[SarProcessingRow] = []
    for band_name, containers in band_arrays.items():
        for container, payload in containers.items():
            notebook_array = _squeeze_array(payload["array"])
            app_array = _squeeze_array(payload["app_array"])
            if notebook_array.shape != app_array.shape or notebook_array.ndim != 2:
                continue
            notebook_valid = _valid_mask(notebook_array, payload["notebook_nodata"])
            app_valid = _valid_mask(app_array, payload["app_nodata"])
            common_valid = notebook_valid & app_valid
            edge_mask = _edge_mask(notebook_array.shape) & common_valid
            interior_mask = (~_edge_mask(notebook_array.shape)) & common_valid
            edge_stats = _masked_delta_stats(notebook_array, app_array, edge_mask)
            interior_stats = _masked_delta_stats(notebook_array, app_array, interior_mask)
            edge_metrics = _masked_compare_metrics(notebook_array, app_array, edge_mask)
            interior_metrics = _masked_compare_metrics(notebook_array, app_array, interior_mask)
            rows.append(
                SarProcessingRow(
                    check=f"f20_edge_interior_{band_name}_{container}",
                    status="DIAGNOSTIC",
                    band_name=band_name,
                    notebook_file="",
                    app_file="",
                    likely_cause="EDGE_INTERIOR_DELTA_DIAGNOSTIC",
                    raw_matching_percent=edge_metrics.get("matching_percent"),
                    common_valid_matching_percent=interior_metrics.get("matching_percent"),
                    mask_overlap_percent=_mask_percent(edge_mask, common_valid),
                    mean_diff=edge_stats.get("mean_abs_diff"),
                    median_diff=interior_stats.get("median_abs_diff"),
                    correlation=None,
                    linear_slope=None,
                    linear_intercept=None,
                    evidence=(
                        f"Edge/interior delta diagnostic; edge_count={edge_stats['count']}; "
                        f"edge_mean_abs_diff={edge_stats['mean_abs_diff_text']}; edge_max_abs_diff={edge_stats['max_abs_diff_text']}; "
                        f"interior_count={interior_stats['count']}; interior_mean_abs_diff={interior_stats['mean_abs_diff_text']}; "
                        f"interior_max_abs_diff={interior_stats['max_abs_diff_text']}."
                    ),
                    recommended_next_action="If edge deltas dominate, inspect border masking, unmask, clip, and tile sampling before changing SAR math.",
                )
            )
    return rows


def _build_nodata_edge_overlap_rows(band_arrays: dict[str, dict[str, Any]]) -> list[SarProcessingRow]:
    rows: list[SarProcessingRow] = []
    for band_name, containers in band_arrays.items():
        for container, payload in containers.items():
            notebook_array = _squeeze_array(payload["array"])
            app_array = _squeeze_array(payload["app_array"])
            if notebook_array.shape != app_array.shape or notebook_array.ndim != 2:
                continue
            notebook_valid = _valid_mask(notebook_array, payload["notebook_nodata"])
            app_valid = _valid_mask(app_array, payload["app_nodata"])
            notebook_invalid = ~notebook_valid
            app_invalid = ~app_valid
            invalid_union = notebook_invalid | app_invalid
            invalid_overlap = notebook_invalid & app_invalid
            edge = _edge_mask(notebook_array.shape)
            rows.append(
                SarProcessingRow(
                    check=f"f20_nodata_edge_overlap_{band_name}_{container}",
                    status="DIAGNOSTIC",
                    band_name=band_name,
                    notebook_file="",
                    app_file="",
                    likely_cause="NODATA_EDGE_BORDER_MASK_DIAGNOSTIC",
                    raw_matching_percent=_mask_percent(notebook_valid == app_valid, np.ones(notebook_valid.shape, dtype=bool)),
                    common_valid_matching_percent=_mask_percent(notebook_valid & app_valid, np.ones(notebook_valid.shape, dtype=bool)),
                    mask_overlap_percent=_mask_percent(invalid_overlap, invalid_union),
                    mean_diff=None,
                    median_diff=None,
                    correlation=None,
                    linear_slope=None,
                    linear_intercept=None,
                    evidence=(
                        f"Nodata-edge overlap diagnostic; notebook_invalid_count={int(np.count_nonzero(notebook_invalid))}; "
                        f"app_invalid_count={int(np.count_nonzero(app_invalid))}; invalid_union_count={int(np.count_nonzero(invalid_union))}; "
                        f"invalid_overlap_count={int(np.count_nonzero(invalid_overlap))}; "
                        f"notebook_edge_invalid_count={int(np.count_nonzero(notebook_invalid & edge))}; "
                        f"app_edge_invalid_count={int(np.count_nonzero(app_invalid & edge))}; "
                        f"edge_invalid_overlap_count={int(np.count_nonzero(invalid_overlap & edge))}."
                    ),
                    recommended_next_action="If invalid pixels are edge-skewed or non-overlapping, inspect border masking, unmask, clip, and sample order.",
                )
            )
    return rows


def _build_angle_delta_rows(band_arrays: dict[str, dict[str, Any]]) -> list[SarProcessingRow]:
    rows: list[SarProcessingRow] = []
    for container, payload in band_arrays.get("incidence", {}).items():
        notebook_angle = _squeeze_array(payload["array"])
        app_incidence = _squeeze_array(payload["app_array"])
        if notebook_angle.shape != app_incidence.shape or notebook_angle.ndim != 2:
            continue
        common_valid = _valid_mask(notebook_angle, payload["notebook_nodata"]) & _valid_mask(app_incidence, payload["app_nodata"])
        deltas = np.abs(app_incidence.astype(np.float64, copy=False) - notebook_angle.astype(np.float64, copy=False))
        large_mask = common_valid & (deltas > ANGLE_LARGE_DELTA_DEGREES)
        edge_large_mask = large_mask & _edge_mask(notebook_angle.shape)
        stats = _masked_delta_stats(notebook_angle, app_incidence, common_valid)
        large_count = int(np.count_nonzero(large_mask))
        edge_large_count = int(np.count_nonzero(edge_large_mask))
        likely_cause = (
            "ANGLE_EDGE_OR_BORDER_DELTA"
            if large_count > 0 and large_count == edge_large_count
            else "ANGLE_DELTA_DISTRIBUTION"
        )
        rows.append(
            SarProcessingRow(
                check=f"f20_angle_delta_distribution_{container}",
                status="DIAGNOSTIC",
                band_name="incidence",
                notebook_file="",
                app_file="",
                likely_cause=likely_cause,
                raw_matching_percent=_mask_percent(common_valid & (deltas <= ANGLE_LARGE_DELTA_DEGREES), common_valid),
                common_valid_matching_percent=_mask_percent(edge_large_mask, large_mask),
                mask_overlap_percent=_mask_percent(common_valid, np.ones(common_valid.shape, dtype=bool)),
                mean_diff=stats.get("mean_abs_diff"),
                median_diff=stats.get("median_abs_diff"),
                correlation=None,
                linear_slope=None,
                linear_intercept=None,
                evidence=(
                    f"Angle delta distribution; common_valid_count={stats['count']}; "
                    f"large_delta_threshold_degrees={ANGLE_LARGE_DELTA_DEGREES}; "
                    f"large_delta_count={large_count}; "
                    f"edge_large_delta_count={edge_large_count}; "
                    f"delta_gt_{ANGLE_EDGE_DELTA_DEGREES:g}_count={int(np.count_nonzero(common_valid & (deltas > ANGLE_EDGE_DELTA_DEGREES)))}; "
                    f"mean_abs_diff={stats['mean_abs_diff_text']}; max_abs_diff={stats['max_abs_diff_text']}."
                ),
                recommended_next_action="If large angle deltas are edge-localized, inspect angle border mask and sampling/finalization order.",
            )
        )
    return rows


def _build_vv_vh_without_angle_delta_rows(band_arrays: dict[str, dict[str, Any]]) -> list[SarProcessingRow]:
    rows: list[SarProcessingRow] = []
    for container, angle_payload in band_arrays.get("incidence", {}).items():
        notebook_angle = _squeeze_array(angle_payload["array"])
        app_incidence = _squeeze_array(angle_payload["app_array"])
        if notebook_angle.shape != app_incidence.shape or notebook_angle.ndim != 2:
            continue
        angle_valid = _valid_mask(notebook_angle, angle_payload["notebook_nodata"]) & _valid_mask(app_incidence, angle_payload["app_nodata"])
        angle_delta = np.abs(app_incidence.astype(np.float64, copy=False) - notebook_angle.astype(np.float64, copy=False))
        low_angle_delta_mask = angle_valid & (angle_delta <= ANGLE_LARGE_DELTA_DEGREES)
        for band_name in ("VV_dB", "VH_dB", "logRatio_dB"):
            payload = band_arrays.get(band_name, {}).get(container)
            if payload is None:
                continue
            notebook_array = _squeeze_array(payload["array"])
            app_array = _squeeze_array(payload["app_array"])
            if notebook_array.shape != app_array.shape or notebook_array.shape != low_angle_delta_mask.shape:
                continue
            common_valid = (
                low_angle_delta_mask
                & _valid_mask(notebook_array, payload["notebook_nodata"])
                & _valid_mask(app_array, payload["app_nodata"])
            )
            metrics = _masked_compare_metrics(notebook_array, app_array, common_valid)
            stats = _masked_delta_stats(notebook_array, app_array, common_valid)
            rows.append(
                SarProcessingRow(
                    check=f"f20_{band_name}_excluding_angle_delta_{container}",
                    status="DIAGNOSTIC",
                    band_name=band_name,
                    notebook_file="",
                    app_file="",
                    likely_cause="SAR_DELTA_EXCLUDING_ANGLE_MISMATCH",
                    raw_matching_percent=metrics.get("matching_percent"),
                    common_valid_matching_percent=metrics.get("matching_percent"),
                    mask_overlap_percent=_mask_percent(common_valid, _valid_mask(notebook_array, payload["notebook_nodata"])),
                    mean_diff=stats.get("mean_abs_diff"),
                    median_diff=stats.get("median_abs_diff"),
                    correlation=None,
                    linear_slope=None,
                    linear_intercept=None,
                    evidence=(
                        f"{band_name} delta after excluding large angle-delta pixels; "
                        f"angle_delta_threshold_degrees={ANGLE_LARGE_DELTA_DEGREES}; "
                        f"comparison_count={stats['count']}; mean_abs_diff={stats['mean_abs_diff_text']}; "
                        f"max_abs_diff={stats['max_abs_diff_text']}; matching_percent={_stringify_number(metrics.get('matching_percent')) or 'n/a'}."
                    ),
                    recommended_next_action="If VV/VH deltas remain after excluding angle-delta pixels, inspect speckle filtering, border mask, aggregation, or sampling order.",
                )
            )
    return rows


def _edge_mask(shape: tuple[int, ...]) -> np.ndarray:
    height, width = int(shape[0]), int(shape[1])
    mask = np.zeros((height, width), dtype=bool)
    if height == 0 or width == 0:
        return mask
    mask[0, :] = True
    mask[-1, :] = True
    mask[:, 0] = True
    mask[:, -1] = True
    return mask


def _masked_compare_metrics(notebook_array: np.ndarray, app_array: np.ndarray, mask: np.ndarray) -> dict[str, Any]:
    if not np.any(mask):
        return {"pass": False, "matching_percent": None, "differing_count": None}
    return compare_arrays(
        notebook_array.astype(np.float64, copy=False)[mask],
        app_array.astype(np.float64, copy=False)[mask],
        tolerance=SAR_BAND_TOLERANCE,
    )


def _masked_delta_stats(notebook_array: np.ndarray, app_array: np.ndarray, mask: np.ndarray) -> dict[str, Any]:
    if not np.any(mask):
        return {
            "count": 0,
            "mean_abs_diff": None,
            "median_abs_diff": None,
            "max_abs_diff": None,
            "mean_abs_diff_text": "n/a",
            "median_abs_diff_text": "n/a",
            "max_abs_diff_text": "n/a",
        }
    delta = np.abs(
        app_array.astype(np.float64, copy=False)[mask]
        - notebook_array.astype(np.float64, copy=False)[mask]
    )
    mean_abs_diff = float(np.mean(delta))
    median_abs_diff = float(np.median(delta))
    max_abs_diff = float(np.max(delta))
    return {
        "count": int(delta.size),
        "mean_abs_diff": mean_abs_diff,
        "median_abs_diff": median_abs_diff,
        "max_abs_diff": max_abs_diff,
        "mean_abs_diff_text": f"{mean_abs_diff:.8f}",
        "median_abs_diff_text": f"{median_abs_diff:.8f}",
        "max_abs_diff_text": f"{max_abs_diff:.8f}",
    }


def _mask_percent(mask: np.ndarray, denominator_mask: np.ndarray) -> float | None:
    denominator = int(np.count_nonzero(denominator_mask))
    if denominator == 0:
        return None
    return round((int(np.count_nonzero(mask)) / denominator) * 100.0, 6)


def _pixel_probe_rows_for_array(
    *,
    band_name: str,
    container: str,
    notebook_array: np.ndarray,
    app_array: np.ndarray,
    notebook_nodata: float | None,
    app_nodata: float | None,
) -> list[SarProcessingRow]:
    height, width = notebook_array.shape
    probe_points = {
        "top_left": (0, 0),
        "top_right": (0, width - 1),
        "center": (height // 2, width // 2),
        "bottom_left": (height - 1, 0),
        "bottom_right": (height - 1, width - 1),
    }
    rows: list[SarProcessingRow] = []
    for label, (row_index, col_index) in probe_points.items():
        notebook_value = float(notebook_array[row_index, col_index])
        app_value = float(app_array[row_index, col_index])
        diff = app_value - notebook_value
        status = (
            "MATCH"
            if _values_match(notebook_value, app_value, notebook_nodata=notebook_nodata, app_nodata=app_nodata)
            else "DIAGNOSTIC"
        )
        rows.append(
            SarProcessingRow(
                check=f"pixel_probe_{band_name}_{container}_{label}",
                status=status,
                band_name=band_name,
                notebook_file="",
                app_file="",
                likely_cause="PIXEL_PROBE",
                raw_matching_percent=None,
                common_valid_matching_percent=None,
                mask_overlap_percent=None,
                mean_diff=diff,
                median_diff=None,
                correlation=None,
                linear_slope=None,
                linear_intercept=None,
                evidence=(
                    f"Relative pixel probe label={label}; row={row_index}; col={col_index}; "
                    f"notebook_value={_probe_value(notebook_value, notebook_nodata)}; "
                    f"app_value={_probe_value(app_value, app_nodata)}; diff={diff:.8f}."
                ),
                recommended_next_action="Use row/col probes to inspect center, edge, and corner deltas without spatial fields.",
            )
        )
    return rows


def _build_prior_comparison_rows(
    *,
    current_rows: list[SarProcessingRow],
    prior_report_path: Path,
) -> list[SarProcessingRow]:
    if not prior_report_path.is_file():
        return [
            SarProcessingRow(
                check="prior_report_comparison",
                status="MISSING",
                band_name="",
                notebook_file="",
                app_file="",
                likely_cause="MISSING_PRIOR_REPORT",
                raw_matching_percent=None,
                common_valid_matching_percent=None,
                mask_overlap_percent=None,
                mean_diff=None,
                median_diff=None,
                correlation=None,
                linear_slope=None,
                linear_intercept=None,
                evidence="Prior SAR processing report was requested but was not found.",
                recommended_next_action="Provide a previous local-only SAR processing report to assess improvement or regression.",
            )
        ]
    prior_payload = json.loads(prior_report_path.read_text(encoding="utf-8"))
    prior_rows = {
        str(row.get("check", "")): row
        for row in prior_payload.get("rows", [])
        if isinstance(row, dict) and row.get("check")
    }
    rows: list[SarProcessingRow] = []
    for current in current_rows:
        if current.check.startswith(("prior_", "pixel_probe_")):
            continue
        if current.raw_matching_percent is None and current.common_valid_matching_percent is None:
            continue
        prior = prior_rows.get(current.check)
        if prior is None:
            continue
        prior_score = _comparison_score(prior)
        current_score = _comparison_score(current.to_report_dict())
        if prior_score is None or current_score is None:
            status = "NEEDS_MANUAL_REVIEW"
            evidence = f"Prior/current numeric scores are not comparable for {current.check}."
        elif current_score > prior_score:
            status = "IMPROVED"
            evidence = f"{current.check} improved versus prior report: prior={prior_score:.8f}; current={current_score:.8f}."
        elif current_score < prior_score:
            status = "REGRESSED"
            evidence = f"{current.check} regressed versus prior report: prior={prior_score:.8f}; current={current_score:.8f}."
        else:
            status = "UNCHANGED"
            evidence = f"{current.check} is unchanged versus prior report: score={current_score:.8f}."
        rows.append(
            SarProcessingRow(
                check=f"prior_comparison_{current.check}",
                status=status,
                band_name=current.band_name,
                notebook_file="",
                app_file="",
                likely_cause="PRIOR_REPORT_COMPARISON",
                raw_matching_percent=current.raw_matching_percent,
                common_valid_matching_percent=current.common_valid_matching_percent,
                mask_overlap_percent=current.mask_overlap_percent,
                mean_diff=current.mean_diff,
                median_diff=current.median_diff,
                correlation=current.correlation,
                linear_slope=current.linear_slope,
                linear_intercept=current.linear_intercept,
                evidence=evidence,
                recommended_next_action="Use this trend only as diagnostic evidence; do not treat improvement as numeric parity.",
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


def _summary_delta(field: str, notebook_value: str, app_value: str) -> str:
    try:
        delta = float(app_value) - float(notebook_value)
    except ValueError:
        return f"{field}: notebook={notebook_value}, app={app_value}"
    return f"{field}: notebook={notebook_value}, app={app_value}, delta={delta:.8f}"


def _values_match(
    notebook_value: float,
    app_value: float,
    *,
    notebook_nodata: float | None,
    app_nodata: float | None,
) -> bool:
    notebook_is_nodata = notebook_nodata is not None and notebook_value == notebook_nodata
    app_is_nodata = app_nodata is not None and app_value == app_nodata
    if notebook_is_nodata or app_is_nodata:
        return notebook_is_nodata and app_is_nodata
    return bool(np.isclose(notebook_value, app_value, atol=SAR_BAND_TOLERANCE.abs_tol, rtol=SAR_BAND_TOLERANCE.rel_tol))


def _probe_value(value: float, nodata: float | None) -> str:
    if nodata is not None and value == nodata:
        return "nodata"
    return f"{value:.8f}"


def _comparison_score(row: dict[str, Any]) -> float | None:
    common_valid = row.get("common_valid_matching_percent")
    if common_valid not in (None, ""):
        return float(common_valid)
    raw = row.get("raw_matching_percent")
    if raw not in (None, ""):
        return float(raw)
    return None


def _compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


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
