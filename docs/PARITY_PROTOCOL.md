# Parity Protocol

This document defines how notebook parity is handled for the core GEE screening pipeline in v1.

## Scope

- Notebook parity applies only to the defensible core stages under `app/pipeline/stages/`.
- The experimental classifier is excluded from notebook parity. It uses separate contract tests.
- Parity tests live under `tests/notebook_parity/`.

## Reference ROI

- Reference fixtures must use a deliberately uninteresting ROI.
- Do not commit production, sensitive, or operational ROIs.
- The fixture ROI is for regression detection only, not for scientific validation.

## Capture Workflow

1. Run the source notebook on the reference ROI.
2. Export only the stage outputs needed for parity comparison.
3. Normalize unstable metadata before committing any fixture-derived reference.
4. Record the capture date, notebook revision, and any intentional exception.
5. Store capture notes in `tests/notebook_parity/fixtures/reference_run/README.md`.

## Fixture Discipline

- Prefer small text fixtures, small numeric arrays, and deterministic synthetic inputs.
- Do not commit large binary artifacts unless an ADR explicitly authorizes them.
- If a large artifact is required later, document why a smaller fixture is insufficient.
- Keep fixture content scrubbed of production coordinates and unrelated notebook debris.

## Parity Categories

- `PARITY_REPRODUCES`: the app stage is intended to reproduce notebook behavior.
- `PARITY_CORRECTS`: the app stage intentionally differs from the notebook to correct a known bug.
- `PARITY_REPLACES`: the notebook behavior is replaced by app infrastructure and does not use notebook parity fixtures.

## Test Collection Rules

- Every notebook parity test file must be registered in `tests/notebook_parity/conftest.py`.
- The registry maps each parity test file to its stage class and expected parity category.
- Pytest collection fails if a registered parity test file disagrees with the stage's declared `parity_category`.
- Unregistered parity test files in `tests/notebook_parity/` also fail collection.

## Current Exception Set

- `IRON_SWIR` is the only current `PARITY_CORRECTS` exception.
- See `docs/PARITY_EXCEPTIONS.md` for the correction record.

End of PRD v0.5. compatible parity protocol notes.
