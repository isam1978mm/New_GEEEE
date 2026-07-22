# TAMUCC Sentinel-1 Feasibility Closeout

Date: 2026-07-22

Status: closed as limited whole-site feasibility evidence.

## Final decision

Retain the provisional TAMUCC site/background analysis only as evidence that a
whole-site Sentinel-1 change may be present across the documented construction
window.

Do not treat this work as:

- target-level detection;
- known-depth evidence;
- relative-depth calibration;
- confirmed-negative calibration;
- scientific validation;
- causal proof of construction response;
- permission to enable depth output in the app.

## Completed evidence chain

1. Exact site/background acquisition matching was completed.
2. Private feature extraction produced 80 usable pre-construction acquisitions and
   81 usable post-construction acquisitions.
3. One post-construction acquisition had zero valid pixels in both polygons after
   the common quality mask. It was retained in private provenance and excluded from
   analysis.
4. The descriptive site-minus-background assessment found directional changes in
   the radar and incidence feature families.
5. All four radar-feature directions remained after pre-period incidence
   adjustment.
6. Temporal-block robustness was mixed, with weak strong-overlap coverage across
   many block comparisons.
7. Common-incidence-support restriction retained 64 pre and 77 post acquisitions.
8. No radar-feature direction reversed on common support. The VH change retained
   the strongest descriptive category; the other radar changes remained small.

## What this resolves

The TAMUCC Sentinel-1 whole-site feasibility question is complete. Additional
whole-site TAMUCC sensitivity analyses are not required for Depth Blocker 2.

## What remains blocked

Depth Blocker 2 remains open because the calibration contract still lacks:

- an official surveyed site and target map;
- target-level depth values tied to observation geometry;
- numerical uncertainty for each depth reference;
- contract-ready confirmed negatives;
- independent group-separated train, validation, and holdout records.

Until those records exist, depth training, depth estimation, scientific validation,
and app depth output remain disabled.

## Next workstream

Return directly to obtaining contract-ready known-depth records and confirmed
negatives. Do not continue broad TAMUCC analysis unless new target-level survey
evidence becomes available.
