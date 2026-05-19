# Notebook Parity Suite

This directory contains notebook parity tests for the core pipeline only.

## What belongs here

- Tests for core stages that compare notebook-style processing flow or corrected analytical references.
- Small deterministic fixture-based checks.
- No experimental classifier tests.

## Category Rules

- `PARITY_REPRODUCES` tests verify notebook-equivalent behavior.
- `PARITY_CORRECTS` tests verify an intentional correction against a non-buggy reference.
- `PARITY_REPLACES` stages do not belong in this suite because they replace notebook-specific infrastructure.

## Registry

- `conftest.py` is the collection-time registry for this suite.
- Every parity test file in this directory must be listed there.
- Collection fails if a test file's declared category disagrees with the mapped stage metadata.

## Fixtures

- Reference fixture notes live under `tests/notebook_parity/fixtures/reference_run/README.md`.
- Avoid committing large binary outputs unless explicitly authorized.
