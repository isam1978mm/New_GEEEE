from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


HYPERCUBE_RES25_RECOVERY_SCHEMA_VERSION = "hypercube_res25_recovery_v1"
HYPERCUBE_RES25_RECOVERY_REPORT_RELATIVE_PATH = (
    "manifests/hypercube_res25_recovery_report.json"
)

ALLOWED_SOURCE_STATUSES = {
    "exact_source_found",
    "partial_source_found",
    "no_source_found",
    "existing_app_equivalent_found",
    "unknown_needs_reference",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "ready_for_implementation_after_reference",
    "requires_reference_output",
    "requires_source_reconstruction",
    "blocked_no_source_formula",
    "blocked_missing_metadata_contract",
    "deferred",
}

_FINAL_TESLA_BAND_ORDER = (
    "AI_READY_640_Secret_Gold_Halo",
    "AI_READY_640_Secret_Silver_Oxide",
    "AI_READY_640_Secret_Tunnel_Ceiling",
    "AI_READY_640_Secret_Thermal_Inertia",
    "AI_READY_640_Secret_Chemical_Protector",
    "AI_READY_640_Secret_Hidden_Doors",
    "REPORT_640_FINAL_Zero_Point_Targets",
    "REPORT_640_Mass_Report",
    "REPORT_640_Pottery_Report",
)


@dataclass(frozen=True)
class HypercubeRes25RecoveryItem:
    id: str
    notebook_output: str
    family: str
    current_app_status: str
    source_status: str
    authoritative_source_available: bool
    source_reference: str
    expected_input_outputs: tuple[str, ...]
    expected_band_order: tuple[str, ...]
    expected_band_count: int | str
    expected_shape_convention: str
    expected_geotiff_band_layout: str
    expected_pixel_size_m: float | str
    expected_resampling_method: str
    expected_dtype: str
    expected_units: str
    expected_nodata_policy: str
    required_reference_outputs: tuple[str, ...]
    required_metadata: tuple[str, ...]
    target_mode: str
    classification: str
    runtime_output_verified: bool
    notebook_value_parity_verified: bool
    implementation_status: str
    blocker: str
    recommended_next_action: str
    notes: str

    def __post_init__(self) -> None:
        if self.source_status not in ALLOWED_SOURCE_STATUSES:
            raise ValueError(f"unsupported source_status: {self.source_status}")
        if self.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"unsupported implementation_status: {self.implementation_status}"
            )
        if self.target_mode == "public_shared":
            raise ValueError("Phase 4I recovery items must not target public_shared")
        if self.runtime_output_verified:
            raise ValueError("Phase 4I recovery does not verify runtime output presence")
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 4I recovery does not verify notebook value parity")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_SOURCE_REFERENCE = (
    "notebooks/new.ipynb lines 26996-27078: the notebook loads "
    "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif with rasterio, reads all bands as "
    "float32, preserves source band descriptions when available, sets OUTPUT_RES_M = 2.5, "
    "computes zoom_factor = GRID['SCALE'] / OUTPUT_RES_M, upsamples each band with "
    "scipy.ndimage.zoom(..., order=3), updates the transform via Affine.scale(1/zoom_factor, "
    "1/zoom_factor), writes FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif with the updated "
    "profile, and writes FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy with the upsampled "
    "band-first array."
)

_COMMON_CURRENT_STATUS = (
    "missing; the app writes hypercube.tif, hypercube.npy, "
    "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif, "
    "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy, and "
    "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif, but it does not write "
    "the 2.5 m resampled hypercube outputs"
)

_COMMON_UNITS = (
    "Notebook source indicates the 2.5 m outputs inherit per-band values from "
    "FINAL_TESLA_V7_2_HYPERCUBE.tif and apply geometric upsampling only. Frozen "
    "reference outputs are still required to lock final unit wording and tolerance."
)

_COMMON_NODATA = (
    "The output GeoTIFF profile is copied from the source hypercube and only height, "
    "width, transform, and dtype are updated, so nodata policy is inherited from the "
    "source GeoTIFF. Frozen reference output is still required to lock the exact nodata "
    "sentinel and any NaN persistence expectations."
)

_COMMON_REQUIRED_METADATA = (
    "band order",
    "band count",
    "shape",
    "dtype",
    "nodata or NaN policy",
    "CRS",
    "transform",
    "pixel size",
    "width",
    "height",
    "band descriptions",
    "value tolerance",
)

_CHECKLIST: tuple[HypercubeRes25RecoveryItem, ...] = (
    HypercubeRes25RecoveryItem(
        id="final_tesla_v7_2_hypercube_res_2p5m_tif",
        notebook_output="FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif",
        family="hypercube/tensor outputs",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=_SOURCE_REFERENCE,
        expected_input_outputs=("FINAL_TESLA_V7_2_HYPERCUBE.tif",),
        expected_band_order=_FINAL_TESLA_BAND_ORDER,
        expected_band_count=9,
        expected_shape_convention="not_applicable_for_tif",
        expected_geotiff_band_layout=(
            "multi-band GeoTIFF with preserved source band order and band descriptions when available"
        ),
        expected_pixel_size_m=2.5,
        expected_resampling_method="cubic",
        expected_dtype="float32",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=(
            "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif",
            "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif",
            "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "The notebook source for the 2.5 m GeoTIFF is explicit, but the app has no "
            "writer and frozen notebook references are still required to lock the exact "
            "captured width, height, transform, nodata behavior, and numeric tolerance."
        ),
        recommended_next_action=(
            "Capture frozen notebook source and resampled GeoTIFF references, then run "
            "the Phase 4I verifier before any later implementation slice."
        ),
        notes=(
            "Existing app FINAL_TESLA outputs are source inputs only. They are not "
            "automatically equivalent to the 2.5 m resampled GeoTIFF."
        ),
    ),
    HypercubeRes25RecoveryItem(
        id="final_tesla_v7_2_hypercube_res_2p5m_npy",
        notebook_output="FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy",
        family="hypercube/tensor outputs",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=_SOURCE_REFERENCE,
        expected_input_outputs=("FINAL_TESLA_V7_2_HYPERCUBE.tif",),
        expected_band_order=_FINAL_TESLA_BAND_ORDER,
        expected_band_count=9,
        expected_shape_convention="CHW",
        expected_geotiff_band_layout="not_applicable_for_npy",
        expected_pixel_size_m=2.5,
        expected_resampling_method="cubic",
        expected_dtype="float32",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=(
            "The notebook saves the upsampled NumPy tensor directly after cubic zoom. "
            "Frozen reference output is still required to confirm whether NaNs, nodata "
            "sentinels, or finite-only source values are present in the captured stack."
        ),
        required_reference_outputs=(
            "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif",
            "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy",
            "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "The notebook source for the 2.5 m NPY is explicit, but the app has no writer "
            "and frozen notebook references are still required to lock the exact CHW shape, "
            "nodata behavior, and numeric tolerance."
        ),
        recommended_next_action=(
            "Capture frozen notebook source and resampled NPY references, then run the "
            "Phase 4I verifier before any later implementation slice."
        ),
        notes=(
            "The notebook saves a band-first CHW array. Existing app hypercube.npy or "
            "FINAL_TESLA_V7_2_HYPERCUBE.npy are not automatically equivalent to the "
            "2.5 m resampled NPY."
        ),
    ),
)


def get_hypercube_res25_recovery_checklist() -> tuple[HypercubeRes25RecoveryItem, ...]:
    """Return the Phase 4I recovery checklist for the 2.5 m resampled hypercube outputs."""

    return _CHECKLIST


def write_hypercube_res25_recovery_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[HypercubeRes25RecoveryItem] | None = None,
    report_relative_path: str | Path = HYPERCUBE_RES25_RECOVERY_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON recovery report without creating TIFF or NPY outputs."""

    report_items = tuple(items or _CHECKLIST)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": HYPERCUBE_RES25_RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_source_status": _counts_by("source_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "phase_4i_hypercube_math_changes": False,
        "notes": (
            "Phase 4I locks source recovery and verification contract details for "
            "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif and "
            "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy only. It does not generate the "
            "2.5 m hypercube, resample files, call Earth Engine, or integrate with the "
            "live pipeline."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[HypercubeRes25RecoveryItem],
) -> dict[str, int]:
    if field_name == "source_status":
        counts = {status: 0 for status in sorted(ALLOWED_SOURCE_STATUSES)}
    elif field_name == "implementation_status":
        counts = {status: 0 for status in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    else:
        raise ValueError(f"unsupported count field: {field_name}")

    for item in items:
        value = getattr(item, field_name)
        counts[value] += 1
    return counts
