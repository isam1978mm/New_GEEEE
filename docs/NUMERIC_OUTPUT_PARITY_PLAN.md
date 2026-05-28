# Numeric Output Parity Plan

## Purpose

This document defines the Phase 5 numeric parity plan at a high level.

It is planning only.

It does not change code, math, tolerances, runtime behavior, or notebook behavior.

## What Numeric Parity Means

Numeric parity means comparing implemented notebook-compatible app outputs against an agreed reference and checking whether the numeric content matches under already accepted parity rules.

Phase 5 should treat numeric parity as evidence gathering, not as a place to change formulas or thresholds.

Numeric parity must stay downstream of:

- output inventory contract checks
- metadata and schema contract checks
- canonical path and naming checks
- not-implemented output classification

If those prerequisites fail, the result should be reported as not ready or config-required, not as a numeric mismatch.

## Phase 5D: Internal Alias-Vs-Source Checks

Phase 5D covers local deterministic checks where a notebook-compatible output is compared to its existing app source equivalent.

Examples include:

- notebook-compatible DEM aliases vs existing DEM outputs
- notebook-compatible SAR GeoTIFF aliases vs existing SAR GeoTIFF outputs
- notebook-compatible SAR NPY aliases vs existing SAR NPY outputs
- notebook-compatible stack aliases vs existing stack outputs

Goal:

- prove the notebook-compatible app aliases are numerically faithful to already accepted app outputs

Rules:

- local only
- deterministic
- no notebook reference bundle required
- no live Earth Engine

## Phase 5E: App-Vs-Notebook Reference Checks

Phase 5E covers app output vs frozen notebook reference comparisons for the canonical notebook-grid run.

Goal:

- prove that implemented notebook-compatible app outputs match the frozen notebook reference set for the same canonical run

Rules:

- requires the operator-supplied notebook reference bundle
- requires the matching app run directory for the same notebook-grid validation case
- must not use arbitrary fresh runs as proof
- must not run live Earth Engine

If the reference bundle or matching app run is missing, the result should be config-required.

If the run exists but the comparison fails, the report should distinguish:

- missing files
- metadata or grid mismatch
- dtype mismatch
- numeric mismatch

## Phase 5E Configuration Requirements

Phase 5E requires two local operator-supplied paths:

- `NOTEBOOK_REFERENCE_BUNDLE_DIR` = the frozen notebook reference bundle
- `APP_NOTEBOOK_OUTPUT_RUN_DIR` = the matching app output directory for the same notebook-grid validation case

Rules:

- both values are local/operator configuration only
- do not commit local absolute paths
- do not commit reference bundles
- do not use arbitrary fresh production-grid UI runs for notebook reference parity
- if either path is missing, Phase 5E tests should skip or xfail as config-required

`APP_NOTEBOOK_OUTPUT_RUN_DIR` must be configured locally and must not be committed.

## Current Phase 5E Status

The current Phase 5E reference-parity classification is:

- DEM: 5 outputs pass
- DEM: `hillshade_0to1_640.tif` is a known strict `xfail`
- SAR: 8 band outputs pass
- STACKS: 3 outputs are known strict `xfail`
- QA grid: 3 outputs pass
- QA post-RTC SAR intermediates: `not_implemented_no_source_equivalent`
- QA post-RTC SAR intermediates: contract-ambiguous notebook intermediate family
- `REPORT_640`: the three root report GeoTIFFs remain `not_implemented_no_source_equivalent`

Verification notes:

- the frozen notebook reference bundle is compared only against a matching notebook-grid app run
- arbitrary fresh production-grid UI runs are not accepted as Phase 5E proof
- app final SAR outputs already pass reference parity through `GEOTIFF_RADAR_BANDS/*`, `NPY_RADAR_BANDS/*`, and `npy_radar_bands/*`
- frozen QA post-RTC reference arrays are inconsistent with those final SAR output families
- the app no longer presents QA post-RTC arrays as implemented notebook-compatible outputs
- `REPORT_640` remains manifest/API verified as not implemented; no fake report rasters are created
- Phase 5E has not approved any math changes
- Phase 5E has not approved any tolerance changes

Future fix candidates:

- hillshade parity
- stack 21-band/layout parity
- QA post-RTC intermediate contract/provenance
- `REPORT_640` generation

Current known blockers:

- hillshade reference provenance
- `FINAL_TESLA` / Secret-layer / `REPORT_640` generation
- QA post-RTC intermediate contract/provenance
- `REPORT_640` generation

## Hillshade Reference Provenance Blocker

Current status:

- app hillshade matches the current literal notebook hillshade expression
- frozen reference hillshade is not exactly reproducible from the current notebook expression
- the remaining residual max error is about `1.8e-07`
- no tolerance is approved
- no app-side guesswork is approved

Accepted resolution paths:

- recover the original notebook/reference generation environment and prove it reproduces the frozen hillshade artifact exactly
- or regenerate the frozen hillshade reference through an approved reference-refresh process

Until reference provenance is resolved, hillshade remains a strict `xfail`.

## Phase 5F: Parity Report Integration

Phase 5F integrates the earlier evidence into one local operator-facing report.

The report should summarize:

- prerequisite status
- Phase 5D alias integrity status
- Phase 5E notebook reference parity status
- known not-implemented outputs
- final overall status

The report must stay local-only and must not expose absolute paths, bundle paths, or raw notebook-local details.

## Known Not-Implemented Outputs

These remain outside numeric parity proof until real source equivalents exist:

- the three root `REPORT_640` GeoTIFF outputs
- the notebook patched `14B` hypercube GeoTIFF
- pre-RTC SAR intermediate groups that are still `not_implemented_no_source_equivalent`

These should be reported explicitly, not silently ignored and not counted as numeric PASS.

## No Code/Math Changes Rule

Phase 5 numeric parity work must not:

- change SAR math
- change DEM math
- change GRID behavior
- change notebook code
- change tolerances
- change output-generation logic

Phase 5 is proof work, not retuning or reimplementation.
