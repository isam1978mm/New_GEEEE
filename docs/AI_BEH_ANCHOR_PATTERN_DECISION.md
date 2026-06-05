# AI_BEH Anchor Pattern Decision

## Purpose

Phase 4H11 locks the decision contract for these notebook-parity semantic patterns:

- `AI_BEH_VegRoot_Anomaly`
- `AI_BEH_IronOxide_Hardness`
- `AI_BEH_GoldAlloy_Signal`
- `AI_BEH_MassVolume_Shadow`

The goal is to decide whether each pattern needs a future standalone parity slice or should remain documented as an internal or downstream REPORT_640 behavior only.

## Scope

Phase 4H11 adds:

- a decision helper for the four anchor and non-TIF semantic patterns;
- a JSON decision report writer;
- tests for decision enumeration and report behavior.

These items remain notebook-parity and private by default. They are not clean public/core outputs by default.

## Non-Goals

Phase 4H11 does not:

- generate anchor or non-TIF outputs;
- implement AI_BEH formulas;
- create new raster writers;
- create a new TIFF verifier for these patterns;
- change `report_640.py`;
- change `secret_layers.py`;
- change hypercube logic;
- change raster math;
- call Earth Engine;
- integrate into the live pipeline;
- change API, frontend, database, or artifact serving policy.

## Notebook Evidence

`notebooks/new.ipynb` keeps the four patterns visible inside `beh_tensors`:

- `AI_BEH_VegRoot_Anomaly` -> `normalizedDifference(B8, B4)`
- `AI_BEH_IronOxide_Hardness` -> `B4 / B3`
- `AI_BEH_GoldAlloy_Signal` -> `B12 / B11`
- `AI_BEH_MassVolume_Shadow` -> `B12 * ST_B10 / 1000`

The same notebook block then uses those tensors like this:

- `AI_BEH_GoldAlloy_Signal`, `AI_BEH_IronOxide_Hardness`, and `AI_BEH_VegRoot_Anomaly` feed the threshold logic for `REPORT_640_FINAL_Zero_Point_Targets`;
- `AI_BEH_MassVolume_Shadow` is renamed into `REPORT_640_Mass_Report`;
- `AI_BEH_GoldAlloy_Signal` is renamed into `REPORT_640_Pottery_Report`.

No standalone exported notebook filenames were recovered for the four AI_BEH anchor patterns themselves.

## Decision Lock

Current decisions:

- `AI_BEH_VegRoot_Anomaly` -> `internal_report_precursor_only`
- `AI_BEH_IronOxide_Hardness` -> `internal_report_precursor_only`
- `AI_BEH_GoldAlloy_Signal` -> `covered_by_report_640_downstream_only`
- `AI_BEH_MassVolume_Shadow` -> `covered_by_report_640_downstream_only`

Reasoning:

- `VegRoot_Anomaly` and `IronOxide_Hardness` are notebook-visible tensors, but the recovered notebook evidence keeps them only as in-memory precursors for the zero-point logic rather than as standalone exported files.
- `GoldAlloy_Signal` and `MassVolume_Shadow` are also notebook-visible tensors, but the recovered notebook evidence shows them being renamed into exported `REPORT_640` outputs rather than exported under their original AI_BEH names.

## REPORT_640 Coverage Relationship

`app/pipeline/stages/report_640.py` already reproduces the downstream formulas:

- `AI_BEH_VegRoot_Anomaly` behavior inside the zero-point condition
- `AI_BEH_IronOxide_Hardness` behavior inside the zero-point condition
- `AI_BEH_GoldAlloy_Signal` behavior inside the zero-point condition and the pottery report output
- `AI_BEH_MassVolume_Shadow` behavior inside the mass report output

Existing `REPORT_640` parity coverage does not automatically mean standalone notebook AI_BEH output parity. It only means the downstream exported REPORT_640 effect is already covered where the notebook exported REPORT_640 outputs instead of notebook-named AI_BEH files.

## Standalone Output Decision

At current evidence level:

- no standalone notebook export filename has been recovered for `AI_BEH_VegRoot_Anomaly`
- no standalone notebook export filename has been recovered for `AI_BEH_IronOxide_Hardness`
- no standalone notebook export filename has been recovered for `AI_BEH_GoldAlloy_Signal`
- no standalone notebook export filename has been recovered for `AI_BEH_MassVolume_Shadow`

Because of that:

- none of these patterns is currently marked `standalone_output_required`
- none of these patterns is currently marked `unresolved_requires_source_reference`

If a future frozen notebook bundle or notebook export cell shows standalone AI_BEH files for any of these patterns, that pattern should move into a future standalone parity slice.

## Metadata And Reference Implications

Frozen notebook references are still required before notebook-value parity can pass for any downstream exported artifact.

If a future standalone AI_BEH export is recovered, the later slice will still need:

- filename evidence
- dtype
- nodata or NaN policy
- CRS
- transform
- shape
- tolerance expectations

## Exposure And Interpretation Rules

These are notebook-parity and private semantic items, not clean public/core outputs by default.

No HTTP exposure is introduced here.

If a later classifier or model interpretation layer uses these patterns, interpreted outputs must use probability-only wording. This phase does not implement classifier logic.

## Remaining Unknowns

Phase 4H11 leaves these unknowns explicit:

- whether any historical notebook run ever exported standalone AI_BEH files for the four anchor patterns
- standalone export metadata, if any such files exist in a future reference bundle
- whether Phase 4Z should collapse some inventory wording now that downstream REPORT_640 coverage is explicit

## Next Step

Phase 4Z should reconcile the semantic inventory and Phase 4 coverage docs now that the per-output AI_BEH semantic branch and the anchor-pattern decision are both locked.
