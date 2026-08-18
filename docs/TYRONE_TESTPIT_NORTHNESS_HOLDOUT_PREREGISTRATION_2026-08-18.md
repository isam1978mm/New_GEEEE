# Tyrone 3X Test-Pit Northness Holdout — Preregistration

Date: 2026-08-18

## Purpose

Independently test the exploratory six-plot northness candidate against mapped individual AS-BUILT cover-verification test pits.

The expected relationship is frozen as **positive** because the six-plot development screen found northness increasing from shallow to medium to deep.

## Primary observations

Use all test pits on `3X_CQAR_006_007_R0.pdf` that have:

- one unambiguous mapped marker;
- one exact numeric cover depth.

Do not treat `+` values or numeric ranges as exact measurements. They are excluded from the primary continuous test rather than assigned invented values.

## Independence filters

Before extracting northness:

- exclude points inside or within 20 m of TP1/TP2/TP3/TP5/TP6/TP7 development polygons;
- exclude points inside the sheet-defined Apex Area because the drawing note says no cover-depth verification was performed there;
- never exclude a point because its northness disagrees with the candidate.

At least 20 primary points must survive. If fewer than 20 survive, the result is `INSUFFICIENT_INDEPENDENT_POINTS`; do not relax the rules.

## Location recovery

Recover each point from the vector AS-BUILT drawing:

1. uniquely link the test-pit label/table row to its drawn marker;
2. fit PDF sheet coordinates to labeled Tyrone mine-grid controls;
3. require grid-control residual <= 5 ft;
4. convert the recovered mine-grid coordinate through the already validated mine-grid/global transform.

Ambiguous or unrecoverable markers are excluded with an explicit reason before northness extraction.

## Frozen predictor

Use the same public 10 m `3dep-seamless` DEM and northness definition as the six-plot terrain screen.

For every accepted test pit, calculate median northness within two fixed neighborhoods:

- 10 m radius;
- 20 m radius.

## Frozen statistical test

For each radius calculate Spearman rank correlation between exact cover depth in inches and northness.

Expected direction: positive.

Use a one-sided permutation test with:

- 100,000 permutations;
- random seed `314101`;
- pass threshold `rho >= 0.30`;
- permutation `p <= 0.05`.

The candidate passes only if **both** the 10 m and 20 m neighborhood tests pass.

## Interpretation

If it fails, close northness without tuning and proceed to thermal as a separate preregistered family.

If it passes, northness is still only a Tyrone site-specific candidate. Do not fit a transferable depth formula from this site alone; further independent-site validation would still be required.

No NB_DEPTH, classifier/PCA depth evidence, Earth Engine, calibration row, model training, or app-depth enablement is allowed in this holdout.
