# Parity Exceptions

This file records intentional deviations from source-notebook output for stages marked `PARITY_CORRECTS`.

## IRON_SWIR

- Stage: `app/pipeline/stages/s2_indices.py`
- Category: `PARITY_CORRECTS`
- Reason: provenance reconciliation is resolved by H4.5 Option A; the app formula is canonical for v1 production parity
- Corrected app formula: `(B11 - B12) / (B11 + B12)`
- Provenance note: see `docs/IRON_SWIR_PROVENANCE.md`
- Validation rule: H5 must use Option A from `docs/IRON_SWIR_PROVENANCE.md`, compare against the corrected analytical/app reference, and must not silently compare against the checked-in notebook sign-flipped raster

## Current Status

- No other core-stage parity corrections are registered in the repo state for Goal M13.
- `PARITY_REPLACES` stages are documented through stage metadata and unit tests, not notebook parity fixtures.
