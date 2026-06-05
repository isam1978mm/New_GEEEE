# AI_BEH Alloy Statue Parity Contract

## Purpose

Phase 4H10 locks the recovery and verification contract for this notebook-parity semantic raster:

- `AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.tif`

The objective is faithful notebook-to-app parity planning without changing stage formulas, runtime behavior, or artifact exposure policy.

## Scope

Phase 4H10 adds:

- a recovery checklist for the alloy/statue output;
- a TIFF verification helper for a future app-produced counterpart;
- tests for recovery reporting and TIFF verification behavior.

This output remains notebook-parity and private by default. It is not a clean public/core output by default.

## Non-Goals

Phase 4H10 does not:

- generate the alloy/statue semantic raster;
- implement AI_BEH formulas;
- change `secret_layers.py`;
- change `report_640.py`;
- change hypercube logic;
- change semantic raster formulas;
- change raster math;
- call Earth Engine;
- integrate into the live pipeline;
- change API, frontend, database, or artifact serving policy.

## Source-Evidence Lock

Current notebook evidence keeps the exact builder cell and later export-name tables visible:

- `notebooks/new.ipynb` around `24307-24310` builds `AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640` directly from `normalizedDifference(['B4', 'B8'])`;
- `notebooks/new.ipynb` around `24372` keeps the exported filename visible in the expected-signatures list;
- `notebooks/new.ipynb` around `35479` keeps the exported filename visible in the candidate file table.

That evidence supports these statements:

- this AI_BEH alloy/statue output is a standalone notebook output;
- it is also a downstream stack component;
- the notebook keeps an exact formula for the output;
- no current app stage writes this notebook-named AI_BEH raster.

Current Phase 4H10 source-status lock:

- `AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.tif`: `exact_source_found`

Current authoritative-source lock:

- authoritative standalone source available for this output: `true`

## Current App Status

The app does not write this AI_BEH alloy/statue raster as an explicit output.

Existing outputs are not automatically equivalent to this notebook output.

`secret_layers.py` remains a notebook-parity semantic raster stage, not clean defensible core by default.

`report_640.py` remains a notebook-parity report/semantic raster stage, not clean defensible core by default.

File existence is not parity proof. Runtime output presence and notebook-value parity remain separate.

## Expected Inputs And Formula Status

Notebook source keeps this input set visible:

- `B4`
- `B8`

Recovered formula:

- `AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.tif` -> `normalizedDifference(B4, B8)`

Implementation status:

- `requires_reference_output`

The formula and export names are visible, but frozen notebook references are still required before any later implementation can claim notebook-value parity.

## Metadata Expectations

The notebook source keeps the formula cell and output name visible, but this phase does not recover a frozen metadata lock for:

- dtype
- nodata or NaN policy
- CRS
- transform
- width
- height
- band count
- numeric tolerance

Frozen notebook references are still required to lock those values.

## Verification Contract

The verifier accepts:

- `app_output_dir`
- `notebook_reference_dir`
- `run_dir`
- `run_id`

It checks this file in both trees:

- `AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.tif`

If `rasterio` is importable, it compares:

- width
- height
- CRS
- transform
- dtype
- nodata
- band count
- numeric values

If `rasterio` is unavailable, the verifier reports `comparison_unavailable` and records SHA256 hashes for presence tracking only.

The verifier writes only:

- `data/runs/<run_id>/manifests/ai_beh_alloy_statue_parity_verification.json`

It does not write or modify raster or NPY outputs.

`notebook_value_parity_verified=true` is allowed only when a real reference comparison passes.

## Classification And Exposure

Verification entries use:

- family: `AI_BEH semantic rasters`
- target mode: `notebook_parity`
- classification: `notebook-parity semantic raster stage`
- artifact class: `LOCAL_SENSITIVE`
- requires coordinates: `false`
- probability only required: `false`
- http servable: `false`

No Phase 4H10 item targets `public_shared`.

## Future Interpretation Rule

If a later classifier or model interpretation layer uses this raster, interpreted outputs must use probability-only wording. This phase does not implement classifier logic.

## Remaining Unknowns

Phase 4H10 leaves these unknowns explicit:

- final exported dtype
- exact nodata or NaN persistence after notebook export
- frozen-reference CRS, transform, width, height, and value tolerance
- whether the notebook export introduced any additional cast or clipping behavior beyond the visible source cell

## Next Step

Later implementation should be source-reference-driven:

1. capture the frozen notebook alloy/statue raster;
2. lock final exported metadata from the frozen reference bundle;
3. run the Phase 4H10 verifier against a future app-produced counterpart;
4. only then decide whether a dedicated writer slice is justified.
