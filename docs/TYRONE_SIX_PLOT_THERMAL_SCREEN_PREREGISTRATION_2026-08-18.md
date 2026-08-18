# Tyrone 3X Six-Plot Thermal Screen — Preregistration

Date: 2026-08-18

## Purpose

Test one new physical feature family, surface temperature, **before inspecting any Tyrone thermal values**.

This is a screening test only. It does not fit a depth formula, create a calibration row, or enable numerical depth.

## Frozen source

Primary source:

- Microsoft Planetary Computer `landsat-c2-l2`;
- Landsat 8/9 Collection 2 Level-2 Surface Temperature (`ST_B10`, Planetary Computer `lwir11` surface-temperature asset);
- date window: `2018-01-01` inclusive to `2024-01-01` exclusive;
- use only items that contain the Level-2 surface-temperature asset;
- use the product scale/offset for surface temperature; if explicit fallback constants are required they are `0.00341802` and `149.0 K`, matching the existing notebook-support implementation;
- cloud/fill/cirrus/cloud-shadow/snow pixels are masked from the Landsat QA band.

The Landsat thermal measurement has approximately 100 m native thermal GSD even where the distributed Level-2 product is sampled on a finer grid. Finer sampling must **not** be treated as independent 10 m or 30 m thermal information.

Do not use the notebook's 1 km MODIS-night proxy as a plot-scale predictor in this test.

## Frozen geometry

Use the validated WGS84 six-plot reference produced by PR #81:

- outslope: TP1 / TP2 / TP3;
- top surface: TP5 / TP6 / TP7;
- measured shallow / medium / deep ordering is fixed from the official AS-BUILT cover records;
- use a fixed 10 m inward polygon erosion to reduce edge mixing;
- do not translate, rotate, resize, or select geometry based on thermal results.

## Primary feature

For each usable Landsat acquisition, calculate one number per plot:

`median daytime surface temperature in kelvin`

No normalization using measured depth is allowed.

No terrain correction, regression, machine learning, feature combination, or result-driven exclusion is allowed in this screen.

## Acquisition acceptance

An acquisition is usable only when:

1. all six eroded plot polygons intersect valid surface-temperature data;
2. each plot has at least one valid native-thermal-supported footprint after QA masking;
3. no plot value is substituted or interpolated from another date;
4. all six values come from the same Landsat acquisition.

Require at least **24 usable acquisitions** overall. Otherwise the thermal family is `INSUFFICIENT_SUPPORT` and no candidate is declared.

## Frozen depth-order test

For every usable acquisition:

- `increasing` support requires `TP1 < TP2 < TP3` **and** `TP5 < TP6 < TP7`;
- `decreasing` support requires `TP1 > TP2 > TP3` **and** `TP5 > TP6 > TP7`;
- every other pattern, including a tie, is `no_support`.

A direct thermal depth candidate exists only if one direction satisfies **all** of these gates:

1. the same direction occurs on at least **70%** of all usable acquisitions;
2. each meteorological season (DJF, MAM, JJA, SON) has at least **4** usable acquisitions;
3. the same global direction occurs on at least **60%** of usable acquisitions within **every** season.

The thresholds and direction rule may not be changed after thermal values are inspected.

## Surface-confounding check

For every usable acquisition also record the matched-depth top-surface minus outslope differences:

- TP5 - TP1 (shallow);
- TP6 - TP2 (medium);
- TP7 - TP3 (deep).

These offsets are diagnostic only. They do not rescue a failed depth-order gate.

## Decision rules

- `THERMAL_DIRECT_CANDIDATE`: all frozen depth-order gates pass.
- `THERMAL_DIRECT_FAILED_CLOSE`: support is sufficient but any frozen depth-order gate fails.
- `THERMAL_INSUFFICIENT_SUPPORT`: fewer than 24 usable acquisitions or seasonal minimum support fails.

If a candidate passes, **do not fit a depth formula**. First preregister an independent validation against the mapped AS-BUILT test-pit depths with spatial-independence controls appropriate to the native thermal footprint.

If it fails, close this direct Landsat daytime thermal route without threshold relaxation, seasonal cherry-picking, geometry adjustment, or combination with failed NB/radar/northness variables.

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
thermal_values_inspected_before_preregistration = false
```
