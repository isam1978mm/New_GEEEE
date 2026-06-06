from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np

from app.pipeline.parity import resolve_run_output_path


PHASE_E3_SEMANTIC_FEATURE_COMPARATOR_SCHEMA_VERSION = (
    "phase_e3_semantic_feature_comparator_v1"
)
PHASE_E3_SEMANTIC_FEATURE_COMPARATOR_REPORT_RELATIVE_PATH = (
    "manifests/phase_e3_semantic_feature_comparator.json"
)
PHASE_E3_COMPARATOR_ID = "phase_e3_semantic_feature_comparator"

PHASE_C1_FAMILY_ID = "phase_c1_ai_beh_relation_features"
PHASE_C2_FAMILY_ID = "phase_c2_ai_beh_extended_features"

PHASE_C_SEMANTIC_FEATURE_OUTPUT_NAMES: tuple[str, ...] = (
    "AI_BEH_VegRoot_REL_ND_DOM_lin_640",
    "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640",
    "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640",
    "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640",
    "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640",
    "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640",
)

PHASE_C_SEMANTIC_FEATURE_FAMILIES: dict[str, str] = {
    "AI_BEH_VegRoot_REL_ND_DOM_lin_640": PHASE_C1_FAMILY_ID,
    "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640": PHASE_C1_FAMILY_ID,
    "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640": PHASE_C1_FAMILY_ID,
    "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640": PHASE_C2_FAMILY_ID,
    "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640": PHASE_C2_FAMILY_ID,
    "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640": PHASE_C2_FAMILY_ID,
}

ALLOWED_PHASE_E3_OUTPUT_STATUSES = {
    "passed",
    "failed",
    "reference_missing",
    "app_output_missing",
    "comparison_unavailable",
    "skipped_by_request",
    "error",
}

ALLOWED_PHASE_E3_OVERALL_STATUSES = {
    "passed",
    "failed",
    "incomplete",
    "comparison_unavailable",
    "error",
}

_NAN_POLICY = "NaN values compare equal only when positions match"


@dataclass(frozen=True)
class PhaseCSemanticFeatureComparatorResult:
    report_path: Path
    selected_outputs: tuple[str, ...]
    results: tuple[dict[str, object], ...]
    overall_status: str
    runtime_output_verified: bool
    notebook_value_parity_verified: bool


def compare_phase_c_semantic_features(
    *,
    app_output_dir: str | Path,
    reference_bundle_dir: str | Path,
    run_dir: str | Path,
    run_id: str,
    selected_outputs: Iterable[str] | None = None,
    atol: float = 1e-6,
    rtol: float = 1e-6,
    app_arrays: Mapping[str, object] | None = None,
    reference_arrays: Mapping[str, object] | None = None,
    report_relative_path: str | Path = PHASE_E3_SEMANTIC_FEATURE_COMPARATOR_REPORT_RELATIVE_PATH,
) -> PhaseCSemanticFeatureComparatorResult:
    """Compare private Phase C semantic feature arrays against frozen references."""

    app_root = Path(app_output_dir)
    reference_root = Path(reference_bundle_dir)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    selected = _validate_selected_outputs(selected_outputs)
    results = tuple(
        _compare_one_output(
            output_name,
            app_root=app_root,
            reference_root=reference_root,
            app_arrays=app_arrays or {},
            reference_arrays=reference_arrays or {},
            atol=atol,
            rtol=rtol,
        )
        for output_name in selected
    )
    overall_status = _overall_status(results)
    runtime_output_verified = bool(results) and all(
        bool(item["app_output_present"]) for item in results
    )
    notebook_value_parity_verified = overall_status == "passed"

    payload = {
        "schema_version": PHASE_E3_SEMANTIC_FEATURE_COMPARATOR_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "comparator_id": PHASE_E3_COMPARATOR_ID,
        "selected_outputs": list(selected),
        "results": list(results),
        "counts_by_status": _counts_by_status(results),
        "overall_status": overall_status,
        "runtime_output_verified": runtime_output_verified,
        "notebook_value_parity_verified": notebook_value_parity_verified,
        "reference_bundle_dir": str(reference_root),
        "app_output_dir": str(app_root),
        "report_path": str(report_path),
        "phase_e3_comparator_only": True,
        "runtime_added": False,
        "writer_added": False,
        "earth_engine_calls_added": False,
        "public_exposure_changes": False,
        "artifact_generation": False,
        "notes": (
            "Phase E3 compares private Phase C semantic feature arrays against "
            "frozen references. It does not create science outputs or expose private "
            "artifacts."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PhaseCSemanticFeatureComparatorResult(
        report_path=report_path,
        selected_outputs=selected,
        results=results,
        overall_status=overall_status,
        runtime_output_verified=runtime_output_verified,
        notebook_value_parity_verified=notebook_value_parity_verified,
    )


def _compare_one_output(
    output_name: str,
    *,
    app_root: Path,
    reference_root: Path,
    app_arrays: Mapping[str, object],
    reference_arrays: Mapping[str, object],
    atol: float,
    rtol: float,
) -> dict[str, object]:
    base = _base_result(output_name, atol=atol, rtol=rtol)
    app_present, app_data = _load_array(output_name, app_root, app_arrays)
    reference_present, reference_data = _load_array(
        output_name,
        reference_root,
        reference_arrays,
    )
    base["app_output_present"] = app_present
    base["reference_present"] = reference_present

    if not app_present:
        return _finish(
            base,
            status="app_output_missing",
            notes="App output array is missing.",
        )
    if not reference_present:
        return _finish(
            base,
            status="reference_missing",
            runtime_output_verified=True,
            notes="Frozen reference array is missing.",
        )
    if app_data is None or reference_data is None:
        return _finish(
            base,
            status="comparison_unavailable",
            runtime_output_verified=app_present,
            notes="Array comparison is unavailable for this output.",
        )

    app_array = np.asarray(app_data)
    reference_array = np.asarray(reference_data)
    base["dtype"] = str(app_array.dtype)
    shape_match = app_array.shape == reference_array.shape
    base["shape_match"] = shape_match
    if not shape_match:
        return _finish(
            base,
            status="failed",
            runtime_output_verified=True,
            notes="Array shapes differ.",
        )

    app_float = app_array.astype(np.float64, copy=False)
    reference_float = reference_array.astype(np.float64, copy=False)
    app_nan = np.isnan(app_float)
    reference_nan = np.isnan(reference_float)
    if not np.array_equal(app_nan, reference_nan):
        return _finish(
            base,
            status="failed",
            runtime_output_verified=True,
            notes="NaN positions differ.",
        )

    finite = ~app_nan
    if finite.any():
        diffs = np.abs(app_float[finite] - reference_float[finite])
        max_abs_error = float(diffs.max())
        mean_abs_error = float(diffs.mean())
        within_tolerance = bool(
            np.allclose(
                app_float[finite],
                reference_float[finite],
                atol=atol,
                rtol=rtol,
                equal_nan=False,
            )
        )
    else:
        max_abs_error = 0.0
        mean_abs_error = 0.0
        within_tolerance = True

    base["max_abs_error"] = max_abs_error
    base["mean_abs_error"] = mean_abs_error
    if within_tolerance:
        return _finish(
            base,
            status="passed",
            runtime_output_verified=True,
            notebook_value_parity_verified=True,
            notes="Arrays match within tolerance.",
        )
    return _finish(
        base,
        status="failed",
        runtime_output_verified=True,
        notes="Array values differ outside tolerance.",
    )


def _base_result(output_name: str, *, atol: float, rtol: float) -> dict[str, object]:
    return {
        "output_name": output_name,
        "family_id": PHASE_C_SEMANTIC_FEATURE_FAMILIES[output_name],
        "status": "comparison_unavailable",
        "app_output_present": False,
        "reference_present": False,
        "shape_match": None,
        "dtype": "",
        "tolerance": {"atol": float(atol), "rtol": float(rtol)},
        "max_abs_error": None,
        "mean_abs_error": None,
        "nan_policy": _NAN_POLICY,
        "runtime_output_verified": False,
        "notebook_value_parity_verified": False,
        "notes": "",
    }


def _finish(
    item: dict[str, object],
    *,
    status: str,
    notes: str,
    runtime_output_verified: bool = False,
    notebook_value_parity_verified: bool = False,
) -> dict[str, object]:
    if status not in ALLOWED_PHASE_E3_OUTPUT_STATUSES:
        raise ValueError(f"unsupported Phase E3 output status: {status}")
    item["status"] = status
    item["runtime_output_verified"] = runtime_output_verified
    item["notebook_value_parity_verified"] = notebook_value_parity_verified
    item["notes"] = notes
    return item


def _load_array(
    output_name: str,
    root: Path,
    arrays: Mapping[str, object],
) -> tuple[bool, np.ndarray | None]:
    if output_name in arrays:
        return True, np.asarray(arrays[output_name])
    filename = f"{output_name}.npy"
    path = _locate_array_file(root, filename)
    if path is None:
        return False, None
    try:
        return True, np.load(path)
    except (OSError, ValueError):
        return True, None


def _locate_array_file(root: Path, filename: str) -> Path | None:
    candidates = (
        root / filename,
        root / "references" / "phase_c_semantic_feature_writers" / filename,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    if root.is_dir():
        for path in root.rglob(filename):
            if path.is_file():
                return path
    return None


def _validate_selected_outputs(
    selected_outputs: Iterable[str] | None,
) -> tuple[str, ...]:
    selected = tuple(selected_outputs or PHASE_C_SEMANTIC_FEATURE_OUTPUT_NAMES)
    unknown = sorted(set(selected) - set(PHASE_C_SEMANTIC_FEATURE_OUTPUT_NAMES))
    if unknown:
        raise ValueError(f"unsupported Phase C semantic feature outputs: {', '.join(unknown)}")
    return selected


def _overall_status(results: Iterable[Mapping[str, object]]) -> str:
    statuses = [str(item["status"]) for item in results]
    if not statuses:
        return "incomplete"
    if any(status == "error" for status in statuses):
        return "error"
    if any(status == "failed" for status in statuses):
        return "failed"
    if any(status == "comparison_unavailable" for status in statuses):
        return "comparison_unavailable"
    if any(status in {"reference_missing", "app_output_missing"} for status in statuses):
        return "incomplete"
    if all(status == "passed" for status in statuses):
        return "passed"
    return "incomplete"


def _counts_by_status(results: Iterable[Mapping[str, object]]) -> dict[str, int]:
    counts = {status: 0 for status in sorted(ALLOWED_PHASE_E3_OUTPUT_STATUSES)}
    for item in results:
        counts[str(item["status"])] += 1
    return counts
