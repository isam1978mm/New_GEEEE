# AI_READY Fraction Parity Contract

## Purpose

Phase 4H4 locks the recovery and verification contract for these notebook-parity semantic rasters:

- `AI_READY_640_Fraction_Gold.tif`
- `AI_READY_640_Fraction_Pottery.tif`
- `AI_READY_640_Fraction_Carbon_Age.tif`
- `AI_READY_640_Fraction_Silver_Lead.tif`

The objective is faithful notebook-to-app parity planning without changing stage formulas, runtime behavior, or artifact exposure policy.

## Scope

Phase 4H4 adds:

- a recovery checklist for the four Fraction_* outputs;
- a TIFF verification helper for future app-produced counterparts;
- tests for recovery reporting and TIFF verification behavior.

These outputs remain notebook-parity and private by default. They are not clean public/core outputs by default.

## Non-Goals

Phase 4H4 does not:

- generate Fraction_* rasters;
- implement Fraction_* formulas;
- change `secret_layers.py`;
- change `report_640.py`;
- change hypercube logic;
- change semantic raster formulas;
- change raster math;
- call Earth Engine;
- integrate into the live pipeline;
- change API, frontend, database, or artifact serving policy.

## Source-Evidence Lock

Current notebook evidence includes both the exact builder cell and later export-monitor cells:

- `notebooks/new.ipynb` around `45229-45267` builds the Sentinel-2 composite, defines `extract_unmixed_targets(image)`, applies `purity_mask.Not()`, and exports the resulting band layers on the Metal Hardness-aligned grid;
- `notebooks/new.ipynb` around `45303-45310` and `45455-45462` keeps the four expected notebook filenames visible.

That evidence supports these statements:

- each Fraction_* output is a standalone notebook output;
- each Fraction_* output is built from Sentinel-2 source bands, not from a patched compatibility branch;
- the Metal Hardness raster is used as the spatial anchor for export geometry;
- no current app stage writes these notebook-named Fraction_* rasters.

Current Phase 4H4 source-status lock:

- `AI_READY_640_Fraction_Gold.tif`: `exact_source_found`
- `AI_READY_640_Fraction_Pottery.tif`: `exact_source_found`
- `AI_READY_640_Fraction_Carbon_Age.tif`: `exact_source_found`
- `AI_READY_640_Fraction_Silver_Lead.tif`: `exact_source_found`

Current authoritative-source lock:

- authoritative standalone source available for all four Fraction_* outputs: `true`

## Current App Status

The app does not write any of the four Fraction_* rasters as explicit outputs.

Existing outputs are not automatically equivalent to these notebook outputs.

`secret_layers.py` remains a notebook-parity semantic raster stage, not clean defensible core by default.

`report_640.py` remains a notebook-parity report/semantic raster stage, not clean defensible core by default.

File existence is not parity proof. Runtime output presence and notebook-value parity remain separate.

## Expected Inputs and Formula Status

Notebook source keeps this input set visible:

- `B1`
- `B2`
- `B4`
- `B8`
- `B8A`
- `B11`
- `B12`
- `AI_READY_640_Metal_Hardness.tif` as the export-grid anchor

Recovered formulas:

- `AI_READY_640_Fraction_Gold.tif` -> `(B12 - B11) / (B12 + B11)`
- `AI_READY_640_Fraction_Pottery.tif` -> `B11 / (B8A + 0.0001)`
- `AI_READY_640_Fraction_Carbon_Age.tif` -> `normalizedDifference(B11, B12)`
- `AI_READY_640_Fraction_Silver_Lead.tif` -> `B2 / (B4 + 0.0001)`

Recovered mask behavior:

- `purity_mask = B8 > B4`
- exported fraction layers use `purity_mask.Not()`

Implementation status for each output:

- `requires_reference_output`

The formulas and export path are visible, but frozen notebook references are still required before any later implementation can claim notebook-value parity.

## Metadata Expectations

Notebook source shows that export geometry is aligned to `drive_crs` and `drive_transform` loaded from `AI_READY_640_Metal_Hardness.tif`.

Frozen notebook references are still required to lock:

- dtype
- nodata or NaN policy
- CRS
- transform
- width
- height
- band count
- numeric tolerance

Until those references are captured, these metadata expectations remain partially unresolved.

## Verification Contract

The verifier accepts:

- `app_output_dir`
- `notebook_reference_dir`
- `run_dir`
- `run_id`

It checks these files in both trees:

- `AI_READY_640_Fraction_Gold.tif`
- `AI_READY_640_Fraction_Pottery.tif`
- `AI_READY_640_Fraction_Carbon_Age.tif`
- `AI_READY_640_Fraction_Silver_Lead.tif`

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

- `data/runs/<run_id>/manifests/ai_ready_fraction_parity_verification.json`

It does not write or modify raster or NPY outputs.

`notebook_value_parity_verified=true` is allowed only when a real reference comparison passes.

## Classification and Exposure

Verification entries use:

- family: `AI_READY semantic rasters`
- target mode: `notebook_parity`
- classification: `notebook-parity semantic raster stage`
- artifact class: `LOCAL_SENSITIVE`
- requires coordinates: `false`
- probability only required: `false`
- http servable: `false`

No Phase 4H4 item targets `public_shared`.

## Future Interpretation Rule

If a later classifier or model interpretation layer uses these rasters, interpreted outputs must use probability-only wording. This phase does not implement classifier logic.

## Remaining Unknowns

Phase 4H4 leaves these unknowns explicit:

- final exported dtype for each Fraction_* raster
- exact nodata or NaN persistence after masking and export
- frozen-reference CRS, transform, width, height, and value tolerance
- whether the notebook export introduced any additional clipping or cast behavior beyond the visible source cell

## Next Step

Later implementation should be source-reference-driven:

1. capture the frozen notebook Fraction_* rasters;
2. confirm final exported metadata from the frozen reference bundle;
3. run the Phase 4H4 verifier against future app-produced counterparts;
4. only then decide whether a dedicated writer slice is justified.
