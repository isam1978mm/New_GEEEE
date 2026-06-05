from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


PHASE_5_QA_INTERMEDIATE_SCHEMA_VERSION = "phase_5_qa_intermediate_inventory_v1"
PHASE_5_QA_INTERMEDIATE_REPORT_RELATIVE_PATH = (
    "manifests/phase_5_qa_intermediate_inventory.json"
)

ALLOWED_CATEGORIES = {
    "qa_manifests",
    "provenance_reports",
    "alignment_checks",
    "sar_provenance",
    "pca_stack_qa",
    "grid_consistency_reports",
}

ALLOWED_SOURCE_STATUSES = {
    "exact_source_found",
    "partial_source_found",
    "no_source_found",
    "existing_app_equivalent_found",
    "unknown_needs_reference",
}

ALLOWED_PARITY_STATUSES = {
    "covered_by_existing_contract",
    "inventory_only",
    "verifier_needed",
    "reference_needed",
    "source_recovery_needed",
    "implementation_later",
    "blocked",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "no_action_needed_existing_contract",
    "requires_verifier_contract",
    "requires_reference_output",
    "requires_source_reconstruction",
    "requires_inventory_reconciliation",
    "implementation_deferred",
}

_COMMON_REQUIRED_METADATA = (
    "artifact naming and folder mapping",
    "artifact class",
    "http_servable policy",
    "run-relative path mapping",
    "grid consistency expectations",
    "value or row-count tolerance where applicable",
)


@dataclass(frozen=True)
class QaIntermediateInventoryItem:
    id: str
    category: str
    notebook_artifact_or_pattern: str
    current_app_artifact_or_pattern: str
    source_status: str
    current_app_status: str
    parity_status: str
    expected_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    required_reference_artifacts: tuple[str, ...]
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
        if self.category not in ALLOWED_CATEGORIES:
            raise ValueError(f"unsupported category: {self.category}")
        if self.source_status not in ALLOWED_SOURCE_STATUSES:
            raise ValueError(f"unsupported source_status: {self.source_status}")
        if self.parity_status not in ALLOWED_PARITY_STATUSES:
            raise ValueError(f"unsupported parity_status: {self.parity_status}")
        if self.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"unsupported implementation_status: {self.implementation_status}"
            )
        if self.target_mode == "public_shared":
            raise ValueError("Phase 5 inventory items must not target public_shared")
        if self.http_servable:
            raise ValueError("Phase 5 inventory items must not default http_servable to true")
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 5 inventory only; notebook value parity must remain false")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_INVENTORY: tuple[QaIntermediateInventoryItem, ...] = (
    QaIntermediateInventoryItem(
        id="phase5_qa_manifests",
        category="qa_manifests",
        notebook_artifact_or_pattern=(
            "QA/RUN_MANIFEST.json | QA/QA_GRID_dx_m_640.tif | "
            "QA/QA_GRID_dy_m_640.tif | QA/QA_GRID_validmask_640.tif"
        ),
        current_app_artifact_or_pattern=(
            "QA/RUN_MANIFEST.json | QA/QA_GRID_dx_m_640.tif | "
            "QA/QA_GRID_dy_m_640.tif | QA/QA_GRID_validmask_640.tif | grid_manifest.json"
        ),
        source_status="exact_source_found",
        current_app_status=(
            "Grid stage writes notebook-compatible QA manifest outputs plus app-native grid_manifest.json"
        ),
        parity_status="verifier_needed",
        expected_inputs=("grid center inputs", "GridManifest", "GRID shape and nodata policy"),
        expected_outputs=(
            "QA/RUN_MANIFEST.json",
            "QA/QA_GRID_dx_m_640.tif",
            "QA/QA_GRID_dy_m_640.tif",
            "QA/QA_GRID_validmask_640.tif",
            "grid_manifest.json",
        ),
        required_reference_artifacts=(
            "frozen notebook QA/RUN_MANIFEST.json",
            "frozen notebook QA grid rasters",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity QA/provenance inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_verifier_contract",
        blocker="No dedicated Phase 5 verifier currently checks notebook QA manifest naming and payload parity.",
        recommended_next_action="Add a focused verifier contract for notebook QA manifest artifacts once frozen references are assembled.",
        notes=(
            "Runtime presence and notebook-value parity remain separate. Grid QA rasters exist as artifacts, "
            "but this inventory does not claim a passing parity comparison."
        ),
    ),
    QaIntermediateInventoryItem(
        id="phase5_provenance_reports",
        category="provenance_reports",
        notebook_artifact_or_pattern=(
            "stage_*.manifest.json | hypercube_band_stats.csv | hypercube_norm_params.csv | "
            "drift_audit.csv | stack_presence_summary.json"
        ),
        current_app_artifact_or_pattern=(
            "stage_*.manifest.json | QA/grid_dem/drift_audit.csv | "
            "QA/stacks/stack_presence_summary.json | QA/stacks/band_stats.csv | "
            "hypercube_band_stats.csv | hypercube_norm_params.csv"
        ),
        source_status="existing_app_equivalent_found",
        current_app_status=(
            "App writes multiple provenance-style manifests and CSV reports, but the notebook naming and grouping are not fully reconciled."
        ),
        parity_status="inventory_only",
        expected_inputs=("stage output manifests", "hypercube metadata", "stack audit rows"),
        expected_outputs=(
            "stage_*.manifest.json",
            "QA/grid_dem/drift_audit.csv",
            "QA/stacks/stack_presence_summary.json",
            "QA/stacks/band_stats.csv",
            "hypercube_band_stats.csv",
            "hypercube_norm_params.csv",
        ),
        required_reference_artifacts=(
            "frozen notebook provenance report bundle",
            "frozen notebook manifest or report naming map",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="private QA/provenance inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_inventory_reconciliation",
        blocker="Notebook provenance report naming is broader than the current app manifest/report grouping.",
        recommended_next_action="Reconcile notebook provenance report patterns against the frozen reference bundle before drafting any verifier slice.",
        notes="This item records candidate equivalents only. It does not claim that stage manifests are notebook-value matches.",
    ),
    QaIntermediateInventoryItem(
        id="phase5_alignment_checks",
        category="alignment_checks",
        notebook_artifact_or_pattern=(
            "alignment QA reports | alignment audit tables | mask-selection summaries"
        ),
        current_app_artifact_or_pattern=(
            "alignment_qa.json | alignment_audit.csv | alignment_mask_selection.json | "
            "QA/alignment/alignment_summary_redacted.json"
        ),
        source_status="existing_app_equivalent_found",
        current_app_status="AlignmentQaStage writes app-native alignment QA artifacts with redacted and filesystem-only variants.",
        parity_status="verifier_needed",
        expected_inputs=("core raster set", "GridSpec", "raster metadata inspection"),
        expected_outputs=(
            "alignment_qa.json",
            "alignment_audit.csv",
            "alignment_mask_selection.json",
            "QA/alignment/alignment_summary_redacted.json",
        ),
        required_reference_artifacts=(
            "frozen notebook alignment QA report set",
            "frozen notebook alignment threshold or summary bundle",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="private QA/alignment inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_verifier_contract",
        blocker="No Phase 5 verifier yet compares alignment audit rows or summary payloads against frozen notebook references.",
        recommended_next_action="Create a later alignment QA verifier only after the frozen notebook alignment report set is captured.",
        notes="The app artifacts are app-native QA outputs. Standalone notebook-value parity still needs reference evidence and a verifier contract.",
    ),
    QaIntermediateInventoryItem(
        id="phase5_sar_provenance",
        category="sar_provenance",
        notebook_artifact_or_pattern=(
            "QA_RADAR_CELL25_PAIR_IDS_*.json | QA_S1_MASTER_UNITS.json | "
            "QA_RADAR_META_*.json | SUMMARY_RADAR_*.csv | QA/sar/intermediates/sar_intermediate_manifest.json"
        ),
        current_app_artifact_or_pattern=(
            "QA/sar/sar_pair_diagnostics.json | QA/sar/sar_summary.csv | "
            "QA/sar/sar_nodata_audit.csv | QA/sar/sar_alignment_summary.json | "
            "QA/sar/intermediates/sar_intermediate_manifest.json"
        ),
        source_status="partial_source_found",
        current_app_status=(
            "SarRtcStage writes app-native SAR provenance and a notebook-style intermediate manifest, but several notebook provenance filenames are folded into different summaries."
        ),
        parity_status="reference_needed",
        expected_inputs=("SAR pairing diagnostics", "post-RTC arrays", "intermediate manifest mapping"),
        expected_outputs=(
            "QA/sar/sar_pair_diagnostics.json",
            "QA/sar/sar_summary.csv",
            "QA/sar/sar_nodata_audit.csv",
            "QA/sar/sar_alignment_summary.json",
            "QA/sar/intermediates/sar_intermediate_manifest.json",
        ),
        required_reference_artifacts=(
            "frozen notebook SAR provenance JSON and CSV files",
            "frozen notebook SAR intermediate manifest",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="private SAR provenance inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker="Notebook provenance filenames and app provenance filenames do not map one-to-one without a frozen reference bundle.",
        recommended_next_action="Capture the frozen SAR provenance bundle and then decide whether parity is filename-level, payload-level, or manifest-mapped.",
        notes="This item does not create earlier SAR intermediates or claim that folded provenance files are already notebook-value equivalent.",
    ),
    QaIntermediateInventoryItem(
        id="phase5_pca_stack_qa",
        category="pca_stack_qa",
        notebook_artifact_or_pattern=(
            "PCA parity QA reports | hypercube audit tables | stack band statistics | tensor audit summaries"
        ),
        current_app_artifact_or_pattern=(
            "QA/parity/parity_qa_summary.json | QA/parity/hypercube_audit.csv | "
            "QA/stacks/band_stats.csv | QA/stacks/tensor_audit_summary.json"
        ),
        source_status="existing_app_equivalent_found",
        current_app_status=(
            "PcaAnomalyStage, HypercubeStage, and FeatureStacksStage write app-native PCA and stack QA artifacts."
        ),
        parity_status="verifier_needed",
        expected_inputs=("hypercube band order", "PCA eigenvalue report", "stack audit rows"),
        expected_outputs=(
            "QA/parity/parity_qa_summary.json",
            "QA/parity/hypercube_audit.csv",
            "QA/stacks/band_stats.csv",
            "QA/stacks/tensor_audit_summary.json",
        ),
        required_reference_artifacts=(
            "frozen notebook PCA QA outputs",
            "frozen notebook stack QA tables or summaries",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="private PCA/stack QA inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_verifier_contract",
        blocker="No Phase 5 verifier currently checks PCA QA or stack QA payloads against notebook references.",
        recommended_next_action="Define a later PCA and stack QA verifier after the frozen notebook QA tables are assembled and named.",
        notes="This item is contract planning only. No PCA math or stack assembly behavior changes are part of Phase 5.",
    ),
    QaIntermediateInventoryItem(
        id="phase5_grid_consistency_reports",
        category="grid_consistency_reports",
        notebook_artifact_or_pattern=(
            "GRID consistency reports | zero-shift summaries | geometry consistency summaries"
        ),
        current_app_artifact_or_pattern=(
            "QA/grid_dem/zero_shift_summary.json | QA/grid_dem/drift_audit.csv | "
            "QA/stacks/geometry_consistency_summary.json | QA/grid_dem/grid_guard_summary.json"
        ),
        source_status="existing_app_equivalent_found",
        current_app_status=(
            "Grid, ZeroShiftStage, and FeatureStacksStage write GRID-consistency style summaries, but notebook naming and grouping remain only partially mapped."
        ),
        parity_status="inventory_only",
        expected_inputs=("GRID manifest", "raster sidecars", "stack geometry inspection"),
        expected_outputs=(
            "QA/grid_dem/zero_shift_summary.json",
            "QA/grid_dem/drift_audit.csv",
            "QA/stacks/geometry_consistency_summary.json",
            "QA/grid_dem/grid_guard_summary.json",
        ),
        required_reference_artifacts=(
            "frozen notebook GRID consistency reports",
            "frozen notebook zero-shift or geometry audit bundle",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="private GRID consistency inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_inventory_reconciliation",
        blocker="Notebook GRID consistency reporting is described at a family level, but exact notebook filenames are not fully locked in current source evidence.",
        recommended_next_action="Reconcile notebook GRID consistency report naming before creating a dedicated verifier slice.",
        notes="This item remains private notebook-parity tracking by default and does not imply public QA exposure.",
    ),
)


def get_phase_5_qa_intermediate_inventory() -> tuple[QaIntermediateInventoryItem, ...]:
    """Return the Phase 5 QA and intermediate parity inventory."""

    return _INVENTORY


def write_phase_5_qa_intermediate_inventory_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[QaIntermediateInventoryItem] | None = None,
    report_relative_path: str | Path = PHASE_5_QA_INTERMEDIATE_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON Phase 5 inventory report without creating binary artifacts."""

    report_items = tuple(items or _INVENTORY)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": PHASE_5_QA_INTERMEDIATE_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_category": _counts_by("category", report_items),
        "counts_by_parity_status": _counts_by("parity_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "phase_5_runtime_changes": False,
        "notes": (
            "Phase 5 is inventory, contract, and verification-planning only. It does not "
            "generate QA or intermediate artifacts, change science logic, or claim notebook-value parity."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[QaIntermediateInventoryItem],
) -> dict[str, int]:
    if field_name == "category":
        counts = {value: 0 for value in sorted(ALLOWED_CATEGORIES)}
    elif field_name == "parity_status":
        counts = {value: 0 for value in sorted(ALLOWED_PARITY_STATUSES)}
    elif field_name == "implementation_status":
        counts = {value: 0 for value in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    else:
        raise ValueError(f"unsupported count field: {field_name}")

    for item in items:
        counts[getattr(item, field_name)] += 1
    return counts
