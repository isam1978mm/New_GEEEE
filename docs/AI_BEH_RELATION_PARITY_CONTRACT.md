# AI_BEH Relation Parity Contract

## Purpose

Phase 4H5 locks the recovery and verification contract for these notebook-parity semantic rasters:

- `AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif`
- `AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif`
- `AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif`

The objective is faithful notebook-to-app parity planning without changing stage formulas, runtime behavior, or artifact exposure policy.

## Scope

Phase 4H5 adds:

- a recovery checklist for the three AI_BEH relation outputs;
- a TIFF verification helper for future app-produced counterparts;
- tests for recovery reporting and TIFF verification behavior.

These outputs remain notebook-parity and private by default. They are not clean public/core outputs by default.

## Non-Goals

Phase 4H5 does not:

- generate AI_BEH relation rasters;
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

Current notebook evidence includes both the exact builder cell and later stack or candidate-file cells:

- `notebooks/new.ipynb` around `23418-23424` builds the three relation rasters directly from Sentinel-2 source bands;
- `notebooks/new.ipynb` around `23644-23732`, `23972-23974`, and `44248-44250` keeps the filenames visible in stack assembly;
- `notebooks/new.ipynb` around `35469-35471` keeps the three output filenames visible in the candidate file table.

That evidence supports these statements:

- each AI_BEH relation output is a standalone notebook output;
- each AI_BEH relation output is also a downstream stack component;
- the notebook keeps exact formulas for all three outputs;
- no current app stage writes these notebook-named AI_BEH relation rasters.

Current Phase 4H5 source-status lock:

- `AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif`: `exact_source_found`
- `AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif`: `exact_source_found`
- `AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif`: `exact_source_found`

Current authoritative-source lock:

- authoritative standalone source available for all three AI_BEH relation outputs: `true`

## Current App Status

The app does not write any of the three AI_BEH relation rasters as explicit outputs.

Existing outputs are not automatically equivalent to these notebook outputs.

`secret_layers.py` remains a notebook-parity semantic raster stage, not clean defensible core by default.

`report_640.py` remains a notebook-parity report/semantic raster stage, not clean defensible core by default.

File existence is not parity proof. Runtime output presence and notebook-value parity remain separate.

## Expected Inputs And Formula Status

Notebook source keeps this input set visible:

- `B3`
- `B4`
- `B8`
- `B11`
- `B12`

Recovered formulas:

- `AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif` -> `normalizedDifference(B8, B4)`
- `AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif` -> `B4 / B3`
- `AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif` -> `B11 / B12`

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

- `AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif`
- `AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif`
- `AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif`

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

- `data/runs/<run_id>/manifests/ai_beh_relation_parity_verification.json`

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

No Phase 4H5 item targets `public_shared`.

## Future Interpretation Rule

If a later classifier or model interpretation layer uses these rasters, interpreted outputs must use probability-only wording. This phase does not implement classifier logic.

## Remaining Unknowns

Phase 4H5 leaves these unknowns explicit:

- final exported dtype for each AI_BEH relation raster
- exact nodata or NaN persistence after notebook export
- frozen-reference CRS, transform, width, height, and value tolerance
- whether the notebook export introduced any additional cast or clipping behavior beyond the visible source cells

## Next Step

Later implementation should be source-reference-driven:

1. capture the frozen notebook AI_BEH relation rasters;
2. confirm final exported metadata from the frozen reference bundle;
3. run the Phase 4H5 verifier against future app-produced counterparts;
4. only then decide whether a dedicated writer slice is justified.
