# Notebook Full-Job Artifact Contract

## Purpose

This document converts the inventory in [NOTEBOOK_FULL_JOB_INVENTORY.md](NOTEBOOK_FULL_JOB_INVENTORY.md) into an implementation contract for future N-phase work.

The contract defines:

- which notebook full-job output families are in scope for the app
- which of those outputs are required app artifacts
- which are internal QA artifacts only
- which output families remain out of scope
- how notebook-style outputs map into the app run-directory layout
- which output families require renamed or stabilized filenames for safety and implementation clarity

This document does not authorize public exposure of notebook full-job outputs. Public exposure remains governed by the app artifact policy, redaction rules, and later implementation goals.

## Source Documents

- [NOTEBOOK_FULL_JOB_INVENTORY.md](NOTEBOOK_FULL_JOB_INVENTORY.md)
- [Notebook_Cells_E.md](Notebook_Cells_E.md)
- [OUTPUT_PARITY_CONTRACT.md](OUTPUT_PARITY_CONTRACT.md)

## Contract Scope

This contract applies only to notebook-equivalent full-job outputs that are:

- scientifically or operationally relevant to the accepted app workflow
- compatible with the project safety rules
- not already excluded as out-of-scope in the inventory unless a later goal explicitly re-approves them

This contract does not authorize:

- notebook edits
- plan changes
- deployment changes
- frontend exposure
- public serving of notebook full-job artifacts

## Classification Model

Output family categories:

- `required_app_artifact`
- `internal_qa_artifact`
- `out_of_scope`

Artifact class rules:

- `FILESYSTEM_ONLY` is the default class for notebook full-job outputs
- `LOCAL_SENSITIVE` is allowed only for explicitly redacted operator QA artifacts
- `REDACTED_PUBLIC` is allowed only for already-redacted summaries approved by later implementation goals
- `PREVIEW_ONLY` is allowed only for safe previews approved by later implementation goals

Forbidden public content remains forbidden in any promoted artifact:

- raw coordinates
- geometry
- WKT
- bounds
- CRS transforms
- filesystem paths
- Drive paths
- hashes and checksums
- exact target locations
- secrets

## App Run-Directory Layout

Notebook full-job outputs must map into the app run directory under:

`./data/runs/<run_id>/`

Contracted subdirectories:

- `./data/runs/<run_id>/`
  - core stage outputs already defined by existing app stages
- `./data/runs/<run_id>/qa/`
  - redacted internal QA summaries, audits, stats, and parity-support files
- `./data/runs/<run_id>/stacks/`
  - approved feature-stack and tensor-support outputs that are not core canonical stage files
- `./data/runs/<run_id>/objects/`
  - approved non-public object-support outputs that are not part of the existing public-safe object tables
- `./data/runs/<run_id>/full_job/`
  - notebook-equivalent non-public outputs that are approved but do not belong to a narrower domain folder
- `./data/runs/<run_id>/experimental/`
  - experimental classifier outputs only, unchanged from existing rules

Layout rules:

- use stage/domain-specific subdirectories rather than mirroring Colab or Drive layout
- do not create Drive-first or Colab-first path structures in the app
- do not emit raw notebook folder names if they leak unstable or unsafe semantics

## Filename Mapping Rules

### Stable names kept as-is

These names are already stable and safe enough for app use:

- `grid_manifest.json`
- `dem.tif`
- `dem.npy`
- `VV_dB.tif`
- `VH_dB.tif`
- `logRatio_dB.tif`
- `incidence.tif`
- `slope.tif`
- `aspect.tif`
- `curvature.tif`
- `TPI.tif`
- `TRI.tif`
- `roughness.tif`
- `TWI.tif`
- `lst.tif`
- `NDVI.tif`
- `NDWI.tif`
- `NDMI.tif`
- `NBR.tif`
- `IRONOX.tif`
- `IRON_SWIR.tif`
- `BSI.tif`
- `hypercube.tif`
- `hypercube.npy`
- `hypercube_band_order.csv`
- `hypercube_band_stats.csv`
- `hypercube_norm_params.csv`
- `pca_anomaly.tif`
- `pca_eigenvalues.json`
- `objects_index.csv`
- `clusters_summary.csv`
- `alignment_qa.json`

### Notebook names that must not be copied literally

Unsafe or unstable notebook names must be mapped to neutral app names when implemented:

- names containing `Drive`, `Colab`, `Tesla`, `RUN_<TAG>`, `ProjectName`, or local path assumptions
- names containing archaeology, treasure, burial, gold, tunnel, chamber, sarcophagus, or target claims
- names containing exact region references or target references
- names implying direct publication formats such as KMZ/GeoJSON/WKT when those are not approved

### Mapping policy

When notebook naming is unsafe or unstable:

- replace with neutral, domain-functional names
- prefer descriptive names tied to data family, stage ownership, and safety class
- keep mapping tables in this document or a later implementing goal if the family is approved

## Required Artifact Families

These are the full-job families that the app must eventually reproduce as part of the approved full-job scope.

### 1. RUN / GRID / DEM contract family

Category:

- `required_app_artifact`

Expected outputs:

- `grid_manifest.json`
- `dem.tif`
- `dem.npy`

Expected support outputs:

- stage manifests already owned by the core app

Artifact class:

- existing core class rules remain authoritative

Notes:

- this family remains owned by the existing GRID and DEM stages

### 2. SAR RTC core family

Category:

- `required_app_artifact`

Expected outputs:

- `VV_dB.tif`
- `VH_dB.tif`
- `logRatio_dB.tif`
- `incidence.tif`

Artifact class:

- existing core class rules remain authoritative

Notes:

- preserve current parity and RTC formula behavior

### 3. DEM derivatives family

Category:

- `required_app_artifact`

Expected outputs:

- `slope.tif`
- `aspect.tif`
- `curvature.tif`
- `TPI.tif`
- `TRI.tif`
- `roughness.tif`
- `TWI.tif`

Artifact class:

- existing core class rules remain authoritative

### 4. Thermal family

Category:

- `required_app_artifact`

Expected outputs:

- `lst.tif`

Artifact class:

- existing core class rules remain authoritative

### 5. S2 core index family

Category:

- `required_app_artifact`

Expected outputs:

- `NDVI.tif`
- `NDWI.tif`
- `NDMI.tif`
- `NBR.tif`
- `IRONOX.tif`
- `IRON_SWIR.tif`
- `BSI.tif`

Artifact class:

- existing core class rules remain authoritative

Notes:

- `IRON_SWIR` remains governed by the existing Option A parity decision

### 6. Hypercube and PCA family

Category:

- `required_app_artifact`

Expected outputs:

- `hypercube.tif`
- `hypercube.npy`
- `hypercube_band_order.csv`
- `hypercube_band_stats.csv`
- `hypercube_norm_params.csv`
- `pca_anomaly.tif`
- `pca_eigenvalues.json`

Artifact class:

- existing core class rules remain authoritative

### 7. Object extraction family

Category:

- `required_app_artifact`

Expected outputs:

- `objects_index.csv`
- `clusters_summary.csv`

Artifact class:

- existing core class rules remain authoritative

Notes:

- this family does not automatically include per-object context exports or location-bearing patches

### 8. Alignment QA family

Category:

- `required_app_artifact`

Expected outputs:

- `alignment_qa.json`

Artifact class:

- existing core class rules remain authoritative

## Internal QA Artifact Families

These families are approved for future reproduction as non-public internal QA outputs only.

### 1. SAR QA family

Category:

- `internal_qa_artifact`

Representative outputs:

- SAR pair diagnostics JSON
- SAR summary CSV
- per-band nodata audit reports
- pixel-center alignment summaries
- tile-boundary consistency summaries

Preferred directory:

- `qa/sar/`

Default artifact class:

- `FILESYSTEM_ONLY`

Promotion allowed only if redacted:

- `LOCAL_SENSITIVE`

### 2. GRID / DEM / zero-shift QA family

Category:

- `internal_qa_artifact`

Representative outputs:

- RUN/GRID guard summaries
- drift audit summaries
- zero-shift validation reports
- DEM-source audit reports

Preferred directory:

- `qa/grid_dem/`

Default artifact class:

- `FILESYSTEM_ONLY`

Promotion allowed only if redacted:

- `LOCAL_SENSITIVE`

### 3. Band stats / stack audit family

Category:

- `internal_qa_artifact`

Representative outputs:

- band stats CSV
- stack presence summaries
- normalized tensor audit summaries
- stack geometry-consistency summaries

Preferred directory:

- `qa/stacks/`

Default artifact class:

- `FILESYSTEM_ONLY`

Promotion allowed only if redacted:

- `LOCAL_SENSITIVE`

### 4. Hypercube / parity / alignment audit family

Category:

- `internal_qa_artifact`

Representative outputs:

- hypercube audit CSV
- parity QA reports
- alignment QA summaries
- reference comparison summaries without unsafe metadata

Preferred directory:

- `qa/parity/`
- `qa/alignment/`

Default artifact class:

- `FILESYSTEM_ONLY`

Promotion allowed only if redacted:

- `LOCAL_SENSITIVE`

### 5. DEM-matched optical and tensor-support family

Category:

- `internal_qa_artifact`

Representative outputs:

- DEM-matched S2 mask support outputs
- approved optical tensor support outputs
- approved stack/tensor support files that do not encode target claims

Preferred directory:

- `stacks/optical_support/`
- `stacks/tensor_support/`

Default artifact class:

- `FILESYSTEM_ONLY`

Promotion allowed only if redacted:

- `LOCAL_SENSITIVE`

## Out-of-Scope Families

These output families remain out of scope unless a later explicit goal re-approves them.

### 1. Direct notebook runtime mirrors

- Colab folder mirrors
- Drive folder mirrors
- raw notebook full-job dumps
- shell listings
- path crawls
- Drive inventory reports

Category:

- `out_of_scope`

Artifact class if ever persisted:

- `FILESYSTEM_ONLY`

### 2. Coordinate-bearing ROI and target outputs

- lat/lon tables
- WKT dumps
- GeoJSON feature dumps
- exact target tables
- GPS comparison outputs
- exact focus-region outputs with location context

Category:

- `out_of_scope`

Artifact class if ever persisted:

- `FILESYSTEM_ONLY`

### 3. KMZ and Earth-browser deliverables

- heatmap KMZ
- 3D target KMZ
- targets-only KMZ
- field-operations KMZ
- navigation KMZ

Category:

- `out_of_scope`

Artifact class if ever persisted:

- `FILESYSTEM_ONLY`

### 4. Treasure/classifier target-claim sections

- treasure-target outputs
- burial/chamber/gold/tunnel typed outputs
- hard-classifier target products
- classifier outputs with target locations
- exact-target TXT/JSON/CSV products

Category:

- `out_of_scope`

Artifact class if ever persisted:

- `FILESYSTEM_ONLY`

### 5. Training and inference family

- training data scaffolds
- learned weights
- memory-profiled training variants
- inference loops
- detector CSV outputs
- detector GeoJSON outputs
- CNN execution outputs

Category:

- `out_of_scope`

Artifact class if ever persisted:

- `FILESYSTEM_ONLY`

### 6. Per-object context with location-bearing semantics

- per-object context patches
- per-object NPY patches with location context
- focus-region object exports tied to exact target context

Category:

- `out_of_scope`

Artifact class if ever persisted:

- `FILESYSTEM_ONLY`

## Naming Map for Future Implementing Goals

The following mapping rules must be applied by future implementing goals when a notebook output family is approved.

### SAR QA

Suggested neutral names:

- `qa/sar/sar_pair_diagnostics.json`
- `qa/sar/sar_summary.csv`
- `qa/sar/sar_nodata_audit.csv`
- `qa/sar/sar_alignment_summary.json`

### GRID / DEM / zero-shift QA

Suggested neutral names:

- `qa/grid_dem/grid_guard_summary.json`
- `qa/grid_dem/zero_shift_summary.json`
- `qa/grid_dem/drift_audit.csv`
- `qa/grid_dem/dem_audit_summary.json`

### Stack and tensor QA

Suggested neutral names:

- `qa/stacks/band_stats.csv`
- `qa/stacks/stack_presence_summary.json`
- `qa/stacks/tensor_audit_summary.json`
- `qa/stacks/geometry_consistency_summary.json`

### Hypercube and parity QA

Suggested neutral names:

- `qa/parity/hypercube_audit.csv`
- `qa/parity/parity_qa_summary.json`
- `qa/alignment/alignment_summary_redacted.json`

### Optical support outputs

Suggested neutral names:

- `stacks/optical_support/s2_mask_support_<name>.tif`
- `stacks/tensor_support/radar_linear_support_stack.tif`
- `stacks/tensor_support/radar_linear_support_stack.npy`
- `stacks/tensor_support/ai_ready_support_stack.tif`
- `stacks/tensor_support/ai_ready_support_stack.npy`
- `stacks/tensor_support/<neutral_tensor_name>.tif`
- `stacks/tensor_support/<neutral_tensor_name>.npy`

Mapping rules:

- avoid notebook marketing or operator-specific labels
- avoid numbered cell-derived names
- avoid unstable "vRUN", "MASTER", "Tesla", "Amer update", or similar notebook-specific names
- use neutral replacements for notebook sigma0/master/tensor-export variants
- prefer stable, neutral, domain-functional names

### Focus-mask and exact target-zone local outputs

Suggested neutral names:

- `full_job/focus/focus_zone_17m.tif`
- `full_job/focus/focus_zone_17m.npy`
- `full_job/focus/focus_zone_ai_ready_window.npy`
- `full_job/focus/focus_zone_summary.json`
- `full_job/focus/focus_zone_band_summary.csv`

Mapping rules:

- keep these outputs `FILESYSTEM_ONLY`
- do not emit GeoJSON, WKT, KMZ, or target labels in F3
- keep exact target-zone context out of public API responses and public artifact lists

### Exact-location GeoJSON and KMZ local outputs

Suggested neutral names:

- `full_job/location/site_location.geojson`
- `kmz/site_location.kmz`

Mapping rules:

- keep these outputs `FILESYSTEM_ONLY`
- write them only under the local run directory
- do not public-list them
- do not serve them through the normal artifact route
- keep any exact coordinates inside the file contents only, not in public DTOs or error payloads

### Field-operations KMZ and local report outputs

Suggested neutral names:

- `kmz/field_ops_navigation.kmz`
- `full_job/field_ops/field_ops_report.json`
- `full_job/field_ops/field_ops_brief.txt`

Mapping rules:

- keep these outputs `FILESYSTEM_ONLY`
- keep them under the local run directory only
- do not public-list them
- do not serve them through the normal artifact route
- keep exact-location and target context inside local file contents only, never in public DTOs or error payloads

### F2 stack-family coverage and deferrals

The notebook stack-variant families approved for F2 are reconciled as follows.

- `NANO` stack family from cells 36-37:
  deferred
  reason: the notebook keeps duplicate nano-scale variants with different internals and no single canonical neutral formula has been captured yet.
- `SIGMA0 MASTER` family from cells 49-50:
  implemented
  neutral app outputs:
  `stacks/tensor_support/radar_linear_support_stack.tif`
  `stacks/tensor_support/radar_linear_support_stack.npy`
  reason: the reusable part is the linearized radar support stack; the notebook "master" naming is not copied.
- `GPHYS MASTER` family from cell 51:
  deferred
  reason: the notebook geophysics master formulas remain domain-specific and need canonical neutral formula capture before implementation.
- `RAD MASTER CUBE` family from cell 53:
  deferred
  reason: this is a near-duplicate radar-layer assembly over outputs the app already preserves; F2 does not duplicate it without a distinct stable contract.
- `ULTIMATE GPHYS SCAN` family from cell 54:
  deferred
  reason: the notebook combines multiple geophysics scans with unstable composition and needs a reproducible fixed definition first.
- `Tesla v7.2` tensor-export and grid-lock support variants from cells 74, 81, 83, 94:
  implemented subset
  neutral app outputs:
  `stacks/tensor_support/ai_ready_support_stack.tif`
  `stacks/tensor_support/ai_ready_support_stack.npy`
  `stacks/optical_support/s2_mask_support_valid.tif`
  reason: F2 implements the useful grid-locked tensor-export subset only. Tesla inference engines, target-oriented outputs, and target-claim variants remain outside F2.

## Ownership by Existing or Future Stage Families

This contract does not reassign stage ownership at implementation time, but it does define the expected ownership domains for future N-goal work.

Expected ownership:

- SAR QA families: SAR stage domain
- GRID / DEM / zero-shift QA families: GRID / DEM / zero-shift domain
- DEM derivative extras: DEM derivative domain
- optical and thermal support families: S2 and thermal domains
- hypercube / PCA support families: hypercube and PCA domains
- object-support QA families: object extraction and alignment QA domains

## Public Exposure Rule

Nothing in this contract makes notebook full-job outputs public API products.

Unless a later goal explicitly implements a redacted derivative:

- required full-job artifacts remain local artifacts
- internal QA artifacts remain non-public
- out-of-scope artifacts remain out of scope

## Contract Summary

This contract requires future N-phase work to:

- preserve the existing core artifact families already implemented
- add only approved notebook full-job families
- keep `FILESYSTEM_ONLY` as the default class
- promote to `LOCAL_SENSITIVE` only for explicitly redacted operator QA files
- avoid literal unsafe notebook naming
- keep out-of-scope notebook families out of scope until separately approved

## Not an Implementation Step

This document is a contract and naming map only.

It does not:

- implement any new artifact family
- authorize notebook edits
- authorize public exposure
- authorize target-location outputs
- override existing safety and redaction rules

## F-Phase Local-Output Expansion Contract

The N-phase contract covers the approved science-core notebook-equivalent workflow.

The F-phase expands the app toward the user-approved full notebook local-output workflow, but keeps those additions local-first and non-public by default.

### F-Phase scope already approved

The following families are approved for future implementation in the F-phase:

- safe map/manual pin UI for operator point selection
- notebook stack-variant local outputs
- `17 m` focus-mask and exact target-zone local analysis
- exact-location GeoJSON and KMZ local outputs
- hard classifiers and neutral target-label local outputs
- field-operations KMZ and local report outputs
- Drive/reference locator utilities
- GPS point comparison reports
- full notebook local-output comparison reports

### F-Phase local-output rule

Unless a later explicit goal changes access policy with tests:

- F-phase outputs are local run-directory artifacts
- F-phase outputs are not public API products
- exact-location outputs are not publicly listed
- exact-location outputs are not served over HTTP
- notebook Drive-first behavior remains mapped to local run-directory outputs

### F-Phase artifact classes

Default rule:

- new F-phase output families default to `FILESYSTEM_ONLY`

This default is mandatory for:

- exact lat/lon outputs
- GeoJSON
- KMZ
- WKT
- exact target-zone analysis
- focus-mask outputs with exact target context
- classifier target outputs
- GPS comparison reports
- field-operation deliverables with target context
- local path or Drive path inventory reports

`LOCAL_SENSITIVE` remains allowed only for explicitly redacted operator QA summaries that contain no forbidden public content.

### F-Phase experimental local outputs

The following families may be implemented as experimental local outputs only:

- domain-specific or treasure-specific feature-stack variants
- hard classifiers
- neutral target-label outputs
- exact-target operational deliverables

Current neutral local output examples:

- `experimental/classifications.csv`
- `experimental/summary.json`
- `experimental/neutral_target_labels.json`

External naming rules remain:

- use neutral app-facing names
- do not use archaeology, treasure, burial, gold, tunnel, chamber, sarcophagus, or target-claim names in app-facing filenames, API responses, or public UI
- keep original/domain mappings only in approved documentation if needed

### F-Phase on-hold families

The following remain on hold and are not authorized by the F-phase baseline:

- training scaffolding
- CNN/Swin/YOLO/SegFormer inference
- broken model-build cells
- any rebuilt ML training workflow not separately approved

These families remain excluded from implementation until a later explicit goal re-approves them.

### F-Phase ownership guidance

Future F-phase work should use these ownership boundaries:

- safe map/manual pin workflow: frontend and run-submission path
- exact-location and KMZ/GeoJSON exporters: dedicated local-only export modules
- stack-variant families: stack/output stages only
- classifier target logic: experimental local-only modules
- GPS and reference comparison reports: dedicated local utilities or report modules

### F-Phase public-surface rule

Nothing in the F-phase approval changes the existing public redaction contract.

Public API responses must still not expose:

- exact coordinates
- geometry
- WKT
- GeoJSON content
- KMZ content
- target-zone boundaries
- filesystem paths
- Drive paths
- target labels
- classifier outputs

### F-Phase implementation guard

The F-phase contract records user-approved local-output scope only.

It does not by itself:

- authorize notebook edits
- authorize HTTP serving of exact-location artifacts
- authorize public listing of local-only outputs
- authorize training or deep-learning inference
- override the existing N-phase contract for science-core outputs
