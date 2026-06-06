from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Iterable

from app.pipeline.parity import resolve_run_output_path


SPECIAL_TRACK_J1_SCHEMA_VERSION = "special_track_j1_tesla_flow_decomposition_v1"
SPECIAL_TRACK_J1_REPORT_RELATIVE_PATH = (
    "manifests/special_track_j1_tesla_flow_decomposition.json"
)

ALLOWED_CATEGORIES = {
    "data_acquisition",
    "roi_grid_alignment",
    "raster_feature_writer",
    "private_map_artifact",
    "private_classifier_scoring",
    "ml_model_attempt",
    "dataset_training",
    "generated_overlay_ui",
    "public_exposure",
    "provenance_report",
    "duplicate_or_variant",
    "unsupported_or_unclear",
    "blocked_by_policy",
}

ALLOWED_MAPPING_TARGETS = {
    "Phase A — map point picker + ROI/grid preview",
    "Phase B — controlled backend Earth Engine run flow",
    "Phase C — defensible raster/feature writers",
    "Phase D — private map artifact writers",
    "Phase E — private parity verifier against frozen notebook outputs",
    "Phase F — private neutral CLI classifier",
    "Special Track G/G1 — controlled location overlay policy",
    "Special Track G2 — operator-only private generated-overlay UI",
    "Special Track H/H1 — deep-learning feasibility",
    "Special Track I/I1 — real dataset/training design",
    "future_slice_required",
    "blocked_do_not_port",
    "duplicate_excluded",
}

ALLOWED_CURRENT_STATUSES = {
    "covered_by_completed_phase",
    "design_only_completed",
    "future_slice_required",
    "blocked_missing_data",
    "blocked_missing_weights",
    "blocked_policy",
    "duplicate_excluded",
    "unsupported_unclear",
    "do_not_port_as_is",
}

ALLOWED_IMPLEMENTATION_DECISIONS = {
    "already_covered",
    "decompose_before_implementation",
    "future_private_slice",
    "future_operator_only_slice",
    "future_ml_feasibility_required",
    "future_dataset_required",
    "future_public_exposure_review_required",
    "blocked_do_not_port",
    "duplicate_ignore",
    "research_only",
}

RECOMMENDED_FUTURE_EXECUTION_ORDER = (
    "J2 optional: source-lock one future private slice from this decomposition",
    "H1 revisit: update model feasibility ranking after I1 data gates",
    "I2 optional: build private dataset pack outside git only after evidence gates pass",
    "H2 optional: dependency sandbox only if model path and validation gates justify it",
    "Phase C follow-up: add one formula-backed private raster writer at a time",
    "Phase D follow-up: add one filesystem-only private map writer at a time",
    "Phase E follow-up: add verifier comparators only with frozen references",
    "G2 implementation slice: add auth and role policy before any overlay UI",
    "Later public exposure review: separate user approval before any public map surface",
)


@dataclass(frozen=True)
class TeslaFlowDecompositionItem:
    id: str
    name: str
    source_evidence: str
    category: str
    description: str
    notebook_behavior: str
    app_mapping_target: str
    current_status: str
    implementation_decision: str
    data_inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    requires_earth_engine: bool
    requires_raster_writer: bool
    requires_private_artifact_writer: bool
    requires_classifier: bool
    requires_ml_model: bool
    requires_dataset: bool
    requires_weights: bool
    requires_operator_ui: bool
    requires_public_exposure: bool
    requires_artifact_serving_change: bool
    private_only: bool
    public_allowed_now: bool
    blocked_reason: str
    recommended_future_slice: str
    dependencies: tuple[str, ...]
    risk_level: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _item(
    *,
    id: str,
    name: str,
    source_evidence: str,
    category: str,
    description: str,
    notebook_behavior: str,
    app_mapping_target: str,
    current_status: str,
    implementation_decision: str,
    data_inputs: tuple[str, ...],
    outputs: tuple[str, ...],
    requires_earth_engine: bool = False,
    requires_raster_writer: bool = False,
    requires_private_artifact_writer: bool = False,
    requires_classifier: bool = False,
    requires_ml_model: bool = False,
    requires_dataset: bool = False,
    requires_weights: bool = False,
    requires_operator_ui: bool = False,
    requires_public_exposure: bool = False,
    requires_artifact_serving_change: bool = False,
    private_only: bool = True,
    public_allowed_now: bool = False,
    blocked_reason: str,
    recommended_future_slice: str,
    dependencies: tuple[str, ...],
    risk_level: str,
    notes: str,
) -> TeslaFlowDecompositionItem:
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"unsupported category: {category}")
    if app_mapping_target not in ALLOWED_MAPPING_TARGETS:
        raise ValueError(f"unsupported mapping target: {app_mapping_target}")
    if current_status not in ALLOWED_CURRENT_STATUSES:
        raise ValueError(f"unsupported status: {current_status}")
    if implementation_decision not in ALLOWED_IMPLEMENTATION_DECISIONS:
        raise ValueError(f"unsupported decision: {implementation_decision}")
    return TeslaFlowDecompositionItem(
        id=id,
        name=name,
        source_evidence=source_evidence,
        category=category,
        description=description,
        notebook_behavior=notebook_behavior,
        app_mapping_target=app_mapping_target,
        current_status=current_status,
        implementation_decision=implementation_decision,
        data_inputs=data_inputs,
        outputs=outputs,
        requires_earth_engine=requires_earth_engine,
        requires_raster_writer=requires_raster_writer,
        requires_private_artifact_writer=requires_private_artifact_writer,
        requires_classifier=requires_classifier,
        requires_ml_model=requires_ml_model,
        requires_dataset=requires_dataset,
        requires_weights=requires_weights,
        requires_operator_ui=requires_operator_ui,
        requires_public_exposure=requires_public_exposure,
        requires_artifact_serving_change=requires_artifact_serving_change,
        private_only=private_only,
        public_allowed_now=public_allowed_now,
        blocked_reason=blocked_reason,
        recommended_future_slice=recommended_future_slice,
        dependencies=dependencies,
        risk_level=risk_level,
        notes=notes,
    )


_ITEMS = (
    _item(
        id="j1_roi_grid_alignment",
        name="ROI and master GRID setup",
        source_evidence="docs/Notebook_Cells_E.md cells 9-18 and 91-94; Phase A contract",
        category="roi_grid_alignment",
        description="Selected point, ROI windows, master GRID metadata, and local pre-run GRID preview.",
        notebook_behavior="Notebook prints point/ROI forms, builds GRID dictionaries, and audits alignment.",
        app_mapping_target="Phase A — map point picker + ROI/grid preview",
        current_status="covered_by_completed_phase",
        implementation_decision="already_covered",
        data_inputs=("operator point", "ROI size", "GRID settings"),
        outputs=("preview metadata", "GRID preview summary"),
        blocked_reason="No J1 runtime work required; Phase A covers preview-only behavior.",
        recommended_future_slice="No new slice unless ROI shapes beyond point-centered preview are approved.",
        dependencies=("docs/IMPLEMENTATION_PHASE_A_MAP_ROI_PREVIEW.md",),
        risk_level="low",
        notes="Exact coordinate artifacts remain outside public DTOs.",
    ),
    _item(
        id="j1_controlled_data_acquisition",
        name="Controlled data acquisition and provider queries",
        source_evidence="docs/Notebook_Cells_E.md cells 20-24, 76-81, 94, 145, 205, 211-212; Phase B contract",
        category="data_acquisition",
        description="Sentinel, Landsat, SAR, and DEM acquisition steps that require controlled backend planning.",
        notebook_behavior="Notebook performs Earth Engine collection queries and Colab-style auth/folder behavior.",
        app_mapping_target="Phase B — controlled backend Earth Engine run flow",
        current_status="future_slice_required",
        implementation_decision="decompose_before_implementation",
        data_inputs=("point/ROI", "date window", "provider filters", "cloud or SAR filters"),
        outputs=("query plan metadata", "future controlled acquisition result metadata"),
        requires_earth_engine=True,
        blocked_reason="Phase B added safe planning gates only; real acquisition needs later controlled slices.",
        recommended_future_slice="Add one provider acquisition slice with service-account auth and no Colab behavior.",
        dependencies=("docs/IMPLEMENTATION_PHASE_B_CONTROLLED_EE_RUN_FLOW.md",),
        risk_level="medium",
        notes="No J1 code calls Earth Engine.",
    ),
    _item(
        id="j1_formula_backed_feature_writers",
        name="Formula-backed raster and semantic feature writers",
        source_evidence="docs/Notebook_Cells_E.md cells 95, 97, 99, 104-117, 145-147; Phase C contract",
        category="raster_feature_writer",
        description="Feature and raster writer substeps that may be implemented only when formula and GRID evidence are locked.",
        notebook_behavior="Notebook builds S2, thermal, DEM, hypercube, and AI_BEH-like feature layers on the 640 GRID.",
        app_mapping_target="Phase C — defensible raster/feature writers",
        current_status="future_slice_required",
        implementation_decision="future_private_slice",
        data_inputs=("GRID-aligned arrays", "locked formula evidence", "reference metadata"),
        outputs=("private raster or array feature outputs",),
        requires_raster_writer=True,
        blocked_reason="Only the first Phase C AI_BEH relation writer slice is complete.",
        recommended_future_slice="Select exactly one formula-backed writer family per future Phase C follow-up.",
        dependencies=("docs/IMPLEMENTATION_PHASE_C_DEFENSIBLE_RASTER_FEATURE_WRITERS.md",),
        risk_level="medium",
        notes="No existing formulas are changed by J1.",
    ),
    _item(
        id="j1_private_geojson_and_kmz_artifacts",
        name="Private coordinate-bearing map artifacts",
        source_evidence="docs/Notebook_Cells_E.md cells 119, 122-123, 133, 139, 149, 155-162, 177-181, 190-202, 237, 241",
        category="private_map_artifact",
        description="GeoJSON, KMZ, KML, and heatmap-like outputs with coordinate-bearing private content.",
        notebook_behavior="Notebook writes or displays local map files with precise geometry and point content.",
        app_mapping_target="Phase D — private map artifact writers",
        current_status="future_slice_required",
        implementation_decision="future_private_slice",
        data_inputs=("already-computed private features", "run-local geometry", "redaction policy"),
        outputs=("filesystem-only private map artifacts", "redacted summaries"),
        requires_private_artifact_writer=True,
        blocked_reason="Phase D added only the first private GeoJSON writer; KMZ/heatmap slices remain separate.",
        recommended_future_slice="Add one filesystem-only private map writer at a time after schema review.",
        dependencies=("docs/IMPLEMENTATION_PHASE_D_PRIVATE_MAP_ARTIFACT_WRITERS.md",),
        risk_level="high",
        notes="Public serving is blocked; coordinate content remains private.",
    ),
    _item(
        id="j1_frozen_reference_and_report_checks",
        name="Private reports and frozen-reference checks",
        source_evidence="docs/Notebook_Cells_E.md cells 57, 93, 124-125, 195, 228-230; Phase E contract",
        category="provenance_report",
        description="QA reports, alignment reports, reference checks, and frozen-reference verifier behavior.",
        notebook_behavior="Notebook writes or prints QA tables, reports, and reference comparison utilities.",
        app_mapping_target="Phase E — private parity verifier against frozen notebook outputs",
        current_status="covered_by_completed_phase",
        implementation_decision="already_covered",
        data_inputs=("app output directory", "frozen notebook reference bundle", "family filters"),
        outputs=("private verifier JSON report", "family status metadata"),
        blocked_reason="No J1 runtime work required; future comparators need frozen references.",
        recommended_future_slice="Add dedicated comparators only after family reference bundles exist.",
        dependencies=("docs/IMPLEMENTATION_PHASE_E_PRIVATE_PARITY_VERIFIER.md",),
        risk_level="low",
        notes="Runtime output presence remains separate from notebook-value parity.",
    ),
    _item(
        id="j1_private_neutral_classifier_scoring",
        name="Private neutral classifier and score aggregation",
        source_evidence="docs/Notebook_Cells_E.md cells 120-135, 169, 173, 180-182, 187-190, 235-240; Phase F contract",
        category="private_classifier_scoring",
        description="Rule-style classifier and score outputs that must remain neutral, private, CLI-only, and probability/score based.",
        notebook_behavior="Notebook contains large rule and model-driver variants with original labels and local outputs.",
        app_mapping_target="Phase F — private neutral CLI classifier",
        current_status="covered_by_completed_phase",
        implementation_decision="decompose_before_implementation",
        data_inputs=("private local score manifest", "neutral class mapping", "run-local inputs"),
        outputs=("private neutral classifier report",),
        requires_classifier=True,
        blocked_reason="Phase F covers the safe CLI boundary; full rule variants need source-locked slices.",
        recommended_future_slice="Recover one neutral rule slice at a time only if source and reference outputs are locked.",
        dependencies=("docs/IMPLEMENTATION_PHASE_F_PRIVATE_CLI_CLASSIFIER.md",),
        risk_level="medium",
        notes="J1 does not change classifier runtime logic.",
    ),
    _item(
        id="j1_generated_operator_overlay_ui",
        name="Generated private overlay UI behavior",
        source_evidence="docs/Notebook_Cells_E.md cell 243; Special Track G2 contract",
        category="generated_overlay_ui",
        description="Later operator-only UI review for generated private overlay results after outputs exist.",
        notebook_behavior="Notebook draws generated probability matrices, markers, buffers, and paths on an interactive map.",
        app_mapping_target="Special Track G2 — operator-only private generated-overlay UI",
        current_status="design_only_completed",
        implementation_decision="future_operator_only_slice",
        data_inputs=("generated private overlay artifacts", "per-run authorization context"),
        outputs=("future operator-only preview",),
        requires_operator_ui=True,
        blocked_reason="Requires auth, role checks, per-run authorization, audit logging, and default-off config.",
        recommended_future_slice="Start with auth and role policy before any overlay UI implementation.",
        dependencies=("docs/SPECIAL_TRACK_G2_OPERATOR_ONLY_OVERLAY_UI_DESIGN.md",),
        risk_level="high",
        notes="No UI implementation is added in J1.",
    ),
    _item(
        id="j1_public_exact_coordinate_exposure",
        name="Public exact-coordinate exposure",
        source_evidence="docs/Notebook_Cells_E.md cells 139, 149, 191, 200, 237, 241, 243; Special Track G1 contract",
        category="public_exposure",
        description="Any future public exact-coordinate map, DTO, tile, download, or overlay behavior.",
        notebook_behavior="Notebook local outputs and live maps include precise geometry or exact point content.",
        app_mapping_target="Special Track G/G1 — controlled location overlay policy",
        current_status="blocked_policy",
        implementation_decision="future_public_exposure_review_required",
        data_inputs=("private map artifacts", "redaction review", "access-control review"),
        outputs=("none in J1",),
        requires_public_exposure=True,
        blocked_reason="Public exact-coordinate exposure is blocked pending explicit later approval and serving review.",
        recommended_future_slice="Run a separate public-exposure review only if the user approves that direction.",
        dependencies=("docs/SPECIAL_TRACK_G_EXACT_COORDINATE_OVERLAY_ACCESS_CONTROL.md",),
        risk_level="blocked",
        notes="J1 makes no API, frontend, or artifact-serving change.",
    ),
    _item(
        id="j1_ml_model_attempts",
        name="Deep-learning and pretrained model attempts",
        source_evidence="docs/Notebook_Cells_E.md cells 148, 150-151, 174-178, 184, 231-236, 238-240; H1 contract",
        category="ml_model_attempt",
        description="CNN, segmentation, object detector, pretrained, and custom model attempts.",
        notebook_behavior="Notebook tries model libraries, model builders, and detector-style routines.",
        app_mapping_target="Special Track H/H1 — deep-learning feasibility",
        current_status="blocked_missing_data",
        implementation_decision="future_ml_feasibility_required",
        data_inputs=("private dataset", "locked labels", "feature or chip schema"),
        outputs=("future private probability or score outputs only",),
        requires_ml_model=True,
        requires_dataset=True,
        requires_weights=True,
        blocked_reason="H1 and I1 gates block ML runtime until data, weights, dependencies, and validation are accepted.",
        recommended_future_slice="Revisit H1 after I1 quantitative gates are applied to real candidate data.",
        dependencies=("docs/SPECIAL_TRACK_H_DEEP_LEARNING_FEASIBILITY.md", "docs/ML_DATA_TRAINING_READINESS_PLAN.md"),
        risk_level="blocked",
        notes="No training or inference is added by J1.",
    ),
    _item(
        id="j1_training_dataset_cells",
        name="Training cells and dataset construction ideas",
        source_evidence="docs/Notebook_Cells_E.md cells 163-168; I1 contract",
        category="dataset_training",
        description="Training scaffolding and dataset ideas that require independent evidence-backed labels.",
        notebook_behavior="Notebook sketches training over labeled examples and pre-training checks.",
        app_mapping_target="Special Track I/I1 — real dataset/training design",
        current_status="blocked_missing_data",
        implementation_decision="future_dataset_required",
        data_inputs=("independent evidence labels", "dataset manifest", "leakage-safe splits"),
        outputs=("future private dataset pack outside git",),
        requires_dataset=True,
        blocked_reason="I1 design is complete; real dataset creation remains blocked until all gates are satisfied.",
        recommended_future_slice="Create a private dataset pack only after independent evidence and numeric gates are set.",
        dependencies=("docs/SPECIAL_TRACK_I_DATASET_TRAINING_DESIGN.md",),
        risk_level="blocked",
        notes="J1 does not create a dataset.",
    ),
    _item(
        id="j1_future_private_slice_bucket",
        name="Future private decomposition slice bucket",
        source_evidence="docs/Notebook_Cells_E.md phases K-S; selected future work needs source/reference review",
        category="blocked_by_policy",
        description="Small future implementation slices that are not covered by A-F or G/H/I yet.",
        notebook_behavior="Notebook mixes drivers, file scans, variants, and output writers in long dependent cells.",
        app_mapping_target="future_slice_required",
        current_status="future_slice_required",
        implementation_decision="decompose_before_implementation",
        data_inputs=("source cell", "reference output", "safety policy"),
        outputs=("one narrow future module per approved slice",),
        blocked_reason="Future slices need separate user approval and must not become a monolithic engine.",
        recommended_future_slice="Create a J2 source-lock task for exactly one candidate substep if needed.",
        dependencies=("docs/SELECTED_NOTEBOOK_CAPABILITIES_IMPLEMENTATION_ROADMAP.md",),
        risk_level="medium",
        notes="This bucket records future work only; it adds no runtime path.",
    ),
    _item(
        id="j1_duplicate_variants",
        name="Duplicate notebook variants and repeated cells",
        source_evidence="docs/Notebook_Cells_E.md cells 100-101, 107-108, 126, 132-134, 136-138, 142-144, 158-162, 180-182, 200-201",
        category="duplicate_or_variant",
        description="Repeated, obsolete, display-only, or variant cells that should map to canonical substeps or be ignored.",
        notebook_behavior="Notebook repeats prior operations, display checks, and output variants.",
        app_mapping_target="duplicate_excluded",
        current_status="duplicate_excluded",
        implementation_decision="duplicate_ignore",
        data_inputs=("canonical substep reference",),
        outputs=("none",),
        private_only=False,
        blocked_reason="Duplicates are excluded unless a canonical substep later needs a source/reference slice.",
        recommended_future_slice="No implementation; map any useful detail to the canonical substep.",
        dependencies=("docs/Notebook_Cells_E.md",),
        risk_level="low",
        notes="This prevents duplicate notebook cells from becoming duplicate app modules.",
    ),
    _item(
        id="j1_unsupported_unclear_cells",
        name="Unsupported, broken, or unclear notebook cells",
        source_evidence="docs/Notebook_Cells_E.md cells 150-154, 171, 183, 203-215, 216-230, 233",
        category="unsupported_or_unclear",
        description="Cells with package installs, Colab automation, broken class definitions, Drive scans, manual uploads, or unclear state.",
        notebook_behavior="Notebook performs environment setup, local scans, manual upload preparation, or broken model code.",
        app_mapping_target="blocked_do_not_port",
        current_status="unsupported_unclear",
        implementation_decision="blocked_do_not_port",
        data_inputs=("unclear notebook state",),
        outputs=("none",),
        blocked_reason="Unsupported or unclear cells are not implementation-ready and must not be ported as-is.",
        recommended_future_slice="Document only; require a new source/reference task before any reconsideration.",
        dependencies=("docs/Notebook_Cells_E.md",),
        risk_level="blocked",
        notes="No dependency install or Colab automation is added.",
    ),
    _item(
        id="j1_monolithic_tesla_flow_block",
        name="Monolithic Tesla-style driver flow",
        source_evidence="docs/Notebook_Cells_E.md cells 96, 171, 173, 240; roadmap non-negotiable rules",
        category="blocked_by_policy",
        description="Notebook driver-style cells that try to run many acquisition, feature, classifier, map, and model steps together.",
        notebook_behavior="Notebook driver cells sequence large dependent blocks and rely on global notebook state.",
        app_mapping_target="blocked_do_not_port",
        current_status="do_not_port_as_is",
        implementation_decision="blocked_do_not_port",
        data_inputs=("global notebook variables", "cell order state", "manual files"),
        outputs=("none",),
        requires_earth_engine=True,
        requires_raster_writer=True,
        requires_private_artifact_writer=True,
        requires_classifier=True,
        requires_ml_model=True,
        requires_dataset=True,
        requires_weights=True,
        requires_operator_ui=True,
        requires_public_exposure=True,
        blocked_reason="The full flow must be decomposed into small approved modules before any runtime work.",
        recommended_future_slice="Never port as one block; select one safe substep and open a later user-approved task.",
        dependencies=("docs/SELECTED_NOTEBOOK_CAPABILITIES_IMPLEMENTATION_ROADMAP.md",),
        risk_level="blocked",
        notes="J1 is the decomposition decision that keeps this blocked.",
    ),
)


def get_special_track_j1_tesla_flow_decomposition() -> tuple[TeslaFlowDecompositionItem, ...]:
    return _ITEMS


def get_recommended_future_execution_order() -> tuple[str, ...]:
    return RECOMMENDED_FUTURE_EXECUTION_ORDER


def _counts_by(field: str, items: Iterable[TeslaFlowDecompositionItem]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = getattr(item, field)
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def write_special_track_j1_tesla_flow_decomposition_report(
    *,
    run_dir: str | Path,
    run_id: str,
    items: Iterable[TeslaFlowDecompositionItem] | None = None,
    report_relative_path: str | Path = SPECIAL_TRACK_J1_REPORT_RELATIVE_PATH,
) -> Path:
    report_items = tuple(items or _ITEMS)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": SPECIAL_TRACK_J1_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_category": _counts_by("category", report_items),
        "counts_by_mapping_target": _counts_by("app_mapping_target", report_items),
        "counts_by_current_status": _counts_by("current_status", report_items),
        "counts_by_implementation_decision": _counts_by(
            "implementation_decision",
            report_items,
        ),
        "recommended_future_execution_order": RECOMMENDED_FUTURE_EXECUTION_ORDER,
        "j1_decomposition_only": True,
        "runtime_added": False,
        "training_added": False,
        "inference_added": False,
        "weights_downloaded": False,
        "dataset_created": False,
        "earth_engine_calls_added": False,
        "public_exposure_changes": False,
        "artifact_generation": False,
        "notes": (
            "J1 maps notebook substeps to completed phases and special tracks. "
            "It does not add runtime behavior, model work, public exposure, or artifact generation."
        ),
    }
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return report_path
