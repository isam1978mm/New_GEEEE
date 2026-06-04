# AI_BEH Logic Parity Contract

## Purpose

Phase 4H7 locks the recovery and verification contract for these notebook-parity semantic rasters:

- `AI_BEH_SecretEntry_REL_ND_DOM_lin_640.tif`
- `AI_BEH_StatueLogic_REL_Diff_DOM_lin_640.tif`

The objective is faithful notebook-to-app parity planning without changing stage formulas, runtime behavior, or artifact exposure policy.

## Scope

Phase 4H7 adds:

- a recovery checklist for the two AI_BEH logic outputs;
- a TIFF verification helper for future app-produced counterparts;
- tests for recovery reporting and TIFF verification behavior.

These outputs remain notebook-parity and private by default. They are not clean public/core outputs by default.

## Non-Goals

Phase 4H7 does not:

- generate AI_BEH logic rasters;
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

Current notebook evidence keeps the exact builder cells visible:

- `notebooks/new.ipynb` around `24207-24209` builds `AI_BEH_SecretEntry_REL_ND_DOM_lin_640` directly from `normalizedDifference(['B12', 'B8A'])`;
- `notebooks/new.ipynb` around `24211-24213` builds `AI_BEH_StatueLogic_REL_Diff_DOM_lin_640` directly from `B11 - B4`;
- `notebooks/new.ipynb` around `35474` keeps the exported filename visible for `AI_BEH_SecretEntry_REL_ND_DOM_lin_640.tif`.

That evidence supports these statements:

- each AI_BEH logic output is a standalone notebook output;
- each AI_BEH logic output is also a downstream stack component;
- the notebook keeps exact formulas for both outputs;
- no current app stage writes these notebook-named AI_BEH logic rasters.

Current Phase 4H7 source-status lock:

- `AI_BEH_SecretEntry_REL_ND_DOM_lin_640.tif`: `exact_source_found`
- `AI_BEH_StatueLogic_REL_Diff_DOM_lin_640.tif`: `exact_source_found`

Current authoritative-source lock:

- authoritative standalone source available for both AI_BEH logic outputs: `true`

For `StatueLogic`, the current lock comes from the builder cell itself. This phase does not claim a separate later notebook filename-table line beyond that builder-cell evidence.

## Current App Status

The app does not write either AI_BEH logic raster as an explicit output.

Existing outputs are not automatically equivalent to these notebook outputs.

`secret_layers.py` remains a notebook-parity semantic raster stage, not clean defensible core by default.

`report_640.py` remains a notebook-parity report/semantic raster stage, not clean defensible core by default.

File existence is not parity proof. Runtime output presence and notebook-value parity remain separate.

## Expected Inputs And Formula Status

Notebook source keeps this input set visible:

- `B4`
- `B8A`
- `B11`
- `B12`

Recovered formulas:

- `AI_BEH_SecretEntry_REL_ND_DOM_lin_640.tif` -> `normalizedDifference(B12, B8A)`
- `AI_BEH_StatueLogic_REL_Diff_DOM_lin_640.tif` -> `B11 - B4`

Implementation status for each output:

- `requires_reference_output`

The formulas and export names are visible, but frozen notebook references are still required before any later implementation can claim notebook-value parity.

## Metadata Expectations

The notebook source keeps the formula cells and output names visible, but this phase does not recover a frozen metadata lock for:

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

It checks these files in both trees:

- `AI_BEH_SecretEntry_REL_ND_DOM_lin_640.tif`
- `AI_BEH_StatueLogic_REL_Diff_DOM_lin_640.tif`

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

- `data/runs/<run_id>/manifests/ai_beh_logic_parity_verification.json`

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

No Phase 4H7 item targets `public_shared`.

## Future Interpretation Rule

If a later classifier or model interpretation layer uses these rasters, interpreted outputs must use probability-only wording. This phase does not implement classifier logic.

## Remaining Unknowns

Phase 4H7 leaves these unknowns explicit:

- final exported dtype for each AI_BEH logic raster
- exact nodata or NaN persistence after notebook export
- frozen-reference CRS, transform, width, height, and value tolerance
- whether the notebook export introduced any additional cast or clipping behavior beyond the visible source cells

## Next Step

Later implementation should be source-reference-driven:

1. capture the frozen notebook AI_BEH logic rasters;
2. lock final exported metadata from the frozen reference bundle;
3. run the Phase 4H7 verifier against future app-produced counterparts;
4. only then decide whether a dedicated writer slice is justified.
