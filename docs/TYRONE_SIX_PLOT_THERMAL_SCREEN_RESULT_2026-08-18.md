# Tyrone 3X Six-Plot Thermal Screen — Final Result

Date: 2026-08-18

## Decision

**DIRECT LANDSAT DAYTIME THERMAL FAILED. CLOSE WITHOUT RESCUE.**

The thermal family was preregistered in PR #89 before Tyrone thermal values were inspected. The experiment used the validated six-plot WGS84 geometry from PR #81 and public Landsat 8/9 Collection 2 Level-2 surface temperature from Microsoft Planetary Computer.

No numerical-depth formula is justified from this route.

## Technical rerun note

The first workflow attempt did not constitute a scientific test. All 173 candidate reads stopped before a temperature value was evaluated because a masked `uint16` raster was incorrectly filled with `NaN`.

The correction changed only the raster-read implementation: integer source data are now read as float while the source mask is carried separately. Geometry, date window, QA rule, thermal feature, thresholds and decision rules were unchanged.

The corrected workflow then read **173 / 173** candidate items successfully.

## Frozen support

- source: Microsoft Planetary Computer `landsat-c2-l2`;
- Landsat 8/9 Collection 2 Level-2 surface temperature (`lwir11` / ST_B10);
- window: 2018-01-01 through 2023-12-31;
- six validated WGS84 AS-BUILT-derived plot polygons;
- fixed 10 m inward erosion;
- approximately 100 m native thermal support explicitly retained as a resolution limitation;
- no 1 km MODIS-night proxy used as a plot-scale predictor.

Usable acquisitions after the frozen all-six-plots availability rule: **134**.

Frozen minimum: 24. Therefore data support was sufficient and the depth-order gate must be evaluated rather than abstained.

## Frozen depth-order result

| Pattern across both surface groups | Acquisitions | Fraction |
|---|---:|---:|
| Increasing with depth | 14 | 10.45% |
| Decreasing with depth | 5 | 3.73% |
| Neither monotonic pattern | 115 | 85.82% |

The strongest direction was `increasing`, but its support fraction was only **0.10448**.

Frozen global requirement: **>= 0.70**.

Result: **FAIL**.

### Seasonal checks

| Season | Usable acquisitions | Increasing support | Fraction | Frozen >=60% gate |
|---|---:|---:|---:|---|
| DJF | 28 | 0 | 0.00% | FAIL |
| MAM | 35 | 8 | 22.86% | FAIL |
| JJA | 37 | 4 | 10.81% | FAIL |
| SON | 34 | 2 | 5.88% | FAIL |

All four seasons had enough observations. All four failed the frozen direction requirement.

## Surface confounding

Matched-depth top-surface minus outslope temperature differences were persistent:

| Matched nominal depth | Pair | Median top-minus-outslope | Positive fraction |
|---|---|---:|---:|
| shallow | TP5 - TP1 | +2.578 K | 99.25% |
| medium | TP6 - TP2 | +1.676 K | 99.25% |
| deep | TP7 - TP3 | +1.113 K | 79.85% |

The surface-condition offset is much more persistent than any depth ordering. This reinforces the earlier conclusion that Tyrone surface/topographic context strongly affects remote-sensing signals.

## Scientific meaning

Therefore:

- direct daytime Landsat surface temperature does not provide a stable shallow/medium/deep ordering across both Tyrone surface groups;
- the thermal route fails before any independent holdout is warranted;
- do not relax the 70%/60% gates;
- do not select only favorable months or seasons;
- do not alter plot geometry based on thermal values;
- do not combine this failed feature with failed NB, raw Sentinel-1 or northness variables to manufacture a six-plot depth model;
- no depth formula is fitted;
- no calibration record is created;
- app numerical depth remains blocked.

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
```

## Exact next action

Preregister the **optical vegetation/moisture feature family** separately before inspecting its six-plot depth ordering.

The next family should use higher-resolution optical observations capable of testing whether cover thickness has a repeatable vegetation or moisture response while still checking the same top-surface versus outslope confounding. No multivariate depth model should be started before a new feature survives both development screening and independent validation.
