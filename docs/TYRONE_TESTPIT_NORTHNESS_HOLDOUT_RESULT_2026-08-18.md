# Tyrone 3X Test-Pit Northness Holdout — Final Result

Date: 2026-08-18

## Decision

**NORTHNESS FAILED THE INDEPENDENT HOLDOUT. CLOSE WITHOUT RESCUE.**

The exploratory six-plot terrain screen had identified northness as a possible site-specific depth-responsive feature. PR #86 froze the independent test before any individual test-pit northness values were extracted.

The independent holdout fails the frozen effect-size requirement at both radii. Northness must therefore not be used to fit or justify numerical cover depth.

## Independent observations

Source: `3X_CQAR_006_007_R0.pdf`, AS-BUILT cover-verification test pits.

Primary set after the preregistered filters:

- 43 uniquely mapped test pits with one exact numeric cover depth;
- `+` values excluded as lower-bound/censored measurements;
- range-valued observations excluded from the continuous test;
- no point removed because of its northness value or whether it supported the candidate;
- all 43 accepted points lie outside and more than 20 m from TP1/TP2/TP3/TP5/TP6/TP7;
- closest accepted test pit to a development plot: 39.098 m;
- Apex Area exclusion respected;
- PDF-to-mine-grid maximum residual: 0.2703 ft, comfortably below the frozen 5 ft maximum.

Permanent point mapping:

`data/depth_reference/tyrone_3x_testpit_northness_holdout_points_v1.csv`

The already validated Tyrone mine-grid/global transform was used after the drawing-coordinate recovery.

## Frozen predictor and test

Terrain source:

- Microsoft Planetary Computer `3dep-seamless`;
- source item `n33w109-13`;
- 10 m GSD;
- EPSG:32612 analysis grid;
- same northness definition as the six-plot development screen.

For every accepted test pit, median northness was calculated within fixed 10 m and 20 m neighborhoods.

The preregistered candidate gate required, at **both** radii:

- positive Spearman association;
- `rho >= 0.30`;
- one-sided 100,000-permutation `p <= 0.05`;
- random seed `314101`.

## Result

| Radius | n | Spearman rho | One-sided permutation p | Frozen gate |
|---|---:|---:|---:|---|
| 10 m | 43 | 0.26355 | 0.04212 | **FAIL** |
| 20 m | 43 | 0.27084 | 0.03846 | **FAIL** |

The p-values are below 0.05, but this does **not** make the candidate pass. The preregistered effect-size requirement was also mandatory, and `rho` is below 0.30 at both radii.

The rho threshold cannot be relaxed after seeing the result.

## Scientific meaning

There is a modest positive association between northness and measured cover depth in these mapped test pits, but it is weaker than the minimum effect size required before the data were inspected.

Therefore:

- the six-plot northness pattern does not survive its predeclared independent validation gate;
- northness is closed as a numerical-depth candidate;
- no depth formula is fitted;
- no calibration record is created;
- no model training begins;
- app numerical depth remains blocked.

This result also leaves the previous conclusions unchanged:

- NB numerical depth remains CLOSED / FAILED;
- raw Sentinel-1 VV/VH/log-ratio remains CLOSED under its six-plot protocol;
- terrain variables remain important surface/slope confounders.

## Safeguards

```text
classifier_output_used = false
pca_anomaly_used = false
nb_depth_used = false
earth_engine_query_executed = false
calibration_record_created = false
training_started = false
app_depth_enabled = false
thresholds_changed_after_result = false
points_removed_based_on_northness = false
```

## Exact next action

Follow the frozen decision rule from PR #86:

**Preregister the thermal feature family separately.**

Do not combine failed NB, raw radar, or northness variables into a six-plot model. The thermal screen must be defined before inspecting its six-plot depth ordering, and any candidate that emerges must receive an independent validation step before numerical-depth use.
