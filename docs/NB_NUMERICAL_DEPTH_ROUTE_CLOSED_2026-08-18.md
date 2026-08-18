# NB Numerical Depth Route — Closed

Date: 2026-08-18
Status: **FAILED VALIDATION / CLOSED FOR NUMERICAL DEPTH**

## Decision

Do not continue tuning the current NB formula to produce numerical depth.

The existing NB output may remain only as an **uncalibrated notebook-derived proxy**. It must not be described or displayed as measured depth, calibrated depth, or validated depth in metres.

## Evidence

### 1. Raw numerical depth failed on TP5/TP6

- TP5 measured mean: 0.68072 m; raw NB median: 2.00718 m; error: +1.32646 m.
- TP6 measured mean: 0.94996 m; raw NB median: 2.03984 m; error: +1.08988 m.
- Measured TP6 - TP5: +0.26924 m.
- Raw NB TP6 - TP5: +0.03266 m.

The direction happened to be correct, but the numerical scale was not.

### 2. Two-anchor calibration failed an unseen holdout

Calibration built only from TP5 and TP6:

`depth_m = -15.865916 + 8.243723 * raw_NB`

TP7 was held out:

- TP7 measured mean: 1.30556 m.
- TP7 measured range: 1.27000-1.37160 m.
- raw NB: 2.05196.
- calibrated prediction: 1.04984 m.
- error: -0.25572 m.
- inside measured range: false.

### 3. Independent outslope sequence failed depth ordering

Measured depth increases TP1 < TP2 < TP3, but raw NB does not:

- TP1: 2.37662
- TP2: 2.40089
- TP3: 2.37451

### 4. Same-depth replicate pairs show strong surface/site effects

Raw NB differences for nominally comparable depths:

- 2-ft pair TP1 - TP5: +0.36944
- 3-ft pair TP2 - TP6: +0.36105
- 4-ft pair TP3 - TP7: +0.32255

These differences are large relative to the NB changes caused by the measured depth sequence on the top surface.

### 5. Individual component screening found no consistent depth signal

Components screened included:

`RATIO_DB, DOOR, THERMAL_DELTA, TPI, VH_DB, TUNNEL, VOID, THERMAL, SAR_COMP, VV_DB, NB_DEPTH, ROUGHNESS`

No tested component changed monotonically with depth in both independent sequences TP1/TP2/TP3 and TP5/TP6/TP7.

## Production safeguards

This closure does **not** authorize changes to:

- classifier;
- UI;
- NB formula;
- SAR constraints.

Numerical app depth remains blocked.

## Replacement path

Use the Tyrone six-plot reference dataset as a scientific screening set. Do not immediately train a global model from six plots.

First extract raw/less-derived physical sensor features and test whether any candidate retains a consistent depth relationship after surface-type effects are considered.
