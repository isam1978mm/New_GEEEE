from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.services.numeric_parity_report import (
    ComparisonSpec,
    compare_arrays,
    build_default_comparison_specs,
    load_raster_snapshot,
)

NUMERIC_PARITY_DIAGNOSIS_PREFIX = "numeric_parity_diagnosis"
DIAGNOSIS_FIELDNAMES = [
    "family",
    "notebook_file",
    "app_file",
    "original_status",
    "diagnosis_category",
    "evidence",
    "max_abs_diff",
    "mean_abs_diff",
    "differing_count",
    "matching_percent",
    "metadata_flags",
    "recommended_next_action",
    "safe_to_auto_reconcile",
]
APP_ONLY_PREFIXES = (
    "full_job/",
    "kmz/",
    "alignment_",
    "qa/parity/",
    "qa/stacks/",
    "qa/alignment/",
)


@dataclass(frozen=True, slots=True)
class NotebookMatch:
    root_label: str
    relative_path: str


@dataclass(frozen=True, slots=True)
class DiagnosisRow:
    family: str
    notebook_file: str
    app_file: str
    original_status: str
    diagnosis_category: str
    evidence: str
    max_abs_diff: float | None
    mean_abs_diff: float | None
    differing_count: int | None
    matching_percent: float | None
    metadata_flags: list[str]
    recommended_next_action: str
    safe_to_auto_reconcile: bool

    def to_report_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_csv_dict(self) -> dict[str, str]:
        payload = self.to_report_dict()
        payload["max_abs_diff"] = _stringify_number(self.max_abs_diff)
        payload["mean_abs_diff"] = _stringify_number(self.mean_abs_diff)
        payload["differing_count"] = "" if self.differing_count is None else str(self.differing_count)
        payload["matching_percent"] = _stringify_number(self.matching_percent)
        payload["metadata_flags"] = ",".join(self.metadata_flags)
        payload["safe_to_auto_reconcile"] = str(self.safe_to_auto_reconcile).lower()
        return {field: str(payload.get(field, "")) for field in DIAGNOSIS_FIELDNAMES}


def build_numeric_parity_diagnosis_report(
    parity_report_path: Path,
    app_run_dir: Path,
    notebook_roots: list[Path],
) -> dict[str, Any]:
    parity_report = json.loads(parity_report_path.read_text(encoding="utf-8"))
    specs_by_app_file = {spec.app_file: spec for spec in build_default_comparison_specs()}
    root_labels = [root.name for root in notebook_roots]
    rows = [
        diagnose_row(
            row,
            app_run_dir=app_run_dir,
            notebook_roots=notebook_roots,
            specs_by_app_file=specs_by_app_file,
        )
        for row in parity_report["rows"]
    ]
    diagnosis_counts: dict[str, int] = {}
    original_status_counts: dict[str, int] = {}
    for row in rows:
        diagnosis_counts[row.diagnosis_category] = diagnosis_counts.get(row.diagnosis_category, 0) + 1
        original_status_counts[row.original_status] = original_status_counts.get(row.original_status, 0) + 1
    return {
        "report_type": "numeric_parity_diagnosis",
        "artifact_class": "FILESYSTEM_ONLY",
        "local_only": True,
        "parity_report_label": parity_report_path.name,
        "app_run_id": app_run_dir.name,
        "notebook_root_labels": root_labels,
        "rows": [row.to_report_dict() for row in rows],
        "summary": {
            "row_count": len(rows),
            "diagnosis_counts": diagnosis_counts,
            "original_status_counts": original_status_counts,
        },
    }


def write_numeric_parity_diagnosis_report(
    *,
    parity_report_path: Path,
    app_run_dir: Path,
    notebook_roots: list[Path],
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_numeric_parity_diagnosis_report(
        parity_report_path=parity_report_path,
        app_run_dir=app_run_dir,
        notebook_roots=notebook_roots,
    )
    stem = f"{NUMERIC_PARITY_DIAGNOSIS_PREFIX}_{app_run_dir.name}"
    json_path = output_dir / f"{stem}.json"
    csv_path = output_dir / f"{stem}.csv"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DIAGNOSIS_FIELDNAMES)
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow(DiagnosisRow(**row).to_csv_dict())
    return json_path, csv_path


def diagnose_row(
    row: dict[str, Any],
    *,
    app_run_dir: Path,
    notebook_roots: list[Path],
    specs_by_app_file: dict[str, ComparisonSpec],
) -> DiagnosisRow:
    app_file = str(row.get("app_file", ""))
    notebook_file = str(row.get("notebook_file", ""))
    spec = specs_by_app_file.get(app_file)
    app_exists = (app_run_dir / app_file).is_file()
    notebook_matches = find_notebook_matches(
        notebook_file=notebook_file,
        spec=spec,
        notebook_roots=notebook_roots,
    )
    metadata_flags = parse_metadata_flags(str(row.get("notes", "")))
    normalized_evidence = build_normalized_evidence(
        row=row,
        app_run_dir=app_run_dir,
        notebook_roots=notebook_roots,
        notebook_matches=notebook_matches,
    )

    original_status = str(row["status"])
    if original_status == "PASS":
        return DiagnosisRow(
            family=str(row["family"]),
            notebook_file=notebook_file,
            app_file=app_file,
            original_status=original_status,
            diagnosis_category="PASS_CONFIRMED",
            evidence="Parity row passed as generated.",
            max_abs_diff=_as_float(row.get("max_abs_diff")),
            mean_abs_diff=_as_float(row.get("mean_abs_diff")),
            differing_count=_as_int(row.get("differing_count")),
            matching_percent=_as_float(row.get("matching_percent")),
            metadata_flags=metadata_flags,
            recommended_next_action="No action required.",
            safe_to_auto_reconcile=False,
        )
    if original_status == "SKIP_MISSING_APP":
        return _build_row(
            row,
            diagnosis_category="SKIP_APP_FILE_NOT_FOUND",
            metadata_flags=metadata_flags,
            evidence="The app artifact is absent from the provided run directory.",
            recommended_next_action="Generate the missing app artifact or confirm it is intentionally absent.",
            safe=False,
        )
    if original_status == "SKIP_UNSUPPORTED_CONTAINER":
        return _build_row(
            row,
            diagnosis_category="SKIP_UNSUPPORTED_CONTAINER",
            metadata_flags=metadata_flags,
            evidence="The parity tool could not read this container type.",
            recommended_next_action="Add a supported comparison or diagnostic handler for this container.",
            safe=False,
        )
    if original_status == "SKIP_MISSING_NOTEBOOK":
        return diagnose_missing_notebook_row(
            row,
            app_exists=app_exists,
            notebook_matches=notebook_matches,
            spec=spec,
            metadata_flags=metadata_flags,
            primary_root_label=notebook_roots[0].name if notebook_roots else "",
        )
    return diagnose_fail_row(
        row,
        metadata_flags=metadata_flags,
        normalized_evidence=normalized_evidence,
    )


def diagnose_missing_notebook_row(
    row: dict[str, Any],
    *,
    app_exists: bool,
    notebook_matches: list[NotebookMatch],
    spec: ComparisonSpec | None,
    metadata_flags: list[str],
    primary_root_label: str,
) -> DiagnosisRow:
    app_file = str(row["app_file"])
    if not app_exists:
        return _build_row(
            row,
            diagnosis_category="SKIP_APP_FILE_NOT_FOUND",
            metadata_flags=metadata_flags,
            evidence="The app artifact is absent from the provided run directory.",
            recommended_next_action="Generate the missing app artifact or confirm it is intentionally absent.",
            safe=False,
        )
    if notebook_matches:
        root_labels = sorted({match.root_label for match in notebook_matches})
        category = (
            "NEEDS_MULTI_ROOT_SEARCH"
            if any(match.root_label != primary_root_label for match in notebook_matches)
            else "SKIP_UNMAPPED_OUTPUT"
        )
        evidence = (
            "Matching notebook files were found under alternate root labels: "
            + ", ".join(sorted({match.root_label for match in notebook_matches if match.root_label != primary_root_label}))
            if category == "NEEDS_MULTI_ROOT_SEARCH"
            else "Matching notebook files are present in the provided roots but were skipped by the original report."
        )
        next_action = (
            "Rerun parity with all notebook roots provided."
            if category == "NEEDS_MULTI_ROOT_SEARCH"
            else "Rerun parity after refreshing notebook-to-app mappings."
        )
        return _build_row(
            row,
            diagnosis_category=category,
            metadata_flags=metadata_flags,
            evidence=evidence,
            recommended_next_action=next_action,
            safe=True,
        )
    if spec is None or is_app_only_output(app_file):
        return _build_row(
            row,
            diagnosis_category="SKIP_UNMAPPED_OUTPUT",
            metadata_flags=metadata_flags,
            evidence="No notebook-equivalent file was found for this app-local output.",
            recommended_next_action="Leave the output app-only unless a notebook-equivalent artifact is explicitly identified.",
            safe=False,
        )
    return _build_row(
        row,
        diagnosis_category="SKIP_NOTEBOOK_FILE_NOT_FOUND",
        metadata_flags=metadata_flags,
        evidence="No matching notebook file was found in the provided notebook roots.",
        recommended_next_action="Provide the missing notebook output root or confirm that the notebook never produced this artifact.",
        safe=False,
    )


def diagnose_fail_row(
    row: dict[str, Any],
    *,
    metadata_flags: list[str],
    normalized_evidence: str,
) -> DiagnosisRow:
    app_file = str(row["app_file"])
    family = str(row["family"])
    differing_count = _as_int(row.get("differing_count"))
    matching_percent = _as_float(row.get("matching_percent"))
    notes = str(row.get("notes", ""))

    if row.get("shape_match") is False:
        return _build_row(
            row,
            diagnosis_category="FAIL_SHAPE_MISMATCH",
            metadata_flags=metadata_flags,
            evidence=_join_evidence("Shape mismatch blocks direct numeric parity.", normalized_evidence),
            recommended_next_action="Verify GRID lock, width, height, and band count before comparing values.",
            safe=False,
        )
    if family == "focus_zone_local" and differing_count is not None and differing_count < 10:
        return _build_row(
            row,
            diagnosis_category="NEEDS_MANUAL_REVIEW",
            metadata_flags=metadata_flags,
            evidence=_join_evidence(
                f"Focus-mask row is a near-match with only {differing_count} differing pixels.",
                normalized_evidence,
            ),
            recommended_next_action="Inspect boundary and mask-encoding behavior before changing code or tolerances.",
            safe=False,
        )
    if family == "radar_tensor_stack":
        return _build_row(
            row,
            diagnosis_category="FAIL_BAND_ORDER_OR_STACK_ORDER",
            metadata_flags=metadata_flags,
            evidence=_join_evidence(
                "Radar stack shape matches but the stack content diverges strongly, which is consistent with band-order or stack-order mismatch.",
                normalized_evidence,
            ),
            recommended_next_action="Compare notebook and app stack channel ordering and stack manifests before changing science logic.",
            safe=True,
        )
    if family in {"sar_geotiff_bands", "sar_npy_bands"}:
        evidence = "SAR row has matching shape and dtype but near-zero agreement, consistent with source selection, orbit pairing, filtering, RTC, or downstream mismatch."
        if "logRatio" in app_file:
            evidence = "logRatio mismatch mirrors the upstream SAR band mismatch and should be treated as downstream SAR divergence."
        elif "incidence" in app_file or "angle" in app_file:
            evidence = "Incidence-angle mismatch tracks the same SAR source-selection path and is not yet evidence of an independent bug."
        return _build_row(
            row,
            diagnosis_category="FAIL_SOURCE_SELECTION_MISMATCH",
            metadata_flags=metadata_flags,
            evidence=_join_evidence(evidence, normalized_evidence),
            recommended_next_action="Inspect notebook/app SAR source selection, orbit pairing, filtering, and RTC path before changing formulas.",
            safe=False,
        )
    if "dtype_mismatch" in notes and matching_percent is not None and matching_percent > 99.9:
        return _build_row(
            row,
            diagnosis_category="FAIL_DTYPE_MISMATCH",
            metadata_flags=metadata_flags,
            evidence=_join_evidence("The row is numerically near-identical apart from dtype or mask encoding.", normalized_evidence),
            recommended_next_action="Normalize dtype or mask encoding and rerun parity before changing algorithms.",
            safe=True,
        )
    if "nodata_policy_mismatch" in notes and matching_percent is not None and matching_percent >= 90.0:
        return _build_row(
            row,
            diagnosis_category="FAIL_NODATA_POLICY_MISMATCH",
            metadata_flags=metadata_flags,
            evidence=_join_evidence("The row is mostly aligned and the mismatch is likely dominated by nodata handling.", normalized_evidence),
            recommended_next_action="Apply nodata-normalized comparison first, then re-evaluate whether any algorithm mismatch remains.",
            safe=True,
        )
    if metadata_flags:
        return _build_row(
            row,
            diagnosis_category="FAIL_METADATA_MISMATCH",
            metadata_flags=metadata_flags,
            evidence=_join_evidence("Raster georeferencing metadata is missing or mismatched in the notebook artifact.", normalized_evidence),
            recommended_next_action="Capture notebook CRS/transform metadata or compare with a documented metadata-normalized path before changing science logic.",
            safe=True,
        )
    if family == "dem_derivatives":
        return _build_row(
            row,
            diagnosis_category="FAIL_ALGORITHM_MISMATCH",
            metadata_flags=metadata_flags,
            evidence=_join_evidence("DEM derivative values diverge beyond metadata and nodata reporting.", normalized_evidence),
            recommended_next_action="Inspect derivative implementation only after ruling out source, metadata, and nodata differences.",
            safe=False,
        )
    return _build_row(
        row,
        diagnosis_category="FAIL_NUMERIC_MISMATCH",
        metadata_flags=metadata_flags,
        evidence=_join_evidence("The row still fails after direct comparison.", normalized_evidence),
        recommended_next_action="Inspect the producing stage and inputs before changing tolerances.",
        safe=False,
    )


def find_notebook_matches(
    *,
    notebook_file: str,
    spec: ComparisonSpec | None,
    notebook_roots: list[Path],
) -> list[NotebookMatch]:
    matches: list[NotebookMatch] = []
    candidates: list[str] = []
    if notebook_file:
        candidates.append(notebook_file)
    if spec is not None:
        candidates.extend(candidate for candidate in spec.notebook_candidates if candidate not in candidates)
    for root in notebook_roots:
        root_label = root.name
        for candidate in candidates:
            exact_path = root / candidate
            if exact_path.is_file():
                matches.append(NotebookMatch(root_label=root_label, relative_path=candidate.replace("\\", "/")))
                continue
            for path in root.rglob("*"):
                if path.is_file() and _match_candidate(path.relative_to(root).as_posix(), candidate):
                    matches.append(NotebookMatch(root_label=root_label, relative_path=path.relative_to(root).as_posix()))
    unique_matches: dict[tuple[str, str], NotebookMatch] = {
        (match.root_label, match.relative_path): match for match in matches
    }
    return list(unique_matches.values())


def build_normalized_evidence(
    *,
    row: dict[str, Any],
    app_run_dir: Path,
    notebook_roots: list[Path],
    notebook_matches: list[NotebookMatch],
) -> str:
    comparison_type = str(row.get("comparison_type", ""))
    app_file = str(row.get("app_file", ""))
    if comparison_type != "raster" or not notebook_matches:
        return ""
    app_path = app_run_dir / app_file
    if not app_path.is_file():
        return ""
    preferred_match = notebook_matches[0]
    notebook_root = next((root for root in notebook_roots if root.name == preferred_match.root_label), None)
    if notebook_root is None:
        return ""
    notebook_path = notebook_root / preferred_match.relative_path
    if not notebook_path.is_file():
        return ""
    try:
        notebook_raster = load_raster_snapshot(notebook_path)
        app_raster = load_raster_snapshot(app_path)
    except Exception:
        return ""
    prepared_arrays = _prepare_nodata_normalization_arrays(notebook_raster.array, app_raster.array)
    if prepared_arrays is None:
        return "Nodata-normalized evidence skipped because raster shapes or band counts differ."
    notebook_array, app_array = prepared_arrays
    notebook_mask = _valid_mask(notebook_array, notebook_raster.nodata)
    app_mask = _valid_mask(app_array, app_raster.nodata)
    overlap_mask = notebook_mask & app_mask
    if not overlap_mask.any():
        return "No overlapping valid pixels remain after nodata normalization."
    notebook_values = notebook_array[overlap_mask]
    app_values = app_array[overlap_mask]
    normalized = compare_arrays(notebook_values, app_values, tolerance=spec_tolerance_for_row(row))
    return (
        f"Nodata-normalized overlap has matching_percent={normalized['matching_percent']:.6f} "
        f"with differing_count={normalized['differing_count']}."
    )


def spec_tolerance_for_row(row: dict[str, Any]):
    tolerance = row.get("tolerance_used") or {}
    abs_tol = float(tolerance.get("abs_tol", 1e-5))
    rel_tol = float(tolerance.get("rel_tol", 1e-5))
    from app.services.numeric_parity_report import Tolerance

    return Tolerance(abs_tol=abs_tol, rel_tol=rel_tol)


def parse_metadata_flags(notes: str) -> list[str]:
    flags: list[str] = []
    for item in notes.replace(";", ",").split(","):
        token = item.strip()
        if token.startswith("missing_") or token.endswith("_mismatch"):
            flags.append(token)
    return flags


def is_app_only_output(app_file: str) -> bool:
    if app_file.startswith(APP_ONLY_PREFIXES):
        return True
    if app_file in {
        "hypercube_band_order.csv",
        "hypercube_band_stats.csv",
        "hypercube_norm_params.csv",
        "alignment_qa.json",
        "qa/sar/sar_summary.csv",
    }:
        return False
    return False


def _build_row(
    row: dict[str, Any],
    *,
    diagnosis_category: str,
    metadata_flags: list[str],
    evidence: str,
    recommended_next_action: str,
    safe: bool,
) -> DiagnosisRow:
    return DiagnosisRow(
        family=str(row["family"]),
        notebook_file=str(row.get("notebook_file", "")),
        app_file=str(row.get("app_file", "")),
        original_status=str(row["status"]),
        diagnosis_category=diagnosis_category,
        evidence=evidence,
        max_abs_diff=_as_float(row.get("max_abs_diff")),
        mean_abs_diff=_as_float(row.get("mean_abs_diff")),
        differing_count=_as_int(row.get("differing_count")),
        matching_percent=_as_float(row.get("matching_percent")),
        metadata_flags=metadata_flags,
        recommended_next_action=recommended_next_action,
        safe_to_auto_reconcile=safe,
    )


def _valid_mask(array: np.ndarray, nodata: float | None) -> np.ndarray:
    mask = np.isfinite(array)
    if nodata is not None:
        mask &= array != nodata
    return mask


def _prepare_nodata_normalization_arrays(
    notebook_array: np.ndarray,
    app_array: np.ndarray,
) -> tuple[np.ndarray, np.ndarray] | None:
    if notebook_array.shape == app_array.shape:
        return notebook_array, app_array
    notebook_single = _squeeze_single_band_array(notebook_array)
    app_single = _squeeze_single_band_array(app_array)
    if notebook_single is not None and app_single is not None and notebook_single.shape == app_single.shape:
        return notebook_single, app_single
    return None


def _squeeze_single_band_array(array: np.ndarray) -> np.ndarray | None:
    if array.ndim == 2:
        return array
    if array.ndim == 3 and array.shape[0] == 1:
        return array[0]
    return None


def _match_candidate(relative_path: str, candidate: str) -> bool:
    import fnmatch

    return fnmatch.fnmatch(relative_path, candidate)


def _join_evidence(*parts: str) -> str:
    return " ".join(part for part in parts if part)


def _stringify_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.8f}"


def _as_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    return float(value)


def _as_int(value: Any) -> int | None:
    if value in ("", None):
        return None
    return int(value)
