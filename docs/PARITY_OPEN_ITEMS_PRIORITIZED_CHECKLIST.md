# Parity Open Items — Prioritized Checklist

## Purpose

This file is the current remaining-job checklist after the Phase 0-10 parity roadmap.

The full roadmap contract history remains in:

- `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md`

## Scope Rule

- `notebooks/new.ipynb` parity is the main app path.
- V6 is parked as a separate external-notebook/package track.
- Reference comparison work requires D1 first.

## Correct Remaining-Job Sequence

### 1. Reconcile checklist docs — DONE

Reconciled files:

- `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md`
- `docs/PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md`
- `docs/V6_PACKAGE_GENERATION_SCOPE.md`

Result:

- `notebooks/new.ipynb` parity = main app path.
- V6 = parked separate external track.
- D1 reference freeze is the gate before value comparisons.

### 2. D1 — Freeze `notebooks/new.ipynb` reference bundle

This is the gate before downstream verification.

- [ ] Run/freeze a known-good `notebooks/new.ipynb` output bundle outside Git.
- [ ] Record notebook version, repo commit, run date, and notes.
- [ ] Record output file list.
- [ ] Record SHA256 and file sizes.

Rule:

- Nothing below should claim notebook-value parity until D1 exists.

### 3. Tier 1 — DEM curvature reference comparison

- [ ] `curv_laplacian_640.tif`
- [ ] `curv_plan_640.tif`
- [ ] `curv_profile_640.tif`

### 4. Tier 1 — Report 640 verification

- [ ] Output presence.
- [ ] Raster/file presence.
- [ ] Shape/name/value parity where applicable.

### 5. Tier 1 — Internal raster / AI-ready verification

- [ ] Internal raster-family parity.
- [ ] AI-ready fraction parity.
- [ ] AI-ready neutral feature-family parity.
- [ ] AI-ready neutral family parity.

### 6. Tier 2 — SAR/S1 recover + build, then verify

- [ ] Recover required S1 ASC/DESC source inputs.
- [ ] Confirm notebook cell/source logic.
- [ ] Build missing app writer/output path.
- [ ] Verify against frozen D1 reference.

### 7. Tier 2 — PAN recover + build, then verify

- [ ] Recover optical/PAN source requirement.
- [ ] Confirm notebook source logic.
- [ ] Build missing app writer/output path.
- [ ] Verify against frozen D1 reference.

### 8. Special Track G — Preview/export decision

- [ ] Decide preview/export behavior.
- [ ] Keep this separate from parity-closing work.

### 9. V6 — parked separate project

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
- `AGENTS.md`

(End of PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md.)
