from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.ai_beh_anchor_decision import (
    get_ai_beh_anchor_pattern_decisions,
)
from app.pipeline.parity.aliases import DEFAULT_RASTER_TENSOR_ALIAS_SPECS
from app.pipeline.parity.classifier_model_inventory import (
    get_phase_7_classifier_model_inventory,
)
from app.pipeline.parity.dem_curv_laplacian_verify import (
    verify_dem_curv_laplacian_parity,
)
from app.pipeline.parity.dem_curvature_reconstruction import (
    get_dem_curvature_reconstruction_registry,
)
from app.pipeline.parity.dem_plan_profile_recovery import (
    get_dem_plan_profile_recovery_checklist,
)
from app.pipeline.parity.hypercube_res25_recovery import (
    get_hypercube_res25_recovery_checklist,
)
from app.pipeline.parity.hypercube_res25_verify import (
    verify_hypercube_res25_parity,
)
from app.pipeline.parity.missing_rasters import get_missing_raster_registry
from app.pipeline.parity.pan_components_verify import verify_pan_components_parity
from app.pipeline.parity.pan_stack_recovery import get_pan_stack_recovery_checklist
from app.pipeline.parity.pan_stack_verify import verify_pan_stack_parity
from app.pipeline.parity.private_map_artifact_inventory import (
    get_phase_6_private_map_artifact_inventory,
)
from app.pipeline.parity.probability_only_classifier_design import (
    get_phase_8_probability_only_classifier_design,
)
from app.pipeline.parity.qa_intermediate_inventory import (
    get_phase_5_qa_intermediate_inventory,
)
from app.pipeline.parity.report_640_verify import verify_report_640_parity
from app.pipeline.parity.s1_filtered_stack_recovery import (
    get_s1_filtered_stack_recovery_checklist,
)
from app.pipeline.parity.s1_filtered_stack_verify import (
    verify_s1_filtered_stack_parity,
)
from app.pipeline.parity.sar_asc_desc_recovery import (
    get_sar_asc_desc_recovery_checklist,
)
from app.pipeline.parity.sar_asc_desc_verify import (
    verify_sar_asc_desc_support_stack_parity,
)
from app.pipeline.parity.secret_layers_verify import verify_secret_layers_parity
from app.pipeline.parity.semantic_raster_recovery import (
    get_semantic_raster_recovery_inventory,
)
from app.pipeline.parity.v6_package import TIMESTAMPED_TOP25_PREFIX, V6_REQUIRED_INPUT_FILES


PHASE_9_END_TO_END_HARNESS_SCHEMA_VERSION = "phase_9_end_to_end_parity_harness_v1"
PHASE_9_END_TO_END_HARNESS_REPORT_RELATIVE_PATH = (
    "manifests/end_to_end_notebook_parity_report.json"
)

ALLOWED_FAMILY_STATUSES = {
    "passed",
    "failed",
    "incomplete",
    "reference_missing",
    "app_output_missing",
    "comparison_unavailable",
    "inventory_only",
    "design_only",
    "decision_only",
    "verifier_not_available",
    "skipped_by_request",
    "error",
}

ALLOWED_OVERALL_STATUSES = {
    "passed",
    "failed",
    "incomplete",
    "comparison_unavailable",
    "inventory_only",
    "error",
}

APP_OUTPUT_STATUS_VALUES = {
    "present",
    "missing",
    "mixed",
    "not_checked",
}

REFERENCE_STATUS_VALUES = {
    "present",
    "missing",
    "mixed",
    "not_checked",
}

DEFAULT_FAMILY_ORDER = (
    "phase0_expected_outputs",
    "v6_package",
    "aliases",
    "missing_raster_families",
    "report_640",
    "secret_layers",
    "dem_curvature",
    "sar_asc_desc",
    "s1_filtered_stack",
    "pan_stack",
    "pan_components",
    "hypercube_res25",
    "semantic_rasters",
    "qa_intermediate",
    "private_map_artifacts",
    "classifier_model",
    "probability_only_design",
)

_PHASE0_EXPECTED_OUTPUTS_PATH = Path("docs/parity_expected_outputs.json")
_PHASE0_INVENTORY_DOC = "docs/PARITY_PHASE_0_OUTPUT_INVENTORY_LOCK.md"
_V6_PACKAGE_DOC = "docs/V6_PACKAGE_PARITY_CONTRACT.md"
_ALIASES_DOC = "docs/RASTER_TENSOR_PARITY_ALIAS_CONTRACT.md"
_MISSING_RASTERS_DOC = "docs/MISSING_RASTER_FAMILIES_CONTRACT.md"
_REPORT_640_DOC = "docs/REPORT_640_PARITY_VERIFICATION_CONTRACT.md"
_SECRET_LAYERS_DOC = "docs/SECRET_LAYERS_PARITY_VERIFICATION_CONTRACT.md"
_DEM_CURVATURE_DOC = (
    "docs/DEM_CURV_LAPLACIAN_PARITY_VERIFICATION_CONTRACT.md; "
    "docs/DEM_CURVATURE_PARITY_RECONSTRUCTION.md"
)
_SAR_ASC_DESC_DOC = (
    "docs/SAR_ASC_DESC_SUPPORT_STACK_VERIFICATION_CONTRACT.md; "
    "docs/SAR_ASC_DESC_SUPPORT_STACK_RECOVERY.md"
)
_S1_FILTERED_DOC = "docs/S1_FILTERED_LAYERS_STACK_PARITY_CONTRACT.md"
_PAN_STACK_DOC = "docs/PAN_LAYERS_STACK_PARITY_CONTRACT.md"
_PAN_COMPONENTS_DOC = "docs/PAN_COMPONENTS_PARITY_VERIFICATION_CONTRACT.md"
_HYPERCUBE_RES25_DOC = "docs/HYPERCUBE_RES_2P5M_PARITY_CONTRACT.md"
_SEMANTIC_DOC = (
    "docs/SEMANTIC_RASTER_RECOVERY_CONTRACT.md; "
    "docs/AI_BEH_ANCHOR_PATTERN_DECISION.md"
)
_QA_INTERMEDIATE_DOC = "docs/PHASE_5_QA_INTERMEDIATE_PARITY_CONTRACT.md"
_PRIVATE_MAP_DOC = "docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md"
_CLASSIFIER_DOC = "docs/PHASE_7_CLASSIFIER_MODEL_PARITY_CONTRACT.md"
_PROBABILITY_DOC = "docs/PHASE_8_PROBABILITY_ONLY_CLASSIFIER_DESIGN.md"


@dataclass(frozen=True)
class EndToEndFamilyResult:
    family_id: str
    contract_doc: str
    module_used: str
    expected_reference_artifacts: tuple[str, ...]
    app_output_status: str
    reference_status: str
    runtime_output_verified: bool
    notebook_value_parity_verified: bool
    comparison_status: str
    status: str
    blocker: str
    recommended_next_action: str
    notes: str

    def __post_init__(self) -> None:
        if self.status not in ALLOWED_FAMILY_STATUSES:
            raise ValueError(f"unsupported family status: {self.status}")
        if self.comparison_status not in ALLOWED_FAMILY_STATUSES:
            raise ValueError(
                f"unsupported family comparison status: {self.comparison_status}"
            )
        if self.app_output_status not in APP_OUTPUT_STATUS_VALUES:
            raise ValueError(f"unsupported app_output_status: {self.app_output_status}")
        if self.reference_status not in REFERENCE_STATUS_VALUES:
            raise ValueError(f"unsupported reference_status: {self.reference_status}")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EndToEndParityHarnessResult:
    report_path: Path
    overall_status: str
    families: tuple[EndToEndFamilyResult, ...]
    runtime_output_verified: bool
    notebook_value_parity_verified: bool


@dataclass(frozen=True)
class FamilyDefinition:
    family_id: str
    contract_doc: str
    module_used: str
    expected_reference_artifacts: tuple[str, ...]
    collector: Callable[..., EndToEndFamilyResult]


def run_end_to_end_notebook_parity_harness(
    *,
    app_output_dir: str | Path,
    reference_bundle_dir: str | Path,
    run_dir: str | Path,
    run_id: str,
    selected_families: Iterable[str] | None = None,
    tolerances: Mapping[str, Mapping[str, float]] | None = None,
    report_relative_path: str | Path = PHASE_9_END_TO_END_HARNESS_REPORT_RELATIVE_PATH,
) -> EndToEndParityHarnessResult:
    """Run the repository-supported end-to-end notebook parity harness."""

    app_root = Path(app_output_dir)
    reference_root = Path(reference_bundle_dir)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    selected = tuple(selected_families or DEFAULT_FAMILY_ORDER)
    unknown = sorted(set(selected) - set(FAMILY_REGISTRY))
    if unknown:
        raise ValueError(f"unsupported parity families: {', '.join(unknown)}")

    tolerances_map = dict(tolerances or {})
    app_dir_exists = app_root.is_dir()
    reference_dir_exists = reference_root.is_dir()

    if not app_dir_exists or not reference_dir_exists:
        family_results = tuple(
            _missing_directory_family_result(
                FAMILY_REGISTRY[family_id],
                app_dir_exists=app_dir_exists,
                reference_dir_exists=reference_dir_exists,
            )
            for family_id in selected
        )
    else:
        family_results = tuple(
            FAMILY_REGISTRY[family_id].collector(
                app_output_dir=app_root,
                reference_bundle_dir=reference_root,
                run_dir=Path(run_dir),
                run_id=run_id,
                tolerances=tolerances_map.get(family_id, {}),
            )
            for family_id in selected
        )

    overall_status = _overall_status(family_results)
    runtime_output_verified = _overall_runtime_verified(family_results)
    notebook_value_parity_verified = overall_status == "passed"
    payload = {
        "schema_version": PHASE_9_END_TO_END_HARNESS_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "app_output_dir": str(app_root),
        "reference_bundle_dir": str(reference_root),
        "selected_families": list(selected),
        "families": [item.to_dict() for item in family_results],
        "counts_by_family_status": _counts_by_status(family_results),
        "overall_status": overall_status,
        "runtime_output_verified": runtime_output_verified,
        "notebook_value_parity_verified": notebook_value_parity_verified,
        "phase_9_runtime_changes": False,
        "public_exposure_changes": False,
        "earth_engine_calls_added": False,
        "artifact_generation": False,
        "notes": (
            "Phase 9 is an end-to-end parity harness only. It does not generate app outputs, "
            "does not run the live pipeline, does not call Earth Engine, and keeps runtime "
            "output presence separate from notebook-value parity."
        ),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return EndToEndParityHarnessResult(
        report_path=report_path,
        overall_status=overall_status,
        families=family_results,
        runtime_output_verified=runtime_output_verified,
        notebook_value_parity_verified=notebook_value_parity_verified,
    )


def _collect_phase0_expected_outputs(
    *,
    app_output_dir: Path,
    reference_bundle_dir: Path,
    run_dir: Path,
    run_id: str,
    tolerances: Mapping[str, float],
) -> EndToEndFamilyResult:
    del app_output_dir, reference_bundle_dir, run_dir, run_id, tolerances
    payload = json.loads(_PHASE0_EXPECTED_OUTPUTS_PATH.read_text(encoding="utf-8"))
    expected_outputs = payload.get("expected_outputs", [])
    return EndToEndFamilyResult(
        family_id="phase0_expected_outputs",
        contract_doc=_PHASE0_INVENTORY_DOC,
        module_used="docs/parity_expected_outputs.json",
        expected_reference_artifacts=(
            "frozen notebook output bundle aligned to docs/parity_expected_outputs.json",
        ),
        app_output_status="not_checked",
        reference_status="not_checked",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        comparison_status="inventory_only",
        status="inventory_only",
        blocker="Phase 0 is a source-of-truth inventory, not a run-level verifier.",
        recommended_next_action=(
            "Use the family-specific verifiers and inventories recorded by later phases."
        ),
        notes=(
            f"Phase 0 tracks {len(expected_outputs)} expected notebook outputs. "
            "The end-to-end harness records the inventory without treating it as a pass condition."
        ),
    )


def _collect_v6_package_family(
    *,
    app_output_dir: Path,
    reference_bundle_dir: Path,
    run_dir: Path,
    run_id: str,
    tolerances: Mapping[str, float],
) -> EndToEndFamilyResult:
    del run_dir, run_id, tolerances
    app_names = {path.name for path in app_output_dir.rglob("*") if path.is_file()}
    reference_names = {
        path.name for path in reference_bundle_dir.rglob("*") if path.is_file()
    }
    expected_reference_artifacts = V6_REQUIRED_INPUT_FILES + (
        f"{TIMESTAMPED_TOP25_PREFIX}*.csv",
        f"{TIMESTAMPED_TOP25_PREFIX}*.geojson",
    )
    app_has_any = any(name in app_names for name in V6_REQUIRED_INPUT_FILES)
    reference_has_core = all(name in reference_names for name in V6_REQUIRED_INPUT_FILES)
    reference_has_timestamped = any(
        name.startswith(TIMESTAMPED_TOP25_PREFIX) and name.endswith(".csv")
        for name in reference_names
    ) and any(
        name.startswith(TIMESTAMPED_TOP25_PREFIX) and name.endswith(".geojson")
        for name in reference_names
    )
    if not reference_has_core or not reference_has_timestamped:
        return EndToEndFamilyResult(
            family_id="v6_package",
            contract_doc=_V6_PACKAGE_DOC,
            module_used="app.pipeline.parity.v6_package.import_v6_package (not invoked)",
            expected_reference_artifacts=expected_reference_artifacts,
            app_output_status="present" if app_has_any else "missing",
            reference_status="missing",
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            comparison_status="reference_missing",
            status="reference_missing",
            blocker="Frozen notebook v6 package bundle is missing required files.",
            recommended_next_action=(
                "Provide the frozen v6 package bundle before any end-to-end v6 parity run."
            ),
            notes=(
                "The harness does not invoke the package import helper because that helper "
                "writes parity artifacts."
            ),
        )
    if not app_has_any:
        return EndToEndFamilyResult(
            family_id="v6_package",
            contract_doc=_V6_PACKAGE_DOC,
            module_used="app.pipeline.parity.v6_package.import_v6_package (not invoked)",
            expected_reference_artifacts=expected_reference_artifacts,
            app_output_status="missing",
            reference_status="present",
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            comparison_status="app_output_missing",
            status="app_output_missing",
            blocker="App output directory does not contain a v6 package family to compare.",
            recommended_next_action=(
                "Add a separate source-approved runtime slice before expecting v6 package parity."
            ),
            notes=(
                "Phase 9 records the missing app-side v6 package family without importing or rebuilding files."
            ),
        )
    return EndToEndFamilyResult(
        family_id="v6_package",
        contract_doc=_V6_PACKAGE_DOC,
        module_used="app.pipeline.parity.v6_package.import_v6_package (not invoked)",
        expected_reference_artifacts=expected_reference_artifacts,
        app_output_status="present",
        reference_status="present",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        comparison_status="verifier_not_available",
        status="verifier_not_available",
        blocker="The existing v6 package helper writes artifacts and is not a side-effect-free verifier.",
        recommended_next_action=(
            "Add a dedicated read-only v6 package parity verifier before treating this family as comparable."
        ),
        notes="Phase 9 keeps the v6 package family out of pass criteria until a read-only verifier exists.",
    )


def _collect_aliases_family(
    *,
    app_output_dir: Path,
    reference_bundle_dir: Path,
    run_dir: Path,
    run_id: str,
    tolerances: Mapping[str, float],
) -> EndToEndFamilyResult:
    del run_dir, run_id, tolerances
    source_presence = []
    reference_presence = []
    for spec in DEFAULT_RASTER_TENSOR_ALIAS_SPECS:
        source_presence.append(
            any((app_output_dir / source).is_file() for source in spec.source_paths)
        )
        reference_presence.append(
            (reference_bundle_dir / spec.notebook_name_or_pattern).is_file()
            or (reference_bundle_dir / spec.parity_path).is_file()
        )
    app_output_status = _presence_to_status(source_presence)
    reference_status = _presence_to_status(reference_presence)
    if reference_status == "missing":
        family_status = "reference_missing"
        blocker = "Frozen notebook alias targets are missing for the raster/tensor alias family."
        next_action = "Provide the frozen notebook alias files before alias parity can be checked."
    elif app_output_status == "missing":
        family_status = "app_output_missing"
        blocker = "App output directory is missing the source artifacts that alias parity would copy from."
        next_action = "Create the source app outputs before expecting alias parity coverage."
    else:
        family_status = "verifier_not_available"
        blocker = "The alias helper copies files into the parity tree and is not a read-only verifier."
        next_action = "Add a read-only alias parity verifier before using the alias family as a pass signal."
    return EndToEndFamilyResult(
        family_id="aliases",
        contract_doc=_ALIASES_DOC,
        module_used="app.pipeline.parity.aliases.copy_alias (not invoked)",
        expected_reference_artifacts=tuple(
            spec.notebook_name_or_pattern for spec in DEFAULT_RASTER_TENSOR_ALIAS_SPECS
        ),
        app_output_status=app_output_status,
        reference_status=reference_status,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        comparison_status=family_status,
        status=family_status,
        blocker=blocker,
        recommended_next_action=next_action,
        notes=(
            "Phase 9 inspects alias source availability only. It does not copy or materialize alias outputs."
        ),
    )


def _collect_missing_raster_family(
    *,
    app_output_dir: Path,
    reference_bundle_dir: Path,
    run_dir: Path,
    run_id: str,
    tolerances: Mapping[str, float],
) -> EndToEndFamilyResult:
    del app_output_dir, reference_bundle_dir, run_dir, run_id, tolerances
    items = get_missing_raster_registry()
    return EndToEndFamilyResult(
        family_id="missing_raster_families",
        contract_doc=_MISSING_RASTERS_DOC,
        module_used="app.pipeline.parity.missing_rasters.get_missing_raster_registry",
        expected_reference_artifacts=tuple(
            pattern
            for item in items
            for pattern in item.notebook_paths_or_patterns
        ),
        app_output_status="not_checked",
        reference_status="not_checked",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        comparison_status="inventory_only",
        status="inventory_only",
        blocker="Missing-raster registry is a recovery inventory, not a comparison verifier.",
        recommended_next_action="Use the dedicated family verifiers where they exist and keep the registry as context only.",
        notes=f"Registry covers {len(items)} missing-raster branches without treating them as a parity pass.",
    )


def _collect_verifier_family(
    *,
    family_id: str,
    contract_doc: str,
    module_used: str,
    expected_reference_artifacts: tuple[str, ...],
    verify_function: Callable[..., Any],
    app_output_dir: Path,
    reference_bundle_dir: Path,
    run_dir: Path,
    run_id: str,
    tolerances: Mapping[str, float],
) -> EndToEndFamilyResult:
    temp_relative_path = Path("manifests") / ".phase9_tmp" / f"{family_id}.json"
    kwargs: dict[str, Any] = {
        "app_output_dir": app_output_dir,
        "notebook_reference_dir": reference_bundle_dir,
        "run_dir": run_dir,
        "run_id": run_id,
        "report_relative_path": temp_relative_path,
    }
    if "atol" in tolerances:
        kwargs["atol"] = float(tolerances["atol"])
    if "rtol" in tolerances:
        kwargs["rtol"] = float(tolerances["rtol"])

    result = verify_function(**kwargs)
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))
    _cleanup_temporary_report(result.report_path, run_dir)

    outputs = tuple(payload.get("outputs", ()))
    app_output_status = _payload_presence_status(payload, outputs, key="app_exists")
    reference_status = _payload_presence_status(payload, outputs, key="reference_exists")
    runtime_output_verified = _payload_runtime_verified(payload, outputs)
    notebook_value_parity_verified = _payload_notebook_value_verified(payload, outputs)
    comparison_status = _family_status_from_verifier_payload(payload, outputs)
    blocker, next_action = _verifier_next_steps(
        comparison_status,
        family_id=family_id,
    )
    payload_notes = str(payload.get("notes", "")).strip()
    if not payload_notes and outputs:
        payload_notes = "; ".join(
            str(item.get("notes", "")).strip()
            for item in outputs
            if str(item.get("notes", "")).strip()
        )

    return EndToEndFamilyResult(
        family_id=family_id,
        contract_doc=contract_doc,
        module_used=module_used,
        expected_reference_artifacts=expected_reference_artifacts,
        app_output_status=app_output_status,
        reference_status=reference_status,
        runtime_output_verified=runtime_output_verified,
        notebook_value_parity_verified=notebook_value_parity_verified,
        comparison_status=comparison_status,
        status=comparison_status,
        blocker=blocker,
        recommended_next_action=next_action,
        notes=payload_notes,
    )


def _collect_dem_curvature_family(
    *,
    app_output_dir: Path,
    reference_bundle_dir: Path,
    run_dir: Path,
    run_id: str,
    tolerances: Mapping[str, float],
) -> EndToEndFamilyResult:
    laplacian = _collect_verifier_family(
        family_id="dem_curvature",
        contract_doc=_DEM_CURVATURE_DOC,
        module_used="app.pipeline.parity.dem_curv_laplacian_verify.verify_dem_curv_laplacian_parity",
        expected_reference_artifacts=(
            "curv_laplacian_640.tif",
            "curv_plan_640.tif",
            "curv_profile_640.tif",
        ),
        verify_function=verify_dem_curv_laplacian_parity,
        app_output_dir=app_output_dir,
        reference_bundle_dir=reference_bundle_dir,
        run_dir=run_dir,
        run_id=run_id,
        tolerances=tolerances,
    )
    reconstruction_items = get_dem_curvature_reconstruction_registry()
    plan_profile_items = get_dem_plan_profile_recovery_checklist()

    if laplacian.status in {
        "failed",
        "reference_missing",
        "app_output_missing",
        "comparison_unavailable",
        "error",
        "incomplete",
    }:
        return EndToEndFamilyResult(
            family_id="dem_curvature",
            contract_doc=_DEM_CURVATURE_DOC,
            module_used=(
                "app.pipeline.parity.dem_curv_laplacian_verify.verify_dem_curv_laplacian_parity; "
                "app.pipeline.parity.dem_curvature_reconstruction.get_dem_curvature_reconstruction_registry; "
                "app.pipeline.parity.dem_plan_profile_recovery.get_dem_plan_profile_recovery_checklist"
            ),
            expected_reference_artifacts=laplacian.expected_reference_artifacts,
            app_output_status=laplacian.app_output_status,
            reference_status=laplacian.reference_status,
            runtime_output_verified=False,
            notebook_value_parity_verified=False,
            comparison_status=laplacian.comparison_status,
            status=laplacian.status,
            blocker=laplacian.blocker,
            recommended_next_action=laplacian.recommended_next_action,
            notes=(
                f"{laplacian.notes} Plan/profile branches remain recovery-only "
                f"({len(reconstruction_items)} reconstruction items, {len(plan_profile_items)} plan/profile items)."
            ).strip(),
        )

    return EndToEndFamilyResult(
        family_id="dem_curvature",
        contract_doc=_DEM_CURVATURE_DOC,
        module_used=(
            "app.pipeline.parity.dem_curv_laplacian_verify.verify_dem_curv_laplacian_parity; "
            "app.pipeline.parity.dem_curvature_reconstruction.get_dem_curvature_reconstruction_registry; "
            "app.pipeline.parity.dem_plan_profile_recovery.get_dem_plan_profile_recovery_checklist"
        ),
        expected_reference_artifacts=(
            "curv_laplacian_640.tif",
            "curv_plan_640.tif",
            "curv_profile_640.tif",
        ),
        app_output_status=laplacian.app_output_status,
        reference_status=laplacian.reference_status,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        comparison_status="verifier_not_available",
        status="verifier_not_available",
        blocker="Only the laplacian branch has a runtime/value verifier; plan and profile remain recovery-only.",
        recommended_next_action="Add plan/profile verifiers before treating the DEM curvature family as fully comparable.",
        notes=(
            f"Laplacian sub-branch status is {laplacian.status}. "
            "Family remains incomplete as an end-to-end verifier surface until plan/profile comparison exists."
        ),
    )


def _collect_inventory_family(
    *,
    family_id: str,
    contract_doc: str,
    module_used: str,
    expected_reference_artifacts: tuple[str, ...],
    status: str,
    get_items: Callable[[], Iterable[Any]],
    app_output_dir: Path,
    reference_bundle_dir: Path,
    run_dir: Path,
    run_id: str,
    tolerances: Mapping[str, float],
) -> EndToEndFamilyResult:
    del app_output_dir, reference_bundle_dir, run_dir, run_id, tolerances
    items = tuple(get_items())
    if items:
        blocker = str(getattr(items[0], "blocker", "")).strip()
        next_action = str(getattr(items[0], "recommended_next_action", "")).strip()
    else:
        blocker = "No inventory items were returned."
        next_action = "Rebuild the inventory helper before using this family in the harness."
    return EndToEndFamilyResult(
        family_id=family_id,
        contract_doc=contract_doc,
        module_used=module_used,
        expected_reference_artifacts=expected_reference_artifacts,
        app_output_status="not_checked",
        reference_status="not_checked",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        comparison_status=status,
        status=status,
        blocker=blocker,
        recommended_next_action=next_action,
        notes=f"Family summarized from {len(items)} inventory or decision items.",
    )


def _missing_directory_family_result(
    definition: FamilyDefinition,
    *,
    app_dir_exists: bool,
    reference_dir_exists: bool,
) -> EndToEndFamilyResult:
    if not reference_dir_exists and not app_dir_exists:
        status = "reference_missing"
        app_status = "missing"
        reference_status = "missing"
        blocker = "App output directory and frozen notebook reference bundle directory are both missing."
    elif not reference_dir_exists:
        status = "reference_missing"
        app_status = "present"
        reference_status = "missing"
        blocker = "Frozen notebook reference bundle directory is missing."
    else:
        status = "app_output_missing"
        app_status = "missing"
        reference_status = "present"
        blocker = "App output directory is missing."
    return EndToEndFamilyResult(
        family_id=definition.family_id,
        contract_doc=definition.contract_doc,
        module_used=definition.module_used,
        expected_reference_artifacts=definition.expected_reference_artifacts,
        app_output_status=app_status,
        reference_status=reference_status,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        comparison_status=status,
        status=status,
        blocker=blocker,
        recommended_next_action=(
            "Provide both directories before treating this family as a runtime or notebook-value comparison."
        ),
        notes="Directory validation happens before any family-specific parity helper is invoked.",
    )


def _payload_presence_status(
    payload: Mapping[str, Any],
    outputs: tuple[Mapping[str, Any], ...],
    *,
    key: str,
) -> str:
    if outputs:
        return _presence_to_status(bool(item.get(key)) for item in outputs)
    if key in payload:
        return "present" if bool(payload.get(key)) else "missing"
    return "not_checked"


def _payload_runtime_verified(
    payload: Mapping[str, Any],
    outputs: tuple[Mapping[str, Any], ...],
) -> bool:
    if outputs:
        return all(bool(item.get("runtime_output_verified")) for item in outputs)
    return bool(payload.get("runtime_output_verified", False))


def _payload_notebook_value_verified(
    payload: Mapping[str, Any],
    outputs: tuple[Mapping[str, Any], ...],
) -> bool:
    if outputs:
        return all(bool(item.get("notebook_value_parity_verified")) for item in outputs)
    return bool(payload.get("notebook_value_parity_verified", False))


def _family_status_from_verifier_payload(
    payload: Mapping[str, Any],
    outputs: tuple[Mapping[str, Any], ...],
) -> str:
    overall_status = str(payload.get("overall_status", "error"))
    output_statuses = {str(item.get("status", "")) for item in outputs}
    if overall_status == "passed":
        return "passed"
    if overall_status == "failed":
        return "failed"
    if overall_status == "comparison_unavailable":
        return "comparison_unavailable"
    if "missing_reference_output" in output_statuses:
        if output_statuses == {"missing_reference_output"}:
            return "reference_missing"
        return "incomplete"
    if "missing_app_output" in output_statuses:
        if output_statuses == {"missing_app_output"}:
            return "app_output_missing"
        return "incomplete"
    if overall_status == "incomplete":
        return "incomplete"
    if overall_status == "error":
        return "error"
    return "error"


def _verifier_next_steps(status: str, *, family_id: str) -> tuple[str, str]:
    if status == "passed":
        return "", "Keep the frozen reference bundle stable and rerun this verifier when app outputs change."
    if status == "reference_missing":
        return (
            "Frozen notebook reference artifacts are missing for this family.",
            "Provide the frozen notebook reference files before expecting notebook-value parity.",
        )
    if status == "app_output_missing":
        return (
            "App output artifacts are missing for this family.",
            "Produce the app outputs in a separate run before using the end-to-end harness.",
        )
    if status == "comparison_unavailable":
        return (
            "Comparison capability is unavailable for this family.",
            "Install the missing optional dependency or rerun on an environment with raster comparison support.",
        )
    if status == "failed":
        return (
            "Runtime outputs and frozen notebook references differ for this family.",
            "Inspect the family-specific parity contract and verifier report details before changing any formulas.",
        )
    if status == "error":
        return (
            "The family verifier raised an internal error.",
            "Inspect the family-specific verifier inputs and report payload before rerunning.",
        )
    return (
        f"Family {family_id} is incomplete.",
        "Review the family-specific contract and reference bundle coverage before treating the family as parity-ready.",
    )


def _presence_to_status(values: Iterable[bool]) -> str:
    values_tuple = tuple(values)
    if not values_tuple:
        return "not_checked"
    if all(values_tuple):
        return "present"
    if any(values_tuple):
        return "mixed"
    return "missing"


def _overall_status(families: Iterable[EndToEndFamilyResult]) -> str:
    statuses = [family.status for family in families]
    if not statuses:
        return "inventory_only"
    if any(status == "error" for status in statuses):
        return "error"
    if any(status == "failed" for status in statuses):
        return "failed"
    if any(status == "comparison_unavailable" for status in statuses):
        return "comparison_unavailable"
    if any(
        status in {
            "reference_missing",
            "app_output_missing",
            "incomplete",
            "verifier_not_available",
        }
        for status in statuses
    ):
        return "incomplete"
    if all(
        status in {"inventory_only", "design_only", "decision_only", "skipped_by_request"}
        for status in statuses
    ):
        return "inventory_only"
    if any(status == "passed" for status in statuses) and all(
        status
        in {"passed", "inventory_only", "design_only", "decision_only", "skipped_by_request"}
        for status in statuses
    ):
        return "passed"
    return "incomplete"


def _overall_runtime_verified(families: Iterable[EndToEndFamilyResult]) -> bool:
    verifier_families = [
        family
        for family in families
        if family.status
        not in {"inventory_only", "design_only", "decision_only", "verifier_not_available", "skipped_by_request"}
    ]
    if not verifier_families:
        return False
    return all(family.runtime_output_verified for family in verifier_families)


def _counts_by_status(families: Iterable[EndToEndFamilyResult]) -> dict[str, int]:
    counts = {value: 0 for value in sorted(ALLOWED_FAMILY_STATUSES)}
    for family in families:
        counts[family.status] += 1
    return counts


def _cleanup_temporary_report(report_path: Path, run_dir: Path) -> None:
    resolved_run_dir = Path(run_dir).resolve()
    resolved_report = report_path.resolve()
    resolved_report.relative_to(resolved_run_dir)
    manifests_root = resolved_run_dir / "manifests"
    if report_path.exists():
        report_path.unlink()
    parent = report_path.parent
    while parent not in {resolved_run_dir, manifests_root} and parent.exists():
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


FAMILY_REGISTRY: dict[str, FamilyDefinition] = {
    "phase0_expected_outputs": FamilyDefinition(
        family_id="phase0_expected_outputs",
        contract_doc=_PHASE0_INVENTORY_DOC,
        module_used="docs/parity_expected_outputs.json",
        expected_reference_artifacts=(
            "frozen notebook output bundle aligned to docs/parity_expected_outputs.json",
        ),
        collector=_collect_phase0_expected_outputs,
    ),
    "v6_package": FamilyDefinition(
        family_id="v6_package",
        contract_doc=_V6_PACKAGE_DOC,
        module_used="app.pipeline.parity.v6_package.import_v6_package (not invoked)",
        expected_reference_artifacts=V6_REQUIRED_INPUT_FILES
        + (f"{TIMESTAMPED_TOP25_PREFIX}*.csv", f"{TIMESTAMPED_TOP25_PREFIX}*.geojson"),
        collector=_collect_v6_package_family,
    ),
    "aliases": FamilyDefinition(
        family_id="aliases",
        contract_doc=_ALIASES_DOC,
        module_used="app.pipeline.parity.aliases.copy_alias (not invoked)",
        expected_reference_artifacts=tuple(
            spec.notebook_name_or_pattern for spec in DEFAULT_RASTER_TENSOR_ALIAS_SPECS
        ),
        collector=_collect_aliases_family,
    ),
    "missing_raster_families": FamilyDefinition(
        family_id="missing_raster_families",
        contract_doc=_MISSING_RASTERS_DOC,
        module_used="app.pipeline.parity.missing_rasters.get_missing_raster_registry",
        expected_reference_artifacts=("frozen notebook outputs for the missing-raster registry",),
        collector=_collect_missing_raster_family,
    ),
    "report_640": FamilyDefinition(
        family_id="report_640",
        contract_doc=_REPORT_640_DOC,
        module_used="app.pipeline.parity.report_640_verify.verify_report_640_parity",
        expected_reference_artifacts=(
            "REPORT_640_Pottery_Report.tif",
            "REPORT_640_Mass_Report.tif",
            "REPORT_640_FINAL_Zero_Point_Targets.tif",
        ),
        collector=lambda **kwargs: _collect_verifier_family(
            family_id="report_640",
            contract_doc=_REPORT_640_DOC,
            module_used="app.pipeline.parity.report_640_verify.verify_report_640_parity",
            expected_reference_artifacts=(
                "REPORT_640_Pottery_Report.tif",
                "REPORT_640_Mass_Report.tif",
                "REPORT_640_FINAL_Zero_Point_Targets.tif",
            ),
            verify_function=verify_report_640_parity,
            **kwargs,
        ),
    ),
    "secret_layers": FamilyDefinition(
        family_id="secret_layers",
        contract_doc=_SECRET_LAYERS_DOC,
        module_used="app.pipeline.parity.secret_layers_verify.verify_secret_layers_parity",
        expected_reference_artifacts=(
            "AI_READY_640_Secret_Gold_Halo.tif",
            "AI_READY_640_Secret_Silver_Oxide.tif",
            "AI_READY_640_Secret_Tunnel_Ceiling.tif",
            "AI_READY_640_Secret_Thermal_Inertia.tif",
            "AI_READY_640_Secret_Chemical_Protector.tif",
            "AI_READY_640_Secret_Hidden_Doors.tif",
        ),
        collector=lambda **kwargs: _collect_verifier_family(
            family_id="secret_layers",
            contract_doc=_SECRET_LAYERS_DOC,
            module_used="app.pipeline.parity.secret_layers_verify.verify_secret_layers_parity",
            expected_reference_artifacts=(
                "AI_READY_640_Secret_Gold_Halo.tif",
                "AI_READY_640_Secret_Silver_Oxide.tif",
                "AI_READY_640_Secret_Tunnel_Ceiling.tif",
                "AI_READY_640_Secret_Thermal_Inertia.tif",
                "AI_READY_640_Secret_Chemical_Protector.tif",
                "AI_READY_640_Secret_Hidden_Doors.tif",
            ),
            verify_function=verify_secret_layers_parity,
            **kwargs,
        ),
    ),
    "dem_curvature": FamilyDefinition(
        family_id="dem_curvature",
        contract_doc=_DEM_CURVATURE_DOC,
        module_used=(
            "app.pipeline.parity.dem_curv_laplacian_verify.verify_dem_curv_laplacian_parity; "
            "app.pipeline.parity.dem_curvature_reconstruction.get_dem_curvature_reconstruction_registry; "
            "app.pipeline.parity.dem_plan_profile_recovery.get_dem_plan_profile_recovery_checklist"
        ),
        expected_reference_artifacts=(
            "curv_laplacian_640.tif",
            "curv_plan_640.tif",
            "curv_profile_640.tif",
        ),
        collector=_collect_dem_curvature_family,
    ),
    "sar_asc_desc": FamilyDefinition(
        family_id="sar_asc_desc",
        contract_doc=_SAR_ASC_DESC_DOC,
        module_used="app.pipeline.parity.sar_asc_desc_verify.verify_sar_asc_desc_support_stack_parity",
        expected_reference_artifacts=tuple(
            item.notebook_output for item in get_sar_asc_desc_recovery_checklist()
        ),
        collector=lambda **kwargs: _collect_verifier_family(
            family_id="sar_asc_desc",
            contract_doc=_SAR_ASC_DESC_DOC,
            module_used="app.pipeline.parity.sar_asc_desc_verify.verify_sar_asc_desc_support_stack_parity",
            expected_reference_artifacts=tuple(
                item.notebook_output for item in get_sar_asc_desc_recovery_checklist()
            ),
            verify_function=verify_sar_asc_desc_support_stack_parity,
            **kwargs,
        ),
    ),
    "s1_filtered_stack": FamilyDefinition(
        family_id="s1_filtered_stack",
        contract_doc=_S1_FILTERED_DOC,
        module_used="app.pipeline.parity.s1_filtered_stack_verify.verify_s1_filtered_stack_parity",
        expected_reference_artifacts=tuple(
            output
            for item in get_s1_filtered_stack_recovery_checklist()
            for output in item.required_reference_outputs
        ),
        collector=lambda **kwargs: _collect_verifier_family(
            family_id="s1_filtered_stack",
            contract_doc=_S1_FILTERED_DOC,
            module_used="app.pipeline.parity.s1_filtered_stack_verify.verify_s1_filtered_stack_parity",
            expected_reference_artifacts=tuple(
                output
                for item in get_s1_filtered_stack_recovery_checklist()
                for output in item.required_reference_outputs
            ),
            verify_function=verify_s1_filtered_stack_parity,
            **kwargs,
        ),
    ),
    "pan_stack": FamilyDefinition(
        family_id="pan_stack",
        contract_doc=_PAN_STACK_DOC,
        module_used="app.pipeline.parity.pan_stack_verify.verify_pan_stack_parity",
        expected_reference_artifacts=tuple(
            output
            for item in get_pan_stack_recovery_checklist()
            for output in item.required_reference_outputs
        ),
        collector=lambda **kwargs: _collect_verifier_family(
            family_id="pan_stack",
            contract_doc=_PAN_STACK_DOC,
            module_used="app.pipeline.parity.pan_stack_verify.verify_pan_stack_parity",
            expected_reference_artifacts=tuple(
                output
                for item in get_pan_stack_recovery_checklist()
                for output in item.required_reference_outputs
            ),
            verify_function=verify_pan_stack_parity,
            **kwargs,
        ),
    ),
    "pan_components": FamilyDefinition(
        family_id="pan_components",
        contract_doc=_PAN_COMPONENTS_DOC,
        module_used="app.pipeline.parity.pan_components_verify.verify_pan_components_parity",
        expected_reference_artifacts=(
            "PAN_LS_Panchromatic_640.tif",
            "PAN_S2_Panchromatic_10m_640.tif",
            "PAN_LS_Panchromatic_640.npy",
            "PAN_S2_Panchromatic_10m_640.npy",
        ),
        collector=lambda **kwargs: _collect_verifier_family(
            family_id="pan_components",
            contract_doc=_PAN_COMPONENTS_DOC,
            module_used="app.pipeline.parity.pan_components_verify.verify_pan_components_parity",
            expected_reference_artifacts=(
                "PAN_LS_Panchromatic_640.tif",
                "PAN_S2_Panchromatic_10m_640.tif",
                "PAN_LS_Panchromatic_640.npy",
                "PAN_S2_Panchromatic_10m_640.npy",
            ),
            verify_function=verify_pan_components_parity,
            **kwargs,
        ),
    ),
    "hypercube_res25": FamilyDefinition(
        family_id="hypercube_res25",
        contract_doc=_HYPERCUBE_RES25_DOC,
        module_used="app.pipeline.parity.hypercube_res25_verify.verify_hypercube_res25_parity",
        expected_reference_artifacts=tuple(
            output
            for item in get_hypercube_res25_recovery_checklist()
            for output in item.required_reference_outputs
        ),
        collector=lambda **kwargs: _collect_verifier_family(
            family_id="hypercube_res25",
            contract_doc=_HYPERCUBE_RES25_DOC,
            module_used="app.pipeline.parity.hypercube_res25_verify.verify_hypercube_res25_parity",
            expected_reference_artifacts=tuple(
                output
                for item in get_hypercube_res25_recovery_checklist()
                for output in item.required_reference_outputs
            ),
            verify_function=verify_hypercube_res25_parity,
            **kwargs,
        ),
    ),
    "semantic_rasters": FamilyDefinition(
        family_id="semantic_rasters",
        contract_doc=_SEMANTIC_DOC,
        module_used=(
            "app.pipeline.parity.semantic_raster_recovery.get_semantic_raster_recovery_inventory; "
            "app.pipeline.parity.ai_beh_anchor_decision.get_ai_beh_anchor_pattern_decisions"
        ),
        expected_reference_artifacts=("frozen notebook semantic raster outputs",),
        collector=lambda **kwargs: _collect_inventory_family(
            family_id="semantic_rasters",
            contract_doc=_SEMANTIC_DOC,
            module_used=(
                "app.pipeline.parity.semantic_raster_recovery.get_semantic_raster_recovery_inventory; "
                "app.pipeline.parity.ai_beh_anchor_decision.get_ai_beh_anchor_pattern_decisions"
            ),
            expected_reference_artifacts=("frozen notebook semantic raster outputs",),
            status="inventory_only",
            get_items=lambda: (
                *get_semantic_raster_recovery_inventory(),
                *get_ai_beh_anchor_pattern_decisions(),
            ),
            **kwargs,
        ),
    ),
    "qa_intermediate": FamilyDefinition(
        family_id="qa_intermediate",
        contract_doc=_QA_INTERMEDIATE_DOC,
        module_used="app.pipeline.parity.qa_intermediate_inventory.get_phase_5_qa_intermediate_inventory",
        expected_reference_artifacts=("frozen notebook QA and intermediate artifact bundle",),
        collector=lambda **kwargs: _collect_inventory_family(
            family_id="qa_intermediate",
            contract_doc=_QA_INTERMEDIATE_DOC,
            module_used="app.pipeline.parity.qa_intermediate_inventory.get_phase_5_qa_intermediate_inventory",
            expected_reference_artifacts=("frozen notebook QA and intermediate artifact bundle",),
            status="inventory_only",
            get_items=get_phase_5_qa_intermediate_inventory,
            **kwargs,
        ),
    ),
    "private_map_artifacts": FamilyDefinition(
        family_id="private_map_artifacts",
        contract_doc=_PRIVATE_MAP_DOC,
        module_used="app.pipeline.parity.private_map_artifact_inventory.get_phase_6_private_map_artifact_inventory",
        expected_reference_artifacts=("frozen notebook private coordinate/map artifact bundle",),
        collector=lambda **kwargs: _collect_inventory_family(
            family_id="private_map_artifacts",
            contract_doc=_PRIVATE_MAP_DOC,
            module_used="app.pipeline.parity.private_map_artifact_inventory.get_phase_6_private_map_artifact_inventory",
            expected_reference_artifacts=("frozen notebook private coordinate/map artifact bundle",),
            status="inventory_only",
            get_items=get_phase_6_private_map_artifact_inventory,
            **kwargs,
        ),
    ),
    "classifier_model": FamilyDefinition(
        family_id="classifier_model",
        contract_doc=_CLASSIFIER_DOC,
        module_used="app.pipeline.parity.classifier_model_inventory.get_phase_7_classifier_model_inventory",
        expected_reference_artifacts=("frozen notebook private classifier/model artifact bundle",),
        collector=lambda **kwargs: _collect_inventory_family(
            family_id="classifier_model",
            contract_doc=_CLASSIFIER_DOC,
            module_used="app.pipeline.parity.classifier_model_inventory.get_phase_7_classifier_model_inventory",
            expected_reference_artifacts=("frozen notebook private classifier/model artifact bundle",),
            status="inventory_only",
            get_items=get_phase_7_classifier_model_inventory,
            **kwargs,
        ),
    ),
    "probability_only_design": FamilyDefinition(
        family_id="probability_only_design",
        contract_doc=_PROBABILITY_DOC,
        module_used="app.pipeline.parity.probability_only_classifier_design.get_phase_8_probability_only_classifier_design",
        expected_reference_artifacts=("frozen notebook probability or score artifact bundle",),
        collector=lambda **kwargs: _collect_inventory_family(
            family_id="probability_only_design",
            contract_doc=_PROBABILITY_DOC,
            module_used="app.pipeline.parity.probability_only_classifier_design.get_phase_8_probability_only_classifier_design",
            expected_reference_artifacts=("frozen notebook probability or score artifact bundle",),
            status="design_only",
            get_items=get_phase_8_probability_only_classifier_design,
            **kwargs,
        ),
    ),
}
