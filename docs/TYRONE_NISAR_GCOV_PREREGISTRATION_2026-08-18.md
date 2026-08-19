# Tyrone NISAR GCOV L-band preregistration — 2026-08-18

## Purpose

Freeze the first NISAR L-band depth-signal test before any NISAR backscatter values are downloaded or inspected.

The question is narrow:

> Does calibrated NISAR L-band Frequency-A GCOV backscatter show a repeatable cover-depth ordering across both independent Tyrone surface groups?

A pass is only permission to perform a separately preregistered independent holdout against the mapped AS-BUILT test pits. It is **not** permission to fit a depth model, create a calibration row, or enable numerical app depth.

## Fixed source

Use only NISAR **L2 GCOV PROVISIONAL Frequency A** from the seven exact Tyrone acquisitions already confirmed by the metadata-only feasibility screen.

The products are fixed before values are inspected:

1. 2026-06-17 ascending, path 48 / frame 18;
2. 2026-06-28 descending, path 27 / frame 72;
3. 2026-06-29 ascending, path 48 / frame 18;
4. 2026-07-10 descending, path 27 / frame 72;
5. 2026-07-11 ascending, path 48 / frame 18;
6. 2026-07-22 descending, path 27 / frame 72;
7. 2026-07-23 ascending, path 48 / frame 18.

All seven are `40+5` acquisitions with Frequency-A HH/HV. For 40 MHz Frequency A, GCOV is posted to a 10 m square grid over land. GCOV provides calibrated gamma-0 covariance/backscatter terms with radiometric terrain correction.

Frequency B is excluded because its GCOV posting is 80 m and is too coarse for these plots. GSLC is deferred because the first test needs only calibrated amplitude/backscatter; phase-preserving complex data would add a separate hypothesis and much larger data volume.

## Fixed geometry

Use the validated WGS84 six-plot reference from PR #81:

`data/depth_reference/tyrone_3x_six_plot_reference_v1_wgs84.geojson`

Apply a fixed 10 m inward erosion to every plot, identical in concept to the earlier six-plot public sensor screens.

The two independent depth sequences remain:

- outslope: TP1 → TP2 → TP3;
- top surface: TP5 → TP6 → TP7.

No geometry translation, resizing, favourable core selection, or result-driven exclusion is allowed.

## Fixed features

Evaluate exactly three features, separately:

- `HH_DB = 10 log10(HHHH)`;
- `HV_DB = 10 log10(HVHV)`;
- `HH_MINUS_HV_DB = HH_DB - HV_DB = 10 log10(HHHH/HVHV)`.

No fitted combination of these features is allowed in this screen.

## Pixel support

For a plot/acquisition/feature to be usable:

- use only product quality/fill metadata for invalid-pixel exclusion;
- no filtering based on whether a backscatter value helps the expected ordering;
- power must be finite and positive before dB conversion;
- at least 15 valid 10 m product pixels must remain inside the fixed eroded plot;
- all six plots must pass for that feature/acquisition.

The direct screen requires all seven fixed acquisitions to be usable. If not, the decision is `NISAR_GCOV_INSUFFICIENT_SUPPORT`; the denominator is not reduced after seeing results.

For each usable plot/acquisition/feature, use the median value.

## Frozen depth-direction test

An acquisition supports **increasing** only if both are true:

- `TP1 < TP2 < TP3`;
- `TP5 < TP6 < TP7`.

It supports **decreasing** only if both are true:

- `TP1 > TP2 > TP3`;
- `TP5 > TP6 > TP7`.

Mixed ordering or a tie is `no_support`.

A feature becomes `NISAR_GCOV_DIRECT_CANDIDATE` only if one single direction satisfies all three gates:

- at least **5 of 7** acquisitions overall;
- at least **3 of 4** ascending acquisitions;
- at least **2 of 3** descending acquisitions.

Otherwise, with full support, that feature is closed as failed.

## Surface-confounding diagnostics

For every acquisition also record matched-depth top-minus-outslope offsets:

- TP5 − TP1;
- TP6 − TP2;
- TP7 − TP3.

These are diagnostics only. They cannot rescue a feature that fails the frozen direction gate.

## What happens after a pass

A six-plot pass is still exploratory because the current NISAR July 2026 products are calibrated but only partially validated.

Before any numerical model or calibration is considered, the passing L-band feature must be tested in a **new preregistration** against the 43 exact, independently mapped AS-BUILT Tyrone test pits. No test-pit L-band values may be inspected before that holdout protocol is frozen.

## Protected boundaries

This preregistration does not:

- use or modify the classifier;
- use `NB_DEPTH`;
- change the NB formula;
- call Earth Engine;
- change the UI;
- fit a model;
- create a calibration record;
- enable numerical app depth.

The existing C-band, northness, thermal, NDVI, and NDMI failures remain closed and are not retuned or mixed into this L-band screen.
