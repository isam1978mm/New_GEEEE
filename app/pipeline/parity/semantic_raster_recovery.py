from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


SEMANTIC_RASTER_RECOVERY_SCHEMA_VERSION = "semantic_raster_recovery_report_v1"
SEMANTIC_RASTER_RECOVERY_REPORT_RELATIVE_PATH = (
    "manifests/semantic_raster_recovery_report.json"
)

ALLOWED_SOURCE_STATUSES = {
    "exact_source_found",
    "partial_source_found",
    "no_source_found",
    "existing_app_equivalent_found",
    "covered_by_existing_contract",
    "unknown_needs_reference",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "covered_no_action_needed",
    "ready_for_implementation_after_reference",
    "requires_reference_output",
    "requires_source_reconstruction",
    "blocked_no_source_formula",
    "blocked_missing_metadata_contract",
    "deferred",
}

_COMMON_REQUIRED_METADATA = (
    "shape",
    "dtype",
    "nodata or NaN policy",
    "CRS",
    "transform",
    "band descriptions where applicable",
    "value tolerance",
)

_COMMON_REFERENCE_OUTPUTS = (
    "frozen notebook raster output",
    "frozen notebook metadata snapshot",
)

_FINAL_TESLA_SEMANTIC_INPUTS = (
    "AI_READY_640_Secret_Gold_Halo.tif",
    "AI_READY_640_Secret_Silver_Oxide.tif",
    "AI_READY_640_Secret_Tunnel_Ceiling.tif",
    "AI_READY_640_Secret_Thermal_Inertia.tif",
    "AI_READY_640_Secret_Chemical_Protector.tif",
    "AI_READY_640_Secret_Hidden_Doors.tif",
    "REPORT_640_FINAL_Zero_Point_Targets.tif",
    "REPORT_640_Mass_Report.tif",
    "REPORT_640_Pottery_Report.tif",
)


@dataclass(frozen=True)
class SemanticRasterRecoveryItem:
    id: str
    notebook_output_or_pattern: str
    family: str
    current_app_status: str
    source_status: str
    authoritative_source_available: bool
    source_reference: str
    covered_by_existing_contract: bool
    existing_contract_reference: str | None
    known_stage_file: str | None
    known_stage_class: str | None
    expected_input_outputs: tuple[str, ...]
    expected_formula_summary: str
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
            raise ValueError("Phase 4J items must not target public_shared")
        if self.http_servable:
            raise ValueError("Phase 4J items must not default http_servable to true")
        if self.notebook_value_parity_verified:
            raise ValueError(
                "Phase 4J is inventory only; notebook value parity must remain false"
            )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_INVENTORY: tuple[SemanticRasterRecoveryItem, ...] = (
    SemanticRasterRecoveryItem(
        id="secret_gold_halo",
        notebook_output_or_pattern="AI_READY_640_Secret_Gold_Halo.tif",
        family="AI_READY semantic rasters",
        current_app_status="covered by existing verification contract for notebook-parity secret layers",
        source_status="covered_by_existing_contract",
        authoritative_source_available=True,
        source_reference=(
            "app/pipeline/stages/secret_layers.py and notebooks/new.ipynb secret-layer "
            "cells define the exported notebook output name and formula."
        ),
        covered_by_existing_contract=True,
        existing_contract_reference="docs/SECRET_LAYERS_PARITY_VERIFICATION_CONTRACT.md",
        known_stage_file="app/pipeline/stages/secret_layers.py",
        known_stage_class="SecretLayersStage",
        expected_input_outputs=("s2_raw_cube.npy",),
        expected_formula_summary="B12 / (B8 + eps)",
        required_reference_outputs=("AI_READY_640_Secret_Gold_Halo.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="covered_no_action_needed",
        blocker="Verification contract exists, but Phase 4J does not assert a passing run/reference report.",
        recommended_next_action="Use the existing secret-layer verifier when a frozen notebook reference bundle is available.",
        notes="secret_layers.py remains notebook-parity semantic raster stage, not clean defensible core by default.",
    ),
    SemanticRasterRecoveryItem(
        id="secret_silver_oxide",
        notebook_output_or_pattern="AI_READY_640_Secret_Silver_Oxide.tif",
        family="AI_READY semantic rasters",
        current_app_status="covered by existing verification contract for notebook-parity secret layers",
        source_status="covered_by_existing_contract",
        authoritative_source_available=True,
        source_reference="app/pipeline/stages/secret_layers.py and notebooks/new.ipynb",
        covered_by_existing_contract=True,
        existing_contract_reference="docs/SECRET_LAYERS_PARITY_VERIFICATION_CONTRACT.md",
        known_stage_file="app/pipeline/stages/secret_layers.py",
        known_stage_class="SecretLayersStage",
        expected_input_outputs=("s2_raw_cube.npy",),
        expected_formula_summary="B2 / (B1 + eps)",
        required_reference_outputs=("AI_READY_640_Secret_Silver_Oxide.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="covered_no_action_needed",
        blocker="Verification contract exists, but Phase 4J does not assert a passing run/reference report.",
        recommended_next_action="Use the existing secret-layer verifier when a frozen notebook reference bundle is available.",
        notes="Covered output; file existence alone is not parity proof.",
    ),
    SemanticRasterRecoveryItem(
        id="secret_tunnel_ceiling",
        notebook_output_or_pattern="AI_READY_640_Secret_Tunnel_Ceiling.tif",
        family="AI_READY semantic rasters",
        current_app_status="covered by existing verification contract for notebook-parity secret layers",
        source_status="covered_by_existing_contract",
        authoritative_source_available=True,
        source_reference="app/pipeline/stages/secret_layers.py and notebooks/new.ipynb",
        covered_by_existing_contract=True,
        existing_contract_reference="docs/SECRET_LAYERS_PARITY_VERIFICATION_CONTRACT.md",
        known_stage_file="app/pipeline/stages/secret_layers.py",
        known_stage_class="SecretLayersStage",
        expected_input_outputs=("s2_raw_cube.npy",),
        expected_formula_summary="B8 - B4",
        required_reference_outputs=("AI_READY_640_Secret_Tunnel_Ceiling.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="covered_no_action_needed",
        blocker="Verification contract exists, but Phase 4J does not assert a passing run/reference report.",
        recommended_next_action="Use the existing secret-layer verifier when a frozen notebook reference bundle is available.",
        notes="Covered output; file existence alone is not parity proof.",
    ),
    SemanticRasterRecoveryItem(
        id="secret_thermal_inertia",
        notebook_output_or_pattern="AI_READY_640_Secret_Thermal_Inertia.tif",
        family="AI_READY semantic rasters",
        current_app_status="covered by existing verification contract for notebook-parity secret layers",
        source_status="covered_by_existing_contract",
        authoritative_source_available=True,
        source_reference="app/pipeline/stages/secret_layers.py and notebooks/new.ipynb",
        covered_by_existing_contract=True,
        existing_contract_reference="docs/SECRET_LAYERS_PARITY_VERIFICATION_CONTRACT.md",
        known_stage_file="app/pipeline/stages/secret_layers.py",
        known_stage_class="SecretLayersStage",
        expected_input_outputs=("lst.tif",),
        expected_formula_summary="l9_col / focal_mean(l9_col, 500m)",
        required_reference_outputs=("AI_READY_640_Secret_Thermal_Inertia.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="covered_no_action_needed",
        blocker="Verification contract exists, but Phase 4J does not assert a passing run/reference report.",
        recommended_next_action="Use the existing secret-layer verifier when a frozen notebook reference bundle is available.",
        notes="Covered output; file existence alone is not parity proof.",
    ),
    SemanticRasterRecoveryItem(
        id="secret_chemical_protector",
        notebook_output_or_pattern="AI_READY_640_Secret_Chemical_Protector.tif",
        family="AI_READY semantic rasters",
        current_app_status="covered by existing verification contract for notebook-parity secret layers",
        source_status="covered_by_existing_contract",
        authoritative_source_available=True,
        source_reference="app/pipeline/stages/secret_layers.py and notebooks/new.ipynb",
        covered_by_existing_contract=True,
        existing_contract_reference="docs/SECRET_LAYERS_PARITY_VERIFICATION_CONTRACT.md",
        known_stage_file="app/pipeline/stages/secret_layers.py",
        known_stage_class="SecretLayersStage",
        expected_input_outputs=("s2_raw_cube.npy",),
        expected_formula_summary="B1 / (B11 + eps)",
        required_reference_outputs=("AI_READY_640_Secret_Chemical_Protector.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="covered_no_action_needed",
        blocker="Verification contract exists, but Phase 4J does not assert a passing run/reference report.",
        recommended_next_action="Use the existing secret-layer verifier when a frozen notebook reference bundle is available.",
        notes="Covered output; file existence alone is not parity proof.",
    ),
    SemanticRasterRecoveryItem(
        id="secret_hidden_doors",
        notebook_output_or_pattern="AI_READY_640_Secret_Hidden_Doors.tif",
        family="AI_READY semantic rasters",
        current_app_status="covered by existing verification contract for notebook-parity secret layers",
        source_status="covered_by_existing_contract",
        authoritative_source_available=True,
        source_reference="app/pipeline/stages/secret_layers.py and notebooks/new.ipynb",
        covered_by_existing_contract=True,
        existing_contract_reference="docs/SECRET_LAYERS_PARITY_VERIFICATION_CONTRACT.md",
        known_stage_file="app/pipeline/stages/secret_layers.py",
        known_stage_class="SecretLayersStage",
        expected_input_outputs=("dem.npy",),
        expected_formula_summary="hillshade(315,35) - hillshade(135,35)",
        required_reference_outputs=("AI_READY_640_Secret_Hidden_Doors.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="covered_no_action_needed",
        blocker="Verification contract exists, but Phase 4J does not assert a passing run/reference report.",
        recommended_next_action="Use the existing secret-layer verifier when a frozen notebook reference bundle is available.",
        notes="Covered output; file existence alone is not parity proof.",
    ),
    SemanticRasterRecoveryItem(
        id="report_pottery",
        notebook_output_or_pattern="REPORT_640_Pottery_Report.tif",
        family="REPORT_640 semantic rasters",
        current_app_status="covered by existing REPORT_640 verification contract",
        source_status="covered_by_existing_contract",
        authoritative_source_available=True,
        source_reference="app/pipeline/stages/report_640.py and notebooks/new.ipynb",
        covered_by_existing_contract=True,
        existing_contract_reference="docs/REPORT_640_PARITY_VERIFICATION_CONTRACT.md",
        known_stage_file="app/pipeline/stages/report_640.py",
        known_stage_class="Report640Stage",
        expected_input_outputs=("s2_raw_cube.npy",),
        expected_formula_summary="B12 / B11",
        required_reference_outputs=("REPORT_640_Pottery_Report.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity report/semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="covered_no_action_needed",
        blocker="Verification contract exists, but Phase 4J does not assert a passing run/reference report.",
        recommended_next_action="Use the existing REPORT_640 verifier when a frozen notebook reference bundle is available.",
        notes="report_640.py remains notebook-parity report/semantic raster stage, not clean defensible core by default.",
    ),
    SemanticRasterRecoveryItem(
        id="report_mass",
        notebook_output_or_pattern="REPORT_640_Mass_Report.tif",
        family="REPORT_640 semantic rasters",
        current_app_status="covered by existing REPORT_640 verification contract",
        source_status="covered_by_existing_contract",
        authoritative_source_available=True,
        source_reference="app/pipeline/stages/report_640.py and notebooks/new.ipynb",
        covered_by_existing_contract=True,
        existing_contract_reference="docs/REPORT_640_PARITY_VERIFICATION_CONTRACT.md",
        known_stage_file="app/pipeline/stages/report_640.py",
        known_stage_class="Report640Stage",
        expected_input_outputs=("s2_raw_cube.npy", "RAW_ST_B10.npy"),
        expected_formula_summary="B12 * ST_B10 / 1000",
        required_reference_outputs=("REPORT_640_Mass_Report.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity report/semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="covered_no_action_needed",
        blocker="Verification contract exists, but Phase 4J does not assert a passing run/reference report.",
        recommended_next_action="Use the existing REPORT_640 verifier when a frozen notebook reference bundle is available.",
        notes="Covered output; file existence alone is not parity proof.",
    ),
    SemanticRasterRecoveryItem(
        id="report_zero_point_targets",
        notebook_output_or_pattern="REPORT_640_FINAL_Zero_Point_Targets.tif",
        family="REPORT_640 semantic rasters",
        current_app_status="covered by existing REPORT_640 verification contract",
        source_status="covered_by_existing_contract",
        authoritative_source_available=True,
        source_reference="app/pipeline/stages/report_640.py and notebooks/new.ipynb",
        covered_by_existing_contract=True,
        existing_contract_reference="docs/REPORT_640_PARITY_VERIFICATION_CONTRACT.md",
        known_stage_file="app/pipeline/stages/report_640.py",
        known_stage_class="Report640Stage",
        expected_input_outputs=("s2_raw_cube.npy",),
        expected_formula_summary=(
            "threshold_intersection(GoldAlloy>1.45, IronOxide>1.25, VegRoot>0.35)"
        ),
        required_reference_outputs=("REPORT_640_FINAL_Zero_Point_Targets.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity report/semantic raster stage",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="covered_no_action_needed",
        blocker="Verification contract exists, but Phase 4J does not assert a passing run/reference report.",
        recommended_next_action="Use the existing REPORT_640 verifier when a frozen notebook reference bundle is available.",
        notes="Covered output; file existence alone is not parity proof.",
    ),
    SemanticRasterRecoveryItem(
        id="hypercube_res25_tif",
        notebook_output_or_pattern="FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif",
        family="hypercube/tensor outputs",
        current_app_status="covered by existing 2.5 m hypercube recovery and verification contract",
        source_status="covered_by_existing_contract",
        authoritative_source_available=True,
        source_reference="docs/HYPERCUBE_RES_2P5M_PARITY_CONTRACT.md and notebooks/new.ipynb",
        covered_by_existing_contract=True,
        existing_contract_reference="docs/HYPERCUBE_RES_2P5M_PARITY_CONTRACT.md",
        known_stage_file="app/pipeline/stages/hypercube.py",
        known_stage_class="HypercubeStage",
        expected_input_outputs=("FINAL_TESLA_V7_2_HYPERCUBE.tif",),
        expected_formula_summary="2.5 m cubic resampling of FINAL_TESLA_V7_2_HYPERCUBE.tif",
        required_reference_outputs=("FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="covered_no_action_needed",
        blocker="Existing contract covers recovery and verification, but Phase 4J does not assert a passing run/reference report.",
        recommended_next_action="Use the existing 2.5 m hypercube verifier when a frozen notebook reference bundle is available.",
        notes="Covered output; existing app hypercube files are not automatic substitutes.",
    ),
    SemanticRasterRecoveryItem(
        id="hypercube_res25_npy",
        notebook_output_or_pattern="FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy",
        family="hypercube/tensor outputs",
        current_app_status="covered by existing 2.5 m hypercube recovery and verification contract",
        source_status="covered_by_existing_contract",
        authoritative_source_available=True,
        source_reference="docs/HYPERCUBE_RES_2P5M_PARITY_CONTRACT.md and notebooks/new.ipynb",
        covered_by_existing_contract=True,
        existing_contract_reference="docs/HYPERCUBE_RES_2P5M_PARITY_CONTRACT.md",
        known_stage_file="app/pipeline/stages/hypercube.py",
        known_stage_class="HypercubeStage",
        expected_input_outputs=("FINAL_TESLA_V7_2_HYPERCUBE.tif",),
        expected_formula_summary="2.5 m cubic resampling of FINAL_TESLA_V7_2_HYPERCUBE.tif saved as CHW float32 NPY",
        required_reference_outputs=("FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="covered_no_action_needed",
        blocker="Existing contract covers recovery and verification, but Phase 4J does not assert a passing run/reference report.",
        recommended_next_action="Use the existing 2.5 m hypercube verifier when a frozen notebook reference bundle is available.",
        notes="Covered output; existing app hypercube files are not automatic substitutes.",
    ),
    SemanticRasterRecoveryItem(
        id="semantic_report_family_used_by_final_tesla",
        notebook_output_or_pattern="semantic/report rasters used by FINAL_TESLA_V7_2_HYPERCUBE*",
        family="semantic/report rasters used by FINAL_TESLA_V7_2_HYPERCUBE*",
        current_app_status="covered by existing secret/report/hypercube contracts",
        source_status="covered_by_existing_contract",
        authoritative_source_available=True,
        source_reference=(
            "app/pipeline/stages/hypercube.py NOTEBOOK_FINAL_TESLA_LAYER_ORDER and "
            "notebooks/new.ipynb hypercube assembly cells."
        ),
        covered_by_existing_contract=True,
        existing_contract_reference="docs/HYPERCUBE_RES_2P5M_PARITY_CONTRACT.md",
        known_stage_file="app/pipeline/stages/hypercube.py",
        known_stage_class="HypercubeStage",
        expected_input_outputs=_FINAL_TESLA_SEMANTIC_INPUTS,
        expected_formula_summary=(
            "9-band semantic/report stack assembled from six AI_READY_640_Secret rasters "
            "plus three REPORT_640 rasters in fixed order"
        ),
        required_reference_outputs=(
            "FINAL_TESLA_V7_2_HYPERCUBE.tif",
            "FINAL_TESLA_V7_2_HYPERCUBE.npy",
        ),
        required_metadata=(
            "band order",
            "band count",
            "dtype",
            "shape",
            "band descriptions",
            "value tolerance",
        ),
        target_mode="notebook_parity",
        classification="notebook-parity",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="covered_no_action_needed",
        blocker="Covered by existing secret/report/hypercube contract chain; Phase 4J does not rerun verification.",
        recommended_next_action="Preserve the fixed nine-layer order when future semantic inventory or verification expands.",
        notes="This is a family-level linkage item, not a new raster writer request.",
    ),
    SemanticRasterRecoveryItem(
        id="ai_beh_pattern",
        notebook_output_or_pattern="AI_BEH_*",
        family="AI_BEH semantic rasters",
        current_app_status="partial; notebook names exist but app does not export a broad AI_BEH raster family",
        source_status="partial_source_found",
        authoritative_source_available=True,
        source_reference=(
            "docs/NOTEBOOK_VS_APP_OUTPUTS.md notes thirteen notebook AI_BEH behavior rasters; "
            "notebooks/new.ipynb contains multiple AI_BEH_* definitions and later consumers."
        ),
        covered_by_existing_contract=False,
        existing_contract_reference=None,
        known_stage_file=None,
        known_stage_class=None,
        expected_input_outputs=("Sentinel-2 composites", "thermal inputs where applicable"),
        expected_formula_summary="Umbrella notebook behavior family; exact formulas are split across multiple notebook cells.",
        required_reference_outputs=_COMMON_REFERENCE_OUTPUTS,
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_source_reconstruction",
        blocker="Exact app writer mapping for the full AI_BEH family does not exist; only selected formulas are source-identified in notebook cells.",
        recommended_next_action="Break the umbrella AI_BEH family into notebook-backed subfamilies and verify each against frozen references.",
        notes="File existence is not parity proof. No classifier/model confirmation wording is introduced here.",
    ),
    SemanticRasterRecoveryItem(
        id="ai_ready_pattern",
        notebook_output_or_pattern="AI_READY_*",
        family="AI_READY semantic rasters",
        current_app_status="partial; six secret outputs are covered, broader notebook-only AI_READY names remain unresolved",
        source_status="partial_source_found",
        authoritative_source_available=True,
        source_reference=(
            "docs/NOTEBOOK_VS_APP_OUTPUTS.md and notebooks/new.ipynb show the six secret outputs plus "
            "additional AI_READY names such as Magnetic_Anomaly, EM_Anomaly, Metal_Hardness, and Fraction_*."
        ),
        covered_by_existing_contract=False,
        existing_contract_reference=None,
        known_stage_file="app/pipeline/stages/secret_layers.py",
        known_stage_class="SecretLayersStage",
        expected_input_outputs=("AI_READY_640_Secret_*", "other notebook-only semantic intermediates"),
        expected_formula_summary="Umbrella notebook AI_READY family; only the six secret layers have current app writer coverage.",
        required_reference_outputs=_COMMON_REFERENCE_OUTPUTS,
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_source_reconstruction",
        blocker="Broader AI_READY notebook outputs are referenced but not source-recovered as app writers.",
        recommended_next_action="Recover each non-secret AI_READY notebook branch separately before implementation.",
        notes="This family must remain private/local and does not default to public/shared exposure.",
    ),
    SemanticRasterRecoveryItem(
        id="ai_beh_known_relation_rasters",
        notebook_output_or_pattern=(
            "AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif | "
            "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif | "
            "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif"
        ),
        family="AI_BEH semantic rasters",
        current_app_status="missing as standalone app notebook-parity outputs",
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=(
            "notebooks/new.ipynb lines around 23418-23424 and repeated stack assembly cells around "
            "23644-23732, 23972-23976, and 35469-35471."
        ),
        covered_by_existing_contract=False,
        existing_contract_reference=None,
        known_stage_file=None,
        known_stage_class=None,
        expected_input_outputs=("Sentinel-2 composite bands B3, B4, B8, B11, B12",),
        expected_formula_summary=(
            "ND(B8,B4), B4/B3, and B11/B12 behavior rasters are explicitly named and stacked in the notebook."
        ),
        required_reference_outputs=(
            "AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif",
            "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif",
            "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker="Notebook formulas and names are explicit, but the app has no standalone writer or parity verifier for this trio.",
        recommended_next_action="Capture frozen references for the trio, then decide whether to implement as standalone rasters or as documented notebook-only outputs.",
        notes="These are notebook semantic outputs, not classifier/model confirmations.",
    ),
    SemanticRasterRecoveryItem(
        id="ai_beh_extended_notebook_semantics",
        notebook_output_or_pattern=(
            "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif | "
            "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif | "
            "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif | "
            "AI_BEH_SecretEntry_REL_ND_DOM_lin_640.tif | "
            "AI_BEH_StatueLogic_REL_Diff_DOM_lin_640.tif | "
            "AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640.tif | "
            "AI_BEH_Artifacts_Jars_Chests_DOM_lin_640.tif | "
            "AI_BEH_Mercury_RareChemicals_DOM_lin_640.tif | "
            "AI_BEH_Gemstones_AncientGlass_DOM_lin_640.tif | "
            "AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.tif"
        ),
        family="AI_BEH semantic rasters",
        current_app_status="missing as standalone app notebook-parity outputs",
        source_status="exact_source_found",
        authoritative_source_available=True,
        source_reference=(
            "notebooks/new.ipynb lines around 24193-24310, 24368-24372, and the later "
            "candidate_files table around 35469-35480."
        ),
        covered_by_existing_contract=False,
        existing_contract_reference=None,
        known_stage_file=None,
        known_stage_class=None,
        expected_input_outputs=("Sentinel-2 composites",),
        expected_formula_summary=(
            "Notebook cells explicitly define named AI_BEH outputs for gold alloy, silver/copper, "
            "ERT proxy, secret entry, statue logic, gold density, artifacts/jars/chests, mercury, "
            "gemstones/glass, and alloys/statues."
        ),
        required_reference_outputs=_COMMON_REFERENCE_OUTPUTS,
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker="Formulas and names are notebook-visible, but there is no app writer surface or frozen reference lock for this branch.",
        recommended_next_action="Split the extended AI_BEH list into reference-backed implementation slices rather than treating it as one opaque family.",
        notes="The names are parity inventory labels only, not product claims.",
    ),
    SemanticRasterRecoveryItem(
        id="ai_beh_report_precursor_tensors",
        notebook_output_or_pattern=(
            "AI_BEH_VegRoot_Anomaly | AI_BEH_IronOxide_Hardness | "
            "AI_BEH_GoldAlloy_Signal | AI_BEH_MassVolume_Shadow"
        ),
        family="AI_BEH semantic rasters",
        current_app_status="partial; formulas are reproduced inside report_640 logic, but standalone notebook-named rasters are not exported",
        source_status="existing_app_equivalent_found",
        authoritative_source_available=True,
        source_reference=(
            "notebooks/new.ipynb lines around 24460-24484 define these four behavior tensors; "
            "app/pipeline/stages/report_640.py reproduces the same calculations inside REPORT_640 generation."
        ),
        covered_by_existing_contract=False,
        existing_contract_reference=None,
        known_stage_file="app/pipeline/stages/report_640.py",
        known_stage_class="Report640Stage",
        expected_input_outputs=("s2_raw_cube.npy", "RAW_ST_B10.npy"),
        expected_formula_summary=(
            "The four notebook AI_BEH precursor tensors are exact formula sources for REPORT_640 outputs, "
            "but the app persists only the derived REPORT_640 rasters."
        ),
        required_reference_outputs=(
            "AI_BEH_VegRoot_Anomaly notebook reference if retained separately",
            "AI_BEH_IronOxide_Hardness notebook reference if retained separately",
            "AI_BEH_GoldAlloy_Signal notebook reference if retained separately",
            "AI_BEH_MassVolume_Shadow notebook reference if retained separately",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker="Exact notebook formulas are known, but standalone notebook-named outputs are not part of the current app writer surface.",
        recommended_next_action="Decide whether these four behavior tensors require standalone parity outputs or remain documented as internal report precursors only.",
        notes="Runtime output presence and notebook-value parity remain separate from formula recovery.",
    ),
    SemanticRasterRecoveryItem(
        id="ai_ready_magnetic_anomaly",
        notebook_output_or_pattern="AI_READY_640_Magnetic_Anomaly.tif",
        family="AI_READY semantic rasters",
        current_app_status="missing; referenced by notebook patch and downstream scoring cells only",
        source_status="partial_source_found",
        authoritative_source_available=False,
        source_reference=(
            "notebooks/new.ipynb patch and optional-band cells around 27117-27123, 27966-28042, "
            "30873-31251, and later scoring cells reference this output name but do not provide a recovered writer formula."
        ),
        covered_by_existing_contract=False,
        existing_contract_reference=None,
        known_stage_file="app/pipeline/stages/hypercube.py",
        known_stage_class="HypercubeStage",
        expected_input_outputs=(),
        expected_formula_summary="Notebook references the filename and optional usage, but no authoritative formula was recovered in app source.",
        required_reference_outputs=("AI_READY_640_Magnetic_Anomaly.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="blocked_no_source_formula",
        blocker="Notebook references exist, but no authoritative writer formula or source stage was recovered.",
        recommended_next_action="Recover the exact notebook source cell or frozen reference before any implementation attempt.",
        notes="Do not fabricate this layer from existing app outputs or from the patched hypercube name alone.",
    ),
    SemanticRasterRecoveryItem(
        id="ai_ready_em_anomaly",
        notebook_output_or_pattern="AI_READY_640_EM_Anomaly.tif",
        family="AI_READY semantic rasters",
        current_app_status="missing; referenced by notebook patch and downstream scoring cells only",
        source_status="partial_source_found",
        authoritative_source_available=False,
        source_reference=(
            "notebooks/new.ipynb patch and optional-band cells around 27122-27125, 27966-28042, "
            "30882-31251, and later scoring cells reference this output name but do not provide a recovered writer formula."
        ),
        covered_by_existing_contract=False,
        existing_contract_reference=None,
        known_stage_file="app/pipeline/stages/hypercube.py",
        known_stage_class="HypercubeStage",
        expected_input_outputs=(),
        expected_formula_summary="Notebook references the filename and optional usage, but no authoritative formula was recovered in app source.",
        required_reference_outputs=("AI_READY_640_EM_Anomaly.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="blocked_no_source_formula",
        blocker="Notebook references exist, but no authoritative writer formula or source stage was recovered.",
        recommended_next_action="Recover the exact notebook source cell or frozen reference before any implementation attempt.",
        notes="Do not fabricate this layer from existing app outputs or from the patched hypercube name alone.",
    ),
    SemanticRasterRecoveryItem(
        id="ai_ready_metal_hardness",
        notebook_output_or_pattern="AI_READY_640_Metal_Hardness.tif",
        family="AI_READY semantic rasters",
        current_app_status="missing; notebook uses it as a spatial reference and success check, but app has no source writer",
        source_status="partial_source_found",
        authoritative_source_available=False,
        source_reference=(
            "notebooks/new.ipynb references the file around 45081, 45168, 45221, 45303, 45455, and 45528 "
            "as a pixel-lock or reference layer, but no authoritative generation formula was recovered."
        ),
        covered_by_existing_contract=False,
        existing_contract_reference=None,
        known_stage_file=None,
        known_stage_class=None,
        expected_input_outputs=(),
        expected_formula_summary="Filename is repeatedly referenced as an anchor layer, but source formula and writer cell remain unrecovered.",
        required_reference_outputs=("AI_READY_640_Metal_Hardness.tif",),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="blocked_no_source_formula",
        blocker="A notebook reference path exists, but no authoritative source formula or app-equivalent writer was recovered.",
        recommended_next_action="Treat this as a missing semantic source artifact until notebook writer logic or frozen references are recovered.",
        notes="This is inventory only; no attempt should be made to infer the layer from reference-path usage.",
    ),
    SemanticRasterRecoveryItem(
        id="ai_ready_fraction_family",
        notebook_output_or_pattern=(
            "AI_READY_640_Fraction_Gold.tif | AI_READY_640_Fraction_Pottery.tif | "
            "AI_READY_640_Fraction_Carbon_Age.tif | AI_READY_640_Fraction_Silver_Lead.tif"
        ),
        family="AI_READY semantic rasters",
        current_app_status="missing; notebook names are visible but no app writer exists",
        source_status="partial_source_found",
        authoritative_source_available=False,
        source_reference=(
            "notebooks/new.ipynb lines around 45306-45310 and 45458-45462 list the four expected "
            "fraction outputs, but the generating formulas and metadata contract are not recovered."
        ),
        covered_by_existing_contract=False,
        existing_contract_reference=None,
        known_stage_file=None,
        known_stage_class=None,
        expected_input_outputs=(),
        expected_formula_summary="Notebook exposes output filenames only; formulas, units, and source-band contract remain unrecovered.",
        required_reference_outputs=(
            "AI_READY_640_Fraction_Gold.tif",
            "AI_READY_640_Fraction_Pottery.tif",
            "AI_READY_640_Fraction_Carbon_Age.tif",
            "AI_READY_640_Fraction_Silver_Lead.tif",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity",
        classification="notebook-parity semantic raster inventory",
        http_servable=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="blocked_missing_metadata_contract",
        blocker="Output names are visible, but formula, units, nodata policy, and source-writer contract are not recovered.",
        recommended_next_action="Recover the generating notebook cell and frozen references before any implementation or verification slice.",
        notes="The filenames are preserved for parity inventory only and are not treated as validated app outputs.",
    ),
)


def get_semantic_raster_recovery_inventory() -> tuple[SemanticRasterRecoveryItem, ...]:
    """Return the full Phase 4J semantic-raster recovery inventory."""

    return _INVENTORY


def filter_semantic_raster_recovery_by_status(
    implementation_status: str,
) -> tuple[SemanticRasterRecoveryItem, ...]:
    """Return inventory items that match an allowed implementation status."""

    if implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
        raise ValueError(f"unsupported implementation_status: {implementation_status}")
    return tuple(
        item for item in _INVENTORY if item.implementation_status == implementation_status
    )


def write_semantic_raster_recovery_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[SemanticRasterRecoveryItem] | None = None,
    report_relative_path: str | Path = SEMANTIC_RASTER_RECOVERY_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local JSON recovery report without creating raster or NPY outputs."""

    report_items = tuple(items or _INVENTORY)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SEMANTIC_RASTER_RECOVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_source_status": _counts_by("source_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "phase_4j_formula_changes": False,
        "notes": (
            "Phase 4J is inventory, recovery, and contract only. It does not implement "
            "AI_BEH formulas, AI_READY formulas, secret/report formulas, hypercube math, "
            "or any raster writer. File existence is not parity proof. Runtime output "
            "presence and notebook-value parity remain separate."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[SemanticRasterRecoveryItem],
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
