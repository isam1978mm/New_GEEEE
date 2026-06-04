# AI_READY Anomaly Parity Contract

## Purpose

Phase 4K locks the recovery and verification contract for these notebook-parity semantic rasters:

- `AI_READY_640_Magnetic_Anomaly.tif`
- `AI_READY_640_EM_Anomaly.tif`

The objective is faithful notebook-to-app parity planning without changing stage formulas, runtime behavior, or artifact exposure policy.

## Scope

Phase 4K adds:

- a recovery checklist for the two anomaly outputs;
- a TIFF verification helper for future app-produced counterparts;
- tests for recovery reporting and TIFF verification behavior.

These outputs remain notebook-parity and private by default. They are not clean public/core outputs by default.

## Non-Goals

Phase 4K does not:

- generate anomaly rasters;
- implement Magnetic or EM anomaly formulas;
- change `secret_layers.py`;
- change `report_640.py`;
- change hypercube logic;
- change semantic raster formulas;
- change raster math;
- call Earth Engine;
- integrate into the live pipeline;
- change API, frontend, database, or artifact serving policy.

## Source-Evidence Lock

Current notebook evidence keeps both anomaly names visible in patch and downstream semantic-scoring cells:

- patch search aliases around `notebooks/new.ipynb` lines `27117-27125` and `30873-30890`;
- optional-band and downstream semantic scoring cells around `27966-28042`, `29595-29792`, `30237-30439`, `31239-31359`, `31679-31871`, `32674-32866`, and `33569-33840`.

That evidence supports these statements:

- both outputs are treated as optional semantic rasters in later notebook scoring;
- both outputs are consumed as standalone raster names by downstream notebook logic;
- no standalone writer formula for either output is recovered in the current app source or the notebook cells reviewed for Phase 4K.

Additional EM-only evidence exists in the patched hypercube compatibility path:

- `app/pipeline/stages/hypercube.py` keeps a frozen-compatible patched stack note that the patched EM slot maps to `DEM_GEO8_TIFS/DEM_640.tif`;
- that mapping is compatibility logic for `FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif`;
- that mapping does not by itself recover a standalone notebook writer contract for `AI_READY_640_EM_Anomaly.tif`.

Current Phase 4K source-status lock:

- `AI_READY_640_Magnetic_Anomaly.tif`: `partial_source_found`
- `AI_READY_640_EM_Anomaly.tif`: `partial_source_found`

Current authoritative-source lock:

- authoritative standalone source available for Magnetic anomaly: `false`
- authoritative standalone source available for EM anomaly: `false`

## Current App Status

The app does not write either anomaly raster as an explicit output.

Existing outputs are not automatically equivalent to these notebook anomaly outputs.

`secret_layers.py` remains a notebook-parity semantic raster stage, not clean defensible core by default.

`report_640.py` remains a notebook-parity report/semantic raster stage, not clean defensible core by default.

File existence is not parity proof. Runtime output presence and notebook-value parity remain separate.

## Expected Inputs and Formula Status

### `AI_READY_640_Magnetic_Anomaly.tif`

- expected input outputs: unknown
- formula status: notebook usage is visible, standalone writer formula remains unrecovered
- implementation status: `blocked_no_source_formula`

### `AI_READY_640_EM_Anomaly.tif`

- patch-era compatibility input evidence: `DEM_GEO8_TIFS/DEM_640.tif`
- formula status: notebook usage is visible, standalone writer formula remains unrecovered
- implementation status: `blocked_no_source_formula`

The EM patch mapping should not be treated as a standalone parity formula. It is only enough to justify recovery status `partial_source_found`.

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

Until those references are captured, these metadata expectations remain unresolved for both outputs.

## Verification Contract

The verifier accepts:

- `app_output_dir`
- `notebook_reference_dir`
- `run_dir`
- `run_id`

It checks these files in both trees:

- `AI_READY_640_Magnetic_Anomaly.tif`
- `AI_READY_640_EM_Anomaly.tif`

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

- `data/runs/<run_id>/manifests/ai_ready_anomaly_parity_verification.json`

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

No Phase 4K item targets `public_shared`.

## Future Interpretation Rule

If a later classifier or model interpretation layer uses these anomaly rasters, interpreted outputs must use probability-only wording. This phase does not implement classifier logic.

## Remaining Unknowns

Phase 4K leaves these unknowns explicit:

- exact standalone notebook writer formula for `AI_READY_640_Magnetic_Anomaly.tif`
- exact standalone notebook writer formula for `AI_READY_640_EM_Anomaly.tif`
- whether either raster had a dedicated writer cell separate from patched hypercube support logic
- final dtype and nodata policy
- frozen-reference CRS, transform, width, height, and value tolerance

## Next Step

Later implementation should be source-reference-driven:

1. capture frozen notebook anomaly rasters;
2. capture any notebook patch report or writer-cell details that tighten the source contract;
3. run the Phase 4K verifier against future app-produced counterparts;
4. only then decide whether a dedicated writer slice is justified.
