# Tyrone 3X Six-Plot Optical Vegetation/Moisture Screen — Preregistration

Date: 2026-08-18

## Purpose

Test two physically interpretable Sentinel-2 optical feature families **before inspecting any Tyrone optical index values**:

1. vegetation response: NDVI;
2. vegetation/water-status response: NDMI.

Each feature is evaluated separately. This is a screening test only. It does not fit a depth formula, combine failed predictors, create a calibration row, or enable numerical depth.

## Frozen source

Primary source:

- Microsoft Planetary Computer `sentinel-2-l2a`;
- Sentinel-2 Level-2A surface reflectance;
- date window: `2018-01-01` inclusive to `2024-01-01` exclusive;
- growing-season months only: April through October;
- all overlapping acquisitions are considered before fixed quality masking;
- no acquisition or month may be selected or removed because its NDVI/NDMI value supports or contradicts depth ordering.

## Frozen quality mask

Use the Sentinel-2 Scene Classification Layer (`SCL`). Exclude pixels classified as:

- 0: no data;
- 1: saturated / defective;
- 3: cloud shadow;
- 8: cloud medium probability;
- 9: cloud high probability;
- 10: thin cirrus;
- 11: snow / ice.

All other SCL classes remain eligible. No result-driven masking changes are allowed.

## Frozen geometry

Use the validated WGS84 six-plot reference produced by PR #81:

- outslope: TP1 / TP2 / TP3;
- top surface: TP5 / TP6 / TP7;
- official measured shallow / medium / deep ordering is fixed from the AS-BUILT cover records;
- use a fixed 10 m inward polygon erosion to reduce boundary mixing;
- do not translate, rotate, resize, or select geometry based on optical results.

## Frozen features

### NDVI — vegetation

Use native 10 m Sentinel-2 bands:

`NDVI = (B08 - B04) / (B08 + B04)`

- B08 = NIR, 10 m;
- B04 = red, 10 m;
- evaluate on the native 10 m support grid;
- require at least **20 valid 10 m product pixels** in every eroded plot for an acquisition to contribute to that plot-month.

### NDMI — vegetation/moisture

Use native 20 m Sentinel-2 bands:

`NDMI = (B8A - B11) / (B8A + B11)`

- B8A = narrow NIR, 20 m;
- B11 = SWIR, 20 m;
- evaluate on the native 20 m support grid;
- do not upsample B11 and claim 10 m moisture information;
- require at least **5 valid 20 m product pixels** in every eroded plot for an acquisition to contribute to that plot-month.

For both indices, non-finite values and zero denominators are invalid. Reflectance scaling may be applied consistently or omitted because the common multiplicative factor cancels in the normalized-difference ratio.

## Frozen monthly-composite rule

The unit of analysis is one **year-month composite**, not an individual scene.

For each feature independently:

1. calculate the median index for each plot in every quality-valid acquisition;
2. for each year-month from April through October, calculate the median of all available acquisition-level plot medians;
3. a year-month is usable only if all six plots have a composite value;
4. require at least one qualifying acquisition for all six plots in that year-month;
5. do not interpolate a missing plot or month.

This produces at most 42 growing-season year-month composites for 2018–2023.

## Frozen support gate

A feature has sufficient support only if:

1. at least **30 usable year-month composites** exist overall;
2. each calendar month April, May, June, July, August, September, and October has usable composites in at least **4 distinct years**.

If either requirement fails, that feature is `OPTICAL_INSUFFICIENT_SUPPORT` and no direct candidate is declared for it.

## Frozen depth-order test

For every usable year-month composite:

- `increasing` support requires `TP1 < TP2 < TP3` **and** `TP5 < TP6 < TP7`;
- `decreasing` support requires `TP1 > TP2 > TP3` **and** `TP5 > TP6 > TP7`;
- every other pattern, including a tie, is `no_support`.

For each feature separately, a direct depth candidate exists only if one direction satisfies **all** of these gates:

1. the same direction occurs in at least **70%** of all usable year-month composites;
2. the same direction occurs in at least **60%** of the usable composites for **every calendar month April–October**;
3. the support gate above is satisfied.

The thresholds and direction rule may not be changed after NDVI or NDMI values are inspected.

## Surface-confounding check

For each usable year-month also record matched-depth top-surface minus outslope differences:

- TP5 - TP1 (shallow);
- TP6 - TP2 (medium);
- TP7 - TP3 (deep).

These offsets are diagnostic only. They cannot rescue a failed depth-order gate.

## Decision rules

Each feature receives one independent decision:

- `OPTICAL_DIRECT_CANDIDATE`: all frozen support and depth-order gates pass;
- `OPTICAL_DIRECT_FAILED_CLOSE`: support is sufficient but any frozen depth-order gate fails;
- `OPTICAL_INSUFFICIENT_SUPPORT`: the frozen support gate fails.

If either NDVI or NDMI passes, **do not fit a depth formula**. First preregister an independent validation against the mapped AS-BUILT test-pit depths, with spatial-independence controls appropriate to the feature's native 10 m or 20 m support.

If a feature fails, close that direct feature without threshold relaxation, favorable-month selection, geometry adjustment, or combination with failed NB, raw radar, northness, or thermal variables.

## Safeguards

```text
classifier_output_used = false
pca_anomaly_used = false
nb_depth_used = false
existing_nb_formula_changed = false
classifier_changed = false
ui_changed = false
model_training_started = false
calibration_record_created = false
app_depth_enabled = false
optical_values_inspected_before_preregistration = false
```
