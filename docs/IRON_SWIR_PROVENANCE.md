# IRON_SWIR Provenance

## Purpose

This document records the `IRON_SWIR` provenance conflict discovered during H4 and defines the decision gate that must be resolved before H5 reference-output comparison can be considered authoritative.

## Verified Conflict

The checked-in notebook inspection performed during H4 found:

- notebook source: `notebooks/new.ipynb`
- observed cell reference: `206`
- observed notebook formula:
  - `(B12 - B11) / (B12 + B11)`

The app implementation and current stage contract use:

- app formula:
  - `(B11 - B12) / (B11 + B12)`

These two formulas are sign-flipped versions of each other.

If `x = B11 - B12`, then:

- app formula = `x / (B11 + B12)`
- checked-in notebook formula = `-x / (B11 + B12)`

This is not just a denominator issue. It changes the sign convention of the output.

## Why H4.5 Exists

H4 established that the checked-in notebook evidence does not cleanly match the older PRD/parity narrative that described a buggy denominator.

Before H5 compares app outputs against frozen notebook references, the project must define one accepted production interpretation for `IRON_SWIR`.

H5 must not silently choose one interpretation.

## Decision Options

One and only one of the following production interpretations must be accepted before H5:

### Option A

App formula is canonical and notebook output is treated as `PARITY_CORRECTS`.

Interpretation:

- production keeps `(B11 - B12) / (B11 + B12)` as the accepted sign convention
- notebook reference output is treated as non-canonical where it differs
- H5 compares the app against the corrected analytical/app reference, not the notebook raster sign

### Option B

Checked-in notebook formula is canonical and the app must be changed later.

Interpretation:

- production treats the checked-in notebook sign convention as authoritative
- a later milestone must change the app or comparison logic accordingly
- H5 compares the app against the checked-in notebook sign convention and must currently fail until the app is reconciled

### Option C

An older notebook revision is canonical and must be identified by commit SHA or file hash.

Interpretation:

- the checked-in notebook is not the authoritative parity source for `IRON_SWIR`
- the canonical notebook revision must be pinned by exact commit SHA and/or file hash
- H5 uses that older revision’s evidence once captured and recorded

### Option D

H5 compares magnitude only, with the sign convention documented.

Interpretation:

- `IRON_SWIR` parity is defined on absolute value or magnitude-equivalent comparison
- the sign convention difference is treated as a documented convention mismatch
- H5 must document and enforce that narrower comparison rule explicitly

## Current Status

No final production interpretation has been accepted automatically in the repo state as of `2026-05-20`.

The provenance decision is therefore unresolved.

## Required Human Decision Before H5

A human project decision is required before H5:

1. Choose exactly one of Options A, B, C, or D.
1. Record the rationale.
1. If Option C is chosen, record the canonical notebook commit SHA and/or file hash.
1. Update `docs/OUTPUT_PARITY_CONTRACT.md` and `docs/PARITY_EXCEPTIONS.md` if the accepted interpretation changes the comparison rule.

## H5 Rule

Until this provenance decision is resolved, H5 must not silently pass `IRON_SWIR` parity.

Required behavior:

- H5 must read this document.
- If the decision remains unresolved, H5 must fail or skip with a clear reason that `IRON_SWIR` provenance is unresolved.
- If the decision is resolved, H5 must apply the accepted comparison rule exactly as documented here.
