from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
import rasterio


OutcomeStatus = Literal["pass", "fail", "xfail", "config_required"]
CaseKind = Literal["raster_alias", "npy_alias", "raster_reference", "npy_reference", "report_not_implemented"]


@dataclass(frozen=True, slots=True)
class Phase5Case:
    group: str
    label: str
    kind: CaseKind
    left_path: str
    right_path: str | None = None
    tolerance: float = 0.0
    expected: Literal["pass", "xfail"] = "pass"
    xfail_reason: str = ""
    allow_validmask_representation_diff: bool = False


@dataclass(frozen=True, slots=True)
class CaseResult:
    group: str
    label: str
    kind: CaseKind
    expected: str
    status: OutcomeStatus
    classification: str | None = None
    message: str | None = None
    max_error: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PHASE5D_ALIAS_CASES: tuple[Phase5Case, ...] = (
    Phase5Case("dem", "DEM_640 alias", "raster_alias", "DEM_GEO8_TIFS/DEM_640.tif", "dem.tif"),
    Phase5Case("dem", "slope alias", "raster_alias", "DEM_GEO8_TIFS/slope_deg_640.tif", "slope.tif"),
    Phase5Case("dem", "aspect alias", "raster_alias", "DEM_GEO8_TIFS/aspect_deg_640.tif", "aspect.tif"),
    Phase5Case("dem", "roughness alias", "raster_alias", "DEM_GEO8_TIFS/roughness_100m_640.tif", "roughness.tif"),
    Phase5Case("dem", "tpi alias", "raster_alias", "DEM_GEO8_TIFS/tpi_100m_640.tif", "TPI.tif"),
    Phase5Case("sar_geotiff", "VV_dB alias", "raster_alias", "GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_app.tif", "VV_dB.tif"),
    Phase5Case("sar_geotiff", "VH_dB alias", "raster_alias", "GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_app.tif", "VH_dB.tif"),
    Phase5Case("sar_geotiff", "logRatio_dB alias", "raster_alias", "GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_app.tif", "logRatio_dB.tif"),
    Phase5Case("sar_geotiff", "angle alias", "raster_alias", "GEOTIFF_RADAR_BANDS/RADAR_angle_640_app.tif", "incidence.tif"),
    Phase5Case("sar_npy", "VV_dB npy alias", "npy_alias", "NPY_RADAR_BANDS/RADAR_VV_dB_640_app.npy", "npy_radar_bands/VV_dB.npy"),
    Phase5Case("sar_npy", "VH_dB npy alias", "npy_alias", "NPY_RADAR_BANDS/RADAR_VH_dB_640_app.npy", "npy_radar_bands/VH_dB.npy"),
    Phase5Case("sar_npy", "logRatio_dB npy alias", "npy_alias", "NPY_RADAR_BANDS/RADAR_logRatio_dB_640_app.npy", "npy_radar_bands/logRatio_dB.npy"),
    Phase5Case("sar_npy", "angle npy alias", "npy_alias", "NPY_RADAR_BANDS/RADAR_angle_640_app.npy", "npy_radar_bands/incidence.npy"),
    Phase5Case("stacks", "hypercube tif alias", "raster_alias", "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif", "hypercube.tif"),
    Phase5Case("stacks", "hypercube npy alias", "npy_alias", "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy", "hypercube.npy"),
    Phase5Case("stacks", "radar stack alias", "npy_alias", "NPY_STACKS/RADAR_STACK_HWC_640_app.npy", "stacks/tensor_support/radar_linear_support_stack.npy"),
    Phase5Case("qa_post_rtc", "post_rtc VV_dB alias", "npy_alias", "QA/sar/intermediates/post_rtc/final_VV_dB.npy", "npy_radar_bands/VV_dB.npy"),
    Phase5Case("qa_post_rtc", "post_rtc VH_dB alias", "npy_alias", "QA/sar/intermediates/post_rtc/final_VH_dB.npy", "npy_radar_bands/VH_dB.npy"),
    Phase5Case("qa_post_rtc", "post_rtc logRatio alias", "npy_alias", "QA/sar/intermediates/post_rtc/final_logRatio_dB.npy", "npy_radar_bands/logRatio_dB.npy"),
    Phase5Case("qa_post_rtc", "post_rtc angle alias", "npy_alias", "QA/sar/intermediates/post_rtc/final_angle.npy", "npy_radar_bands/incidence.npy"),
)

PHASE5E_REFERENCE_CASES: tuple[Phase5Case, ...] = (
    Phase5Case("dem", "DEM_640 reference", "raster_reference", "DEM_GEO8_TIFS/DEM_640.tif", "DEM_GEO8_TIFS/DEM_640.tif", tolerance=1e-5),
    Phase5Case("dem", "slope reference", "raster_reference", "DEM_GEO8_TIFS/slope_deg_640.tif", "DEM_GEO8_TIFS/slope_deg_640.tif", tolerance=1e-4),
    Phase5Case("dem", "aspect reference", "raster_reference", "DEM_GEO8_TIFS/aspect_deg_640.tif", "DEM_GEO8_TIFS/aspect_deg_640.tif", tolerance=1e-4),
    Phase5Case("dem", "roughness reference", "raster_reference", "DEM_GEO8_TIFS/roughness_100m_640.tif", "DEM_GEO8_TIFS/roughness_100m_640.tif", tolerance=1e-4),
    Phase5Case("dem", "tpi reference", "raster_reference", "DEM_GEO8_TIFS/tpi_100m_640.tif", "DEM_GEO8_TIFS/tpi_100m_640.tif", tolerance=1e-4),
    Phase5Case(
        "dem",
        "hillshade reference",
        "raster_reference",
        "DEM_GEO8_TIFS/hillshade_0to1_640.tif",
        "DEM_GEO8_TIFS/hillshade_0to1_640.tif",
        expected="xfail",
        xfail_reason="known hillshade numeric mismatch",
    ),
    Phase5Case("sar", "VV_dB geotiff reference", "raster_reference", "GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_app.tif", "GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_", tolerance=1e-4),
    Phase5Case("sar", "VH_dB geotiff reference", "raster_reference", "GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_app.tif", "GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_", tolerance=1e-4),
    Phase5Case("sar", "logRatio geotiff reference", "raster_reference", "GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_app.tif", "GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_", tolerance=1e-4),
    Phase5Case("sar", "angle geotiff reference", "raster_reference", "GEOTIFF_RADAR_BANDS/RADAR_angle_640_app.tif", "GEOTIFF_RADAR_BANDS/RADAR_angle_640_", tolerance=1e-4),
    Phase5Case("sar", "VV_dB npy reference", "npy_reference", "NPY_RADAR_BANDS/RADAR_VV_dB_640_app.npy", "NPY_RADAR_BANDS/RADAR_VV_dB_640_", tolerance=1e-4),
    Phase5Case("sar", "VH_dB npy reference", "npy_reference", "NPY_RADAR_BANDS/RADAR_VH_dB_640_app.npy", "NPY_RADAR_BANDS/RADAR_VH_dB_640_", tolerance=1e-4),
    Phase5Case("sar", "logRatio npy reference", "npy_reference", "NPY_RADAR_BANDS/RADAR_logRatio_dB_640_app.npy", "NPY_RADAR_BANDS/RADAR_logRatio_dB_640_", tolerance=1e-4),
    Phase5Case("sar", "angle npy reference", "npy_reference", "NPY_RADAR_BANDS/RADAR_angle_640_app.npy", "NPY_RADAR_BANDS/RADAR_angle_640_", tolerance=1e-4),
    Phase5Case(
        "stacks",
        "hypercube tif reference",
        "raster_reference",
        "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif",
        "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif",
        expected="xfail",
        xfail_reason="known hypercube band-count mismatch",
    ),
    Phase5Case(
        "stacks",
        "hypercube npy reference",
        "npy_reference",
        "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy",
        "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy",
        expected="xfail",
        xfail_reason="known hypercube layout mismatch",
    ),
    Phase5Case(
        "stacks",
        "radar stack reference",
        "npy_reference",
        "NPY_STACKS/RADAR_STACK_HWC_640_app.npy",
        "NPY_STACKS/RADAR_STACK_HWC_640_",
        expected="xfail",
        xfail_reason="known radar stack numeric mismatch",
    ),
    Phase5Case("qa", "QA dx reference", "raster_reference", "QA/QA_GRID_dx_m_640.tif", "QA/QA_GRID_dx_m_640.tif", allow_validmask_representation_diff=False),
    Phase5Case("qa", "QA dy reference", "raster_reference", "QA/QA_GRID_dy_m_640.tif", "QA/QA_GRID_dy_m_640.tif", allow_validmask_representation_diff=False),
    Phase5Case("qa", "QA validmask reference", "raster_reference", "QA/QA_GRID_validmask_640.tif", "QA/QA_GRID_validmask_640.tif", allow_validmask_representation_diff=True),
    Phase5Case(
        "qa",
        "post_rtc VV_dB reference",
        "npy_reference",
        "QA/sar/intermediates/post_rtc/final_VV_dB.npy",
        "QA/sar/intermediates/post_rtc/final_VV_dB.npy",
        tolerance=1e-4,
        expected="xfail",
        xfail_reason="known post-RTC numeric mismatch",
    ),
    Phase5Case(
        "qa",
        "post_rtc VH_dB reference",
        "npy_reference",
        "QA/sar/intermediates/post_rtc/final_VH_dB.npy",
        "QA/sar/intermediates/post_rtc/final_VH_dB.npy",
        tolerance=1e-4,
        expected="xfail",
        xfail_reason="known post-RTC numeric mismatch",
    ),
    Phase5Case(
        "qa",
        "post_rtc logRatio reference",
        "npy_reference",
        "QA/sar/intermediates/post_rtc/final_logRatio_dB.npy",
        "QA/sar/intermediates/post_rtc/final_logRatio_dB.npy",
        tolerance=1e-4,
        expected="xfail",
        xfail_reason="known post-RTC numeric mismatch",
    ),
    Phase5Case(
        "qa",
        "post_rtc angle reference",
        "npy_reference",
        "QA/sar/intermediates/post_rtc/final_angle.npy",
        "QA/sar/intermediates/post_rtc/final_angle.npy",
        tolerance=1e-4,
        expected="xfail",
        xfail_reason="known post-RTC numeric mismatch",
    ),
)

REPORT_640_OUTPUTS = (
    "REPORT_640_Pottery_Report.tif",
    "REPORT_640_Mass_Report.tif",
    "REPORT_640_FINAL_Zero_Point_Targets.tif",
)


def build_phase5_numeric_output_parity_summary(
    *,
    app_run_dir: Path | None,
    notebook_reference_bundle_dir: Path | None,
    alias_cases: tuple[Phase5Case, ...] = PHASE5D_ALIAS_CASES,
    reference_cases: tuple[Phase5Case, ...] = PHASE5E_REFERENCE_CASES,
) -> dict[str, Any]:
    prerequisites = {
        "app_notebook_output_run_dir_configured": app_run_dir is not None,
        "notebook_reference_bundle_dir_configured": notebook_reference_bundle_dir is not None,
        "app_run_dir_exists": bool(app_run_dir and app_run_dir.is_dir()),
        "reference_bundle_exists": bool(notebook_reference_bundle_dir and notebook_reference_bundle_dir.is_dir()),
    }
    if not all(prerequisites.values()):
        return {
            "report_type": "phase5_numeric_output_parity_summary",
            "local_only": True,
            "summary": {
                "overall_status": "CONFIG_REQUIRED",
                "phase5d_alias_integrity_status": "CONFIG_REQUIRED",
                "phase5e_reference_parity_status": "CONFIG_REQUIRED",
                "not_implemented_inventory_status": "CONFIG_REQUIRED",
                "final_reference_proof_complete": False,
            },
            "prerequisites": prerequisites,
            "phase5d_alias_integrity": {"status": "CONFIG_REQUIRED", "cases": []},
            "phase5e_reference_parity": {"status": "CONFIG_REQUIRED", "cases": []},
            "known_not_implemented_outputs": {"status": "CONFIG_REQUIRED", "entries": []},
        }

    assert app_run_dir is not None
    assert notebook_reference_bundle_dir is not None

    alias_results = [_evaluate_case(case, app_run_dir=app_run_dir, notebook_root=app_run_dir) for case in alias_cases]
    reference_results = [
        _evaluate_case(case, app_run_dir=app_run_dir, notebook_root=notebook_reference_bundle_dir) for case in reference_cases
    ]
    not_implemented = _evaluate_report_not_implemented(app_run_dir)

    alias_status = _aggregate_case_status(alias_results, allow_expected_xfails=False)
    reference_status = _aggregate_case_status(reference_results, allow_expected_xfails=True)
    not_implemented_status = "PASS" if all(entry["status"] == "not_implemented_no_source_equivalent" for entry in not_implemented) else "FAIL"

    overall_status = (
        "PASS_WITH_CLASSIFIED_EXCEPTIONS"
        if alias_status == "PASS" and reference_status == "PASS_WITH_CLASSIFIED_EXCEPTIONS" and not_implemented_status == "PASS"
        else "FAIL"
    )
    return {
        "report_type": "phase5_numeric_output_parity_summary",
        "local_only": True,
        "app_run_id": app_run_dir.name,
        "reference_bundle_label": notebook_reference_bundle_dir.name,
        "summary": {
            "overall_status": overall_status,
            "phase5d_alias_integrity_status": alias_status,
            "phase5e_reference_parity_status": reference_status,
            "not_implemented_inventory_status": not_implemented_status,
            "final_reference_proof_complete": overall_status == "PASS",
        },
        "prerequisites": prerequisites,
        "phase5d_alias_integrity": {
            "status": alias_status,
            "case_counts": _count_statuses(alias_results),
            "cases": [result.to_dict() for result in alias_results],
        },
        "phase5e_reference_parity": {
            "status": reference_status,
            "case_counts": _count_statuses(reference_results),
            "cases": [result.to_dict() for result in reference_results],
        },
        "known_not_implemented_outputs": {
            "status": not_implemented_status,
            "entries": not_implemented,
        },
    }


def _evaluate_case(case: Phase5Case, *, app_run_dir: Path, notebook_root: Path) -> CaseResult:
    left_path = app_run_dir / case.left_path
    if not left_path.is_file():
        return CaseResult(case.group, case.label, case.kind, case.expected, "config_required", "missing_app_file", case.left_path)

    if case.kind in {"raster_alias", "npy_alias"}:
        assert case.right_path is not None
        right_path = app_run_dir / case.right_path
        if not right_path.is_file():
            return CaseResult(case.group, case.label, case.kind, case.expected, "config_required", "missing_alias_source", case.right_path)
    else:
        assert case.right_path is not None
        right_path = _resolve_reference_path(notebook_root, case)
        if right_path is None:
            return CaseResult(case.group, case.label, case.kind, case.expected, "config_required", "missing_reference_file", case.right_path)

    if case.kind in {"raster_alias", "raster_reference"}:
        comparison = _compare_rasters(left_path, right_path, case)
    else:
        comparison = _compare_npy(left_path, right_path, case.tolerance)

    actual_status = "pass" if comparison["pass"] else "fail"
    if case.expected == "pass":
        return CaseResult(case.group, case.label, case.kind, case.expected, actual_status, comparison.get("classification"), comparison.get("message"), comparison.get("max_error"))
    if actual_status == "fail":
        return CaseResult(case.group, case.label, case.kind, case.expected, "xfail", comparison.get("classification"), case.xfail_reason, comparison.get("max_error"))
    return CaseResult(case.group, case.label, case.kind, case.expected, "fail", "unexpected_pass", f"Expected xfail but comparison passed for {case.label}.", comparison.get("max_error"))


def _resolve_reference_path(notebook_root: Path, case: Phase5Case) -> Path | None:
    assert case.right_path is not None
    target = case.right_path.replace("\\", "/")
    if case.kind == "raster_reference":
        exact = notebook_root / target
        if exact.is_file():
            return exact
        prefix_matches = sorted(
            path
            for path in notebook_root.rglob("*.tif")
            if path.relative_to(notebook_root).as_posix().startswith(target)
        )
        return prefix_matches[0] if len(prefix_matches) == 1 else None
    if case.kind == "npy_reference":
        exact = notebook_root / target
        if exact.is_file():
            return exact
        prefix_matches = sorted(path for path in notebook_root.rglob("*.npy") if path.relative_to(notebook_root).as_posix().startswith(target))
        return prefix_matches[0] if len(prefix_matches) == 1 else None
    return None


def _compare_rasters(left_path: Path, right_path: Path, case: Phase5Case) -> dict[str, Any]:
    with rasterio.open(left_path) as left_ds, rasterio.open(right_path) as right_ds:
        if (left_ds.width, left_ds.height) != (right_ds.width, right_ds.height):
            return {"pass": False, "classification": "metadata mismatch", "message": "width/height differ"}
        if left_ds.crs != right_ds.crs:
            return {"pass": False, "classification": "grid mismatch", "message": "CRS differs"}
        if left_ds.transform != right_ds.transform:
            return {"pass": False, "classification": "grid mismatch", "message": "transform differs"}
        if left_ds.count != right_ds.count:
            return {"pass": False, "classification": "metadata mismatch", "message": f"band count {left_ds.count} != {right_ds.count}"}
        if left_ds.dtypes != right_ds.dtypes and not _is_allowed_validmask_dtype_pair(left_ds.dtypes, right_ds.dtypes, case.allow_validmask_representation_diff):
            return {"pass": False, "classification": "dtype mismatch", "message": f"{left_ds.dtypes} != {right_ds.dtypes}"}
        if left_ds.nodata != right_ds.nodata and not _is_allowed_validmask_nodata_pair(left_ds.nodata, right_ds.nodata, case.allow_validmask_representation_diff):
            return {"pass": False, "classification": "nodata mismatch", "message": f"{left_ds.nodata} != {right_ds.nodata}"}

        max_error = 0.0
        for band in range(1, left_ds.count + 1):
            left_mask = left_ds.read_masks(band) == 0
            right_mask = right_ds.read_masks(band) == 0
            if not np.array_equal(left_mask, right_mask):
                return {"pass": False, "classification": "nodata mismatch", "message": f"band {band} mask differs"}

            left_array = left_ds.read(band, masked=False).astype(np.float32, copy=False)
            right_array = right_ds.read(band, masked=False).astype(np.float32, copy=False)
            if not np.array_equal(np.isnan(left_array), np.isnan(right_array)):
                return {"pass": False, "classification": "nodata mismatch", "message": f"band {band} NaN mask differs"}

            finite_mask = np.isfinite(left_array) & np.isfinite(right_array)
            if finite_mask.any():
                band_error = float(np.max(np.abs(left_array[finite_mask] - right_array[finite_mask])))
                max_error = max(max_error, band_error)
                if band_error > case.tolerance:
                    return {"pass": False, "classification": "value mismatch", "message": f"band {band} max_error={band_error} tolerance={case.tolerance}", "max_error": band_error}
        return {"pass": True, "max_error": max_error}


def _compare_npy(left_path: Path, right_path: Path, tolerance: float) -> dict[str, Any]:
    left = np.load(left_path)
    right = np.load(right_path)
    if left.shape != right.shape:
        return {"pass": False, "classification": "metadata mismatch", "message": f"shape {left.shape} != {right.shape}"}
    if left.dtype != right.dtype:
        return {"pass": False, "classification": "dtype mismatch", "message": f"{left.dtype} != {right.dtype}"}
    if not np.array_equal(np.isnan(left), np.isnan(right)):
        return {"pass": False, "classification": "nodata mismatch", "message": "NaN mask differs"}
    if not np.array_equal(np.isfinite(left), np.isfinite(right)):
        return {"pass": False, "classification": "nodata mismatch", "message": "finite mask differs"}
    finite = np.isfinite(left) & np.isfinite(right)
    max_error = 0.0
    if finite.any():
        max_error = float(np.max(np.abs(left[finite] - right[finite])))
        if max_error > tolerance:
            return {"pass": False, "classification": "value mismatch", "message": f"max_error={max_error} tolerance={tolerance}", "max_error": max_error}
    return {"pass": True, "max_error": max_error}


def _evaluate_report_not_implemented(app_run_dir: Path) -> list[dict[str, Any]]:
    manifest_path = app_run_dir / "QA" / "REPORT_640_manifest.json"
    if not manifest_path.is_file():
        return [{"relative_path": name, "status": "missing_manifest"} for name in REPORT_640_OUTPUTS]
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    reports = payload.get("reports", {})
    results: list[dict[str, Any]] = []
    for name in REPORT_640_OUTPUTS:
        status = reports.get(name, {}).get("status")
        file_exists = (app_run_dir / name).is_file()
        results.append(
            {
                "relative_path": name,
                "status": status if status == "not_implemented_no_source_equivalent" and not file_exists else "fail",
                "file_exists": file_exists,
            }
        )
    return results


def _aggregate_case_status(results: list[CaseResult], *, allow_expected_xfails: bool) -> str:
    statuses = {result.status for result in results}
    if statuses == {"pass"}:
        return "PASS"
    if allow_expected_xfails and statuses <= {"pass", "xfail"} and "xfail" in statuses:
        return "PASS_WITH_CLASSIFIED_EXCEPTIONS"
    if "config_required" in statuses:
        return "CONFIG_REQUIRED"
    return "FAIL"


def _count_statuses(results: list[CaseResult]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return counts


def _is_allowed_validmask_dtype_pair(
    left_dtypes: tuple[object, ...],
    right_dtypes: tuple[object, ...],
    allow_validmask_representation_diff: bool,
) -> bool:
    if not allow_validmask_representation_diff:
        return False
    return tuple(str(value) for value in left_dtypes) == ("float32",) and tuple(str(value) for value in right_dtypes) == ("uint8",)


def _is_allowed_validmask_nodata_pair(
    left_nodata: object,
    right_nodata: object,
    allow_validmask_representation_diff: bool,
) -> bool:
    if not allow_validmask_representation_diff:
        return False
    return left_nodata == -9999.0 and right_nodata == 0.0
