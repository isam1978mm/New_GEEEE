from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


AI_BEH_RELATION_RECOVERY_SCHEMA_VERSION = "ai_beh_relation_recovery_v1"
AI_BEH_RELATION_RECOVERY_REPORT_RELATIVE_PATH = (
    "manifests/ai_beh_relation_recovery_report.json"
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

_COMMON_REQUIRED_METADATA = (
    "dtype",
    "nodata or NaN policy",
    "CRS",
    "transform",
    "width",
    "height",
    "band count",
    "value tolerance",
)

_COMMON_SOURCE_REFERENCE = (
    "notebooks/new.ipynb lines around 23418-23424 keep the exact AI_BEH relation "
    "builder: normalizedDifference(B8,B4) is renamed "
    "AI_BEH_VegRoot_REL_ND_DOM_lin_640, B4/B3 is renamed "
    "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640, and B11/B12 is renamed "
    "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640. Later notebook cells around "
    "23644-23732, 23972-23974, 35469-35471, and 44248-44250 keep the filenames "
    "visible in stack assembly and candidate file tables."
)

_COMMON_CURRENT_STATUS = (
    "missing; notebook source and export naming are visible, but the app has no "
    "standalone writer for the AI_BEH relation rasters"
)

_COMMON_EXPECTED_INPUT_OUTPUTS = (
    "S2:B3",
    "S2:B4",
    "S2:B8",
    "S2:B11",
    "S2:B12",
)

_COMMON_UNITS = (
    "Notebook formulas produce ratio or normalized-difference relation rasters from "
    "Sentinel-2 reflectance bands. Frozen notebook references are still required to "
    "lock final unit wording and numeric tolerance."
)

_COMMON_NODATA = (
    "The notebook source shows the relation formulas and exported names, but the exact "
    "exported nodata or NaN persistence remains unresolved until frozen notebook "
    "references are captured."
)


@dataclass(frozen=True)
class AIBehRelationRecoveryItem:
    id: str
    notebook_output: str
    family: str
    current_app_status: str
    source_status: str
    authoritative_source_available: bool
    source_reference: str
    expected_input_outputs: tuple[str, ...]
    expected_formula_summary: str
    expected_dtype: str
    expected_units: str
    expected_nodata_policy: str
    required_reference_outputs: tuple[str, ...]
    required_metadata: tuple[str, ...]
    target_mode: str
    classification: str
    http_servable: bool
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
            raise ValueError("Phase 4H5 recovery items must not target public_shared")
        if self.http_servable:
            raise ValueError("Phase 4H5 recovery items must not default http_servable true")
        if self.runtime_output_verified:
            raise ValueError("Phase 4H5 recovery does not verify runtime output presence")
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 4H5 recovery does not verify notebook value parity")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_CHECKLIST: tuple[AIBehRelationRecoveryItem, ...] = (
    AIBehRelationRecoveryItem(
        id="ai_beh_vegroot_relation",
        notebook_output="AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif",
        family="AI_BEH semantic rasters",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=_COMMON_SOURCE_REFERENCE,
        expected_input_outputs=_COMMON_EXPECTED_INPUT_OUTPUTS,
        expected_formula_summary=(
            "AI_BEH_VegRoot_REL_ND_DOM_lin_640 = normalizedDifference(B8, B4)."
        ),
        expected_dtype="unknown",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=("AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "The source cell and notebook export names are visible, but frozen notebook "
            "references are still required to lock final metadata and numeric tolerance."
        ),
        recommended_next_action=(
            "Capture the frozen VegRoot relation raster and run the Phase 4H5 verifier "
            "before any implementation slice."
        ),
        notes=(
            "This is a standalone notebook output and a downstream stack component. "
            "Existing app outputs are not automatic equivalents."
        ),
    ),
    AIBehRelationRecoveryItem(
        id="ai_beh_ironoxide_relation",
        notebook_output="AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif",
        family="AI_BEH semantic rasters",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=_COMMON_SOURCE_REFERENCE,
        expected_input_outputs=_COMMON_EXPECTED_INPUT_OUTPUTS,
        expected_formula_summary=(
            "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640 = B4 / B3."
        ),
        expected_dtype="unknown",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=("AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "The source cell and notebook export names are visible, but frozen notebook "
            "references are still required to lock final metadata and numeric tolerance."
        ),
        recommended_next_action=(
            "Capture the frozen IronOxide relation raster and run the Phase 4H5 verifier "
            "before any implementation slice."
        ),
        notes=(
            "This is a standalone notebook output and a downstream stack component. "
            "Existing app outputs are not automatic equivalents."
        ),
    ),
    AIBehRelationRecoveryItem(
        id="ai_beh_claythermal_relation",
        notebook_output="AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif",
        family="AI_BEH semantic rasters",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=_COMMON_SOURCE_REFERENCE,
        expected_input_outputs=_COMMON_EXPECTED_INPUT_OUTPUTS,
        expected_formula_summary=(
            "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640 = B11 / B12."
        ),
        expected_dtype="unknown",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=("AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker=(
            "The source cell and notebook export names are visible, but frozen notebook "
            "references are still required to lock final metadata and numeric tolerance."
        ),
        recommended_next_action=(
            "Capture the frozen ClayThermal relation raster and run the Phase 4H5 verifier "
            "before any implementation slice."
        ),
        notes=(
            "This is a standalone notebook output and a downstream stack component. "
            "Existing app outputs are not automatic equivalents."
        ),
    ),
)


def get_ai_beh_relation_recovery_checklist() -> tuple[AIBehRelationRecoveryItem, ...]:
    """Return the Phase 4H5 recovery checklist for the AI_BEH relation rasters."""

    return _CHECKLIST


def write_ai_beh_relation_recovery_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[AIBehRelationRecoveryItem] | None = None,
    report_relative_path: str | Path = AI_BEH_RELATION_RECOVERY_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON recovery report without creating TIFF or NPY outputs."""

    report_items = tuple(items or _CHECKLIST)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": AI_BEH_RELATION_RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_source_status": _counts_by("source_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status", report_items
        ),
        "phase_4h5_formula_changes": False,
        "notes": (
            "Phase 4H5 is recovery and verification-contract work only. It does not "
            "implement AI_BEH relation rasters, change semantic formulas, or introduce "
            "public serving."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[AIBehRelationRecoveryItem],
) -> dict[str, int]:
    if field_name == "source_status":
        counts = {status: 0 for status in sorted(ALLOWED_SOURCE_STATUSES)}
    elif field_name == "implementation_status":
        counts = {status: 0 for status in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    else:
        raise ValueError(f"unsupported count field: {field_name}")

    for item in items:
        counts[getattr(item, field_name)] += 1
    return counts
