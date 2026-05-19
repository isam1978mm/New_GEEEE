# Parity Exceptions

This file records intentional deviations from source-notebook output for stages marked `PARITY_CORRECTS`.

## IRON_SWIR

- Stage: `app/pipeline/stages/s2_indices.py`
- Category: `PARITY_CORRECTS`
- Reason: the notebook used the wrong denominator for `IRON_SWIR`
- Notebook bug: `(B11 - B12) / (B11 - B12)`
- Corrected app formula: `(B11 - B12) / (B11 + B12)`
- Validation rule: parity tests assert the corrected analytical result, not the buggy notebook output

## Current Status

- No other core-stage parity corrections are registered in the repo state for Goal M13.
- `PARITY_REPLACES` stages are documented through stage metadata and unit tests, not notebook parity fixtures.
