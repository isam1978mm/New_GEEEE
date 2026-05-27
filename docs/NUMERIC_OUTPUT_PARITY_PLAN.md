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
- notebook-compatible post-RTC SAR intermediate aliases vs existing SAR arrays

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
