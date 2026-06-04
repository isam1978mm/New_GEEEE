from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


AI_READY_ANOMALY_RECOVERY_SCHEMA_VERSION = "ai_ready_anomaly_recovery_v1"
AI_READY_ANOMALY_RECOVERY_REPORT_RELATIVE_PATH = (
    "manifests/ai_ready_anomaly_recovery_report.json"
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


@dataclass(frozen=True)
class AIReadyAnomalyRecoveryItem:
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
            raise ValueError("Phase 4K recovery items must not target public_shared")
        if self.http_servable:
            raise ValueError("Phase 4K recovery items must not default http_servable true")
        if self.runtime_output_verified:
            raise ValueError("Phase 4K recovery does not verify runtime output presence")
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 4K recovery does not verify notebook value parity")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


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

_COMMON_CURRENT_STATUS = (
    "missing; notebook patch and downstream scoring cells reference the output names, "
    "but the app has no standalone writer for either anomaly raster"
)

_COMMON_UNITS = (
    "Notebook scoring cells treat both anomaly rasters as semantic support surfaces. "
    "Frozen notebook references are still required to lock final unit wording and "
    "tolerance."
)

_COMMON_NODATA = (
    "Nodata, NaN persistence, and exact fill behavior remain unresolved until frozen "
    "notebook references are captured."
)

_CHECKLIST: tuple[AIReadyAnomalyRecoveryItem, ...] = (
    AIReadyAnomalyRecoveryItem(
        id="ai_ready_640_magnetic_anomaly",
        notebook_output="AI_READY_640_Magnetic_Anomaly.tif",
        family="AI_READY semantic rasters",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="partial_source_found",
        authoritative_source_available=False,
        source_reference=(
            "notebooks/new.ipynb patch and optional-band cells around 27117-27125, "
            "27966-28042, 30873-30890, 31239-31251, and later scoring cells treat the "
            "raster as optional semantic input. app/pipeline/stages/hypercube.py keeps "
            "the patched 14-band compatibility note that AI_READY_640_Magnetic_Anomaly "
            "remains unavailable."
        ),
        expected_input_outputs=(),
        expected_formula_summary=(
            "Notebook evidence keeps the output name, filename aliases, and downstream "
            "semantic usage visible, but no standalone writer formula or source raster "
            "contract is recovered."
        ),
        expected_dtype="unknown",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=("AI_READY_640_Magnetic_Anomaly.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="blocked_no_source_formula",
        blocker=(
            "Notebook references exist, but no authoritative writer formula, source "
            "raster contract, or frozen reference metadata set is available."
        ),
        recommended_next_action=(
            "Recover the exact notebook writer cell or a frozen notebook reference set "
            "before any implementation or alias decision."
        ),
        notes=(
            "Do not substitute the output with another app raster or with patched "
            "hypercube compatibility logic."
        ),
    ),
    AIReadyAnomalyRecoveryItem(
        id="ai_ready_640_em_anomaly",
        notebook_output="AI_READY_640_EM_Anomaly.tif",
        family="AI_READY semantic rasters",
        current_app_status=_COMMON_CURRENT_STATUS,
        source_status="partial_source_found",
        authoritative_source_available=False,
        source_reference=(
            "notebooks/new.ipynb patch and optional-band cells around 27122-27125, "
            "27966-28042, 30882-30890, 31239-31251, and later scoring cells treat the "
            "raster as optional semantic input. app/pipeline/stages/hypercube.py keeps "
            "the patched 14-band compatibility note that the patched EM slot maps to "
            "DEM_GEO8_TIFS/DEM_640.tif for frozen-compatible stack rebuilding only."
        ),
        expected_input_outputs=("DEM_GEO8_TIFS/DEM_640.tif",),
        expected_formula_summary=(
            "Notebook evidence keeps the output name, filename aliases, and downstream "
            "semantic usage visible. The patched hypercube compatibility layer maps the "
            "missing EM slot to DEM_640.tif, but no standalone notebook writer formula "
            "or dedicated source-stage contract is recovered."
        ),
        expected_dtype="unknown",
        expected_units=_COMMON_UNITS,
        expected_nodata_policy=_COMMON_NODATA,
        required_reference_outputs=(
            "AI_READY_640_EM_Anomaly.tif",
            "FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="blocked_no_source_formula",
        blocker=(
            "Patch-era compatibility evidence exists, but it does not recover a "
            "standalone notebook writer formula or final metadata contract for the EM "
            "anomaly raster itself."
        ),
        recommended_next_action=(
            "Capture the frozen notebook EM anomaly raster and any writer cell or patch "
            "report details before implementation or alias planning."
        ),
        notes=(
            "The patched-hypercube DEM mapping is compatibility evidence only. It is not "
            "a standalone parity writer contract."
        ),
    ),
)


def get_ai_ready_anomaly_recovery_checklist() -> tuple[AIReadyAnomalyRecoveryItem, ...]:
    """Return the Phase 4K recovery checklist for the AI_READY anomaly outputs."""

    return _CHECKLIST


def write_ai_ready_anomaly_recovery_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[AIReadyAnomalyRecoveryItem] | None = None,
    report_relative_path: str | Path = AI_READY_ANOMALY_RECOVERY_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON recovery report without creating TIFF or NPY outputs."""

    report_items = tuple(items or _CHECKLIST)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": AI_READY_ANOMALY_RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_source_status": _counts_by("source_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status", report_items
        ),
        "phase_4k_formula_changes": False,
        "notes": (
            "Phase 4K is recovery and verification-contract work only. It does not "
            "implement anomaly rasters, change semantic formulas, or introduce public "
            "serving."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[AIReadyAnomalyRecoveryItem],
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
