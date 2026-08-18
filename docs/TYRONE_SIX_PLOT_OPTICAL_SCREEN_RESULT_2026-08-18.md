# Tyrone 3X Six-Plot Optical Vegetation/Moisture Screen — Final Result

Date: 2026-08-18

## Decision

**NDVI FAILED. NDMI FAILED. CLOSE BOTH DIRECT OPTICAL ROUTES WITHOUT RESCUE.**

The Sentinel-2 optical family was preregistered in PR #92 before Tyrone NDVI or NDMI values were inspected. The experiment used the validated PR #81 six-plot WGS84 geometry and public Sentinel-2 Level-2A data from Microsoft Planetary Computer.

No numerical-depth formula is justified from either feature.

## Frozen support

- source: Microsoft Planetary Computer `sentinel-2-l2a`;
- period: 2018-01-01 through 2023-12-31;
- growing season: April through October;
- fixed SCL mask from the preregistration;
- fixed 10 m inward erosion of all six plots;
- NDVI: B08/B04 on native 10 m support;
- NDMI: B8A/B11 on native 20 m support;
- unit of analysis: year-month median of qualifying acquisition-level plot medians.

The run processed **308** candidate Sentinel-2 items, producing **616** feature-scene rows with **zero technical failures**.

Both NDVI and NDMI had **42 / 42 possible usable growing-season year-month composites**. The support gate therefore passed fully for both features.

## NDVI result

Frozen rule: one direction must occur in both surface groups on at least 70% of all usable composites and at least 60% within every April-October calendar-month bucket.

| Pattern | Composites | Fraction |
|---|---:|---:|
| Decreasing with depth | 12 | 28.57% |
| Increasing with depth | 4 | 9.52% |
| Neither monotonic pattern | 26 | 61.90% |

The strongest direction was `decreasing`, at **28.57%**, far below the frozen 70% requirement.

Calendar-month support for that direction ranged from 16.67% to 66.67%; only September exceeded 60%. The all-month gate failed.

**NDVI decision: `OPTICAL_DIRECT_FAILED_CLOSE`.**

## NDMI result

| Pattern | Composites | Fraction |
|---|---:|---:|
| Increasing with depth | 12 | 28.57% |
| Decreasing with depth | 3 | 7.14% |
| Neither monotonic pattern | 27 | 64.29% |

The strongest direction was `increasing`, again only **28.57%**, far below the frozen 70% requirement.

Calendar-month support ranged from 0% to 66.67%; only June exceeded 60%. The all-month gate failed.

**NDMI decision: `OPTICAL_DIRECT_FAILED_CLOSE`.**

## Surface-confounding diagnostic

NDMI showed a much more persistent surface-group separation than depth ordering:

| Matched nominal depth | Pair | Median top-minus-outslope NDMI | Negative fraction |
|---|---|---:|---:|
| shallow | TP5 - TP1 | -0.03360 | 100.00% |
| medium | TP6 - TP2 | -0.03689 | 100.00% |
| deep | TP7 - TP3 | -0.03229 | 95.24% |

This is the same recurring scientific problem seen in radar and thermal screening: surface/topographic condition is more stable than the desired shallow/medium/deep cover signal.

NDVI surface offsets were weaker/mixed, but NDVI still failed the direct depth-order gate decisively.

## Scientific meaning

Therefore:

- vegetation greenness does not provide stable six-plot depth ordering;
- Sentinel-2 NDMI does not provide stable six-plot depth ordering;
- NDMI strongly distinguishes top-surface from outslope conditions at matched depth, which is confounding rather than validated depth sensitivity;
- no independent optical holdout is warranted;
- do not select favorable months such as September NDVI or June NDMI;
- do not change the frozen 70% / 60% thresholds;
- do not move plot geometry;
- do not combine these failed optical variables with failed NB, raw radar, northness, or thermal variables to manufacture a depth model;
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

**Do not continue feature fishing on the same six plots.**

Before any additional satellite feature family is tested, inspect the existing official-record/project evidence for a **second independent measured-depth site** with coordinate-tied geometry or survey points. The project history already contains Tyrone Dam 1 / other official-record screening material that must be exhausted first.

If a second independent site exists, use it to decide whether a replacement method can be designed with true site-level validation. If it does not, the project must explicitly choose between obtaining new direct/geophysical depth data and accepting that satellite-only numerical depth remains unsupported.
