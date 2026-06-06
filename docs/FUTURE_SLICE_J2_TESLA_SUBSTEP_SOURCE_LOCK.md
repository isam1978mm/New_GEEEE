# Future Slice J2 Tesla Substep Source Lock

J2 is source-lock, decision, and implementation-readiness only. It does not
implement Phase C2, generate outputs, call Earth Engine, change raster or math
logic, expose anything through API or frontend, or change artifact-serving
policy.

The full Tesla-style flow remains blocked as one monolithic runtime path. Phase
C2 implementation requires a separate user-approved slice.

## Selected Substep

J2 source-locks exactly one coherent family:

```text
AI_BEH extended semantic rasters
```

Selected outputs:

- `AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif`
- `AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif`
- `AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif`

## Source Evidence

Source contracts:

- `docs/AI_BEH_EXTENDED_PARITY_CONTRACT.md`
- `docs/SEMANTIC_RASTER_RECOVERY_CONTRACT.md`
- `docs/PHASE_10_CLEAN_VS_PARITY_DECISION.md`
- `docs/SPECIAL_TRACK_J_TESLA_FLOW_DECOMPOSITION.md`

Source recovery module:

- `app/pipeline/parity/ai_beh_extended_recovery.py`

The Phase 4H6 contract records notebook lines around `24193-24205` for the exact
extended AI_BEH builder and lines around `35472-35475` for later file-table
visibility. That contract records all three outputs as standalone notebook
outputs and downstream stack components.

## Formulas And Inputs

Required input arrays:

- `B2`
- `B4`
- `B8`
- `B11`
- `B12`

Locked formulas:

- `AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif = B12 / B11`
- `AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif = B4 / B2`
- `AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif = (B8 + B4) / (B11 + 0.001)`

These formulas are local-array-testable. Unit tests for a later Phase C2 slice
do not require Earth Engine.

## Metadata Policy

A future Phase C2 implementation must accept same-shaped 2D GRID-aligned arrays.

Expected dtype policy:

- compute `float32` arrays unless frozen references require a narrower export
  policy

Expected nodata or NaN policy:

- unsafe ratio denominators become `NaN` in local array tests
- final TIFF nodata behavior remains locked by frozen references

GRID metadata policy:

- preserve caller-supplied GRID metadata
- later compare CRS, transform, width, height, band count, dtype, nodata, and
  numeric values against frozen references

## Privacy Boundary

The selected outputs are private notebook-parity outputs.

- clean app allowed: `false`
- private parity allowed: `true`
- HTTP servable: `false`
- frontend visible: `false`
- downloadable through API: `false`
- Earth Engine required for tests: `false`

No public API, frontend, artifact-serving, or download exposure is allowed in J2
or the later Phase C2 writer slice unless a separate user-approved policy change
is opened.

## Implementation Readiness

The family is ready for a later Phase C2 implementation slice because:

- exact formula evidence exists in the Phase 4H6 contract
- source recovery module already records the selected outputs
- formulas are simple local-array expressions
- tests can use tiny local arrays
- outputs remain private and notebook-parity only

Implementation blockers that remain:

- Phase C2 implementation is not part of J2
- frozen notebook references are needed before notebook-value parity can pass
- final exported dtype, nodata, CRS, transform, width, height, and tolerance are
  reference-locked
- no public serving or frontend exposure is approved

## Required Phase C2 Tests

A later Phase C2 implementation must test:

- formula values for all three selected outputs
- safe denominator and NaN policy
- same-shape 2D input validation
- required band validation
- private run-directory path safety
- no Earth Engine import or call
- no API, frontend, or artifact-serving exposure
- `notebook_value_parity_verified=false` until frozen reference comparison passes

## Report Helper

The source-lock helper is:

```text
app/pipeline/parity/tesla_substep_source_lock.py
```

It writes a private JSON report:

```text
data/runs/<run_id>/manifests/future_slice_j2_source_lock_report.json
```

The report is metadata only. It does not create raster, NPY, GeoJSON, KMZ, KML,
HTML, image, coordinate, classifier, model, weight, dataset, label, chip, or
training artifacts.

## Recommended Next Slice

Recommended next slice:

```text
Phase C2 separate implementation slice
```

Phase C2 should implement only the selected AI_BEH extended semantic raster
family as a private notebook-parity writer using local arrays and tiny fixtures.
