# Future Slice 02 / Phase C2 AI_BEH Extended Writer

## Scope

Phase C2 implements only the J2 source-locked `AI_BEH` extended semantic feature family. It adds local-array helpers and private run-directory NPY writer support for the three selected outputs. It is not wired into the live pipeline.

## Source Evidence

- `docs/FUTURE_SLICE_J2_TESLA_SUBSTEP_SOURCE_LOCK.md`
- `docs/AI_BEH_EXTENDED_PARITY_CONTRACT.md`
- `app/pipeline/parity/ai_beh_extended_recovery.py`

## Selected Outputs

| Output | Formula |
| --- | --- |
| `AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif` | `B12 / B11` |
| `AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif` | `B4 / B2` |
| `AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif` | `(B8 + B4) / (B11 + 0.001)` |

Required input arrays are local 2D arrays for `B2`, `B4`, `B8`, `B11`, and `B12`.

## Array Policy

- Shape policy: every required input must be a 2D array and all required inputs must share one shape.
- Dtype policy: computations coerce inputs to `float64` internally and return `float32` arrays.
- Denominator policy: division denominators with absolute value less than or equal to the configured epsilon become `NaN`.
- ERT denominator policy: the denominator is evaluated as `B11 + 0.001` before the unsafe-denominator check.
- Input mutation policy: computation helpers do not mutate caller-provided arrays.

## Boundary

Phase C2 is private and parity-only. Optional NPY output writing stays under a caller-provided run directory and is classified as `LOCAL_SENSITIVE` with:

- `filesystem_only=true`
- `http_servable=false`
- `frontend_visible=false`
- `downloadable_via_api=false`

Phase C2 does not:

- call Earth Engine
- start backend runs
- wire the writer into the live pipeline
- change existing raster or stage math
- change API, frontend, database, or artifact-serving behavior
- expose outputs through public surfaces
- create map, coordinate, classifier, model, weight, dataset, label, or chip artifacts
- implement Phase D, E, G, H, I, or J follow-up work

## Parity Status

Runtime output presence remains separate from notebook-value parity. Phase C2 does not claim notebook-value parity. Frozen notebook references and a later Phase E3 comparator are required before notebook-value parity can pass for these outputs.

## Later Work

Phase E3 should add a comparator for Phase C semantic feature outputs, including the Phase C1 relation family and this Phase C2 extended family, using frozen notebook references and documented tolerances.
