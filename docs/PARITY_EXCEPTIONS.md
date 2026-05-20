# Parity Exceptions

This file records intentional deviations from source-notebook output for stages marked `PARITY_CORRECTS`.

## IRON_SWIR

- Stage: `app/pipeline/stages/s2_indices.py`
- Category: `PARITY_CORRECTS`
- Reason: parity provenance is under reconciliation; current app formula keeps the accepted corrected denominator while notebook sign/source evidence is being resolved
- Corrected app formula: `(B11 - B12) / (B11 + B12)`
- Provenance note: see `docs/IRON_SWIR_PROVENANCE.md`
- Validation rule: H5 must use the accepted provenance decision from `docs/IRON_SWIR_PROVENANCE.md`; if unresolved, H5 must fail or skip with a clear reason

## Current Status

- No other core-stage parity corrections are registered in the repo state for Goal M13.
- `PARITY_REPLACES` stages are documented through stage metadata and unit tests, not notebook parity fixtures.
