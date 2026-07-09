# Parity Exceptions

This file records intentional deviations from source-notebook output for stages marked `PARITY_CORRECTS`.

## IRON_SWIR

- Stage: `app/pipeline/stages/s2_indices.py`
- Category: `PARITY_CORRECTS`
- Reason: provenance reconciliation is resolved by H4.5 Option A; the app formula is canonical for v1 production parity
- Corrected app formula: `(B11 - B12) / (B11 + B12)`
- Provenance note: see `docs/IRON_SWIR_PROVENANCE.md`
- Validation rule: H5 must use Option A from `docs/IRON_SWIR_PROVENANCE.md`, compare against the corrected analytical/app reference, and must not silently compare against the checked-in notebook sign-flipped raster

## Audit 2026-07 Planned Corrections

These records are added before implementation so the audit fixes have an explicit parity trail. Each item must be linked to focused tests when implemented.

### Secret thermal inertia source/unit correction

- Stage: `app/pipeline/stages/secret_layers.py`
- Related stage: `app/pipeline/stages/thermal.py`
- Category: `PARITY_CORRECTS`
- Audit checklist item: `1.1`, `1.2`, `1.3`
- Problem: local fallback and EE-style path can compute the same artifact from different thermal source/unit bases.
- Required correction: align local and EE-style thermal inertia to one declared source/unit basis and record source/unit metadata.
- Validation rule: focused fixture tests must prove local and EE-style thermal inertia agree for the declared basis.

### Fusion target mask DN/reflectance correction

- Stage: `app/pipeline/stages/s2_indices.py`
- Category: `PARITY_CORRECTS`
- Audit checklist item: `1.4`, `1.5`, `1.6`, `1.7`
- Problem: production fusion target logic can apply reflectance-style thresholds to raw S2 DN values while deterministic tests use scaled reflectance-like values.
- Required correction: make production and deterministic paths use the same scaling semantics and cloud-filter policy.
- Validation rule: focused fixture tests must prove the production formula and deterministic twin agree on the same scaled inputs.

### Empty/all-nodata source blocking

- Stages: `app/pipeline/stages/s2_indices.py`, `app/pipeline/stages/thermal.py`, `app/pipeline/stages/dem.py`
- Category: `PARITY_CORRECTS`
- Audit checklist item: `1.8`, `1.9`, `1.10`, `1.11`
- Problem: missing or empty source data can produce all-nodata outputs that still look successful.
- Required correction: add source collection size gates and valid-fraction checks that fail the stage instead of reporting successful output.
- Validation rule: focused tests must prove empty or all-nodata inputs raise `StageError` or equivalent stage failure.

## Current Status

- IRON_SWIR is the only completed registered correction before the 2026-07 audit plan.
- Audit 2026-07 corrections above are planned and must be marked complete only after code and tests land.
- `PARITY_REPLACES` stages are documented through stage metadata and unit tests, not notebook parity fixtures.
