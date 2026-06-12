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

## Blocked Real App Parity Items

These are blocked, not failed. Each needs a matching app-generated output for the D1C grid.

- [ ] R1 REPORT_640 real app-vs-reference parity.
- [ ] AIREADY real app-vs-reference parity.
- [ ] HYPER-1A RES_2p5M real app-vs-reference parity.
- [ ] HYPER-1B core tensor/NPY real app-vs-reference parity.
- [ ] INT-1 internal raster real app-vs-reference parity.
- [ ] S1-1 core-band real app-vs-reference parity.

## Source-Recovery Items

- [ ] AI_READY remaining support families.
- [ ] Object-table outputs documented by D1D.
- [ ] S1-1 support stacks, intermediate layers, and QA/provenance outputs where the app lacks matching writer paths or has renamed equivalents only.

## Current Remaining-Job Sequence

### 1. Tier 2 — PAN/optical recover + build, then verify — NEXT

- [ ] Query Graphify before direct source-file reading.
- [ ] Confirm notebook source logic.
- [ ] Classify outputs as reproducible, source-recovery, blocked-needs-app-run, or out of current notebook scope.
- [ ] Build missing app writer/output path where required.
- [ ] Verify against frozen D1C reference when a faithful source path exists.

### 2. Special Track G — Preview/export decision

- [ ] Decide preview/export behavior.
- [ ] Keep this separate from parity-closing work.

### 3. V6 — parked separate project

- [ ] Later: provide external V6 notebook/export.
- [ ] Later: freeze V6 package.
- [ ] Later: source-lock V6 formulas.
- [ ] Later: decide whether app integrates V6 workflow.

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
