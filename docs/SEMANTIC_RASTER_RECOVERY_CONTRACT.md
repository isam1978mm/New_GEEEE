# Semantic Raster Recovery Contract

## Purpose

Phase 4J locks a recovery inventory for notebook semantic raster families broader than the six `AI_READY_640_Secret_*` outputs. The objective remains faithful notebook conversion. This phase records what is already covered by existing contracts, what notebook semantic outputs have source evidence, and what remains missing or ambiguous before any implementation work can be attempted.

## Scope

Phase 4J covers:

- `AI_BEH_*`
- `AI_READY_*`
- `AI_READY_640_Secret_*`
- `REPORT_640_*`
- semantic/report rasters used by `FINAL_TESLA_V7_2_HYPERCUBE*`
- any notebook-only semantic raster family found in `notebooks/new.ipynb`, `docs/Notebook_Cells_E.md`, or parity docs

Phase 4J adds an inventory helper and a run-local JSON report writer only. It does not change `secret_layers.py`, `report_640.py`, hypercube math, feature-stack logic, API behavior, frontend behavior, database behavior, or artifact serving policy.

## Non-Goals

Phase 4J does not:

- implement `AI_BEH` formulas
- implement new `AI_READY` formulas
- change `secret_layers.py`
- change `report_640.py`
- change hypercube logic
- generate rasters
- create `.npy` arrays
- call Earth Engine
- integrate into the live pipeline
- expose semantic rasters publicly
- rename existing outputs

## Classification Rules

- `app/pipeline/stages/secret_layers.py` remains a notebook-parity semantic raster stage, not clean defensible core by default.
- `app/pipeline/stages/report_640.py` remains a notebook-parity report/semantic raster stage, not clean defensible core by default.
- File existence is not parity proof.
- Runtime output presence and notebook-value parity remain separate.
- No Phase 4J item targets `public_shared`.
- No Phase 4J item defaults `http_servable=true`.
- If a later semantic output is interpreted through classifier or model wording, probability-only wording must still be preserved.

## Already Covered Outputs

The following outputs are explicitly linked to existing contracts and are tracked in Phase 4J as `covered_by_existing_contract`:

- `AI_READY_640_Secret_Gold_Halo.tif`
- `AI_READY_640_Secret_Silver_Oxide.tif`
- `AI_READY_640_Secret_Tunnel_Ceiling.tif`
- `AI_READY_640_Secret_Thermal_Inertia.tif`
- `AI_READY_640_Secret_Chemical_Protector.tif`
- `AI_READY_640_Secret_Hidden_Doors.tif`
- `REPORT_640_Pottery_Report.tif`
- `REPORT_640_Mass_Report.tif`
- `REPORT_640_FINAL_Zero_Point_Targets.tif`
- `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif`
- `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy`

Contract linkage:

- secret-layer outputs -> `docs/SECRET_LAYERS_PARITY_VERIFICATION_CONTRACT.md`
- `REPORT_640_*` outputs -> `docs/REPORT_640_PARITY_VERIFICATION_CONTRACT.md`
- `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.*` -> `docs/HYPERCUBE_RES_2P5M_PARITY_CONTRACT.md`

Phase 4J does not claim those contracts have already passed on a real run. It only records that a recovery or verification contract already exists.

## Final Tesla Semantic Family

`app/pipeline/stages/hypercube.py` and `notebooks/new.ipynb` establish an evidence-backed semantic/report source family for `FINAL_TESLA_V7_2_HYPERCUBE*`.

Fixed semantic/report input order:

1. `AI_READY_640_Secret_Gold_Halo.tif`
2. `AI_READY_640_Secret_Silver_Oxide.tif`
3. `AI_READY_640_Secret_Tunnel_Ceiling.tif`
4. `AI_READY_640_Secret_Thermal_Inertia.tif`
5. `AI_READY_640_Secret_Chemical_Protector.tif`
6. `AI_READY_640_Secret_Hidden_Doors.tif`
7. `REPORT_640_FINAL_Zero_Point_Targets.tif`
8. `REPORT_640_Mass_Report.tif`
9. `REPORT_640_Pottery_Report.tif`

This family is included in the Phase 4J inventory as a linkage item so later recovery work does not lose the notebook-defined dependency chain.

## Evidence-Backed Notebook Families

Evidence recovered from `notebooks/new.ipynb` and `docs/NOTEBOOK_VS_APP_OUTPUTS.md` shows several notebook semantic branches beyond the six secret outputs:

- broad `AI_BEH_*` family
- broad `AI_READY_*` family
- explicit `AI_BEH` relation rasters such as:
  - `AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif`
  - `AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif`
  - `AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif`
- additional `AI_BEH` named rasters such as:
  - `AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif`
  - `AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif`
  - `AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif`
  - `AI_BEH_SecretEntry_REL_ND_DOM_lin_640.tif`
  - `AI_BEH_StatueLogic_REL_Diff_DOM_lin_640.tif`
  - `AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640.tif`
  - `AI_BEH_Artifacts_Jars_Chests_DOM_lin_640.tif`
  - `AI_BEH_Mercury_RareChemicals_DOM_lin_640.tif`
  - `AI_BEH_Gemstones_AncientGlass_DOM_lin_640.tif`
  - `AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.tif`
- notebook `AI_BEH` precursor tensors used to derive `REPORT_640`:
  - `AI_BEH_VegRoot_Anomaly`
  - `AI_BEH_IronOxide_Hardness`
  - `AI_BEH_GoldAlloy_Signal`
  - `AI_BEH_MassVolume_Shadow`

These names are preserved as parity inventory labels only. They are not product claims.

## Missing Or Ambiguous Notebook Families

The inventory also records notebook semantic outputs that are referenced but not sufficiently recovered for implementation:

- `AI_READY_640_Magnetic_Anomaly.tif`
- `AI_READY_640_EM_Anomaly.tif`
- `AI_READY_640_Metal_Hardness.tif`
- `AI_READY_640_Fraction_Gold.tif`
- `AI_READY_640_Fraction_Pottery.tif`
- `AI_READY_640_Fraction_Carbon_Age.tif`
- `AI_READY_640_Fraction_Silver_Lead.tif`

For these items, the notebook currently provides filename references, optional-band logic, or downstream consumers, but not a recovered authoritative writer formula or a locked metadata contract. Phase 4J marks that honestly.

## Inventory Model

Phase 4J adds `app/pipeline/parity/semantic_raster_recovery.py` with:

- `get_semantic_raster_recovery_inventory()`
- `filter_semantic_raster_recovery_by_status()`
- `write_semantic_raster_recovery_report()`

Each recovery item records:

- notebook output name or pattern
- current app status
- source status
- whether authoritative source is available
- whether an existing contract already covers the output
- expected input outputs
- expected formula summary
- required reference outputs
- required metadata
- target mode
- classification
- exposure flags
- implementation status
- blocker and next action

Allowed `source_status` values:

- `exact_source_found`
- `partial_source_found`
- `no_source_found`
- `existing_app_equivalent_found`
- `covered_by_existing_contract`
- `unknown_needs_reference`

Allowed `implementation_status` values:

- `covered_no_action_needed`
- `ready_for_implementation_after_reference`
- `requires_reference_output`
- `requires_source_reconstruction`
- `blocked_no_source_formula`
- `blocked_missing_metadata_contract`
- `deferred`

## Report Output

The JSON report is written under:

```text
data/runs/<run_id>/manifests/semantic_raster_recovery_report.json
```

The report path is resolved under the run directory and path traversal is rejected.

Report fields:

- `schema_version`
- `run_id`
- `created_at`
- `items`
- `counts_by_source_status`
- `counts_by_implementation_status`
- `phase_4j_formula_changes=false`
- `notes`

Phase 4J report writing does not create `.tif` or `.npy` files.

## Interpretation

Read the Phase 4J inventory conservatively:

- `covered_by_existing_contract` means recovery or verification work already exists elsewhere.
- `exact_source_found` means notebook naming and source logic were recovered well enough to inventory the branch.
- `partial_source_found` means notebook evidence exists but formula, metadata, or writer recovery is incomplete.
- `existing_app_equivalent_found` means the app reproduces some of the semantic logic internally, but not as a standalone notebook-named output.

No Phase 4J item is marked notebook-value parity verified. Frozen notebook references are still required before any later implementation or verification slice can claim parity.

## Recommended Next Direction

The next clean Phase 4K target should be one unresolved notebook semantic branch with explicit names but incomplete writer recovery. The strongest candidate is the `AI_READY_640_Magnetic_Anomaly` / `AI_READY_640_EM_Anomaly` pair, because:

- both names are used repeatedly in downstream notebook logic
- both are already connected to `FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B`
- both remain blocked on source recovery rather than on public-surface policy

## Confirmation

Phase 4J changes no semantic raster formulas, no `secret_layers.py` formulas, no `report_640.py` formulas, no hypercube math, no raster math, no API behavior, no database behavior, and no artifact serving behavior.
