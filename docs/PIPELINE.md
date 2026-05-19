# Pipeline

This document describes the v1 core pipeline and the boundary around the experimental module.

## Core pipeline order

The defensible core run is built from these stages:

1. `grid`
2. `dem`
3. `zero_shift`
4. `sar_rtc`
5. `s2_indices`
6. `dem_derivatives`
7. `thermal`
8. `hypercube`
9. `pca_anomaly`
10. `object_extract`
11. `alignment_qa`

Each stage declares parity metadata and emits classified artifacts.

## Storage model

- Run data lives under `./data/runs/<run_id>/`.
- The authoritative GRID manifest is internal.
- Stage manifests are written as `LOCAL_SENSITIVE`.
- Public-safe outputs, such as `objects_index.csv` and `alignment_qa.json`, avoid coordinates and use row or column offsets instead.

## Artifact classes

- `LOCAL_SENSITIVE`: internal rasters, arrays, manifests, and other sensitive outputs.
- `REDACTED_PUBLIC`: public-safe summaries and tables.
- `PREVIEW_ONLY`: reserved preview class where needed by the guarded artifact policy.
- `FILESYSTEM_ONLY`: never served; used for experimental artifacts and other local-only outputs.

## Orchestration

The core orchestrator:

- validates stage parity metadata
- records run status transitions
- records emitted artifacts with a non-null artifact class
- writes safe stage manifests on success and failure
- never imports or invokes `stages_experimental`

## Experimental module boundary

The experimental classifier is not part of the core orchestrator. It is a local post-processing step over a completed core run and has contract tests rather than notebook parity tests.
