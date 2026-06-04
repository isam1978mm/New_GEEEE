# AI_READY Metal Hardness Parity Contract

## Purpose

Phase 4H3 locks the recovery and verification contract for the notebook-parity semantic raster:

- `AI_READY_640_Metal_Hardness.tif`

The objective is faithful notebook-to-app parity planning without changing stage formulas, runtime behavior, or artifact exposure policy.

## Scope

Phase 4H3 adds:

- a recovery checklist for the Metal Hardness output;
- a TIFF verification helper for a future app-produced counterpart;
- tests for recovery reporting and TIFF verification behavior.

This output remains notebook-parity and private by default. It is not a clean public/core output by default.

## Non-Goals

Phase 4H3 does not:

- generate the Metal Hardness raster;
- implement a Metal Hardness formula;
- change `secret_layers.py`;
- change `report_640.py`;
- change hypercube logic;
- change semantic raster formulas;
- change raster math;
- call Earth Engine;
- integrate into the live pipeline;
- change API, frontend, database, or artifact serving policy.

## Source-Evidence Lock

Current notebook evidence keeps `AI_READY_640_Metal_Hardness.tif` visible as a spatial reference and expected-layer artifact:

- `notebooks/new.ipynb` line area `45081` uses it as the pixel-lock reference path;
- `notebooks/new.ipynb` line area `45168` includes it in the expected output list;
- `notebooks/new.ipynb` line areas `45221`, `45303`, `45455`, and `45528` reuse it as a spatial anchor for later export flows.

That evidence supports these statements:

- the notebook treats `AI_READY_640_Metal_Hardness.tif` as a standalone named artifact;
- later notebook flows depend on it as an anchor or reference raster;
- no standalone writer formula for the raster is recovered in the current app source or notebook cells reviewed for Phase 4H3;
- no dedicated patch-compatibility derivation path is recovered for this raster.

Current Phase 4H3 source-status lock:

- `AI_READY_640_Metal_Hardness.tif`: `partial_source_found`

Current authoritative-source lock:

- authoritative standalone source available for Metal Hardness: `false`

## Current App Status

The app does not write `AI_READY_640_Metal_Hardness.tif` as an explicit output.

Existing outputs are not automatically equivalent to this notebook output.

`secret_layers.py` remains a notebook-parity semantic raster stage, not clean defensible core by default.

`report_640.py` remains a notebook-parity report/semantic raster stage, not clean defensible core by default.

File existence is not parity proof. Runtime output presence and notebook-value parity remain separate.

## Expected Inputs and Formula Status

Current evidence does not recover a standalone input contract.

- expected input outputs: unknown
- formula status: notebook usage is visible, standalone writer formula remains unrecovered
- implementation status: `blocked_no_source_formula`

The notebook references show how the raster is reused, not how it is generated.

## Metadata Expectations

Frozen notebook references are required to lock:

- dtype
- nodata or NaN policy
- CRS
- transform
- width
- height
- band count
- numeric tolerance

Until those references are captured, these metadata expectations remain unresolved.

## Verification Contract

The verifier accepts:

- `app_output_dir`
- `notebook_reference_dir`
- `run_dir`
- `run_id`

It checks this file in both trees:

- `AI_READY_640_Metal_Hardness.tif`

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

- `data/runs/<run_id>/manifests/ai_ready_metal_hardness_parity_verification.json`

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

No Phase 4H3 item targets `public_shared`.

## Future Interpretation Rule

If a later classifier or model interpretation layer uses this raster, interpreted outputs must use probability-only wording. This phase does not implement classifier logic.

## Remaining Unknowns

Phase 4H3 leaves these unknowns explicit:

- exact standalone notebook writer formula for `AI_READY_640_Metal_Hardness.tif`
- whether the notebook generated the raster directly or copied it from an earlier private export path
- final dtype and nodata policy
- frozen-reference CRS, transform, width, height, and value tolerance
- any source-stage dependency chain that fed the raster before it became the notebook anchor layer

## Next Step

Later implementation should be source-reference-driven:

1. capture the frozen notebook Metal Hardness raster;
2. recover any notebook writer-cell or export-cell details that tighten the source contract;
3. run the Phase 4H3 verifier against a future app-produced counterpart;
4. only then decide whether a dedicated writer slice is justified.
