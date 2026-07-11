# Local Private App — Safe Repair Order

This document is the read-first repair order for the current audit.

## Non-negotiable framing

This project is a **local/private app**, not a public product.

The audit must not treat public release, public exposure, or public sharing as the main risk unless the owner explicitly changes that goal.

The real audit question is:

> Can the local app give the operator wrong, overconfident, misaligned, corrupted, or poorly-labeled results inside the private workflow?

Repo docs are not a bible. They are project state at a point in time and can be changed by the owner. The code, tests, and UI should follow the current owner-approved intent.

## Current accepted issue status

1. **S2 nodata / dtype issue — accepted.**
   - Sentinel-2 index and mask metadata must be corrected before downstream analysis.

2. **Alignment / zero-shift QA issue — accepted.**
   - QA must verify real GeoTIFF metadata, not only sidecar metadata.

3. **Classifier framing — corrected.**
   - The classifier is now a **main/core feature**, not an experimental feature to remove.
   - The repair is to harden it as core, with stronger input contracts, quality gates, tests, and careful confidence language.

4. **Paid Imagery Export framing — corrected.**
   - There is no product-level "V6" anymore; old V6 naming is legacy naming that still exists in code/files/docs.
   - Audits must verify the **current Paid Imagery Export wiring**, not assume old fallback V6 paths are the live product path.
   - Legacy V6/fallback helpers should be renamed, quarantined, or clearly marked if they are not the current path.

5. **Package provenance / ZIP readiness issue — accepted.**
   - Provenance and integrity must survive generation, loading, review, and UI display.

## Safest repair order

### 1. Fix S2 nodata and mask dtype first

Fix the raw data entering the stack before touching classifier or export logic.

Required repairs:

- S2 index sidecars must not declare real `0.0` values as nodata.
- Mask TIFF actual dtype and metadata dtype must match.
- Hypercube assembly must not blindly trust sidecar nodata when actual GeoTIFF metadata disagrees.

Why first:

If S2 values are corrupted, every downstream product can look clean while being built on damaged optical data.

Impact if skipped:

Classifier, anomaly maps, run summaries, and export packages may be based on corrupted layers.

### 2. Fix real GeoTIFF alignment and zero-shift QA

After values are safe, verify that all raster layers truly align to the same grid.

Required repairs:

- Read CRS, transform, width, height, dtype, and nodata from the real GeoTIFF.
- Treat sidecars as secondary metadata, not the source of truth.
- Do not silently skip TIFFs without sidecars.
- Ensure the hypercube is covered by an alignment check.

Why second:

Clean values are still unreliable if the layers do not refer to the same ground pixels.

Impact if skipped:

The app may compare data from different ground locations and still report a clean result.

### 3. Add a server-generated Run Quality Summary gate

Create one server-side truth layer before hardening classifier and export behavior.

Required repairs:

- Emit one run quality status: `PASS`, `WARNING`, `BLOCKED`, or `UNKNOWN`.
- Include S2 coverage, nodata checks, alignment status, scene counts, source dates, missing outputs, and blocking reasons.
- Make the UI read this summary instead of using file presence as proof of quality.

Why third:

This gives the app and operator a single answer to: "Is this run usable?"

Impact if skipped:

The app can keep showing green-looking rows while serious upstream checks are failing or unknown.

### 4. Harden the classifier as a core stage

Do not remove the classifier. Treat it as a first-class project feature.

Required repairs:

- Rename/framing must not imply experimental status if the owner has promoted it to core.
- Define the classifier input contract: required bands, masks, coverage, valid fractions, and alignment state.
- Block or downgrade classifier output when Run Quality Summary is `BLOCKED` or `UNKNOWN`.
- Use evidence-based confidence language unless validation supports stronger wording.
- Add tests for missing bands, low coverage, bad nodata, misalignment, and unstable score behavior.

Why fourth:

The classifier depends on the S2 and alignment fixes. Hardening it before fixing upstream data would protect the wrong layer.

Impact if skipped:

Classifier output may look official even when the underlying inputs are weak, damaged, or not aligned.

### 5. Audit the current Paid Imagery Export wiring

Only after upstream data and classifier gates are stable, verify the actual export path.

Required repairs:

- Identify the live UI/API/backend path used by the current Paid Imagery Export.
- Separate the current path from legacy V6/fallback code.
- Rename, quarantine, or clearly mark old V6 helpers if they are not current product logic.
- Verify that the current export uses real scored candidates, real grid cells or approved geometry, and preserved provenance.
- Remove or soften labels like "best zones" unless the quality gate supports them.

Why fifth:

Paid Imagery Export is downstream. It should consume validated candidates, not hide upstream quality problems.

Impact if skipped:

Audits and fixes may keep chasing old V6 fallback code instead of the current Paid Imagery Export path.

### 6. Strengthen package provenance and ZIP readiness

Protect final package readiness after the current export path is known.

Required repairs:

- Preserve score basis, geometry basis, fallback flags, placeholder flags, and parity status through generation, load, review, and UI display.
- Reopen the ZIP during review.
- Recompute ZIP hash and compare it to the validation report.
- Block readiness on run ID mismatch, corrupt ZIP, hash mismatch, fallback/placeholder provenance where not allowed, or missing provenance.

Why sixth:

The package is the final handoff artifact. It should not appear ready if it is stale, mismatched, corrupted, or based on weak assumptions.

Impact if skipped:

A package can look ready even when its integrity or provenance is not trustworthy.

### 7. Make parity, integration, and frontend checks strict

After behavior is corrected, lock it down with tests.

Required repairs:

- Source-locked numeric parity profile must fail when references are missing.
- It must fail when expected app artifacts are missing.
- Deterministic full-run integration must end with `done`, not `failed`.
- Frontend `tsc --noEmit` should be required.
- Tests must cover the corrected Paid Imagery Export path, not only legacy V6 names.

Why last:

Tests should lock correct behavior after the behavior is fixed.

Impact if skipped:

The same failures can return later while the standard test suite still appears green.

## Final priority list

1. S2 nodata / dtype.
2. Real GeoTIFF alignment / zero-shift QA.
3. Server-generated Run Quality Summary.
4. Core classifier hardening.
5. Current Paid Imagery Export wiring audit.
6. Package provenance and ZIP readiness.
7. Strict parity / integration / frontend tests.

## Core rule

Fix upstream truth first, then classifier, then export/package, then tests.
