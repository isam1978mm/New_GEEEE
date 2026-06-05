# Phase 5 QA Intermediate Parity Contract

## Purpose

Phase 5 locks the source-of-truth inventory for notebook QA and intermediate parity work.

This phase is inventory, contract, and verification-planning only. It records which QA and intermediate artifact families appear in notebook references, which app artifacts look like source-backed candidates, and which later verifier or reference slices are still required.

## Scope

Phase 5 covers these categories:

- `qa_manifests`
- `provenance_reports`
- `alignment_checks`
- `sar_provenance`
- `pca_stack_qa`
- `grid_consistency_reports`

## Non-Goals

Phase 5 does not:

- generate QA or intermediate artifacts
- generate rasters
- generate NPY arrays
- call Earth Engine
- change science, raster, SAR, optical, DEM, PCA, or GRID logic
- change object extraction logic
- change classifier logic
- change API, frontend, or database behavior
- change artifact serving policy
- expose notebook-parity outputs publicly
- rename existing outputs

## Inventory Model

Phase 5 adds `app/pipeline/parity/qa_intermediate_inventory.py` with:

- `get_phase_5_qa_intermediate_inventory()`
- `write_phase_5_qa_intermediate_inventory_report()`

Each inventory item records:

- notebook artifact or pattern
- current app artifact or pattern
- source status
- current app status
- parity status
- expected inputs
- expected outputs
- required reference artifacts
- required metadata
- target mode
- classification
- exposure flags
- runtime output verification state
- notebook-value parity verification state
- implementation status
- blocker and next action

## Status Rules

Allowed `source_status` values:

- `exact_source_found`
- `partial_source_found`
- `no_source_found`
- `existing_app_equivalent_found`
- `unknown_needs_reference`

Allowed `parity_status` values:

- `covered_by_existing_contract`
- `inventory_only`
- `verifier_needed`
- `reference_needed`
- `source_recovery_needed`
- `implementation_later`
- `blocked`

Allowed `implementation_status` values:

- `no_action_needed_existing_contract`
- `requires_verifier_contract`
- `requires_reference_output`
- `requires_source_reconstruction`
- `requires_inventory_reconciliation`
- `implementation_deferred`

## Interpretation Rules

Read the Phase 5 inventory conservatively:

- runtime output presence and notebook-value parity are separate
- an app artifact that looks similar to a notebook artifact is only a candidate until source evidence supports the mapping
- frozen notebook references are required before notebook-value parity can pass
- all Phase 5 items remain private notebook-parity tracking by default
- no Phase 5 item defaults to `http_servable=true`

This contract does not claim notebook-value parity for any QA or intermediate artifact family.

## Category Notes

### QA manifests

This category tracks notebook-style QA manifest artifacts such as:

- `QA/RUN_MANIFEST.json`
- `QA/QA_GRID_dx_m_640.tif`
- `QA/QA_GRID_dy_m_640.tif`
- `QA/QA_GRID_validmask_640.tif`

The app grid stage writes notebook-compatible QA manifest artifacts plus `grid_manifest.json`. A later verifier is still required before parity claims are reasonable.

### Provenance reports

This category tracks broader provenance-style manifests and CSV or JSON reports:

- `stage_*.manifest.json`
- hypercube or stack audit reports
- drift or report-summary tables

The app already emits several provenance-style artifacts, but the notebook grouping and filename expectations still need reconciliation against frozen references.

### Alignment checks

This category tracks alignment reports such as:

- `alignment_qa.json`
- `alignment_audit.csv`
- `alignment_mask_selection.json`
- `QA/alignment/alignment_summary_redacted.json`

The app alignment stage produces app-native outputs. A later verifier slice still needs frozen notebook references.

### SAR provenance

This category tracks notebook SAR provenance and notebook SAR intermediate reporting patterns such as:

- `QA_RADAR_CELL25_PAIR_IDS_*.json`
- `QA_S1_MASTER_UNITS.json`
- `QA_RADAR_META_*.json`
- `SUMMARY_RADAR_*.csv`
- `QA/sar/intermediates/sar_intermediate_manifest.json`

The app SAR stage writes provenance reports and a notebook-style intermediate manifest, but the mapping between notebook filenames and app provenance outputs is still not one-to-one.

### PCA stack QA

This category tracks PCA and stack QA artifacts such as:

- `QA/parity/parity_qa_summary.json`
- `QA/parity/hypercube_audit.csv`
- `QA/stacks/band_stats.csv`
- `QA/stacks/tensor_audit_summary.json`

The app writes these artifacts, but Phase 5 does not yet add a notebook-reference verifier.

### GRID consistency reports

This category tracks GRID consistency artifacts such as:

- `QA/grid_dem/zero_shift_summary.json`
- `QA/grid_dem/drift_audit.csv`
- `QA/stacks/geometry_consistency_summary.json`
- `QA/grid_dem/grid_guard_summary.json`

The app has equivalent-style reports, but the notebook family still needs tighter inventory reconciliation before a dedicated verifier should be written.

## Report Output

The Phase 5 JSON report is written under:

```text
data/runs/<run_id>/manifests/phase_5_qa_intermediate_inventory.json
```

The report path is resolved under the run directory and path traversal is rejected.

Report fields:

- `schema_version`
- `run_id`
- `created_at`
- `items`
- `counts_by_category`
- `counts_by_parity_status`
- `counts_by_implementation_status`
- `phase_5_runtime_changes=false`
- `notes`

The report must not create `.tif`, `.tiff`, `.npy`, `.geojson`, `.kmz`, or raster artifacts.

## Roadmap Position

Phase 5 follows Phase `4Z` and precedes Phase `6` in the full notebook-parity roadmap.

Later implementation or verifier slices must remain source-driven and reference-driven. This contract is the inventory lock only.
