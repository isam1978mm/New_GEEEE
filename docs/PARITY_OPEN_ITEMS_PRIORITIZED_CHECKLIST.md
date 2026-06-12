# Parity Open Items — Prioritized Checklist

## Purpose

This is the current operational checklist for `notebooks/new.ipynb` parity work.

Full roadmap history remains in `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md`.
Expected output scope is maintained in `docs/parity_expected_outputs_sourcelocked.json`.

## Scope Rule

- `notebooks/new.ipynb` is the in-scope notebook.
- V6 remains parked as a separate external-notebook/package track.
- Real value parity requires the frozen D1C reference plus D2 validation.
- Same-source comparisons prove mapping/tooling only.
- Real app parity requires matching app-generated output for the D1C grid.
- Source-recovery items are documented notebook outputs but are not fabricated or regenerated from mismatched pipelines.
- Preview/export is not parity-blocking unless future work changes artifact names, filtering, safety classes, generated previews, or export packages.

## Closed Work

- [x] Checklist docs reconciled.
- [x] D1/D1C frozen reference created outside Git.
- [x] D2 frozen bundle validator implemented.
- [x] D1A bundle-wide scope audit implemented.
- [x] D1B source-locked baseline created.
- [x] D1D object-table outputs documented as source-recovery; D1A required missing count is zero.
- [x] D3 DEM curvature parity accepted end-to-end.
- [x] R1 REPORT_640 verifier/CLI tooling and same-source mapping check completed.
- [x] AIREADY-1 verifier/CLI tooling and same-source mapping check completed.
- [x] HYPER-1A RES_2p5M verifier/CLI tooling and same-source mapping check completed.
- [x] HYPER-1B core tensor/NPY verifier/CLI tooling and same-source mapping check completed.
- [x] INT-1 internal raster verifier/CLI tooling and same-source mapping check completed.
- [x] S1-1 family classification and same-source verification completed.
- [x] PAN-1 image-family classification and same-source verification completed.
- [x] G-1 preview/export decision closed as not parity-blocking.

## Blocked Real App Parity Items

These are blocked, not failed. Same-source comparisons prove verifier mapping/tooling only; they
are not real app parity. Real app-vs-reference parity requires app-generated output on the frozen
D1C grid/source contract, D2-valid reference bundle validation, and then the existing verifier/CLI.

Unblock condition for every blocked item below:

1. produce the matching app-generated output without fabricating or copying reference artifacts;
2. prove the same D1C grid/source contract: same CRS, scale, width/height, transform/origin,
   source contract, band count, shape convention, dtype, and output semantics;
3. run the existing D2-gated verifier/CLI against the frozen D1C reference bundle.

| Item | Status | Blocked reason | Existing verification path |
| --- | --- | --- | --- |
| R1 REPORT_640 real app-vs-reference parity | blocked | Needs matching D1C-grid app `REPORT_640_*` rasters produced by the app run. | `REPORT_640` verifier/CLI. |
| AIREADY real app-vs-reference parity | blocked | Needs matching D1C-grid app six top-level `AI_READY_640_Secret_*` rasters. | Secret-layer verifier/CLI. |
| HYPER-1A RES_2p5M real app-vs-reference parity | blocked | Needs matching D1C-grid app `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.*` outputs. | RES_2p5M verifier/CLI. |
| HYPER-1B core tensor/NPY real app-vs-reference parity | blocked | Needs matching D1C-grid app core tensor and radar-stack NPY outputs with comparable grid/source metadata. | Tensor verifier/CLI. |
| INT-1 internal raster real app-vs-reference parity | blocked | Needs matching D1C-grid app internal raster outputs for the closed INT-1 mapping set. | Internal raster verifier/recovery tooling. |
| S1-1 core-band real app-vs-reference parity | blocked | Needs matching D1C-grid app SAR/S1 core-band outputs with the same grid and source contract, not merely same shape/EPSG. | SAR core-band same-source support checks and existing SAR parity tooling. |

## Source-Recovery Items

Source-recovery items have notebook/source evidence but are not verified runtime parity targets yet.
Do not fabricate outputs, do not regenerate from a mismatched notebook or pipeline version, and do
not treat renamed/app-native equivalents as notebook parity. Each item needs an explicit
recovery/build task before parity verification.

| Item | Status | Reason | Needed to unblock |
| --- | --- | --- | --- |
| D1D object-table outputs | source-recovery | `AI_OBJECT_TABLES/objects_index.csv` and `AI_OBJECT_TABLES/clusters_summary.csv` are source-locked, but D1C did not export the required same-run object-table family and related source tensors consistently. | Corrected same-run source recovery/export, then D2-gated comparison. |
| AI_READY remaining support families | source-recovery | Broader `AI_READY_*` / `AI_BEH_*` support families have evidence in the semantic recovery contracts but are outside the six AIREADY-1 top-level secret-layer outputs. | Per-family recovery/build task with source evidence, output paths, metadata, and frozen references. |
| SAR/S1 support, intermediate, and QA/provenance outputs | source-recovery | ASC/DESC filtered layers, `S1_FILTERED_LAYERS_STACK_640.npy`, pre-RTC/intermediate/QA outputs either lack matching app writer paths or have app-native/renamed equivalents only. | Recover exact notebook source contract, selected source IDs/metadata, writer paths, and references before verification. |
| PAN/optical image components and stack | source-recovery | D1C has source-locked PAN components and `PAN_LAYERS_STACK_640.npy`; current app has no matching PAN writer and existing optical outputs are not equivalents. | Add explicit source-driven PAN writer/run, then run PAN component and stack verifiers. |

## Current Remaining-Job Sequence

### 1. FINAL-1 — Final parity status / remaining blocked-run list — NEXT

- [x] Query Graphify before direct source-file reading.
- [x] Produce final closed-work list.
- [x] Produce final blocked real app-vs-reference list.
- [x] Produce final source-recovery list.
- [x] Confirm V6 remains parked.
- [x] Do not modify runtime code or generated artifacts.

FINAL-1 status: closed as a docs-only parity status update. The local Graphify CLI was invoked
first, but `graphify-out/graph.json` was absent, so no graph traversal was available. The final
status was reconciled from the active parity checklist, source-locked baseline, V6 scope document,
and the relevant verifier/recovery contracts. No runtime code, formulas, writers, verifiers,
tolerances, source-locked baseline values, notebook files, reference bundles, generated artifacts,
frontend build files, cache files, or Graphify outputs were changed.

### 2. V6 — parked separate project

- [ ] Later: provide external V6 notebook/export.
- [ ] Later: freeze V6 package.
- [ ] Later: source-lock V6 formulas.
- [ ] Later: decide whether app integrates V6 workflow.

V6 status: parked. It is a separate external-notebook/package track and does not block
`notebooks/new.ipynb` parity closure. V6 can restart only after the operator supplies the separate
originating V6 notebook or a real frozen V6 package.

## Completed Foundation

- [x] A2 — Safe Run File Inspector + Run Diagnostics CLI.
- [x] A3 — DEM curvature runtime outputs.
- [x] A4 — Public safety verification harness.
- [x] A5 — Stale running-run cleanup verification.
- [x] A6 — Disk-usage scan verification on DONE/FAILED completion.

## Cross-Reference

- `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md`
- `docs/V6_PACKAGE_GENERATION_SCOPE.md`
- `docs/SAFE_NOTEBOOK_CAPABILITY_PHASES.md`
- `docs/parity_expected_outputs_sourcelocked.json`
- `AGENTS.md`

(End of PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md.)
