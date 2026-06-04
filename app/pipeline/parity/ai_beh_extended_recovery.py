from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


AI_BEH_EXTENDED_RECOVERY_SCHEMA_VERSION = "ai_beh_extended_recovery_v1"
AI_BEH_EXTENDED_RECOVERY_REPORT_RELATIVE_PATH = (
    "manifests/ai_beh_extended_recovery_report.json"
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
    "notebooks/new.ipynb lines around 24193-24205 keep the exact extended AI_BEH "
    "builder: B12/B11 is renamed AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640, B4/B2 is "
    "renamed AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640, and the expression "
    "((B8 + B4) / (B11 + 0.001)) is renamed "
    "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640. Later notebook cells around "
    "35472-35475 keep the filenames visible in the candidate file table."
)

_COMMON_CURRENT_STATUS = (
    "missing; notebook source and export naming are visible, but the app has no "
    "standalone writer for the extended AI_BEH semantic rasters"
)

_COMMON_EXPECTED_INPUT_OUTPUTS = (
    "S2:B2",
    "S2:B4",
    "S2:B8",
    "S2:B11",
    "S2:B12",
)

_COMMON_UNITS = (
    "Notebook formulas produce ratio or expression-based semantic rasters from "
    "Sentinel-2 reflectance bands. Frozen notebook references are still required to "
    "lock final unit wording and numeric tolerance."
)

_COMMON_NODATA = (
    "The notebook source shows the formulas and exported names, but the exact exported "
    "nodata or NaN persistence remains unresolved until frozen notebook references are "
    "captured."
)


@dataclass(frozen=True)
class AIBehExtendedRecoveryItem:
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
            raise ValueError("Phase 4H6 recovery items must not target public_shared")
        if self.http_servable:
            raise ValueError("Phase 4H6 recovery items must not default http_servable true")
        if self.runtime_output_verified:
            raise ValueError("Phase 4H6 recovery does not verify runtime output presence")
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 4H6 recovery does not verify notebook value parity")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_CHECKLIST: tuple[AIBehExtendedRecoveryItem, ...] = (
    AIBehExtendedRecoveryItem(
        id="ai_beh_goldalloy_extended",
        notebook_output="AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif",
        family="AI_BEH semantic rasters",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=_COMMON_SOURCE_REFERENCE,
        expected_input_outputs=_COMMON_EXPECTED_INPUT_OUTPUTS,
        expected_formula_summary=(
            "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640 = B12 / B11."
        ),
        expected_dtype="unknown",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=("AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif",),
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
            "Capture the frozen GoldAlloy relation raster and run the Phase 4H6 verifier "
            "before any implementation slice."
        ),
        notes=(
            "This is a standalone notebook output and a downstream stack component. "
            "The same core ratio also appears inside the REPORT_640 precursor logic, but "
            "the app does not persist this notebook-named raster."
        ),
    ),
    AIBehExtendedRecoveryItem(
        id="ai_beh_silvercopper_extended",
        notebook_output="AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif",
        family="AI_BEH semantic rasters",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=_COMMON_SOURCE_REFERENCE,
        expected_input_outputs=_COMMON_EXPECTED_INPUT_OUTPUTS,
        expected_formula_summary=(
            "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640 = B4 / B2."
        ),
        expected_dtype="unknown",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=("AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif",),
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
            "Capture the frozen SilverCopper relation raster and run the Phase 4H6 verifier "
            "before any implementation slice."
        ),
        notes=(
            "This is a standalone notebook output and a downstream stack component. "
            "Existing app outputs are not automatic equivalents."
        ),
    ),
    AIBehExtendedRecoveryItem(
        id="ai_beh_ert_proxy_extended",
        notebook_output="AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif",
        family="AI_BEH semantic rasters",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=_COMMON_SOURCE_REFERENCE,
        expected_input_outputs=_COMMON_EXPECTED_INPUT_OUTPUTS,
        expected_formula_summary=(
            "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640 = (B8 + B4) / (B11 + 0.001)."
        ),
        expected_dtype="unknown",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=("AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif",),
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
            "Capture the frozen ERT proxy raster and run the Phase 4H6 verifier before "
            "any implementation slice."
        ),
        notes=(
            "This is a standalone notebook output and a downstream stack component. "
            "Existing app outputs are not automatic equivalents."
        ),
    ),
)


def get_ai_beh_extended_recovery_checklist() -> tuple[AIBehExtendedRecoveryItem, ...]:
    """Return the Phase 4H6 recovery checklist for the extended AI_BEH rasters."""

    return _CHECKLIST


def write_ai_beh_extended_recovery_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[AIBehExtendedRecoveryItem] | None = None,
    report_relative_path: str | Path = AI_BEH_EXTENDED_RECOVERY_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON recovery report without creating TIFF or NPY outputs."""

    report_items = tuple(items or _CHECKLIST)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": AI_BEH_EXTENDED_RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_source_status": _counts_by("source_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status", report_items
        ),
        "phase_4h6_formula_changes": False,
        "notes": (
            "Phase 4H6 is recovery and verification-contract work only. It does not "
            "implement AI_BEH extended rasters, change semantic formulas, or introduce "
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
    items: Iterable[AIBehExtendedRecoveryItem],
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
