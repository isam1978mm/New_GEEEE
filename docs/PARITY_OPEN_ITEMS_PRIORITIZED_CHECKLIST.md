# Parity Open Items — Prioritized Checklist

## Purpose

This is the operational checklist for `notebooks/new.ipynb` parity work. It is separate from the private/local Paid Imagery Export Package audit track.

Full roadmap history remains in:

```text
docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md
```

Expected output scope is maintained in:

```text
docs/parity_expected_outputs_sourcelocked.json
```

## Scope Rule

- `notebooks/new.ipynb` is the in-scope notebook for this parity checklist.
- The Paid Imagery Export Package is active app functionality, but old/external V6 notebook parity is not claimed here.
- Internal `V6` / `v6_*` names are legacy implementation names for the export-package path unless a document explicitly says otherwise.
- Real value parity requires the frozen D1C reference plus D2 validation.
- Same-source comparisons prove mapping/tooling only.
- Real app parity requires matching app-generated output for the D1C grid.
- Source-recovery items are documented notebook outputs but are not fabricated or regenerated from mismatched pipelines.
- Preview/export work is not parity-blocking unless future work changes artifact names, filtering, safety classes, generated previews, or export packages.

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

These are blocked, not failed. Same-source comparisons prove verifier mapping/tooling only; they are not real app parity. Real app-vs-reference parity requires app-generated output on the frozen D1C grid/source contract, D2-valid reference bundle validation, and then the existing verifier/CLI.

Unblock condition for every blocked item below:

1. produce the matching app-generated output without fabricating or copying reference artifacts;
2. prove the same D1C grid/source contract: same CRS, scale, width/height, transform/origin, source contract, band count, shape convention, dtype, and output semantics;
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

Source-recovery items have notebook/source evidence but are not verified runtime parity targets yet. Do not fabricate outputs, do not regenerate from a mismatched notebook or pipeline version, and do not treat renamed/app-native equivalents as notebook parity.

| Item | Status | Reason | Needed to unblock |
| --- | --- | --- | --- |
| D1D object-table outputs | source-recovery | `AI_OBJECT_TABLES/objects_index.csv` and `AI_OBJECT_TABLES/clusters_summary.csv` are source-locked, but D1C did not export the required same-run object-table family and related source tensors consistently. | Corrected same-run source recovery/export, then D2-gated comparison. |
| AI_READY remaining support families | source-recovery | Broader `AI_READY_*` / `AI_BEH_*` support families have evidence in the semantic recovery contracts but are outside the six AIREADY-1 top-level secret-layer outputs. | Per-family recovery/build task with source evidence, output paths, metadata, and frozen references. |
| SAR/S1 support, intermediate, and QA/provenance outputs | source-recovery | ASC/DESC filtered layers, `S1_FILTERED_LAYERS_STACK_640.npy`, pre-RTC/intermediate/QA outputs either lack matching app writer paths or have app-native/renamed equivalents only. | Recover exact notebook source contract, selected source IDs/metadata, writer paths, and references before verification. |
| PAN/optical image components and stack | source-recovery | D1C has source-locked PAN components and `PAN_LAYERS_STACK_640.npy`; current app has no matching PAN writer and existing optical outputs are not equivalents. | Add explicit source-driven PAN writer/run, then run PAN component and stack verifiers. |

## Paid Imagery Export Package Clarification

The app-side Paid Imagery Export Package remains active and in scope for the private/local app audit. It is not parked, deprecated, or removed.

The separate old/external V6 notebook parity track remains unresolved until an operator supplies a verified external V6 notebook/export source. The active app package records provenance and does not claim frozen external V6 notebook parity.

## Completed Foundation

- [x] A2 — Safe Run File Inspector + Run Diagnostics CLI.
- [x] A3 — DEM curvature runtime outputs.
- [x] A4 — Public safety verification harness.
- [x] A5 — Stale running-run cleanup verification.
- [x] A6 — Disk-usage scan verification on DONE/FAILED completion.

## Cross-Reference

- `docs/AUDIT_FIX_PLAN_STUB.md`
- `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md`
- `docs/V6_PACKAGE_GENERATION_SCOPE.md`
- `docs/SAFE_NOTEBOOK_CAPABILITY_PHASES.md`
- `docs/parity_expected_outputs_sourcelocked.json`
- `AGENTS.md`
