# Tyrone 3X Six-Plot Terrain Screen — Result

Date: 2026-08-18

## Result

The preregistered terrain screen produced **one exploratory direct-depth candidate: northness**.

Northness is the north/south component of downslope aspect. It completely separated the replicated shallow, medium and deep plot levels in the same increasing direction at both frozen 10 m and 20 m inward buffers.

This is **not numerical-depth validation** and no formula/model may be fitted from these six plot values. The relationship could simply reflect where the 2 ft, 3 ft and 4 ft test plots were placed.

## Strong terrain-confounder result

Five variables consistently separated top-surface from outslope at the three matched depth levels and at both geometry buffers:

- elevation
- slope
- 3x3 roughness
- approximately 50 m TPI
- Laplacian curvature

This strengthens the earlier radar conclusion: terrain/surface condition is a major confounder at Tyrone.

## Northness plot medians

10 m inward buffer:

| Plot | Northness median |
|---|---:|
| TP1 | -0.06317 |
| TP2 | -0.01356 |
| TP3 | 0.77733 |
| TP5 | -0.42590 |
| TP6 | 0.18296 |
| TP7 | 0.68614 |

20 m inward buffer:

| Plot | Northness median |
|---|---:|
| TP1 | -0.06135 |
| TP2 | -0.01210 |
| TP3 | 0.78500 |
| TP5 | -0.42328 |
| TP6 | 0.16904 |
| TP7 | 0.59255 |

At each buffer the two shallow plots lie below both medium plots, and both medium plots lie below both deep plots.

## Execution

- workflow run: `32168252824`
- public source: Microsoft Planetary Computer `3dep-seamless`
- 10 m GSD
- one overlapping DEM item; read succeeded
- analysis CRS: EPSG:32612
- geometry sensitivities: 10 m and 20 m inward buffers

No Earth Engine, NB_DEPTH, classifier/PCA output, calibration row, model training or app-depth enablement was used.

## Scientific interpretation

Northness is only an **exploratory site-specific candidate**. Aspect cannot physically be assumed to measure cover thickness. The six test plots may have been deliberately located along a geometry/orientation pattern that happens to covary with nominal depth.

Therefore the next test must be independent of the six plot averages.

## Exact next action

Use the mapped individual cover-verification test pits on the official AS-BUILT sheets `3X_CQAR_006_R0` and `3X_CQAR_007_R0` as an independent holdout.

Primary validation rules must be preregistered before extracting northness values:

1. include all test pits with an unambiguous mapped marker and an exact numeric cover depth;
2. exclude values marked with `+` from the primary continuous test because they are lower-bound/censored measurements, not exact depths;
3. do not delete points based on their northness or whether they support the candidate;
4. digitize locations from the coordinate-controlled AS-BUILT drawing and transform them with the already validated Tyrone mine-grid/global transform;
5. test the fixed positive association independently; do not refit the six-plot screen.

If northness fails the independent test-pit holdout, close it without rescue and proceed to a separately preregistered thermal family.
