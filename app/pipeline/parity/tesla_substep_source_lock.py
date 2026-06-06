from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from app.pipeline.parity import resolve_run_output_path


FUTURE_SLICE_J2_SCHEMA_VERSION = "future_slice_j2_tesla_substep_source_lock_v1"
FUTURE_SLICE_J2_REPORT_RELATIVE_PATH = (
    "manifests/future_slice_j2_source_lock_report.json"
)


@dataclass(frozen=True)
class TeslaSubstepSourceLockItem:
    id: str
    selected_substep_name: str
    source_contracts: tuple[str, ...]
    source_recovery_modules: tuple[str, ...]
    notebook_evidence_summary: str
    selected_outputs: tuple[str, ...]
    formulas: dict[str, str]
    required_input_bands_or_arrays: tuple[str, ...]
    output_names: tuple[str, ...]
    expected_shape_policy: str
    expected_dtype_policy: str
    nodata_or_nan_policy: str
    grid_metadata_policy: str
    privacy_boundary: str
    clean_app_allowed: bool
    parity_private_allowed: bool
    http_servable: bool
    frontend_visible: bool
    downloadable_via_api: bool
    earth_engine_required_for_tests: bool
    implementation_ready: bool
    implementation_blockers: tuple[str, ...]
    recommended_phase_c_followup_scope: str
    tests_required_for_implementation: tuple[str, ...]
    notebook_value_parity_requirement: str
    frozen_reference_requirement: str
    risks: tuple[str, ...]
    notes: tuple[str, ...]
    source_lock_status: str
    recommended_next_slice: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_SELECTED_OUTPUTS = (
    "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif",
    "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif",
    "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif",
)

_FORMULAS = {
    "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif": "B12 / B11",
    "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif": "B4 / B2",
    "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif": "(B8 + B4) / (B11 + 0.001)",
}

_SOURCE_LOCK_ITEM = TeslaSubstepSourceLockItem(
    id="future_slice_j2_ai_beh_extended_source_lock",
    selected_substep_name="AI_BEH extended semantic rasters",
    source_contracts=(
        "docs/AI_BEH_EXTENDED_PARITY_CONTRACT.md",
        "docs/SEMANTIC_RASTER_RECOVERY_CONTRACT.md",
        "docs/PHASE_10_CLEAN_VS_PARITY_DECISION.md",
        "docs/SPECIAL_TRACK_J_TESLA_FLOW_DECOMPOSITION.md",
    ),
    source_recovery_modules=(
        "app/pipeline/parity/ai_beh_extended_recovery.py",
    ),
    notebook_evidence_summary=(
        "Phase 4H6 records notebook lines around 24193-24205 for the exact extended "
        "AI_BEH builder and lines around 35472-35475 for the later file table. "
        "The J1 decomposition maps this formula-backed semantic substep to a later "
        "Phase C writer slice."
    ),
    selected_outputs=_SELECTED_OUTPUTS,
    formulas=_FORMULAS,
    required_input_bands_or_arrays=("B2", "B4", "B8", "B11", "B12"),
    output_names=_SELECTED_OUTPUTS,
    expected_shape_policy=(
        "All input arrays for a future implementation must be same-shaped 2D GRID-aligned arrays."
    ),
    expected_dtype_policy=(
        "Future implementation should compute float32 arrays unless frozen references require a narrower export policy."
    ),
    nodata_or_nan_policy=(
        "Unsafe ratio denominators should become NaN in local array tests; final TIFF nodata behavior remains reference-locked."
    ),
    grid_metadata_policy=(
        "Future writer must preserve caller-supplied GRID metadata and later compare CRS, transform, width, height, band count, dtype, nodata, and values against frozen references."
    ),
    privacy_boundary="private_notebook_parity_only",
    clean_app_allowed=False,
    parity_private_allowed=True,
    http_servable=False,
    frontend_visible=False,
    downloadable_via_api=False,
    earth_engine_required_for_tests=False,
    implementation_ready=True,
    implementation_blockers=(
        "Phase C2 implementation is not part of J2.",
        "Frozen notebook references are still needed before notebook-value parity can pass.",
        "Final exported dtype, nodata, CRS, transform, width, height, and tolerance remain reference-locked.",
        "No public serving, frontend exposure, or artifact download policy is approved.",
    ),
    recommended_phase_c_followup_scope=(
        "Phase C2 should implement only the AI_BEH extended semantic raster family as a private notebook-parity writer using local arrays and tiny fixtures."
    ),
    tests_required_for_implementation=(
        "formula value tests for all three selected outputs",
        "safe denominator and NaN policy tests",
        "same-shape 2D input validation",
        "required band validation",
        "private run-dir path safety",
        "no Earth Engine import or call",
        "no API, frontend, or artifact-serving exposure",
        "notebook_value_parity_verified remains false until frozen reference comparison passes",
    ),
    notebook_value_parity_requirement=(
        "notebook-value parity requires frozen reference comparison through the Phase 4H6 verifier or a later approved comparator"
    ),
    frozen_reference_requirement=(
        "Capture the three frozen AI_BEH extended rasters and metadata before any notebook-value parity claim."
    ),
    risks=(
        "Final TIFF metadata may differ from visible formula intent.",
        "Division denominator behavior must match frozen references before parity can pass.",
        "The output names are notebook-parity semantic labels and must not be treated as clean public claims.",
    ),
    notes=(
        "J2 source-locks one coherent family only.",
        "No writer, runtime integration, artifact generation, Earth Engine call, or public exposure is added.",
        "The family was chosen because it has exact formula evidence, simple local-array formulas, and a private Phase 4H6 contract.",
    ),
    source_lock_status="source_locked_for_future_phase_c2",
    recommended_next_slice="Phase C2 separate implementation slice",
)


def get_future_slice_j2_source_lock_item() -> TeslaSubstepSourceLockItem:
    return _SOURCE_LOCK_ITEM


def write_future_slice_j2_source_lock_report(
    *,
    run_dir: str | Path,
    run_id: str,
    item: TeslaSubstepSourceLockItem | None = None,
    report_relative_path: str | Path = FUTURE_SLICE_J2_REPORT_RELATIVE_PATH,
) -> Path:
    selected_item = item or _SOURCE_LOCK_ITEM
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": FUTURE_SLICE_J2_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "selected_substep": selected_item.to_dict(),
        "source_lock_status": selected_item.source_lock_status,
        "recommended_next_slice": selected_item.recommended_next_slice,
        "j2_source_lock_only": True,
        "runtime_added": False,
        "writer_added": False,
        "artifact_generation": False,
        "earth_engine_calls_added": False,
        "public_exposure_changes": False,
        "notes": (
            "J2 source-locks one AI_BEH semantic feature family for a later Phase C2 slice. "
            "It does not add a writer or runtime behavior."
        ),
    }
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return report_path
