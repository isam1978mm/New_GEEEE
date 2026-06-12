from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import fnmatch
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

from app.pipeline.parity import resolve_run_output_path


HYPERCUBE_TENSOR_VERIFICATION_SCHEMA_VERSION = "hypercube_tensor_npy_verification_v1"
HYPERCUBE_TENSOR_REPORT_RELATIVE_PATH = "manifests/hypercube_tensor_npy_verification.json"
HYPERCUBE_TENSOR_CLASSIFICATION = "notebook-parity"
HYPERCUBE_TENSOR_FAMILY = "hypercube/tensor outputs"

ALLOWED_OUTPUT_STATUSES = {
    "passed",
    "missing_app_output",
    "missing_reference_output",
    "ambiguous_app_output",
    "ambiguous_reference_output",
    "shape_mismatch",
    "dtype_mismatch",
    "value_mismatch",
    "error",
}
STATUS_BLOCKED_NOT_COMPARABLE = "blocked_needs_app_hypercube_tensor_run"
ALLOWED_OVERALL_STATUSES = {"passed", "failed", "incomplete", STATUS_BLOCKED_NOT_COMPARABLE}


@dataclass(frozen=True)
class HypercubeTensorSpec:
    logical_name: str
    app_locators: tuple[str, ...]
    reference_locators: tuple[str, ...]
    channel_axis: int
    channel_names: tuple[str, ...]
    notebook_evidence: str


HYPERCUBE_TENSOR_SPECS: tuple[HypercubeTensorSpec, ...] = (
    HypercubeTensorSpec(
        logical_name="final_tesla_v7_2_hypercube_npy",
        app_locators=("NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy",),
        reference_locators=("NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy",),
        channel_axis=0,
        channel_names=(
            "AI_READY_640_Secret_Gold_Halo",
            "AI_READY_640_Secret_Silver_Oxide",
            "AI_READY_640_Secret_Tunnel_Ceiling",
            "AI_READY_640_Secret_Thermal_Inertia",
            "AI_READY_640_Secret_Chemical_Protector",
            "AI_READY_640_Secret_Hidden_Doors",
            "REPORT_640_FINAL_Zero_Point_Targets",
            "REPORT_640_Mass_Report",
            "REPORT_640_Pottery_Report",
        ),
        notebook_evidence=(
            "notebooks/new.ipynb writes np.save(..., FINAL_TESLA_V7_2_HYPERCUBE.npy) "
            "from the FINAL_TESLA_V7_2_HYPERCUBE stack under STACK_DIR/NPY_STACKS."
        ),
    ),
    HypercubeTensorSpec(
        logical_name="radar_stack_hwc_640_npy",
        app_locators=(
            "NPY_STACKS/RADAR_STACK_HWC_640_app.npy",
            "NPY_STACKS/RADAR_STACK_HWC_640_*.npy",
        ),
        reference_locators=("NPY_STACKS/RADAR_STACK_HWC_640_*.npy",),
        channel_axis=-1,
        channel_names=("VV_dB", "VH_dB", "logRatio_dB", "angle"),
        notebook_evidence=(
            "notebooks/new.ipynb writes np.save(stack_path, cube) where stack_path is "
            "STACKS_DIR/RADAR_STACK_HWC_640_{tag}.npy."
        ),
    ),
)


@dataclass(frozen=True)
class HypercubeTensorVerificationResult:
    report_path: Path
    overall_status: str
    outputs: tuple[dict[str, Any], ...]
    run_contract: dict[str, Any]
    npy_outputs_passed: bool


def verify_hypercube_tensor_parity(
    app_output_dir: str | Path,
    notebook_reference_dir: str | Path,
    run_dir: str | Path,
    run_id: str,
    *,
    specs: tuple[HypercubeTensorSpec, ...] = HYPERCUBE_TENSOR_SPECS,
    atol: float = 1e-6,
    rtol: float = 1e-6,
    report_relative_path: str | Path = HYPERCUBE_TENSOR_REPORT_RELATIVE_PATH,
) -> HypercubeTensorVerificationResult:
    """Verify HYPER-1B core notebook NPY tensors against frozen references."""

    app_root = Path(app_output_dir)
    reference_root = Path(notebook_reference_dir)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    run_contract = _build_run_contract_summary(app_root, reference_root)

    output_items = tuple(
        _verify_one_spec(
            spec,
            app_root,
            reference_root,
            atol=atol,
            rtol=rtol,
        )
        for spec in specs
    )
    overall_status = _overall_status(output_items, run_contract=run_contract)
    npy_outputs_passed = all(item["status"] == "passed" for item in output_items)
    payload = {
        "schema_version": HYPERCUBE_TENSOR_VERIFICATION_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "app_output_dir": str(app_root),
        "notebook_reference_dir": str(reference_root),
        "outputs": list(output_items),
        "run_contract": run_contract,
        "classification": HYPERCUBE_TENSOR_CLASSIFICATION,
        "family": HYPERCUBE_TENSOR_FAMILY,
        "target_mode": "notebook_parity",
        "http_servable": False,
        "npy_outputs_passed": npy_outputs_passed,
        "overall_status": overall_status,
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return HypercubeTensorVerificationResult(
        report_path=report_path,
        overall_status=overall_status,
        outputs=output_items,
        run_contract=run_contract,
        npy_outputs_passed=npy_outputs_passed,
    )


def _verify_one_spec(
    spec: HypercubeTensorSpec,
    app_root: Path,
    reference_root: Path,
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    app_resolution = _resolve_locators(app_root, spec.app_locators)
    reference_resolution = _resolve_locators(reference_root, spec.reference_locators)
    item = _base_output_item(spec, app_resolution.path, reference_resolution.path)
    item["app_resolution_status"] = app_resolution.status
    item["reference_resolution_status"] = reference_resolution.status

    if app_resolution.status == "ambiguous":
        return _finish_output(
            item,
            status="ambiguous_app_output",
            notes="More than one app tensor matched the source-locked locator.",
        )
    if reference_resolution.status == "ambiguous":
        return _finish_output(
            item,
            status="ambiguous_reference_output",
            notes="More than one reference tensor matched the source-locked locator.",
        )

    app_exists = app_resolution.path.is_file()
    reference_exists = reference_resolution.path.is_file()
    item["app_present"] = app_exists
    item["reference_present"] = reference_exists
    item["app_sha256"] = _sha256_file(app_resolution.path) if app_exists else None
    item["reference_sha256"] = _sha256_file(reference_resolution.path) if reference_exists else None
    item["sha256_match"] = (
        item["app_sha256"] == item["reference_sha256"]
        if item["app_sha256"] and item["reference_sha256"]
        else None
    )

    if not app_exists:
        return _finish_output(
            item,
            status="missing_app_output",
            notes="App tensor output is missing.",
        )
    if not reference_exists:
        return _finish_output(
            item,
            status="missing_reference_output",
            runtime_output_verified=True,
            notes="Frozen notebook tensor reference is missing.",
        )

    try:
        return _compare_npy(item, app_resolution.path, reference_resolution.path, atol=atol, rtol=rtol)
    except Exception as exc:  # pragma: no cover - defensive report path
        return _finish_output(
            item,
            status="error",
            runtime_output_verified=True,
            notes=f"NPY comparison failed: {type(exc).__name__}: {exc}",
        )


def _base_output_item(spec: HypercubeTensorSpec, app_path: Path, reference_path: Path) -> dict[str, Any]:
    return {
        "logical_name": spec.logical_name,
        "app_path": str(app_path),
        "reference_path": str(reference_path),
        "app_locators": list(spec.app_locators),
        "reference_locators": list(spec.reference_locators),
        "app_resolution_status": "missing",
        "reference_resolution_status": "missing",
        "app_present": False,
        "reference_present": False,
        "app_sha256": None,
        "reference_sha256": None,
        "sha256_match": None,
        "shape_match": None,
        "dtype_match": None,
        "app_shape": None,
        "reference_shape": None,
        "app_dtype": None,
        "reference_dtype": None,
        "app_finite_count": None,
        "app_nan_count": None,
        "app_inf_count": None,
        "reference_finite_count": None,
        "reference_nan_count": None,
        "reference_inf_count": None,
        "channel_axis": spec.channel_axis,
        "channel_names": list(spec.channel_names),
        "channel_count": None,
        "per_channel": [],
        "compared_element_count": 0,
        "max_abs_diff": None,
        "mean_abs_diff": None,
        "allclose_pass": False,
        "values_compared": False,
        "runtime_output_verified": False,
        "notebook_value_parity_verified": False,
        "status": "error",
        "classification": HYPERCUBE_TENSOR_CLASSIFICATION,
        "family": HYPERCUBE_TENSOR_FAMILY,
        "target_mode": "notebook_parity",
        "artifact_class": "FILESYSTEM_ONLY",
        "http_servable": False,
        "requires_coordinates": False,
        "probability_only_required": False,
        "notebook_evidence": spec.notebook_evidence,
        "notes": "",
    }


def _compare_npy(
    item: dict[str, Any],
    app_path: Path,
    reference_path: Path,
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    app_data = np.load(app_path, allow_pickle=False)
    reference_data = np.load(reference_path, allow_pickle=False)

    item["app_shape"] = list(app_data.shape)
    item["reference_shape"] = list(reference_data.shape)
    item["app_dtype"] = str(app_data.dtype)
    item["reference_dtype"] = str(reference_data.dtype)
    item["shape_match"] = app_data.shape == reference_data.shape
    item["dtype_match"] = app_data.dtype == reference_data.dtype
    item.update(_array_presence_counts(app_data, prefix="app"))
    item.update(_array_presence_counts(reference_data, prefix="reference"))
    item["channel_count"] = _channel_count(app_data, axis=int(item["channel_axis"]))

    if not item["shape_match"]:
        return _finish_output(
            item,
            status="shape_mismatch",
            runtime_output_verified=True,
            notes="NPY shapes did not match; value comparison was not run.",
        )
    if not item["dtype_match"]:
        return _finish_output(
            item,
            status="dtype_mismatch",
            runtime_output_verified=True,
            notes="NPY dtypes did not match; value comparison was not run.",
        )

    item.update(_diff_stats(app_data, reference_data, atol=atol, rtol=rtol))
    item["per_channel"] = _per_channel_diff_stats(
        app_data,
        reference_data,
        channel_axis=int(item["channel_axis"]),
        channel_names=tuple(str(name) for name in item["channel_names"]),
        atol=atol,
        rtol=rtol,
    )
    item["values_compared"] = True
    if item["allclose_pass"]:
        return _finish_output(
            item,
            status="passed",
            runtime_output_verified=True,
            notebook_value_parity_verified=True,
            notes="App and notebook tensor outputs match within tolerance.",
        )
    return _finish_output(
        item,
        status="value_mismatch",
        runtime_output_verified=True,
        notes="NPY values differ outside tolerance.",
    )


def _diff_stats(
    app_data: np.ndarray,
    reference_data: np.ndarray,
    *,
    atol: float,
    rtol: float,
) -> dict[str, Any]:
    app_float = np.asarray(app_data, dtype=np.float64)
    reference_float = np.asarray(reference_data, dtype=np.float64)
    valid = np.isfinite(app_float) & np.isfinite(reference_float)
    compared = int(np.count_nonzero(valid))
    if compared == 0:
        return {
            "compared_element_count": 0,
            "max_abs_diff": None,
            "mean_abs_diff": None,
            "allclose_pass": False,
        }

    app_valid = app_float[valid]
    reference_valid = reference_float[valid]
    abs_diff = np.abs(app_valid - reference_valid)
    return {
        "compared_element_count": compared,
        "max_abs_diff": float(np.max(abs_diff)),
        "mean_abs_diff": float(np.mean(abs_diff)),
        "allclose_pass": bool(
            np.allclose(app_valid, reference_valid, atol=atol, rtol=rtol, equal_nan=True)
        ),
    }


def _array_presence_counts(data: np.ndarray, *, prefix: str) -> dict[str, int]:
    values = np.asarray(data, dtype=np.float64)
    return {
        f"{prefix}_finite_count": int(np.count_nonzero(np.isfinite(values))),
        f"{prefix}_nan_count": int(np.count_nonzero(np.isnan(values))),
        f"{prefix}_inf_count": int(np.count_nonzero(np.isinf(values))),
    }


def _channel_count(data: np.ndarray, *, axis: int) -> int:
    normalized_axis = axis if axis >= 0 else data.ndim + axis
    return int(data.shape[normalized_axis])


def _per_channel_diff_stats(
    app_data: np.ndarray,
    reference_data: np.ndarray,
    *,
    channel_axis: int,
    channel_names: tuple[str, ...],
    atol: float,
    rtol: float,
) -> list[dict[str, Any]]:
    normalized_axis = channel_axis if channel_axis >= 0 else app_data.ndim + channel_axis
    channel_count = int(app_data.shape[normalized_axis])
    summaries: list[dict[str, Any]] = []
    for index in range(channel_count):
        app_channel = np.take(app_data, index, axis=normalized_axis)
        reference_channel = np.take(reference_data, index, axis=normalized_axis)
        diff = _diff_stats(app_channel, reference_channel, atol=atol, rtol=rtol)
        summaries.append(
            {
                "channel_index": index,
                "channel_name": channel_names[index] if index < len(channel_names) else f"channel_{index}",
                **_array_presence_counts(app_channel, prefix="app"),
                **_array_presence_counts(reference_channel, prefix="reference"),
                "compared_element_count": diff["compared_element_count"],
                "max_abs_diff": diff["max_abs_diff"],
                "mean_abs_diff": diff["mean_abs_diff"],
                "allclose_pass": diff["allclose_pass"],
            }
        )
    return summaries


def _finish_output(
    item: dict[str, Any],
    *,
    status: str,
    runtime_output_verified: bool = False,
    notebook_value_parity_verified: bool = False,
    notes: str,
) -> dict[str, Any]:
    if status not in ALLOWED_OUTPUT_STATUSES:
        raise ValueError(f"unsupported hypercube tensor status: {status}")
    item["status"] = status
    item["runtime_output_verified"] = runtime_output_verified
    item["notebook_value_parity_verified"] = notebook_value_parity_verified
    item["notes"] = notes
    return item


@dataclass(frozen=True)
class _Resolution:
    path: Path
    status: str


def _resolve_locators(root: Path, locators: tuple[str, ...]) -> _Resolution:
    for locator in locators:
        matches = _find_matches(root, locator)
        if len(matches) == 1:
            return _Resolution(path=matches[0], status="resolved")
        if len(matches) > 1:
            return _Resolution(path=root / locator, status="ambiguous")
    return _Resolution(path=root / locators[0], status="missing")


def _find_matches(root: Path, locator: str) -> list[Path]:
    normalized = locator.replace("\\", "/")
    if not _has_glob(normalized):
        path = root / normalized
        return [path] if path.is_file() else []

    return sorted(
        path
        for path in root.rglob("*.npy")
        if fnmatch.fnmatch(path.relative_to(root).as_posix(), normalized)
    )


def _has_glob(locator: str) -> bool:
    return any(token in locator for token in ("*", "?", "["))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _build_run_contract_summary(app_root: Path, reference_root: Path) -> dict[str, Any]:
    app_grid = _read_grid_metadata(app_root)
    reference_grid = _read_grid_metadata(reference_root)
    summary: dict[str, Any] = {
        "status": "unknown",
        "app": app_grid,
        "reference": reference_grid,
        "epsg_match": None,
        "scale_match": None,
        "size_match": None,
        "transform_match": None,
        "origin_delta": None,
        "transform_delta": None,
        "comparable": None,
    }
    if not app_grid.get("available") or not reference_grid.get("available"):
        return summary

    app_transform = app_grid.get("transform")
    reference_transform = reference_grid.get("transform")
    transform_delta = None
    origin_delta = None
    if isinstance(app_transform, list) and isinstance(reference_transform, list) and len(app_transform) == len(reference_transform):
        transform_delta = [
            float(app_value) - float(reference_value)
            for app_value, reference_value in zip(app_transform, reference_transform)
        ]
        origin_delta = [transform_delta[2], transform_delta[5]]

    summary.update(
        {
            "epsg_match": app_grid.get("epsg") == reference_grid.get("epsg"),
            "scale_match": app_grid.get("scale") == reference_grid.get("scale"),
            "size_match": app_grid.get("width") == reference_grid.get("width")
            and app_grid.get("height") == reference_grid.get("height"),
            "transform_match": transform_delta is not None and all(delta == 0.0 for delta in transform_delta),
            "origin_delta": origin_delta,
            "transform_delta": transform_delta,
        }
    )
    comparable = bool(
        summary["epsg_match"]
        and summary["scale_match"]
        and summary["size_match"]
        and summary["transform_match"]
    )
    summary["comparable"] = comparable
    summary["status"] = "comparable" if comparable else "not_comparable"
    return summary


def _read_grid_metadata(root: Path) -> dict[str, Any]:
    for reader in (_read_grid_manifest, _read_run_manifest, _read_final_tesla_raster_metadata):
        metadata = reader(root)
        if metadata.get("available"):
            return metadata
    return {"available": False, "source": None}


def _read_grid_manifest(root: Path) -> dict[str, Any]:
    path = root / "grid_manifest.json"
    if not path.is_file():
        return {"available": False, "source": "grid_manifest.json"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    transform = [float(value) for value in payload.get("crs_transform", [])]
    return {
        "available": True,
        "source": "grid_manifest.json",
        "epsg": int(payload["epsg"]),
        "crs": f"EPSG:{payload['epsg']}",
        "scale": float(payload["scale_m"]),
        "width": int(payload["size_px"]),
        "height": int(payload["size_px"]),
        "transform": transform,
        "origin": [transform[2], transform[5]] if len(transform) >= 6 else None,
    }


def _read_run_manifest(root: Path) -> dict[str, Any]:
    path = root / "QA" / "RUN_MANIFEST.json"
    if not path.is_file():
        return {"available": False, "source": "QA/RUN_MANIFEST.json"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    transform = [float(value) for value in payload.get("crsTransform", [])]
    crs = str(payload["CRS"])
    epsg = int(crs.split(":")[-1]) if ":" in crs else None
    return {
        "available": True,
        "source": "QA/RUN_MANIFEST.json",
        "epsg": epsg,
        "crs": crs,
        "scale": float(payload["SCALE"]),
        "width": int(payload["OUT_SIZE"]),
        "height": int(payload["OUT_SIZE"]),
        "transform": transform,
        "origin": [transform[2], transform[5]] if len(transform) >= 6 else None,
    }


def _read_final_tesla_raster_metadata(root: Path) -> dict[str, Any]:
    path = root / "NPY_STACKS" / "FINAL_TESLA_V7_2_HYPERCUBE.tif"
    if not path.is_file() or importlib.util.find_spec("rasterio") is None:
        return {"available": False, "source": "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif"}
    import rasterio

    with rasterio.open(path) as dataset:
        transform = [float(value) for value in dataset.transform][:6]
        return {
            "available": True,
            "source": "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif",
            "epsg": int(dataset.crs.to_epsg()) if dataset.crs and dataset.crs.to_epsg() else None,
            "crs": str(dataset.crs),
            "scale": float(abs(dataset.res[0])),
            "width": int(dataset.width),
            "height": int(dataset.height),
            "transform": transform,
            "origin": [transform[2], transform[5]],
        }


def _overall_status(outputs: tuple[dict[str, Any], ...], *, run_contract: dict[str, Any]) -> str:
    if run_contract.get("status") == "not_comparable":
        return STATUS_BLOCKED_NOT_COMPARABLE
    statuses = {item["status"] for item in outputs}
    if statuses == {"passed"}:
        return "passed"
    if statuses & {"missing_app_output", "missing_reference_output"}:
        return "incomplete"
    return "failed"
