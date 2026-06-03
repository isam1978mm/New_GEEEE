# Missing Raster Families Contract

## Purpose

Phase 4A creates a controlled registry and report system for notebook raster families that are missing, partial, or not yet safely implementable. The goal is to make these gaps explicit and machine-readable before any later Phase 4B/4C task implements a family.

Phase 4A is registry/report only. It does not invent formulas, fabricate rasters, call Earth Engine, run the live pipeline, change raster math, alter output names, change artifact serving, or decide public/shared exposure.

## Scope

The registry covers these Phase 4 missing or partial notebook raster families:

- DEM curvature variants: `curv_laplacian_640.tif`, `curv_plan_640.tif`, `curv_profile_640.tif`
- Separate ASC/DESC Sentinel-1 support stacks: `S1_ASC_*_Filtered_640.*`, `S1_DESC_*_Filtered_640.*`
- Panchromatic/optical outputs: `PAN_LS_Panchromatic_640.*`, `PAN_S2_Panchromatic_10m_640.*`, `PAN_LAYERS_STACK_640.npy`
- Resampled/filtered hypercube variants: `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.*`, `S1_FILTERED_LAYERS_STACK_640.npy`
- Broader `AI_BEH_*` and `AI_READY_*` series not already covered by the six secret outputs
- `REPORT_640_*` runtime/value parity
- Six `AI_READY_640_Secret_*` runtime/value parity outputs

Phase 4A does not implement these outputs. Missing families are split so later Phase 4B tasks can target one family at a time with source formulas, fixtures, and parity tests.

## Registry Fields

Each registry item records:

```text
id
family
notebook_paths_or_patterns
current_app_status
known_stage_file
known_stage_class
target_mode
target_phase
parity_priority
classification
requires_coordinates
requires_external_dependency
source_formula_status
runtime_output_verified
notebook_value_parity_verified
implementation_status
blocker
recommended_next_action
notes
```

Allowed `implementation_status` values:

```text
missing
partial
source_writer_exists_unverified
no_source_equivalent_identified
requires_reference_notebook_output
requires_formula_reconstruction
requires_external_dependency
deferred_to_later_phase
```

No registry item targets `public_shared`.

## Verification Rules

File existence is not parity proof. A source writer existing in the repository is different from runtime output proof and different again from notebook-value parity.

The registry keeps these facts separate:

- `source_formula_status`: what is known from source inspection about formulas or writer availability.
- `runtime_output_verified`: whether a real run has proven the output is produced.
- `notebook_value_parity_verified`: whether comparison against a notebook reference has proven value parity.

Phase 4A defaults runtime and notebook-value parity to `false` for all registry items.

## Stage Classification Rules

`app/pipeline/stages/secret_layers.py` is a notebook-parity semantic raster stage, not clean defensible core by default.

`app/pipeline/stages/report_640.py` is a notebook-parity report/semantic raster stage, not clean defensible core by default.

These classifications allow later implementation to preserve notebook behavior without silently promoting semantic/report rasters into core app or public/shared mode.

## Report Output

The report helper writes:

```text
data/runs/<run_id>/manifests/missing_raster_families_report.json
```

The JSON report contains:

```text
schema_version
run_id
created_at
items
counts_by_status
```

The report path is resolved under the run directory. Report writing creates only the manifest JSON parent directory and the JSON file. It does not create, copy, or synthesize `.tif`, `.npy`, or other raster/tensor files.

## Non-Goals

Phase 4A does not:

- invent missing source formulas;
- generate DEM curvature variants;
- generate ASC/DESC SAR stacks;
- generate panchromatic rasters or stacks;
- generate resampled hypercubes or filtered S1 stacks;
- generate broader AI behavior rasters;
- prove runtime presence of `REPORT_640_*` or `AI_READY_640_Secret_*` outputs;
- prove notebook-value parity for any raster family;
- change live pipeline behavior;
- add API, frontend, database, migration, or artifact-serving changes;
- decide public/shared exposure.

Future classifier/model output wording remains probability-only, but Phase 4A does not implement classifier logic.

## Recommended Phase 4B Flow

Each Phase 4B task should select one registry family, recover or cite the exact source formulas and data-selection rules, add focused tests, and then implement that family without changing unrelated math or outputs.

A practical first Phase 4B target is the DEM curvature variants because they are narrow, non-coordinate-bearing, and already adjacent to `dem_derivatives.py`; however they still require exact notebook formula reconstruction and reference output comparison before implementation.
